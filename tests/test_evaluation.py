import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Chess"))
import ChessEngine  # noqa: E402
from evaluation import MaterialEvaluator, PieceSquareEvaluator  # noqa: E402

POSITIONS = [
    ChessEngine.STARTING_FEN,
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 1 5",
]


def mirrored(fen):
    # Same position with colours swapped and the board flipped
    return chess.Board(fen).mirror().fen()


def test_evaluation_is_colour_symmetric():
    for evaluator in (MaterialEvaluator(), PieceSquareEvaluator()):
        for fen in POSITIONS:
            original = evaluator.evaluate(ChessEngine.GameState(fen))
            flipped = evaluator.evaluate(ChessEngine.GameState(mirrored(fen)))
            assert original == flipped, (evaluator.name, fen)


def test_starting_position_is_level():
    assert PieceSquareEvaluator().evaluate(ChessEngine.GameState()) == 0


def test_central_knight_beats_rim_knight():
    centre = ChessEngine.GameState("4k3/8/8/8/3N4/8/8/4K3 w - - 0 1")
    rim = ChessEngine.GameState("4k3/8/8/8/N7/8/8/4K3 w - - 0 1")
    assert PieceSquareEvaluator().evaluate(centre) > PieceSquareEvaluator().evaluate(rim)
