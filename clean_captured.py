#!/usr/bin/env python3
"""Clean editor chrome out of the 8 captured pages and write them to site/."""
import sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
CAPTURED = ROOT / "captured"
SITE = ROOT / "site"

PAGES = {
    "vbid-3c96d052-qreqb1jd.html": ("binance-leaderboard", "Binance Leaderboard"),
    "vbid-cec78374-qreqb1jd.html": ("binance-future-trading-platform", "Binance Future Trading Platform"),
    "vbid-ddd17111-qreqb1jd.html": ("traderwagon_platform", "TraderWagon Platform"),
    "vbid-4e15ac70-e41s75dj.html":  ("traderwagon_mkt", "TraderWagon MKT"),
    "vbid-39ecf264-lok1anrm.html": ("icardai", "iCard.Ai"),
    "vbid-fc78c7a5-pkv7u8oy.html": ("bnct", "BNCT"),
    "vbid-ac5cd3be-lok1anrm.html": ("coinful", "Coinful"),
    "vbid-3c197782-0lvtbbbh.html": ("xxyz", "X.xyz"),
}

# Top-level body div first-class names to strip entirely (with full subtree)
REMOVE_FIRST_CLASS = {
    "page-loader", "control-panel-holder", "welcome-popup", "publish-ui",
    "publish-module", "module-back", "module-ui", "module-iframe-wrapper",
    "iframe-loader", "user-menu-btn", "translation-box", "part-of-dropdown",
    "user-nickname", "editor-logo", "save-status", "edit-bar", "edit-toolbar",
    "settings-module", "spell-check-module", "imos-module",
    "im-shop-module", "shop-module-iframe-wrapper",
    "module", "loader", "tooltip", "drop-overlay", "color-picker",
    "image-uploader", "lightbox-display",
}
# IDs to strip
REMOVE_IDS = {
    "control-panel", "control-panel-holder", "save-button-tooltip",
    "publish-module", "settings-module", "module-back",
}

# Top-level div first-class prefixes that mean "step1, step2, step20, …" → strip
REMOVE_FIRST_CLASS_PREFIXES = ("step",)

def is_editor_top_div(tag):
    if tag.name not in ("div", "section", "noscript", "iframe"):
        return False
    if tag.has_attr("id") and tag["id"] in REMOVE_IDS:
        return True
    if tag.has_attr("class"):
        cls = tag["class"]
        if not cls: return False
        first = cls[0]
        if first in REMOVE_FIRST_CLASS:
            return True
        if any(first.startswith(p) for p in REMOVE_FIRST_CLASS_PREFIXES):
            return True
    if tag.name == "noscript":
        return True
    if tag.name == "iframe":
        src = tag.get("src", "")
        if any(s in src for s in ("intercom", "hotjar", "google-analytics", "googletagmanager", "pinterest")):
            return True
    return False

def clean(html, title):
    soup = BeautifulSoup(html, "lxml")

    # 1. Replace title
    if soup.title:
        soup.title.string = f"{title} - Ceci's Portfolio 2023"

    # 2. Remove robots noindex meta (we want this site indexed once deployed)
    for m in soup.find_all("meta", attrs={"name": "robots"}):
        m.decompose()

    # 3. Remove tracking script tags
    for s in soup.find_all("script"):
        src = s.get("src", "") or ""
        if any(p in src for p in ("intercom", "hotjar", "googletagmanager", "google-analytics",
                                  "pinterest", "shoprocket", "appspot.com")):
            s.decompose()

    # 4. From body: keep ONLY the xprs portfolio container; drop everything else
    if soup.body:
        xprs = soup.body.find("div", id="xprs") or soup.body.find("div", class_="xprs-holder") or soup.body.find("div", class_="xprs")
        for child in list(soup.body.children):
            if hasattr(child, "name") and child.name and child is not xprs:
                child.decompose()

        # Switch body data attrs from editor-mode to live-mode
        if soup.body.get("data-caller") in ("dual", "editor", "edit"):
            soup.body["data-caller"] = "live"
        # Strip "-no-viewer" suffix from app-version (which disables the runtime)
        ver = soup.body.get("data-app-version", "")
        if "-no-viewer" in ver:
            soup.body["data-app-version"] = ver.replace("-no-viewer", "")
        # Editor-only data attrs to drop
        for attr in ("data-ecommerce-dashboard",):
            if soup.body.has_attr(attr):
                del soup.body.attrs[attr]
        # Strip editor-only classes from body
        if soup.body.has_attr("class"):
            soup.body["class"] = [c for c in soup.body["class"] if c not in ("blockfreeurl",)]

        if xprs:
            # Strip editor mode classes
            if xprs.has_attr("class"):
                xprs["class"] = [c for c in xprs["class"] if c not in ("in-editor", "phone-mode", "tablet-mode", "desktop-mode")]
            # Strip "disable_effects" from main-page
            for mp in xprs.find_all("div", class_="main-page"):
                if mp.has_attr("class"):
                    mp["class"] = [c for c in mp["class"] if c != "disable_effects"]

    return str(soup)

def main():
    if not CAPTURED.is_dir():
        print(f"FATAL: {CAPTURED} not found"); sys.exit(1)

    for fname, (slug, title) in PAGES.items():
        src = CAPTURED / fname
        if not src.exists():
            print(f"  ✗ MISSING source: {fname}"); continue
        raw = src.read_text(errors="replace")
        cleaned = clean(raw, title)
        target = SITE / slug / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(cleaned)
        print(f"  ✓ {slug:<35} {len(raw)//1024}KB → {len(cleaned)//1024}KB  ({title})")

if __name__ == "__main__":
    main()
