# promptwrought-site

The site behind [promptwrought.com](https://promptwrought.com). One static page,
`index.html`, plus the brand `design-system/` and `assets/`.

## Adding an issue

The "lexicon so far" section is generated. Don't hand-edit it — everything between
`<!-- lexicon:start -->` and `<!-- lexicon:end -->` in `index.html` gets overwritten.

1. Write `issues/00N-<word>.json`, copying the shape of an existing one:

   | field        | notes                                                        |
   | ------------ | ------------------------------------------------------------ |
   | `no`         | issue number; drives the `Nº` counter and the ordering        |
   | `word`       | the headword                                                  |
   | `pos`        | part of speech, e.g. `n.` or `n. & v.`                        |
   | `pron`       | pronunciation, backslash-delimited — escape as `\\` in JSON   |
   | `tag`        | the one-word category pill, e.g. `Asking`, `Keeping`          |
   | `definition` | the sense line under the headword                             |
   | `etymology`, `in_use`, `the_case` | the three fields below it                |
   | `next_word`  | optional; names next issue's word in the closing line         |

   Values are HTML fragments, so `<em>` works. A bare `&` is escaped for you.
   `in_use` is wrapped in `<cite>` and curly quotes — write it bare.

2. Regenerate and check the diff:

   ```bash
   python3 tools/build-lexicon.py && git diff index.html
   ```

   Entries render newest first. `--check` exits non-zero if the page is out of date,
   and writes nothing.

3. Commit. **Push after the Substack issue has actually gone out** — pushing early
   puts the word on the site before subscribers get the email.

## Design system

`design-system/` mirrors the Promptwrought Claude Design project. `_ds_manifest.json`
is generated remotely and gitignored. Fonts are vendored — see `design-system/FONTS.md`.
