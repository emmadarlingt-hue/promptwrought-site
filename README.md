# promptwrought-site

The site behind [promptwrought.com](https://promptwrought.com). One static page,
`index.html`, plus the brand `design-system/` and `assets/`.

## Adding an issue

A word appears in two places: the "lexicon so far" on the front page, and the Type
Case at `/calendar`. Both are generated from the same source — one JSON file per
issue — so that file is the only thing written by hand.

Don't edit either output. Everything between `<!-- lexicon:start -->` and
`<!-- lexicon:end -->` in `index.html` is overwritten, and so is the whole of
`calendar/words.js`.

1. Write `issues/00N-<word>.json`, copying the shape of an existing one:

   | field        | notes                                                        |
   | ------------ | ------------------------------------------------------------ |
   | `no`         | issue number; drives the `Nº` counter, the ordering, and the calendar week |
   | `word`       | the headword                                                  |
   | `pos`        | part of speech, e.g. `n.` or `n. & v.`; written out in full on the calendar |
   | `pron`       | pronunciation, backslash-delimited — escape as `\\` in JSON   |
   | `tag`        | the one-word category pill, e.g. `Asking`, `Keeping`          |
   | `definition` | the sense line under the headword                             |
   | `etymology`, `in_use`, `the_case` | the three fields below it                |
   | `issueUrl`   | the Substack link; the calendar's "Read issue" link stays hidden while empty |
   | `note`       | optional; an aside shown under the definition on the calendar |
   | `next_word`  | optional; names next issue's word in the closing line         |

   Values are HTML fragments, so `<em>` works. A bare `&` is escaped for you.
   `in_use` is wrapped in `<cite>` and curly quotes — write it bare.

2. Regenerate and read the diff:

   ```bash
   python3 tools/build-lexicon.py && git diff
   ```

   Entries render newest first. `--check` exits non-zero if either output is stale,
   and writes nothing.

3. Commit. **Push after the Substack issue has actually gone out** — pushing early
   puts the word on the site before subscribers get the email. The script warns if
   an issue is dated in the future.

### How an issue becomes a calendar week

The tray is one calendar year and the run opens at week 31, so **issue N is week
N + 30**: issue 001 is week 031. The release date is the Tuesday of that ISO week,
worked out for you. Weeks with no issue render sealed if they are still to come,
blank if their date has passed.

A second year needs its own `words.js` and its own `VOLUME_YEAR` in the script.
Rather than run past week 52, the script stops with an error saying so.

## Design system

`design-system/` mirrors the Promptwrought Claude Design project. `_ds_manifest.json`
is generated remotely and gitignored. Fonts are vendored — see `design-system/FONTS.md`.
