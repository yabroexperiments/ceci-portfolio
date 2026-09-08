#!/usr/bin/env python3
"""Integrate Ceci's "2026 portfolio/" drop into site/ (idempotent).

Source of truth for the new design = the HTML files Ceci exports into
"2026 portfolio/". This script copies them into site/ and applies ONLY the
integration patches that keep the site standalone and shareable — zero visual
changes:

  1. Google Fonts <link> tags  ->  self-hosted assets/fonts/inter/inter.css
  2. SEO/OG/Twitter meta + favicon injected after <title> (chat-app scrapers
     need absolute og:image URLs — see CLAUDE.md image rules)
  3. index.html: the About Me pill points at the preserved /about-me/ page
     (her export still says href="#about", a section that doesn't exist yet)
  4. ui-design.html: her absolute https://changhsiju.xyz/<slug>/ links are made
     relative so the page also works in local preview and on any future host
  5. i18n.js: dict keys renamed to match the data-i18n attributes in her HTML
     (card.wallet.* -> card.leaderboard.*, card.leader.* -> card.tw.*);
     the translations editor reads keys from i18n.js so the rename sticks

2026-09 drop note: Ceci now exports HTML through a formatter that reorders and
lowercases attributes and self-closes void tags (`<link href=... rel=.../>`).
Every patch below is therefore matched ATTRIBUTE-ORDER-AGNOSTICALLY. A patch
written against one particular attribute order is a silent no-op the next time
she re-exports.

Re-run any time Ceci delivers updated files. Fails loudly if any patch stops
matching (its cause is gone -> delete it) or any gate fails.
"""

import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "patches"))
from imgsize import image_size  # noqa: E402

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "2026 portfolio"
SITE = ROOT / "site"
DOMAIN = "https://changhsiju.xyz"
FAVICON = "assets/img/dd_e0xA19up9208Tv6odcjHEw6z4cKAA6fTgjZ9ynkKoSnr5R4vFxI7gZp6p-16acb57ca0.png"

# image file types Ceci ships; site/images is MIRRORED against these globs
IMAGE_GLOBS = ("*.png", "*.webp")

# 2026-09-08 (AC): serve the WebP twin wherever Ceci shipped one. Measured on
# her set: 49 usable twins, pixel dimensions identical to the PNG, SSIM 0.93-0.999
# / PSNR 37-52 dB, and indistinguishable from the PNG at 3x magnification — far
# beyond any size these are displayed at. Cuts what a visitor downloads across
# the case-study pages from 33.2 MB to 15.4 MB.
# The swap is conditional per image and gated below: a twin is used ONLY if it
# decodes and its dimensions match the PNG. bnct-app-05.webp arrived as a
# ZERO-BYTE file in her export (her conversion failed on that one), which is
# exactly what the gate exists to catch — it stays PNG.
# The PNGs stay deployed: og:image must remain PNG for chat-app scrapers, and
# they are the originals.
PREFER_WEBP = True

# Twins we KNOW are unusable, so they keep serving the PNG. Listed rather than
# silently skipped: an unlisted bad twin FAILS the build, and an entry here that
# has become healthy also fails, so this list cannot rot.
# Tell Ceci about these — they are bugs in her export, not in the site.
WEBP_SKIP = {
    "bnct-app-05.png": "her bnct-app-05.webp is a ZERO-BYTE file — the WebP "
                       "conversion failed for this one image",
}

