import pytest
import chess
import sys
import os


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from chess_game import ChessGame
except ImportError:
    from Chess_BTL.chess_group7.chess_game import ChessGame

@pytest.fixture
def game():
    return ChessGame()



def test_initial_state_and_get_piece(game):
    """TC01: Kiểm tra trạng thái khởi tạo và hàm get_piece"""
    assert game.board.fen() == chess.STARTING_FEN
    assert game.get_piece(chess.E2).symbol() == 'P'
    assert game.get_piece(chess.E4) is None

def test_move_valid_return_structure(game):
    """TC02: Kiểm tra nước đi hợp lệ trả về đúng cấu trúc"""
    result = game.move(chess.E2, chess.E4)
    assert result["valid"] is True
    assert result["promotion_required"] is False
    assert len(game.move_history) == 1

def test_move_invalid_return_structure(game):
    """TC03: Kiểm tra nước đi sai luật trả về đúng cấu trúc (Pawn đi lùi)"""
    result = game.move(chess.E2, chess.E1) 
    assert result["valid"] is False
    assert len(game.move_history) == 0

def test_undo_functionality(game):
    """TC04: Kiểm tra Undo"""
    game.move(chess.E2, chess.E4)
    game.undo()
    assert len(game.move_history) == 0
    assert game.board.fen() == chess.STARTING_FEN

def test_promotion_trigger_ui_logic(game):
    """TC05: Kiểm tra cờ báo hiệu UI (promotion_required)"""
    # Tốt trắng sắp phong cấp
    game.board.set_fen("8/P7/8/8/8/8/8/k6K w - - 0 1")
    # Đi Tốt lên hàng cuối KHÔNG chỉ định quân
    result = game.move(chess.A7, chess.A8)
    
    assert result["valid"] is True # Logic wrapper cho phép move
    assert result["promotion_required"] is True # Báo hiệu UI
    
def test_promotion_execution_final(game):
    """TC06: Kiểm tra thực hiện phong cấp (Kết thúc quá trình)"""
    game.board.set_fen("8/P7/8/8/8/8/8/k6K w - - 0 1")
    result = game.move(chess.A7, chess.A8, promotion=chess.QUEEN)
    
    assert result["valid"] is True
    assert game.board.piece_at(chess.A8).piece_type == chess.QUEEN