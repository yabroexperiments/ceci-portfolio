#!/usr/bin/env python3
"""Extract content from each captured editor HTML and render via a clean template.

Layout per page:
  - Top-left floating "Ceci Chang" logo
  - Full-width hero image (first real big content image)
  - Brand + title + description intro section
  - Body sections (subtitles, paragraphs, image grids)
  - "Back to portfolio" + footer
  - Sticky nav that slides in on scroll past the hero
"""
import re
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
CAPTURED = ROOT / "captured"
SITE = ROOT / "site"

PAGES = [
    ("vbid-3c96d052-qreqb1jd.html", "binance-leaderboard", "Social Trading Leaderboard Design", "BINANCE"),
    ("vbid-cec78374-qreqb1jd.html", "binance-future-trading-platform", "Future Trading Platform", "BINANCE"),
    ("vbid-ddd17111-qreqb1jd.html", "traderwagon_platform", "TraderWagon Platform", "TRADERWAGON"),
    ("vbid-4e15ac70-e41s75dj.html", "traderwagon_mkt", "Social Trading Marketing Design", "TRADERWAGON"),
    ("vbid-39ecf264-lok1anrm.html", "icardai", "iCard.Ai", "ICARD.AI"),
    ("vbid-fc78c7a5-pkv7u8oy.html", "bnct", "Copy Trading App & Web Design", "BINANCE"),
    ("vbid-ac5cd3be-lok1anrm.html", "coinful", "Coinful", "COINFUL"),
    ("vbid-3c197782-0lvtbbbh.html", "xxyz", "X.xyz", "X.XYZ"),
]

SHARED_CSS = """
:root {
  --max: 1100px;
  --text: #111;
  --muted: #666;
  --bg: #fff;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: var(--text); background: var(--bg);
  line-height: 1.6; -webkit-font-smoothing: antialiased;
}
a { color: inherit; }

.floating-logo {
  position: absolute;
  top: 28px; left: 56px;
  z-index: 5;
  font-size: 22px; font-weight: 600;
}
.floating-logo a { text-decoration: none; }

.page-nav {
  position: fixed;
  top: 0; left: 0; right: 0;
  background: rgba(255,255,255,0.96);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  padding: 18px 56px;
  display: flex; justify-content: space-between; align-items: center;
  transform: translateY(-100%);
  transition: transform 0.3s ease;
  z-index: 100;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}
.page-nav.visible { transform: translateY(0); }
.page-nav .logo {
  font-size: 22px; font-weight: 600; text-decoration: none;
}
.page-nav nav a {
  margin-left: 32px; text-decoration: none; text-transform: uppercase;
  font-weight: 500; font-size: 14px; letter-spacing: 0.5px;
}
.page-nav nav a:hover { opacity: 0.6; }

.hero {
  width: 100%;
  height: 66.67vh;
  background: #f8f8f8;
  overflow: hidden;
  display: flex; align-items: center; justify-content: center;
}
.hero img {
  width: 100%; height: 100%; object-fit: cover; display: block;
}

.project-intro {
  max-width: var(--max); margin: 96px auto 64px;
  padding: 0 56px; text-align: center;
}
.project-intro .brand {
  font-size: 14px; font-weight: 700;
  color: var(--text); letter-spacing: 0.2em;
  margin: 0 0 16px;
}

/* === UNIFIED TYPOGRAPHY (3 levels) === */
/* Level 1: Heading — used for project title + every section title */
.project-intro .title,
.content-section h2 {
  font-size: 36px; font-weight: 600;
  color: var(--text); line-height: 1.2;
  letter-spacing: -0.01em;
  margin: 0 0 24px;
}
/* Level 2: Body — used for project description + section paragraphs */
.project-intro .description,
.content-section p {
  font-size: 18px; font-weight: 400;
  color: #333; line-height: 1.7;
  margin: 0 0 16px;
  max-width: 760px;
  white-space: pre-wrap;
}
.project-intro .description { max-width: 720px; margin: 0 auto; }
/* Level 3: Description — used for image captions / subtitles */
.content-section h3,
.content-section .description {
  font-size: 15px; font-weight: 400;
  color: var(--muted); line-height: 1.6;
  margin: 0 0 16px;
}

.content-section {
  max-width: var(--max); margin: 64px auto;
  padding: 0 56px;
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
  max-width: var(--max); margin: 96px auto 0;
  padding: 48px 56px;
  border-top: 1px solid #eee;
  display: flex; justify-content: space-between; align-items: center;
}
.next-project a { text-decoration: none; font-weight: 500; }
.next-project a:hover { opacity: 0.6; }

.page-footer {
  max-width: var(--max); margin: 32px auto 0;
  padding: 24px 56px 64px;
  color: var(--muted); font-size: 13px;
  display: flex; justify-content: space-between; align-items: center;
  gap: 24px; flex-wrap: wrap;
}
.page-footer .socials {
  display: flex; gap: 20px;
}
.page-footer .socials a {
  text-decoration: none; color: var(--text);
  font-weight: 500;
}
.page-footer .socials a:hover { opacity: 0.6; }
.page-footer .copyright { margin: 0; }

@media (max-width: 768px) {
  .floating-logo { top: 20px; left: 24px; }
  .page-nav { padding: 14px 24px; }
  .page-nav nav a { margin-left: 16px; }
  .project-intro, .content-section, .next-project, .page-footer {
    padding-left: 24px; padding-right: 24px;
  }
  .hero { height: 50vh; }
  .content-section .images.cols-2,
  .content-section .images.cols-3 { grid-template-columns: 1fr; }
}
"""

