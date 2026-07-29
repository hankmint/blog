#!/usr/bin/env bash
# The test harness for the self-hosted site. Builds, then asserts invariants.
# Every assertion here corresponds to a success criterion in
# docs/superpowers/specs/2026-07-28-selfhost-migration-design.md
set -uo pipefail

FAILED=0
pass() { echo "  PASS  $1"; }
fail() { echo "  FAIL  $1" >&2; FAILED=1; }
check() { if [ "$1" = "0" ]; then pass "$2"; else fail "$2"; fi }

# A running `hugo server` writes its own output over public/, built with
# baseURL rewritten to localhost. Checking that build would report a feed full
# of localhost URLs, or worse, pass while the real production build is broken.
if pgrep -f "hugo server" >/dev/null 2>&1; then
  echo "REFUSING TO RUN: a 'hugo server' is running and will contaminate public/." >&2
  echo "Stop it first (Ctrl-C, or: pkill -f 'hugo server'), then run this again." >&2
  exit 2
fi

echo "Building..."
# --cleanDestinationDir matters. Hugo leaves files behind for content that no
# longer exists, so a deleted post keeps its page in public/ and gets deployed.
if hugo --quiet --cleanDestinationDir --destination public; then
  pass "hugo build exits 0"
else
  fail "hugo build exits 0"
  echo "Build failed, cannot run further assertions." >&2
  exit 1
fi

# --- Content and images ---
# Counted, not hard-coded, so publishing a post does not fail the harness. The
# 18 imported from Micro.blog are the floor: none of them may ever go missing.
POSTS=$(find content -path 'content/20*' -name '*.md' | wc -l | tr -d ' ')
[ "$POSTS" -ge 18 ]; check $? "all posts present in content/ ($POSTS, floor is the 18 imported)"

# No generated page may reference Micro.blog's servers. This is what keeps the
# site independent: rescuing the files is not enough if the HTML still asks
# their CDN for them.
LEAKS=$(grep -rlE 'cdn\.uploads\.micro\.blog|s3\.amazonaws\.com/micro\.blog' public --include='*.html' --include='*.json' --include='*.xml' 2>/dev/null | wc -l | tr -d ' ')
[ "$LEAKS" = "0" ]; check $? "no Micro.blog CDN references in generated output (found $LEAKS files)"

# Every image the built HTML asks for must exist on disk.
#
# This resolves each src RELATIVE TO THE PAGE IT APPEARS ON, which is the only
# way to catch the relative-path trap: Micro.blog stored bodies as
# <img src="uploads/2025/x.jpg"> and rewrote that to an absolute CDN URL at
# render time. Hugo does not. On a page at /2025/12/21/ the browser resolves
# that to /2025/12/21/uploads/2025/x.jpg, which does not exist. An assertion
# that only looks for src="/uploads/..." finds nothing and passes vacuously.
python3 - <<'PY'
import pathlib, re, sys, urllib.parse
pub = pathlib.Path("public")
missing, checked = [], 0
for page in pub.rglob("*.html"):
    for src in re.findall(r'<img[^>]+src="([^"]*)"', page.read_text(encoding="utf-8", errors="ignore")):
        if not src or src.startswith(("http://", "https://", "data:", "//")):
            continue
        checked += 1
        src = urllib.parse.unquote(src.split("?")[0].split("#")[0])
        target = pub / src.lstrip("/") if src.startswith("/") else page.parent / src
        if not target.is_file():
            missing.append(f"{page.relative_to(pub)} asks for {src}")
for m in missing[:10]:
    print("    missing:", m, file=sys.stderr)
if len(missing) > 10:
    print(f"    ... and {len(missing)-10} more", file=sys.stderr)
print(f"    checked {checked} local img references", file=sys.stderr)
sys.exit(1 if missing else 0)
PY
check $? "every image reference resolves, relative to its own page"

