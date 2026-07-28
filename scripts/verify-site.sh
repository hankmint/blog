#!/usr/bin/env bash
# The test harness for the self-hosted site. Builds, then asserts invariants.
# Every assertion here corresponds to a success criterion in
# docs/superpowers/specs/2026-07-28-selfhost-migration-design.md
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

# --- Content and images ---
POSTS=$(find content -path 'content/20*' -name '*.md' | wc -l | tr -d ' ')
[ "$POSTS" = "18" ]; check $? "18 posts present in content/ (found $POSTS)"

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
[ "$IMGCOUNT" = "28" ]; check $? "28 photographs present in static/uploads (found $IMGCOUNT)"

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

echo
echo "Results:"
if [ "$FAILED" -eq 0 ]; then echo "ALL ASSERTIONS PASSED"; else echo "THERE WERE FAILURES" >&2; fi
exit "$FAILED"
