# Movement 1: Self-Hosted nanakofiwrites.com Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `hankmint/blog` from a Micro.blog theme into a self-hosted Hugo site that serves nanakofiwrites.com with all 18 posts, all 28 photographs, and working feeds, depending on nothing owned by Micro.blog.

**Architecture:** The repo's existing `layouts/` and `static/` are already at a Hugo site root, so the MINT theme becomes the site's own layouts rather than a `themes/` subdirectory. Content and photographs are imported from the Micro.blog export, with every Micro.blog URL rewritten to a local path. Feed templates are adopted from Micro.blog's own MIT-licensed export so `/feed.json` and `/feed.xml` keep the exact shape the cross-posting relay already reads.

**Tech Stack:** Hugo 0.163.2 extended (installed at `/opt/homebrew/bin/hugo`), Bash, Python 3 for the content rewrite, Cloudflare Pages for hosting.

**Spec:** `docs/superpowers/specs/2026-07-28-selfhost-migration-design.md`

## Global Constraints

- **No em dashes or en dashes** in any file, comment, commit message or copy. Use commas, colons, periods or "to". This applies to content and to code comments.
- **Never delete or overwrite anything in the Micro.blog account.** This plan only reads from it.
- **`/feed.json` and `/feed.xml` must exist at exactly those paths.** `https://nanakofiwrites.com/feed.json` is registered on Kay's Micro.blog Sources page and drives cross-posting to twelve networks. If it 404s or returns invalid JSON Feed, cross-posting stops with no error anywhere.
- **Post permalinks must not change.** Every post carries `url:` in its front matter. Preserve it byte for byte.
- **Zero references to `cdn.uploads.micro.blog` or `s3.amazonaws.com/micro.blog` may remain** in generated HTML at the end of Task 3.
- The export lives at `~/Downloads/themint_e83356.zip`. Unpacked working copy is at `/private/tmp/claude-501/-Users-mint/e7f4cbdf-04e6-46a3-a32c-85c3878e2105/scratchpad/mbexport`. Re-unzip if missing; never edit the zip.
- Micro.blog CDN base for this account is `https://cdn.uploads.micro.blog/217795/`. Site ID `217795`.
- Commit after every task. Do not push without Kay's explicit say-so.

## File Structure

| File | Responsibility |
| --- | --- |
| `scripts/rescue-photos.sh` | Create. Reads the export, downloads every original photo into `static/uploads/`. Idempotent. |
| `scripts/rewrite-content.py` | Create. Rewrites Micro.blog URLs in imported content to local paths. Idempotent. |
| `scripts/verify-site.sh` | Create. The test harness. Asserts every invariant against `public/` after a build. Grows across tasks. |
| `hugo.toml` | Create. Site config: baseURL, feed output formats, taxonomy, goldmark unsafe, MINT params. |
| `content/` | Create. The 18 posts, 5 pages, 1 note from the export. |
| `static/uploads/` | Create. The 28 rescued photographs. |
| `layouts/partials/microblog_head.html` | Create. Empty stub replacing the partial Micro.blog injected. |
| `layouts/index.json` | Create. JSON Feed template, adopted from the export. |
| `layouts/_default/rss.xml` | Create. RSS template, adopted from the export. |
| `layouts/_default/_markup/render-image.html` | Create. Turns Markdown images with a title into captioned figures. |
| `layouts/index.html` | Modify. Year index must include untitled posts. |
| `content/photos.md` | Modify. Declare `type: gallery` so the MINT gallery template renders at `/photos/`. |
| `content/archive.md`, `content/stories.md`, `content/replies.md` | Modify. Drop `menu: main` so blank pages leave the nav. URLs stay alive. |
| `config.json` | Delete. Micro.blog params file, superseded by `hugo.toml`. |

`layouts/partials/header.html` is deliberately NOT modified. Its nav ranges over `.Site.Menus.main`, which the pages populate through their own front matter.

---

### Task 1: Rescue the photographs

This is the only irreversible step in the project. The export contains no image files. All 28 photographs exist solely on Micro.blog's CDN.

**Files:**
- Create: `scripts/rescue-photos.sh`
- Create: `static/uploads/2025/*.jpg`, `static/uploads/2026/*.jpg` (28 files, ~35 MB)

**Interfaces:**
- Consumes: the unpacked export at `$EXPORT` (default `/private/tmp/claude-501/-Users-mint/e7f4cbdf-04e6-46a3-a32c-85c3878e2105/scratchpad/mbexport`)
- Produces: `static/uploads/<year>/<filename>` for every photo. Later tasks rewrite content to point at `/uploads/<year>/<filename>`.

- [ ] **Step 1: Write the rescue script**

Create `scripts/rescue-photos.sh`:

