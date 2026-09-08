# 2026-09-08 — Debugging an unresponsive parallel local session

Cloud session (`claude/parallel-local-session-debug-vfjlkx`), Opus 5, ~12:00–13:00 TPE.
AC asked what was going on in a local Claude Code session that had stopped
responding to anything he typed. **This session changed no site code.** Its output
is a diagnosis, a correction of that diagnosis, and one technical finding about
`integrate_2026.py` that is still open.

---

## What the local session actually was

`session_01S8mtbyQQYUnsYziWPY1wme` — "Ceci's portfolio website analysis", Claude
Code CLI on AC's Mac, reached from cloud as `environment_kind: bridge`. Started
2026-09-08 00:00 TPE, still running at 13:00. Eight commits straight to `main`:
the 202609 drop, the WebP swap, a `/wrap`, three visual fixes, then the About Me
proposal and its pipeline fix.

### It was working directly on `main` for 13 hours

`current_branches: {ceci-portfolio: "main"}`. No `claude/<slug>` branch, so none
of the multi-session machinery at the top of `CLAUDE.md` applied to it: no branch
to partition by files, nothing for the 5-branch cap to count, no merge gate. It
happened to collide with nothing — this cloud session was the only other one and
carried zero commits — so there is no damage to repair. Recording it because the
protocol exists precisely to make that outcome not depend on luck.

### It wrapped at 06:36 and then shipped five more commits

`ed92203` is a formal `/wrap`. Its brief (`docs/handoffs/handoff-2026-09-08-0635.md`)
says *"No in-flight work, nothing half-refactored, no branch to clean up."* Five
commits landed after it and none are in that brief. A `/backtowork` off it would
have briefed a state that no longer existed.

---

## GLOBAL CANDIDATE — a long turn and a hung session are the same observation from outside; do not act on the difference until you have separated them

AC reported "it is not responding to anything I type." I read the session record —
`WORKING`, `connection_status: connected`, no commit for 2h43m, and a
`worktree_state.reported_at` still frozen at the session-start snapshot 12 hours
earlier — and concluded it was wedged below the interrupt checkpoint, most likely
in a hung browser call. I told AC to press `Esc`, then `Ctrl+C` twice, then
`pkill -f playwright`.

**It was not hung.** It was mid-turn authoring a 447-line page, and it pushed 32
minutes later. Following my recovery steps would have destroyed in-flight work.

Both facts were true at once: a turn that long genuinely does block typed input
until it ends, so the symptom AC reported and "everything is fine" are the same
state. The evidence I had could not tell them apart, and I picked the alarming
reading and issued destructive advice on it.

The generalizable rule: **an external observer of an agent session can see
liveness but not progress.** `status: WORKING` and a live-refreshing `updated_at`
prove the process is alive; they say nothing about whether the turn is advancing.
Silence is not evidence of death — a big authored artifact and an infinite loop
produce identical telemetry. Before recommending anything that discards work,
either find a signal that actually distinguishes them (does the transcript grow?
is CPU burning? does a child process exist?) or say plainly that you cannot tell
and give the non-destructive option first. Reversibility should be ranked ahead
of speed when the diagnosis is a guess.

## GLOBAL CANDIDATE — `interrupt_session` carries `cancel_queued: true`, so it discards what the user typed

The remote-control interrupt emits `{"subtype":"interrupt","cancel_queued":true}`.
Anything the user had queued is dropped along with the turn. When you interrupt a
session on someone's behalf, **tell them their input is gone and they must retype
it** — otherwise they wait on a message the system has already thrown away.

Related, and worth knowing before reaching for it: from a cloud container there is
**no message path to a bridge session at all**. `ListAgents` reports "no other
Claude session is running on this machine" because the container is not that
machine, and the claude-code-remote MCP exposes `interrupt_session` but no
send-message tool for it. You can knock; you cannot talk. Plan around that rather
than discovering it mid-incident.

## GLOBAL CANDIDATE — when a fix duplicates a code path instead of joining it, the bug class survives the bug

`e12ae27` is a good catch and an incomplete fix, and the gap is instructive.

