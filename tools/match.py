"""
Play a match between this engine and Stockfish (or any UCI engine) and
estimate this engine's rating.

Stockfish can be limited to a target rating with UCI_Elo (1320 and up), which
gives a fixed, known opponent to measure against. Each opening is played
twice, once with each colour, so neither side gets an easier set of games.

Example:
    python tools/match.py --stockfish /path/to/stockfish --elo 1320 --games 40 --tc 20+0.2

Writes every game to a PGN file and prints the score and estimated rating.
"""
import argparse
import concurrent.futures
import datetime
import math
import os
import sys
import time

import chess
import chess.engine
import chess.pgn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUR_ENGINE = [sys.executable, os.path.join(ROOT, "Chess", "uci.py")]

# Common, roughly balanced openings (UCI moves). Each is played with both colours.
OPENINGS = [
    "e2e4 e7e5 g1f3 b8c6",            # Open game
    "e2e4 c7c5 g1f3 d7d6",            # Sicilian
    "e2e4 e7e6 d2d4 d7d5",            # French
    "e2e4 c7c6 d2d4 d7d5",            # Caro-Kann
    "d2d4 d7d5 c2c4 e7e6",            # Queen's Gambit Declined
    "d2d4 g8f6 c2c4 g7g6",            # King's Indian
    "d2d4 d7d5 c2c4 c7c6",            # Slav
    "c2c4 e7e5 b1c3 g8f6",            # English
    "g1f3 d7d5 g2g3 g8f6",            # Reti
    "e2e4 d7d5 e4d5 d8d5",            # Scandinavian
    "d2d4 g8f6 c2c4 e7e6 g1f3 b7b6",  # Queen's Indian
    "e2e4 e7e5 g1f3 g8f6",            # Petrov
    "e2e4 g7g6 d2d4 f8g7",            # Modern
    "d2d4 f7f5 g2g3 g8f6",            # Dutch
    "e2e4 c7c5 b1c3 b8c6",            # Closed Sicilian
    "d2d4 d7d5 c1f4 g8f6",            # London
    "e2e4 d7d6 d2d4 g8f6",            # Pirc
    "c2c4 c7c5 g1f3 g8f6",            # Symmetrical English
    "e2e4 e7e5 f1c4 g8f6",            # Bishop's Opening
    "d2d4 g8f6 g1f3 e7e6 c1g5",       # Torre
]

MAX_PLIES = 400  # adjudicate as a draw after this many half-moves


def parse_tc(text):
    base, _, inc = text.partition("+")
    return float(base), float(inc or 0)


def play_game(opening, our_colour, args, game_number):
    base, inc = parse_tc(args.tc)
    ours = chess.engine.SimpleEngine.popen_uci(OUR_ENGINE)
    theirs = chess.engine.SimpleEngine.popen_uci(args.stockfish)
    try:
        options = {"Threads": 1, "Hash": 16}
        if args.elo:
            options.update({"UCI_LimitStrength": True, "UCI_Elo": args.elo})
        if args.skill is not None:
            options["Skill Level"] = args.skill
        theirs.configure(options)

        board = chess.Board()
        for uci in opening.split():
            board.push_uci(uci)
        clocks = {chess.WHITE: base, chess.BLACK: base}
        engines = {our_colour: ours, not our_colour: theirs}
        result, reason = None, None

        while result is None:
            if board.is_game_over(claim_draw=True):
                outcome = board.outcome(claim_draw=True)
                result, reason = outcome.result(), outcome.termination.name.lower()
                break
            if board.ply() >= MAX_PLIES:
                result, reason = "1/2-1/2", "move limit"
                break
            side = board.turn
            limit = chess.engine.Limit(white_clock=clocks[chess.WHITE], black_clock=clocks[chess.BLACK],
                                       white_inc=inc, black_inc=inc)
            start = time.time()
            try:
                move = engines[side].play(board, limit).move
            except chess.engine.EngineError as error:
                result = "0-1" if side == chess.WHITE else "1-0"
                reason = "engine error: %s" % error
                break
            clocks[side] -= time.time() - start
            if clocks[side] < 0:
                result = "0-1" if side == chess.WHITE else "1-0"
                reason = "time forfeit"
                break
            clocks[side] += inc
            if move is None or move not in board.legal_moves:
                result = "0-1" if side == chess.WHITE else "1-0"
                reason = "illegal move %s" % move
                break
            board.push(move)
    finally:
        ours.quit()
        theirs.quit()

    game = chess.pgn.Game.from_board(board)
    opponent = "Stockfish" + (" %d" % args.elo if args.elo else "") + \
        (" skill %d" % args.skill if args.skill is not None else "")
    game.headers.update({
        "Event": "RoshanChess vs %s" % opponent,
        "Date": datetime.date.today().strftime("%Y.%m.%d"),
        "Round": str(game_number),
        "White": "RoshanChess" if our_colour == chess.WHITE else opponent,
        "Black": opponent if our_colour == chess.WHITE else "RoshanChess",
        "Result": result,
        "TimeControl": "%g+%g" % (base, inc),
        "Termination": reason,
    })
    our_score = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}[result]
    if our_colour == chess.BLACK:
        our_score = 1.0 - our_score
    return game, our_score, reason


