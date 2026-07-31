#!/usr/bin/env python3
"""Export every post as a readable markdown file.

The posts are already markdown, but they are stored the way Hugo wants them:
content/2026/07/29/started-blogging-again/index.md. Eighteen files all called
index.md, in eighteen nested folders, is fine for a site and useless for
reading, searching, or opening in anything else.

This flattens them to 2026-07-29-started-blogging-again.md in one folder, keeps
the front matter, and rewrites image paths so the pictures still resolve. An
untitled micro post is named from its opening words, so the filenames say
something.

Nothing is moved or changed in the repo. This only ever reads.

    python3 scripts/export-markdown.py                 -> ~/Downloads/mint-posts-<date>/
    python3 scripts/export-markdown.py --zip           -> ...and a .zip beside it
    python3 scripts/export-markdown.py --with-images   -> copy the photographs too
    python3 scripts/export-markdown.py --out ~/Desktop
"""
import argparse, datetime, pathlib, re, shutil, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"


def front_matter(text):
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[3:end].strip(), text[end + 4:].lstrip("\n")


def field(fm, name):
    m = re.search(rf"^{name}:\s*(.+)$", fm, re.M)
    return m.group(1).strip().strip('"\'') if m else ""


def slugify(s, limit=8):
    # The Micro.blog imports carry raw <img> tags rather than markdown, so
    # stripping only markdown images left filenames like
    # "chi-tarctica-img-srcuploads2025c97644...jpg-width450-height600-alt.md".
    s = re.sub(r"<[^>]+>", " ", s)                        # raw HTML
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)          # markdown images
    s = re.sub(r"[^\w\s-]", "", s.lower())
    words = [w for w in s.split() if w][:limit]
    return "-".join(words) or "post"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(pathlib.Path.home() / "Downloads"))
    ap.add_argument("--zip", action="store_true")
    ap.add_argument("--with-images", action="store_true")
    args = ap.parse_args()

    stamp = datetime.date.today().isoformat()
    out = pathlib.Path(args.out).expanduser() / f"mint-posts-{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    if args.with_images:
        (out / "images").mkdir(exist_ok=True)

    written = images = 0
    for src in sorted(CONTENT.rglob("index.md")):
        raw = src.read_text(encoding="utf-8", errors="replace")
        fm, body = front_matter(raw)
        if field(fm, "type") != "post":
            continue

        date = (field(fm, "date") or "")[:10] or "undated"
        title = field(fm, "title")
        name = f"{date}-{slugify(title) if title else slugify(body)}.md"

        text = raw
        if args.with_images:
            # Same reason: match markdown images AND raw <img src>, or most of
            # the archive's photographs are silently left behind.
            refs = set(re.findall(r"!\[[^\]]*\]\((/[^)\s]+)", raw))
            refs |= set(re.findall(r'<img[^>]+src="(/[^"]+)"', raw))
            for ref in refs:
                f = STATIC / ref.lstrip("/")
                if f.exists():
                    dst = out / "images" / f.name
                    if not dst.exists():
                        shutil.copy2(f, dst)
                        images += 1
                    text = text.replace(ref, f"images/{f.name}")

        (out / name).write_text(text, encoding="utf-8")
        written += 1

    print(f"  {written} posts -> {out}", file=sys.stderr)
    if args.with_images:
        print(f"  {images} photographs -> {out / 'images'}", file=sys.stderr)

    if args.zip:
        archive = out.with_suffix(".zip")
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            for f in out.rglob("*"):
                if f.is_file():
                    z.write(f, f.relative_to(out.parent))
        print(f"  zipped -> {archive}  ({archive.stat().st_size // 1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main()
