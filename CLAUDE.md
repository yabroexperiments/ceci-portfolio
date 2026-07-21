# Ceci Chang Portfolio — Project Memory

## Cross-machine workflow (Claude Code · Codex CLI · Codex Web)

This project syncs through GitHub. Same rules apply wherever you operate.

**Session start:**
1. `git pull --ff-only` (skip on Codex Web — the container is already at HEAD).
2. Read the latest `.handoffs/*.md` and `.handoffs/INDEX.md` — the bridge from the previous session.

**Session end (mandatory):**
1. Write `.handoffs/YYYY-MM-DD-<task>.md` with: Done · Left · Gotchas · Files touched · How to resume.
2. Commit + push everything stable. Feature branches (`feat/...`) for half-done work. No force-push to `main`. No committing `.env` or any real secret.

**File convention:**
- `CLAUDE.md` is the canonical project brief. `AGENTS.md` in the same directory is a **symlink** to it — both names resolve to the same content for Claude Code and Codex.
- Never replace `AGENTS.md` with a regular file (atomic-save tools can do this). Use in-place writes.
- If `AGENTS.md` ever becomes a regular file: `rm AGENTS.md && ln -s CLAUDE.md AGENTS.md`. Server-side enforcement: `.github/workflows/agents-symlink.yml`. Local enforcement: `.githooks/pre-commit`.

**Fresh clone setup (one-time):** `./setup.sh` — wires up the tracked git hooks.

---

