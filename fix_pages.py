#!/usr/bin/env python3
"""Light fix pass for Wayback-fetched pages only:
  - Replace dead //xprs.imcreator.com with //www.imcreator.com (older Wayback pages)
  - Inject width/typography override CSS
  - Inject SEO/OG meta tags for proper link previews on social/chat apps

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
    # Homepage-only overrides (selected by element id from the captured DOM)
    HOMEPAGE_OVERRIDES = """
/* Homepage: every preview-title shrunk to 20px */
.master .preview-title, .master .blocks-preview-title { font-size: 20px !important; }
/* Binance Leaderboard + Coinful sections: dark background, force white text */
#vbid-f2da5321-sfstatxx, #vbid-f2da5321-sfstatxx *,
#vbid-f2da5321-b9qvfnxw, #vbid-f2da5321-b9qvfnxw *,
#element-15ba1119c75b3ae, #element-15ba1119c75b3ae *,
#vbid-5512a7b7-b5hr0axu, #vbid-5512a7b7-b5hr0axu * {
  color: #fff !important;
}
/* Copyright line at the bottom — rendered as a preview-title; show at description size */
#vbid-739d6300-rqzcld5a { font-size: 14px !important; font-weight: 400 !important; color: #666 !important; }
"""

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
  font-size: 26px !important; font-weight: 600 !important;
  color: #111 !important; line-height: 1.3 !important;
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
  font-size: 14px !important; font-weight: 400 !important;
  color: #666 !important; line-height: 1.6 !important;
}
</style>
""".strip()

    SITE_URL = "https://changhsiju.xyz"
    DEFAULT_DESC = "Ceci Chang - Senior Product Designer / Design Lead"
    LOGO_URL = "https://lh3.googleusercontent.com/LpF5FkXmIWcEsH77dZ6Z_kV7Y3wLf3y3JQnx7r6TOuVkeypK_jDauMNjgFC-zLhwzd5dlRv82i7ifxBfaw=s260"

    # Floating Ceci Chang logo at top-left, links to homepage. Skipped on the homepage
    # (already has the image natively in IM Creator's nav).
    LOGO_INJECT_HTML = (
        f'<a class="ceci-logo-inject" href="../" aria-label="Ceci Chang home" '
        f'style="position:absolute;top:39px;left:68px;z-index:50;display:block;text-decoration:none;">'
        f'<img src="{LOGO_URL}" alt="Ceci Chang" '
        f'style="height:27px;width:auto;display:block;">'
        f'</a>'
    )

    def page_meta(slug, current_title):
        """Return (title, description) for a page slug."""
        if slug is None:  # homepage
            return ("Ceci Chang - Portfolio", DEFAULT_DESC)
        # Decode common HTML entities so the regex can strip the trailing site name
        t = current_title.replace("&#39;", "'").replace("&apos;", "'").replace("&amp;", "&")
        # Strip "Ceci's Portfolio 2023" / "Ceci.Chang Portfolio" / "Ceci Chang Portfolio" suffixes
        t = re.sub(r"\s*-?\s*Ceci(?:'s|\.Chang| Chang)?\s+Portfolio.*$", "", t, flags=re.I).strip()
        if not t:
            t = slug.replace("_", " ").replace("-", " ").title()
        return (f"{t} - Ceci Chang Portfolio", DEFAULT_DESC)

    for f in sorted(files):
        rel = f.relative_to(SITE)
        slug = rel.parts[0] if len(rel.parts) > 1 else None
        if slug in CAPTURED_SLUGS:
            print(f"  · {rel} (skipped — captured page)"); continue

        html = f.read_text(errors="replace")
        new_html = html.replace("//xprs.imcreator.com/", "//www.imcreator.com/")
        new_html = new_html.replace("xprs.imcreator.com/", "www.imcreator.com/")

        # Inject portfolio-fix CSS into <head> (idempotent — strip old block first)
        new_html = re.sub(
            r'<style data-portfolio-fix=[^>]*>.*?</style>',
            '', new_html, flags=re.DOTALL
        )
        # Homepage gets extra overrides
        css_to_inject = width_fix
        if slug is None:
            css_to_inject = width_fix.replace(
                "</style>",
                HOMEPAGE_OVERRIDES + "\n</style>"
            )
        new_html = new_html.replace("</head>", css_to_inject + "\n</head>", 1)

        # Inject Ceci Chang floating logo on every page EXCEPT the homepage
        # (homepage already has the image in its IM Creator-rendered nav).
        if slug is not None:
            # idempotent: strip any prior inject before re-adding
            new_html = re.sub(
                r'<a class="ceci-logo-inject"[^>]*>.*?</a>',
                '', new_html, flags=re.DOTALL
            )
            new_html = new_html.replace(
                "<body", LOGO_INJECT_HTML + "\n<body", 1
            ) if "<body" in new_html else new_html
            # Above injection puts logo BEFORE <body> tag — we actually want it INSIDE body.
            # Fix: move it just AFTER opening <body ...>
            new_html = re.sub(
                r'(<body[^>]*>)',
                lambda m: m.group(1) + "\n" + LOGO_INJECT_HTML,
                new_html.replace(LOGO_INJECT_HTML + "\n<body", "<body", 1),
                count=1
            )

        # --- Replace <title> and inject SEO/OG meta tags ---
        # Get current title for derivation
        title_m = re.search(r"<title[^>]*>(.*?)</title>", new_html, re.S | re.I)
        current_title = (title_m.group(1).strip() if title_m else "")
        new_title, new_desc = page_meta(slug, current_title)
        page_url = SITE_URL + ("/" if slug is None else f"/{slug}/")

        # Replace <title>
        new_html = re.sub(
            r"<title[^>]*>.*?</title>",
            f"<title>{new_title}</title>",
            new_html, count=1, flags=re.S | re.I
        )

        # Strip any existing portfolio-meta block, then inject fresh one
        new_html = re.sub(
            r'<!--portfolio-meta-->.*?<!--/portfolio-meta-->',
            '', new_html, flags=re.DOTALL
        )
        meta_block = f'''<!--portfolio-meta-->
<meta name="description" content="{new_desc}">
<meta property="og:type" content="website">
<meta property="og:title" content="{new_title}">
<meta property="og:description" content="{new_desc}">
<meta property="og:url" content="{page_url}">
<meta property="og:site_name" content="Ceci Chang Portfolio">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{new_title}">
<meta name="twitter:description" content="{new_desc}">
<link rel="canonical" href="{page_url}">
<!--/portfolio-meta-->'''
        new_html = new_html.replace("</head>", meta_block + "\n</head>", 1)

        if new_html != html:
            f.write_text(new_html)
            print(f"  ✓ {rel}  →  '{new_title}'")
        else:
            print(f"  · {rel} (unchanged)")

if __name__ == "__main__":
    main()
