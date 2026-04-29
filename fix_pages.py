#!/usr/bin/env python3
"""Light fix pass for Wayback-fetched pages only:
  - Replace dead //xprs.imcreator.com with //www.imcreator.com (older Wayback pages)

That's it. Don't touch anything else — Wayback pages are already in working
post-render form. The 8 captured pages are handled by build_clean.py instead.
"""
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"

# Slugs handled by build_clean.py — skip those here
CAPTURED_SLUGS = {
    "binance-leaderboard", "binance-future-trading-platform",
    "traderwagon_platform", "traderwagon_mkt",
    "icardai", "bnct", "coinful", "xxyz",
}

def main():
    files = list(SITE.rglob("*.html"))
    print(f"Fixing {len(files)} HTML files…")
    for f in sorted(files):
        rel = f.relative_to(SITE)
        slug = rel.parts[0] if len(rel.parts) > 1 else None
        if slug in CAPTURED_SLUGS:
            print(f"  · {rel} (skipped — captured page)"); continue

        html = f.read_text(errors="replace")
        new_html = html.replace("//xprs.imcreator.com/", "//www.imcreator.com/")
        new_html = new_html.replace("xprs.imcreator.com/", "www.imcreator.com/")
        if new_html != html:
            f.write_text(new_html)
            print(f"  ✓ {rel} (host fixed)")
        else:
            print(f"  · {rel} (unchanged)")

if __name__ == "__main__":
    main()
