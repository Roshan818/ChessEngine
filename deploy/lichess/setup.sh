#!/usr/bin/env bash
# One-time setup on the machine that will host the bot (Linux or WSL).
# Downloads lichess-bot, installs it in a virtual environment and writes the config.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LICHESS_BOT_VERSION="f2b38b4f3ec4fc990001c05a4000fcf8adbb339d"  # pinned so updates never surprise us

cd "$DIR"
if [ ! -d lichess-bot ]; then
  git clone https://github.com/lichess-bot-devs/lichess-bot.git
fi
git -C lichess-bot fetch --quiet origin
git -C lichess-bot checkout --quiet "$LICHESS_BOT_VERSION"

python3 -m venv venv
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r lichess-bot/requirements.txt

sed "s|ENGINE_DIR|$DIR|" config.yml > lichess-bot/config.yml
echo "Setup done. Next: export LICHESS_BOT_TOKEN=... and run ./start.sh"
