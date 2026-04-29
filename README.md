# Ceci's Portfolio — Migration

Static migration of [Ceci Chang's portfolio](https://changhsiju.com) off IM Creator (which is in decline) to a self-hosted static site.

## Status

| Page | Source | Notes |
|------|--------|-------|
| Homepage `/` | 2025-07-10 Wayback snapshot | Full 2023 design |
| About-me `/about-me` | 2025-07-11 Wayback snapshot | Full 2023 design |
| HTC project pages (9) | 2019 Wayback snapshots | Older portfolio era — content preserved, design is older |
| Mozilla project pages (3) | 2019 Wayback snapshots | Same — older era |
| Acadine project pages (3) | 2019 Wayback snapshots | Same — older era |
| Binance / TraderWagon / iCardAi / BNCT / Coinful / X.xyz (8) | Captured from IM Creator editor, rendered via clean simplified template | Content preserved, design is a stop-gap (different from rest of site) |

The 8 captured pages are rendered through a custom Python template (`build_clean.py`) because IM Creator's runtime layout engine couldn't be reproduced statically without their backend.

## Build pipeline

```
rip2.py          # downloads pages from Wayback Machine
fix_pages.py     # rewrites dead //xprs.imcreator.com to //www.imcreator.com
build_clean.py   # for the 8 captured pages: extracts content from /captured/ and renders via clean template
```

The `/captured/` folder (gitignored) holds the source HTML for the 8 pages downloaded directly from the IM Creator editor.

## Local preview

```
cd site && python3 -m http.server 8765
# open http://localhost:8765/
```

## Deploying

The `site/` folder is a static site. Drop it into any static host:
- GitHub Pages (this repo)
- Cloudflare Pages, Netlify, Vercel — drag and drop

## Future maintenance

This repo is a stop-gap to preserve the existing portfolio. For long-term editing, the recommended path is rebuilding on **Framer** or a Claude-maintained custom Astro/Next.js site — see conversation notes.
