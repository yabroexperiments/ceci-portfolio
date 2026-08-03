#!/usr/bin/env python3
"""
localize_assets.py - Make site/ fully standalone: no runtime dependency on
IM Creator, Google CDNs, or any third-party host for assets.

What it does
------------
1. Crawls every .html and .css under site/ and finds external asset URLs.
2. Downloads them into site/assets/{img,fonts,css}/.
3. Rewrites every reference to a depth-correct relative local path.
4. Resolves fonts.googleapis.com @import CSS: fetches the stylesheet, pulls the
   fonts.gstatic.com files it references, self-hosts both.
5. Disables IM Creator's IMOS/Stripe ecommerce init by flipping
   data-ecommerce-solution="IMOS" -> "DISABLED" (their own supported code path
   in spimeengine.js, which early-returns before the XHR to their backend).
6. Writes site/assets/MANIFEST.json recording every localized URL AND every URL
   deliberately left remote, so the scope of the work is auditable.

Idempotent: already-downloaded files are not re-fetched; already-rewritten
references are left alone. Safe to re-run.

Usage:  python3 localize_assets.py [--dry-run] [--jobs N]
"""

import argparse
import concurrent.futures as futures
import hashlib
import json
import mimetypes
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE = pathlib.Path(__file__).parent / "site"
ASSETS = SITE / "assets"

# Hosts whose assets we pull local. Everything else is either her own outbound
# content links or an intentional remote embed (see LEAVE_REMOTE).
LOCALIZE_HOSTS = {
    "lh3.googleusercontent.com",      # her portfolio imagery (IM Creator's Google acct)
    "storage.googleapis.com",         # IM Creator's own xprs_resources font bucket
    "themes.googleusercontent.com",   # legacy Google webfont CDN
    "fonts.gstatic.com",              # Google Fonts binaries
}
# Google Fonts stylesheets need recursive handling, not a plain download.
GFONT_CSS_HOST = "fonts.googleapis.com"

# Deliberately NOT localized, with the reason. Recorded in the manifest.
LEAVE_REMOTE = {
    "www.youtube.com": "Video embeds - cannot be self-hosted; her content choice, not an IM Creator dependency",
    "www.w3.org": "XML/SVG namespace URIs - never fetched by the browser",
    "www.linkedin.com": "Outbound content link",
    "github.com": "Outbound content link",
    "www.binance.com": "Outbound content link",
    "binance.com": "Outbound content link",
    "icard.ai": "Outbound content link",
    "www.apollox.finance": "Outbound content link",
    "peakd.com": "Outbound content link",
    "jonsuh.com": "URL inside a CSS credit comment - never fetched",
    # 2026-08-03 purge: www.imcreator.com / imos006 appspot / admin.bricksite.net /
    # www.imdomainrouter.com literals were REMOVED outright (dead attributes
    # stripped from all pages; dead JS literals swapped for inert same-origin or
    # .invalid values). data-ecommerce-solution="DISABLED" must remain on every
    # page - removing the attribute re-enables the ecommerce phone-home branch.
    "checkout.stripe.com": "Inert: only loaded by the ecommerce branch, gated off by DISABLED",
    "changhsiju.xyz": "Her own canonical/og: URLs injected by enrich_meta.py",
    "www.google.com": "Outbound content link",
    "www.fontsquirrel.com": "URL inside a CSS credit comment - never fetched",
    "localhost": "Dev-only branch inside IM Creator JS",
}

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# NOTE: '|' must be in this class. Google Fonts v1 stylesheet URLs separate
# families with a literal pipe (family=Teko:300|Dosis|Abel|...). Omitting it
# truncates the URL at the first family, which both under-downloads the fonts
# and leaves the remainder dangling in the rewritten file.
URL_RE = re.compile(r'https?://[A-Za-z0-9._~:/?#\[\]@!$&\'()*+,;=%|-]+')

