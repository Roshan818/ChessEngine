"""
UCI (Universal Chess Interface) front end.

UCI is the text protocol chess GUIs, Stockfish matches and Lichess bots use
to talk to an engine. Run it with:

    python Chess/uci.py

and it reads commands on stdin and answers on stdout, e.g.

    position startpos moves e2e4 e7e5
    go movetime 2000
    -> info depth 3 score cp 0 nodes 2510 time 640 nps 3921 pv g1f3
    -> bestmove g1f3
"""
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ChessEngine  # noqa: E402
from search import MATE, Searcher  # noqa: E402

ENGINE_NAME = "RoshanChess"
ENGINE_AUTHOR = "Roshan Kumar"
MOVE_OVERHEAD = 0.1  # seconds kept in reserve for communication lag


def send(text):
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def parsePosition(tokens):
    # position [startpos | fen <6 fields>] [moves m1 m2 ...]
    if "moves" in tokens:
        split = tokens.index("moves")
        setup, moves = tokens[:split], tokens[split + 1:]
    else:
        setup, moves = tokens, []
    if setup and setup[0] == "fen":
        gs = ChessEngine.GameState(" ".join(setup[1:]))
    else:
        gs = ChessEngine.GameState()
    for uci in moves:
        legal = {m.getChessNotation(): m for m in gs.getValidMoves()}
        if uci not in legal:
            send("info string illegal move " + uci)
            break
        gs.makeMove(legal[uci])
    return gs


def thinkTime(params, whiteToMove):
    """Seconds to spend on this move, from the UCI 'go' parameters (None = no limit)."""
    if "movetime" in params:
        return max(0.01, params["movetime"] / 1000 - MOVE_OVERHEAD)
    if "infinite" in params:
        return None
    remaining = params.get("wtime" if whiteToMove else "btime")
    if remaining is None:
        return None
    increment = params.get("winc" if whiteToMove else "binc", 0)
    movesToGo = params.get("movestogo", 30)
    budget = remaining / 1000 / movesToGo + increment / 1000 * 0.8
    budget = min(budget, remaining / 1000 * 0.5)  # never risk flagging
    return max(0.01, budget - MOVE_OVERHEAD)


def formatScore(score):
    if abs(score) >= MATE - 1000:
        plies = MATE - abs(score)
        moves = (plies + 1) // 2
        return "mate " + str(moves if score > 0 else -moves)
    return "cp " + str(score)


class UCIEngine:
    def __init__(self):
        self.gs = ChessEngine.GameState()
        self.searcher = Searcher()
        self.thread = None

    def waitForSearch(self):
        if self.thread is not None:
            self.searcher.stop()
            self.thread.join()
            self.thread = None

    def go(self, tokens):
        params, i = {}, 0
        while i < len(tokens):
            key = tokens[i]
            if key == "infinite":
                params[key] = True
                i += 1
            elif i + 1 < len(tokens):
                try:
                    params[key] = int(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
            else:
                i += 1

        movetime = thinkTime(params, self.gs.whiteToMove)
        depth = params.get("depth", 64 if (movetime or "infinite" in params) else 4)

        def info(result):
            nps = int(result.nodes / result.seconds) if result.seconds > 0 else 0
            send("info depth %d score %s nodes %d time %d nps %d pv %s" % (
                result.depth, formatScore(result.score), result.nodes,
                int(result.seconds * 1000), nps, result.move.getChessNotation()))

        def run():
            result = self.searcher.search(self.gs, maxDepth=depth, movetime=movetime, onInfo=info)
            send("bestmove " + (result.move.getChessNotation() if result.move else "0000"))

        self.searcher.stopRequested = False
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def handle(self, line):
        tokens = line.split()
        if not tokens:
            return True
        command, args = tokens[0], tokens[1:]
        if command == "uci":
            send("id name " + ENGINE_NAME)
            send("id author " + ENGINE_AUTHOR)
            send("uciok")
        elif command == "isready":
            send("readyok")
        elif command == "ucinewgame":
            self.waitForSearch()
            self.gs = ChessEngine.GameState()
        elif command == "position":
            self.waitForSearch()
            self.gs = parsePosition(args)
        elif command == "go":
            self.waitForSearch()
            self.go(args)
        elif command == "stop":
            self.waitForSearch()
        elif command == "quit":
            self.waitForSearch()
            return False
        elif command == "d":  # debug: print the current position
            send(self.gs.getFEN())
        return True


def main():
    engine = UCIEngine()
    for line in sys.stdin:
        if not engine.handle(line.strip()):
            break


if __name__ == "__main__":
    main()
