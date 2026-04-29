#!/usr/bin/env python3
"""Rip Ceci's portfolio with new→old URL fallback for missing pages.

Output structure: each project page lives at the NEW (underscore) URL
the 2023 homepage links to, but its content may come from an older
2019-era archived version when no 2023 capture exists.

Pages with no archive in any era are listed at the end as "missing".
"""
import hashlib, json, os, re, ssl, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "site"
CACHE = ROOT / ".rip-cache"
OUT.mkdir(exist_ok=True)
CACHE.mkdir(exist_ok=True)

DOMAIN = "changhsiju.com"
ANCHOR_TS = "20250710003607"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
WB = "https://web.archive.org"
THROTTLE = 0.7

SSL_CTX = ssl.create_default_context(); SSL_CTX.check_hostname = False; SSL_CTX.verify_mode = ssl.CERT_NONE

# Mapping: NEW URL the 2023 homepage links to → list of fallback URL paths to try (in order)
# Always tries the new path first; falls back to older equivalents.
URL_FALLBACKS = {
    "/": ["/"],
    "/about-me": ["/about-me"],
    "/htc_clock": ["/htc_clock", "/htc-clock-and-calculator"],
    "/htc_dot-view": ["/htc_dot-view", "/htc-dotview"],
    "/htc_lifeme": ["/htc_lifeme", "/htc-lifeme"],
    "/htc_message": ["/htc_message", "/htc-message"],
    "/htc_phone-app": ["/htc_phone-app", "/htc-phone"],
    "/htc_scribble": ["/htc_scribble", "/htc-scribble"],
    "/htc_cos-wallpaper": ["/htc_cos-wallpaper", "/htc-wallpaper"],
    "/htc_tablet": ["/htc_tablet", "/htc-tablet"],
    "/htc_mini": ["/htc_mini", "/htc-lite"],
    "/mozilla_car-ui": ["/mozilla_car-ui", "/mozilla-car-ui"],
    "/mozilla_smart-tv": ["/mozilla_smart-tv", "/mozilla-tv"],
    "/mozilla_feature-phone": ["/mozilla_feature-phone"],
    "/acadine_feature-phone": ["/acadine_feature-phone", "/acadine-feature-phone"],
    "/acadine_smart-home": ["/acadine_smart-home", "/acadine-smart-home"],
    "/acadine_watch": ["/acadine_watch", "/acadine-watch"],
    # No public archives exist for these - will be reported as missing
    "/binance-future-trading-platform": ["/binance-future-trading-platform"],
    "/binance-leaderboard": ["/binance-leaderboard"],
    "/bnct": ["/bnct"],
    "/coinful": ["/coinful"],
    "/icardai": ["/icardai"],
    "/traderwagon_mkt": ["/traderwagon_mkt"],
    "/traderwagon_platform": ["/traderwagon_platform"],
    "/xxyz": ["/xxyz"],
}

