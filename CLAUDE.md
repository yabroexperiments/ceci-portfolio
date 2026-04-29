# Ceci Chang Portfolio — Project Memory

Static migration of [Ceci Chang's UX/UI design portfolio](https://changhsiju.xyz) off the failing IM Creator platform. Deployed as a static site via GitHub Pages.

## Architecture at a glance

- **Static HTML site** in `site/` deployed by GitHub Actions to GitHub Pages.
- **Custom domain**: `changhsiju.xyz` (Namecheap) → GitHub Pages IPs.
- **Repo**: [yabroexperiments/ceci-portfolio](https://github.com/yabroexperiments/ceci-portfolio) (public).
- **GitHub user/email** for git: `yabroexperiments` / `yabroexperiments@gmail.com`.

## The 25 pages — three sources

| Source | Pages | Style era |
|--------|-------|-----------|
| **Wayback 2025-07** | `index.html`, `about-me/` | 2023 redesign — IM Creator post-render snapshots |
| **Wayback 2019** | 15 HTC/Mozilla/Acadine project pages | older portfolio era — IM Creator post-render |
| **User-captured editor HTML** | 8 newer projects (Binance, TraderWagon, iCardAi, BNCT, Coinful, X.xyz) | rendered through a custom Python template |

The 8 captured pages came from Ceci pasting a JS console snippet into IM Creator's editor that does `document.documentElement.outerHTML` → download. Files live in `captured/` (gitignored — they're inputs to the build, not source of truth).

## Build pipeline (run in this order)

```bash
python3 rip2.py        # Only re-run if Wayback content needs re-fetch (uses .rip-cache/)
python3 build_clean.py # Renders 8 captured pages from captured/ via clean template
python3 fix_pages.py   # Post-processes ALL Wayback pages: host rewrite + CSS overrides + footer/logo inject
python3 fix_links.py   # Rewrites root-relative href="/foo" → "./foo/" so site works under any base path
```

`rip2.py` should rarely need re-running — its outputs are committed in `site/`. The cache makes re-runs cheap if needed (`.rip-cache/` is 3MB of Wayback responses, gitignored).

## Where to make changes

| Change | File to edit |
|--------|-------------|
| Universal CSS (typography, footer hide, logo size, nav links) | `fix_pages.py` → `width_fix` variable |
| Homepage-specific tweaks (e.g. white text on dark sections) | `fix_pages.py` → `HOMEPAGE_OVERRIDES` variable |
| About-me-specific tweaks (e.g. circular profile photo) | `fix_pages.py` → inside the `width_fix` block targeting `#vbid-686774fa-nvkm78sz` |
| 8 captured pages template/CSS | `build_clean.py` → `SHARED_CSS` variable + `render_page()` |
| Captured-page section/block classification | `build_clean.py` → `parse_section()` |
| Bottom HOME button removal / Back-to-portfolio inject | `fix_pages.py` → loop body |
| Footer markup (used everywhere) | `build_clean.py` page template AND `fix_pages.py` `FOOTER_HTML` — keep them byte-identical |

## Critical rule: CSS scope

`HOMEPAGE_OVERRIDES` is injected ONLY on the homepage. Universal rules (apply to all Wayback pages including `about-me/` + project pages) MUST go in `width_fix`. **Misclassifying scope is the #1 bug we hit** (footer-box was visible on about-me because the hide-rule was misplaced in `HOMEPAGE_OVERRIDES`).

## Design system standards

- **Logo**: 97×20 px (Google CDN: `https://lh3.googleusercontent.com/LpF5FkXmIWcEsH77dZ6Z_kV7Y3wLf3y3JQnx7r6TOuVkeypK_jDauMNjgFC-zLhwzd5dlRv82i7ifxBfaw=s260`)
- **Typography (3 levels)**:
  - Heading — 26px Montserrat 600 / `#111` / line-height 1.3
  - Body — 18px Montserrat 400 / `#333` / line-height 1.7
  - Description — 14px Montserrat 400 / `#666` / line-height 1.6
- **Footer (uniform across all pages)**: Custom `<footer class="ceci-footer-inject">` — left = `Copyright © 2026 Ceci Chang. All rights reserved.`; right = Email + LinkedIn 24×24 icons; thin top border (`#eee`).
- **Footer icon URLs** (Google CDN, hardcoded in two places):
  - Email: `https://lh3.googleusercontent.com/lXDKZBXBa_mQ0A-IrOjHdi9s79RAhEe7zhdTEuKpKGLXGde6iL2n46n2Zi4TVA9Daag9Z13s1dGTbsnAXg=s100`
  - LinkedIn: `https://lh3.googleusercontent.com/nJ0IsRDlfNRwXaO-ySLjDaIGgTW24qj6x5j0csqCgvEpaQGBPJJtU4qP83pmkOkcorVnLWAbkyJ_fELF=s100`

## Image-extraction rules (build_clean.py)

When parsing a captured page's images, always:
- Drop images with `=s50` size suffix or smaller (they're icons / social buttons)
- Drop image URLs whose stem appears 3+ times on the same page (page background / repeated decoration)
- Rewrite size suffix to `=s2000` for the highest-res available

## IM Creator-specific gotchas (HARD-WON)

These will bite again if forgotten:

1. **`xprs.imcreator.com` is DEAD** — older Wayback HTML references it for CSS/JS. `fix_pages.py` rewrites it to `www.imcreator.com` (which still serves old version strings like `?v=1.5.1g`).
2. **Captured pages had `data-app-version` ending in `-no-viewer`** — that suffix loads the editor build of `all_js.js` which disables the rendering engine. Strip it.
3. **`spimeengine.js` causes infinite layout re-runs on `about-me`** — it keeps oscillating an element's margin between 0 and 20px, producing visible flicker. We strip both `spimeengine.js` and `all_js.js` from `about-me` only. Without those scripts the post-render Wayback HTML still displays correctly, but you must explicitly set `border-radius: 50%` on the profile photo (`#vbid-686774fa-nvkm78sz`) since the engine no longer applies it at runtime.
4. **`body { display: inline-block }`** is set by IM Creator's CSS — must override to `block` or the page won't fill viewport width.
5. **IM Creator's native footer-box (`.footer-box`)** must be hidden via `display: none !important` because we replace it with our own consistent footer. The class is on every Wayback page including the homepage.
6. **Triple-injection bug** — if you re-run `fix_pages.py` and use regex to strip prior injections, it may miss some and stack duplicates. ALWAYS use bs4 (`soup.find_all(class_=...).decompose()`) for idempotent inject/strip operations.
7. **Captured pages have nested `page-box` blocks inside `gallery-box` sections** — each `page-box` is one image+caption pair. Collapsing them into a single section per `gallery-box` loses the per-image captions. `parse_section()` handles this.
8. **The IM Creator editor's HTML uses `blocks-preview-title`** (1.5.x) vs `preview-title` (1.6.x) for headings — CSS rules need to target both.
9. **Image URLs are mostly Google CDN** (`lh3.googleusercontent.com/...`) — they're independent of IM Creator and stable. Don't try to download them locally; reference directly.

## GitHub Pages deploy

Workflow: `.github/workflows/pages.yml` — uploads `site/` as a Pages artifact on every push to `main`. Auto-deploys (~30s after push completes). DNS:
- `changhsiju.xyz` → 4 A records pointing at GitHub IPs (`185.199.108-111.153`)
- `www.changhsiju.xyz` → CNAME to `yabroexperiments.github.io`
- HTTPS via Let's Encrypt (auto-provisioned by GitHub Pages)

## Local preview

```bash
cd site && python3 -m http.server 8765
# open http://localhost:8765/
```

The build scripts edit `site/` in place — don't add intermediate output dirs.

## Dependencies

Python 3 with `beautifulsoup4` and `lxml` (`pip3 install beautifulsoup4 lxml`). Stdlib for everything else (urllib, ssl, etc.). No npm/node, no JS toolchain.

`gh` CLI required for repo ops, authenticated as `yabroexperiments`.

## Ceci's contact info (used in footer everywhere)

- Email: `changhsiju@gmail.com`
- LinkedIn: `https://www.linkedin.com/in/changhsiju/` (limited public visibility — looks like a 404 to logged-out users in some regions, but profile exists)

## Backup snapshots

Tag `v1-pre-bnct-restructure` at commit `2a3ae6f`: state before the captured-page nested-block restructure. To roll back:
```bash
git reset --hard v1-pre-bnct-restructure && git push --force origin main
```
(Confirm with user before force-pushing.)

## Long-term direction (acknowledged but deferred)

Static rip is a stop-gap. Long-term, Ceci should rebuild on **Framer** (designer-friendly visual editor, $15/mo) or have Claude maintain a custom Astro/Next.js site (free, requires Markdown editing or asking Claude). User chose to stick with static rip "for now" but is aware of the maintainability trade-off.