Static replica of [Ceci Chang's UX/UI design portfolio](https://changhsiju.xyz) — a 1:1 mirror of the live IM Creator site at www.changhsiju.com, hosted on GitHub Pages.

## Architecture at a glance

- **Static HTML site** in `site/` deployed by GitHub Actions to GitHub Pages.
- **Custom domain**: `changhsiju.xyz` (Namecheap) → GitHub Pages IPs.
- **Repo**: [yabroexperiments/ceci-portfolio](https://github.com/yabroexperiments/ceci-portfolio) (public).
- **GitHub user/email** for git: `yabroexperiments` / `yabroexperiments@gmail.com`.
- **Source of truth**: `http://www.changhsiju.com/` (Ceci's IM Creator site). When IM Creator publishes content updates, re-run the ripper.

## v2 (current) — fresh rip from live IM Creator

Replaces the v1 stop-gap (Wayback + JS-console hack + custom build template) which was deployed when the IM Creator site was unreachable. Now that IM Creator is online again, we mirror the live site directly.

### Build pipeline (two steps)

```bash
python3 rip_live.py        # Mirror live www.changhsiju.com → mirror_v2/
rm -rf site && mv mirror_v2 site
python3 enrich_meta.py     # Inject SEO/OG/Twitter meta tags into site/*.html
```

`enrich_meta.py` is the ONE intentional deviation from "100% identical to live": IM Creator HTML has no `<meta name="description">`, so chat-app crawlers (LINE, WhatsApp, iMessage, Slack) fall back to scraping the first big text block — which is the Gem Spot project description. The enricher injects per-page title/description/og:image/twitter tags. Idempotent.

`rip_live.py`:
1. Fetches all 25 pages (homepage + about-me + 23 project pages — slug list is hardcoded inside).
2. Discovers every `<link rel=stylesheet>` and `<script src>` per page.
3. Downloads imcreator.com CSS/JS into `mirror_v2/_imc/`.
4. Recursively walks `url(...)` references in CSS, downloads referenced fonts/images.
5. Rewrites HTML attributes to local relative paths.
6. Per-page `static_style?vbid=X` URLs become `_imc/static_style/{vbid}.css`.

What it does NOT do:
- Download Google CDN images (`lh3.googleusercontent.com`) — they're stable and cross-origin-safe; left remote.
- Inject any custom logo, footer, CSS, or back-link. The whole point of v2 is **100% identical to live**.

Output is `mirror_v2/` (gitignored). To deploy, copy contents into `site/`.

### Re-mirroring after Ceci updates IM Creator

```bash
rm -rf .ripcache_live mirror_v2   # clear cache so we re-fetch fresh
python3 rip_live.py
rm -rf site && mv mirror_v2 site
python3 enrich_meta.py
git add site/ && git commit -m "Re-mirror live changhsiju.com" && git push
```

Auto-deploys via `.github/workflows/pages.yml` (~30–60s).

## Backups

| Tag / Branch | Commit | What it is |
|--------------|--------|------------|
| `v2-current-deployed` (tag) | `429f319` | v1 state right before fresh rip — fully deployable |
| `archive/v2-current-deployed` (branch) | `429f319` | Same — branch form for easy GitHub navigation |
| `v1-pre-bnct-restructure` (tag) | `2a3ae6f` | Older v1 state pre-captured-restructure |

To roll back to v1 (DESTRUCTIVE — confirm with user):
```bash
git reset --hard v2-current-deployed && git push --force origin main
```

## v1 (legacy) — preserved for reference

The v1 pipeline is still in the repo but no longer part of the build:

| File | What it did in v1 | Status |
|------|-------------------|--------|
| `rip2.py` | Wayback-Machine fetcher (CDX API + `id_/` raw form) | Kept for reference |
| `build_clean.py` | Rendered 8 captured editor-HTML files via custom template | Kept for reference |
| `fix_pages.py` | Wayback post-processor: dead-host rewrite, footer hide, logo inject | Kept for reference |
| `fix_links.py` | Rewrites root-relative href="/foo" → "./foo/" | Kept for reference |
| `clean_captured.py` | Earlier failed attempt to clean captured HTML in place | Kept for reference |
| `captured/` (gitignored) | Editor-HTML dumps Ceci downloaded via JS-console snippet | Possibly empty — was the v1 fallback when IM Creator was unreachable |

If IM Creator goes back down, v1 is the fallback strategy: Wayback + JS-console capture.

## v2 visual fidelity vs. v1

What v2 fixed by re-ripping:

- **Captured pages now show original IM Creator design**: bnct (yellow hero, 4 device mockups composed side-by-side), binance-leaderboard (dark composition), traderwagon, icardai, coinful, xxyz, binance-future-trading-platform — all now match live exactly. v1 had simpler `build_clean.py` template-rendered versions.
- **about-me profile photo** natively centered above heading (no CSS workaround needed). v1 had hand-coded `display:block; width:200px; margin:auto` rule.
- **Original IM Creator footer + social icons** rendered as IM Creator does it — no custom Ceci-Chang-logo, no unified-footer injection, no back-link.
- **No spimeengine flicker** because v2 uses the actual published HTML which is post-render and stable.

## Pages (25 URLs total)

Homepage + about-me + 23 project pages, mirrored from live changhsiju.com:

- `/` (homepage with all project links)
- `/about-me/`
- Captured-page slugs: `bnct`, `binance-future-trading-platform`, `binance-leaderboard`, `traderwagon_platform`, `traderwagon_mkt`, `xxyz`, `coinful`, `icardai`
- Older-portfolio slugs: `acadine_watch`, `acadine_smart-home`, `acadine_feature-phone`, `mozilla_smart-tv`, `mozilla_feature-phone`, `mozilla_car-ui`, `htc_phone-app`, `htc_dot-view`, `htc_cos-wallpaper`, `htc_message`, `htc_clock`, `htc_scribble`, `htc_lifeme`, `htc_mini`, `htc_tablet`

The 2 `/vbid-3b46eede-...` URLs that appear in the homepage `<a>` scan are IM Creator placeholders for "More" buttons Ceci never filled in. They return "No index" on the live site too. Not real content; ignore them.

## Ceci's contact info (for reference — not used in any custom injection in v2)

- Email: `changhsiju@gmail.com`
- LinkedIn: `https://www.linkedin.com/in/changhsiju/`

## GitHub Pages deploy

Workflow: `.github/workflows/pages.yml` — uploads `site/` as a Pages artifact on every push to `main`. Auto-deploys (~30–60s after push).

DNS:
- `changhsiju.xyz` → 4 A records pointing at GitHub IPs (`185.199.108-111.153`)
- `www.changhsiju.xyz` → CNAME to `yabroexperiments.github.io`
- HTTPS via Let's Encrypt (auto-provisioned by GitHub Pages)

## Local preview

```bash
python3 -m http.server 8765 --directory site
# open http://localhost:8765/
```

## Dependencies

Python 3 with `beautifulsoup4` and `lxml` (`pip3 install beautifulsoup4 lxml`). No npm/node.

`gh` CLI required for repo ops, authenticated as `yabroexperiments`.

## Long-term direction

The static rip captures the site as it exists today, but Ceci can't easily edit it (10K+ lines of IM Creator HTML per page with cryptic `vbid-...` IDs). The paths forward, in rough order of designer-friendliness vs. cost:

1. **Framer** ($15–25/mo) — true freeform per-page layouts, designer-favorite, Figma import. Best fit for a portfolio that needs new case studies with distinct layouts.
2. **Astro/Eleventy rebuild** (free) — Markdown-driven; layouts come from a small set of templates. Free forever, but layout flexibility is constrained to whatever Claude builds upfront.
3. **Once-a-year Framer subscription** ($15–30/year) — subscribe only the month she's building, then cancel. Custom domain works while subscribed.

For Ceci's actual cadence (~once a year, between jobs), the static rip + occasional Claude session for layout updates is genuinely viable. See the editing strategy doc when she next wants to update.

<!-- ECVP:BEGIN (managed by install-vet-protocol.sh — edit the yabro-hq copy, then re-run) -->
> **🛡️ EXTERNAL CODE VETTING PROTOCOL — mandatory, ALL projects
> (Albert, 2026-07-21).** NO external skill / plugin / MCP server /
> package / prompt / workflow enters any environment without passing
> the ECVP pipeline (run via **`/vet <url>`**; full spec in
> `docs/external-code-vetting-protocol.md` in this repo, or
> `~/.claude/docs/` for the global copy). Pipeline: intake
> (true-owner/typosquat check, trust tier) → scan (SkillSpector for
> skills, mcp-scan for MCP, Socket+OSV for packages) → full-file
> analysis (scanners are bypassable — a scan pass alone is NEVER a
> green light) → quarantine test in a secret-free throwaway session →
> merge pinned to exact SHA + row in the project's
> `docs/vetted-external-code.md` registry (present but unlisted =
> unvetted) → monitor (updates are new vettings). Hard rules: secrets
> and unvetted code never meet; unknown author + wants
> network/auth/secrets = automatic reject; Albert reads only
> plain-English GREEN/YELLOW/RED verdicts and makes the go/no-go call.
<!-- ECVP:END -->
