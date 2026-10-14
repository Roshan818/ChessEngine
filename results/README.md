# Match results

Ratings are measured by playing [Stockfish](https://stockfishchess.org/) limited to a fixed
rating (its `UCI_Elo` option). Each of 20 common openings is played with both colours,
100 games per match, at 20 seconds plus 0.2 seconds per move.
Run your own match with `tools/match.py`, or from GitHub's Actions tab ("match vs stockfish").

These are ratings on Stockfish's scale, not Lichess ratings. They are good for comparing
versions of this engine with each other. The Lichess bot will get its own public rating.

| Version | What changed | Opponent | Result (W-D-L) | Score | Estimated rating (95% range) | Games |
|---|---|---|---|---|---|---|
| v1 | Baseline: material only, alpha-beta, iterative deepening | Stockfish 1320 | 11-15-74 | 18.5% | 1062 (972–1130) | [pgn](v1_baseline_vs_stockfish_elo1320_20+0.2.pgn) |
| v2 | + quiescence search, move ordering | Stockfish 1320 | 34-17-49 | 42.5% | 1267 (1202–1329) | [pgn](v2_quiescence_vs_stockfish_elo1320_20+0.2.pgn) |
| v3 | + transposition table | Stockfish 1320 | 34-17-49 | 42.5% | 1267 (1202–1329) | [pgn](v3_ttable_vs_stockfish_elo1320_20+0.2.pgn) |
| v4 | + piece-square tables | Stockfish 1320 | 80-7-13 | 83.5% | 1602 (1527–1708) | [pgn](v4_pst_vs_stockfish_elo1320_20+0.2.pgn) |
| v4 | (same version, stronger opponent) | Stockfish 1600 | 51-15-34 | 58.5% | **1660** (1597–1726) | [pgn](v4_pst_vs_stockfish_elo1600_20+0.2.pgn) |

**Current estimate: about 1650**, up from about 1060.

## What each change did

**v1, baseline.** Stockfish found 277 blunders by the engine (moves that lose 3 pawns or more
of value), about three per game. About three quarters were quiet moves rather than captures,
and in over a third of them the opponent's best reply was simply to take something. All 15
draws were by repetition: with only material to go on, the engine had no reason to prefer one
quiet move over another and shuffled back and forth.

**v2, quiescence search and move ordering (+205).** At the depth limit the engine now keeps
searching captures until the position is quiet, so it no longer evaluates positions halfway
through an exchange. Moves are searched best-first (captures of valuable pieces by cheap ones,
then moves that caused cutoffs elsewhere), which lets alpha-beta prune more.

**v3, transposition table (no measurable change).** The engine now remembers positions it has
already searched. The score was identical to v2 (different games, same result). At the depth this
engine reaches in a few seconds the table rarely pays off; it is kept because it helps more as
the search gets faster and deeper.

**v4, piece-square tables (+335 to +390).** Each piece gets a bonus or penalty for its square:
knights in the centre, rooks on the seventh rank, the king sheltered in the middlegame and
active in the endgame. Before this, after 1.e4 e5 2.Nf3 Nc6 the engine played 3.Ng1, undeveloping
its knight, because every quiet move looked equal to it. Now it plays 3.Nc3.