```bash
#!/usr/bin/env bash
# Downloads every photograph referenced by the Micro.blog export into static/uploads/.
# The export contains no image files. These exist only on Micro.blog's CDN.
# Idempotent: already-downloaded files are skipped.
set -euo pipefail

EXPORT="${EXPORT:-/private/tmp/claude-501/-Users-mint/e7f4cbdf-04e6-46a3-a32c-85c3878e2105/scratchpad/mbexport}"
CDN_BASE="https://cdn.uploads.micro.blog/217795"
DEST="static/uploads"

if [ ! -d "$EXPORT/content" ]; then
  echo "FAIL: export not found at $EXPORT" >&2
  exit 1
fi

# Collect relative paths like "2025/abc123.jpg" from two places:
#  1. body <img src="uploads/2025/abc123.jpg">
#  2. front matter absolute CDN URLs
{
  grep -rhoE '<img[^>]+src="uploads/[^"]+"' "$EXPORT/content" \
    | sed -E 's|.*src="uploads/||; s|"$||'
  grep -rhoE "https://cdn\.uploads\.micro\.blog/217795/[^ \"')]+" "$EXPORT/content" \
    | sed -E "s|https://cdn\.uploads\.micro\.blog/217795/||"
} | sed 's|[[:space:]]*$||' | sort -u > /tmp/photo-list.txt

total=$(wc -l < /tmp/photo-list.txt | tr -d ' ')
echo "Found $total unique photographs to rescue."

ok=0; skip=0; fail=0
while IFS= read -r rel; do
  [ -z "$rel" ] && continue
  out="$DEST/$rel"
  if [ -s "$out" ]; then
    skip=$((skip+1)); continue
  fi
  mkdir -p "$(dirname "$out")"
  if curl -fsS --max-time 60 -o "$out" "$CDN_BASE/$rel"; then
    ok=$((ok+1)); echo "  got $rel"
  else
    fail=$((fail+1)); rm -f "$out"; echo "  FAILED $rel" >&2
  fi
done < /tmp/photo-list.txt

echo "downloaded=$ok skipped=$skip failed=$fail"
[ "$fail" -eq 0 ] || { echo "FAIL: $fail photographs could not be rescued" >&2; exit 1; }
```

- [ ] **Step 2: Run it**

```bash
chmod +x scripts/rescue-photos.sh && ./scripts/rescue-photos.sh
```

Expected: `Found 28 unique photographs to rescue.` then `downloaded=28 skipped=0 failed=0`.

If the count is not 28, stop and investigate before continuing. Do not proceed with a partial rescue.

- [ ] **Step 3: Verify every file is a real image, not an error page**

```bash
find static/uploads -type f | wc -l
find static/uploads -type f -exec file --mime-type {} \; | grep -cv 'image/'
du -sh static/uploads
```

Expected: file count `28`, non-image count `0`, size roughly 30 to 40 MB.

A zero-byte file or an `text/html` mime type means the CDN returned an error page. Delete it and re-run.

- [ ] **Step 4: Commit the photographs**

```bash
git add scripts/rescue-photos.sh static/uploads
git commit -m "feat: rescue all 28 photographs from the Micro.blog CDN

The Micro.blog export contains no image files. These 28 photographs existed
only on cdn.uploads.micro.blog and would have been lost permanently if the
hosted blog were deleted first."
```

- [ ] **Step 5: Confirm they are safe**

```bash
git log --stat -1 | tail -5
```

Expected: the commit contains 28 image files plus the script. From this point the photographs exist in git history and the migration is no longer destructive.

---

### Task 2: Make the repo a Hugo site that builds

**Files:**
- Create: `hugo.toml`
- Create: `layouts/partials/microblog_head.html`
- Create: `scripts/verify-site.sh`
- Delete: `config.json`, and the untracked iCloud duplicates

**Interfaces:**
- Produces: a `hugo` build that exits 0 with no content. `scripts/verify-site.sh` becomes the test harness every later task extends.

- [ ] **Step 1: Delete the iCloud duplicate cruft**

These are untracked files macOS created by syncing. They are the same class of file that breaks CLI builds on `knodai_v1`.

```bash
cd /Users/mint/Documents/GitHub/blog
git status --porcelain --untracked-files=all | grep ' 2\.' || true
find . -name '* 2.*' -not -path './.git/*' -print -delete
find . -name '* 2' -type d -not -path './.git/*' -print -exec rmdir {} + 2>/dev/null || true
git status --short
```

Expected: the `* 2` files are listed then removed, and `git status --short` shows a clean tree.

- [ ] **Step 2: Write the failing verification harness**

Create `scripts/verify-site.sh`. It builds the site and asserts the invariants. At this point only the build assertion exists; later tasks add more.

```bash
#!/usr/bin/env bash
# The test harness for the self-hosted site. Builds, then asserts invariants.
# Every assertion here corresponds to a success criterion in the design spec.
set -uo pipefail

FAILED=0
pass() { echo "  PASS  $1"; }
fail() { echo "  FAIL  $1" >&2; FAILED=1; }
check() { if [ "$1" = "0" ]; then pass "$2"; else fail "$2"; fi }

echo "Building..."
if hugo --quiet --destination public; then
  pass "hugo build exits 0"
else
  fail "hugo build exits 0"
  echo "Build failed, cannot run further assertions." >&2
  exit 1
fi

echo
echo "Results:"
if [ "$FAILED" -eq 0 ]; then echo "ALL ASSERTIONS PASSED"; else echo "THERE WERE FAILURES" >&2; fi
exit "$FAILED"
```

- [ ] **Step 3: Run it to verify it fails**

```bash
chmod +x scripts/verify-site.sh && ./scripts/verify-site.sh
```

Expected: FAIL. Hugo errors because there is no site config and because `layouts/partials/head.html` calls `microblog_head.html`, which does not exist.

- [ ] **Step 4: Write the site config**

Create `hugo.toml`. The `outputFormats` and `mediaTypes` blocks are copied from Micro.blog's own exported `config.json` and are safety-critical: they are what produce `/feed.xml` and `/feed.json`.

