#!/bin/bash
# Paste this whole file into Oracle Cloud's "Initialization script" (cloud-init) box when
# creating the server. On first boot it installs the engine and lichess-bot and starts the bot.
# Works on Ubuntu (22.04 or 24.04). Progress is logged to /var/log/roshanchess-setup.log.

# >>> Put the bot account's token between the quotes before pasting. <<<
LICHESS_BOT_TOKEN="PASTE_TOKEN_HERE"

exec > /var/log/roshanchess-setup.log 2>&1
set -euxo pipefail

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y git python3-venv python3-pip

id chessbot || useradd --create-home --shell /bin/bash chessbot
HOME_DIR=/home/chessbot
REPO=$HOME_DIR/ChessEngine
if [ ! -d "$REPO" ]; then
  sudo -u chessbot git clone https://github.com/Roshan818/ChessEngine.git "$REPO"
fi
cd "$REPO/deploy/lichess"
sudo -u chessbot ./setup.sh

# Token stays on this server only, readable by the bot user alone
echo "LICHESS_BOT_TOKEN=$LICHESS_BOT_TOKEN" > token.env
chown chessbot:chessbot token.env
chmod 600 token.env

# Upgrade the account to a BOT account (only works on an account that has never played)
sudo -u chessbot timeout 60 ./start.sh -u || true

# Run the bot as a service that starts on boot and restarts if it stops
sed -e "s|User=USER|User=chessbot|" -e "s|/home/USER/ChessEngine|$REPO|g" \
  roshanchess-bot.service > /etc/systemd/system/roshanchess-bot.service
systemctl daemon-reload
systemctl enable --now roshanchess-bot
echo "RoshanChess bot setup finished"