EXT_BY_TYPE = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
    "image/webp": ".webp", "image/svg+xml": ".svg",
    "font/woff": ".woff", "font/woff2": ".woff2",
    "application/font-woff": ".woff", "application/font-woff2": ".woff2",
    "font/ttf": ".ttf", "application/x-font-ttf": ".ttf",
    "font/otf": ".otf", "application/vnd.ms-fontobject": ".eot",
    "text/css": ".css",
}


def slug(url: str, fallback_ext: str = "") -> str:
    """Deterministic, collision-free, human-recognisable local filename."""
    p = urllib.parse.urlsplit(url)
    stem = pathlib.Path(p.path).name or "asset"
    stem = re.sub(r"[^A-Za-z0-9_.-]", "_", stem)[:60]
    # Distinguish =s300 / =s50 variants and query strings.
    tag = hashlib.sha1(url.encode()).hexdigest()[:10]
    stem = re.sub(r"\.[A-Za-z0-9]+$", "", stem)
    return f"{stem}-{tag}{fallback_ext}"


def fetch(url: str, timeout: int = 45):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "").split(";")[0].strip()


def kind_of(url: str, ctype: str) -> str:
    if ctype.startswith("image/"):
        return "img"
    if ctype.startswith("font/") or "font" in ctype or url.endswith(
            (".woff", ".woff2", ".ttf", ".otf", ".eot", ".svg")):
        return "fonts"
    if ctype == "text/css":
        return "css"
    return "img"


def source_files():
    for p in sorted(SITE.rglob("*")):
        if p.is_file() and p.suffix.lower() in (".html", ".css", ".js") and ASSETS not in p.parents:
            yield p


def relpath_from(src: pathlib.Path, target: pathlib.Path) -> str:
    """Depth-correct local path for a reference to `target` written inside `src`.

    HTML/CSS get a document-relative path, matching the site's existing
    convention (`assets/...` from site root, `../assets/...` from a page dir).

    JavaScript gets a ROOT-relative path instead. A relative URL assigned in JS
    (e.g. img.src = "...") is resolved by the browser against the *document*
    URL, not the script URL - so a document-relative path written into a shared
    script would resolve correctly on the homepage and 404 on every subpage.
    Root-relative is correct because the site is served from the domain root.
    """
    import os
    if src.suffix.lower() == ".js":
        return "/" + str(target.relative_to(SITE)).replace(os.sep, "/")
    return os.path.relpath(target, src.parent).replace(os.sep, "/")


def discover():
    """url -> set(files referencing it)"""
    refs = {}
    for f in source_files():
        text = f.read_text(errors="replace")
        for m in URL_RE.finditer(text):
            url = m.group(0).rstrip(").,;'\"")
            host = urllib.parse.urlsplit(url).netloc
            if host in LOCALIZE_HOSTS or host == GFONT_CSS_HOST:
                refs.setdefault(url, set()).add(f)
    return refs


def download_one(url, dry_run=False):
    """Returns (url, local_path or None, error or None)."""
    try:
        # Pre-compute a stable name; if any existing file matches the hash tag, reuse.
        tag = hashlib.sha1(url.encode()).hexdigest()[:10]
        for sub in ("img", "fonts", "css"):
            d = ASSETS / sub
            if d.is_dir():
                hit = list(d.glob(f"*-{tag}.*"))
                if hit:
                    return url, hit[0], None
        if dry_run:
            return url, None, "dry-run"
        data, ctype = fetch(url)
        sub = kind_of(url, ctype)
        ext = EXT_BY_TYPE.get(ctype) or pathlib.Path(
            urllib.parse.urlsplit(url).path).suffix or mimetypes.guess_extension(ctype) or ".bin"
        out = ASSETS / sub / slug(url, ext)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        return url, out, None
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as e:
        return url, None, f"{type(e).__name__}: {e}"


# IM Creator does responsive images by appending Google's CDN resize parameter
# (=s300, =s600, ...) to an image URL at runtime. That only works because
# lh3.googleusercontent.com resizes on the fly. Self-hosted static files cannot,
# so an appended "=s260" turns a valid local path into a 404.
#
# Every one of these sources is the ORIGINAL, unsized image (data-bgimg and the
# <img src> attributes now point at the base file), so simply not appending
# yields full-resolution images - strictly better than the resized variant.
RESIZE_PATCHES = [
    ("_imc/js/lightbox.js",
     'imageSrc + "=s" + newWidth', 'imageSrc'),
    ("_imc/js/lightbox.js",
     'imageSrc += "=s" + newWidth', 'imageSrc += ""'),
    ("_imc/js/spimeengine.js",
     'currentImg.attr("src") + "=s" + loadWidth', 'currentImg.attr("src")'),
]


