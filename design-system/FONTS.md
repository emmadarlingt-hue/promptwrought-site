# Fonts

Three families, all under the SIL Open Font License — free to use, embed and
redistribute, including commercially. Verified 2026-08-02.

| Role | Family | Token | Weights used |
| --- | --- | --- | --- |
| Display | Cormorant Garamond | `--pw-font-display` | 500, 600, 400 italic |
| Body | EB Garamond | `--pw-font-body` | 400, 400 italic |
| Utility | Courier Prime | `--pw-font-utility` | 400 |

## Direct downloads

Canonical files from Google's own font repository. These are complete fonts —
prefer them over the `fonts.gstatic.com` URLs in the CSS API, which are
per-subset slices with opaque hashed names.

**Cormorant Garamond**
- [CormorantGaramond\[wght\].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf) — variable, 1.2 MB
- [CormorantGaramond-Italic\[wght\].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/CormorantGaramond-Italic%5Bwght%5D.ttf) — variable italic, 716 KB

**EB Garamond**
- [EBGaramond\[wght\].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/ebgaramond/EBGaramond%5Bwght%5D.ttf) — variable, 851 KB
- [EBGaramond-Italic\[wght\].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/ebgaramond/EBGaramond-Italic%5Bwght%5D.ttf) — variable italic, 754 KB

**Courier Prime**
- [CourierPrime-Regular.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/courierprime/CourierPrime-Regular.ttf) — 71 KB

Bold and italic cuts of Courier Prime exist in the same directory but this
system never uses them: utility type is 400 only, and nothing in the brand is
ever set in bold.

The two variable files per Garamond cover every weight the system asks for, so
five files is the whole set.

## How the fonts load

All three families are served from Google Fonts, imported at the top of
`tokens.css` so the @font-face rules travel with the token layer — any page
that links `tokens.css` gets the real faces without its own font `<link>`.

```css
@import url("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300..700;1,300..700&family=EB+Garamond:ital,wght@0,400..800;1,400..800&family=Courier+Prime:wght@400&display=swap");
```

Those ranges cover every weight the system uses: display 500 and 600, body 400,
italic 400, utility 400.

**This means the design system depends on Google Fonts at render time.** No font
binaries are uploaded to the Claude Design project — `brandFonts` resolves
because the families are reachable over the CDN, not because they are embedded.

The five files *are* vendored in this repo under `design-system/fonts/`, each
family beside its OFL licence — the licence must travel with the fonts when they
are redistributed. To self-host, swap the @import for local @font-face rules
pointing at those files. Their weight axes:

| File | Axis | Covers |
| --- | --- | --- |
| CormorantGaramond\[wght\] | 300–700, default **300** | display 500, 600 |
| EBGaramond\[wght\] | 400–800, default 400 | body 400 |
| CourierPrime-Regular | static | utility 400 |

**Mind Cormorant's default.** Its default instance is 300 (Light), so anything
that uses the family without naming a weight renders Light — noticeably thinner
than the 600 the wordmark is set in. Every rule in this system states its
weight explicitly. Keep it that way.

## Specimens and upstream sources

| Family | Specimen | Upstream |
| --- | --- | --- |
| Cormorant Garamond | [fonts.google.com](https://fonts.google.com/specimen/Cormorant+Garamond) | [CatharsisFonts/Cormorant](https://github.com/CatharsisFonts/Cormorant) |
| EB Garamond | [fonts.google.com](https://fonts.google.com/specimen/EB+Garamond) | [octaviopardo/EBGaramond12](https://github.com/octaviopardo/EBGaramond12) |
| Courier Prime | [fonts.google.com](https://fonts.google.com/specimen/Courier+Prime) | [quoteunquoteapps/CourierPrime](https://github.com/quoteunquoteapps/CourierPrime) |

Note: `fonts.google.com/download?family=…` returns the web app's HTML, not a
zip. It is not a direct download link, despite looking like one.

## Fallbacks

```css
--pw-font-display: "Cormorant Garamond", Garamond, Georgia, serif;
--pw-font-body:    "EB Garamond", Garamond, Georgia, serif;
--pw-font-utility: "Courier Prime", ui-monospace, "Courier New", monospace;
```

Garamond and Georgia are acceptable substitutes in body copy on a machine
without the webfont. **They are not acceptable in the wordmark** — see
`brand/wordmark.html`. If Cormorant cannot load, use the wordmark artwork
in `assets/` rather than letting a fallback set the name.

## Why the tokens are named this way

Design-system tooling classifies custom properties by **name**, not by value.
The first cut of this file used `--pw-display` / `--pw-body` / `--pw-utility`
for the families and `--pw-text` for the body size, and the generated manifest
came back as:

```json
"fonts": [],
"brandFonts": [{ "family": "+ 0.42vw", "status": "no-face", "tokens": ["--pw-text"] }]
```

Zero real fonts, one phantom. `--pw-text` was parsed for a family and yielded
the fragment `+ 0.42vw` out of its `clamp()`; the three actual families were
typed as `other`, because `--pw-display` reads as the CSS `display` property.

Hence the rule: **families are `--pw-font-*`, sizes are `--pw-size-*`.** Never
name a size token after text or type — `--pw-text`, `--pw-type`, `--pw-copy`
will all be mined for a font family they do not contain.
