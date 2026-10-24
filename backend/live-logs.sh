#!/usr/bin/env bash
# Streams the live backend activity from Render into this terminal (for demos and debugging).
#   ./live-logs.sh srv-xxxxxxxx     -> first run: pass your Render service ID (it is remembered)
#   ./live-logs.sh                  -> later runs
# One-time setup: brew install render && render login
# The service ID is in the Render dashboard URL: dashboard.render.com/web/srv-xxxxxxxx
set -e
cd "$(dirname "$0")"
ID_FILE=.render-service-id

if [ -n "$1" ]; then echo "$1" > "$ID_FILE"; fi
if [ ! -s "$ID_FILE" ]; then
  echo "Usage: ./live-logs.sh srv-xxxxxxxx   (your Render service ID, from the dashboard URL)"
  exit 1
fi

echo "Streaming live backend activity from Render. Press Ctrl+C to stop."
echo "Admin live page: https://canteen-backend-xzko.onrender.com/admin/live"
echo
render logs --resources "$(cat "$ID_FILE")" --tail --output text
