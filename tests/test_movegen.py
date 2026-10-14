"""
Move generation and rules tests.

Perft counts every leaf of the move tree to a fixed depth. The expected
numbers for these positions are published reference values
(https://www.chessprogramming.org/Perft_Results), so any rules bug shows
up as a wrong count. The random-game test compares legal moves against
python-chess on thousands of positions.

Run with:  python -m pytest -q
"""
import os
import random
import sys

import chess
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Chess"))
import ChessEngine  # noqa: E402

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
POS3 = "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
POS4 = "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1"
POS5 = "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8"


def perft(gs, depth):
    if depth == 0:
        return 1
    total = 0
    for move in gs.getValidMoves():
        gs.makeMove(move)
        total += perft(gs, depth - 1)
        gs.undoMove()
    return total


@pytest.mark.parametrize("fen,depth,expected", [
    (ChessEngine.STARTING_FEN, 3, 8902),
    (KIWIPETE, 1, 48),
    (KIWIPETE, 2, 2039),
    (KIWIPETE, 3, 97862),
    (POS3, 4, 43238),
    (POS4, 3, 9467),
    (POS5, 3, 62379),
])
def test_perft(fen, depth, expected):
    assert perft(ChessEngine.GameState(fen), depth) == expected


def legal_uci(gs):
    return sorted(m.getChessNotation() for m in gs.getValidMoves())


def test_random_games_match_python_chess():
    rng = random.Random(2026)
    for _ in range(300):
        gs, board = ChessEngine.GameState(), chess.Board()
        for _ in range(160):
            expected = sorted(m.uci() for m in board.legal_moves)
            assert legal_uci(gs) == expected, board.fen()
            if not expected:
                break
            uci = rng.choice(expected)
            board.push_uci(uci)
            gs.makeMove(next(m for m in gs.getValidMoves() if m.getChessNotation() == uci))
            assert gs.getFEN().split()[:4] == board.fen(en_passant="fen").split()[:4]


def test_undo_restores_everything():
    gs = ChessEngine.GameState(KIWIPETE)
    before = (gs.getFEN(), dict(gs.positionCounts))
    for move in gs.getValidMoves():
        gs.makeMove(move)
        for reply in gs.getValidMoves():
            gs.makeMove(reply)
            gs.undoMove()
        gs.undoMove()
        assert (gs.getFEN(), dict(gs.positionCounts)) == before


def test_fen_round_trip():
    for fen in (ChessEngine.STARTING_FEN, KIWIPETE, POS3, POS4, POS5):
        assert ChessEngine.GameState(fen).getFEN() == fen


def test_black_rook_move_keeps_white_castling():
    gs = ChessEngine.GameState("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
    gs.makeMove(next(m for m in gs.getValidMoves() if m.getChessNotation() == "a8b8"))
    assert {"e1g1", "e1c1"} <= set(legal_uci(gs))


def test_underpromotion():
    gs = ChessEngine.GameState("8/P6k/8/8/8/8/8/K7 w - - 0 1")
    assert {"a7a8q", "a7a8r", "a7a8b", "a7a8n"} <= set(legal_uci(gs))
    gs.makeMove(next(m for m in gs.getValidMoves() if m.getChessNotation() == "a7a8n"))
    assert gs.board[0][0] == "wN"


def test_threefold_repetition():
    gs = ChessEngine.GameState()
    for uci in ["g1f3", "g8f6", "f3g1", "f6g8"] * 2:
        assert not gs.draw
        gs.makeMove(next(m for m in gs.getValidMoves() if m.getChessNotation() == uci))
        gs.getValidMoves()
    assert gs.draw and gs.drawReason == "threefold repetition"


def test_fifty_move_rule():
    gs = ChessEngine.GameState("8/8/8/4k3/8/8/8/R3K3 w - - 99 80")
    gs.makeMove(next(m for m in gs.getValidMoves() if m.getChessNotation() == "a1a2"))
    gs.getValidMoves()
    assert gs.draw and gs.drawReason == "50-move rule"


@pytest.mark.parametrize("fen,is_draw", [
    ("8/8/8/4k3/8/8/8/4K3 w - - 0 1", True),
    ("8/8/8/4k3/8/8/8/2B1K3 w - - 0 1", True),
    ("8/8/8/4k3/8/8/8/1N2K3 w - - 0 1", True),
    ("2b5/8/8/4k3/8/8/8/2B1K3 w - - 0 1", False),  # bishops on different colours
    ("8/8/8/4k3/8/8/8/1NN1K3 w - - 0 1", False),
    ("8/8/8/4k3/8/8/4P3/4K3 w - - 0 1", False),
])
def test_insufficient_material(fen, is_draw):
    assert ChessEngine.GameState(fen).insufficientMaterial() == is_draw
