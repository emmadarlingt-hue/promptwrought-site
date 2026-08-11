#!/usr/bin/env python3
"""Render issues/*.json into the two places a published word appears.

One issue is one JSON file, and it is the only file you write by hand.
From it this script generates:

  index.html        everything between the <!-- lexicon:start --> and
                    <!-- lexicon:end --> markers, and nothing else: the
                    Nº counter, the word entries (newest first), and the
                    closing "forthcoming" line.

  calendar/words.js the whole file — fifty-two week slots, filled in
                    where an issue exists and left empty where it does
                    not. Don't hand-edit it; your edit will be lost.

    python3 tools/build-lexicon.py            rewrite both
    python3 tools/build-lexicon.py --check    exit 1 if either would change

Field values are HTML fragments — <em>, <cite> and the like are kept as
written. A bare & is escaped for you; a real entity such as &amp; is left
alone.

Because a word only reaches either file once you have written its issue
JSON, and you only write that once the issue has gone out, neither file
can leak a word early. The script warns if it notices otherwise.
"""

import json
import re
import sys
import textwrap
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ISSUES = ROOT / "issues"
INDEX = ROOT / "index.html"
WORDS_JS = ROOT / "calendar" / "words.js"

START = "    <!-- lexicon:start -->"
END = "    <!-- lexicon:end -->"

WIDTH = 112

# ── the calendar ──────────────────────────────────────────────────────────
# The tray is one calendar year, and the run opens at week 31, so issue
# number and ISO week differ by a constant: issue 1 is week 31. Release
# day is the Tuesday of that week, matching the publication slot.
VOLUME_YEAR = 2026
FIRST_ISSUE_WEEK = 31
TOTAL_WEEKS = 52
TUESDAY = 2  # in ISO numbering Monday is 1

# The homepage sets part of speech in dictionary abbreviations; the
# calendar writes them out. Anything not listed here is passed through
# untouched, with a warning, so a new abbreviation fails loudly.
POS_WORDS = {
    "n.": "noun",
    "v.": "verb",
    "adj.": "adjective",
    "adv.": "adverb",
    "prep.": "preposition",
    "int.": "interjection",
}

ORDINALS = [
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
    "eighth", "ninth", "tenth", "eleventh", "twelfth", "thirteenth",
    "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth",
    "nineteenth", "twentieth",
]


def esc(text):
    """Escape bare ampersands, leaving existing entities intact."""
    return re.sub(r"&(?!#?\w+;)", "&amp;", text)


def para(indent, open_tag, text, close_tag):
    """One paragraph, wrapped the way the hand-written markup was."""
    return textwrap.fill(
        open_tag + esc(text) + close_tag,
        width=WIDTH,
        initial_indent=indent,
        subsequent_indent=indent + "  ",
        break_long_words=False,
        break_on_hyphens=False,
    )


def field(key, open_tag, text, close_tag):
    return "\n".join([
        '      <div class="field">',
        f'        <div class="field__k">{key}</div>',
        para("        ", open_tag, text, close_tag),
        "      </div>",
    ])


def article(issue):
    head = "\n".join([
        '    <article class="word-entry">',
        '      <div class="word-entry__head">',
        f'        <span class="word-entry__word">{esc(issue["word"])}</span>',
        f'        <span class="word-entry__pos">{esc(issue["pos"])}</span>',
        f'        <span class="word-entry__pron">{esc(issue["pron"])}</span>',
        f'        <span class="word-entry__meta"><span class="tag">{esc(issue["tag"])}</span></span>',
        "      </div>",
    ])
    return "\n\n".join([
        head,
        para("      ", '<p class="word-entry__def">', issue["definition"], "</p>"),
        "\n".join([
            field("Etymology", '<p class="field__v">', issue["etymology"], "</p>"),
            field("In use", '<p class="field__v"><cite>“', issue["in_use"], "”</cite></p>"),
            field("The case", '<p class="field__v">', issue["the_case"], "</p>"),
        ]),
    ]) + "\n    </article>"


def forthcoming(issues):
    nth = len(issues) + 1
    ordinal = ORDINALS[nth - 1] if nth <= len(ORDINALS) else "next"
    word = issues[0].get("next_word") if issues else None
    subject = f"The {ordinal} entry"
    if word:
        subject += f" — <em>{esc(word)}</em> —"
    return para(
        "    ",
        '<p class="forthcoming">',
        f"{subject} is being set. Subscribe below and it will arrive when it is ready, "
        "and not before.",
        "</p>",
    )


def render(issues):
    """issues arrive newest first."""
    head = "\n".join([
        '    <div class="lexicon__head">',
        '      <h2 id="lexicon">The lexicon so far</h2>',
        f'      <p class="label">Nº {issues[0]["no"]:03d}</p>',
        "    </div>",
    ])
    blocks = [head] + [article(i) for i in issues] + [forthcoming(issues)]
    return "\n\n".join(blocks)


# ══════════════════════════════════════════════════════════════════════════
#  calendar/words.js — the same issues, in the shape the tray reads
# ══════════════════════════════════════════════════════════════════════════

