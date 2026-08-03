#!/usr/bin/env python3
"""Mirror the live www.changhsiju.com site into mirror_v2/ as a 100% identical
self-contained static replica.

What it does:
  1. Fetches all 24 known pages (homepage + about-me + 22 project pages).
  2. Discovers every <link rel=stylesheet> and <script src> reference per page.
  3. Downloads each unique imcreator.com asset (CSS, JS) into mirror_v2/_imc/.
  4. Recursively walks downloaded CSS for url(...) references — downloads
     referenced fonts/images on imcreator.com so we don't depend on it being up.
  5. Rewrites HTML <link>/<script>/<a> URLs to local relative paths.
  6. Per-page static_style?vbid=X URLs become _imc/static_style/{vbid}.css.

What it does NOT do:
  - Download Google CDN images (lh3.googleusercontent.com). Per existing project
    convention these are stable and cross-origin-safe; we keep them remote so
    the site stays small.
  - Modify the design — no logo/footer/styling injection. 100% identical to live.

Cache: .ripcache_live/  (gitignored)
Output: mirror_v2/  (gitignored)
"""
from __future__ import annotations
import hashlib
import re
import ssl
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from bs4 import BeautifulSoup

# --- Config -----------------------------------------------------------------

BASE = "http://www.changhsiju.com"
ROOT = Path(__file__).parent
MIRROR = ROOT / "mirror_v2"
CACHE = ROOT / ".ripcache_live"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# All real content slugs (verified from live homepage <a> scrape)
PAGES = [
    "",                             # homepage
    "about-me",
    "bnct",
    "binance-future-trading-platform",
    "binance-leaderboard",
    "traderwagon_platform",
    "traderwagon_mkt",
    "xxyz",
    "coinful",
    "icardai",
    "acadine_watch",
    "acadine_smart-home",
    "acadine_feature-phone",
    "mozilla_smart-tv",
    "mozilla_feature-phone",
    "mozilla_car-ui",
    "htc_phone-app",
    "htc_dot-view",
    "htc_cos-wallpaper",
    "htc_message",
    "htc_clock",
    "htc_scribble",
    "htc_lifeme",
    "htc_mini",
    "htc_tablet",
]

# Hosts whose assets we want LOCAL copies of (so site is self-contained).
LOCALIZE_HOSTS = {"www.imcreator.com", "imcreator.com", "xprs.imcreator.com"}

# Hosts whose assets we leave remote (stable CDNs we trust).
REMOTE_OK_HOSTS = {
    "lh3.googleusercontent.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "ajax.googleapis.com",
    "www.youtube.com",
    "youtube.com",
    "www.google-analytics.com",
}

# --- HTTP -------------------------------------------------------------------

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE  # tolerate stale certs on legacy hosts

def http_get(url: str, *, retries: int = 3) -> bytes | None:
    """Cached GET. Returns bytes or None on failure."""
    CACHE.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha1(url.encode()).hexdigest()
    cf = CACHE / h
    if cf.exists():
        return cf.read_bytes()
    last_err = None
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, context=CTX, timeout=30) as r:
                data = r.read()
            cf.write_bytes(data)
            return data
        except (HTTPError, URLError, TimeoutError) as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(1 + attempt)
    print(f"    !! GET failed: {url}  ({last_err})", file=sys.stderr)
    return None

# --- URL helpers ------------------------------------------------------------

def absolutize(href: str, page_url: str) -> str:
    """Turn a relative or protocol-relative href into an absolute http(s):// URL."""
    if href.startswith("//"):
        return "http:" + href
    if href.startswith(("http://", "https://")):
        return href
    return urljoin(page_url, href)

def is_localize(url: str) -> bool:
    """Should we download this asset and serve it locally?"""
    host = urlparse(url).netloc.lower()
    return host in LOCALIZE_HOSTS

def local_path_for(url: str) -> str:
    """Return a relative-from-root local path like '_imc/css/fonts.css'.

    Strips query string except for static_style which uses ?vbid=... as identity.
    """
    p = urlparse(url)
    path = p.path
    if path.startswith("/static_style"):
        # Pull vbid out of query
        m = re.search(r"vbid=([^&]+)", p.query)
        vbid = m.group(1) if m else "default"
        return f"_imc/static_style/{vbid}.css"
    if path == "/all_js.js":
        return "_imc/all_js.js"
    if path.startswith("/css/"):
        return f"_imc{path}"
    if path.startswith("/js/"):
        return f"_imc{path}"
    if path.startswith("/img/") or path.startswith("/imgs/") or path.startswith("/fonts/"):
        return f"_imc{path}"
    # Catch-all for any other imcreator.com asset
    return f"_imc/_misc{path}"

def relpath_from(page_slug: str, target: str) -> str:
    """Build a relative href from a page slug back to a target rooted at mirror_v2/.

    page_slug='' (homepage) → target as-is.
    page_slug='about-me' (lives at about-me/index.html) → '../' + target.
    """
    if page_slug == "":
        return target
    depth = page_slug.count("/") + 1
    return ("../" * depth) + target

# --- CSS post-processing ----------------------------------------------------

CSS_URL_RE = re.compile(r"url\(\s*['\"]?([^)'\"]+)['\"]?\s*\)")

