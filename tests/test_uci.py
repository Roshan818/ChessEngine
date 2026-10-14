"""
UCI tests: drive the engine through python-chess exactly as a GUI,
a Stockfish match runner or lichess-bot would.
"""
import os
import sys
import time

import chess
import chess.engine
import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "Chess"))
import ChessEngine  # noqa: E402
from search import MATE, Searcher  # noqa: E402

ENGINE_CMD = [sys.executable, os.path.join(ROOT, "Chess", "uci.py")]


@pytest.fixture
def engine():
    eng = chess.engine.SimpleEngine.popen_uci(ENGINE_CMD)
    yield eng
    eng.quit()


def test_handshake(engine):
    assert engine.id["name"] == "RoshanChess"
    assert engine.id["author"] == "Roshan Kumar"


def test_returns_legal_move_from_moves_list(engine):
    board = chess.Board()
    for uci in ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4"]:
        board.push_uci(uci)
    result = engine.play(board, chess.engine.Limit(depth=2))
    assert result.move in board.legal_moves


def test_plays_a_short_game_against_itself(engine):
    board = chess.Board()
    while not board.is_game_over() and board.fullmove_number <= 6:
        move = engine.play(board, chess.engine.Limit(depth=1)).move
        assert move in board.legal_moves
        board.push(move)


def test_finds_mate_in_one(engine):
    board = chess.Board("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1")  # Ra8#
    info = engine.analyse(board, chess.engine.Limit(depth=2))
    assert info["pv"][0] == chess.Move.from_uci("a1a8")
    assert info["score"].white() == chess.engine.Mate(1)


def test_respects_movetime(engine):
    start = time.time()
    engine.play(chess.Board(), chess.engine.Limit(time=0.5))
    assert time.time() - start < 1.5


def test_respects_clock(engine):
    board = chess.Board()
    start = time.time()
    engine.play(board, chess.engine.Limit(white_clock=3, black_clock=3))
    assert time.time() - start < 2.0


def test_promotion_move_from_fen(engine):
    board = chess.Board("8/P6k/8/8/8/8/8/K7 w - - 0 1")
    move = engine.play(board, chess.engine.Limit(depth=2)).move
    assert move in board.legal_moves


def test_search_prefers_faster_mate():
    # Mate in one is available; the search must take it, not a slower mate
    gs = ChessEngine.GameState("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1")
    result = Searcher().search(gs, maxDepth=3)
    assert result.move.getChessNotation() == "a1a8"
    assert result.score == MATE - 1


def test_search_scores_stalemate_as_draw():
    # Black to move, no legal moves, not in check
    gs = ChessEngine.GameState("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    gs.getValidMoves()
    assert gs.stalemate
