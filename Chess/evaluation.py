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