def process_css(css_text: str, source_url: str, downloaded: dict[str, str]) -> str:
    """Walk url(...) refs in a CSS file. Download each imcreator.com one and
    rewrite its reference to a relative path from the CSS file's location."""
    css_local_path = local_path_for(source_url)  # e.g. _imc/css/fonts.css
    css_dir_depth = css_local_path.count("/")    # how many dirs deep

    def repl(m):
        ref = m.group(1).strip()
        if ref.startswith("data:") or ref.startswith("#"):
            return m.group(0)
        abs_url = absolutize(ref, source_url)
        host = urlparse(abs_url).netloc.lower()
        if host in REMOTE_OK_HOSTS or (not is_localize(abs_url) and host):
            # Leave as-is
            return f"url({abs_url})"
        if not is_localize(abs_url):
            return m.group(0)  # unknown host, leave alone
        # Download & localize
        if abs_url not in downloaded:
            data = http_get(abs_url)
            if data is None:
                return m.group(0)
            target_local = local_path_for(abs_url)
            tp = MIRROR / target_local
            tp.parent.mkdir(parents=True, exist_ok=True)
            # If it's CSS, recurse on its url() refs
            if target_local.endswith(".css"):
                inner = data.decode("utf-8", errors="replace")
                inner = process_css(inner, abs_url, downloaded)
                tp.write_text(inner, encoding="utf-8")
            else:
                tp.write_bytes(data)
            downloaded[abs_url] = target_local
        target_local = downloaded[abs_url]
        # Build relative path from CSS file to asset
        rel = ("../" * (css_dir_depth)) + target_local
        return f"url({rel})"

    return CSS_URL_RE.sub(repl, css_text)

# --- Page processing --------------------------------------------------------

def process_page(slug: str, downloaded: dict[str, str]) -> bool:
    """Fetch a page, localize all assets, save HTML to mirror_v2/{slug}/index.html."""
    page_url = f"{BASE}/{slug}" if slug else BASE + "/"
    print(f"  · {slug or '(home)'}")
    raw = http_get(page_url)
    if raw is None:
        print(f"    !! could not fetch {page_url}", file=sys.stderr)
        return False

    soup = BeautifulSoup(raw, "lxml")

    # 1) Process <link rel="stylesheet">
    for link in soup.find_all("link"):
        href = link.get("href")
        if not href:
            continue
        rel = link.get("rel") or []
        if "stylesheet" not in rel and link.get("type") != "text/css":
            # Could be icon/apple-touch-icon — leave remote (Google CDN)
            abs_url = absolutize(href, page_url)
            host = urlparse(abs_url).netloc.lower()
            if host in REMOTE_OK_HOSTS:
                link["href"] = abs_url
            continue
        abs_url = absolutize(href, page_url)
        if not is_localize(abs_url):
            link["href"] = abs_url
            continue
        if abs_url not in downloaded:
            data = http_get(abs_url)
            if data is None:
                continue
            target_local = local_path_for(abs_url)
            tp = MIRROR / target_local
            tp.parent.mkdir(parents=True, exist_ok=True)
            css_text = data.decode("utf-8", errors="replace")
            css_text = process_css(css_text, abs_url, downloaded)
            tp.write_text(css_text, encoding="utf-8")
            downloaded[abs_url] = target_local
        link["href"] = relpath_from(slug, downloaded[abs_url])

    # 2) Process <script src="">
    for script in soup.find_all("script"):
        src = script.get("src")
        if not src:
            continue
        abs_url = absolutize(src, page_url)
        if not is_localize(abs_url):
            script["src"] = abs_url
            continue
        if abs_url not in downloaded:
            data = http_get(abs_url)
            if data is None:
                continue
            target_local = local_path_for(abs_url)
            tp = MIRROR / target_local
            tp.parent.mkdir(parents=True, exist_ok=True)
            tp.write_bytes(data)
            downloaded[abs_url] = target_local
        script["src"] = relpath_from(slug, downloaded[abs_url])

    # 3) Rewrite <a href="/foo"> → relative paths so site works under any base
    for a in soup.find_all("a"):
        href = a.get("href") or ""
        if href.startswith("/") and not href.startswith("//"):
            target = href.lstrip("/")
            if target == "" or target == "/":
                a["href"] = relpath_from(slug, "") or "./"
            else:
                # Preserve trailing slash convention
                a["href"] = relpath_from(slug, target.rstrip("/") + "/")

    # 4) Localize any data-img-url="//www.imcreator.com/..." (e.g. social icons
    #    that IM Creator's JS reads and renders as backgrounds at runtime).
    for el in soup.find_all(attrs={"data-img-url": True}):
        u = el["data-img-url"]
        abs_url = absolutize(u, page_url)
        if not is_localize(abs_url):
            continue
        if abs_url not in downloaded:
            data = http_get(abs_url)
            if data is None:
                continue
            target_local = local_path_for(abs_url)
            tp = MIRROR / target_local
            tp.parent.mkdir(parents=True, exist_ok=True)
            tp.write_bytes(data)
            downloaded[abs_url] = target_local
        el["data-img-url"] = relpath_from(slug, downloaded[abs_url])

    # 5) Rewrite remaining `//host/...` URLs on <img> tags to absolute http://
    for img in soup.find_all("img"):
        src = img.get("src") or ""
        if src.startswith("//"):
            img["src"] = "http:" + src

    # 5) Save
    out_dir = MIRROR if slug == "" else (MIRROR / slug)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(str(soup), encoding="utf-8")
    return True

# --- Main -------------------------------------------------------------------

def main():
    MIRROR.mkdir(parents=True, exist_ok=True)
    downloaded: dict[str, str] = {}
    print(f"Mirroring {len(PAGES)} pages from {BASE} → {MIRROR}/")
    ok = 0
    for slug in PAGES:
        if process_page(slug, downloaded):
            ok += 1
    print(f"\nDone. {ok}/{len(PAGES)} pages saved.")
    print(f"Localized assets: {len(downloaded)}")
    print(f"\nLocal preview:")
    print(f"  cd {MIRROR} && python3 -m http.server 8767")

if __name__ == "__main__":
    main()
