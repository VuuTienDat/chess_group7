import pytest
import chess
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


mock_screen = MagicMock()
mock_sounds_dict = {
    'move': MagicMock(),
    'capture': MagicMock(),
    'check': MagicMock(),
    'checkmate': MagicMock()
}


patcher = patch.multiple(
    'utils',
    screen=mock_screen,
    menu_background=MagicMock(),
    game_font=MagicMock(),
    sounds=mock_sounds_dict,
    create=True
)
patcher.start()
# Bây giờ mới import, đảm bảo an toàn không crash
from notification import handle_move_outcome
patcher.stop()

# --- FIXTURES ---
@pytest.fixture(autouse=True)
def reset_all_mocks():
    """Tự động reset bộ đếm của Mock trước mỗi Test Case"""
    mock_screen.reset_mock()
    for m in mock_sounds_dict.values():
        m.reset_mock()

@pytest.fixture
def mock_game():
    """Tạo game giả với trạng thái mặc định là False (không chiếu/hòa/thắng)"""
    game = MagicMock()
    # Mặc định tất cả các cờ trạng thái là False
    game.board.is_checkmate.return_value = False
    game.board.is_stalemate.return_value = False
    game.board.is_insufficient_material.return_value = False
    game.board.is_seventyfive_moves.return_value = False
    game.board.is_fivefold_repetition.return_value = False
    game.board.is_check.return_value = False
    return game

@pytest.fixture
def notification_display_mock():
    """Chặn hàm hiển thị popup (show_notification) để không bị treo vòng lặp"""
    with patch('notification.show_notification') as mock:
        yield mock

# --- TEST CASES CHI TIẾT ---

def test_sound_normal_move(mock_game):
    """TC01: Đi nước thường -> Chỉ kêu 'Move', không kêu cái khác"""
    handle_move_outcome(mock_game, target_piece=None)
    
    mock_sounds_dict['move'].play.assert_called_once()
    mock_sounds_dict['capture'].play.assert_not_called()
    mock_sounds_dict['check'].play.assert_not_called()

def test_sound_capture(mock_game):
    """TC02: Ăn quân -> Chỉ kêu 'Capture', không kêu 'Move'"""
    # Giả lập có target_piece (tức là ăn quân)
    handle_move_outcome(mock_game, target_piece="Pawn")
    
    mock_sounds_dict['capture'].play.assert_called_once()
    mock_sounds_dict['move'].play.assert_not_called()

def test_sound_check(mock_game):
    """TC03: Chiếu tướng -> Kêu 'Move' VÀ 'Check'"""
    # Giả lập trạng thái đang chiếu
    mock_game.board.is_check.return_value = True
    
    handle_move_outcome(mock_game, target_piece=None)
    
    mock_sounds_dict['move'].play.assert_called_once()
    mock_sounds_dict['check'].play.assert_called_once()

def test_checkmate_flow(mock_game, notification_display_mock):
    """TC04: Chiếu hết -> Kêu 'Checkmate' + Hiện thông báo thắng"""
    mock_game.board.is_checkmate.return_value = True
    mock_game.board.turn = chess.BLACK # Đen bị chiếu hết -> Trắng thắng
    
    handle_move_outcome(mock_game)
    
    # Phải kêu tiếng checkmate
    mock_sounds_dict['checkmate'].play.assert_called_once()
    # Phải gọi hàm hiện thông báo với nội dung đúng
    notification_display_mock.assert_called_with(mock_game, "Checkmate! White wins!")

def test_stalemate_flow(mock_game, notification_display_mock):
    """TC05: Cờ hòa (Stalemate) -> Hiện thông báo hòa"""
    mock_game.board.is_stalemate.return_value = True
    
    handle_move_outcome(mock_game)
    
    notification_display_mock.assert_called_with(mock_game, "Stalemate!")

def test_draw_insufficient_material(mock_game, notification_display_mock):
    """TC06: Hòa do thiếu quân -> Hiện thông báo"""
    mock_game.board.is_insufficient_material.return_value = True
    
    handle_move_outcome(mock_game)
    
    notification_display_mock.assert_called_with(mock_game, "Draw: Insufficient material!")