```toml
baseURL = "https://nanakofiwrites.com/"
languageCode = "en"
defaultContentLanguage = "en"
title = "M I N T"
enableRobotsTXT = true
pluralizeListTitles = false

[pagination]
  pagerSize = 25

[services.rss]
  limit = 25

[taxonomies]
  category = "categories"

# Required: post bodies contain raw HTML img tags.
[markup.goldmark.renderer]
  unsafe = true

# Feed output. Carried over verbatim from Micro.blog's exported config so that
# /feed.json and /feed.xml keep the exact paths the cross-posting relay reads.
[mediaTypes."application/json"]
  suffixes = ["json"]

[outputFormats.RSS]
  baseName = "feed"

[outputFormats.JSON]
  baseName = "feed"
  mediaType = "application/json"

[outputs]
  home = ["HTML", "RSS", "JSON"]
  page = ["HTML"]
  section = ["HTML"]
  taxonomy = ["HTML"]
  term = ["HTML"]

# MINT theme params, carried over from the old Micro.blog config.json.
[params]
  dateFormatToUse = "January 02, 2006"
  logoTitle = '<span class="mark">MINT</span><span class="by">by Nana Kofi</span>'
  description = "On building, creativity, and life."
  featuredCount = 2
  archive-paginate = 100

[params.author]
  name = "Nana Kofi"
```

- [ ] **Step 5: Stub the Micro.blog partial**

Create `layouts/partials/microblog_head.html`:

```html
{{/* Micro.blog injected this partial when the site was hosted there.
     Self-hosted, it is ours and intentionally empty. Anything that must go
     in <head> belongs in head.html. */}}
```

- [ ] **Step 6: Remove the superseded Micro.blog params file**

```bash
git rm config.json
```

- [ ] **Step 7: Run the harness to verify it passes**

```bash
./scripts/verify-site.sh
```

Expected: `PASS  hugo build exits 0` and `ALL ASSERTIONS PASSED`. The site is empty, which is correct at this stage.

- [ ] **Step 8: Commit**

```bash
echo "public/" >> .gitignore
echo "resources/_gen/" >> .gitignore
git add -A hugo.toml layouts/partials/microblog_head.html scripts/verify-site.sh .gitignore
git add -u
git commit -m "feat: turn the theme repo into a self-hosted Hugo site

Adds hugo.toml carrying over Micro.blog's own feed output formats, taxonomy
and goldmark unsafe setting. Stubs the microblog_head partial that Micro.blog
injected. Removes the superseded config.json and the iCloud duplicate files."
```

---

### Task 3: Import the content and cut every tie to Micro.blog's servers

**Files:**
- Create: `scripts/rewrite-content.py`
- Create: `content/**` (18 posts, 5 pages, 1 note)
- Modify: `scripts/verify-site.sh` (add assertions)

**Interfaces:**
- Consumes: `static/uploads/` from Task 1, `hugo.toml` from Task 2
- Produces: `content/` where every image reference is a local `/uploads/...` path

- [ ] **Step 1: Copy the content in, untouched**

```bash
EXPORT=/private/tmp/claude-501/-Users-mint/e7f4cbdf-04e6-46a3-a32c-85c3878e2105/scratchpad/mbexport
mkdir -p content && cp -R "$EXPORT/content/." content/
find content -name '*.md' | wc -l
```

Expected: `24`.

- [ ] **Step 2: Add the assertions that must fail right now**

Append to `scripts/verify-site.sh`, before the `echo "Results:"` line:

```bash
# --- Content and images ---
POSTS=$(find content -path 'content/20*' -name '*.md' | wc -l | tr -d ' ')
[ "$POSTS" = "18" ]; check $? "18 posts present in content/"

# No generated page may reference Micro.blog's servers.
LEAKS=$(grep -rlE 'cdn\.uploads\.micro\.blog|s3\.amazonaws\.com/micro\.blog' public --include='*.html' --include='*.json' --include='*.xml' 2>/dev/null | wc -l | tr -d ' ')
[ "$LEAKS" = "0" ]; check $? "no Micro.blog CDN references in generated output (found $LEAKS files)"

# Every image the built HTML asks for must exist on disk.
MISSING=0
for src in $(grep -rhoE 'src="/uploads/[^"]+"' public --include='*.html' | sed 's|src="||; s|"$||' | sort -u); do
  [ -f "public$src" ] || { echo "    missing: $src" >&2; MISSING=$((MISSING+1)); }
done
[ "$MISSING" = "0" ]; check $? "every referenced image resolves locally ($MISSING missing)"

IMGCOUNT=$(find static/uploads -type f | wc -l | tr -d ' ')
[ "$IMGCOUNT" = "28" ]; check $? "28 photographs present in static/uploads"

# --- Permalinks must not change. Every url: in front matter must exist as a
#     generated page at exactly that path. This is a hard constraint: those URLs
#     are already live and already sitting in the Micro.blog timeline. ---
BADURL=0
for u in $(grep -rhoE '^url: "[^"]+"' content | sed 's|^url: "||; s|"$||' | sort -u); do
  case "$u" in
    */) target="public${u}index.html" ;;
    *)  target="public${u}" ;;
  esac
  [ -f "$target" ] || { echo "    permalink missing: $u" >&2; BADURL=$((BADURL+1)); }
done
[ "$BADURL" = "0" ]; check $? "every declared permalink resolves ($BADURL missing)"
```

- [ ] **Step 3: Run the harness to verify it fails**

```bash
./scripts/verify-site.sh
```

Expected: `FAIL  no Micro.blog CDN references in generated output` and `FAIL  every referenced image resolves locally`. The content is still pointing at Micro.blog.

