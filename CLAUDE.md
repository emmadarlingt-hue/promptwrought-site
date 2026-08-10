# CLAUDE.md

Guidance for Claude Code and other AI assistants working in this repository.

`README.md` is the human-facing guide to adding an issue and stays the source of
truth for that workflow. This file covers what an assistant needs on top of it:
the shape of the repo, the one generated region, and the conventions that are
easy to break without noticing.

## What this is

The site behind [promptwrought.com](https://promptwrought.com) — a newsletter
that coins one word at a time for the craft of talking to machines. It is a
**single static page**, `index.html`, with no framework, no bundler, no
dependency manifest, and no CI. The only tooling is one Python script that
regenerates part of that page from JSON.

The newsletter itself lives on Substack; the site links out to it and does not
host the archive.

## Layout

```
index.html              the whole site — markup + inline <style>, self-contained
issues/00N-<word>.json  one issue's lexicon entry; the data behind the page
tools/build-lexicon.py  renders issues/*.json into index.html (stdlib only)
design-system/          brand reference sheets — see the warning below
assets/                 logos, wordmarks, mastheads (PNG) + lockup HTML
```

There is no `.github/`, no test suite, and no package manifest. How the site is
deployed is not recorded anywhere in the repo — don't assume GitHub Pages, and
don't add deploy config without asking.

## Commands

Python 3 standard library only; no install step, no virtualenv.

| Task | Command |
|---|---|
| Regenerate the lexicon | `python3 tools/build-lexicon.py` |
| Verify the page is current | `python3 tools/build-lexicon.py --check` |
| Preview locally | `python3 -m http.server` then open `index.html` |

`--check` writes nothing and exits non-zero if `index.html` is stale. Run it
before you commit; it is the closest thing this repo has to a test.

## The one generated region

`tools/build-lexicon.py` owns everything between these two markers in
`index.html` and nothing else:

```html
    <!-- lexicon:start -->
    <!-- lexicon:end -->
```

**Never hand-edit inside them** — the next build silently overwrites it. That
region contains the `Nº` counter, the word entries, and the closing
"forthcoming" line. Everything outside the markers is hand-written and the
script will not touch it.

How it renders:

- Entries are sorted by the `no` field and shown **newest first**.
- The `Nº` counter takes the highest `no`.
- The closing line names the next word from the newest issue's `next_word`
  field, and counts the ordinal from the number of issues on file.
- Field values are **HTML fragments** — `<em>` and friends survive as written.
  A bare `&` is escaped for you; an existing entity like `&amp;` is left alone.
- `in_use` is wrapped in `<cite>` and curly quotes by the script — write it bare.
- The marker indentation (four spaces) is part of the contract; the script
  matches on the exact string.

`README.md` documents the JSON fields. Copy an existing issue rather than
writing one from scratch — `pron` in particular is backslash-delimited and needs
escaping as `\\` in JSON.

## `design-system/` does not style the site

This is the thing most likely to waste your time.

`index.html` is **self-contained**: it carries its own inline `<style>` block and
its own Google Fonts `<link>`. It does **not** link `design-system/tokens.css`.
Editing `tokens.css` changes nothing on the live site.

The two layers hold the same values under different names:

| Layer | Naming | Used by |
|---|---|---|
| `index.html` inline `<style>` | `--ink`, `--parchment`, `--hot-metal` | the live site |
| `design-system/tokens.css` | `--pw-ink`, `--pw-parchment`, `--pw-hot-metal` | reference; portable into other projects |

So a colour or type change intended to reach the site must be made in
`index.html`. If it is meant to be part of the brand, make it in **both** and say
so in the commit — they drift apart otherwise, and nothing catches it.

`design-system/` mirrors the Promptwrought Claude Design project. Each sheet is
standalone HTML with its tokens inlined so it renders with no build step.
`design-system/_ds_manifest.json` is generated remotely and gitignored — do not
create it by hand.

## House rules for anything visual

These are stated in `design-system/README.md` and `FONTS.md` and are deliberate,
not accidental. Breaking one is immediately visible as off-brand.

- **Nothing is bold.** Emphasis is italic throughout. The only weight change is
  between display 500 and 600. A bold run in a serif at body size reads as a
  second typeface.
- **Radius is zero, everywhere.** The system is rules and rectangles. One
  rounded corner reads as a different brand.
- **The accent has three values, not one.** `#c2451c` measures 3.9:1 on
  parchment — fine for marks and display type at 24px+, below AA at body size.
  Use `#a63914` for accent text and fills on light, `#e0703f` for accent text on
  ink. Both measure 5.1:1.
- **Rules vs. control edges are different tokens.** A divider may be faint
  (`--rule`); the edge of something clickable may not (`--control-edge`, 3:1
  minimum). Never use a rule token for a control boundary.
- **Every font rule states its weight.** Cormorant Garamond's variable default
  instance is 300 (Light), so any rule that omits a weight renders noticeably
  thinner than intended.
- **Size tokens are never named after text or type.** Families are
  `--pw-font-*`, sizes are `--pw-size-*`. Design tooling classifies custom
  properties by name: a size called `--pw-text` gets mined for a font family and
  yields a phantom entry. `FONTS.md` documents the incident that set this rule.

Contrast is a standing commitment: every text node on the live site clears WCAG
AA. If you change a colour pairing, check the ratio rather than eyeballing it.

## Publishing discipline

**Commit freely; push deliberately.** From `README.md`:

> Push after the Substack issue has actually gone out — pushing early puts the
> word on the site before subscribers get the email.

Treat a push to the default branch as publishing. If you have generated an entry
for an issue that has not been sent yet, say so and leave the push to a human.

## Git

- Work on a feature branch; open pull requests as drafts.
- Imperative-mood commit subjects, with a body explaining *why* when the change
  is not self-evident.
- Push with `git push -u origin <branch-name>`.
- When you add an issue, commit the JSON file and the regenerated `index.html`
  **together** — a commit that has one without the other leaves `--check` failing
  for whoever pulls next.

## Known wrinkles

- `.DS_Store` and `assets/.DS_Store` are tracked despite being listed in
  `.gitignore`; the ignore rule was added after they were committed, and
  `.gitignore` does not untrack existing files. Removing them with
  `git rm --cached` would be a tidy-up, not a fix to anything functional.
- The design system depends on Google Fonts at render time. The five font files
  *are* vendored under `design-system/fonts/` with their OFL licences, but
  nothing currently loads them locally — self-hosting means swapping the
  `@import` in `tokens.css` for `@font-face` rules.
- The subscribe control is a plain link to Substack, not a form. This is
  intentional: Substack's API sends no `Access-Control-Allow-Origin`, so an
  in-page form cannot submit to it. There is a comment in `index.html` saying so.

## Maintaining this file

Keep it true. If you change a command, a marker, a directory, or one of the
house rules, update this file in the same commit. Base additions on files you
have read and commands you have run — not on what a project of this kind usually
looks like.