IMGCOUNT=$(find static/uploads -type f | wc -l | tr -d ' ')
[ "$IMGCOUNT" -ge 28 ]; check $? "the 28 rescued photographs are all still present (found $IMGCOUNT)"

# Permalinks must not change. Every url: in front matter must exist as a
# generated page at exactly that path. Those URLs are already live and already
# sitting in the Micro.blog timeline.
BADURL=0
for u in $(grep -rhoE '^url: "[^"]+"' content | sed 's|^url: "||; s|"$||' | sort -u); do
  case "$u" in
    */) target="public${u}index.html" ;;
    *)  target="public${u}" ;;
  esac
  [ -f "$target" ] || { echo "    permalink missing: $u" >&2; BADURL=$((BADURL+1)); }
done
[ "$BADURL" = "0" ]; check $? "every declared permalink resolves ($BADURL missing)"

# A blob: URL is a temporary in-browser reference that dies with the tab. The
# editor can save one if an image is still uploading when the post is saved,
# which looks fine in the editor and is a permanently broken image on the site.
BLOBS=$(grep -rlE 'blob:https?:' content 2>/dev/null | wc -l | tr -d ' ')
[ "$BLOBS" = "0" ]; check $? "no blob: image references left in content (found $BLOBS files)"
if [ "$BLOBS" != "0" ]; then grep -rlE 'blob:https?:' content | sed 's/^/     /' >&2; fi

# Images saved beside a post only publish if the post is index.md inside that
# folder. A sibling folder next to slug.md is silently ignored by Hugo.
python3 - <<'PY' 2>&1
import pathlib, sys
bad = []
for md in pathlib.Path("content").rglob("*.md"):
    if md.name == "index.md":
        continue
    twin = md.with_suffix("")
    if twin.is_dir() and any(twin.iterdir()):
        bad.append(f"{md} has a sibling folder {twin.name}/ that Hugo will ignore")
for b in bad:
    print("    ", b, file=sys.stderr)
sys.exit(1 if bad else 0)
PY
check $? "no post has an orphaned sibling asset folder"

# A <figure> inside a <p> is invalid HTML that browsers tear apart, leaving a
# stray empty paragraph after the photograph. It happens whenever an image is
# written directly after text instead of on its own line. Checked across the
# whole site, not just the caption test post, because that is where it appeared.
NESTEDFIG=$(grep -rloE '<p>[^<]*<figure' public --include='*.html' 2>/dev/null | wc -l | tr -d ' ')
[ "$NESTEDFIG" = "0" ]; check $? "no <figure> is nested inside a <p> ($NESTEDFIG pages)"
if [ "$NESTEDFIG" != "0" ]; then grep -rloE '<p>[^<]*<figure' public --include='*.html' | sed 's/^/     /' >&2; fi

# No Go value should ever leak into the rendered page. This catches a map or a
# slice printed directly by a template, which reads as "map[name:Nana Kofi]" or
# "[a b c]" on the live site and is easy to miss in a quick look.
GOLEAK=$(grep -rlE 'map\[[a-zA-Z]+:' public --include='*.html' 2>/dev/null | wc -l | tr -d ' ')
[ "$GOLEAK" = "0" ]; check $? "no raw Go values rendered into the HTML (found $GOLEAK files)"

# On-site navigation must not be absolute. Absolute hrefs are built from
# baseURL, so on a Cloudflare preview deployment every link would jump back to
# the production domain and the preview would be untestable. Feeds and
# canonical URLs are the exception and stay absolute on purpose.
python3 - <<'PY' 2>&1
import pathlib, re, sys
bad = []
for page in pathlib.Path("public").rglob("*.html"):
    text = page.read_text(encoding="utf-8", errors="ignore")
    for href in re.findall(r'href="(https?://[^"]+)"', text):
        if "nanakofiwrites.com" in href:
            bad.append(f"{page.relative_to('public')} links absolutely to {href}")
for b in bad[:6]:
    print("    ", b, file=sys.stderr)
if len(bad) > 6:
    print(f"    ... and {len(bad)-6} more", file=sys.stderr)