- [ ] **Step 4: Write the rewrite script**

Create `scripts/rewrite-content.py`:

```python
#!/usr/bin/env python3
"""Rewrite Micro.blog URLs in imported content to local paths.

Three jobs:
  1. Body <img src="uploads/..."> becomes site-absolute /uploads/...
  2. Front matter CDN URLs become /uploads/...
  3. Micro.blog-generated front matter keys that point at their servers and
     that the MINT theme does not read are dropped entirely.

Idempotent: safe to run more than once.
"""
import pathlib
import re
import sys

CDN = "https://cdn.uploads.micro.blog/217795/"
OWN = "https://nanakofiwrites.com/uploads/"

# Keys Micro.blog generated that point at their infrastructure. The MINT theme
# reads .Params.images and .Params.image only, so these are dead weight that
# would keep the site tethered to Micro.blog.
DROP_KEYS = ("thumbnail:", "opengraph:", "photos_with_metadata:")

root = pathlib.Path("content")
if not root.is_dir():
    sys.exit("FAIL: content/ not found. Run step 1 first.")

changed = 0
for path in sorted(root.rglob("*.md")):
    original = path.read_text(encoding="utf-8")
    text = original

    # 1. Body images: src="uploads/..." becomes src="/uploads/..."
    text = re.sub(r'src="uploads/', 'src="/uploads/', text)

    # 2. Absolute URLs in front matter and body become local paths.
    text = text.replace(CDN, "/uploads/")
    text = text.replace(OWN, "/uploads/")

    # 3. Drop the Micro.blog-only front matter blocks. A block runs from its
    #    key at column 0 until the next column-0 key or the closing ---.
    lines = text.split("\n")
    out, skipping = [], False
    for line in lines:
        if skipping:
            # Still inside the dropped block if the line is indented or a list item.
            if line.startswith((" ", "\t", "-")) and line.strip():
                continue
            skipping = False
        if line.startswith(DROP_KEYS):
            skipping = True
            continue
        out.append(line)
    text = "\n".join(out)

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1

print(f"rewrote {changed} files")
```

- [ ] **Step 5: Run the rewrite**

```bash
python3 scripts/rewrite-content.py
```

Expected: `rewrote 18 files` or similar. Then confirm nothing points at Micro.blog any more:

```bash
grep -rc 'micro\.blog' content | grep -v ':0' || echo "no micro.blog references remain in content"
```

Expected: only `guid:` lines may remain, which are permanent post identifiers and must NOT be rewritten. Verify with:

```bash
grep -rhoE 'micro\.blog[^ "]*' content | sort | uniq -c
```

Expected: only `micro.blog/...` fragments from `guid:` values. No `cdn.uploads.micro.blog` and no `s3.amazonaws.com`.

- [ ] **Step 6: Run the harness to verify it passes**

```bash
./scripts/verify-site.sh
```

Expected: all four content assertions PASS, including `28 photographs present` and `every referenced image resolves locally (0 missing)`.

- [ ] **Step 7: Look at it with your own eyes**

```bash
hugo server --port 1313 &
sleep 3
open http://localhost:1313/2025/12/21/i-forgot-to-share-these.html
```

Confirm both photographs render. Then stop the server.

- [ ] **Step 8: Commit**

```bash
git add scripts/rewrite-content.py content scripts/verify-site.sh
git commit -m "feat: import posts and cut every tie to Micro.blog's servers

Imports the 18 posts, 5 pages and 1 note from the export, then rewrites every
image reference to a local path. Rewrites front matter as well as post bodies,
because the gallery template reads .Params.images before it reads the body and
would otherwise have kept loading from Micro.blog's CDN.

Drops the thumbnail, opengraph and photos_with_metadata keys, which Micro.blog
generated, which point at their infrastructure, and which the MINT theme does
not read."
```

---

### Task 4: The feeds that keep cross-posting alive

**Files:**
- Create: `layouts/index.json`, `layouts/_default/rss.xml`
- Modify: `scripts/verify-site.sh`, `LICENSE`

**Interfaces:**
- Consumes: the `outputFormats` from `hugo.toml` (Task 2) and content (Task 3)
- Produces: `public/feed.json` and `public/feed.xml`

- [ ] **Step 1: Add the failing feed assertions**

Append to `scripts/verify-site.sh` before `echo "Results:"`:

```bash
# --- Feeds. Safety-critical: /feed.json drives cross-posting to twelve networks. ---
[ -f public/feed.json ]; check $? "public/feed.json exists"
[ -f public/feed.xml ];  check $? "public/feed.xml exists"

if [ -f public/feed.json ]; then
  python3 -c "import json,sys; json.load(open('public/feed.json'))" 2>/dev/null
  check $? "feed.json is valid JSON"

  python3 - <<'PY' 2>/dev/null
import json, sys
d = json.load(open("public/feed.json"))
assert d.get("version", "").startswith("https://jsonfeed.org/version/"), "missing jsonfeed version"
assert d.get("feed_url", "").endswith("/feed.json"), "feed_url must end in /feed.json"
items = d.get("items", [])
assert len(items) == 18, f"expected 18 items, got {len(items)}"
for it in items:
    assert it.get("id"), "item missing id"
    assert it.get("url"), "item missing url"
    assert it.get("date_published"), "item missing date_published"
    assert "content_html" in it, "item missing content_html"
PY
  check $? "feed.json is a valid JSON Feed with all 18 items"
fi
```

- [ ] **Step 2: Run the harness to verify it fails**

