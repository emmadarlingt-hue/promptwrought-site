# CLAUDE.md

Guidance for Claude Code and other AI assistants working in this repository.

`README.md` is the human-facing guide to adding an issue and stays the source of
truth for that workflow. This file covers what an assistant needs on top of it:
the shape of the repo, the two generated files, and the conventions that are easy
to break without noticing.

## What this is

The site behind [promptwrought.com](https://promptwrought.com) — a newsletter
that coins one word at a time for the craft of talking to machines. There is
**no framework, no bundler and no dependency manifest**. The only tooling is one
Python script, standard library only — and one GitHub Actions workflow that runs
that same script on pull requests, which is the whole of the CI.

It has two surfaces:

- **The front page**, `index.html` — the current word and the lexicon so far.
- **The Type Case**, `calendar/` — the year as fifty-two compartments, one per
  ISO week, served at `/calendar`.

The newsletter itself lives on Substack; the site links out to it and does not
host the archive.

## Layout

```
index.html              the front page — markup + inline <style>, self-contained
calendar/
  index.html            the Type Case page
  words.js              GENERATED — 52 week slots; do not hand-edit
  app.js                the tray, plain browser JS, no build step
  style.css             maps --pw-* tokens onto local names; light + dark
issues/00N-<word>.json  one issue; the only file written by hand
tools/build-lexicon.py  generates both outputs from issues/*.json (stdlib only)
design-system/          brand reference sheets + tokens.css
assets/                 logos, wordmarks, mastheads (PNG) + lockup HTML
.github/workflows/
  publish-guard.yml     runs --check and --ready on every pull request
```

That workflow is the only file under `.github/`. There is no test suite and no
package manifest.

## Deployment

**Netlify builds from the repo on push.** There is no build command to run and
no artifact to produce — the pushed files *are* the site.

Nothing about the deploy lives in this repo: there is no `netlify.toml`, no
`_redirects`, no `_headers`. Site settings, the publish directory, and the domain
are configured in the Netlify dashboard. So you cannot change deploy behaviour
from here, and adding one of those files would silently start overriding the
dashboard — don't, without asking.

The practical consequence is the next section: **a push to the deploy branch is a
publication**, live in a minute or two, with no gate in between.

## Commands

Python 3 standard library only; no install step, no virtualenv.

| Task | Command |
|---|---|
| Where things stand | `python3 tools/build-lexicon.py --status` |
| Start the next issue file | `python3 tools/build-lexicon.py --new <word>` |
| Regenerate both outputs | `python3 tools/build-lexicon.py` |
| Verify both are current | `python3 tools/build-lexicon.py --check` |
| Is it safe to push? | `python3 tools/build-lexicon.py --ready` |
| Preview locally | `python3 -m http.server` then open `/` or `/calendar/` |

`--status` is the orientation command: what has gone out, what is next, whether
the outputs are current, whether pushing is safe. Start there.

`--check` writes nothing and exits non-zero if **either** output is stale. Run it
before you commit; it is the closest thing this repo has to a test.

`--new` scaffolds `issues/00N-<word>.json` with the number and week worked out
and `issueUrl` guessed from the usual `/p/<word>` pattern — verify that against
Substack. A scaffold is deliberately unusable: generating refuses while any issue
is missing a field in `REQUIRED`, so a half-written entry cannot reach either
page with an empty definition.

## One source, two generated files

`issues/00N-<word>.json` is the only file you write by hand. `build-lexicon.py`
generates everything else a word appears in:

**1. The lexicon region of `index.html`** — everything between these markers, and
nothing else:

```html
    <!-- lexicon:start -->
    <!-- lexicon:end -->
```

The marker indentation (four spaces) is part of the contract; the script matches
the exact string. Everything outside the markers is hand-written and untouched.

**2. The whole of `calendar/words.js`** — all 52 slots, regenerated from scratch
every run. The file has a "GENERATED FILE — do not edit by hand" banner. Anything
typed into it is overwritten without warning.

**Never hand-edit either.** Edit the issue JSON and re-run the script.

How they render:

- Lexicon entries are sorted by `no`, shown **newest first**; the `Nº` counter
  takes the highest `no`; the closing line names the newest issue's `next_word`.
- Field values are **HTML fragments** — `<em>` survives as written. A bare `&` is
  escaped for you; an existing entity like `&amp;` is left alone.
- `in_use` is wrapped in `<cite>` and curly quotes by the script — write it bare.
- On the calendar, `pos` is expanded to long form (`n. & v.` → `noun & verb`).
  An abbreviation not in `POS_WORDS` passes through **with a warning** rather
  than failing — check stderr after adding an unusual part of speech.

## The week arithmetic

The tray is one calendar year and the run opens at week 31, so **issue N is week
N + 30** — issue 001 is week 031. The release date is the Tuesday of that ISO
week, computed via `date.fromisocalendar`. Weeks with no issue render sealed if
still to come, blank if their date has passed.

Two constraints worth knowing before you touch this:

- **The constants are duplicated.** `FIRST_ISSUE_WEEK` and `TOTAL_WEEKS` are
  defined in *both* `tools/build-lexicon.py` and `calendar/app.js`, and
  `VOLUME_YEAR` only in the script. Change one and you must change the other —
  nothing catches the mismatch.
- **The volume stops at week 52.** Issue 023 would be week 53; rather than run
  past the end of the tray, the script exits with an error saying a second year
  needs its own `words.js` and its own `VOLUME_YEAR`. That is deliberate. Don't
  "fix" it by widening the range.

`calendar/app.js` parses dates with `Date.UTC` by hand rather than
`new Date(string)`, because a bare date string is read as midnight UTC and lands
on the previous day for anyone west of Greenwich. This is commented in the file.
Leave it alone — `new Date(iso)` looks tidier and is wrong.

## How `design-system/` reaches each surface — they differ

This is the thing most likely to waste your time, and the two pages do **not**
behave the same way.

| Surface | Links `tokens.css`? | Names it uses |
|---|---|---|
| `index.html` (front page) | **No** — self-contained inline `<style>` | `--ink`, `--parchment`, `--hot-metal` |
| `calendar/` | **Yes** — `../design-system/tokens.css` | `--pw-*`, remapped to `--surface`, `--text`, `--accent` |

So editing `design-system/tokens.css`:

- **changes the calendar**, which consumes those tokens through `style.css`;
- **changes nothing on the front page**, which holds its own copy of the values.

A brand change intended to reach both must be made in `tokens.css` *and* in the
inline `<style>` of `index.html`. Say so in the commit — they drift apart
otherwise, and nothing catches it.

`calendar/style.css` defines a semantic layer (`--surface`, `--text`, `--accent`,
`--rule`, `--edge`) on top of the brand tokens, so **dark mode is a reassignment
of that layer** under `:root[data-theme="dark"]`, not a second set of rules. Add
a colour by adding it to the semantic layer in both blocks — never by hardcoding
a hex in a component rule. The front page has no dark theme.

`design-system/` otherwise mirrors the Promptwrought Claude Design project. Each
sheet is standalone HTML with tokens inlined so it renders with no build step.
`design-system/_ds_manifest.json` is generated remotely and gitignored — do not
create it by hand.

## House rules for anything visual

Stated in `design-system/README.md` and `FONTS.md`, and deliberate. Breaking one
is immediately visible as off-brand.

- **Nothing is bold.** Emphasis is italic throughout. The only weight change is
  between display 500 and 600. A bold run in a serif at body size reads as a
  second typeface.
- **Radius is zero, everywhere.** The system is rules and rectangles. One rounded
  corner reads as a different brand.
- **The accent has three values, not one.** `#c2451c` measures 3.9:1 on parchment
  — fine for marks and display type at 24px+, below AA at body size. Use
  `#a63914` for accent text and fills on light, `#e0703f` for accent text on ink.
  Both measure 5.1:1. `calendar/style.css` already picks the right one per theme.
- **Rules vs. control edges are different tokens.** A divider may be faint
  (`--rule`); the edge of something clickable may not (`--control-edge`, 3:1
  minimum). Never use a rule token for a control boundary.
- **Every font rule states its weight.** Cormorant Garamond's variable default
  instance is 300 (Light), so any rule omitting a weight renders noticeably
  thinner than intended.
- **Size tokens are never named after text or type.** Families are `--pw-font-*`,
  sizes are `--pw-size-*`. Design tooling classifies custom properties by name: a
  size called `--pw-text` gets mined for a font family and yields a phantom
  entry. `FONTS.md` documents the incident that set this rule.

Contrast is a standing commitment: every text node on the live site clears WCAG
AA, in both themes. If you change a pairing, measure it rather than eyeballing.

## Publishing discipline

**Commit freely; push deliberately.** From `README.md`:

> Push after the Substack issue has actually gone out — pushing early puts the
> word on the site before subscribers get the email.

Netlify makes this literal: a push to the deploy branch goes live within a minute
or two, unreviewed. There is no staging step to catch a word that has not been
emailed yet. Treat pushing to that branch as pressing publish; feature branches
are free.

This is enforced in four places, weakest to strongest. The first three are local
and none of them stops a merge on GitHub, which is the way a prepared branch
usually reaches the site; the fourth exists to cover exactly that.

The script **warns on stderr** while an issue's publication moment is still ahead.
A warning is not a failure — the build still writes, because preparing the files
early is the normal way to work. Read the output rather than trusting the exit
code.

`--ready` **exits non-zero** while any issue file describes a word that has not
gone out, and `tools/pre-push` wires that into `git push`. The hook reads the refs
git is about to send and gates **only those bound for `refs/heads/main`**, since
only main deploys — pushing a feature branch or opening a pull request is never
blocked. It has to be linked into place once per clone, because `.git/hooks/` is
not version controlled:

```bash
ln -sf ../../tools/pre-push .git/hooks/pre-push
```

`git push --no-verify` bypasses it. That is the intended escape hatch, not a
workaround — but if you reach for it, know what you are publishing.

**And a merge is not a push.** This is the gap in the guard, and it is structural
rather than a bug. `tools/pre-push` is a git hook: it runs in a clone, on `git
push`, against the refs git is about to send. Merging a pull request on GitHub
runs on their servers — no clone, no push, no hook — and Netlify builds `main`
straight afterwards. So the merge button publishes without consulting `--ready`
at all, and it is how issues actually reach the site when the work was prepared
on a branch. Nº 006 went live five days early exactly this way — which is why the
fourth enforcement point below exists.

**`.github/workflows/publish-guard.yml` runs the same checks where the merge
happens.** Two jobs on every pull request against main: *outputs current* runs
`--check`, *word has gone out* runs `--ready`. Both check out the pull request's
**merge result** rather than its head, so each answers the question that actually
matters — what would be true of main if this were merged now.

Two things about it are easy to get wrong:

- **A red job does not block a merge on its own.** Both have to be marked required
  under Settings → Branches → branch protection for `main`. Untick that and they
  are advice, not a gate. Nothing in this repo can tell you which they are; check
  the setting rather than assuming.
- **It only works because `PUBLISH_ZONE` is named.** Runners are UTC, so a naive
  13:30 would read as 13:30Z and hold the guard shut for an hour after the email.
  That is the same bug the local script had; don't reintroduce it here.

While an issue is prepared and waiting, *word has gone out* is red on **every** open
pull request against main, not just the one carrying the word — because the check
describes the state of main after a merge, and any merge deploys whatever main then
holds. That is correct, and it is also inconvenient: expect unrelated work to sit
behind a red check during a prep week.

**A feature branch is free of the deploy, not of the web.** Netlify builds a deploy
preview for every pull request, at a public though unlisted URL. Preparing an issue
early therefore puts the unsent word online, off promptwrought.com but reachable by
anyone holding the link. The exposure is small — nobody finds a preview URL without
the pull request — but "feature branches are free" is a statement about the live
site, not about secrecy.

**The comparison is a moment, not a date.** `PUBLISH_TIME` is 13:30, matching the
Substack slot, and `release_moment()` combines it with the Tuesday. This is the
whole point of the guard: on publication morning the date has already arrived and
the email has not, so a date-only check waves the entire morning through.

**And the moment carries a zone.** `PUBLISH_ZONE` is `Europe/London`, so 13:30
means 13:30 in London wherever the script runs; `current_moment()` is the other
half of every comparison and returns an aware `now` in the same zone. Both sides
have to stay aware — a naive `datetime.now()` anywhere in this file raises a
`TypeError` on comparison rather than failing quietly, which is the intended
behaviour. Don't "fix" it by dropping the zone: on a UTC machine — a CI runner,
a cloud dev container — a naive 13:30 reads as 13:30Z and holds the guard shut
for an hour *after* the email has gone. `ZoneInfo` also tracks the clock change,
which this volume crosses: weeks 031–043 release in BST, weeks 044–052 in GMT, so
a fixed offset would be wrong from late October on.

The structural guard, still the strongest, is that a word only reaches either
output once its issue JSON exists and is complete.

## Git

- Work on a feature branch; open pull requests as drafts.
- Imperative-mood commit subjects, with a body explaining *why* when the change
  is not self-evident.
- Push with `git push -u origin <branch-name>`.
- When you add an issue, commit the JSON **and both regenerated outputs**
  (`index.html`, `calendar/words.js`) together — a commit missing one leaves
  `--check` failing for whoever pulls next.

## Known wrinkles

- `assets/.DS_Store` is still tracked, though the root one has been removed and
  `.DS_Store` is in `.gitignore` — the ignore rule does not untrack files already
  committed. `git rm --cached assets/.DS_Store` finishes the job.
- `athenadarling/` is gitignored: it is a separate project with its own git repo
  that happens to sit inside this folder, and without the ignore git offers to
  swallow it as a submodule. It is not part of this site.
- The design system depends on Google Fonts at render time. The five font files
  *are* vendored under `design-system/fonts/` with their OFL licences, but nothing
  currently loads them locally — self-hosting means swapping the `@import` in
  `tokens.css` for `@font-face` rules.
- The subscribe control is a plain link to Substack, not a form. Intentional:
  Substack's API sends no `Access-Control-Allow-Origin`, so an in-page form
  cannot submit to it. There is a comment in `index.html` saying so.
- `calendar/words.js` is loaded as a plain `<script>` defining a global `WORDS`,
  read by `app.js`. No modules, no imports, load order matters.

## Maintaining this file

Keep it true. If you change a command, a marker, a directory, a constant, or one
of the house rules, update this file in the same commit. Base additions on files
you have read and commands you have run — not on what a project of this kind
usually looks like.