NAV_SCRIPT = """
(function() {
  var nav = document.querySelector('.page-nav');
  var hero = document.querySelector('.hero');
  if (!nav || !hero) return;
  var threshold = function() { return hero.offsetHeight * 0.6; };
  var onScroll = function() {
    if (window.scrollY > threshold()) nav.classList.add('visible');
    else nav.classList.remove('visible');
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();
"""


def has_class(el, name):
    cls = el.get("class") or []
    return name in cls if isinstance(cls, list) else name == cls


def extract_text(el):
    if el is None: return ""
    text = el.get_text("\n", strip=True)
    return re.sub(r"\n{3,}", "\n\n", text)


def url_size_hint(u):
    """Return Google CDN size hint as int (=s300 → 300, full → 9999)."""
    m = re.search(r"=s(\d+)(?:-c)?$", u)
    return int(m.group(1)) if m else 9999


def url_stem(u):
    return re.sub(r"=s\d+(?:-c)?$", "", u)


def best_url(u):
    """Strip size suffix and request large version."""
    return re.sub(r"=s\d+(?:-c)?$", "=s2000", u)


def extract_all_image_urls(section):
    """Yield (url, size_hint) tuples from <img src>, data-src, and background-image."""
    for img in section.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        if "googleusercontent" in src:
            yield src, url_size_hint(src)
    for el in section.find_all(style=True):
        st = el.get("style", "")
        if "background-image" in st:
            for m in re.finditer(r'url\([\'"]?([^\'")]+)[\'"]?\)', st):
                u = m.group(1)
                if "googleusercontent" in u:
                    yield u, url_size_hint(u)


def filter_real_content_images(image_pairs, stem_freq):
    """Drop icons (size <100), drop URLs that repeat 3+ times across page (decorative)."""
    out = []
    seen = set()
    for u, sz in image_pairs:
        if sz < 100:  # icons / social media buttons
            continue
        s = url_stem(u)
        if stem_freq[s] >= 3:  # repeated decoration
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(best_url(u))
    return out


def parse_section(section, stem_freq):
    titles = [el for el in section.find_all() if has_class(el, "preview-title")]
    subtitles = [el for el in section.find_all() if has_class(el, "preview-subtitle")]
    paragraphs = []
    for el in section.find_all():
        if has_class(el, "preview-body"):
            text = el.get_text("\n", strip=True)
            if text and len(text) > 2:
                paragraphs.append(text)

    title_text = titles[0].get_text(" ", strip=True) if titles else ""
    subtitle_text = subtitles[0].get_text("\n", strip=True) if subtitles else ""

    images = filter_real_content_images(list(extract_all_image_urls(section)), stem_freq)

    return {
        "title": title_text,
        "subtitle": subtitle_text,
        "paragraphs": paragraphs,
        "images": images,
    }


