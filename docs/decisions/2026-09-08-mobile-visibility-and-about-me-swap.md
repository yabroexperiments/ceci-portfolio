# 2026-09-08 — mobile visibility bugs, the About Me rebuild, and four ways a check lied

Second half of the 202609 session. Earlier half:
`2026-09-08-202609-drop-ui-design-archive-and-webp.md` (drop integration, WebP,
and the mobile blank-page bug in its addendum).

Shipped `16f4596` `6925d86` `b90056f` `ee3f4db` `e12ae27` `381a874` `481a605`
`e74f011` `55206d2` — all live and verified against production.

---

## Project decisions

### /about-me/ is now the v2026 page (Ceci approved 2026-09-08)
The rebuilt page **replaced the IM Creator one at its own URL** rather than
living beside it, so the homepage pill, external links and bookmarks keep
working with no redirect. The review URL `/about-me-2026.html` is retired.

Its source is `patches/about-me-2026.html` — authored by us, so it stays OUT of
`2026 portfolio/`, which remains purely Ceci's export. `PROPOSALS` in
`integrate_2026.py` carries an `out` path; anything with a `/` in it is passed
through `to_subdir()`, which shifts every relative `href`/`src` up one level.

Its shell (head, tokens, nav, footer, scripts) is **sliced verbatim from
ui-design.html** so the chrome and type scale match by construction rather than
by eye. Content is Ceci's own text, verbatim. English only, exactly as the old
page was; nav/footer keep their `data-i18n` so a Chinese bio needs only copy.
The EN/中 switcher is removed from this page — nothing to switch.
Portrait is the existing 1045×1045 asset, already circular with transparent
corners, shown at **140px centred**, matching what the old page rendered at both
390px and 1440px.

### The reveal system had two independent failure modes, both now closed
1. `IntersectionObserver(..., {threshold: .1})` is **unsatisfiable** once the
   observed element exceeds ~10× the viewport (see GLOBAL CANDIDATE below).
   Now `threshold: 0` on every page.
2. A backstop `__reveal()` runs immediately, on rAF, on DOMContentLoaded and
   after load, revealing any on-screen `.reveal`. Gating it on `load` alone was
   not enough — ui-design waits on 17 images, and the hero revealed while the
   grid stayed hidden.

### The canvas, not the footer, paints below the document
A white strip under the black footer on iOS was **not** layout: every page's
footer already ends exactly at the document end. The overscroll region and the
bottom safe-area are painted from the **canvas**, which takes `<html>`'s
background, or `<body>`'s when html has none. No page set one on html.
Now `html{background:#0b0b0f}` on every page, gated so the build fails if the
footer is ever restyled away from that colour, or if the rule fails to inject.
**Trade-off accepted:** the same canvas shows at the TOP, so overscrolling above
the nav now reveals dark. One canvas cannot be light at one end and dark at the
other. No `<meta name="theme-color">` was added — it tints the whole browser UI
and that is a design decision for Ceci.

### IM Creator page anatomy, as measured
Needed by anything that manipulates the wrapped archive pages:
`div.xprs-holder > div.main-page > div#content`; header is `div.header-box` /
`.header-wrapper`; **no `<nav>` or `<footer>` elements exist**; the pager block
is a `div.gallery-box` ~68px tall (visibly BLUE on htc_dot-view) and the
copyright block ~262px; laid out at runtime by `_imc/js/spimeengine.js`; several
pages carry under 30 characters of text and use CSS `background-image`, not
`<img>`.

---

## GLOBAL CANDIDATE — a threshold expressed as a FRACTION of the observed element becomes unreachable once that element outgrows the viewport

`threshold: 0.1` reads as "a bit of it" but means *a fraction of the element*,
not of the screen. Past ~10× the viewport the condition can never be met —
silently, with no error, and only on the smaller screens where the element is
tallest. Measured: a 8095px mobile grid needs 810px visible inside a ~660px
phone viewport; the same grid is 3400px on desktop and fires fine.
Any percentage-of-target trigger — IntersectionObserver thresholds, "50% viewed"
analytics, scroll-depth gates — needs the required pixels compared against the
**smallest viewport you support**. Prefer `threshold: 0` plus a `rootMargin`,
which is expressed in pixels and cannot become unreachable.

