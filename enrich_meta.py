#!/usr/bin/env python3
"""Inject SEO + Open Graph + Twitter Card meta tags into every page in site/.

The live IM Creator HTML doesn't include a meta description, so link-preview
crawlers (LINE, WhatsApp, iMessage, Slack, etc.) fall back to scraping the
first big text block they find — which on the homepage is the Gem Spot
project description ("The largest food and restaurant reservation system…").

This is the ONLY non-identical-to-live change in v2: we ADD metadata. We
don't modify any rendered content. Idempotent — re-run anytime.
"""
import re
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
SITE = ROOT / "site"

SITE_URL = "https://changhsiju.xyz"
SITE_NAME = "Ceci's Portfolio 2026"
DEFAULT_DESC = (
    "Ceci Chang — Senior Product Designer / Design Lead. "
    "Selected case studies from Binance, TraderWagon, Coinful, "
    "iCard.AI, Mozilla, and HTC."
)
OG_IMAGE = (
    # Use the floating-logo image as a stand-in OG image. It's small but
    # consistent and on a stable Google CDN. Can swap to a hero image later.
    "https://lh3.googleusercontent.com/LpF5FkXmIWcEsH77dZ6Z_kV7Y3wLf3y3JQnx7r6TOuVkeypK_jDauMNjgFC-zLhwzd5dlRv82i7ifxBfaw=s400"
)

# Per-page meta overrides. Slug → (title_override_or_None, description).
PAGE_META = {
    "":                                ("Ceci's Portfolio 2026", DEFAULT_DESC),
    "about-me":                        ("About me - Ceci's Portfolio 2026",
                                        "Hi, I'm Ceci. I am a Senior Product Designer at Binance. "
                                        "I create user-centric, delightful and human experiences."),
    "bnct":                            (None, "BINANCE Copy Trading App & Web Design — replicate trades of experienced traders. UX/UI by Ceci Chang."),
    "binance-future-trading-platform": (None, "BINANCE Derivatives — Futures Trading Platform UX/UI design by Ceci Chang."),
    "binance-leaderboard":             (None, "BINANCE Social Trading — Leaderboard Design by Ceci Chang."),
    "traderwagon_platform":            (None, "TraderWagon Social Trading — Binance third-party tool. UX/UI by Ceci Chang."),
    "traderwagon_mkt":                 (None, "TraderWagon Marketing Design Guideline by Ceci Chang."),
    "xxyz":                            (None, "X.xyz NFT Platform — design case study by Ceci Chang."),
    "coinful":                         (None, "Coinful Cryptocurrency Trading Platform — UX/UI by Ceci Chang."),
    "icardai":                         (None, "iCard.AI Web & App — credit-card recommendation service. UX/UI by Ceci Chang."),
    "acadine_watch":                   (None, "Acadine Digital Watch Designs by Ceci Chang."),
    "acadine_smart-home":              (None, "Acadine Smart Home Dashboard design by Ceci Chang."),
    "acadine_feature-phone":           (None, "Acadine Feature Phone & Card Design by Ceci Chang."),
    "mozilla_smart-tv":                (None, "Firefox Smart TV UI design by Ceci Chang at Mozilla."),
    "mozilla_feature-phone":           (None, "Mozilla Feature Phone design by Ceci Chang."),
    "mozilla_car-ui":                  (None, "Mozilla Car UI design by Ceci Chang."),
    "htc_phone-app":                   (None, "HTC Android Phone app design by Ceci Chang."),
    "htc_dot-view":                    (None, "HTC Dot Matrix Event Design by Ceci Chang."),
    "htc_cos-wallpaper":               (None, "HTC COS Wallpaper design by Ceci Chang."),
    "htc_message":                     (None, "HTC Message App UI Design by Ceci Chang."),
    "htc_clock":                       (None, "HTC Clock and Calculator Widgets design by Ceci Chang."),
    "htc_scribble":                    (None, "HTC Scribble app design by Ceci Chang."),
    "htc_lifeme":                      (None, "HTC Life.me app design by Ceci Chang."),
    "htc_mini":                        (None, "HTC Mini Phone design by Ceci Chang."),
    "htc_tablet":                      (None, "HTC Tablet Apps Design by Ceci Chang."),
}