last_req = [0.0]
def fetch(url, retries=3):
    key = hashlib.sha1(url.encode()).hexdigest()
    cp = CACHE / key
    if cp.exists():
        return cp.read_bytes()
    for attempt in range(retries):
        wait = THROTTLE - (time.time() - last_req[0])
        if wait > 0: time.sleep(wait)
        last_req[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as r:
                body = r.read()
                cp.write_bytes(body)
                return body
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429 or e.code >= 500:
                time.sleep(2 ** attempt * 2); continue
            return None
        except Exception:
            if attempt == retries - 1: return None
            time.sleep(2 ** attempt)
    return None

def closest_snapshot(target_url, prefer_ts=ANCHOR_TS):
    q = f"{WB}/cdx/search/cdx?url={urllib.parse.quote(target_url)}&output=json&filter=statuscode:200&filter=mimetype:text/html&limit=200"
    body = fetch(q)
    if not body: return None
    try: rows = json.loads(body.decode())[1:]
    except: return None
    # filter out tiny captures (stub redirects)
    rows = [r for r in rows if int(r[6]) >= 3000]
    if not rows: return None
    target_int = int(prefer_ts)
    rows.sort(key=lambda r: abs(int(r[1]) - target_int))
    return rows[0][1], rows[0][2]

def id_url(ts, orig):
    return f"{WB}/web/{ts}id_/{orig}"

def url_to_local(new_path):
    """Map a new URL path (e.g. /htc_clock) to a local file path."""
    if new_path == "/":
        return "index.html"
    return new_path.lstrip("/") + "/index.html"

# ---- Step 1: fetch each page using fallback chain ----
print(f"[1/3] Fetching {len(URL_FALLBACKS)} pages with fallback…")
results = {}  # new_path -> (local_path, body, source_path, source_ts)
missing = []
for i, (new_path, fallbacks) in enumerate(sorted(URL_FALLBACKS.items()), 1):
    body = None
    source_path = None
    source_ts = None
    for fb in fallbacks:
        target = f"http://{DOMAIN}{fb}"
        snap = closest_snapshot(target)
        if not snap: continue
        ts, orig = snap
        b = fetch(id_url(ts, orig))
        if b and len(b) >= 3000:
            body, source_path, source_ts = b, fb, ts
            break
    if body:
        local = url_to_local(new_path)
        results[new_path] = (local, body, source_path, source_ts)
        tag = "(2023)" if source_ts.startswith("2025") else f"(fallback from {source_path})"
        print(f"  [{i:2}/{len(URL_FALLBACKS)}] ✓ {new_path:<40} {tag}")
    else:
        missing.append(new_path)
        print(f"  [{i:2}/{len(URL_FALLBACKS)}] ✗ {new_path:<40} MISSING")

print(f"\n  Got {len(results)}/{len(URL_FALLBACKS)} pages")

# ---- Step 2: rewrite each page ----
print(f"\n[2/3] Rewriting HTML…")

WB_PREFIX = re.compile(rb"(?:https?:)?//web\.archive\.org/web/\d+[^/]*/(?:(?:https?:)?/?/?)?")
DOMAIN_ABS = re.compile(rb"https?://(?:www\.)?" + re.escape(DOMAIN.encode()))
TOOLBAR_RE = re.compile(rb"<!-- BEGIN WAYBACK TOOLBAR INSERT -->.*?<!-- END WAYBACK TOOLBAR INSERT -->", re.DOTALL)
ARCHIVE_TAG = re.compile(rb"<(?:script|link|img)[^>]*(?:web-static\.archive\.org|web\.archive\.org)[^>]*?(?:/>|>(?:[^<]*</[^>]+>)?)", re.I)

def relpath_from(local_path):
    """Compute "../" prefix for assets relative to a saved page."""
    depth = local_path.count("/")
    return "../" * depth

def rewrite(html, local_path, source_path):
    # Strip Wayback toolbar
    html = TOOLBAR_RE.sub(b"", html)
    html = ARCHIVE_TAG.sub(b"", html)
    # Strip Wayback URL prefix wherever it appears
    html = WB_PREFIX.sub(b"", html)

    # Now URLs look like "http://changhsiju.com/...", "//imcreator.com/...", "/relative-path", etc.
    # 1. Replace absolute changhsiju.com URLs with site-root style (then we'll fix root-rel below)
    html = DOMAIN_ABS.sub(b"", html)

    # 2. Map root-relative path/links - if it's a known fallback source path, rewrite to its new path
    # Build lookup: source_path -> new_path
    src_to_new = {}
    for new_p, (lp, _, sp, _) in results.items():
        src_to_new[sp] = new_p
        # also include the new_p mapping to itself for safety
        src_to_new.setdefault(new_p, new_p)

    def fix_link(m):
        prefix = m.group("pre")
        url = m.group("url").decode("utf-8", "replace")
        if url.startswith(("http://", "https://", "//", "javascript:", "mailto:", "tel:", "data:", "#")):
            return m.group(0)
        if not url.startswith("/"):
            return m.group(0)
        # Drop query/fragment for matching
        clean = url.split("?")[0].split("#")[0].rstrip("/")
        clean = "/" + clean.lstrip("/") if clean else "/"
        if clean in src_to_new:
            new_p = src_to_new[clean]
            target_local = url_to_local(new_p)
            # convert to relative from current page
            rel = relpath_from(local_path) + (target_local if target_local != "index.html" else "")
            if not rel: rel = "./"
            # If linking to homepage from non-home page, give clean URL
            if target_local == "index.html":
                rel = relpath_from(local_path) or "./"
            return prefix + rel.encode()
        return m.group(0)

    html = re.sub(
        rb'(?P<pre>(?:src|href|data-src|data-image|poster)\s*=\s*["\'])(?P<url>[^"\']+)',
        fix_link, html
    )
    return html

OUT_clean = OUT
for f in OUT_clean.rglob("*"):
    if f.is_file(): f.unlink()

for new_path, (local_path, body, source_path, source_ts) in results.items():
    new_html = rewrite(body, local_path, source_path)
    full = OUT / local_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_bytes(new_html)

# Write a missing-pages stub so links from homepage don't 404 visibly
for mp in missing:
    local = url_to_local(mp)
    full = OUT / local
    full.parent.mkdir(parents=True, exist_ok=True)
    title = mp.lstrip("/").replace("_", " ").replace("-", " ").title()
    rel_root = relpath_from(local)
    stub = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title} — Coming Back Soon</title>
<style>body{{font-family:-apple-system,sans-serif;max-width:600px;margin:10vh auto;padding:0 1em;color:#333;line-height:1.6}}h1{{font-weight:300}}a{{color:#06c}}</style>
</head><body>
<h1>{title}</h1>
<p>This project page was part of the 2023 portfolio redesign and is being restored.</p>
<p><a href="{rel_root or './'}">← Back to portfolio</a></p>
</body></html>"""
    full.write_text(stub)

print(f"  Wrote {len(results)} pages + {len(missing)} placeholders")

# ---- Step 3: report ----
print(f"\n[3/3] Summary")
print(f"  ✓ Recovered (2023 originals): {sum(1 for _,(_,_,_,ts) in results.items() if ts.startswith('2025'))}")
print(f"  ✓ Recovered (older fallback): {sum(1 for _,(_,_,_,ts) in results.items() if not ts.startswith('2025'))}")
print(f"  ✗ Missing (placeholder shown):  {len(missing)}")
if missing:
    print(f"\n  Missing pages (need fresh source — VPN to IM Creator):")
    for m in missing: print(f"    - {m}")
print(f"\n  Output: {OUT}")
total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
print(f"  Size: {total/1024:.0f} KB ({len(list(OUT.rglob('*.html')))} HTML files)")
