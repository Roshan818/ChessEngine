import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from match import OPENINGS, elo_estimate  # noqa: E402

import chess  # noqa: E402


def test_even_score_equals_opponent_rating():
    estimate, low, high = elo_estimate([1, 0] * 50, 1500)
    assert round(estimate) == 1500 and low < 1500 < high


def test_lower_score_means_lower_rating():
    assert elo_estimate([1, 0, 0, 0] * 25, 1500)[0] < 1500


def test_openings_are_legal():
    for opening in OPENINGS:
        board = chess.Board()
        for uci in opening.split():
            board.push_uci(uci)
