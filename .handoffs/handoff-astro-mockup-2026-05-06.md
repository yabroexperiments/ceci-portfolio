# Handoff Brief — astro_mockup branch — 2026-05-06

> Sibling to `handoff-2026-04-30-0015.md`. That one covered v1 (the Wayback-based static rip on `main`). This one covers the parallel branch `claude/jovial-pare-6629c8` which rebuilt the production pipeline (v2) AND added a separate Astro proof-of-concept (`astro_mockup/`).

## 1. Mission

Two parallel goals diverged from the v1 mission:

1. **Production v2 — mirror live, not Wayback.** Replace the v1 Python pipeline (`rip2.py` from Wayback + `build_clean.py` custom templates + `fix_pages.py` CSS overrides) with a simpler one: just download the live `changhsiju.xyz` site exactly as deployed and add SEO meta tags. No layout changes. The reasoning: the v1 site we built and deployed already looks how Ceci wants — preserving it byte-for-byte is safer than re-running a complex transform pipeline.

2. **astro_mockup/ — designer-self-editable rebuild.** Prove that Ceci could own and edit her portfolio without IM Creator and without code edits — drop a `.mdx` file into `src/content/projects/`, fill in frontmatter, write Markdown body sprinkled with `<Section>`/`<Mockups>`/`<Grid>` components, commit on GitHub.com, auto-deploys. This is the path away from "Albert maintains a Python pipeline" toward "Ceci edits Markdown directly."

## 2. Current State

### Worktree

This work lives in a **git worktree**, NOT on `main`:
- Worktree path: `/Users/albert/Documents/Claude/Projects/CeciPorfolio/.claude/worktrees/jovial-pare-6629c8/`
- Branch: `claude/jovial-pare-6629c8`
- HEAD: `9129fb4 Update footer copyright year 2023 → 2026 across all v2 pages`
- Diverged from `main` at `f43a99b` (the original v1 handoff commit)
- Branch has 6 commits ahead of main, none on main behind branch.
- **Branch is NOT pushed yet** — no remote tracking.

### Production v2 site

- `rip_live.py` mirrors `https://www.changhsiju.com` (the LIVE deployed site) into `mirror_v2/` and then ultimately overwrites `site/`. Output is byte-identical to live + downloads all imcreator.com CSS/JS/fonts into `site/_imc/` so the site no longer depends on `www.imcreator.com` being up.
- `enrich_meta.py` ONLY adds meta tags (title, description, og:*, twitter:*) to each page in `site/`. Idempotent. Also rewrites `Copyright © 20YY Ceci Chang` → `2026`.
- `site/` in this branch is a fresh re-rip from the live site — completely different bytes from the v1 `site/` on main, but visually identical to what's currently deployed.

### astro_mockup/

- Astro 4.16.18 + `@astrojs/mdx` 3.1.9. Pure static, no SSR.
- `npm run build` **succeeds**. Generates 5 pages: `/`, `/about/`, `/projects/binance-leaderboard/`, `/projects/bnct/`, `/projects/htc-clock/`.
- The MDX integration was added mid-session; .md files were migrated to .mdx so each project body can `import` and use `<Mockups>`, `<Section>`, `<Grid>` components inline.
- Currently 3 case studies have been rebuilt as MDX: `binance-leaderboard.mdx`, `bnct.mdx`, `htc-clock.mdx`. The other ~22 are not yet started.
- **Live preview port: 8768** (`npm run preview` in astro_mockup/). Not running automatically — start manually.

### Uncommitted changes in worktree

The MDX migration was being polished when the session crashed on the screenshot. Working tree:

```
Modified:
  astro_mockup/astro.config.mjs           (added mdx() integration)
  astro_mockup/package.json               (added @astrojs/mdx)
  astro_mockup/package-lock.json          (lockfile from npm install)
  astro_mockup/src/content/config.ts      (allow .mdx in collection schema; add new optional fields)
  astro_mockup/src/pages/index.astro      (homepage tweaks)
  astro_mockup/src/pages/projects/[...slug].astro  (replaced old layout switch with single CaseStudy layout)

Deleted:
  astro_mockup/src/content/projects/binance-leaderboard.md
  astro_mockup/src/content/projects/bnct.md
  astro_mockup/src/content/projects/htc-clock.md
  astro_mockup/src/content/projects/htc-mini.md
  astro_mockup/src/layouts/DarkHero.astro
  astro_mockup/src/layouts/HeroComposition.astro
  astro_mockup/src/layouts/ImageGrid.astro

New (untracked):
  astro_mockup/src/components/Grid.astro
  astro_mockup/src/components/Mockups.astro
  astro_mockup/src/components/Section.astro
  astro_mockup/src/content/projects/binance-leaderboard.mdx
  astro_mockup/src/content/projects/bnct.mdx
  astro_mockup/src/content/projects/htc-clock.mdx
  astro_mockup/src/layouts/CaseStudy.astro
```

These changes implement the .md → .mdx migration. Build passes, but **none of this is committed**. If the worktree is deleted before commit, all of it is lost.

## 3. Completed This Session (across the branch's 6 commits)

In chronological order:

1. **`429f319` about-me: force profile photo into centered hero above text** — followup polish on v1 about-me layout.
2. **`572183f` Replace site/ with fresh rip from live www.changhsiju.com (v2)** — major pivot. Decided to mirror live instead of regenerating from Wayback. New `rip_live.py` script (~12KB). Output: a byte-identical mirror with all imcreator.com assets bundled into `site/_imc/`, breaking the runtime dependency on imcreator.com being up.
3. **`78d42b8` Add enrich_meta.py + rebrand title to "Ceci's Portfolio 2026"** — only modification to live HTML is meta-tag injection. Title rebrand 2023 → 2026. Per-page descriptions hard-coded in `PAGE_META` map.
4. **`3f99256` Remove stale AGENTS.md (was a v1-era duplicate of CLAUDE.md)** — cleanup. AGENTS.md was a duplicate of CLAUDE.md from earlier session noise.
5. **`d18df9b` Add astro_mockup/ — proof-of-concept self-editable rebuild** — entire Astro project committed. Initial state: 4 case studies as `.md` files, 3 distinct layouts (DarkHero, HeroComposition, ImageGrid).
6. **`9129fb4` Update footer copyright year 2023 → 2026 across all v2 pages** — `enrich_meta.py` extended to rewrite copyright year in body text.

Then the **uncommitted MDX migration work** (see Section 2): converted `.md` → `.mdx`, replaced 3 separate layouts with a single flexible `CaseStudy.astro` layout that defers rendering decisions to the body via inline components.

## 4. In-Flight Work — exactly where we stopped

The user's exact words (from the chat scrollback): *"the MDX issues I was fighting through were entirely contained in astro_mockup/. The deployed site at changhsiju.xyz is unaffected. Even if I broke astro_mockup/ completely, production stays up. Now back to the BNCT comparison — let me grab the screenshot of the rebuilt mockup."*

So:
- **MDX issues are RESOLVED.** `astro build` succeeds, all 3 .mdx pages render.
- **The BNCT visual comparison is the in-flight task.** The user was about to take a screenshot of the rebuilt astro_mockup `/projects/bnct/` page (probably from `npm run preview` on port 8768) to compare against the production `/bnct/` on `https://changhsiju.xyz/bnct/`.
- **The screenshot tool triggered an API error** — one of the prior images in that session's context exceeded 2000px. That session is now blocked; every new message reloads the offending image.

So the next thing to do is: **render astro_mockup's `/projects/bnct/` page and compare against `https://changhsiju.xyz/bnct/`. Identify visual gaps. Iterate the .mdx file or components until they match.**

## 5. Next Steps (prioritized)

1. **Resume the BNCT comparison** —
   - Start preview: `cd astro_mockup && npm run preview`
   - Visit `http://localhost:8768/projects/bnct/`
   - Open `https://changhsiju.xyz/bnct/` side-by-side
   - Note differences (typography, image sizing, section spacing, hero composition)
   - Tweak `bnct.mdx` frontmatter (`hero_images`, `background_color`) and/or the components in `src/components/` until visual parity reached
