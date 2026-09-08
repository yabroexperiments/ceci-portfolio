# 2026-09-08 — Ceci's 202609 drop: UI Design archive, wrapped legacy pages, WebP

Session shipped `4d5c0d2` (drop integration) and `b215b88` (WebP switch).
Both live on changhsiju.xyz and verified against production.

---

## Project decisions

### The v2026 architecture now has three layers, not two
`index.html` + 6 case studies + **`ui-design.html`** (new archive index) →
**`legacy-project.html?project=<key>`** (iframe wrapper) → the 17 preserved
IM Creator pages at `/coinful/`, `/htc_mini/`, …

The wrapper is the point: it renders a 2011–2020 archive page inside the v2026
nav and footer so a visitor never lands on a bare IM Creator page. Ceci's export
built the wrapper but linked the cards straight past it; the integration reroutes
them. **If a card's `?project=` key is ever wrong, the wrapper silently falls
back to Coinful** — hence the gate that resolves every key against the wrapper's
own `projects` map.

### Her export now passes through an HTML formatter
Attributes are reordered and lowercased, void tags self-closed
(`<link href=… rel=…/>`, `viewbox`). This **silently broke both existing
integration patches** — a `str.replace()` keyed to one attribute order matched
nothing and reported success. Every patch in `integrate_2026.py` is now
attribute-order-agnostic. Assume the next drop is formatted differently again.

### What an IM Creator archive page actually looks like (measured)
Needed by anything that manipulates them inside the wrapper:
- **No `<nav>`, `<footer>`, `.navbar`, `.site-nav`, `.site-header` elements at
  all.** The header is `div.header-box` / `div.header-wrapper` (95px tall).
- Content root: `div.xprs-holder.desktop-mode > div.main-page > div#content`.
- Laid out at runtime by `_imc/js/spimeengine.js`.
- Many are **extremely sparse** — `htc_mini` has 9 characters of text,
  `mozilla_smart-tv` has 21 — and use CSS `background-image`, not `<img>`.
- The pager reads `PREVIOUS NEXT` mid-sequence but `PREVIOUS HOME` on the last
  page (`htc_tablet`). A bare `HOME` is *real content* on `mozilla_car-ui`,
  whose screens are labelled HOME / Dashboard / Climate.

### Sticky nav: two innocuous rules that kill it together
`html{overflow-y:scroll}` (new in her drop) + `body{overflow-x:hidden}`
(pre-existing) makes **body** a scroll container, so `nav`'s `position:sticky`
resolves against a scrollport that never scrolls. Measured: scroll 0→3000 gave
`navTop` 0→−3000 locally vs a constant 0 on production. Either rule alone is
fine. `scrollbar-gutter:stable` carries her stated intent and is **kept**; only
`overflow-y:scroll` is stripped, by a patch that fails the build if she stops
emitting it. If a future drop reintroduces a sticky-header bug, check this pair
first.

### i18n-cases.js now has TWO IIFEs with opposite merge semantics
The original block (`var ADD`) is **non-overwriting** (`if (!dict[k])`); the new
2026-09 block (`var X`) is **overwriting** (`dict[k] = X[k]`). Consequence:
`card.wallet.*` / `card.leader.*` in `i18n.js` are dead — the overlay's
`card.leaderboard.*` / `card.tw.*` win. `I18N_KEY_REMAP` still matches so it
stays, but it is now belt-and-braces, not load-bearing.

### WebP: lossy, but adopted after measurement
49 usable twins, dimensions identical to the PNG, SSIM 0.929–0.999 /
PSNR 37.1–52.0 dB, indistinguishable at 3× magnification. 33.2 MB → 15.4 MB
across the case studies. **`bnct-app-05.webp` arrived ZERO-BYTE** — her
conversion failed on that one image; it is listed in `WEBP_SKIP` and keeps
serving the PNG. **31 PNGs still have no twin**, including 7 of the homepage's
10 — that is the largest remaining win (homepage would go 3.63 MB → ~0.9 MB).
PNGs stay deployed: `og:image` / `twitter:image` must remain PNG for chat-app
scrapers.

### Not deployed, deliberately
`coinful.html` — a one-off wrapper superseded by
`legacy-project.html?project=coinful`. It also diverges structurally (ids
`portfolioNav` / `portfolioFooter`, so the shared `nav#nav` CSS does not reach
it; no `data-i18n` in its nav). Its restyle logic was the better of her two
wrappers and was ported into `legacy-project.html`.