WORDS_HEADER = '''/* ══════════════════════════════════════════════════════════════════════════
   Promptwrought — the year in 52 words

   GENERATED FILE — do not edit by hand. tools/build-lexicon.py writes it
   from issues/*.json. Edit the issue file and run the script; anything
   typed straight in here is overwritten without warning.

   One object per week of {year}. `week` is the ISO week number and
   `releaseDate` its Tuesday. Neither ever changes, so the tray is built
   from them whether or not a word has been struck yet.

   A slot with an empty `word` renders as blank — a week before the run
   began, or one that was skipped — or as sealed, a week still to come.
   app.js decides by comparing `releaseDate` with today.

   Issue number and week differ by {offset}: issue 001 is week {first:03d}.

       week         ISO week of {year}, 1–{total}
       releaseDate  the Tuesday of that week, YYYY-MM-DD
       word         the headword; empty until the issue ships
       pos          part of speech, written out — "noun", "noun & verb"
       definition   the sense line, as it reads on the site
       tag          the category chip, e.g. "Asking", "Keeping"
       note         optional editor's aside, shown under the definition
       issueUrl     link to the Substack issue; omitted if empty

   `definition` and `note` are HTML fragments, as in issues/*.json — <em>
   works. The rest are plain text.
   ══════════════════════════════════════════════════════════════════════════ */

const WORDS = [
'''


def warn(message):
    print(f"  warning: {message}", file=sys.stderr)


def expand_pos(pos, word):
    """"n. & v." becomes "noun & verb" — the calendar writes them out."""
    parts = []
    for token in pos.split("&"):
        token = token.strip()
        if not token:
            continue
        if token not in POS_WORDS:
            warn(f'{word}: no long form known for "{token}", used as written')
        parts.append(POS_WORDS.get(token, token))
    return " & ".join(parts)


def week_for(issue):
    """Issue 1 is week 31, issue 2 is week 32, and so on up the year."""
    week = issue["no"] + FIRST_ISSUE_WEEK - 1
    if not 1 <= week <= TOTAL_WEEKS:
        sys.exit(
            f'issue {issue["no"]} ({issue["word"]}) lands on week {week}, past '
            f"the end of the {VOLUME_YEAR} tray. A second year needs its own "
            f"words.js and its own VOLUME_YEAR."
        )
    return week


def js_string(value):
    """A double-quoted JavaScript string literal."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def slot(week, issue):
    """One of the fifty-two objects. `issue` is None for a week with no word."""
    released = date.fromisocalendar(VOLUME_YEAR, week, TUESDAY)

    fields = {"word": "", "pos": "", "definition": "",
              "tag": "", "note": "", "issueUrl": ""}

    if issue:
        fields["word"] = issue["word"]
        fields["pos"] = expand_pos(issue.get("pos", ""), issue["word"])
        fields["definition"] = issue["definition"]
        fields["tag"] = issue.get("tag", "")
        fields["note"] = issue.get("note", "")
        fields["issueUrl"] = issue.get("issueUrl", "")

        # The issue file is meant to be written on publication day. If it
        # exists before its date, say so — pushing would beat the email.
        if released > date.today():
            warn(
                f'{issue["word"]} is dated {released}, which has not arrived '
                f"yet. Pushing now puts it on the site before subscribers "
                f"get the issue."
            )

    lines = ["  {", f"    week: {week},",
             f"    releaseDate: {js_string(released.isoformat())},"]
    lines += [f"    {name}: {js_string(value)}," for name, value in fields.items()]
    lines.append("  },")
    return "\n".join(lines)


def render_words(issues):
    """The whole of calendar/words.js — all fifty-two weeks, in week order."""
    by_week = {}
    for issue in issues:
        week = week_for(issue)
        if week in by_week:
            sys.exit(
                f'two issue files both claim Nº {issue["no"]}: '
                f'{by_week[week]["word"]} and {issue["word"]}'
            )
        by_week[week] = issue

    header = WORDS_HEADER.format(
        year=VOLUME_YEAR,
        offset=FIRST_ISSUE_WEEK - 1,
        first=FIRST_ISSUE_WEEK,
        total=TOTAL_WEEKS,
    )
    body = "\n".join(slot(w, by_week.get(w)) for w in range(1, TOTAL_WEEKS + 1))
    return f"{header}{body}\n];\n"


def load_issues():
    issues = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(ISSUES.glob("*.json"))]
    if not issues:
        sys.exit(f"no issue files found in {ISSUES}")
    return sorted(issues, key=lambda i: i["no"], reverse=True)


def main():
    check = "--check" in sys.argv[1:]

    issues = load_issues()

    current = INDEX.read_text(encoding="utf-8")
    if START not in current or END not in current:
        sys.exit(f"markers {START.strip()} / {END.strip()} not found in {INDEX}")
    before, rest = current.split(START, 1)
    _, after = rest.split(END, 1)

    # (file, what it says now, what it should say)
    targets = [
        (INDEX, current, f"{before}{START}\n{render(issues)}\n{END}{after}"),
        (WORDS_JS,
         WORDS_JS.read_text(encoding="utf-8") if WORDS_JS.exists() else "",
         render_words(issues)),
    ]

    stale = [(path, wanted) for path, now, wanted in targets if now != wanted]
    summary = f"{len(issues)} issue(s), latest Nº {issues[0]['no']:03d}"

    if not stale:
        print(f"up to date — {summary}")
        return

    names = ", ".join(path.relative_to(ROOT).as_posix() for path, _ in stale)

    if check:
        sys.exit(f"out of date: {names} — run: python3 tools/build-lexicon.py")

    for path, wanted in stale:
        path.write_text(wanted, encoding="utf-8")
    print(f"wrote {names} — {summary}")


if __name__ == "__main__":
    main()