sys.exit(1 if bad else 0)
PY
check $? "on-site links are relative, so preview deployments are testable"

# --- Feeds ---
#
# SAFETY CRITICAL and silent when it breaks. /feed.json is registered on the
# Micro.blog Sources page and drives cross-posting to twelve networks. If it
# 404s or is malformed, nothing errors anywhere: posts just stop arriving.
[ -f public/feed.json ]; check $? "public/feed.json exists"
[ -f public/feed.xml ];  check $? "public/feed.xml exists"

if [ -f public/feed.json ]; then
  python3 - <<'PY' 2>&1
import json, sys
try:
    d = json.load(open("public/feed.json"))
except Exception as e:
    print("    invalid JSON:", e, file=sys.stderr); sys.exit(1)
problems = []
if not str(d.get("version", "")).startswith("https://jsonfeed.org/version/"):
    problems.append("missing or wrong jsonfeed version")
if not str(d.get("feed_url", "")).endswith("/feed.json"):
    problems.append(f"feed_url must end in /feed.json, got {d.get('feed_url')!r}")
items = d.get("items", [])
if len(items) < 18:
    problems.append(f"expected at least the 18 imported posts, got {len(items)}")
for i, it in enumerate(items):
    for key in ("id", "url", "date_published", "content_html"):
        if not it.get(key):
            problems.append(f"item {i} missing {key}")
    if "micro.blog" in str(it.get("url", "")):
        problems.append(f"item {i} url still points at micro.blog")
for p in problems[:8]:
    print("    ", p, file=sys.stderr)
sys.exit(1 if problems else 0)
PY
  check $? "feed.json is a valid JSON Feed with every post in it"
fi

if [ -f public/feed.xml ]; then
  # Existence is not validity. Hugo HTML-escapes a literal <?xml declaration
  # unless it is passed through safeHTML, which produced a feed.xml that looked
  # perfectly fine in a text editor and would not parse in any reader.
  python3 - <<'PY' 2>&1
import sys, xml.dom.minidom
try:
    x = xml.dom.minidom.parse("public/feed.xml")
except Exception as e:
    print("    feed.xml does not parse:", e, file=sys.stderr); sys.exit(1)
items = x.getElementsByTagName("item")
if len(items) < 18:
    print(f"    expected at least the 18 imported posts, got {len(items)}", file=sys.stderr); sys.exit(1)
PY
  check $? "feed.xml is well-formed RSS with every post in it"
fi

# --- The site must show its own content ---
#
# Every one of the 18 posts is an untitled micro post, and the homepage index
# filtered to titled posts only. Shipped unchanged it would have read "0 essays"
# on launch day.
ENTRIES=$(grep -c 'class="mint-entry' public/index.html || true)
[ "${ENTRIES:-0}" -ge 16 ]; check $? "homepage index lists the posts (found ${ENTRIES:-0} entries)"

if grep -qE '>0 (essays|posts)<' public/index.html; then fail "homepage reports zero posts"; else pass "homepage does not report zero posts"; fi

# The gallery only renders for a page with type: gallery. Nothing declared it,
# so the gallery and its lightbox did not exist at all.
[ -f public/photos/index.html ]; check $? "the gallery page is generated at /photos/"
if [ -f public/photos/index.html ]; then
  # Count photographs, not tiles. The gallery shows one tile per post, so a post
  # with several photographs is a single carousel tile holding all of them.
  SHOTS=$(grep -o 'data-full="' public/photos/index.html | wc -l | tr -d ' ')
  [ "${SHOTS:-0}" -ge 28 ]; check $? "the gallery shows every photograph (found ${SHOTS:-0})"
  TILES=$(grep -o 'class="mint-shot' public/photos/index.html | wc -l | tr -d ' ')
  [ "${TILES:-0}" -lt "${SHOTS:-0}" ]; check $? "the gallery groups photographs into posts ($TILES tiles for $SHOTS photographs)"
  if grep -q 'mint-gallery-empty' public/photos/index.html; then fail "the gallery says it is empty"; else pass "the gallery is not empty"; fi
