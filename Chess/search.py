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

from evaluation import PIECE_VALUES, PieceSquareEvaluator

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


MAX_PLY = 128
TT_MAX_ENTRIES = 300_000  # cleared when full; keeps memory to roughly 100 MB
EXACT, LOWER, UPPER = 0, 1, 2  # what a stored score means


class Searcher:
    def __init__(self, evaluator=None):
        self.evaluator = evaluator or PieceSquareEvaluator()
        self.nodes = 0
        self.stopRequested = False
        self.deadline = None
        self.killers = [[None, None] for _ in range(MAX_PLY)]
        self.history = {}
        # Transposition table: position key -> (depth, score, bound, best move id).
        # Kept between moves, since the next position's tree overlaps this one.
        self.table = {}

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
        self.killers = [[None, None] for _ in range(MAX_PLY)]
        self.history = {}
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
        first = moves[0]
        rest = moves[1:]
        self._orderMoves(rest, 0)
        moves[:] = [first] + rest
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

    # ------------------------------------------------------------ move ordering
    # Alpha-beta prunes most when the best move is searched first, so moves are
    # sorted by how promising they look:
    #   1. captures, most valuable victim first, least valuable attacker first (MVV-LVA)
    #   2. promotions
    #   3. "killer" quiet moves that caused a cutoff at the same depth elsewhere
    #   4. other quiet moves, by how often they have caused cutoffs (history)

    def _orderScore(self, move, ply, ttMove=None):
        if move.moveID == ttMove:
            return 2000000
        if move.pieceCaptured != '--':
            return 1000000 + 10 * PIECE_VALUES[move.pieceCaptured[1]] - PIECE_VALUES[move.pieceMoved[1]]
        if move.isPawnPromotion:
            return 900000 + PIECE_VALUES[move.promotionPiece]
        if ply < MAX_PLY:
            if move == self.killers[ply][0]:
                return 800000
            if move == self.killers[ply][1]:
                return 790000
        return self.history.get(move.moveID, 0)

    def _orderMoves(self, moves, ply, ttMove=None):
        moves.sort(key=lambda m: self._orderScore(m, ply, ttMove), reverse=True)

    def _rememberCutoff(self, move, depth, ply):
        if move.pieceCaptured != '--' or ply >= MAX_PLY:
            return
        if move != self.killers[ply][0]:
            self.killers[ply][1] = self.killers[ply][0]
            self.killers[ply][0] = move
        self.history[move.moveID] = self.history.get(move.moveID, 0) + depth * depth

    def _checkTime(self):
        self.nodes += 1
        if self.nodes & 1023 == 0:
            if self.stopRequested or (self.deadline and time.time() > self.deadline):
                raise SearchStopped()

    # ------------------------------------------------------------ main search

    def _negamax(self, gs, depth, alpha, beta, ply):
        self._checkTime()
        originalAlpha = alpha

        # Have we already searched this position at least this deep?
        key = gs.positionLog[-1]
        entry = self.table.get(key)
        ttMove = None
        if entry is not None:
            entryDepth, entryScore, bound, ttMove = entry
            if entryDepth >= depth and not gs.isRepetition(2):
                entryScore = self._fromTable(entryScore, ply)
                if bound == EXACT:
                    return entryScore
                if bound == LOWER and entryScore >= beta:
                    return entryScore
                if bound == UPPER and entryScore <= alpha:
                    return entryScore

        moves = gs.getValidMoves()
        if gs.checkmate:
            return -(MATE - ply)
        if gs.stalemate or gs.draw:
            return 0
        if depth == 0:
            return self._quiescence(gs, alpha, beta, ply, moves)

        self._orderMoves(moves, ply, ttMove)
        best, bestMove = -INFINITY, None
        for move in moves:
            gs.makeMove(move)
            try:
                score = -self._negamax(gs, depth - 1, -beta, -alpha, ply + 1)
            finally:
                gs.undoMove()
            if score > best:
                best, bestMove = score, move
            if best > alpha:
                alpha = best
            if alpha >= beta:
                self._rememberCutoff(move, depth, ply)
                break

        if best <= originalAlpha:
            bound = UPPER
        elif best >= beta:
            bound = LOWER
        else:
            bound = EXACT
        self._store(key, depth, best, bound, bestMove, ply)
        return best

    # Mate scores are stored relative to the position, not the root, so they
    # stay correct when the same position is reached at a different distance.
    def _toTable(self, score, ply):
        if score >= MATE - MAX_PLY:
            return score + ply
        if score <= -(MATE - MAX_PLY):
            return score - ply
        return score

    def _fromTable(self, score, ply):
        if score >= MATE - MAX_PLY:
            return score - ply
        if score <= -(MATE - MAX_PLY):
            return score + ply
        return score

    def _store(self, key, depth, score, bound, move, ply):
        if len(self.table) >= TT_MAX_ENTRIES:
            self.table.clear()
        old = self.table.get(key)
        if old is None or depth >= old[0]:
            self.table[key] = (depth, self._toTable(score, ply), bound, move.moveID if move else None)

    # ------------------------------------------------------------ quiescence search
    # At depth 0 the position may be in the middle of an exchange. Instead of
    # evaluating it there, keep searching captures (and promotions) until the
    # position is quiet. The side to move may also "stand pat": decline to
    # capture and keep the static evaluation.

    def _quiescence(self, gs, alpha, beta, ply, moves=None):
        if ply >= MAX_PLY - 1:
            return self.evaluator.evaluate(gs)
        if moves is None:
            self._checkTime()
            moves = gs.getValidMoves()
            if gs.checkmate:
                return -(MATE - ply)
            if gs.stalemate or gs.draw:
                return 0

        if gs.inCheck:
            # In check every legal move must be considered, not just captures
            best = -INFINITY
            candidates = moves
        else:
            best = self.evaluator.evaluate(gs)
            if best >= beta or ply >= MAX_PLY - 1:
                return best
            if best > alpha:
                alpha = best
            candidates = [m for m in moves if m.pieceCaptured != '--' or m.isPawnPromotion]

        self._orderMoves(candidates, MAX_PLY)
        for move in candidates:
            gs.makeMove(move)
            try:
                score = -self._quiescence(gs, -beta, -alpha, ply + 1)
            finally:
                gs.undoMove()
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
