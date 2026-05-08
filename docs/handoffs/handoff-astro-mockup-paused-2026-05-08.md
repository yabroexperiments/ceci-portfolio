# Pointer — astro_mockup paused 2026-05-08

The astro_mockup rebuild was paused on 2026-05-08 after the BNCT visual comparison. Production v2 at [changhsiju.xyz](https://changhsiju.xyz) is unaffected and remains the source of truth.

**Archive lives on a different branch.** The mockup files, four bug fixes from the close-out session, and the full close-out handoff are all on:

- Branch: `claude/jovial-pare-6629c8`
- Tag: `archive/astro-mockup-paused-2026-05-08`
- Close-out handoff inside that ref: `docs/handoffs/handoff-astro-mockup-paused-2026-05-08.md`

Read the close-out handoff there for: what was attempted, what bugs landed, what gaps remain, and how to revive.

## Quick revive

```bash
git fetch origin
git worktree add ../revive-astro archive/astro-mockup-paused-2026-05-08
cd ../revive-astro/astro_mockup
npm install
npm run dev    # http://localhost:4321
```

## Production unchanged

The two-script pipeline (`rip_live.py` + `enrich_meta.py`) and the `site/` directory on `main` are not touched by anything in the archive. Re-mirroring after Ceci updates IM Creator still works exactly as documented in the project [CLAUDE.md](../../CLAUDE.md).
