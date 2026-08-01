# Promptwrought — design system

A workshop of words. **Two surfaces, one accent, three voices.**

Everything here is derived from the existing artwork (`assets/promptwrought-*.png`),
the portable lockup sheet (`assets/promptwrought-web.html`) and the live site
(`index.html`). Nothing was invented that contradicts them.

## The sheets

| Sheet | What it fixes |
| --- | --- |
| `foundations/colour.html` | 10 tokens, approved pairings, measured contrast ratios, rule weights |
| `foundations/typography.html` | The three voices, the 9-step scale, the squeeze, the tracking floor |
| `foundations/layout.html` | Measure, gutter, the band, vertical rhythm, motion |
| `brand/wordmark.html` | Primary + reversed, clear space, minimum size, six misuses |
| `brand/monogram.html` | P·w in double rule, size steps down to favicon |
| `brand/masthead.html` | The locked issue lockup, the banner, the web header |
| `components/labels.html` | Eyebrows, numerals, issue numbers, tags, the interpunct |
| `components/dictionary-entry.html` | The signature block, with its five-part anatomy |
| `components/lexicon-entry.html` | The archive unit — definition, etymology, citation, the case |
| `components/process-stages.html` | The roman-numeral grid |
| `components/prose.html` | Running copy, pull quote, editor's note, prose rules |
| `components/actions.html` | Buttons, links, focus, states — on light and reversed |
| `components/forms.html` | Email capture, input states, the subscribe band |
| `components/surfaces.html` | The band stack, footer, reversed token swaps |

Each sheet is a standalone HTML file with its tokens inlined, so it renders
anywhere with no build step and no shared stylesheet.

## Using the tokens

`tokens.css` is the machine-readable version, namespaced `--pw-*` so it can be
dropped into any project without colliding. The site's own `index.html` uses
unprefixed names (`--ink`, `--parchment`) — both are the same values.

## Three things worth knowing before you use this

**1. The accent has three values, not one.** Reds sit in an awkward part of the
luminance range. `#C2451C` on parchment measures 3.9 : 1 — fine for the
interpunct and display type, below AA for anything at body size. Use
`--pw-hot-metal-deep` (#A63914) for accent text and accent fills on light, and
`--pw-hot-metal-light` (#E0703F) for accent text on ink. They are visually
near-identical; only the checker can tell.

**2. There is a live accessibility bug on the site.** The subscribe band in
`index.html` is filled with `--hot-metal` and carries a 0.95em note in
parchment — 3.9 : 1, below AA. Swapping that one fill to `#A63914` fixes it and
looks the same. `components/forms.html` shows the corrected band.

**3. Radius is zero, everywhere.** The system is built from rules and
rectangles. A single rounded corner reads as a different brand instantly.

## Nothing here is bold

Emphasis is italic throughout. A serif at body size with a bold run in it reads
as a second typeface. The only weight change is between display 500 and 600.
