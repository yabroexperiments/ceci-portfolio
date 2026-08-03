# Legacy build tooling — DO NOT RUN against site/

## rip_live.py — RETIRED 2026-08-03

This script mirrors www.changhsiju.com (IM Creator) into mirror_v2/. It was the
v2 build pipeline **until the standalone-assets migration** (branch
feat/standalone-assets): site/ now self-hosts every asset (685 files under
site/assets/) with zero runtime dependency on IM Creator or Google CDNs —
verified by a 25/25-page runtime sweep and an independent adversarial audit.

**Re-running this ripper and copying its output into site/ would re-introduce
every IM Creator dependency and destroy that work.** The git repo — not the
IM Creator site — is now the source of truth.

If content must ever be pulled from IM Creator again: rip into mirror_v2/,
then run `python3 localize_assets.py` and re-verify BEFORE replacing site/.
