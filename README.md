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

## What's next

1. **Measure it.** Play matches against Stockfish set to fixed ratings to get an honest rating.
2. **Make it stronger.** Each change is measured before it is kept:
   keep searching captures past the depth limit (quiescence search), try the most promising
   moves first, remember positions already searched, and teach the evaluation about piece
   placement, king safety and pawn structure.
3. **Deploy it.** A version you can play in the browser, and a Lichess bot account.
4. **Let it learn.** The evaluation sits behind one small interface
   ([`Chess/evaluation.py`](Chess/evaluation.py)), so a learned evaluation can replace the
   hand-written one. Once the bot is live, its games and self-play can be used to train it.

## Play it

```bash
pip install -r requirements.txt
python Chess/ChessMain.py                # you play white
python Chess/ChessMain.py --human black  # you play black
python Chess/ChessMain.py --think 5      # give the engine 5 seconds per move
```

Click a piece, then its destination. Press `z` to undo and `r` to restart.

To use it in any UCI chess GUI (for example [Cute Chess](https://cutechess.com/) or
[Arena](http://www.playwitharena.de/)), add an engine with the command `python Chess/uci.py`.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```