PAGES = {
    "index.html": {
        "url": f"{DOMAIN}/",
        "desc": ("Ceci Chang — DeFi product & brand designer. Web3 product design "
                 "for Drift Protocol and Binance: Earn, Copy Trading, Futures, "
                 "growth and community experiences."),
        "og_image": f"{DOMAIN}/images/hero.png",
    },
    "drift-earn.html": {
        "url": f"{DOMAIN}/drift-earn.html",
        "desc": ("Led the end-to-end UI/UX design for the Drift Earn ecosystem, "
                 "including onboarding, deposits, borrowing, isolated pools, and "
                 "portfolio management experiences."),
        "og_image": f"{DOMAIN}/images/hero.png",
    },
    "drift-growth.html": {
        "url": f"{DOMAIN}/drift-growth.html",
        "desc": ("Product experiences, reward programs, and campaigns that "
                 "encouraged users to discover, participate in, and stay engaged "
                 "across the Drift ecosystem."),
        "og_image": f"{DOMAIN}/images/drift-growth.png",
    },
    "binance-copytrading.html": {
        "url": f"{DOMAIN}/binance-copytrading.html",
        "desc": ("Built the Binance Copy Trading platform from 0 to 1 as Design "
                 "Lead — app & web, end-to-end UX/UI, launched in 2 months."),
        "og_image": f"{DOMAIN}/images/bnct-hero.png",
    },
    "binance-futures.html": {
        "url": f"{DOMAIN}/binance-futures.html",
        "desc": ("Designed the Binance Futures Trading Platform — trading page "
                 "redesign, Battle game platform, Futures Wallet, and Binance "
                 "Convert."),
        "og_image": f"{DOMAIN}/images/bnf-hero.png",
    },
    "binance-leaderboard.html": {
        "url": f"{DOMAIN}/binance-leaderboard.html",
        "desc": ("The Futures Leaderboard ranks traders on Binance by ROI, PnL, "
                 "and popularity — turning individual performance into a public "
                 "signal that drives competition and trader discovery."),
        "og_image": f"{DOMAIN}/images/bnl-hero.png",
    },
    "traderwagon.html": {
        "url": f"{DOMAIN}/traderwagon.html",
        "desc": ("TraderWagon is a social crypto trading platform that helps "
                 "beginners find experienced traders and copy their trades — "
                 "design lead for the platform, design system, and the Binance "
                 "third-party app."),
        "og_image": f"{DOMAIN}/images/tw-hero.png",
    },
    # NEW 2026-09: the archive index that finally gives the 17 preserved
    # IM Creator project pages an entry point in the v2026 navigation.
    "ui-design.html": {
        "url": f"{DOMAIN}/ui-design.html",
        "desc": ("Selected interface and concept work from Ceci Chang's earlier "
                 "career (2011—2020) across fintech, mobile OS, smart devices, "
                 "and connected experiences — Coinful, iCard.AI, Acadine, "
                 "Mozilla, and HTC."),
        # deliberately a .png: some chat-app scrapers still refuse webp og:images
        "og_image": f"{DOMAIN}/images/hero.png",
    },
    # NEW 2026-09: the archive wrapper. ui-design.html's 17 cards point here
    # (?project=<key>); it renders the preserved IM Creator page inside the
    # v2026 nav + footer so a visitor never leaves the new site.
    "legacy-project.html": {
        "url": f"{DOMAIN}/legacy-project.html",
        "desc": ("Archived UI design project from Ceci Chang's earlier career "
                 "(2011—2020) — Coinful, iCard.AI, Acadine, Mozilla, and HTC."),
        "og_image": f"{DOMAIN}/images/hero.png",
    },
}

# Files in her export that are deliberately NOT deployed.
#
# coinful.html is a one-off wrapper for a single archive page. legacy-project.html
# now covers all 17 (including coinful) with coinful.html's own — better — restyle
# logic ported into it, so shipping coinful.html too would be a second URL for the
# same content. It also diverges structurally: its ids are portfolioNav /
# portfolioFooter, so the "shared navigation contract" CSS (scoped to nav#nav)
# does not apply to it, and its nav carries no data-i18n attributes. Kept in her
# source as the reference the ported logic came from.
STUBS = {
    "coinful.html": "one-off wrapper superseded by legacy-project.html?project=coinful",
}


# Attribute-order-agnostic match for the 3 Google-Fonts <link> tags.
FONT_LINKS_RE = re.compile(
    r'<link(?=[^>]*\bhref="https://fonts\.googleapis\.com")(?![^>]*css2)[^>]*>\s*'
    r'<link(?=[^>]*\bhref="https://fonts\.gstatic\.com")[^>]*>\s*'
    r'<link(?=[^>]*\bhref="https://fonts\.googleapis\.com/css2\?family=Inter)[^>]*>'
)
LOCAL_FONT_LINK = '<link href="assets/fonts/inter/inter.css" rel="stylesheet">'

# hosts a page may legitimately reference besides our own domain
EXTERNAL_ALLOW = ("linkedin.com", "apollox.finance", "hoyabit.com", "binance.com")