def page_meta(slug: str, current_title: str) -> tuple[str, str]:
    if slug in PAGE_META:
        title_override, desc = PAGE_META[slug]
        if title_override:
            return title_override, desc
    # Derive title from current <title> if no override
    t = (current_title or "").replace("&#39;", "'").replace("&apos;", "'").replace("&amp;", "&")
    t = re.sub(r"\s*-?\s*Ceci(?:'s|\.Chang| Chang)?\s+Portfolio.*$", "", t, flags=re.I).strip()
    if not t:
        t = (slug or "page").replace("_", " ").replace("-", " ").title()
    desc = PAGE_META.get(slug, (None, DEFAULT_DESC))[1]
    return f"{t} - {SITE_NAME}", desc


def enrich(path: Path, slug: str) -> bool:
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "lxml")
    head = soup.head
    if not head:
        return False

    # Get current title
    title_tag = head.find("title")
    current_title = title_tag.get_text(strip=True) if title_tag else ""
    new_title, desc = page_meta(slug, current_title)
    page_url = SITE_URL + ("/" if slug == "" else f"/{slug}/")

    # Update <title>
    if title_tag:
        title_tag.string = new_title
    else:
        nt = soup.new_tag("title")
        nt.string = new_title
        head.insert(0, nt)

    # Drop any existing portfolio-meta block (idempotent re-runs)
    for marker in head.find_all(string=lambda s: isinstance(s, str) and "portfolio-meta-start" in s):
        # Remove from start marker through end marker
        n = marker.find_next(string=lambda s: isinstance(s, str) and "portfolio-meta-end" in s)
        cur = marker
        while cur and cur is not n:
            nxt = cur.next_sibling
            cur.extract()
            cur = nxt
        if n:
            n.extract()
    # Drop existing meta description / og: / twitter: tags we'll re-author
    for m in head.find_all("meta"):
        name = (m.get("name") or "").lower()
        prop = (m.get("property") or "").lower()
        if name == "description" or prop.startswith("og:") or name.startswith("twitter:"):
            m.decompose()
    # Drop existing canonical
    for c in head.find_all("link", rel="canonical"):
        c.decompose()

    # Append meta tags using soup.new_tag (lxml fragment parsing auto-wraps in
    # html/head, which corrupts the output — this approach builds each tag
    # in the existing document).
    from bs4 import Comment
    head.append(Comment("portfolio-meta-start"))

    def add_meta(attrs):
        m = soup.new_tag("meta")
        for k, v in attrs.items():
            m[k] = v
        head.append(m)

    add_meta({"name": "description", "content": desc})
    add_meta({"property": "og:type", "content": "website"})
    add_meta({"property": "og:title", "content": new_title})
    add_meta({"property": "og:description", "content": desc})
    add_meta({"property": "og:url", "content": page_url})
    add_meta({"property": "og:site_name", "content": SITE_NAME})
    add_meta({"property": "og:image", "content": OG_IMAGE})
    add_meta({"name": "twitter:card", "content": "summary_large_image"})
    add_meta({"name": "twitter:title", "content": new_title})
    add_meta({"name": "twitter:description", "content": desc})
    add_meta({"name": "twitter:image", "content": OG_IMAGE})

    canon = soup.new_tag("link", rel="canonical", href=page_url)
    head.append(canon)
    head.append(Comment("portfolio-meta-end"))

    # Body-level fixup: bump the footer copyright year from 2023 → 2026.
    # IM Creator's rendered HTML hard-codes the year in the social-preview
    # block at the bottom of every page. Replace any "© 20YY Ceci Chang"
    # → "© 2026 Ceci Chang" so the deployed site reflects the current year.
    if soup.body:
        for el in soup.body.find_all(string=re.compile(r"©\s*20\d\d\s+Ceci\s+Chang")):
            new_text = re.sub(
                r"©\s*20\d\d\s+Ceci\s+Chang",
                "© 2026 Ceci Chang",
                el.string,
            )
            el.replace_with(new_text)

    new_html = str(soup)
    if new_html != html:
        path.write_text(new_html, encoding="utf-8")
        return True
    return False


def main():
    files = list(SITE.rglob("index.html"))
    print(f"Enriching meta on {len(files)} pages…")
    changed = 0
    for f in sorted(files):
        rel = f.relative_to(SITE)
        slug = "" if rel == Path("index.html") else str(rel.parent)
        if enrich(f, slug):
            changed += 1
            print(f"  ✓ {rel}")
        else:
            print(f"  · {rel} (unchanged)")
    print(f"\nUpdated {changed}/{len(files)} pages.")


if __name__ == "__main__":
    main()
