# Chess Engine

A chess engine I wrote from scratch in Python: the rules, the board, the search and the
graphical board you play on. No chess libraries are used in the engine itself.

## How it started (2023)

I built the first version in August 2023 as a personal project, with
[Pygame](https://www.pygame.org/) for the board. The goal was to understand how classical
chess engines think, so everything was hand-written:

- **The board** is an 8×8 grid. Each square holds a two-letter code: colour, then piece
  (`wK` is the white king, `bp` a black pawn, `--` an empty square).
- **Move generation** walks the board, generates moves piece by piece, and tracks pins and
  checks so that only legal moves are produced. It handles castling, en passant and promotion.
- **The AI** went through several versions, each kept in [`Chess/ChessAI.py`](Chess/ChessAI.py):
  1. **Random moves:** a baseline that just picks any legal move.
  2. **Greedy, two plies:** take the move that leaves the opponent with the worst best reply,
     counting material only.
  3. **Minimax:** look several moves ahead, assuming both sides play their best.
     White maximises the score, black minimises it.
  4. **Negamax:** the same idea written as one function, using the fact that a position's value
     for one side is the negative of its value for the other.
  5. **Alpha-beta pruning:** skip branches that cannot change the final decision. Same answer
     as minimax, far fewer positions searched, so it can look deeper in the same time.

The evaluation was simple: add up the material (pawn 1, knight and bishop 3, rook 5, queen 9)
and search four moves deep.

## Revisiting it (2026)

Coming back to the project, I set out to deploy it (a playable web version and a
[Lichess](https://lichess.org/) bot) and to make it stronger. Before changing anything, I
tested the rules properly.

**Testing the rules.** I checked the engine against two references: published *perft* counts
(the exact number of positions reachable from a test position at each depth) and the
[python-chess](https://python-chess.readthedocs.io/) library, move for move, over thousands of
random games. That turned up several real bugs, mostly in rare situations: castling rights
being lost or corrupted, a pinned pawn not allowed to move along its pin, en passant captures
that exposed the king along the rank, and en passant not counting as a way out of check. I also
added the missing rules: promotion to any piece, and draws by repetition, the 50-move rule and
insufficient material. The engine now agrees with python-chess on every one of more than half a
million positions tested, and these checks run automatically on every change.

**Speaking UCI.** UCI is the standard protocol chess programs use to talk to each other. With
it, the engine can play matches against Stockfish to measure its real strength, and it can be
connected to Lichess as a bot. To play under a clock, the search now uses **iterative
deepening**: it searches 1 move deep, then 2, then 3, and so on, and when time runs out it plays
the best move from the last completed depth.

**Measuring it.** To get an honest rating, the engine played 100 games against Stockfish
limited to a rating of 1320, across 20 common openings with both colours. It scored 18.5%,
which puts it at about **1060** on Stockfish's scale. Stockfish's analysis of those games
showed the main weakness: about three big blunders per game, mostly tactics just past the
search depth.

**Making it stronger.** Each change was kept only after a 100-game match showed its effect:

| Change | Score vs Stockfish 1320 | Rating |
|---|---|---|
| Starting point | 18.5% | ~1060 |
| **Quiescence search**: at the depth limit, keep searching captures until the position is quiet, instead of judging it halfway through an exchange. **Move ordering**: search the most promising moves first, so alpha-beta can skip more. | 42.5% | ~1270 |
| **Transposition table**: remember positions already searched. No measurable gain at this depth, kept for later. | 42.5% | ~1270 |
| **Piece-square tables**: reward good squares (central knights, rooks on the seventh, a sheltered king in the middlegame and an active one in the endgame). | 83.5% | ~1600 |

Against Stockfish set to 1600, the latest version scored 58.5%, which puts it at about
**1650**. Details and every game are in [`results/`](results/).

## What's next

1. **Make it faster.** The engine searches about 7,000 positions a second, so in a few seconds
   it only looks 3 to 4 moves ahead. A faster board representation means deeper search.
2. **Deploy it.** A version you can play in the browser, and a Lichess bot account.
3. **Let it learn.** The evaluation sits behind one small interface
   ([`Chess/evaluation.py`](Chess/evaluation.py)), so a learned evaluation can replace the
   hand-written one. Once the bot is live, its games and self-play can be used to train it,
   and every new version can be measured the same way against Stockfish.

## Play it

```bash
pip install -r requirements.txt
python Chess/ChessMain.py                # you play white
python Chess/ChessMain.py --human black  # you play black
python Chess/ChessMain.py --think 5      # give the engine 5 seconds per move
```

Click a piece, then its destination. Press `z` to undo and `r` to restart.

To run it as a Lichess bot, see [`deploy/lichess/`](deploy/lichess/).

To use it in any UCI chess GUI (for example [Cute Chess](https://cutechess.com/) or
[Arena](http://www.playwitharena.de/)), add an engine with the command `python Chess/uci.py`.

## Measure it yourself

```bash
pip install chess
python tools/match.py --stockfish /path/to/stockfish --elo 1320 --games 100
```

Or run it on GitHub: **Actions → match vs stockfish → Run workflow**.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```
