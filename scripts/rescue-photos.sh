#!/usr/bin/env bash
# Downloads every photograph referenced by the Micro.blog export into static/uploads/.
#
# The "theme and Markdown" export contains NO image files. Every photograph on
# nanakofiwrites.com exists only on Micro.blog's CDN. If the hosted blog is
# deleted before this runs, they are gone permanently.
#
# Idempotent: files already present and non-empty are skipped.
set -euo pipefail

EXPORT="${EXPORT:-/private/tmp/claude-501/-Users-mint/e7f4cbdf-04e6-46a3-a32c-85c3878e2105/scratchpad/mbexport}"
CDN_BASE="https://cdn.uploads.micro.blog/217795"
DEST="static/uploads"
LIST="${LIST:-/tmp/photo-list.txt}"

if [ ! -d "$EXPORT/content" ]; then
  echo "FAIL: export content not found at $EXPORT" >&2
  echo "Unzip ~/Downloads/themint_e83356.zip and set EXPORT to that directory." >&2
  exit 1
fi

# Collect relative paths like "2025/abc123.jpg" from two places:
#   1. body <img src="uploads/2025/abc123.jpg">
#   2. front matter absolute CDN URLs (images:, photos:, photos_with_metadata:)
{
  grep -rhoE '<img[^>]+src="uploads/[^"]+"' "$EXPORT/content" \
    | sed -E 's|.*src="uploads/||; s|"$||'
  grep -rhoE "https://cdn\.uploads\.micro\.blog/217795/[^ \"')]+" "$EXPORT/content" \
    | sed -E "s|https://cdn\.uploads\.micro\.blog/217795/||"
} | sed 's|[[:space:]]*$||' | sort -u > "$LIST"

total=$(grep -c . "$LIST" || true)
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
done < "$LIST"

echo "downloaded=$ok skipped=$skip failed=$fail"
[ "$fail" -eq 0 ] || { echo "FAIL: $fail photographs could not be rescued" >&2; exit 1; }
