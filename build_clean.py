#!/usr/bin/env python3
"""Extract content from each captured editor HTML and render via a clean template.

Output: site/<slug>/index.html — a simple, working case-study page.
"""
import re
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
CAPTURED = ROOT / "captured"
SITE = ROOT / "site"

PAGES = [
    ("vbid-3c96d052-qreqb1jd.html", "binance-leaderboard", "Binance Leaderboard"),
    ("vbid-cec78374-qreqb1jd.html", "binance-future-trading-platform", "Binance Future Trading Platform"),
    ("vbid-ddd17111-qreqb1jd.html", "traderwagon_platform", "TraderWagon Platform"),
    ("vbid-4e15ac70-e41s75dj.html", "traderwagon_mkt", "TraderWagon MKT"),
    ("vbid-39ecf264-lok1anrm.html", "icardai", "iCard.Ai"),
    ("vbid-fc78c7a5-pkv7u8oy.html", "bnct", "BNCT"),
    ("vbid-ac5cd3be-lok1anrm.html", "coinful", "Coinful"),
    ("vbid-3c197782-0lvtbbbh.html", "xxyz", "X.xyz"),
]

# CSS shared across project pages
SHARED_CSS = """
:root {
  --max: 1100px;
  --text: #111;
  --muted: #666;
  --bg: #fff;
  --accent: #f0c93c;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: var(--text);
  background: var(--bg);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
a { color: inherit; }

.page-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 28px 56px; max-width: var(--max); margin: 0 auto; width: 100%;
  font-size: 14px; letter-spacing: 0.5px;
}
.page-header .logo {
  font-size: 22px; font-weight: 600; text-decoration: none;
}
.page-header nav a {
  margin-left: 32px; text-decoration: none; text-transform: uppercase;
  font-weight: 500;
}
.page-header nav a:hover { opacity: 0.6; }

.project-hero {
  max-width: var(--max); margin: 64px auto 32px; padding: 0 56px;
}
.project-hero h1 {
  font-size: clamp(36px, 5vw, 64px); font-weight: 700; margin: 0 0 16px;
  letter-spacing: -0.02em;
}
.project-hero .meta { color: var(--muted); font-size: 14px; }

.content-section {
  max-width: var(--max); margin: 64px auto; padding: 0 56px;
}
.content-section h2 {
  font-size: 28px; font-weight: 600; margin: 0 0 12px;
  letter-spacing: -0.01em;
}
.content-section h3 {
  font-size: 18px; font-weight: 500; color: var(--muted);
  margin: 0 0 16px;
}
.content-section p {
  font-size: 16px; margin: 0 0 16px; max-width: 760px;
  white-space: pre-wrap;
}
.content-section .images {
  display: grid; gap: 16px; margin-top: 24px;
}
.content-section .images.cols-1 { grid-template-columns: 1fr; }
.content-section .images.cols-2 { grid-template-columns: repeat(2, 1fr); }
.content-section .images.cols-3 { grid-template-columns: repeat(3, 1fr); }
.content-section img {
  width: 100%; height: auto; display: block;
  border-radius: 4px;
}

.next-project {
  max-width: var(--max); margin: 96px auto 0; padding: 48px 56px;
  border-top: 1px solid #eee;
  display: flex; justify-content: space-between; align-items: center;
}
.next-project a {
  text-decoration: none; font-weight: 500;
}
.next-project a:hover { opacity: 0.6; }

.page-footer {
  max-width: var(--max); margin: 32px auto 0; padding: 24px 56px 64px;
  color: var(--muted); font-size: 13px;
}

@media (max-width: 768px) {
  .page-header, .project-hero, .content-section, .next-project, .page-footer {
    padding-left: 24px; padding-right: 24px;
  }
  .content-section .images.cols-2,
  .content-section .images.cols-3 { grid-template-columns: 1fr; }
}
"""


def extract_text(el):
    """Get text content with preserved line breaks."""
    if el is None: return ""
    text = el.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def extract_image_urls(section):
    """Yield Google CDN image URLs from <img src> and background-image styles."""
    seen = set()
    # img tags
    for img in section.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        if "googleusercontent" in src and src not in seen:
            seen.add(src); yield src
    # background-image styles
    for el in section.find_all(style=True):
        st = el.get("style", "")
        if "background-image" in st:
            for m in re.finditer(r'url\([\'"]?([^\'")]+)[\'"]?\)', st):
                u = m.group(1)
                if "googleusercontent" in u and u not in seen:
                    seen.add(u); yield u


def best_url(url):
    """Strip Google CDN size suffix (=s50, =s300) to get the highest-resolution version."""
    return re.sub(r"=s\d+(?:-c)?$", "=s2000", url)


def filter_decorative(image_urls, freq):
    """Drop URLs that appear 4+ times across the whole page (likely decorative bg)."""
    return [u for u in image_urls if freq[u] < 4]