### Self-hosted Inter ships weights 400/500/600 only
No page uses 700/800, so coverage is complete today even though her Google Fonts
URL requests `400;500;600;700;800`. **If she starts using 600+ weights the
browser will synthesize them** — add the faces to `site/assets/fonts/inter/`.

---

## GLOBAL CANDIDATE — a text-extraction harness cannot see iframe, canvas, or CSS-background content

I ran an `HTMLParser` text extractor over two files, got nav + footer and nothing
else, concluded "empty shells", and **wrote that false conclusion into the build
script's `STUBS` list**. They were iframe wrappers holding the entire archive
feature. It took AC relaying one sentence from Ceci to catch it.

**"This file has no content" is a claim about the world produced by an
instrument that is structurally blind to several kinds of content** — iframes,
`<canvas>`, `<object>`, CSS `background-image`, JS-injected DOM. An `<img>` count
misses the last two as well. Before labelling any file a stub, empty, dead, or
safe to delete, read the raw markup between the landmarks (`</nav>` → `<footer>`),
not the extracted text. Companion to the existing "verify an absence by a second
method" rule, with a sharper edge: here the second method is *the source itself*.

## GLOBAL CANDIDATE — a "small block" heuristic inverts on sparse content

Ceci's chrome-remover hid the first ancestor with `children <= 4 && text < 180
chars`, intending a footer strip. On image-led pages with almost no text **the
entire page satisfies that predicate**, so it hid `div.main-page` and rendered
three archive entries as 0px blank. My first guard ("don't cross an element
containing an `<img>`") did not help, because those pages use CSS
`background-image`.

Any heuristic that identifies *chrome* by being small/short/sparse must be bounded
by something content cannot accidentally satisfy: a **rendered-height ceiling**
(a footer strip is short, a page is not), an explicit container denylist, and
**leaf-most matching only** (an element containing another match is never the
strip). Same family as "a gate that rejects a match must not discard the position
the match established" — the failure is a predicate that is true of the thing you
are trying to protect.

## GLOBAL CANDIDATE — a harness returning a uniform result for every input is reporting on itself

Twice in one session:
- an ffmpeg SSIM loop returned `ERR` for all 50 image pairs — `-v error`
  suppressed the stats line the filter logs at info level;
- a shell page-weight loop reported `imgs=1` for all 8 pages.

Neither was a fact about the data. **Before reading any sweep result, calibrate
with a positive control (a known-identical input must score perfect) and a
negative control (a known-different input must score badly).** Doing that turned
the SSIM numbers from noise into evidence: self-vs-self `1.000000`, two different
images `0.246563`. A uniform column — all pass, all fail, all identical — is the
tell. Extends "never trust a detector you haven't fed known-bad input" to the
measurement side.

## GLOBAL CANDIDATE — a known-bad matrix must not be able to reach the real files

While testing gates in a sandbox copy, one `perl -0pi -e` in my loop was written
against `$R/patches/legacy-wrapper.js` — the **real repo path** — and corrupted
the shipped wrapper's project map. The build gate caught it immediately, which is
the only reason it did not ship.

Destructive test fixtures must be constructed so a typo cannot resolve to the
original: `cd` into the sandbox once and use **relative paths only**, never a
variable holding the source root in the same script that mutates files. And run
the real build after the matrix, not just the sandbox one — the control that
caught this was rebuilding the actual repo.

## GLOBAL CANDIDATE — a terse follow-up instruction outranks the option the user picked from my menu

AC answered an `AskUserQuestion` with "keep the archive links as-is", then
immediately sent "go 1-4", which included the two items that option declined.
The verbatim instruction won, and it agreed with what he had originally relayed
from Ceci ("the HTMLs should all be linked") — so the *menu answer* was the
outlier, not the follow-up.

An option set I authored carries my framing, and picking from it is cooperation
with the menu rather than an independent decision. **When a later free-text
instruction contradicts an earlier menu pick, follow the free text, say in one
line which one you are following and why, and do not stop to re-ask.** Confirms
the existing "an interview option set is a steering device" rule from the
generation side.

## GLOBAL CANDIDATE — environment traps for the Claude Code browser + macOS TCC

Cost real time this session; both are structural, not incidental.

- **A static server spawned by `preview_start` cannot read `~/Documents`** (macOS
  TCC). It starts fine and 404s every file — an empty-looking site, not an error.
  `python3 -m http.server` also dies at *argparse* time with
  `PermissionError` because `--directory`'s default calls `os.getcwd()`.
  Fix: copy the site into the session scratchpad and serve from there with a
  script that `chdir`s to an absolute path.
- **A hidden browser pane never fires `requestAnimationFrame`**, does not run CSS
  animations, does not animate `scroll-behavior: smooth` (so `scrollTo` appears
  to do nothing and `scrollY` sticks), and does not repaint for screenshots taken
  after a programmatic scroll. Use `setTimeout`, set `scroll-behavior: auto`
  before measuring scroll, prefer structural measurement over screenshots, and
  split long `await` loops across calls or the tool times out at 45s.

---

# Addendum — ui-design.html was blank on mobile (fixed `16f4596`, `6925d86`)

AC opened the page on his phone after the wrap: blank. It renders on desktop.

## Root cause: an IntersectionObserver threshold that cannot be satisfied
Her shared reveal snippet uses `IntersectionObserver(…, {threshold: .1})` —
"fire when 10% of this element is visible". **For an element more than ~10× the
viewport height, 10% of it does not fit on screen, so the observer never fires at
any scroll position** and the block stays at `.reveal{opacity:0}` forever.

Measured on production at 375px wide:
| | grid height | needs visible | viewport | result |
|---|---|---|---|---|
| desktop, 3 columns | ~3,400px | 340px | 900px | fires |
| mobile, 1 column | **8,095px** | **810px** | ~660px usable | **can never fire** |

Two things made this a *blank page* rather than a missing animation:
`ui-design.html` collapses its 17 cards to one column under 620px (uniquely tall),
and it is the only page where `.reveal` wraps **all** the content — every other
page has an ungated hero, so a failed observer there costs a fade, not the page.

Fix: `threshold: 0` on all 8 pages, plus a failsafe that reveals any on-screen
`.reveal` immediately / on rAF / on DOMContentLoaded / after load. Gating the
backstop on `load` alone was not enough — this page waits on 17 images, and the
hero revealed while the grid stayed hidden.

## GLOBAL CANDIDATE — a threshold expressed as a FRACTION of the observed element is unsatisfiable once that element outgrows the viewport

`threshold: 0.1` reads like "a bit of it", but it means *a fraction of the
element*, not of the screen. The moment the element exceeds 10× the viewport the
condition becomes unreachable — silently, with no error, and only on the smaller
screens where the element is tallest. Any percentage-of-target trigger
(IntersectionObserver thresholds, "50% viewed" analytics, scroll-depth gates,
lazy-load margins) needs the same sanity check: **compare the required pixels
against the smallest viewport you support.** Prefer `threshold: 0` plus a
`rootMargin` when you want "slightly after it enters" — that is expressed in
pixels and cannot become unreachable.

## GLOBAL CANDIDATE — an entrance animation must never be the only thing standing between a user and the content

`.reveal{opacity:0}` with JS as the sole path to `opacity:1` means **every
failure mode of that JS is a blank page** — an unmet threshold, an unsupported
API, a throw earlier in the same script, a slow `load` event. Content should
default to visible and be *hidden* by JS that has proven it will also unhide it,
or carry an unconditional backstop. When reviewing a reveal-on-scroll pattern,
the question is not "does it animate?" but "what does the user see if this
script never runs?"

## GLOBAL CANDIDATE — a near-blank render is EVIDENCE, not a rendering artifact, until proven otherwise

I verified this page as working. My very first screenshot of it was almost blank
— a faint ghost of the heading and nothing else — and I explained that away as
"the hidden pane doesn't run CSS animations", then switched to structural
measurement that confirmed 17 cards in the DOM with decoding images. Every one of
those measurements was true. The page was still blank for the user.

**A dismissed anomaly needs a positive explanation, not a plausible one.** The
honest move was to ask *why* the animation state matched a broken-page state so
exactly, and to note explicitly that appearance was unverified rather than let
structural passes stand in for it. Two concrete rules for this environment:
- **Structural checks (DOM present, images decode, links resolve) cannot see a
  visibility bug.** `opacity: 0` passes all of them.
- **The hidden pane cannot fire IntersectionObserver at all**, so any
  reveal-on-scroll behaviour is simply *unverifiable* here — that must be stated
  as an open item, not silently covered by adjacent green checks. The root cause
  here was ultimately found by arithmetic (element height vs viewport), which is
  environment-independent — reach for that when the loop cannot see.
