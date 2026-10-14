# Match results

Ratings are measured by playing [Stockfish](https://stockfishchess.org/) limited to a fixed
rating (its `UCI_Elo` option). Each of 20 common openings is played with both colours.
Run your own match with `tools/match.py`, or from GitHub's Actions tab ("match vs stockfish").

These are ratings on Stockfish's scale, not Lichess ratings. They are good for comparing
versions of this engine with each other. The Lichess bot will get its own public rating.

| Version | Opponent | Time control | Games | Result (W-D-L) | Score | Estimated rating (95% range) |
|---|---|---|---|---|---|---|
| Baseline: material only, alpha-beta, iterative deepening | Stockfish 17.1 at 1320 | 20s + 0.2s | 100 | 11-15-74 | 18.5% | **1062** (972–1130) |

Games: [`vs_stockfish_elo1320_20+0.2.pgn`](vs_stockfish_elo1320_20+0.2.pgn)

## Notes on the baseline

- 85 of 100 games ended in checkmate; the average game lasted 37 moves.
- Results were similar with white (5 wins, 10 draws) and black (6 wins, 5 draws).
- All 15 draws were by threefold repetition: with material as its only guide, the engine
  often has no reason to prefer one quiet move over another and shuffles back and forth.
- Stockfish found 277 blunders by the engine (moves that lose 3 pawns or more of value), about
  three per game. About three quarters were quiet moves rather than captures, and in over a
  third of them the opponent's best reply was simply to take something. The engine cannot
  see the tactics just past its search depth, and it stops searching in the middle of
  exchanges. That points to step 4: keep searching captures to the end of the exchange
  (quiescence search) and search deeper in the same time.