def patch_dynamic_resize(dry_run=False):
    """Neutralise runtime =sNNN URL construction. Fails loudly on drift."""
    applied, already, missing = 0, 0, []
    for rel, needle, repl in RESIZE_PATCHES:
        f = SITE / rel
        if not f.is_file():
            missing.append(f"{rel} (file not found)")
            continue
        t = f.read_text(errors="replace")
        if needle in t:
            if not dry_run:
                f.write_text(t.replace(needle, repl))
            applied += 1
        elif repl in t:
            already += 1
        else:
            missing.append(f"{rel}: {needle!r}")
    print(f"  resize patches: {applied} applied, {already} already present")
    if missing:
        # Do NOT continue silently: an unpatched call site means 404 images at
        # runtime, which static grep-based checks will not catch.
        print("!! resize patch target(s) NOT FOUND - IM Creator JS has changed:")
        for m in missing:
            print(f"   {m}")
        sys.exit(2)


# Social-preview meta tags (og:image, twitter:image) MUST hold absolute URLs -
# the OG spec requires it, and chat-app scrapers (LINE/WhatsApp/Slack, the
# audience enrich_meta.py exists for) won't resolve relative paths. The main
# rewrite pass turns their lh3.googleusercontent.com URLs into relative local
# paths like "../assets/img/x.png"; this pass re-absolutizes them against the
# canonical domain, keeping them self-hosted AND scraper-resolvable.
CANONICAL = "https://changhsiju.xyz"
# Matches the whole <meta ...> tag regardless of attribute order (enrich_meta's
# output puts content= FIRST: <meta content="..." property="og:image"/>).
META_TAG_RE = re.compile(
    r'<meta\b[^>]*(?:property="og:image"|name="twitter:image")[^>]*>')
CONTENT_ATTR_RE = re.compile(r'(content=")([^"]+)(")')