fi

# No nav link may lead to a page with nothing on it.
python3 - <<'PY' 2>&1
import pathlib, re, sys
home = pathlib.Path("public/index.html").read_text(encoding="utf-8")
nav = re.search(r'<nav class="nav".*?</nav>', home, re.DOTALL)
if not nav:
    print("    no nav found", file=sys.stderr); sys.exit(1)
links = sorted(set(re.findall(r'href="(/[^"]*)"', nav.group(0))))
bad = []
for href in links:
    page = pathlib.Path("public" + href.rstrip("/") + "/index.html")
    if href == "/":
        continue
    if not page.is_file():
        bad.append(f"{href} has no generated page"); continue
    body = re.search(r"<main.*?</main>", page.read_text(encoding="utf-8"), re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", body.group(0) if body else "")
    if len(text.split()) < 12:
        bad.append(f"{href} renders almost nothing ({len(text.split())} words)")
print("    nav links:", ", ".join(links) or "(none)", file=sys.stderr)
for b in bad:
    print("    ", b, file=sys.stderr)
sys.exit(1 if bad else 0)
PY
check $? "every nav link leads to a page with content on it"

# --- Captioned images ---
#
# static/css/mint.css has styled figure and figcaption since the theme was built,
# but the theme had no render hook and no shortcode, so nothing ever emitted a
# <figure> and the styling was unreachable.
#
# The test post is created here, built into a throwaway directory, and removed,
# so the behaviour is always tested and a test post never appears on the live
# blog or in the feeds.
CAPDIR=$(mktemp -d)
CAPPOST="content/2026/07/28/zz-caption-check.md"
mkdir -p "$(dirname "$CAPPOST")"
cat > "$CAPPOST" <<'EOF'
---
date: 2026-07-28T12:00:00-04:00
type: post
title: "Caption check"
url: "/zz-caption-check.html"
---
![Nani in the snow](/uploads/2026/548458a206d94b7f827547b2a14d35bb.jpg "Nani, the morning after the storm")

![Just the picture](/uploads/2025/1-2.png)
EOF
hugo --quiet --destination "$CAPDIR" >/dev/null 2>&1
CAPOUT="$CAPDIR/zz-caption-check.html"
if [ -f "$CAPOUT" ]; then
  python3 - "$CAPOUT" <<'PY' 2>&1
import pathlib, re, sys
h = pathlib.Path(sys.argv[1]).read_text()
problems = []
figs = re.findall(r"<figure.*?</figure>", h, re.DOTALL)
if len(figs) != 1:
    problems.append(f"expected exactly 1 figure, got {len(figs)}")
elif "Nani, the morning after the storm" not in figs[0]:
    problems.append("the caption text is not inside the figure")
elif "<figcaption" not in figs[0]:
    problems.append("the caption is not in a figcaption")
elif "1-2.png" in figs[0]:
    problems.append("the uncaptioned image was wrapped in a figure")
if re.search(r"<figcaption>\s*</figcaption>", h):
    problems.append("an empty figcaption was rendered")
if re.search(r"<p>\s*<figure", h):
    problems.append("a <figure> was wrapped in a <p>, which is invalid HTML")
for p in problems:
    print("    ", p, file=sys.stderr)
sys.exit(1 if problems else 0)
PY
  check $? "a markdown image with a title renders as a captioned <figure>, one without stays a plain img"
else
  fail "the caption check post did not build"
fi
rm -f "$CAPPOST"
rmdir -p "$(dirname "$CAPPOST")" 2>/dev/null || true
rm -rf "$CAPDIR"

echo
echo "Results:"
if [ "$FAILED" -eq 0 ]; then echo "ALL ASSERTIONS PASSED"; else echo "THERE WERE FAILURES" >&2; fi
exit "$FAILED"
