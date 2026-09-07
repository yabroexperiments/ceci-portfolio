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
