# Fonts

Three families, all under the SIL Open Font License — free to use, embed and
redistribute, including commercially. Verified 2026-08-02.

| Role | Family | Token | Weights used |
| --- | --- | --- | --- |
| Display | Cormorant Garamond | `--pw-display` | 500, 600, 400 italic |
| Body | EB Garamond | `--pw-body` | 400, 400 italic |
| Utility | Courier Prime | `--pw-utility` | 400 |

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
--pw-display: "Cormorant Garamond", Garamond, Georgia, serif;
--pw-body:    "EB Garamond", Garamond, Georgia, serif;
--pw-utility: "Courier Prime", ui-monospace, "Courier New", monospace;
```

Garamond and Georgia are acceptable substitutes in body copy on a machine
without the webfont. **They are not acceptable in the wordmark** — see
`brand/wordmark.html`. If Cormorant cannot load, use the wordmark artwork
in `assets/` rather than letting a fallback set the name.

## A parsing note

A design-system tool reading `tokens.css` may report a missing font named
`+ 0.42vw`. There is no such font. It is a misread of

```css
--pw-text: clamp(1.0625rem, 0.98rem + 0.42vw, 1.1875rem);
```

where the fragment `+ 0.42vw` is mistaken for a family name. The only real
families are the three above.
