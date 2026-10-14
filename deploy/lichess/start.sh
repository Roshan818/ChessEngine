#!/usr/bin/env bash
# Starts the bot. Needs the LICHESS_BOT_TOKEN environment variable.
# Pass -u the first time to upgrade the account to a BOT account.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "${LICHESS_BOT_TOKEN:-}" ] && [ -f "$DIR/token.env" ]; then
  # shellcheck disable=SC1091
  source "$DIR/token.env"
  export LICHESS_BOT_TOKEN
fi
: "${LICHESS_BOT_TOKEN:?Set LICHESS_BOT_TOKEN (or create token.env) first}"
cd "$DIR/lichess-bot"
exec "$DIR/venv/bin/python" lichess-bot.py "$@"