```bash
./scripts/verify-site.sh
```

Expected: `FAIL  public/feed.json exists`. Hugo declares the output format but has no template to render it.

- [ ] **Step 3: Adopt Micro.blog's JSON Feed template**

Create `layouts/index.json`. This is Micro.blog's own template from the export (MIT, Copyright 2019 Micro.blog), with the avatar changed to a local path since the Micro.blog-hosted avatar goes away.

```
{{- /* JSON Feed. Adopted from the Micro.blog export theme (MIT, (c) 2019 Micro.blog).
       Safety-critical: https://nanakofiwrites.com/feed.json is registered on Kay's
       Micro.blog Sources page and drives cross-posting. Do not rename or move. */ -}}
{
	"version": "https://jsonfeed.org/version/1",
	"title": {{ .Site.Title | jsonify }},
	"home_page_url": "{{ .Site.BaseURL }}",
	"feed_url": "{{ .Site.BaseURL }}feed.json",
	"items": [
		{{- $list := first 25 (where .Site.RegularPages "Type" "post") -}}
		{{- $len := (len $list) -}}
		{{ range $index, $value := $list }}
			{
				{{ if .Params.guid -}}
				"id": "{{ .Params.guid }}",
				{{- else -}}
				"id": "{{ .Permalink }}",
				{{- end }}
				{{ if .Title -}}
				"title": {{ .Title | jsonify }},
				{{- end -}}
				{{- $s := .Content | jsonify -}}
				{{- $s := replace $s "\\u003c" "<" -}}
				{{- $s := replace $s "\\u003e" ">" -}}
				{{- $s := replace $s "\\u0026" "&" }}
				"content_html": {{ $s }},
				"date_published": "{{ .Date.Format "2006-01-02T15:04:05-07:00" }}",
				"url": "{{ .Permalink }}"
				{{- with .Params.categories -}}
				,
				"tags": {{ . | jsonify }}
				{{- end }}
			}
			{{- if ne (add $index 1) $len -}},{{- end -}}
		{{ end }}
	]
}
```

- [ ] **Step 4: Adopt Micro.blog's RSS template**

Create `layouts/_default/rss.xml`, same provenance:

```xml
{{- /* RSS. Adopted from the Micro.blog export theme (MIT, (c) 2019 Micro.blog).
       Serves /feed.xml, which the footer links and which readers subscribe to. */ -}}
<rss version="2.0">
  <channel>
    <title>{{ if eq .Title .Site.Title }}{{ .Site.Title }}{{ else }}{{ with .Title }}{{ . }} on {{ end }}{{ .Site.Title }}{{ end }}</title>
    <link>{{ .Permalink }}</link>
    <description>{{ .Site.Params.description }}</description>
    {{ with .Site.LanguageCode }}<language>{{ . }}</language>{{ end }}
    <lastBuildDate>{{ .Date.Format "Mon, 02 Jan 2006 15:04:05 -0700" | safeHTML }}</lastBuildDate>
    {{ range .Pages }}
    <item>
      <title>{{ .Title }}</title>
      <link>{{ .Permalink }}</link>
      <pubDate>{{ .Date.Format "Mon, 02 Jan 2006 15:04:05 -0700" | safeHTML }}</pubDate>
      {{- if .Params.guid }}
      <guid>{{ .Params.guid }}</guid>
      {{- else }}
      <guid>{{ .Permalink }}</guid>
      {{- end }}
      <description>{{ .Content | html }}</description>
    </item>
    {{ end }}
  </channel>
</rss>
```

- [ ] **Step 5: Record the attribution**

Append to `LICENSE`:

```
The feed templates layouts/index.json and layouts/_default/rss.xml are adopted
from the Micro.blog export theme, MIT licensed, Copyright (c) 2019 Micro.blog.
```

- [ ] **Step 6: Run the harness to verify it passes**

```bash
./scripts/verify-site.sh
```

Expected: all four feed assertions PASS, including `feed.json is a valid JSON Feed with all 18 items`.

- [ ] **Step 7: Read the feed yourself**

```bash
python3 -m json.tool public/feed.json | head -30
```

Confirm `feed_url` reads `https://nanakofiwrites.com/feed.json` exactly.

- [ ] **Step 8: Commit**

```bash
git add layouts/index.json layouts/_default/rss.xml LICENSE scripts/verify-site.sh
git commit -m "feat: serve /feed.json and /feed.xml so cross-posting survives the move

Adopts Micro.blog's own MIT-licensed feed templates from the export, so the
JSON Feed keeps the exact shape their relay already reads. This is the piece
that fails silently: if /feed.json 404s or is malformed, cross-posting to
twelve networks stops with no error anywhere."
```

---

### Task 5: Make the site show its own content

Three separate defects here, all verified. Without this the homepage renders "0 essays", the gallery does not exist at all, and four of the five nav links lead to blank pages.

**Background, established by reading the files:**

- `layouts/index.html` line 3 filters `"Title" "!=" ""`, and none of the 18 posts has a title.
- `layouts/gallery/single.html` only renders for a page with `type: gallery`. No content declares it, so the gallery and its lightbox never appear.
- The nav is not hardcoded. `layouts/partials/header.html` line 18 ranges over `.Site.Menus.main`, populated by the `menu: main` front matter on the five imported pages: About (weight 1), Photos (2), Stories (3), Replies (4), Archive (5).
- `photos.md` carries `type: photos` and `layout: list.photoshtml`, and `archive.md` carries `type: archive` and `layout: list.archivehtml`. Both are Micro.blog templates that do not exist in this theme, so both pages render blank.
- `stories.md` and `replies.md` are empty. `replies.md` has no content and no source of content now that Micro.blog's conversation system is gone.