def parse_section(section, all_image_freq):
    """Extract structured content from one IM Creator section div."""
    def has_class(el, name):
        cls = el.get("class") or []
        return name in cls if isinstance(cls, list) else name == cls

    titles = [el for el in section.find_all() if has_class(el, "preview-title")]
    subtitles = [el for el in section.find_all() if has_class(el, "preview-subtitle")]
    # Body text: preview-body class (NOT preview-body-holder)
    paragraphs = []
    for el in section.find_all():
        if has_class(el, "preview-body"):
            text = el.get_text("\n", strip=True)
            if text and len(text) > 2:
                paragraphs.append(text)

    # Fallback: any text directly inside the section that's not in a heading/title
    if not paragraphs and not titles and not subtitles:
        # Skip pure-image sections
        pass

    title_text = titles[0].get_text(" ", strip=True) if titles else ""
    subtitle_text = subtitles[0].get_text("\n", strip=True) if subtitles else ""

    # Images
    raw = list(extract_image_urls(section))
    images = filter_decorative(raw, all_image_freq)
    images = [best_url(u) for u in images]
    # Dedup keep order
    seen = set(); images_dedup = []
    for u in images:
        if u not in seen:
            seen.add(u); images_dedup.append(u)
    images = images_dedup

    return {
        "title": title_text,
        "subtitle": subtitle_text,
        "paragraphs": paragraphs,
        "images": images,
    }


def render_page(slug, project_title, sections):
    blocks = []
    for sec in sections:
        if not (sec["title"] or sec["subtitle"] or sec["paragraphs"] or sec["images"]):
            continue
        out = ['<section class="content-section">']
        if sec["title"]:
            out.append(f'  <h2>{escape_html(sec["title"])}</h2>')
        if sec["subtitle"]:
            out.append(f'  <h3>{escape_html(sec["subtitle"])}</h3>')
        for p in sec["paragraphs"]:
            out.append(f'  <p>{escape_html(p)}</p>')
        if sec["images"]:
            n = len(sec["images"])
            cols = 1 if n == 1 else (2 if n in (2, 4) else 3)
            out.append(f'  <div class="images cols-{cols}">')
            for u in sec["images"]:
                out.append(f'    <img src="{u}" loading="lazy" alt="">')
            out.append('  </div>')
        out.append('</section>')
        blocks.append("\n".join(out))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape_html(project_title)} - Ceci's Portfolio 2023</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap">
  <link rel="stylesheet" href="../assets/project.css">
</head>
<body>
  <header class="page-header">
    <a href="../" class="logo">Ceci Chang</a>
    <nav>
      <a href="../">HOME</a>
      <a href="../about-me/">ABOUT</a>
    </nav>
  </header>

  <div class="project-hero">
    <h1>{escape_html(project_title)}</h1>
  </div>

{chr(10).join(blocks)}

  <div class="next-project">
    <a href="../">← Back to portfolio</a>
  </div>

  <footer class="page-footer">
    <p>Copyright © 2023 Ceci Chang. All rights reserved.</p>
  </footer>
</body>
</html>
"""


def escape_html(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&#39;"))


def main():
    # Write shared CSS
    assets = SITE / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "project.css").write_text(SHARED_CSS)

    for fname, slug, title in PAGES:
        src_file = CAPTURED / fname
        if not src_file.exists():
            print(f"  ✗ MISSING: {fname}"); continue
        soup = BeautifulSoup(src_file.read_text(errors="replace"), "lxml")

        # Walk top-level sections
        children_div = soup.find("div", id="children")
        if not children_div:
            # fallback: look for .master directly
            master = soup.find("div", class_="master")
            children_div = master if master else None
        if not children_div:
            print(f"  ✗ NO CONTENT FOUND: {slug}"); continue

        sections = list(children_div.find_all(recursive=False))

        # Compute image-URL frequency across whole page (for decorative-image filter)
        all_imgs = []
        for sec in sections:
            all_imgs.extend(extract_image_urls(sec))
        freq = Counter(all_imgs)

        parsed = []
        for sec in sections:
            cls_str = " ".join(sec.get("class") or [])
            if "header-box" in cls_str or "footer-box" in cls_str:
                continue
            data = parse_section(sec, freq)
            parsed.append(data)

        html = render_page(slug, title, parsed)
        out_file = SITE / slug / "index.html"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html)
        n_sections_real = sum(1 for s in parsed if s["title"] or s["subtitle"] or s["paragraphs"] or s["images"])
        n_imgs = sum(len(s["images"]) for s in parsed)
        print(f"  ✓ {slug:<40} {n_sections_real} sections, {n_imgs} images, {len(html)//1024}KB")


if __name__ == "__main__":
    main()
