#!/usr/bin/env bash
# Starts the backend and a public HTTPS tunnel so teammates anywhere can use the API.
#   ./start.sh          -> backend + public URL
#   ./start.sh --local  -> backend only (http://localhost:8000)
set -e
cd "$(dirname "$0")"

if ! /opt/homebrew/opt/postgresql@16/bin/pg_isready -q 2>/dev/null; then
  echo "Starting PostgreSQL..."
  brew services start postgresql@16 >/dev/null
  sleep 2
fi

source .venv/bin/activate
python seed.py >/dev/null

uvicorn app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT

if [ "$1" == "--local" ]; then
  echo "Backend: http://localhost:8000  (docs: http://localhost:8000/docs)"
  wait $API_PID
else
  echo "Starting public tunnel... share the https://....trycloudflare.com URL printed below."
  echo "(The URL changes every time you restart. Press Ctrl+C to stop everything.)"
  cloudflared tunnel --no-autoupdate --url http://localhost:8000 2>&1 \
    | grep --line-buffered -oE "https://[a-z0-9-]+\.trycloudflare\.com" \
    | while read -r url; do
        echo
        echo "=================================================================="
        echo "  PUBLIC API URL : $url"
        echo "  API DOCS       : $url/docs"
        echo "=================================================================="
      done
fi