def elo_estimate(scores, opponent_elo):
    """Rating estimate and 95% interval from a list of per-game scores (1, 0.5, 0)."""
    n = len(scores)
    mean = sum(scores) / n
    variance = sum((s - mean) ** 2 for s in scores) / n
    margin = 1.96 * math.sqrt(variance / n)

    def to_elo(score):
        score = min(max(score, 0.5 / n), 1 - 0.5 / n)  # avoid infinite values at 0% or 100%
        return opponent_elo - 400 * math.log10(1 / score - 1)

    return to_elo(mean), to_elo(mean - margin), to_elo(mean + margin)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stockfish", default=os.environ.get("STOCKFISH", "stockfish"), help="path to Stockfish")
    parser.add_argument("--elo", type=int, help="limit Stockfish to this rating (1320 or more)")
    parser.add_argument("--skill", type=int, help="Stockfish 'Skill Level' 0-20 instead of a rating (not calibrated)")
    parser.add_argument("--games", type=int, default=40, help="number of games (even; default 40)")
    parser.add_argument("--tc", default="20+0.2", help="time control in seconds, base+increment (default 20+0.2)")
    parser.add_argument("--concurrency", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    parser.add_argument("--pgn", help="where to write the games (default results/<name>.pgn)")
    args = parser.parse_args()

    jobs = []
    for i in range(args.games):
        opening = OPENINGS[(i // 2) % len(OPENINGS)]
        colour = chess.WHITE if i % 2 == 0 else chess.BLACK
        jobs.append((opening, colour, i + 1))

    label = "elo%d" % args.elo if args.elo else "skill%d" % (args.skill or 0)
    pgn_path = args.pgn or os.path.join(ROOT, "results", "vs_stockfish_%s_%s.pgn" % (label, args.tc))
    os.makedirs(os.path.dirname(pgn_path), exist_ok=True)

    scores, reasons = [], {}
    with open(pgn_path, "w") as pgn, concurrent.futures.ThreadPoolExecutor(args.concurrency) as pool:
        futures = [pool.submit(play_game, o, c, args, n) for o, c, n in jobs]
        for future in concurrent.futures.as_completed(futures):
            game, score, reason = future.result()
            scores.append(score)
            reasons[reason] = reasons.get(reason, 0) + 1
            print(game, file=pgn, end="\n\n")
            pgn.flush()
            print("game %2d/%d  %-7s  %s" % (len(scores), args.games, game.headers["Result"], reason), flush=True)

    wins, draws = scores.count(1.0), scores.count(0.5)
    losses = len(scores) - wins - draws
    print("\nRoshanChess: +%d =%d -%d  (score %.1f%%)" % (wins, draws, losses, 100 * sum(scores) / len(scores)))
    print("How games ended:", ", ".join("%s %d" % kv for kv in sorted(reasons.items())))
    if args.elo:
        estimate, low, high = elo_estimate(scores, args.elo)
        print("Estimated rating: %.0f  (95%% range %.0f to %.0f)" % (estimate, low, high))
    print("Games saved to", pgn_path)


if __name__ == "__main__":
    main()