# Regex patches. Each MUST match at least once across the pages listed in
# `pages`, or its cause is gone and the entry has to be deleted — a
# re.sub() whose target vanished is a SILENT no-op.
PATCHES = [
    {
        # TEMPORARY (AC 2026-08-11): Ceci's About section doesn't exist yet, so
        # the homepage About Me pill points at the preserved old /about-me/
        # page. Remove once she ships the new About section.
        "name": "about-link -> about-me/",
        "pages": ["index.html"],
        "re": re.compile(r'<a\b[^>]*\bclass="about-link"[^>]*>'),
        "sub": lambda m: m.group(0).replace('href="#about"', 'href="about-me/"'),
        "expect": lambda before, after: 'href="#about"' in before,
    },
    {
        # BUGFIX 2026-09-08 (AC reported ui-design.html blank ON MOBILE; measured
        # on a real 375x812 viewport against production):
        # Her shared reveal snippet observes every .reveal block with
        #   IntersectionObserver(..., {threshold: .1})
        # i.e. "fire when 10% of this element is visible". That is unsatisfiable
        # for any element more than 10x the viewport height — 10% of it simply
        # does not fit on screen, so the observer NEVER fires at ANY scroll
        # position and the block stays at .reveal{opacity:0} forever.
        #   ui-design.html mobile grid = 8095px tall -> needs 810px visible
        #   iPhone Safari usable viewport ~660px      -> CAN NEVER FIRE
        #   desktop 3-column grid = ~3400px           -> needs 340px -> fine
        # That asymmetry is exactly why it renders on desktop and is blank on a
        # phone. ui-design.html is the first page to cross the line because its
        # 17 cards collapse to ONE column under 620px; it is also the only page
        # where .reveal wraps ALL the content, so the failure is a blank page
        # rather than one section that does not animate.
        # threshold:0 fires as soon as a single pixel is visible, which is
        # correct for any element size. Applied to every page so a future tall
        # section on a case study cannot hit this.
        "name": "reveal observer threshold .1 -> 0 (unsatisfiable on tall blocks)",
        "pages": ["index.html", "drift-earn.html", "drift-growth.html",
                  "binance-copytrading.html", "binance-futures.html",
                  "binance-leaderboard.html", "traderwagon.html", "ui-design.html"],
        "re": re.compile(r"\{threshold:\s*\.1\}"),
        "sub": lambda m: "{threshold:0}",
        "expect": lambda before, after: True,
    },
    {
        # Belt and braces for the same class of bug: an ENTRANCE animation must
        # never be able to leave content permanently invisible. If the observer
        # does not fire for any reason (unsupported, threshold maths, a throw
        # earlier in the script), reveal anything that is actually on screen.
        "name": "reveal failsafe (content can never stay invisible)",
        "pages": ["index.html", "drift-earn.html", "drift-growth.html",
                  "binance-copytrading.html", "binance-futures.html",
                  "binance-leaderboard.html", "traderwagon.html", "ui-design.html"],
        "re": re.compile(r"document\.querySelectorAll\('\.reveal'\)"
                         r"\.forEach\(el=>io\.observe\(el\)\);"),
        # Runs at DOMContentLoaded (immediately — a block already on screen has
        # nothing to animate INTO, so revealing it at once is also the correct
        # behaviour), again on rAF, and again after load. Gating this only on
        # 'load' was not enough: this page waits on 17 images, so the backstop
        # could arrive seconds late on a phone.
        "sub": lambda m: m.group(0) + (
            "var __reveal=function(){"
            "document.querySelectorAll('.reveal:not(.in)').forEach(function(el){"
            "var r=el.getBoundingClientRect();"
            "if(r.top<innerHeight&&r.bottom>0)el.classList.add('in');});};"
            "__reveal();"
            "requestAnimationFrame(__reveal);"
            "addEventListener('DOMContentLoaded',__reveal);"
            "addEventListener('load',function(){__reveal();setTimeout(__reveal,400);});"),
        "expect": lambda before, after: True,
    },
    {
        # BUGFIX 2026-09-08 (measured, not guessed): her new
        #   html{scrollbar-gutter:stable;overflow-y:scroll}
        # combines with the pre-existing body{overflow-x:hidden} (which computes
        # overflow-y:auto, making BODY a scroll container) to defeat the sticky
        # header. The nav's nearest scrolling ancestor becomes body, whose
        # scrollport never scrolls, so the nav scrolls away with the page.
        # Measured on this build: scroll 0->3000 gives navTop 0 -> -3000, while
        # production gives navTop 0 throughout. Isolated with a positive control
        # (html{overflow-y:visible} restores it; reverting re-breaks it).
        # Only index.html and ui-design.html carry the rule, so shipping it would
        # pin the nav on the 6 case pages and drop it on 2 — the opposite of her
        # own comment, "header stays pinned while scrolling".
        # scrollbar-gutter:stable is KEPT: it delivers the stable-gutter intent
        # on its own and is not what breaks sticky.
        # DELETE THIS once her export stops emitting overflow-y:scroll on html.
        "name": "drop html{overflow-y:scroll} (breaks the sticky nav)",
        "pages": ["index.html", "ui-design.html"],
        "re": re.compile(r"html\{([^}]*?)overflow-y:\s*scroll;?\s*([^}]*)\}"),
        "sub": lambda m: "html{" + (m.group(1) + m.group(2)).strip() + "}",
        "expect": lambda before, after: True,
    },
    {
        # NEW 2026-09: her ui-design.html links straight out to the bare
        # IM Creator pages, so the wrapper she built for exactly this is
        # unreachable. Route the cards through it instead.
        "name": "ui-design cards -> legacy-project.html wrapper",
        "pages": ["ui-design.html"],
        "re": re.compile(r'href="' + re.escape(DOMAIN) + r'/([a-z0-9][a-z0-9_-]*)/"'),
        "sub": lambda m: f'href="legacy-project.html?project={m.group(1)}"',
        "expect": lambda before, after: True,
    },
]

