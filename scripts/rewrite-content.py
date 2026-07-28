#!/usr/bin/env python3
"""Rewrite Micro.blog URLs in imported content to local paths.

Three jobs:

  1. Body `<img src="uploads/...">` becomes site-absolute `/uploads/...`.
     Micro.blog stored a RELATIVE path and rewrote it to an absolute CDN URL at
     render time. Hugo does not, so left alone every image 404s.

  2. Front matter CDN URLs become local `/uploads/...` paths. This matters
     because layouts/gallery/single.html reads .Params.images BEFORE it scans
     the body, so rewriting only the body would leave the gallery pulling every
     photograph from Micro.blog's CDN.

  3. Micro.blog-generated front matter keys that point at their infrastructure
     and that the MINT theme never reads are dropped entirely.

Front matter and body are handled separately so that a dropped key can never
swallow the closing `---` or a markdown list in the body.

Idempotent: safe to run more than once.
"""
import pathlib
import re
import sys

# Every host Micro.blog has served this blog's uploads from. All three appear in
# the export. The themint.micro.blog form is the pre-custom-domain one and shows
# up in a single early post, which is exactly the kind of straggler that a
# CDN-only rewrite would leave pointing at a server we no longer control.
UPLOAD_HOSTS = (
    "https://cdn.uploads.micro.blog/217795/",
    "https://nanakofiwrites.com/uploads/",
    "https://themint.micro.blog/uploads/",
    "http://themint.micro.blog/uploads/",
)

# Keys Micro.blog generated that point at their servers. The MINT theme reads
# .Params.images and .Params.image only. photos_with_metadata additionally
# carries `sizes` pointing at -m and -s resized variants that Micro.blog made
# and that we do not have, so it cannot be rewritten, only dropped.
DROP_KEYS = ("thumbnail:", "opengraph:", "photos_with_metadata:")


def strip_keys(front: str) -> str:
    """Drop DROP_KEYS and their indented continuation lines from front matter."""
    out, skipping = [], False
    for line in front.split("\n"):
        if skipping:
            # Still inside the dropped block while lines are indented or are
            # list items belonging to it.
            if line[:1] in (" ", "\t", "-") and line.strip():
                continue
            skipping = False
        if line.startswith(DROP_KEYS):
            skipping = True
            continue
        out.append(line)
    return "\n".join(out)


def main() -> int:
    root = pathlib.Path("content")
    if not root.is_dir():
        sys.exit("FAIL: content/ not found. Import the export first.")

    changed = 0
    for path in sorted(root.rglob("*.md")):
        original = path.read_text(encoding="utf-8")

        # Split front matter from body. Anything without front matter is left
        # entirely alone apart from the body rewrite.
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", original, re.DOTALL)
        if m:
            front, body = m.group(1), m.group(2)
            front = strip_keys(front)
            for host in UPLOAD_HOSTS:
                front = front.replace(host, "/uploads/")
            text = f"---\n{front}\n---\n{body}"
        else:
            text = original

        # Body images. Applied to the whole document, which is safe because the
        # front matter no longer contains any src="uploads/ pattern.
        text = re.sub(r'src="uploads/', 'src="/uploads/', text)
        for host in UPLOAD_HOSTS:
            text = text.replace(host, "/uploads/")

        if text != original:
            path.write_text(text, encoding="utf-8")
            changed += 1

    print(f"rewrote {changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
