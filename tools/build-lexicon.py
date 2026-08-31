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

    python3 tools/build-lexicon.py                 rewrite both
    python3 tools/build-lexicon.py --status        where things stand
    python3 tools/build-lexicon.py --new <word>    start the next issue file
    python3 tools/build-lexicon.py --check         exit 1 if either is stale
    python3 tools/build-lexicon.py --ready         exit 1 if a word is unpublished

If you only remember one, remember --status. It says what has gone out,
what is next, whether the generated files are current, and whether it is
safe to push yet.

Field values are HTML fragments — <em>, <cite> and the like are kept as
written. A bare & is escaped for you; a real entity such as &amp; is left
alone.

Nothing here talks to Substack. Sending the issue and pushing the site are
two separate acts, and the site changes only when you push. --ready is the
backstop: it fails while any issue file describes a word whose publication
moment has not arrived, and tools/pre-push wires it into `git push`.
"""

import html
import json
import re
import sys
import textwrap
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
ISSUES = ROOT / "issues"
INDEX = ROOT / "index.html"
WORDS_JS = ROOT / "calendar" / "words.js"

SITE = "https://promptwrought.com"

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

# The Substack slot. This is the whole reason the guard is worth having:
# on publication day the date has already arrived hours before the email
# does, so anything comparing dates alone reads as safe all morning.
#
# The zone is named rather than assumed. 13:30 means 13:30 in London, and
# a naive datetime would instead mean 13:30 wherever the script happens to
# run — an hour out on a UTC machine such as a CI runner or a cloud dev
# container, which holds the guard shut for an hour after the email has
# gone. ZoneInfo also handles the clock change: this volume opens in BST
# and ends in GMT, so a fixed offset would be wrong from week 44 on.
PUBLISH_ZONE = ZoneInfo("Europe/London")
PUBLISH_TIME = time(13, 30)

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


def plain(text):
    """A field value as prose: no tags, no entities.

    Field values are HTML fragments — <em> and &amp; are written to survive
    into the markup. Structured data wants the sentence a person would read,
    so both come back out here.
    """
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def anchor(word):
    """The id an entry is deep-linked by: promptwrought.com/#misask."""
    return re.sub(r"[^a-z0-9]+", "-", word.lower()).strip("-")


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
        f'    <article class="word-entry" id="{anchor(issue["word"])}">',
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


SET_ID = f"{SITE}/#lexicon"

SET_DESCRIPTION = ("Coined words for the craft of talking to machines — one a week, "
                   "with its definition, its roots, and the case for keeping it.")


def structured_data(issues):
    """schema.org DefinedTermSet — the lexicon, said again for machines.

    A coinage has no search volume on the day it is coined: nobody types a
    word they have not met. What a search engine can be told is that this
    page is a glossary and these are its entries, which is the question
    "what does <word> mean" answered before it is asked. Regenerated with
    the markup so the two cannot drift.
    """
    terms = []
    for issue in issues:
        term = {
            "@type": "DefinedTerm",
            "@id": f"{SITE}/#{anchor(issue['word'])}",
            "name": plain(issue["word"]),
            "description": plain(issue["definition"]),
            "inDefinedTermSet": SET_ID,
        }
        if issue.get("issueUrl"):
            term["sameAs"] = issue["issueUrl"]
        terms.append(term)

    payload = {
        "@context": "https://schema.org",
        "@type": "DefinedTermSet",
        "@id": SET_ID,
        "name": "The Promptwrought Lexicon",
        "description": SET_DESCRIPTION,
        "url": SET_ID,
        "inLanguage": "en",
        "hasDefinedTerm": terms,
    }

    body = json.dumps(payload, ensure_ascii=False, indent=2)
    # A literal </script> inside the JSON would close the tag early. No field
    # holds one today; escaping the sequence means none ever can.
    body = body.replace("</", "<\\/")
    body = textwrap.indent(body, "      ")
    return "\n".join([
        '    <script type="application/ld+json">',
        body,
        "    </script>",
    ])