# --- archive wrapper rebuild (legacy-project.html) ---------------------------
# Her wrapper export ships a stripped nav (no data-i18n, dead EN/中 buttons, no
# i18n <script> tags) and a wrapper script with three measured defects. Both are
# replaced wholesale from files under patches/. If she ever reworks either, the
# anchors below stop matching and the build fails rather than silently keeping
# our version.
PATCH_DIR = ROOT / "patches"
WRAPPER_PAGE = "legacy-project.html"

I18N_KEY_REMAP = {
    "card.wallet.title": "card.leaderboard.title",
    "card.wallet.desc": "card.leaderboard.desc",
    "card.leader.title": "card.tw.title",
    "card.leader.desc": "card.tw.desc",
}


def swap_in_webp(page, site_dir):
    """Point <img src> at the WebP twin where one is usable. Returns
    (page, swapped, skipped) — skipped lists (name, why) so a bad twin is
    reported rather than silently left as PNG."""
    swapped, skipped = [], []

    def sub(m):
        ref = m.group(1)
        png, webp = site_dir / "images" / ref, site_dir / "images" / (ref[:-4] + ".webp")
        if not webp.exists():
            return m.group(0)
        why = None
        if webp.stat().st_size == 0:
            why = "WebP twin is a ZERO-BYTE file"
        else:
            dw, dp = image_size(webp), image_size(png)
            if dw is None:
                why = "WebP twin does not decode"
            elif dp is not None and dw != dp:
                why = (f"WebP twin is {dw[0]}x{dw[1]} but the PNG is "
                       f"{dp[0]}x{dp[1]} — not the same image")
        if why:
            skipped.append((ref, why))
            return m.group(0)
        if ref in WEBP_SKIP:
            skipped.append((ref, "listed in WEBP_SKIP but the twin is now HEALTHY "
                                 "— delete the entry so the WebP gets served"))
            return m.group(0)
        swapped.append(ref)
        return f'src="images/{ref[:-4]}.webp"'

    # src= only: og:image / twitter:image use content= and must stay PNG.
    page = re.sub(r'src="images/([^"]+\.png)"', sub, page)
    return page, swapped, skipped