2. **Commit the MDX migration** as soon as user confirms BNCT looks acceptable. Suggested commit message: `astro_mockup: migrate .md → .mdx with inline component layouts`.
3. **Rebuild remaining case studies as .mdx** — only 3 of ~25 are done. Each captured page from v1 is a candidate (binance-future-trading-platform, traderwagon_*, icardai, coinful, xxyz). Older Wayback-only pages (htc_*, mozilla_*, acadine_*) might be lower priority — they're already polished on production v2.
4. **Decide deployment strategy for astro_mockup/** — currently `dist/` is ignored. Options: (a) GitHub Action that builds astro_mockup and overwrites `site/`, (b) deploy astro_mockup to a separate Vercel project for staging, (c) keep it as a local mockup until Ceci approves the design.
5. **Rebase or merge the branch into main** — main is significantly behind. The whole v2 production setup, the docs/handoffs/, and astro_mockup/ all live only on this branch.
6. **Push the branch** — currently local-only. `git push -u origin claude/jovial-pare-6629c8`.

## 6. Key Decisions + Rationale

Don't re-litigate:

| Decision | Rationale |
|----------|-----------|
| v2: mirror live instead of regenerating from Wayback | The v1 Python pipeline shaped the live site. Re-running it could drift from what's currently deployed. Mirroring `changhsiju.xyz` byte-for-byte is the safest way to "snapshot" the polished result. |
| Bundle imcreator.com CSS/JS into `site/_imc/` | IM Creator's CDN endpoints have been flaky during the project. Self-hosting the assets eliminates the dependency. |
| `enrich_meta.py` ONLY adds metadata, doesn't modify content | Minimizes risk of layout regressions. The only legitimate ADDITION to a mirror is what wasn't there in the source. |
| Astro + MDX over Framer | Free, open-source, designer-friendly enough for Markdown editing, lets us embed React-like components in body. Framer is $15/mo and locks in. |
| Single `CaseStudy.astro` layout instead of 3-4 specialized layouts | Earlier we had `DarkHero`, `HeroComposition`, `ImageGrid` — but each layout had to anticipate every body shape. Better: a thin layout that owns chrome (header, footer, hero) and lets the MDX body decide its own structure via `<Section>` / `<Mockups>` / `<Grid>` components. |
| `<Mockups>`, `<Section>`, `<Grid>` as MDX-importable components | Each component encapsulates one recurring visual pattern. Author-friendly: just write Markdown + nest images inside `<Mockups>`. |
| Astro content collections with Zod schema | Schema validation prevents Ceci from accidentally saving a broken page (missing title, etc.). Build will fail loudly. |

## 7. Open Questions / Blockers

- **Visual fidelity of astro_mockup's BNCT vs production** — unknown. The comparison wasn't completed. Most likely needs typography tweaks; could need hero composition adjustments.
- **What lh3.googleusercontent.com images are real vs decorative** — `bnct.mdx` was hand-curated. Other case studies will need similar curation. There's no automated way to know which images are content vs background; v1's `build_clean.py` had heuristics (frequency-based filter, size-suffix filter) but they're not reused here.
- **Should astro_mockup eventually replace `site/` entirely** — open question. If yes, we need a migration plan (DNS swap, GitHub Pages workflow update). If no, astro_mockup stays as design reference.
- **The branch is unpushed.** If this machine fails or the worktree is wiped, all 6 commits + uncommitted MDX work are lost. Push is overdue.

## 8. Gotchas & Landmines

1. **Worktree, not main branch.** `git status` from the main repo will lie. Always `cd .claude/worktrees/jovial-pare-6629c8` before running git commands related to this work.
2. **MDX files MUST have an empty line between frontmatter and `import` statements.** Astro's MDX integration silently breaks otherwise. The `bnct.mdx` example shows the pattern.
3. **`<Mockups>` and `<Section>` need explicit `import` at the top of each .mdx file.** They are NOT auto-imported. Easy to forget when copy-pasting between files.
4. **Markdown-inside-MDX-component-children quirk**: In Astro MDX, plain Markdown inside a component's children is processed, BUT lists (`- foo`) only work if there's a blank line between the component opening and the list. e.g. `<Section>\n\n- item\n\n</Section>` works; `<Section>- item</Section>` doesn't.
5. **Single-image inside `<Mockups>` gets a different size cap** — see the `:only-child` CSS rules. Designed to make solo mockups (e.g. a single web screenshot) bigger than they would be in a 3-up phone row.
6. **`.mdx` files in `src/content/projects/` are routed automatically by `[...slug].astro`.** The slug = filename minus `.mdx`. Don't add `.mdx` extension manually to URLs.
7. **`site/` on this branch is COMPLETELY DIFFERENT from `site/` on main.** `git diff main..HEAD --stat -- site/` shows ~138K lines of difference. Don't accidentally merge in a way that drops one or the other.
8. **`assets/project.css` was deleted on this branch** (it was the v1 captured-pages CSS, no longer needed). If a process tries to read it, will 404. Confirm nothing references it.
9. **Both `enrich_meta.py` and `rip_live.py` write to the same `site/` directory.** Always run `rip_live.py` first, then `enrich_meta.py`. The other order would have meta tags overwritten.
10. **astro_mockup/dist/ is in .gitignore** — check before assuming committed builds match deploy state.

## 9. Files Modified Across The Branch

Top-level Python pipeline:
- `rip_live.py` (NEW, +12KB) — live-site mirror
- `enrich_meta.py` (NEW, +9KB) — SEO meta-tag injector

astro_mockup/ (NEW directory tree, +20+ files):
- `astro.config.mjs`, `package.json`, `package-lock.json`, `tsconfig.json`
- `src/content/config.ts` — Zod schema for projects collection
- `src/layouts/BaseLayout.astro` — page chrome (header/footer)
- `src/layouts/CaseStudy.astro` — single flexible case-study wrapper (NEW, replaces 3 old layouts)
- `src/layouts/ProfilePage.astro` — about page layout
- `src/components/SiteHeader.astro`, `SiteFooter.astro`, `ProjectCard.astro`
- `src/components/Section.astro`, `Mockups.astro`, `Grid.astro` (NEW, untracked — body-level components)
- `src/pages/index.astro`, `about.astro`, `projects/[...slug].astro` (route)
- `src/content/projects/{binance-leaderboard,bnct,htc-clock}.mdx` (NEW, untracked — replace .md files)

site/:
- All 25 page HTMLs replaced with v2 versions (different bytes, visually similar)
- `site/_imc/` — bundled imcreator.com CSS/JS/fonts
- `site/assets/project.css` — DELETED (v1 only, no longer needed)

## 10. Env / Config / Dependencies

- **Same Python deps as v1** — bs4, lxml. Used by `enrich_meta.py`.
- **NEW: Node.js + npm.** astro_mockup needs Node 18+. `package.json` declares Astro 4.16 + `@astrojs/mdx` 3.1. `node_modules/` is gitignored.
- **astro_mockup ports**: `npm run dev` uses Astro default (4321). `npm run preview` uses 8768.
- **No new env vars.** No secrets.

## 11. Commands to Resume

```bash
# 1. cd into the worktree
cd /Users/albert/Documents/Claude/Projects/CeciPorfolio/.claude/worktrees/jovial-pare-6629c8

# 2. confirm we're on the branch
git status                       # branch claude/jovial-pare-6629c8, with uncommitted MDX changes

# 3. (optional) build production v2 site/
python3 rip_live.py              # mirrors live; outputs to mirror_v2/, syncs into site/
python3 enrich_meta.py           # adds meta tags
# rip_live.py is conservative — re-runs hit cache (.ripcache_live/, gitignored)

# 4. astro_mockup work
cd astro_mockup
npm install                      # if node_modules missing
npm run build                    # confirms MDX still compiles (currently ✓)
npm run preview                  # serves dist/ on http://localhost:8768

# 5. compare BNCT pages
# Open http://localhost:8768/projects/bnct/ AND https://changhsiju.xyz/bnct/ side-by-side
# Iterate bnct.mdx + components until visually matched

# 6. commit + push when ready
cd /Users/albert/Documents/Claude/Projects/CeciPorfolio/.claude/worktrees/jovial-pare-6629c8
git add -A
git commit -m "astro_mockup: ..."
git push -u origin claude/jovial-pare-6629c8    # FIRST PUSH — branch is local-only right now
```

## 12. Git State

### Main worktree (`/Users/albert/Documents/Claude/Projects/CeciPorfolio/`):
- Branch: `main`
- HEAD: `f43a99b Add CLAUDE.md (project memory) + handoff brief`
- Working tree: clean except for one untracked file `AGENTS.md` (an old artifact — was already on the branch but got removed in commit `3f99256`; reappeared on main somehow. Probably safe to delete.)
- Up-to-date with `origin/main`.

### astro_mockup worktree (`.claude/worktrees/jovial-pare-6629c8/`):
- Branch: `claude/jovial-pare-6629c8`
- HEAD: `9129fb4 Update footer copyright year 2023 → 2026 across all v2 pages`
- Working tree: lots of uncommitted .md→.mdx migration (see Section 2)
- **Branch NOT pushed** — local-only. `git push -u origin claude/jovial-pare-6629c8` overdue.
- Behind main by 0, ahead of main by 6 commits.

### Tag
- `v1-pre-bnct-restructure` at `2a3ae6f` (pushed to origin).

## 13. Context the Summary Would Lose

- **The session that did this work crashed on a screenshot.** Specifically the user (Albert in our chat — but possibly a different operator on this branch?) ran a screenshot tool with too many images already in context. The `(image dimension > 2000px)` API error blocks any followup in that session.
- **The pivot from v1 to v2 was a strategic call**, not a forced one. v1 was working — the live site at changhsiju.xyz already looked fine. The decision to mirror the live deploy and abandon the Wayback-derived pipeline was about **future-proofing**: any future tweak runs through a simpler 2-script pipeline (`rip_live.py`, `enrich_meta.py`) instead of the v1 chain of `rip2.py` → `build_clean.py` → `fix_pages.py` → `fix_links.py`.
- **astro_mockup is a "DESIGN proof", not a "DEPLOY proof".** It demonstrates the editing workflow — drop a .mdx file, build, deploy. It does NOT yet have feature parity with the production site (it has 3 of 25 case studies). When evaluating whether astro_mockup is "ready," remember it's intentionally incomplete.
- **The `<Mockups>` / `<Section>` / `<Grid>` triad is the design language.** They were chosen because IM Creator's actual case studies use these exact patterns:
  - `<Mockups>`: a row of 1-3 device screenshots side-by-side (the most common pattern)
  - `<Section>`: heading + body text + nested content (the standard scrolling pattern)
  - `<Grid>`: N-column gallery for image-dense pages like HTC Clock
  Other patterns (e.g. side-by-side text+image, video embeds) might need new components later. Don't add them speculatively.
- **`HeroComposition` was sacrificed.** The old `HeroComposition.astro` layout had logic to compose 3 mockup images at angles into a hero. The new `CaseStudy.astro` has a simpler "lay them flat side-by-side" hero. If the user wants the angled version back, we'd need to either revive that layout OR add a `<HeroComposition>` MDX component.
- **The Zod schema in `content/config.ts` is permissive.** Almost everything is `optional()`. Tightening it later is fine, but for now the philosophy is: let case studies omit what they don't need.
- **`enrich_meta.py`'s description copy is hand-tuned.** It uses Ceci's bio voice ("Senior Product Designer / Design Lead") and references specific clients. If new clients are added, update `PAGE_META` dict.
- **The user is technical.** They'll likely commit the MDX work themselves once the comparison passes — no need to over-explain git mechanics.
- **Production deploy from this branch hasn't happened.** GitHub Pages still serves from main. If we want this branch's v2 site to go live, we need to either merge to main OR change the workflow to deploy from this branch. Currently neither has been done.

---

**That's the brief.** Read alongside `handoff-2026-04-30-0015.md` for the full v1 → v2 arc.