The local session added a `PROPOSALS` map for pages we author (as opposed to
Ceci's export). A proposal is sliced from her shell, so it inherits her *unfixed*
source — and the new branch skipped `PATCHES` entirely, so the About Me draft
shipped with the same `{threshold:.1}` reveal defect that had blanked
`ui-design.html` on mobile hours earlier. It caught this three minutes after
shipping and fixed it.

But the fix **copies** the pages loop rather than sharing it, and the two copies
have already drifted in three measurable ways (detail below). The instance is
fixed; the class — "a new page category bypasses the gate by default" — is not.
A fourth category added later bypasses `PATCHES` again for exactly the same
reason.

The principle, which is our own "conditions enforced in code, not memory" rule
pointed at control flow: **a gate that must be remembered per call site is not a
gate.** When you find that a code path skipped a required step, prefer making the
step unskippable (one loop, one entry point, the flag as data) over adding the
step to the second copy. Two parallel loops mean every future change to one is a
silent bug in the other, and the drift is invisible because both sides keep
passing.

## GLOBAL CANDIDATE — an aggregate "did this ever fire?" counter cannot detect a per-item failure

`integrate_2026.py` gates on `patch_hits[name] == 0` → "PATCH never matched, its
cause is gone." The counter is summed across every page a patch is listed for.
The reveal patches are now listed for 9 pages, so a patch going dead on **one**
page leaves the counter non-zero and the gate silent.

This is not hypothetical for this repo: the code's own comment records that
Ceci's formatter reordered attributes and broke the literal-string form of both
remaining patches once already. The gate catches "this patch is dead
everywhere"; the failure that actually happens is "this patch is dead on the one
page whose source changed."

Generally: **a check that ORs across a collection answers a weaker question than
the one you care about.** If the unit of failure is the item, the assertion has
to be per-item — `hits[patch][page]`, not `hits[patch]`. Aggregate counters are
reassuring precisely when they are least informative, because the healthy members
mask the sick one.

---

## OPEN — three concrete asymmetries between the `PAGES` and `PROPOSALS` loops

Found by reading `integrate_2026.py` at `e12ae27`; **not fixed** — AC ran `/wrap`
before ruling on it, and the file is owned by the local session right now.

1. **`patch_hits` is aggregated, not per-page** (`:469`, `:495`, `:534`, `:567`).
   A reveal patch that stops matching on `about-me-2026.html` alone is invisible,
   because the 8 real pages keep the counter positive. This is pre-existing for
   the 8 pages too — `PROPOSALS` only widened it.
2. **The WebP anti-rot check is weaker on the proposals path.** Pages loop:
   `if ref in WEBP_SKIP and "now HEALTHY" not in why` → print, else error.
   Proposals loop: `if ref not in WEBP_SKIP` → error. So a `WEBP_SKIP` entry that
   has become healthy is silently accepted on a proposal page, losing the "the
   list cannot rot" property that `b215b88` was built to guarantee.
3. **`webp_swapped[name]` is never populated for proposals**, so the reported
   KB-saved total silently excludes them. Cosmetic, but it is the same drift.

Suggested shape if AC wants it fixed: one loop over `PAGES | PROPOSALS` with an
`authored: True` flag on proposal entries, so the patch/WebP/meta path is
physically shared and only the source directory differs.

## Verified independently this session (claims from the local session's commits)

Checked at `origin/main` `e12ae27`, so these do not rest on its own reporting:

- `site/about-me-2026.html` carries `threshold:0` and the failsafe.
- **Nothing links to it.** The only two `about-me-2026` references in the whole of
  `site/` are inside the page itself (canonical / og:url).
- `site/about-me/` is byte-identical across `b90056f..e12ae27` — the preserved IM
  Creator page is genuinely untouched.
- All 8 v2026 pages carry `threshold:0` + failsafe; `legacy-project.html` has no
  reveal block, which is correct.
- The only zero-byte file in `site/` is the known, `WEBP_SKIP`-listed
  `images/bnct-app-05.webp`.
- `repo-guards` and Pages deploy are green on `ee3f4db` and `e12ae27`.

---

## ENV — a cloud session cannot reach changhsiju.xyz

The agent proxy returns **403 to CONNECT** for `changhsiju.xyz:443`
(`curl -sS "$HTTPS_PROXY/__agentproxy/status"` lists it under
`recentRelayFailures`, `kind: connect_rejected`). The environment's network
policy does not allow it, and this is not a certificate problem — do not go
looking for a TLS fix.

Consequence worth planning around: **a cloud session on this repo can never
verify production.** It can read the repo, read the GitHub Actions result, and
confirm the deploy reported success — it cannot fetch a page from
`changhsiju.xyz` to see what shipped. For a project whose last three bugs were
all visual and all missed by structural checks, that is a hard limit on what
cloud work can claim. Pair it with the existing rule in `CLAUDE.md`: pixel-visual
verification belongs in a local loop, and a cloud session should say
"unverified — needs device" rather than infer from a green deploy.

Also true, and cheap to hit: `bs4` is not installed in the cloud container, so
`integrate_2026.py` cannot be run there at all. The gate is a local-only tool.
