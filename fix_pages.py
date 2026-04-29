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
from bs4 import BeautifulSoup

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
/* Shrink IM Creator's logo image to exact 97x20 to match all other pages */
.left-div .preview-icon-holder img,
.logo-holder img,
#element-e325df23660bd16 {
  width: 97px !important;
  height: 20px !important;
  max-width: none !important;
}
/* Hide IM Creator's native footer-box — we inject our own consistent footer instead.
   Use a broad selector since the footer-box can be nested at varying depths. */
.footer-box, .item-content.footer { display: none !important; }

/* Style HOME / ABOUT nav links consistently with the captured pages */
.menu_layout a, .links-menu a, .header-box a, .stripe-header a {
  color: #111 !important;
  font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  text-decoration: none !important;
  letter-spacing: 0.5px !important;
  text-transform: uppercase !important;
}
.menu_layout a:hover, .links-menu a:hover, .header-box a:hover { opacity: 0.6; }
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
        f'style="position:absolute;top:32px;left:56px;z-index:50;display:block;text-decoration:none;">'
        f'<img src="{LOGO_URL}" alt="Ceci Chang" '
        f'style="width:97px;height:20px;display:block;">'
        f'</a>'
    )

    EMAIL_ICON = "https://lh3.googleusercontent.com/lXDKZBXBa_mQ0A-IrOjHdi9s79RAhEe7zhdTEuKpKGLXGde6iL2n46n2Zi4TVA9Daag9Z13s1dGTbsnAXg=s100"
    LINKEDIN_ICON = "https://lh3.googleusercontent.com/nJ0IsRDlfNRwXaO-ySLjDaIGgTW24qj6x5j0csqCgvEpaQGBPJJtU4qP83pmkOkcorVnLWAbkyJ_fELF=s100"

    # Standard footer HTML (used on homepage + all Wayback project pages — captured
    # pages have the same footer baked in by build_clean.py).
    FOOTER_HTML = (
        '<footer class="ceci-footer-inject" '
        'style="max-width:1100px;margin:80px auto 0;padding:32px 56px 64px;'
        'display:flex;justify-content:space-between;align-items:center;gap:24px;'
        'flex-wrap:wrap;font-family:\'Montserrat\',-apple-system,sans-serif;'
        'color:#666;font-size:14px;border-top:1px solid #eee;">'
        '<p style="margin:0;">Copyright © 2026 Ceci Chang. All rights reserved.</p>'
        '<div style="display:flex;gap:16px;align-items:center;">'
        f'<a href="mailto:changhsiju@gmail.com" aria-label="Email" style="display:block;line-height:0;">'
        f'<img src="{EMAIL_ICON}" alt="Email" style="width:24px;height:24px;display:block;opacity:0.85;">'
        '</a>'
        f'<a href="https://www.linkedin.com/in/changhsiju/" target="_blank" rel="noopener" aria-label="LinkedIn" style="display:block;line-height:0;">'
        f'<img src="{LINKEDIN_ICON}" alt="LinkedIn" style="width:24px;height:24px;display:block;opacity:0.85;">'
        '</a>'
        '</div>'
        '</footer>'
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

        # Inject Ceci Chang floating logo on every page EXCEPT the homepage and about-me
        # (homepage already has the image in its native IM Creator nav; about-me is
        # explicitly suppressed by user request).
        if slug is not None and slug != "about-me":
            soup_logo = BeautifulSoup(new_html, "lxml")
            # Strip all prior injects (any number of them)
            for old in soup_logo.find_all(class_="ceci-logo-inject"):
                old.decompose()
            # Insert fresh logo as the very first child of <body>
            if soup_logo.body:
                logo_tag = BeautifulSoup(LOGO_INJECT_HTML, "lxml").a
                soup_logo.body.insert(0, logo_tag)
                new_html = str(soup_logo)
        elif slug == "about-me":
            # Strip any prior injection (don't add a new one)
            soup_logo = BeautifulSoup(new_html, "lxml")
            removed = False
            for old in soup_logo.find_all(class_="ceci-logo-inject"):
                old.decompose(); removed = True
            if removed:
                new_html = str(soup_logo)

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

        # On about-me only: remove the broken inner-pic placeholder div
        # (it's an IM Creator empty image holder that renders as a gray block)
        if slug == "about-me":
            soup_apx = BeautifulSoup(new_html, "lxml")
            for el in soup_apx.find_all("div", id="no-image", class_="inner-pic"):
                el.decompose()
            # Also catch by class match alone in case id varies
            for el in soup_apx.find_all("div", class_="inner-pic"):
                if "preview-element" in (el.get("class") or []):
                    el.decompose()
            new_html = str(soup_apx)

        # On project pages (not homepage): remove the bottom HOME page-box,
        # add a "← Back to portfolio" link before the footer.
        if slug is not None:
            soup = BeautifulSoup(new_html, "lxml")

            # Remove last .page-box that contains only a single HOME link
            children_div = soup.find("div", id="children")
            if children_div:
                # iterate from the last direct child upward
                for child in reversed(list(children_div.find_all(recursive=False))):
                    cls = " ".join(child.get("class") or [])
                    if "page-box" not in cls:
                        continue
                    links = child.find_all("a")
                    text = child.get_text(strip=True).upper()
                    if links and text == "HOME":
                        child.decompose()
                    break  # stop after the first page-box we examined

            # Inject "Back to portfolio" link as a fixed/absolute element near bottom-left
            # but only if not already present
            if not soup.find(class_="back-to-portfolio-inject"):
                back_link = soup.new_tag("a", href="../",
                                          attrs={"class": "back-to-portfolio-inject",
                                                 "style": "display:block;max-width:1100px;margin:64px auto 32px;padding:0 56px;color:#111;text-decoration:none;font-family:'Montserrat',sans-serif;font-size:14px;font-weight:500;"})
                back_link.string = "← Back to portfolio"
                if soup.body:
                    soup.body.append(back_link)

            new_html = str(soup)

        # Inject the standard custom footer on EVERY page (homepage + Wayback project pages).
        # Re-parse with bs4 to drop any prior inject and append fresh.
        soup = BeautifulSoup(new_html, "lxml")
        for old_footer in soup.find_all(class_="ceci-footer-inject"):
            old_footer.decompose()
        if soup.body:
            footer_tag = BeautifulSoup(FOOTER_HTML, "lxml").footer
            soup.body.append(footer_tag)
            new_html = str(soup)

        if new_html != html:
            f.write_text(new_html)
            print(f"  ✓ {rel}  →  '{new_title}'")
        else:
            print(f"  · {rel} (unchanged)")

if __name__ == "__main__":
    main()
