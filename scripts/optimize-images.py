#!/usr/bin/env python3
"""Make the photographs web-weight, and build thumbnails for the gallery grid.

The images imported from Micro.blog are untouched phone originals: 1800x2400 at
up to 5 MB each, which is near-lossless and absurd for a web page. The gallery
loaded all 31 of them at full size into tiles a few hundred pixels wide, so that
page weighed 72 MB.

Two jobs:

  1. Recompress every photograph in place to a sane web size. These are what a
     post shows and what the lightbox opens.

  2. Write a <name>-thumb.<ext> beside each one for the gallery grid.

The full-resolution originals are not lost: they are in git history, in the
commit that rescued them from the Micro.blog CDN.

Idempotent. Already-optimised files are skipped, and thumbnails are never
themselves treated as sources.
"""
import pathlib
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("FAIL: Pillow is required.  pip3 install Pillow")

FULL_MAX = 1600      # long edge for the image a reader actually opens
FULL_Q = 80
THUMB_MAX = 800      # long edge for a grid tile, which is never bigger than this
THUMB_Q = 72
THUMB_SUFFIX = "-thumb"

# Anything already at or under this is left alone, so re-running is cheap and
# does not slowly degrade a file by recompressing it over and over.
ALREADY_SMALL_BYTES = 400 * 1024

ROOTS = [pathlib.Path("static/uploads"), pathlib.Path("content")]
EXTS = {".jpg", ".jpeg", ".png"}


def sources():
    for root in ROOTS:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if p.suffix.lower() in EXTS and THUMB_SUFFIX not in p.stem:
                yield p


def save(img, path, quality):
    if path.suffix.lower() == ".png":
        img.save(path, "PNG", optimize=True)
    else:
        img.convert("RGB").save(
            path, "JPEG", quality=quality, optimize=True, progressive=True
        )


def main() -> int:
    shrunk = skipped = thumbed = 0
    before = after = 0

    for src in sources():
        size = src.stat().st_size
        before += size

        with Image.open(src) as im:
            im.load()

            # 1. The full-size image the reader opens.
            if size > ALREADY_SMALL_BYTES or max(im.size) > FULL_MAX:
                full = im.copy()
                full.thumbnail((FULL_MAX, FULL_MAX), Image.LANCZOS)
                save(full, src, FULL_Q)
                shrunk += 1
            else:
                skipped += 1

            # 2. The thumbnail the grid uses.
            thumb_path = src.with_name(f"{src.stem}{THUMB_SUFFIX}{src.suffix}")
            if not thumb_path.exists():
                thumb = im.copy()
                thumb.thumbnail((THUMB_MAX, THUMB_MAX), Image.LANCZOS)
                save(thumb, thumb_path, THUMB_Q)
                thumbed += 1

        after += src.stat().st_size

    print(f"  recompressed : {shrunk}")
    print(f"  left alone   : {skipped}")
    print(f"  thumbnails   : {thumbed} written")
    print(f"  originals    : {before // 1024 // 1024} MB -> {after // 1024 // 1024} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
