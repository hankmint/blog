#!/usr/bin/env python3
"""Generate the site icons and the social share card.

The blog had no favicon, no app icons and no share image, so a link to it
rendered as bare grey text everywhere it was posted, and the browser tab was
blank.

Everything here is drawn from the theme's own palette in static/css/mint.css,
in a serif close to the Fraunces display face the site uses. The web fonts
themselves are woff2, which Pillow cannot read, so this uses Georgia, which is
what the theme's own font stack falls back to anyway.

Idempotent: re-running simply redraws the same files.
"""
import pathlib
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("FAIL: Pillow is required.  pip3 install Pillow")

PAPER = (251, 248, 243)
PAPER_DARK = (22, 19, 15)
INK = (29, 26, 22)
ACCENT = (122, 46, 40)
MUTED = (110, 103, 93)

SERIF_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
SERIF = "/System/Library/Fonts/Supplemental/Georgia.ttf"
SANS = "/System/Library/Fonts/Supplemental/Futura.ttc"

OUT = pathlib.Path("static")


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def centre(draw, xy, text, f, fill, tracking=0):
    """Draw text centred on xy, optionally letter-spaced."""
    cx, cy = xy
    if not tracking:
        w = draw.textbbox((0, 0), text, font=f)[2]
        h = draw.textbbox((0, 0), text, font=f)[3]
        draw.text((cx - w / 2, cy - h / 2), text, font=f, fill=fill)
        return
    widths = [draw.textbbox((0, 0), c, font=f)[2] for c in text]
    total = sum(widths) + tracking * (len(text) - 1)
    h = draw.textbbox((0, 0), text, font=f)[3]
    x = cx - total / 2
    for c, w in zip(text, widths):
        draw.text((x, cy - h / 2), c, font=f, fill=fill)
        x += w + tracking


def icon(size):
    """A single M on oxblood. Reads at 16px, which a wordmark would not."""
    img = Image.new("RGB", (size, size), ACCENT)
    d = ImageDraw.Draw(img)
    centre(d, (size / 2, size / 2 - size * 0.06), "M", font(SERIF_BOLD, int(size * 0.62)), PAPER)
    return img


def share_card():
    """1200x630, the size every social network and messaging app expects."""
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)

    # A broad oxblood band down the left, so the card is recognisable as a
    # shape even at thumbnail size in a message list.
    d.rectangle([0, 0, 18, h], fill=ACCENT)

    centre(d, (w / 2, h / 2 - 74), "MINT", font(SERIF_BOLD, 132), INK, tracking=22)
    centre(d, (w / 2, h / 2 + 16), "by Nana Kofi", font(SERIF, 40), MUTED, tracking=4)

    d.line([(w / 2 - 150, h / 2 + 74), (w / 2 + 150, h / 2 + 74)], fill=ACCENT, width=2)
    centre(d, (w / 2, h / 2 + 128), "On building, creativity, and life.", font(SERIF, 32), INK)
    centre(d, (w / 2, h - 62), "nanakofiwrites.com", font(SERIF, 26), MUTED, tracking=3)
    return img


def main() -> int:
    OUT.mkdir(exist_ok=True)
    written = []

    for size, name in [
        (32, "favicon-32.png"),
        (180, "apple-touch-icon.png"),
        (192, "icon-192.png"),
        (512, "icon-512.png"),
    ]:
        p = OUT / name
        icon(size).save(p, "PNG", optimize=True)
        written.append(p)

    # A real .ico so old browsers and bookmark bars behave.
    ico = OUT / "favicon.ico"
    icon(64).save(ico, "ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    written.append(ico)

    card = OUT / "share-card.png"
    share_card().save(card, "PNG", optimize=True)
    written.append(card)

    for p in written:
        print(f"  {p}  {p.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
