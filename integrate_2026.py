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
}

FONT_LINKS_RE = re.compile(
    r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\s*\n'
    r'<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>\s*\n'
    r'<link href="https://fonts\.googleapis\.com/css2\?family=Inter[^"]*" rel="stylesheet">'
)
LOCAL_FONT_LINK = '<link href="assets/fonts/inter/inter.css" rel="stylesheet">'

IMG_REMAP = {  # referenced-but-missing filename -> file that holds that content
    "images/binance-leaderboard.png": "images/binance-03.png",
    "images/traderwagon.png": "images/binance-04.png",
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

    # --- images ---
    (SITE / "images").mkdir(exist_ok=True)
    copied = 0
    for img in sorted((SRC / "images").glob("*.png")):
        shutil.copy2(img, SITE / "images" / img.name)
        copied += 1
    print(f"images: copied {copied}")

    # --- i18n.js (with key remap) ---
    js = (SRC / "i18n.js").read_text(encoding="utf-8")
    for old, new in I18N_KEY_REMAP.items():
        js = js.replace(f"'{old}'", f"'{new}'")
    (SITE / "i18n.js").write_text(js, encoding="utf-8")
    print("i18n.js: copied, keys remapped:",
          ", ".join(f"{o}->{n}" for o, n in I18N_KEY_REMAP.items()))

    # --- pages ---
    for name, info in PAGES.items():
        page = (SRC / name).read_text(encoding="utf-8")

        page, n = FONT_LINKS_RE.subn(LOCAL_FONT_LINK, page)
        if n != 1:
            errors.append(f"{name}: expected exactly 1 Google-Fonts link block, replaced {n}")

        page, n = re.subn(r"(</title>)", r"\1" + meta_block(page, info), page, count=1)
        if n != 1:
            errors.append(f"{name}: could not inject meta after <title>")

        if name == "index.html":
            for old, new in IMG_REMAP.items():
                if old in page:
                    page = page.replace(old, new)
                else:
                    errors.append(f"{name}: expected reference {old} not found "
                                  "(Ceci may have fixed it — update IMG_REMAP)")

        (SITE / name).write_text(page, encoding="utf-8")
        print(f"{name}: written")

    # --- verify: every referenced local image exists ---
    missing = []
    for name in PAGES:
        page = (SITE / name).read_text(encoding="utf-8")
        for ref in sorted(set(re.findall(r'(?:src|href)="(images/[^"]+)"', page))):
            if not (SITE / ref).exists():
                missing.append(f"{name}: {ref}")
    known_missing = {"images/other-01.png", "images/other-02.png", "images/other-03.png"}
    real = [m for m in missing if m.split(": ")[1] not in known_missing]
    waived = [m for m in missing if m.split(": ")[1] in known_missing]
    if waived:
        print("missing images WAIVED by Albert 2026-08-11 (ship broken until Ceci exports):")
        for m in waived:
            print("  -", m)
    if real:
        errors.extend("missing image: " + m for m in real)

    # --- verify: no external requests left (fonts/CDNs) ---
    for name in PAGES:
        page = (SITE / name).read_text(encoding="utf-8")
        ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', page)
        bad = [u for u in ext if not (
            u.startswith(DOMAIN) or "linkedin.com" in u)]
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