**Files:**
- Modify: `layouts/index.html`
- Modify: `content/photos.md`, `content/archive.md`, `content/stories.md`, `content/replies.md`
- Modify: `scripts/verify-site.sh`

- [ ] **Step 1: Read the current templates before changing them**

```bash
sed -n '1,60p' layouts/index.html
cat layouts/partials/header.html
head -12 content/photos.md content/archive.md content/stories.md content/replies.md
```

- [ ] **Step 2: Add the failing assertions**

Append to `scripts/verify-site.sh` before `echo "Results:"`:

```bash
# --- The homepage must not be empty on day one. ---
ENTRIES=$(grep -c 'class="mint-entry' public/index.html || true)
[ "${ENTRIES:-0}" -ge 16 ]; check $? "homepage index lists the posts (found ${ENTRIES:-0} entries)"

if grep -q '0 essays' public/index.html; then fail "homepage says '0 essays'"; else pass "homepage does not say '0 essays'"; fi

# --- The gallery must actually render, with photographs in it. ---
[ -f public/photos/index.html ]; check $? "the gallery page is generated at /photos/"
if [ -f public/photos/index.html ]; then
  SHOTS=$(grep -c 'class="mint-shot"' public/photos/index.html || true)
  [ "${SHOTS:-0}" -ge 20 ]; check $? "the gallery shows the photographs (found ${SHOTS:-0})"
  if grep -q 'mint-gallery-empty' public/photos/index.html; then fail "the gallery says it is empty"; else pass "the gallery is not empty"; fi
fi

# --- No nav link may lead to a blank page. ---
for nav in $(grep -oE 'class="nav"' -A20 public/index.html | grep -oE 'href="/[a-z]+/"' | sed 's|href="||; s|"$||' | sort -u); do
  page="public${nav}index.html"
  if [ -f "$page" ]; then
    BYTES=$(wc -c < "$page" | tr -d ' ')
    [ "$BYTES" -gt 2000 ]; check $? "nav link $nav leads to a page with content ($BYTES bytes)"
  else
    fail "nav link $nav has no generated page"
  fi
done
```

- [ ] **Step 3: Run the harness to verify it fails**

```bash
./scripts/verify-site.sh
```

Expected: FAIL on the homepage entries assertion, because every post is untitled and the index filters them out.

- [ ] **Step 4: Include untitled posts in the year index**

In `layouts/index.html`, the featured block keeps using titled posts only. The index changes to use all posts.

Replace line 3:

```
  {{ $posts := where (where .Site.RegularPages "Type" "post") "Title" "!=" "" }}
```

with:

```
  {{ $titled := where (where .Site.RegularPages "Type" "post") "Title" "!=" "" }}
  {{ $titled = $titled.ByDate.Reverse }}
  {{ $posts := where .Site.RegularPages "Type" "post" }}
```

Change the featured range to use `$titled`:

```
      {{ range first $n $titled }}
```

And in the index section, list every post, falling back to the opening line when there is no title. Replace the `$rest` line and the entry markup so that:

```
    {{ $rest := $posts }}
```

and each entry renders:

```
      <li><a class="mint-entry h-entry" href="{{ .Permalink }}">
        <span class="date">{{ .Date.Format "Jan 02" }}</span>
        <span class="title">{{ with .Title }}{{ . }}{{ else }}{{ .Plain | truncate 90 }}{{ end }}</span>
      </a></li>
```

Keep the surrounding year-grouping logic exactly as it is. Update the count label to say "posts" rather than "essays" since it now counts both:

```
      <span class="count">{{ len $posts }} {{ cond (eq (len $posts) 1) "post" "posts" }}</span>
```

- [ ] **Step 5: Make the gallery exist**

Rewrite `content/photos.md` so it triggers the MINT gallery template. Keep `url: /photos/` exactly, so the existing link keeps working, and keep `menu: main` so it stays in the nav.

```markdown
---
title: "Photographs"
navigation: true
menu: main
weight: 2
type: gallery
date: 2025-12-19T00:39:49-0500
url: /photos/
---
Mornings before the city wakes. Photographs, made mostly at first light.
```

Note what changed: `type: photos` becomes `type: gallery`, and the `layout: list.photoshtml` line is removed because that template belongs to Micro.blog and does not exist here.

- [ ] **Step 6: Prune the nav to pages that have something on them**

Three pages would otherwise sit in the nav leading nowhere. Same principle Kay applied to the rooms: nothing on the site should promise something it does not have.

- `content/archive.md`: remove the `menu: main`, `navigation: true`, `weight`, `type: archive` and `layout: list.archivehtml` lines. The MINT homepage is already a year-grouped index, so a separate archive is redundant. Keep the file and its `url: /archive/` so the old URL still resolves.
- `content/stories.md`: remove `menu: main` and `navigation: true`. Empty page, keep the URL alive.
- `content/replies.md`: remove `menu: main` and `navigation: true`. Micro.blog's conversation system does not come with us, so this page has no source of content.

The nav becomes About and Photographs. Both have content.

- [ ] **Step 7: Run the harness to verify it passes**

```bash
./scripts/verify-site.sh
```

Expected: all three assertions PASS.

- [ ] **Step 8: Look at it with your own eyes**

