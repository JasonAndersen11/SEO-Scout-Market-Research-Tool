#!/bin/bash
# Double-click this file to start RankRent AI.
# First run: sets up Python and installs what the app needs (a few minutes).
# After that: starts the app and opens it in your browser.
# To stop the app, close this window or press Ctrl+C.

cd "$(dirname "$0")" || exit 1
PORT=8000
URL="http://localhost:$PORT"

say_line() { printf '\n%s\n' "$1"; }
pause_exit() { printf '\nPress Return to close this window.'; read -r _; exit "${1:-1}"; }

echo "──────────────────────────────────────"
echo "  RankRent AI"
echo "──────────────────────────────────────"

# 1. Already running? Just open it.
if curl -s -o /dev/null "$URL/api/health"; then
  say_line "RankRent AI is already running — opening it in your browser."
  open "$URL"
  exit 0
fi

# 2. Find a Python the app supports (3.10 – 3.13).
PY=""
for cand in python3.12 python3.11 python3.13 python3.10 python3 \
            /opt/homebrew/bin/python3 /usr/local/bin/python3 \
            /Library/Frameworks/Python.framework/Versions/Current/bin/python3; do
  if command -v "$cand" >/dev/null 2>&1; then
    if "$cand" -c 'import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)' 2>/dev/null; then
      PY="$(command -v "$cand")"; break
    fi
  fi
done
if [ ! -x venv/bin/python ] && [ -z "$PY" ]; then
  say_line "This app needs Python 3.12 (3.10–3.13 also work), and I couldn't find it."
  echo "Opening the download page. Install it, then double-click this file again."
  open "https://www.python.org/downloads/release/python-3128/"
  pause_exit 1
fi

# 3. Create the app's Python environment the first time.
if [ ! -x venv/bin/python ]; then
  say_line "First-time setup: creating the app's Python environment…"
  "$PY" -m venv venv || { echo "Couldn't create the environment."; pause_exit 1; }
fi

# 4. Install or update packages when requirements.txt changes.
REQ_HASH="$(shasum requirements.txt | cut -d' ' -f1)"
if [ "$(cat venv/.req_hash 2>/dev/null)" != "$REQ_HASH" ]; then
  say_line "Installing what the app needs (only happens when something changed)…"
  venv/bin/python -m pip install --upgrade pip -q
  if venv/bin/python -m pip install -r requirements.txt; then
    echo "$REQ_HASH" > venv/.req_hash
  else
    say_line "Installing packages failed — see the messages above."
    pause_exit 1
  fi
fi

# 5. API keys.
if [ ! -f .env ]; then
  cp .env.example .env
fi
missing=""
for key in ANTHROPIC_API_KEY SEMRUSH_API_KEY SERPER_API_KEY; do
  val="$(grep -E "^$key=" .env | head -1 | cut -d= -f2- | tr -d '[:space:]\"'"'")"
  [ -z "$val" ] && missing="$missing $key"
done
if [ -n "$missing" ]; then
  say_line "Your API keys aren't filled in yet:$missing"
  echo "Opening the .env file in TextEdit. Paste each key after its = sign,"
  echo "save (Cmd+S), then double-click Start RankRent again."
  open -e .env
  pause_exit 1
fi

# 6. Start the app and open the browser once it's ready.
say_line "Starting RankRent AI at $URL"
echo "Keep this window open while you use the app. Close it (or press Ctrl+C) to stop."
(
  for _ in $(seq 1 60); do
    if curl -s -o /dev/null "$URL/api/health"; then open "$URL"; exit 0; fi
    sleep 1
  done
) &
exec venv/bin/python -m uvicorn main:app --port "$PORT"