## GLOBAL CANDIDATE — hiding the leaf leaves the box; `innerText` cannot see the difference

Hiding the element that *holds* unwanted text removes the words and leaves its
container's height and background standing. Every wrapped archive page carried
~330px of dead space above the footer this way.
It survived verification because the check read `innerText`, and **`innerText`
excludes hidden descendants** — the words were gone, so the assertion passed,
while the box was still on screen. `textContent` would have seen them; a
screenshot did.
Two rules: when removing chrome, hide the **outermost** element that is still
plausibly chrome (bound it by rendered height, never by depth alone); and never
assert the absence of a visual element through a text API.

## GLOBAL CANDIDATE — a block element's width always equals its container's, so "does it fit?" measured that way is vacuous

Checking whether a heading fits on one line by comparing
`h1.getBoundingClientRect().width` against the available width is meaningless:
an `h1` is a block, so the two are identical at every viewport (measured
288/288, 736/736…). The check returns "fits" for **any** font size, and with
`white-space: nowrap` the failure would have been silent clipping rather than
visible wrapping.
Measure the **text**, not the box: `range.selectNodeContents(el)` then
`getBoundingClientRect()`, or compare `scrollWidth` against `clientWidth`.
Same family as "a gate's pass covers only the criteria it measures".

## GLOBAL CANDIDATE — a page assembled from a source shell inherits that source's unfixed code

The About Me draft was sliced from Ceci's `ui-design.html` **source**, while the
reveal fixes are applied by the build as patches to files in `PAGES`. The
proposals branch skipped `PATCHES` entirely, so the new page shipped with the
exact `{threshold:.1}`-and-no-failsafe combination that had blanked another page
hours earlier. Its own numbers happened to survive, which is luck, not
correctness.
**Anything derived from an unfixed source must re-enter the same pipeline as
everything else.** If a build applies corrective patches, every emitted artifact
goes through them — a second code path that writes files is a second place for
every known bug to reappear.

## GLOBAL CANDIDATE — before believing a user's "it's still broken", check what their cache was serving

A screen recording showed the white strip 8 minutes after the fix was committed
and ~5 minutes after it deployed. GitHub Pages sends `cache-control: max-age=600`
— a 10-minute window — so the device was almost certainly serving the pre-fix
copy, and the recording was evidence about the OLD build.
Before treating a report as a failed fix, reconcile three clocks: when the fix
deployed, when the observation was made, and how long the delivery layer caches.
`stat` the file and read `format_tags=creation_time` off the video; read
`cache-control` off the served asset. Corollary already known and re-earned:
every "it's live" message ships with the refresh instruction attached.

## GLOBAL CANDIDATE — a destructive test fixture must not be able to name the real file

While feeding known-bad input to the build gates, one `perl -0pi -e` in the loop
was written against the **real** `patches/legacy-wrapper.js` instead of the
sandbox copy, and corrupted a shipped file. The build gate caught it on the next
run, which is the only reason it did not ship.
Construct such fixtures so a typo cannot resolve to the original: `cd` into the
sandbox once and use **relative paths only**, never a variable holding the source
root in the same script that mutates files — and re-run the real build after the
matrix, not just the sandbox one.

## GLOBAL CANDIDATE — reading a screen recording

Useful and cheap, worth keeping as a recipe:
- `ffmpeg -i in.mp4 -vf "fps=2,scale=440:-1" -q:v 3 f_%03d.jpg` for an overview.
- To find *when* something appears, reduce each frame's region of interest to a
  single pixel and dump the series:
  `-vf "fps=4,crop=W:H:X:Y,scale=1:1" -f rawvideo -pix_fmt gray -` then read the
  bytes. A brightness column located the white band to a 3-second window instantly.
- To identify *what* a band is, scan one column at full resolution
  (`-f rawvideo -pix_fmt rgb24`) and print colour transitions with their y — that
  gave `footer #0b0b0f ends y=1194, white 254,254,255 to y=1280`, i.e. an 85px
  band ≈ 56pt on the device, which is Safari-bottom-bar sized.
- Convert to device points before interpreting: video px ÷ (video height ÷
  viewport points).
