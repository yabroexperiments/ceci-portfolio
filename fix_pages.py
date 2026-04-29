#!/usr/bin/env python3
"""Light fix pass for Wayback-fetched pages only:
  - Replace dead //xprs.imcreator.com with //www.imcreator.com (older Wayback pages)

That's it. Don't touch anything else — Wayback pages are already in working
post-render form. The 8 captured pages are handled by build_clean.py instead.
"""
import re
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
    # Inline override CSS:
    #   - body inline-block → block (so it fills viewport width)
    #   - unified typography across all old pages
    #     (3 levels: heading / body / description, mapped to IM Creator's preview-* classes)
    width_fix = """
<style data-portfolio-fix="1">
html, body { display: block !important; width: 100% !important; }
.master.container { width: auto !important; max-width: none !important; margin: 0 auto !important; }

/* === UNIFIED TYPOGRAPHY (3 levels) === */
/* Load Montserrat from Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

/* Level 1: Heading — covers IM Creator 1.5.x and 1.6.x naming */
.preview-title, .blocks-preview-title,
h1.preview-title, h2.preview-title, h2.blocks-preview-title {
  font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
  font-size: 36px !important; font-weight: 600 !important;
  color: #111 !important; line-height: 1.2 !important;
  letter-spacing: -0.01em !important;
}
/* Level 2: Body */
.preview-body, .blocks-preview-body,
.preview-body p, .blocks-preview-body p {
  font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
  font-size: 18px !important; font-weight: 400 !important;
  color: #333 !important; line-height: 1.7 !important;
}
/* Level 3: Description (captions/subtitles) */
.preview-subtitle, .blocks-preview-subtitle,
.preview-subtitle p, .blocks-preview-subtitle p {
  font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
  font-size: 15px !important; font-weight: 400 !important;
  color: #666 !important; line-height: 1.6 !important;
}
</style>
""".strip()

    for f in sorted(files):
        rel = f.relative_to(SITE)
        slug = rel.parts[0] if len(rel.parts) > 1 else None
        if slug in CAPTURED_SLUGS:
            print(f"  · {rel} (skipped — captured page)"); continue

        html = f.read_text(errors="replace")
        new_html = html.replace("//xprs.imcreator.com/", "//www.imcreator.com/")
        new_html = new_html.replace("xprs.imcreator.com/", "www.imcreator.com/")
        # Inject portfolio-fix CSS into <head> if not already present (idempotent)
        # Always strip old fix block first so updates take effect
        new_html = re.sub(
            r'<style data-portfolio-fix=[^>]*>.*?</style>',
            '', new_html, flags=re.DOTALL
        )
        new_html = new_html.replace("</head>", width_fix + "\n</head>", 1)

        if new_html != html:
            f.write_text(new_html)
            print(f"  ✓ {rel}")
        else:
            print(f"  · {rel} (unchanged)")

if __name__ == "__main__":
    main()
