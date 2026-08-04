#!/usr/bin/env python3
"""Render issues/*.json into the lexicon section of index.html.

One issue is one JSON file. This script owns everything between the
<!-- lexicon:start --> and <!-- lexicon:end --> markers in index.html and
nothing else: the Nº counter, the word entries (newest first), and the
closing "forthcoming" line.

    python3 tools/build-lexicon.py            rewrite index.html
    python3 tools/build-lexicon.py --check    exit 1 if it would change

Field values are HTML fragments — <em>, <cite> and the like are kept as
written. A bare & is escaped for you; a real entity such as &amp; is left
alone.
"""

import json
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ISSUES = ROOT / "issues"
INDEX = ROOT / "index.html"

START = "    <!-- lexicon:start -->"
END = "    <!-- lexicon:end -->"

WIDTH = 112

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
    updated = f"{before}{START}\n{render(issues)}\n{END}{after}"

    if updated == current:
        print(f"lexicon up to date — {len(issues)} issue(s), latest Nº {issues[0]['no']:03d}")
        return

    if check:
        sys.exit("index.html is out of date — run: python3 tools/build-lexicon.py")

    INDEX.write_text(updated, encoding="utf-8")
    print(f"wrote {INDEX.name} — {len(issues)} issue(s), latest Nº {issues[0]['no']:03d}")


if __name__ == "__main__":
    main()
