# Running RoshanChess as a Lichess bot

The bot uses [lichess-bot](https://github.com/lichess-bot-devs/lichess-bot), the official
bridge between a UCI engine and Lichess. It accepts challenges from people and other bots,
and when idle it challenges other bots to rated games so it keeps building a rating.

## 1. Create the bot account (once, about 5 minutes)

1. Log out of your own Lichess account and **create a new account** for the bot,
   for example `RoshanChessBot`. A bot account must never have played a game, so don't
   play with it.
2. Logged in as the bot, open <https://lichess.org/account/oauth/token/create>, tick
   **"Play games with the bot API"** (`bot:play`), and create the token.
3. Copy the token somewhere safe. Treat it like a password: never commit it or paste it
   into chats or issues.

## 2. Set it up on the machine that will run it

Any always-on Linux machine works (a small cloud server, a Raspberry Pi, or WSL on Windows).
It needs Python 3.10+ and git.

```bash
git clone https://github.com/Roshan818/ChessEngine.git
cd ChessEngine/deploy/lichess
./setup.sh
echo 'LICHESS_BOT_TOKEN=paste_the_token_here' > token.env   # stays on this machine, ignored by git
chmod 600 token.env
./start.sh -u     # first time only: upgrades the account to a BOT account (cannot be undone)
```

After the first run, start it with `./start.sh`. To keep it running after you log out and
restart it automatically, install the systemd service in `roshanchess-bot.service`
(instructions are inside the file).

## 3. Settings worth knowing (`config.yml`)

| Setting | Value | Why |
|---|---|---|
| Time controls | 3 minutes and longer | A Python engine is too slow for bullet |
| Games at once | 1 | Each game uses one CPU core at full speed |
| Matchmaking | on, rated 3+2 / 5+3 vs bots within 300 points | Keeps the rating moving without you doing anything |
| Outside help | none (no opening books, tablebases or cloud analysis) | Every move is the engine's own |
| Game records | saved to `lichess-bot/game_records/` | Training data for later |

Lichess allows a bot at most 100 games a day against other bots; the matchmaking settings keep
it well under that.

## Updating the bot

```bash
cd ChessEngine && git pull && sudo systemctl restart roshanchess-bot
```