```bash
hugo server --port 1313 &
sleep 3
open http://localhost:1313/
open http://localhost:1313/photos/
```

Confirm: the year index shows 2026 and 2025 with all 18 posts, each showing its opening line; the nav reads About and Photographs only; the gallery at `/photos/` shows the photographs and the lightbox opens on click and closes on Escape. Check both in dark mode. Stop the server.

- [ ] **Step 9: Commit**

```bash
git add layouts/index.html content/photos.md content/archive.md content/stories.md content/replies.md scripts/verify-site.sh
git commit -m "feat: show every post, make the gallery exist, prune the nav

Three defects, all of which would have shipped:

All 18 posts are untitled micro posts and the index filtered to titled posts
only, so the homepage would have read '0 essays'. The year index now carries
every post, showing its opening line when there is no title. The featured
block still shows titled essays and renders nothing until there is one.

The gallery template only fires for type: gallery and no page declared it, so
the gallery and its lightbox never rendered at all. photos.md now declares it,
at the same /photos/ URL.

Archive, Stories and Replies were in the nav carrying Micro.blog layouts that
do not exist here, so all three rendered blank. They leave the nav and keep
their URLs."
```

---

### Task 6: Photographs with captions

**Files:**
- Create: `layouts/_default/_markup/render-image.html`
- Create: `content/2026/07/28/caption-test.md` (temporary, deleted in step 6)
- Modify: `scripts/verify-site.sh`

- [ ] **Step 1: Write the failing test**

Create a temporary post `content/2026/07/28/caption-test.md`:

```markdown
---
date: 2026-07-28T12:00:00-04:00
type: post
title: "Caption test"
url: "/2026/07/28/caption-test.html"
---
![a woman on the cliff path](/uploads/2026/548458a206d94b7f827547b2a14d35bb.jpg "Kwahu, the morning after the storm")
```

Append to `scripts/verify-site.sh` before `echo "Results:"`:

```bash
# --- Captioned images render as real figures. ---
if [ -f public/2026/07/28/caption-test.html ]; then
  grep -q '<figure' public/2026/07/28/caption-test.html
  check $? "markdown image renders as a <figure>"
  grep -q 'Kwahu, the morning after the storm' public/2026/07/28/caption-test.html
  check $? "the caption text appears in the output"
  grep -q '<figcaption' public/2026/07/28/caption-test.html
  check $? "the caption renders in a <figcaption>"
fi
```

- [ ] **Step 2: Run the harness to verify it fails**

```bash
./scripts/verify-site.sh
```

Expected: `FAIL  markdown image renders as a <figure>`. Hugo's default renders a bare `<img>` with the caption stranded in the `title` attribute.

- [ ] **Step 3: Write the render hook**

Create `layouts/_default/_markup/render-image.html`:

```html
{{- /* Turns Markdown images into captioned figures.

       ![alt text](/uploads/2026/photo.jpg "the caption")

       becomes a <figure> with a <figcaption>, styled by the rules already in
       static/css/mint.css. Plain Markdown, so any editor can write it and it
       survives changing editors.

       With no title, it renders a plain img and no caption. */ -}}
{{- $caption := .Title -}}
{{- if $caption -}}
<figure>
  <img src="{{ .Destination | safeURL }}" alt="{{ .Text }}" loading="lazy" />
  <figcaption>{{ $caption }}</figcaption>
</figure>
{{- else -}}
<img src="{{ .Destination | safeURL }}" alt="{{ .Text }}" loading="lazy" />
{{- end -}}
```

- [ ] **Step 4: Run the harness to verify it passes**

```bash
./scripts/verify-site.sh
```

Expected: all three caption assertions PASS.

- [ ] **Step 5: Look at it**

```bash
hugo server --port 1313 &
sleep 3
open http://localhost:1313/2026/07/28/caption-test.html
```

Confirm the caption sits under the photograph in small muted sans-serif, in both light and dark mode. Stop the server.

- [ ] **Step 6: Remove the test post and guard against regression**

```bash
rm content/2026/07/28/caption-test.md
rmdir -p content/2026/07/28 2>/dev/null || true
```

The assertion is wrapped in `if [ -f ... ]` so it skips cleanly once the test post is gone, and runs again for anyone who recreates it.

- [ ] **Step 7: Commit**

```bash
./scripts/verify-site.sh
git add layouts/_default/_markup/render-image.html scripts/verify-site.sh
git commit -m "feat: render markdown images with titles as captioned figures

The caption styling has been sitting in mint.css since the theme was built but
nothing ever emitted a <figure>. A render hook makes it reachable using plain
markdown, so any editor can produce captions and they survive changing editors."
```

---

### Task 7: Deploy a preview and run the editor bake-off

**Files:**
- Create: `static/admin/index.html`, `static/admin/config.yml` (Sveltia)
- Create: `.pages.yml` (Pages CMS)

**Interfaces:**
- Consumes: a passing `scripts/verify-site.sh`
- Produces: a live preview URL and a decision from Kay on which editor to keep

- [ ] **Step 1: Verify everything passes before deploying**

```bash
./scripts/verify-site.sh
```

Expected: `ALL ASSERTIONS PASSED`. Do not deploy otherwise.

- [ ] **Step 2: Push the branch and connect Cloudflare Pages**

Ask Kay before pushing. Then, in the Cloudflare dashboard, create a Pages project connected to the `hankmint/blog` repository with:

- Build command: `hugo --gc --minify`
- Build output directory: `public`
- Environment variable: `HUGO_VERSION` = `0.163.2`