def absolutize_social_meta(dry_run=False):
    fixed_pages = 0
    fixed_tags = 0
    for f in SITE.rglob("*.html"):
        if ASSETS in f.parents:
            continue
        text = f.read_text(errors="replace")
        page_dir = f.parent

        def fix_tag(tag_match):
            nonlocal fixed_tags
            tag = tag_match.group(0)

            def fix_content(m):
                nonlocal fixed_tags
                url = m.group(2)
                if url.startswith(("http://", "https://")):
                    return m.group(0)  # already absolute
                target = (page_dir / url).resolve()
                try:
                    rel = target.relative_to(SITE.resolve())
                except ValueError:
                    return m.group(0)  # points outside site/ - leave untouched
                fixed_tags += 1
                return m.group(1) + f"{CANONICAL}/{rel.as_posix()}" + m.group(3)

            return CONTENT_ATTR_RE.sub(fix_content, tag)

        new = META_TAG_RE.sub(fix_tag, text)
        if new != text:
            if not dry_run:
                f.write_text(new)
            fixed_pages += 1
    print(f"  social meta absolutized: {fixed_tags} tags in {fixed_pages} pages")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--jobs", type=int, default=12)
    args = ap.parse_args()

    if not SITE.is_dir():
        sys.exit(f"site/ not found at {SITE}")

    print("== discovering external asset references ==")
    refs = discover()
    gfont_css = {u for u in refs if urllib.parse.urlsplit(u).netloc == GFONT_CSS_HOST}
    direct = {u for u in refs if u not in gfont_css}
    print(f"  {len(direct)} direct asset URLs")
    print(f"  {len(gfont_css)} Google Fonts stylesheets (will be resolved recursively)")

    mapping = {}   # remote url -> local Path
    errors = {}

    # --- pass 1: direct assets -------------------------------------------------
    print(f"\n== downloading {len(direct)} assets (jobs={args.jobs}) ==")
    done = 0
    with futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for url, path, err in ex.map(lambda u: download_one(u, args.dry_run), sorted(direct)):
            done += 1
            if err and err != "dry-run":
                errors[url] = err
            elif path:
                mapping[url] = path
            if done % 50 == 0:
                print(f"  {done}/{len(direct)}")
    print(f"  {done}/{len(direct)} done, {len(errors)} errors")

    # --- pass 2: Google Fonts stylesheets + their gstatic binaries -------------
    print(f"\n== resolving {len(gfont_css)} Google Fonts stylesheets ==")
    for url in sorted(gfont_css):
        if args.dry_run:
            continue
        try:
            css_bytes, _ = fetch(url)
        except Exception as e:              # noqa: BLE001 - report and continue
            errors[url] = f"gfont css: {e}"
            continue
        css = css_bytes.decode("utf-8", "replace")
        inner = sorted(set(URL_RE.findall(css)))
        inner = [u.rstrip(").,;'\"") for u in inner
                 if urllib.parse.urlsplit(u).netloc in LOCALIZE_HOSTS]
        for iu in inner:
            _, p, err = download_one(iu)
            if err:
                errors[iu] = err
            elif p:
                mapping[iu] = p
                css = css.replace(iu, f"../{p.parent.name}/{p.name}")
        out = ASSETS / "css" / slug(url, ".css")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(css)
        mapping[url] = out
        print(f"  {out.name}  ({len(inner)} font files)")

    # --- pass 3: rewrite every reference --------------------------------------
    print("\n== rewriting references ==")
    rewritten = 0
    for f in source_files():
        text = original = f.read_text(errors="replace")
        # LONGEST URL FIRST. Google image URLs come in a base form and sized
        # variants (".../ABC" and ".../ABC=s300"), so the base is a strict
        # prefix of the variant. Replacing the base first rewrites the variant
        # into "assets/img/ABC-hash.png=s300", which 404s. Descending length
        # guarantees the most specific URL is consumed before its prefix.
        for url, path in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
            if url in text:
                text = text.replace(url, relpath_from(f, path))
        # Disable the IMOS/Stripe ecommerce init (kills the IM Creator XHR).
        text = text.replace('data-ecommerce-solution="IMOS"',
                            'data-ecommerce-solution="DISABLED"')
        if text != original and not args.dry_run:
            f.write_text(text)
            rewritten += 1
    print(f"  {rewritten} files rewritten")

    print("\n== neutralising runtime =sNNN image resizing ==")
    patch_dynamic_resize(args.dry_run)

    print("\n== absolutizing og:image / twitter:image ==")
    absolutize_social_meta(args.dry_run)

    # --- manifest --------------------------------------------------------------
    if not args.dry_run:
        ASSETS.mkdir(parents=True, exist_ok=True)
        mf = SITE.parent / "docs" / "asset-manifest.json"
        # MERGE with any existing manifest. This script is idempotent, so a
        # second run discovers nothing (references are already local) - writing
        # a fresh manifest from that run would erase the record of everything
        # localized previously. The manifest is the audit trail; it must only
        # ever grow.
        previous = {}
        if mf.is_file():
            try:
                previous = json.loads(mf.read_text()).get("localized", {})
            except (json.JSONDecodeError, OSError):
                previous = {}
        merged = dict(previous)
        merged.update({u: str(p.relative_to(SITE)) for u, p in mapping.items()})
        mf.write_text(json.dumps({
            "localized": dict(sorted(merged.items())),
            "localized_count": len(merged),
            "left_remote_by_design": LEAVE_REMOTE,
            "errors": errors,
        }, indent=2))
        print(f"\n  manifest -> {mf}")

    if errors:
        print(f"\n!! {len(errors)} FAILED - site is NOT yet standalone:")
        for u, e in list(errors.items())[:20]:
            print(f"   {u}\n     {e}")
        sys.exit(1)
    print("\nOK - all discovered assets localized.")


if __name__ == "__main__":
    main()