def rebuild_wrapper(page, canonical_nav, wrapper_js):
    """Give legacy-project.html the same nav + i18n wiring as every other page,
    and swap in the fixed wrapper script. Returns (page, errors)."""
    errs = []

    # 1. canonical nav (hers has no data-i18n and inert EN/中 buttons)
    start, end = page.find("<nav"), page.find("</nav>")
    if start == -1 or end == -1:
        errs.append("no <nav> to replace")
    else:
        page = page[:start] + canonical_nav + page[end + len("</nav>"):]

    # 2. the wrapper script: her <script> containing the projects map
    m = re.search(r"<script(?![^>]*\bsrc=)[^>]*>(?:(?!</script>)[\s\S])*?"
                  r"projects\s*=\s*\{(?:(?!</script>)[\s\S])*?</script>", page)
    if not m:
        errs.append("wrapper <script> with the projects map not found — "
                    "she reworked it, review patches/legacy-wrapper.js")
    else:
        page = page[:m.start()] + "<script>\n" + wrapper_js + "\n</script>" + page[m.end():]

    # 3. Inter. Her wrapper declares font-family:'Inter' but ships no <link> of
    #    any kind, so its nav would fall back to the system stack while every
    #    other page renders in Inter.
    if LOCAL_FONT_LINK not in page:
        n = page.count("</title>")
        if n != 1:
            errs.append(f"expected exactly 1 </title> to inject the font link, found {n}")
        else:
            page = page.replace("</title>", "</title>\n" + LOCAL_FONT_LINK, 1)

    # 4. i18n dictionaries, so the wrapper's nav translates like every other page
    if 'src="i18n.js"' not in page:
        n = page.count("</body>")
        if n != 1:
            errs.append(f"expected exactly 1 </body> to inject i18n scripts, found {n}")
        else:
            page = page.replace(
                "</body>",
                '<script src="i18n.js"></script>\n'
                '<script src="i18n-cases.js"></script>\n</body>')
    return page, errs


def meta_block(page, info):
    title_m = re.search(r"<title>(.*?)</title>", page)
    title = title_m.group(1) if title_m else "Ceci Chang"
    d = info["desc"].replace('"', "&quot;")
    return f"""
<meta name="description" content="{d}">
<link rel="canonical" href="{info['url']}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Ceci Chang">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{info['url']}">
<meta property="og:image" content="{info['og_image']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{info['og_image']}">
<link href="{FAVICON}" rel="icon" type="image/png">
<link href="{FAVICON}" rel="apple-touch-icon">"""