- [ ] **Step 3: Verify the deployed preview**

```bash
PREVIEW="<the pages.dev URL>"
curl -sS -o /dev/null -w "home: %{http_code}\n" "$PREVIEW/"
curl -sS -o /dev/null -w "feed.json: %{http_code}\n" "$PREVIEW/feed.json"
curl -sS -o /dev/null -w "feed.xml: %{http_code}\n" "$PREVIEW/feed.xml"
curl -sS -o /dev/null -w "a post: %{http_code}\n" "$PREVIEW/2025/12/21/i-forgot-to-share-these.html"
curl -sS "$PREVIEW/feed.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print('items:', len(d['items']))"
curl -sS "$PREVIEW/" | grep -c 'cdn.uploads.micro.blog' || echo "no CDN leaks on the live preview"
```

Expected: four `200`s, `items: 18`, and no CDN leaks.

- [ ] **Step 4: Confirm a commit triggers a rebuild**

This is the assumption the whole editing workflow rests on, and the equivalent hook is known-broken on the `remix-knod-ai` repo, so prove it rather than assume it.

Make a trivial commit, push, and confirm Cloudflare builds automatically and the change appears. If it does not, stop and fix the git connection before Task 7 continues.

- [ ] **Step 5: Stand up Sveltia CMS**

Create `static/admin/index.html`:

```html
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>MINT editor</title>
  </head>
  <body>
    <script src="https://unpkg.com/@sveltia/cms/dist/sveltia-cms.js"></script>
  </body>
</html>
```

Create `static/admin/config.yml`:

```yaml
backend:
  name: github
  repo: hankmint/blog
  branch: main

media_folder: static/uploads/2026
public_folder: /uploads/2026

collections:
  - name: posts
    label: Posts
    folder: content/2026
    create: true
    path: "{{year}}/{{month}}/{{day}}/{{slug}}"
    extension: md
    format: yaml-frontmatter
    fields:
      - { name: title, label: Title, widget: string, required: false }
      - { name: date, label: Date, widget: datetime }
      - { name: type, label: Type, widget: hidden, default: post }
      - { name: categories, label: Room, widget: select, required: false, multiple: true, options: [Building, Creative, Life] }
      - { name: body, label: Post, widget: markdown }
```

Deploy the GitHub auth Worker from `sveltia/sveltia-cms-auth` into Kay's Cloudflare account and point the CMS at it, following that project's README.

- [ ] **Step 6: Stand up Pages CMS**

Create `.pages.yml` at the repo root:

```yaml
media:
  input: static/uploads/2026
  output: /uploads/2026

content:
  - name: posts
    label: Posts
    type: collection
    path: content/2026
    filename: "{year}/{month}/{day}/{primary}.md"
    fields:
      - { name: title, label: Title, type: string, required: false }
      - { name: date, label: Date, type: date, options: { format: "yyyy-MM-dd'T'HH:mm:ssxxx" } }
      - { name: type, label: Type, type: string, default: post, hidden: true }
      - { name: categories, label: Room, type: select, list: true, options: { values: [Building, Creative, Life] } }
      - { name: body, label: Post, type: rich-text }
```

Kay authorises the repo at app.pagescms.org.

- [ ] **Step 7: Kay writes the same post in both**

Kay writes one real photo post with a caption, from his phone, in each editor. What to judge:

- How easy it is to place a photograph and give it a caption
- Whether the caption produces the Markdown title syntax the render hook needs
- How the editor behaves on a phone
- Whether publishing triggers a rebuild and appears on the preview

- [ ] **Step 8: Keep one, remove the other**

Delete the losing editor's config files. Verify the site still builds and deploys.

```bash
./scripts/verify-site.sh
git add -A
git commit -m "feat: keep <chosen editor> as the writing tool for nanakofiwrites.com"
```

- [ ] **Step 9: Update the spec's open questions**

Record the decision in `docs/superpowers/specs/2026-07-28-selfhost-migration-design.md` under Open Questions, and commit.

---

## Cutover (after Task 7, with Kay present)

Not a coding task. Do it in this exact order and stop at the first failure.

- [ ] Point nanakofiwrites.com at the Cloudflare Pages project.
- [ ] `curl -sS https://nanakofiwrites.com/feed.json | python3 -m json.tool | head -20` and confirm valid JSON Feed with `feed_url` reading `https://nanakofiwrites.com/feed.json`.
- [ ] Spot check three post URLs and three photographs directly.
- [ ] In Micro.blog, Account then Edit Feeds and Cross-posting, press the refresh control on the existing Source. Change no settings.
- [ ] Publish one real post. Watch it reach Bluesky and Mastodon.
- [ ] Only then consider deleting the Micro.blog-hosted blog. Leaving it indefinitely costs nothing and the $5 account is being kept regardless as the cross-post relay.

## Known follow-ups, deliberately not in this plan

- **No Open Graph tags.** `layouts/partials/head.html` emits none, and Task 3 drops the Micro.blog-generated `opengraph:` front matter. Links shared to social networks will render plainly. Worth a small follow-up task; not a migration blocker.
- **The 5 scaffolding pages** (`about`, `archive`, `photos`, `replies`, `stories`) are imported as-is in Task 3. `archive` and `photos` overlap the MINT year index and gallery, and `replies` has no content. Review with Kay once the site is visible.
- **The three April 2025 test posts** carry over by default. Kay decides whether to drop them once he can see the site.
- **Movement 2, Indiekit**, is a separate plan written after this one is live.
