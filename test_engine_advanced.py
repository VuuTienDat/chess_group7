import pytest
import chess
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Engine.engine import Engine

@pytest.fixture
def ai():
    return Engine(max_depth=3, max_time=0.5, num_threads=2)

# --- KIỂM THỬ EVALUATION (ĐÁNH GIÁ THẾ CỜ) ---

def test_material_advantage(ai):
    """TC01: Kiểm tra nhận biết lợi thế vật chất (Hậu vs Vua)"""
    fen = "8/8/8/8/8/8/Q7/K6k w - - 0 1"
    score = ai.evaluate_position(chess.Board(fen))
    assert score > 800

def test_positional_knight_bonus_bva(ai):
    """TC02: Kiểm tra ưu tiên Mã trung tâm so với Mã ở biên (Vị trí)"""
    # FEN đã fix lỗi, cân bằng vật chất
    board_center = chess.Board("k7/8/8/8/4N3/8/8/K7 w - - 0 1")
    board_corner = chess.Board("k7/8/8/8/8/8/8/K6N w - - 0 1")
    
    score_center = ai.evaluate_position(board_center)
    score_corner = ai.evaluate_position(board_corner)
    
    assert score_center > score_corner

# --- KIỂM THỬ TÌM KIẾM (SEARCH) VÀ ĐỘ ỔN ĐỊNH ---

def test_find_mate_in_one(ai):
    """TC03: Kiểm tra AI giải được thế cờ thắng nhanh (a2a8)"""
    fen = "k7/8/1K6/8/8/8/R7/8 w - - 0 1"
    ai.set_position(fen)
    best_move = ai.get_best_move()
    assert best_move == chess.Move.from_uci("a2a8")

def test_engine_threading_stability(ai):
    """TC04: Kiểm tra sự ổn định khi chạy đa luồng (Lazy SMP)"""
    ai.num_threads = 4
    ai.set_position(chess.STARTING_FEN)
    # Nếu không crash và trả về move là PASS
    move = ai.get_best_move()
    assert move is not None