def escape_html(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&#39;"))


def render_page(slug, project_title, brand, sections, hero_url):
    # Build content section blocks (skip empty)
    blocks = []
    intro_used = False
    intro_title = ""
    intro_description = ""

    for sec in sections:
        if not (sec["title"] or sec["subtitle"] or sec["paragraphs"] or sec["images"]):
            continue

        # Use the first section that has BOTH title AND paragraph as the intro
        # (typically section 1 of the captured page: project name + tagline)
        if not intro_used and sec["title"] and sec["paragraphs"]:
            intro_title = sec["title"]
            intro_description = sec["paragraphs"][0]
            intro_used = True
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

    # Fallback intro if no section had title+paragraph
    if not intro_used:
        intro_title = project_title

    hero_html = f'<div class="hero"><img src="{hero_url}" alt="" loading="eager"></div>' if hero_url else ""

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
  <div class="floating-logo"><a href="../">Ceci Chang</a></div>

  <header class="page-nav">
    <a href="../" class="logo">Ceci Chang</a>
    <nav>
      <a href="../">HOME</a>
      <a href="../about-me/">ABOUT</a>
    </nav>
  </header>

  {hero_html}

  <section class="project-intro">
    <p class="brand">{escape_html(brand)}</p>
    <h1 class="title">{escape_html(intro_title)}</h1>
    {('<p class="description">' + escape_html(intro_description) + '</p>') if intro_description else ''}
  </section>

{chr(10).join(blocks)}

  <div class="next-project">
    <a href="../">← Back to portfolio</a>
  </div>

  <footer class="page-footer">
    <p class="copyright">Copyright © 2023 Ceci Chang. All rights reserved.</p>
    <div class="socials">
      <a href="https://www.linkedin.com/in/changhsiju/" target="_blank" rel="noopener">LinkedIn</a>
      <a href="mailto:changhsiju@gmail.com">Email</a>
    </div>
  </footer>

  <script>{NAV_SCRIPT}</script>
</body>
</html>
"""


def find_hero(sections, stem_freq):
    """Pick the first big content image across all sections — preferring =s1600 or larger originals."""
    # Pass 1: find a =s1600+ image
    for sec in sections:
        for u, sz in extract_all_image_urls(sec):
            if sz >= 1000 and stem_freq[url_stem(u)] < 3:
                return best_url(u)
    # Pass 2: any non-decorative image >= 200
    for sec in sections:
        for u, sz in extract_all_image_urls(sec):
            if sz >= 200 and stem_freq[url_stem(u)] < 3:
                return best_url(u)
    return None


def main():
    assets = SITE / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "project.css").write_text(SHARED_CSS)

    for fname, slug, title, brand in PAGES:
        src_file = CAPTURED / fname
        if not src_file.exists():
            print(f"  ✗ MISSING: {fname}"); continue
        soup = BeautifulSoup(src_file.read_text(errors="replace"), "lxml")

        children_div = soup.find("div", id="children") or soup.find("div", class_="master")
        if not children_div:
            print(f"  ✗ NO CONTENT: {slug}"); continue

        sections = list(children_div.find_all(recursive=False))

        # Build stem-frequency map across the whole page (for decorative-image filter)
        all_pairs = []
        for sec in sections:
            all_pairs.extend(extract_all_image_urls(sec))
        stem_freq = Counter(url_stem(u) for u, _ in all_pairs)

        # Pick hero before stripping header/footer
        hero = find_hero(sections, stem_freq)

        parsed = []
        for sec in sections:
            cls_str = " ".join(sec.get("class") or [])
            if "header-box" in cls_str or "footer-box" in cls_str:
                continue
            parsed.append(parse_section(sec, stem_freq))

        # Drop the hero image from any section that references it (so it's not duplicated)
        if hero:
            hero_stem = url_stem(re.sub(r"=s\d+(?:-c)?$", "", hero))
            for sec in parsed:
                sec["images"] = [u for u in sec["images"] if url_stem(u) != hero_stem]

        html = render_page(slug, title, brand, parsed, hero)
        out_file = SITE / slug / "index.html"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html)
        n_imgs = sum(len(s["images"]) for s in parsed)
        print(f"  ✓ {slug:<40} hero={'Y' if hero else 'N'}, {n_imgs} content images")


if __name__ == "__main__":
    main()
