"""
Position evaluation.

The search asks an Evaluator how good a position is for the side to move,
in centipawns (100 = one pawn). Keeping this behind one small interface
means the hand-written evaluation can later be swapped for a learned one
(a neural network trained from self-play or engine games) without touching
the search, the UI or the UCI code.
"""

PIECE_VALUES = {"p": 100, "N": 300, "B": 300, "R": 500, "Q": 900, "K": 0}


class Evaluator:
    """Interface: return a score in centipawns from the side to move's point of view."""

    name = "base"

    def evaluate(self, gs):
        raise NotImplementedError


class MaterialEvaluator(Evaluator):
    """The original evaluation: count material, nothing else."""

    name = "material"

    def evaluate(self, gs):
        score = 0
        for row in gs.board:
            for square in row:
                if square[0] == "w":
                    score += PIECE_VALUES[square[1]]
                elif square[0] == "b":
                    score -= PIECE_VALUES[square[1]]
        return score if gs.whiteToMove else -score


# Piece-square tables, based on Tomasz Michniewski's "Simplified Evaluation Function".
# Written from white's side with the 8th rank first, matching the board's row order
# (row 0 = rank 8). Black uses the same tables mirrored top to bottom.
PST = {
    "p": [
        0, 0, 0, 0, 0, 0, 0, 0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5, 5, 10, 25, 25, 10, 5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, -5, -10, 0, 0, -10, -5, 5,
        5, 10, 10, -20, -20, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0],
    "N": [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50],
    "B": [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -20, -10, -10, -10, -10, -10, -10, -20],
    "R": [
        0, 0, 0, 0, 0, 0, 0, 0,
        5, 10, 10, 10, 10, 10, 10, 5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        0, 0, 0, 5, 5, 0, 0, 0],
    "Q": [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        0, 0, 5, 5, 5, 5, 0, -5,
        -10, 5, 5, 5, 5, 5, 0, -10,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20],
    # King: stay sheltered while there is material on the board...
    "K_middlegame": [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        20, 20, 0, 0, 0, 0, 20, 20,
        20, 30, 10, 0, 0, 10, 30, 20],
    # ...and come to the centre in the endgame.
    "K_endgame": [
        -50, -40, -30, -20, -20, -30, -40, -50,
        -30, -20, -10, 0, 0, -10, -20, -30,
        -30, -10, 20, 30, 30, 20, -10, -30,
        -30, -10, 30, 40, 40, 30, -10, -30,
        -30, -10, 30, 40, 40, 30, -10, -30,
        -30, -10, 20, 30, 30, 20, -10, -30,
        -30, -30, 0, 0, 0, 0, -30, -30,
        -50, -30, -30, -30, -30, -30, -30, -50],
}

PST_PIECE_VALUES = {"p": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}
PHASE_WEIGHTS = {"N": 1, "B": 1, "R": 2, "Q": 4}  # 24 = all pieces on the board
BISHOP_PAIR = 30


class PieceSquareEvaluator(Evaluator):
    """
    Material plus piece placement. The king's table blends from middlegame to
    endgame as pieces come off the board (a "tapered" evaluation).
    """

    name = "piece-square"

    def evaluate(self, gs):
        score = 0
        phase = 0
        kingSquares = {}
        bishops = {"w": 0, "b": 0}
        for r, row in enumerate(gs.board):
            for c, square in enumerate(row):
                if square == "--":
                    continue
                color, piece = square[0], square[1]
                if piece == "K":
                    kingSquares[color] = (r, c)
                    continue
                index = r * 8 + c if color == "w" else (7 - r) * 8 + c
                value = PST_PIECE_VALUES[piece] + PST[piece][index]
                score += value if color == "w" else -value
                phase += PHASE_WEIGHTS.get(piece, 0)
                if piece == "B":
                    bishops[color] += 1

        phase = min(phase, 24)
        for color, (r, c) in kingSquares.items():
            index = r * 8 + c if color == "w" else (7 - r) * 8 + c
            value = (PST["K_middlegame"][index] * phase + PST["K_endgame"][index] * (24 - phase)) // 24
            score += value if color == "w" else -value

        if bishops["w"] >= 2:
            score += BISHOP_PAIR
        if bishops["b"] >= 2:
            score -= BISHOP_PAIR
        return score if gs.whiteToMove else -score
