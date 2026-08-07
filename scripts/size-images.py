#!/usr/bin/env python3
"""Give every raw <img> in content/ the width and height of the real file.

An <img> that is lazy-loaded and declares no width or height has NO intrinsic
size until it decodes, so it occupies zero height and the page shows whatever
is behind it. In the gallery that is the tile's paper background, which is what
Kay saw as tiles "always flashing white". In a post it is the same collapse,
once per photograph, and the text under it jumps every time one lands.

Markdown images are handled at build time by layouts/_default/_markup/
render-image.html, which asks layouts/partials/img-dims.html. Render hooks
never see RAW HTML, though, and the Micro.blog importer wrote raw <img> tags.
It was not even consistent about it: content/2025/12/18/chitarctica/index.md
already carries width="450" height="600", while the post one folder over
carries none at all. This fills in the ones it missed, in the same shape.

Idempotent. An <img> that already declares either dimension is left exactly as
it is, so this can be run any time and re-run safely.

    python3 scripts/size-images.py            # write the attributes
    python3 scripts/size-images.py --check    # report only, change nothing

--check exits 1 if anything is missing, so CI can use it.
"""

from __future__ import annotations

import os
import re
import sys

from PIL import Image

CONTENT_DIR = "content"
STATIC_DIR = "static"

IMG_TAG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
SRC_ATTR = re.compile(r"""\bsrc\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
HAS_DIM = re.compile(r"""\b(width|height)\s*=""", re.IGNORECASE)


def dimensions(src: str) -> tuple[int, int] | None:
    """The real pixel size of the file this src points at, or None."""
    if not src.startswith("/"):
        return None  # a remote or relative image; nothing local to measure
    path = os.path.join(STATIC_DIR, src.lstrip("/"))
    if not os.path.isfile(path):
        return None
    try:
        with Image.open(path) as im:
            return im.size
    except Exception:
        # Not decodable as an image. Leave the tag alone rather than guess.
        return None


def fix_tag(tag: str) -> tuple[str, str | None]:
    """Return (tag, reason-it-was-skipped). Reason is None when it was sized."""
    if HAS_DIM.search(tag):
        return tag, "already sized"

    match = SRC_ATTR.search(tag)
    if not match:
        return tag, "no src"

    src = match.group(1)
    size = dimensions(src)
    if size is None:
        return tag, f"cannot measure {src}"

    width, height = size
    # Insert straight after <img so the attributes read in a sensible order,
    # matching what the importer produced where it did produce them.
    return tag[:4] + f' width="{width}" height="{height}"' + tag[4:], None


def main() -> int:
    check_only = "--check" in sys.argv

    if not os.path.isdir(CONTENT_DIR):
        print(f"no {CONTENT_DIR}/ here; run from the repository root", file=sys.stderr)
        return 2

    changed_files = 0
    sized = 0
    unmeasurable: list[str] = []

    for root, _dirs, files in os.walk(CONTENT_DIR):
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as handle:
                text = handle.read()

            out = []
            last = 0
            file_sized = 0
            for m in IMG_TAG.finditer(text):
                new_tag, reason = fix_tag(m.group(0))
                if reason and reason.startswith("cannot measure"):
                    unmeasurable.append(f"{path}: {reason}")
                if new_tag != m.group(0):
                    out.append(text[last : m.start()])
                    out.append(new_tag)
                    last = m.end()
                    file_sized += 1
            if not file_sized:
                continue

            out.append(text[last:])
            sized += file_sized
            changed_files += 1
            print(f"{'would size' if check_only else 'sized'} {file_sized} in {path}")
            if not check_only:
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write("".join(out))

    for line in unmeasurable:
        print(f"  cannot measure: {line}", file=sys.stderr)

    if sized == 0:
        print("every raw <img> in content/ already declares its size")
        return 0

    print(f"\n{sized} image tag(s) in {changed_files} file(s)")
    return 1 if check_only else 0


if __name__ == "__main__":
    raise SystemExit(main())
