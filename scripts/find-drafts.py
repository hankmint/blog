#!/usr/bin/env python3
"""Find posts that are written and committed but not on the site.

Saving in the editor commits to main, which deploys. It does NOT publish: the
`draft` switch decides that, and it defaults to ON. So a post can be saved
perfectly, deploy perfectly, and never appear, with nothing anywhere reporting
a problem. That happened on 2026-08-02 and was not noticed for three days.

This is the scanner behind .github/workflows/draft-watch.yml. It reads content/
and prints one JSON object describing what is sitting unpublished. It makes no
network calls and changes nothing, so it is safe to run by hand:

    python3 scripts/find-drafts.py | python3 -m json.tool

Deliberately has no dependencies. PyYAML would be tidier, but this runs on
every push and an install step is a thing that can break at the moment it is
most needed. The front matter written by the editor is flat key/value, so a
real YAML parser buys nothing here.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys

CONTENT_DIR = "content"
SITE = "https://nanakofiwrites.com"
COLLECTION = "posts"  # must match the collection name in static/admin/config.yml

# The editor writes ![alt](/uploads/...) and sometimes a "caption" after it.
IMAGE_LINE = re.compile(r"^!\[[^\]]*\]\([^)]*\)\s*$")
# Strip inline markdown that reads badly when quoted back in an issue body.
INLINE_MD = re.compile(r"[*_`]")


def split_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Return (front matter as flat strings, body).

    Only top level `key: value` lines are read. Nested list values, such as
    categories, are ignored on purpose: nothing here needs them.
    """
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines()
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return {}, text

    fm: dict[str, str] = {}
    for line in lines[1:end]:
        if line.startswith((" ", "\t", "-")) or ":" not in line:
            continue  # nested value, or not a key line
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip("'\"")

    return fm, "\n".join(lines[end + 1 :])


def first_line_of(body: str) -> str:
    """A line that reminds Kay which post this is, from his own words."""
    for line in body.splitlines():
        line = line.strip()
        if not line or IMAGE_LINE.match(line):
            continue
        line = INLINE_MD.sub("", line)
        return line[:157] + "..." if len(line) > 160 else line
    return "(opens with a photograph)"


def days_since(value: str) -> int | None:
    try:
        when = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=dt.timezone.utc)
    return max(0, (dt.datetime.now(dt.timezone.utc) - when).days)


def human_date(value: str) -> str:
    try:
        return dt.datetime.fromisoformat(value).strftime("%-d %B %Y")
    except ValueError:
        return value or "no date"


def find_drafts() -> list[dict]:
    drafts = []
    for root, _dirs, files in os.walk(CONTENT_DIR):
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as handle:
                text = handle.read()

            fm, body = split_front_matter(text)
            if fm.get("draft", "").lower() != "true":
                continue

            # The editor's own deep link. subPath is the path below content/
            # with the extension removed, which is what Sveltia routes on.
            sub_path = os.path.splitext(os.path.relpath(path, CONTENT_DIR))[0]

            date = fm.get("date", "")
            drafts.append(
                {
                    "path": path,
                    "title": fm.get("title") or "(untitled)",
                    "date": date,
                    "date_human": human_date(date),
                    "days": days_since(date),
                    "first_line": first_line_of(body),
                    "edit_url": f"{SITE}/admin/#/collections/{COLLECTION}/entries/{sub_path}",
                }
            )

    drafts.sort(key=lambda d: d["date"], reverse=True)
    return drafts


def build_title(drafts: list[dict]) -> str:
    n = len(drafts)
    return f"{n} post{'' if n == 1 else 's'} written and NOT live"


def build_body(drafts: list[dict]) -> str:
    n = len(drafts)
    is_are = "is" if n == 1 else "are"
    lines = [
        f"**{n} post{'' if n == 1 else 's'} {is_are} saved in the repository but not on the site.**",
        "",
        "Save in the editor commits and deploys. It does not publish. The switch at the",
        "top of the post, **NOT LIVE**, is what publishes. Turn it off, Save, and this",
        "issue closes itself.",
        "",
    ]

    for draft in drafts:
        lines.append("---")
        lines.append("")
        lines.append(f"### {draft['title']} · {draft['date_human']}")
        lines.append("")
        lines.append(f"> {draft['first_line']}")
        lines.append("")
        lines.append(f"**[Open it in the editor]({draft['edit_url']})**")
        lines.append("")
        lines.append(f"`{draft['path']}`")
        if draft["days"] is not None:
            if draft["days"] == 0:
                lines.append("")
                lines.append("Written today.")
            else:
                day_word = "day" if draft["days"] == 1 else "days"
                lines.append("")
                lines.append(f"Sitting unpublished for **{draft['days']} {day_word}**.")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "_Opened and closed automatically by `.github/workflows/draft-watch.yml`. "
        "Do not close this by hand: publishing is what closes it, and closing it "
        "yourself only means it reopens on the next push._"
    )
    return "\n".join(lines)


def main() -> int:
    if not os.path.isdir(CONTENT_DIR):
        print(f"no {CONTENT_DIR}/ directory here; run from the repository root", file=sys.stderr)
        return 2

    drafts = find_drafts()
    json.dump(
        {
            "count": len(drafts),
            "title": build_title(drafts) if drafts else "",
            "body": build_body(drafts) if drafts else "",
            "drafts": drafts,
        },
        sys.stdout,
        indent=2,
        ensure_ascii=False,
    )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
