"""
Move search: Negamax with alpha-beta pruning, run as iterative deepening
so it can stop on a time limit and still return the best move found so far.

This is the same algorithm as ChessAI.findBestMoveNegaMaxAlphaBeta, with
three changes needed to play under a clock:
  - iterative deepening (depth 1, 2, 3, ... until time runs out)
  - mate scores that prefer faster mates
  - draws (stalemate, repetition, 50-move rule) scored as 0
"""
import time

from evaluation import MaterialEvaluator

MATE = 100000  # centipawns; a mate in n plies scores MATE - n
INFINITY = 10 ** 9


class SearchStopped(Exception):
    pass


class SearchResult:
    def __init__(self, move=None, score=0, depth=0, nodes=0, seconds=0.0):
        self.move = move
        self.score = score
        self.depth = depth
        self.nodes = nodes
        self.seconds = seconds


class Searcher:
    def __init__(self, evaluator=None):
        self.evaluator = evaluator or MaterialEvaluator()
        self.nodes = 0
        self.stopRequested = False
        self.deadline = None

    def stop(self):
        # Safe to call from another thread (UCI "stop")
        self.stopRequested = True

    def search(self, gs, maxDepth=64, movetime=None, onInfo=None):
        """
        Search the position in gs and return a SearchResult.
        maxDepth: stop after this depth. movetime: seconds to think (None = no limit).
        onInfo(result) is called after every completed depth.
        Call stop() from another thread to end the search early; reset
        stopRequested to False before reusing the Searcher.
        """
        self.nodes = 0
        start = time.time()
        self.deadline = start + movetime if movetime else None

        rootMoves = gs.getValidMoves()
        best = SearchResult(rootMoves[0] if rootMoves else None)
        if len(rootMoves) <= 1:
            return best

        for depth in range(1, maxDepth + 1):
            try:
                move, score = self._searchRoot(gs, rootMoves, depth)
            except SearchStopped:
                break
            best = SearchResult(move, score, depth, self.nodes, time.time() - start)
            if onInfo:
                onInfo(best)
            # Search the best move first next iteration: it is usually still best
            rootMoves.remove(move)
            rootMoves.insert(0, move)
            if abs(score) >= MATE - 1000:
                break  # found a forced mate, deeper search won't change it
        best.nodes = self.nodes
        best.seconds = time.time() - start
        return best

    def _searchRoot(self, gs, moves, depth):
        alpha, bestMove = -INFINITY, moves[0]
        for move in moves:
            gs.makeMove(move)
            try:
                score = -self._negamax(gs, depth - 1, -INFINITY, -alpha, 1)
            finally:
                gs.undoMove()
            if score > alpha:
                alpha, bestMove = score, move
        return bestMove, alpha

    def _negamax(self, gs, depth, alpha, beta, ply):
        self.nodes += 1
        if self.nodes & 1023 == 0:
            if self.stopRequested or (self.deadline and time.time() > self.deadline):
                raise SearchStopped()

        moves = gs.getValidMoves()
        if gs.checkmate:
            return -(MATE - ply)
        if gs.stalemate or gs.draw:
            return 0
        if depth == 0:
            return self.evaluator.evaluate(gs)

        best = -INFINITY
        for move in moves:
            gs.makeMove(move)
            try:
                score = -self._negamax(gs, depth - 1, -beta, -alpha, ply + 1)
            finally:
                gs.undoMove()
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