def main():
    errors = []

    if not (SITE / "assets/fonts/inter/inter.css").exists():
        sys.exit("FATAL: site/assets/fonts/inter/inter.css missing — self-host Inter first")

    # --- stubs: verify they are still stubs before skipping them ---
    for name, why in STUBS.items():
        f = SRC / name
        if not f.exists():
            errors.append(f"STUBS lists {name} but it is gone from her export — delete the entry")
            continue
        html = f.read_text(encoding="utf-8")
        if "<iframe" not in html:
            errors.append(
                f"{name}: no longer an iframe wrapper — it was being SKIPPED as "
                f"'{why}'. Add it to PAGES or update STUBS.")
        else:
            print(f"{name}: NOT DEPLOYED — {why}")

    # --- images: MIRROR, not copy. A copy-only sync accumulates: a file Ceci
    # renames or drops would linger in site/ forever, still deployed. site/images
    # is owned entirely by this script, so anything not in her export is stale.
    (SITE / "images").mkdir(exist_ok=True)
    src_names = set()
    copied = 0
    for pat in IMAGE_GLOBS:
        for img in sorted((SRC / "images").glob(pat)):
            src_names.add(img.name)
            shutil.copy2(img, SITE / "images" / img.name)
            copied += 1
    site_names = set()
    for pat in IMAGE_GLOBS:
        site_names |= {p.name for p in (SITE / "images").glob(pat)}
    pruned = sorted(site_names - src_names)
    for name in pruned:
        (SITE / "images" / name).unlink()
    print(f"images: copied {copied}" +
          (f", PRUNED {len(pruned)} stale: {', '.join(pruned)}" if pruned else ""))

    # --- i18n dictionaries (key remap applies to i18n.js only) ---
    js = (SRC / "i18n.js").read_text(encoding="utf-8")
    remap_hits = 0
    for old, new in I18N_KEY_REMAP.items():
        n = js.count(f"'{old}'")
        remap_hits += n
        js = js.replace(f"'{old}'", f"'{new}'")
    if remap_hits == 0:
        errors.append("I18N_KEY_REMAP never matched — her i18n.js no longer uses "
                      "card.wallet.*/card.leader.*, delete the remap")
    (SITE / "i18n.js").write_text(js, encoding="utf-8")
    print(f"i18n.js: copied, {remap_hits} key(s) remapped:",
          ", ".join(f"{o}->{n}" for o, n in I18N_KEY_REMAP.items()))
    cases = SRC / "i18n-cases.js"
    if cases.exists():
        shutil.copy2(cases, SITE / "i18n-cases.js")
        print("i18n-cases.js: copied")
    elif (SITE / "i18n-cases.js").exists():
        errors.append("i18n-cases.js gone from source but pages may still "
                      "reference it — check <script> tags before removing")

    # --- pages ---
    canonical_nav = (PATCH_DIR / "canonical-nav.html").read_text(encoding="utf-8").strip()
    wrapper_js = (PATCH_DIR / "legacy-wrapper.js").read_text(encoding="utf-8").strip()

    patch_hits = {p["name"]: 0 for p in PATCHES}
    webp_swapped = {}
    for name, info in PAGES.items():
        page = (SRC / name).read_text(encoding="utf-8")

        if name == WRAPPER_PAGE:
            page, errs = rebuild_wrapper(page, canonical_nav, wrapper_js)
            errors.extend(f"{name}: {e}" for e in errs)

        page, n = FONT_LINKS_RE.subn(LOCAL_FONT_LINK, page)
        if n != 1 and LOCAL_FONT_LINK not in page:
            errors.append(f"{name}: expected exactly 1 Google-Fonts link block "
                          f"(or the local one already in place), replaced {n}")

        page, n = re.subn(r"(</title>)", r"\1" + meta_block(page, info), page, count=1)
        if n != 1:
            errors.append(f"{name}: could not inject meta after <title>")

        if PREFER_WEBP:
            page, sw, sk = swap_in_webp(page, SITE)
            webp_swapped[name] = sw
            for ref, why in sk:
                if ref in WEBP_SKIP and "now HEALTHY" not in why:
                    print(f"{name}: {ref} kept as PNG — {WEBP_SKIP[ref]}")
                else:
                    errors.append(f"{name}: {ref} — {why}")

        for p in PATCHES:
            if name not in p["pages"]:
                continue
            before = page
            page, n = p["re"].subn(p["sub"], page)
            if p["expect"](before, page) and before != page:
                patch_hits[p["name"]] += 1

        (SITE / name).write_text(page, encoding="utf-8")
        print(f"{name}: written")

    if PREFER_WEBP:
        total = sorted({r for v in webp_swapped.values() for r in v})
        before = sum((SITE / "images" / r).stat().st_size for r in total)
        after = sum((SITE / "images" / (r[:-4] + ".webp")).stat().st_size for r in total)
        if total:
            print(f"webp: serving {len(total)} image(s) as WebP instead of PNG "
                  f"({before // 1024} KB -> {after // 1024} KB, "
                  f"-{100 - after * 100 // before}% for those files)")
        for ref in WEBP_SKIP:
            if not (SITE / "images" / ref).exists():
                errors.append(f"WEBP_SKIP lists {ref} but that PNG is gone — "
                              "delete the entry")

    # --- retire pages that left her export ---
    stale_pages = sorted(
        p.name for p in SITE.glob("*.html")
        if p.name not in PAGES and (SRC / p.name).exists())
    for name in stale_pages:
        errors.append(f"site/{name} exists but is no longer in PAGES — "
                      "delete it or add it back")

    # --- verify: every patch still had something to patch ---
    # A regex sub whose target vanished is a SILENT no-op, so a workaround
    # outlives its cause invisibly. Every entry must match at least once or be
    # deliberately deleted. (2026-08-11: Ceci removed the About pill from the
    # case pages and that remap entry quietly stopped doing anything.
    # 2026-09-08: her new formatter reordered attributes and broke the literal
    # string form of both remaining patches — hence the regex rewrite.)
    for pname, hits in patch_hits.items():
        if hits == 0:
            errors.append(f"PATCH never matched — its cause is gone (or its "
                          f"pattern rotted), fix or delete it: {pname}")

    # --- verify: every data-i18n key a page asks for is actually defined ---
    # A missing key silently renders the English fallback, so a typo or a rename
    # only shows up as "that card won't translate". (Bit us with
    # card.leaderboard/card.tw on 2026-08-11.)
    dict_keys = set()
    for jsname in ("i18n.js", "i18n-cases.js"):
        f = SITE / jsname
        if f.exists():
            dict_keys |= set(re.findall(r"""['"]([\w.]+)['"]\s*:\s*\{\s*en:""",
                                        f.read_text(encoding="utf-8")))
    for name in PAGES:
        page = (SITE / name).read_text(encoding="utf-8")
        used = set(re.findall(r'data-i18n(?:-html)?="([^"]+)"', page))
        for k in sorted(used - dict_keys):
            errors.append(f"{name}: data-i18n key '{k}' has no entry in i18n.js "
                          "or i18n-cases.js (would silently fall back to English)")

    # --- verify: every referenced local image exists ---
    referenced = set()
    missing = []
    for name in PAGES:
        page = (SITE / name).read_text(encoding="utf-8")
        for ref in sorted(set(re.findall(r'(?:src|href|srcset)="(images/[^"]+)"', page))):
            referenced.add(ref.split("/", 1)[1])
            if not (SITE / ref).exists():
                missing.append(f"{name}: {ref}")
    if missing:
        errors.extend("missing image: " + m for m in missing)
    unreferenced = sorted(src_names - referenced)
    if unreferenced:
        print(f"images: {len(unreferenced)} shipped but referenced by no deployed page "
              f"(harmless, not served unless requested): "
              f"{', '.join(unreferenced[:6])}{' …' if len(unreferenced) > 6 else ''}")

    # --- verify: every same-site link resolves to something we deploy ---
    for name in PAGES:
        page = (SITE / name).read_text(encoding="utf-8")
        for href in sorted(set(re.findall(r'href="(?!https?:|mailto:|#)([^"]+)"', page))):
            target = href.split("#")[0].split("?")[0]
            if not target or target.startswith("images/") or target.startswith("assets/"):
                continue
            p = SITE / target
            if not (p.exists() or (p / "index.html").exists()):
                errors.append(f"{name}: dead internal link -> {href}")

    # --- verify: every ?project=<key> resolves ---
    # The dead-internal-link check above strips the query string, so a card
    # pointing at legacy-project.html?project=typo would pass it while silently
    # falling back to coinful at runtime. Check the key against the wrapper's own
    # projects map AND the directory it names.
    wrapper = (SITE / WRAPPER_PAGE).read_text(encoding="utf-8")
    known = dict(re.findall(r"'([\w-]+)':\s*\{\s*title:[^}]*?path:\s*'/([\w-]+)/'", wrapper))
    if len(known) != 17:
        errors.append(f"{WRAPPER_PAGE}: parsed {len(known)} projects from the wrapper "
                      "map, expected 17 — the map's shape changed")
    for name in PAGES:
        page = (SITE / name).read_text(encoding="utf-8")
        for key in sorted(set(re.findall(
                r'href="' + re.escape(WRAPPER_PAGE) + r'\?project=([^"&]+)"', page))):
            if key not in known:
                errors.append(f"{name}: ?project={key} is not in {WRAPPER_PAGE}'s "
                              "projects map (would silently fall back to coinful)")
            elif not (SITE / known[key] / "index.html").exists():
                errors.append(f"{WRAPPER_PAGE}: project '{key}' points at "
                              f"/{known[key]}/ which is not deployed")

    # --- verify: no external requests left (fonts/CDNs) ---
    for name in PAGES:
        page = (SITE / name).read_text(encoding="utf-8")
        ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', page)
        bad = [u for u in ext if not (
            u.startswith(DOMAIN) or any(h in u for h in EXTERNAL_ALLOW))]
        for u in bad:
            errors.append(f"{name}: external ref {u}")

    if errors:
        print("\nERRORS:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("\nOK — integration complete, all checks passed")


if __name__ == "__main__":
    main()
