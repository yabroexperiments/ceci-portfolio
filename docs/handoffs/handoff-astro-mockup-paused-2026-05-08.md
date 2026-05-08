# Handoff Brief — astro_mockup PAUSED — 2026-05-08

> Sibling to [`handoff-astro-mockup-2026-05-06.md`](./handoff-astro-mockup-2026-05-06.md), which described the in-flight BNCT visual comparison. This doc is the close-out: the BNCT comparison was completed, four bugs were fixed, but the astro_mockup is still not at the visual-parity bar needed to replace production. **Project paused**.

## TL;DR

- **Production v2** at [changhsiju.xyz](https://changhsiju.xyz) (served from `site/` on `main`) is **unchanged** and remains the source of truth.
- The astro_mockup/ rebuild lives only on this branch: `claude/jovial-pare-6629c8`. Six commits ahead of (a now-merged-into-main version of itself) plus this commit's archive snapshot.
- Tagged as `archive/astro-mockup-paused-2026-05-08` for future revival.
- Worktree at `.claude/worktrees/jovial-pare-6629c8/` can be removed once branch and tag are pushed; nothing in production depends on it.

## What got fixed in the 2026-05-08 session

Four real bugs landed; visual structure now closely matches production for the BNCT page hero and section layout. Image content per section was only partially reconciled.

1. **Hero composition rewrite.** `bnct.mdx` was passing 3 separate URLs as `hero_images`; `CaseStudy.astro` rendered them flat side-by-side. Production uses ONE composite PNG via `background-size: cover`. New `hero-cover` branch in `CaseStudy.astro` triggers when `hero_images.length === 1`. Frontmatter trimmed to the one composite URL. `SiteHeader` background → `transparent` so the yellow band extends behind the sticky nav (matches production).
2. **Heading double-padding.** `CaseStudy.astro`'s `.body :global(h2)` was matching descendant h2s — including ones inside `<Section>`, which already pads them. Tightened to `.body :global(> h2)` (direct child only); same for h3.
3. **`Mockups` `:only-child` selector bug.** `.mockups img:only-child` was matching every image because each MDX `![](url)` is the only child of its own `<p>` wrapper, so multi-image rows got promoted to the 900px solo cap. Removed; only `.mockups p:only-child > img` (the genuine single-image case) gets the wider cap.
4. **`Mockups` flex-wrapping.** `<p>` MDX wrappers were behaving as ~740px-wide flex items, forcing every image onto its own row. Set `.mockups > p { display: contents }` so the `<img>` becomes the direct flex child; rows now correctly side-by-side.

Plus polish:
- Single-image `<Mockups>` cap raised to 1000px (matches production's 999px).
- `<Mockups>` default `maxHeight` raised 460 → 620px.
- Removed a duplicate hero-composite URL that was repeated in the "Copy Trading App Design" body section.

## Why paused

The user inspected the result and called it. The mockup still isn't at the bar needed for it to replace production. Specific gaps observed but not closed:

- **Per-section image content doesn't match production.** Production composes related screenshots into ONE big PNG per section. Current `bnct.mdx` lists multiple URLs per section, some of which point to images production uses elsewhere or to assets that look stylistically wrong in `<Mockups>` rows. Closing this gap requires either: (a) reorganizing `bnct.mdx` to use single-image-per-section matching production's URL inventory, or (b) sourcing/exporting per-phone screenshots that don't currently exist as standalone assets.
- **22 of 25 case studies are not rebuilt.** Only `bnct.mdx`, `binance-leaderboard.mdx`, `htc-clock.mdx` exist. The other 22 (binance-future-trading-platform, traderwagon_*, icardai, coinful, xxyz, htc/mozilla/acadine series) are still v1-only.
- **No fade-in animations.** IM Creator uses scroll-triggered opacity transitions. The astro_mockup renders flatly. May or may not matter depending on Ceci's preference.
- **Header treatment on non-hero pages.** `transparent` works fine when there's a colored hero. On pages with white background and no hero (the homepage, about page) the transparent nav can feel ungrounded; probably needs a scroll-shadow.
- **Image asset strategy is unsettled.** Currently every image is a remote `lh3.googleusercontent.com` URL. Those came from IM Creator's CDN. If Ceci adds a new case study without IM Creator, where do the images live? GitHub repo? External CDN? Open question.

## What would be needed to resume

1. **Decide visual-language direction.** Mirror production exactly (one composed PNG per section), or own a different design (multiple individual phone screenshots side-by-side)? The existing `<Mockups>` abstraction supports both. Current implementation is hybrid and inconsistent.
2. **Settle the image-asset strategy.** This blocks every case study added without IM Creator.
3. **Rebuild the 22 remaining case studies.** Each one is an `.mdx` file with frontmatter + section components. Mechanical work once the design language is settled.
4. **Decide deployment.** Options: (a) separate Vercel project for staging, (b) GitHub Action that builds astro_mockup and overwrites `site/` (replaces production v2), (c) keep as design reference only. The handoff from 2026-05-06 also lists these.

## Files at archive time

Branch: `claude/jovial-pare-6629c8`
Tag: `archive/astro-mockup-paused-2026-05-08`

The archive commit folds in the .md → .mdx migration that was uncommitted on 2026-05-06 *plus* the four bugfixes from this session. Modified/new files (relative to the prior commit `9129fb4`):

```
astro_mockup/astro.config.mjs                   M  (mdx() integration)
astro_mockup/package.json                       M  (@astrojs/mdx dep)
astro_mockup/package-lock.json                  M
astro_mockup/src/content/config.ts              M  (allow .mdx; new optional fields)
astro_mockup/src/content/projects/binance-leaderboard.md  D
astro_mockup/src/content/projects/bnct.md                D
astro_mockup/src/content/projects/htc-clock.md           D
astro_mockup/src/content/projects/htc-mini.md            D  (orphan; layout deleted)
astro_mockup/src/content/projects/binance-leaderboard.mdx ?
astro_mockup/src/content/projects/bnct.mdx               ?
astro_mockup/src/content/projects/htc-clock.mdx          ?
astro_mockup/src/layouts/DarkHero.astro          D
astro_mockup/src/layouts/HeroComposition.astro   D
astro_mockup/src/layouts/ImageGrid.astro         D
astro_mockup/src/layouts/CaseStudy.astro         ?  (single flexible layout)
astro_mockup/src/components/Section.astro        ?
astro_mockup/src/components/Mockups.astro        ?
astro_mockup/src/components/Grid.astro           ?
astro_mockup/src/components/SiteHeader.astro     M  (transparent bg)
astro_mockup/src/pages/index.astro               M
astro_mockup/src/pages/projects/[...slug].astro  M
docs/handoffs/handoff-astro-mockup-paused-2026-05-08.md  ?  (this file)
```

Build status at archive: `npm run build` passes; 5 routes generated (`/`, `/about/`, `/projects/binance-leaderboard/`, `/projects/bnct/`, `/projects/htc-clock/`). `npm run preview` was running on :8768 during the session and was stopped before commit.

## Production v2 (unchanged — still the live site)

- Lives on `main`, served from `site/` via `.github/workflows/pages.yml`.
- Pipeline: `python3 rip_live.py && python3 enrich_meta.py`.
- Re-mirror flow when Ceci updates IM Creator: see project [CLAUDE.md](../../CLAUDE.md) → "Re-mirroring after Ceci updates IM Creator".
- DNS, deploy, and backup state are all unchanged from the 2026-05-06 handoff.

## How to revive

```bash
# from anywhere in the repo
git fetch origin
git worktree add ../revive-astro archive/astro-mockup-paused-2026-05-08
cd ../revive-astro/astro_mockup
npm install
npm run dev    # http://localhost:4321 with hot reload
```

Or — if the worktree at `.claude/worktrees/jovial-pare-6629c8/` still exists locally — just `cd` in and `npm run dev`.

## How to delete the worktree (after branch + tag are pushed)

```bash
git worktree remove .claude/worktrees/jovial-pare-6629c8
# branch claude/jovial-pare-6629c8 stays in refs; tag stays in refs.
# To recover later, `git worktree add` from either ref.
```
