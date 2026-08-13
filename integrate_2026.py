#!/usr/bin/env python3
"""Integrate Ceci's "2026 portfolio/" drop into site/ (idempotent).

Source of truth for the new design = the HTML files Ceci exports into
"2026 portfolio/". This script copies them into site/ and applies ONLY the
integration patches that keep the site standalone and shareable — zero visual
changes:

  1. Google Fonts <link> tags  ->  self-hosted assets/fonts/inter/inter.css
  2. SEO/OG/Twitter meta + favicon injected after <title> (chat-app scrapers
     need absolute og:image URLs — see CLAUDE.md image rules)
  3. index.html: two card images whose filenames don't exist in her export are
     mapped to the files that hold that content (binance-03/04, verified
     visually 2026-08-11)
  4. i18n.js: dict keys renamed to match the data-i18n attributes in her HTML
     (card.wallet.* -> card.leaderboard.*, card.leader.* -> card.tw.*);
     the translations editor reads keys from i18n.js so the rename sticks

Re-run any time Ceci delivers updated files. Fails loudly if the expected
font-link block is missing (layout changed -> review the patch list).
"""

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "2026 portfolio"
SITE = ROOT / "site"
DOMAIN = "https://changhsiju.xyz"
FAVICON = "assets/img/dd_e0xA19up9208Tv6odcjHEw6z4cKAA6fTgjZ9ynkKoSnr5R4vFxI7gZp6p-16acb57ca0.png"

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
}

FONT_LINKS_RE = re.compile(
    r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\s*\n'
    r'<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>\s*\n'
    r'<link href="https://fonts\.googleapis\.com/css2\?family=Inter[^"]*" rel="stylesheet">'
)
LOCAL_FONT_LINK = '<link href="assets/fonts/inter/inter.css" rel="stylesheet">'

# hosts a page may legitimately reference besides our own domain
EXTERNAL_ALLOW = ("linkedin.com", "apollox.finance", "hoyabit.com", "binance.com")

# TEMPORARY (AC 2026-08-11): Ceci's About section doesn't exist yet, so the
# homepage About Me link points at the preserved old /about-me/ page. Remove
# once she ships the new About section (nav.about -> #about again).
# (Her 2026-08-11 revision already removed the About pill from case pages.)
LINK_REMAP = {
    'href="#about" class="about-link"': 'href="about-me/" class="about-link"',
}

I18N_KEY_REMAP = {
    "card.wallet.title": "card.leaderboard.title",
    "card.wallet.desc": "card.leaderboard.desc",
    "card.leader.title": "card.tw.title",
    "card.leader.desc": "card.tw.desc",
}


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

    # --- images: MIRROR, not copy. A copy-only sync accumulates: a file Ceci
    # renames or drops would linger in site/ forever, still deployed. site/images
    # is owned entirely by this script, so anything not in her export is stale.
    (SITE / "images").mkdir(exist_ok=True)
    src_names = {img.name for img in (SRC / "images").glob("*.png")}
    copied = 0
    for img in sorted((SRC / "images").glob("*.png")):
        shutil.copy2(img, SITE / "images" / img.name)
        copied += 1
    pruned = [p.name for p in sorted((SITE / "images").glob("*.png"))
              if p.name not in src_names]
    for name in pruned:
        (SITE / "images" / name).unlink()
    print(f"images: copied {copied}" +
          (f", PRUNED {len(pruned)} stale: {', '.join(pruned)}" if pruned else ""))

    # --- i18n dictionaries (key remap applies to i18n.js only) ---
    js = (SRC / "i18n.js").read_text(encoding="utf-8")
    for old, new in I18N_KEY_REMAP.items():
        js = js.replace(f"'{old}'", f"'{new}'")
    (SITE / "i18n.js").write_text(js, encoding="utf-8")
    print("i18n.js: copied, keys remapped:",
          ", ".join(f"{o}->{n}" for o, n in I18N_KEY_REMAP.items()))
    cases = SRC / "i18n-cases.js"
    if cases.exists():
        shutil.copy2(cases, SITE / "i18n-cases.js")
        print("i18n-cases.js: copied")
    elif (SITE / "i18n-cases.js").exists():
        errors.append("i18n-cases.js gone from source but pages may still "
                      "reference it — check <script> tags before removing")

    # --- pages ---
    link_remap_hits = {k: 0 for k in LINK_REMAP}
    for name, info in PAGES.items():
        page = (SRC / name).read_text(encoding="utf-8")

        page, n = FONT_LINKS_RE.subn(LOCAL_FONT_LINK, page)
        if n != 1:
            errors.append(f"{name}: expected exactly 1 Google-Fonts link block, replaced {n}")

        page, n = re.subn(r"(</title>)", r"\1" + meta_block(page, info), page, count=1)
        if n != 1:
            errors.append(f"{name}: could not inject meta after <title>")

        for old, new in LINK_REMAP.items():
            if old in page:
                page = page.replace(old, new)
                link_remap_hits[old] += 1

        (SITE / name).write_text(page, encoding="utf-8")
        print(f"{name}: written")

    # --- verify: every patch still had something to patch ---
    # A str.replace() whose target vanished is a SILENT no-op, so a workaround
    # outlives its cause invisibly. Every entry must match at least once or be
    # deliberately deleted. (2026-08-11: Ceci removed the About pill from the
    # case pages and that remap entry quietly stopped doing anything.)
    for pat, hits in link_remap_hits.items():
        if hits == 0:
            errors.append(f"LINK_REMAP entry never matched — its cause is gone, "
                          f"delete it: {pat}")

    # --- verify: every data-i18n key a page asks for is actually defined ---
    # A missing key silently renders the English fallback, so a typo or a rename
    # only shows up as "that card won't translate". (Bit us with
    # card.leaderboard/card.tw on 2026-08-11.)
    dict_keys = set()
    for jsname in ("i18n.js", "i18n-cases.js"):
        f = SITE / jsname
        if f.exists():
            dict_keys |= set(re.findall(r"'([\w.]+)':\s*\{\s*en:", f.read_text(encoding="utf-8")))
    for name in PAGES:
        page = (SITE / name).read_text(encoding="utf-8")
        used = set(re.findall(r'data-i18n(?:-html)?="([^"]+)"', page))
        for k in sorted(used - dict_keys):
            errors.append(f"{name}: data-i18n key '{k}' has no entry in i18n.js "
                          "or i18n-cases.js (would silently fall back to English)")

    # --- verify: every referenced local image exists ---
    missing = []
    for name in PAGES:
        page = (SITE / name).read_text(encoding="utf-8")
        for ref in sorted(set(re.findall(r'(?:src|href)="(images/[^"]+)"', page))):
            if not (SITE / ref).exists():
                missing.append(f"{name}: {ref}")
    if missing:
        errors.extend("missing image: " + m for m in missing)

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
