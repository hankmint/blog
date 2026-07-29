#!/usr/bin/env bash
# Start the blog locally with the editor, no accounts and no internet needed.
#
#   ./scripts/edit.sh
#
# Opens two things:
#   http://localhost:1313/        the blog, live reloading as you write
#   http://localhost:1313/admin/  the editor
#
# In the editor click "Work with Local Repository" and choose this folder. It
# writes directly to the files here. It does NOT commit or push, so when you are
# happy, the changes still need committing.
#
# Requires a Chromium browser for the editor: Chrome, Edge, Arc or Brave.
# Safari and Firefox do not support the File System Access API it relies on.
set -euo pipefail

cd "$(dirname "$0")/.."
PORT="${PORT:-1313}"

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port $PORT is already in use. Stop whatever is on it, or run: PORT=1314 ./scripts/edit.sh" >&2
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN | tail -n +2 >&2
  exit 1
fi

echo "Starting the blog on http://localhost:$PORT"
hugo server --port "$PORT" --disableFastRender --quiet &
HUGO_PID=$!
trap 'kill $HUGO_PID 2>/dev/null || true' EXIT INT TERM

for _ in $(seq 1 30); do
  curl -sf -o /dev/null "http://localhost:$PORT/" && break
  sleep 0.4
done

echo
echo "  Blog    http://localhost:$PORT/"
echo "  Editor  http://localhost:$PORT/admin/"
echo
echo "In the editor, click 'Work with Local Repository' and pick this folder."
echo "Press Ctrl-C to stop."

# Prefer a Chromium browser, since the editor needs the File System Access API.
for app in "Google Chrome" "Arc" "Microsoft Edge" "Brave Browser"; do
  if [ -d "/Applications/$app.app" ]; then
    open -a "$app" "http://localhost:$PORT/admin/"
    break
  fi
done

wait $HUGO_PID
