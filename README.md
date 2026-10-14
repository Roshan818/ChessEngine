# Chess Engine

A chess engine written from scratch in Python, with a Pygame board to play against it.

- **Move generation:** full rules, including castling, en passant, all four promotions,
  checks and pins, plus draws by threefold repetition, the 50-move rule and insufficient material.
- **Search:** Negamax with alpha-beta pruning.
- **Correctness:** tested with standard perft positions and checked move-for-move against
  [python-chess](https://python-chess.readthedocs.io/) on hundreds of thousands of random positions.

## Play

```bash
pip install -r requirements.txt
python Chess/ChessMain.py               # you play white
python Chess/ChessMain.py --human black # you play black
```

Click a piece, then its destination. Press `z` to undo a move and `r` to restart.

## Test

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```
