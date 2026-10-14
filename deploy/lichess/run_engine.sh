#!/usr/bin/env bash
# Starts the engine in UCI mode. lichess-bot runs this file as the engine.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/../../Chess/uci.py"