def render(issues):
    """issues arrive newest first."""
    head = "\n".join([
        '    <div class="lexicon__head">',
        '      <h2 id="lexicon">The lexicon so far</h2>',
        f'      <p class="label">Nº {issues[0]["no"]:03d}</p>',
        "    </div>",
    ])
    blocks = ([head] + [article(i) for i in issues]
              + [forthcoming(issues), structured_data(issues)])
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


QUIET = False  # --status reports the same facts in a tidier form


def warn(message):
    if not QUIET:
        print(f"  warning: {message}", file=sys.stderr)


def release_date(week):
    """The Tuesday of that ISO week."""
    return date.fromisocalendar(VOLUME_YEAR, week, TUESDAY)


def release_moment(week):
    """The moment the issue actually reaches subscribers — date *and* time."""
    return datetime.combine(release_date(week), PUBLISH_TIME, tzinfo=PUBLISH_ZONE)


def current_moment():
    """Now, in the publication zone — the other half of every comparison.

    Both sides have to be aware, or Python refuses to compare them at all.
    """
    return datetime.now(PUBLISH_ZONE)


def human_gap(delta):
    """A timedelta as "11h 26m", for saying how long until something."""
    minutes = int(delta.total_seconds() // 60)
    days, minutes = divmod(minutes, 60 * 24)
    hours, minutes = divmod(minutes, 60)
    if days:
        return f"{days}d {hours}h"
    return f"{hours}h {minutes:02d}m"


def unpublished(issues):
    """Issues whose publication moment is still in the future, soonest first."""
    now = current_moment()
    pending = [i for i in issues if release_moment(week_for(i)) > now]
    return sorted(pending, key=lambda i: i["no"])


# Everything an entry needs before it can render. issueUrl, note and
# next_word are left off deliberately — each is legitimately empty.
REQUIRED = ["word", "pos", "pron", "tag", "definition",
            "etymology", "in_use", "the_case"]

# seo_title and seo_description are deliberately not in REQUIRED. They are
# copy for Substack's own fields and reach neither generated output, so a
# missing one is a chore outstanding, never a reason to refuse to build.
# The limits are where Google truncates, not where it penalises.
SEO_TITLE_MAX = 60
SEO_DESC_MAX = 160


def incomplete(issues):
    """(issue, missing fields) for any issue still part-written."""
    found = []
    for issue in sorted(issues, key=lambda i: i["no"]):
        missing = [f for f in REQUIRED if not str(issue.get(f, "")).strip()]
        if missing:
            found.append((issue, missing))
    return found


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
    released = release_date(week)

    fields = {"word": "", "pos": "", "definition": "",
              "tag": "", "note": "", "issueUrl": ""}

    if issue:
        fields["word"] = issue["word"]
        fields["pos"] = expand_pos(issue.get("pos", ""), issue["word"])
        fields["definition"] = issue["definition"]
        fields["tag"] = issue.get("tag", "")
        fields["note"] = issue.get("note", "")
        fields["issueUrl"] = issue.get("issueUrl", "")

        # Compared against the moment, not the day. On publication morning
        # the date has arrived and the email has not, which is exactly the
        # window a date-only check waves through.
        moment = release_moment(week)
        if moment > current_moment():
            warn(
                f'{issue["word"]} is not out until {moment:%a %d %b, %H:%M} — '
                f"{human_gap(moment - current_moment())} away. Writing the file "
                f"now is fine; pushing would beat the email."
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


def build_targets(issues):
    """(file, what it says now, what it should say) for each generated file."""
    current = INDEX.read_text(encoding="utf-8")
    if START not in current or END not in current:
        sys.exit(f"markers {START.strip()} / {END.strip()} not found in {INDEX}")
    before, rest = current.split(START, 1)
    _, after = rest.split(END, 1)
    return [
        (INDEX, current, f"{before}{START}\n{render(issues)}\n{END}{after}"),
        (WORDS_JS,
         WORDS_JS.read_text(encoding="utf-8") if WORDS_JS.exists() else "",
         render_words(issues)),
    ]


# ══════════════════════════════════════════════════════════════════════════
#  --new : start the next issue file, so the numbering is never guessed at
# ══════════════════════════════════════════════════════════════════════════

def do_new(word, issues):
    slug = re.sub(r"[^a-z0-9-]", "", word.strip().lower())
    if not slug:
        sys.exit("name the word: python3 tools/build-lexicon.py --new grainsense")

    number = max(i["no"] for i in issues) + 1
    week = number + FIRST_ISSUE_WEEK - 1
    if week > TOTAL_WEEKS:
        sys.exit(
            f"issue {number} would be week {week}, past the end of the "
            f"{VOLUME_YEAR} tray. A second year needs its own words.js."
        )

    path = ISSUES / f"{number:03d}-{slug}.json"
    if path.exists():
        sys.exit(f"{path.relative_to(ROOT).as_posix()} already exists — edit that.")

    skeleton = {
        "no": number,
        "word": slug,
        "pos": "",
        "pron": "\\  \\",
        "tag": "",
        "definition": "",
        "etymology": "",
        "in_use": "",
        "the_case": "",
        "issueUrl": f"https://promptwrought.substack.com/p/{slug}",
        "seo_title": "",
        "seo_description": "",
        "next_word": "",
    }
    path.write_text(json.dumps(skeleton, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")

    moment = release_moment(week)
    print(f"wrote {path.relative_to(ROOT).as_posix()}")
    print(f"  Nº {number:03d} · week {week:03d} · out {moment:%a %d %b %Y, %H:%M}")
    print()
    print("  Fill it in from Verbarium, then run the script with no arguments.")
    print("  The issueUrl is a guess from the pattern — check it against Substack.")
    print("  seo_title and seo_description are for Substack's own SEO fields;")
    print("  --seo prints them to paste, with their lengths.")


# ══════════════════════════════════════════════════════════════════════════
#  --status : the one command worth remembering
# ══════════════════════════════════════════════════════════════════════════

def do_status(issues):
    global QUIET
    QUIET = True  # the same facts appear below, more tidily

    now = current_moment()
    pending = unpublished(issues)
    pending_numbers = {i["no"] for i in pending}
    struck = [i for i in issues if i["no"] not in pending_numbers]
    stale = [p for p, was, wants in build_targets(issues) if was != wants]
    newest = max(issues, key=lambda i: i["no"])

    print()
    print(f"  Promptwrought — {VOLUME_YEAR}")
    print()
    print(f"  struck         {len(struck)} of {TOTAL_WEEKS}")

    if struck:
        last = max(struck, key=lambda i: i["no"])
        week = week_for(last)
        print(f"  latest         Nº {last['no']:03d}  {last['word']:<15}"
              f"week {week:03d}   {release_date(week):%a %d %b}")

    if pending:
        for issue in pending:
            week = week_for(issue)
            moment = release_moment(week)
            print(f"  in flight      Nº {issue['no']:03d}  {issue['word']:<15}"
                  f"week {week:03d}   out {moment:%a %d %b, %H:%M}")
    else:
        number = newest["no"] + 1
        week = number + FIRST_ISSUE_WEEK - 1
        if week <= TOTAL_WEEKS:
            name = newest.get("next_word") or "not yet named"
            print(f"  next up        Nº {number:03d}  {name:<15}"
                  f"week {week:03d}   {release_moment(week):%a %d %b, %H:%M}")
            print(f"                 no file yet — --new {name}"
                  if newest.get("next_word") else
                  "                 no file yet — --new <word>")

    print()
    for issue, missing in incomplete(issues):
        print(f"  unfinished     Nº {issue['no']:03d} {issue['word']} — "
              f"{', '.join(missing)}")
    print(f"  generated      {'up to date' if not stale else 'STALE — run the script'}")

    if pending:
        moment = release_moment(week_for(pending[0]))
        print(f"  safe to push   NO — {pending[0]['word']} is out in "
              f"{human_gap(moment - now)}")
    else:
        print("  safe to push   yes")
    print()


# ══════════════════════════════════════════════════════════════════════════
#  --ready : the backstop git push runs
# ══════════════════════════════════════════════════════════════════════════

def do_ready(issues):
    pending = unpublished(issues)
    if not pending:
        return

    now = current_moment()
    say = lambda line: print(line, file=sys.stderr)
    say("")
    say("  Push blocked — a word in this repo has not gone out yet:")
    say("")
    for issue in pending:
        moment = release_moment(week_for(issue))
        say(f"    Nº {issue['no']:03d}  {issue['word']} — out "
            f"{moment:%a %d %b, %H:%M}, {human_gap(moment - now)} away")
    say("")
    say("  Pushing now puts it on promptwrought.com before subscribers get")
    say("  the email. Wait for the send, or override with:")
    say("")
    say("    git push --no-verify")
    say("")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════
#  --seo : the Substack fields, ready to paste
# ══════════════════════════════════════════════════════════════════════════

def do_seo(issues, want=None):
    """Print the SEO copy for one issue or all of them.

    Substack keeps its SEO title and description in its own editor, where
    nothing is versioned and nothing counts the characters. Holding the copy
    beside the word means it can be reviewed with the rest of the entry;
    printing it unwrapped means it can be selected and pasted in one go.
    """
    chosen = [i for i in reversed(issues)
              if want is None or i["word"] == want]
    if not chosen:
        sys.exit(f"no issue for {want!r} — try --status to see what there is.")

    for issue in chosen:
        print()
        print(f'  Nº {issue["no"]:03d}  {issue["word"]}')
        for label, key, limit in (("title", "seo_title", SEO_TITLE_MAX),
                                  ("description", "seo_description", SEO_DESC_MAX)):
            text = issue.get(key, "").strip()
            print()
            if not text:
                print(f"  SEO {label} — not written yet")
                continue
            over = " — over, Google will cut it" if len(text) > limit else ""
            print(f"  SEO {label}  {len(text)}/{limit}{over}")
            print(f"  {text}")
    print()


def main():
    args = sys.argv[1:]
    issues = load_issues()

    if "--new" in args:
        position = args.index("--new")
        do_new(args[position + 1] if len(args) > position + 1 else "", issues)
        return

    if "--status" in args:
        do_status(issues)
        return

    if "--ready" in args:
        do_ready(issues)
        return

    if "--seo" in args:
        position = args.index("--seo")
        word = args[position + 1] if len(args) > position + 1 else None
        do_seo(issues, word)
        return

    # A scaffolded file has the headword in it but nothing else. Generating
    # from it would put the word on both pages with an empty definition.
    part_written = incomplete(issues)
    if part_written:
        lines = ["nothing written — these issue files are not filled in yet:", ""]
        for issue, missing in part_written:
            lines.append(f"  Nº {issue['no']:03d} {issue['word']}: "
                         f"{', '.join(missing)}")
        lines += ["", "Fill them in from Verbarium and run this again."]
        sys.exit("\n".join(lines))

    stale = [(path, wanted) for path, now, wanted in build_targets(issues)
             if now != wanted]
    summary = f"{len(issues)} issue(s), latest Nº {issues[0]['no']:03d}"

    if not stale:
        print(f"up to date — {summary}")
        return

    names = ", ".join(path.relative_to(ROOT).as_posix() for path, _ in stale)

    if "--check" in args:
        sys.exit(f"out of date: {names} — run: python3 tools/build-lexicon.py")

    for path, wanted in stale:
        path.write_text(wanted, encoding="utf-8")
    print(f"wrote {names} — {summary}")


if __name__ == "__main__":
    main()
