import pygame
import chess
from chess_game import ChessGame
from Engine.engine import Engine
from Engine.elo_system import EloSystem
from utils import (
    WIDTH, HEIGHT, screen, images, menu_background, game_font, sounds,
    draw_board, draw_pieces, draw_button
)
from notification import handle_move_outcome
import time
import threading
import queue

def ai_move_thread(engine, board_fen, result_queue):
    """Hàm chạy trong luồng riêng để tính toán nước đi tốt nhất của AI"""
    try:
        engine.set_position(board_fen)
        move = engine.get_best_move()
        result_queue.put(move)
    except Exception as e:
        print(f"[ERROR] Lỗi khi tính toán nước đi: {e}")
        result_queue.put(None)

def play_ai_vs_ai():
    """Play a game between two AI players with multithreading optimization."""
    board = chess.Board()
    engine1 = Engine(max_depth=4, max_time=10.0)
    engine2 = Engine(max_depth=4, max_time=10.0)
    
    # Initialize ELO system
    elo_system = EloSystem()
    engine1_id = "AI_1"
    engine2_id = "AI_2"
    rating1 = elo_system.get_rating(engine1_id)
    rating2 = elo_system.get_rating(engine2_id)
    
    # Tạo queue để nhận kết quả từ các luồng
    result_queue = queue.Queue()
    
    # Biến để theo dõi trạng thái luồng
    ai_thinking = False
    ai_thread = None
    
    print("Starting AI vs AI game...")
    print("AI 1 (White) vs AI 2 (Black)")
    print("\nInitial position:")
    print(board)
    
    # Tạo cửa sổ hiển thị
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("AI vs AI Chess Game")
    clock = pygame.time.Clock()
    
    running = True
    while running and not board.is_game_over():
        # Xử lý sự kiện
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Vẽ bàn cờ và quân cờ
        draw_board(screen, menu_background)
        
        # Hiển thị bàn cờ hiện tại
        game = ChessGame()
        game.board = board
        draw_pieces(screen, game, images)
        
        # Hiển thị thông tin lượt đi
        turn_text = f"Turn: {'White' if board.turn == chess.WHITE else 'Black'}"
        font = pygame.font.Font(None, 36)
        text = font.render(turn_text, True, (255, 255, 255))
        screen.blit(text, (20, 20))
        
        # Hiển thị trạng thái AI đang suy nghĩ
        if ai_thinking:
            thinking_text = "AI is thinking" + "." * (int(pygame.time.get_ticks() / 500) % 4)
            thinking_surface = font.render(thinking_text, True, (255, 0, 0))
            screen.blit(thinking_surface, (WIDTH // 2 - 100, 20))
        
        pygame.display.flip()
        
        # Nếu AI chưa đang suy nghĩ, bắt đầu tính toán nước đi trong luồng riêng
        if not ai_thinking:
            # Lấy engine hiện tại dựa trên lượt đi
            current_engine = engine1 if board.turn == chess.WHITE else engine2
            
            # Bắt đầu luồng mới để tính toán nước đi
            ai_thinking = True
            ai_thread = threading.Thread(
                target=ai_move_thread,
                args=(current_engine, board.fen(), result_queue)
            )
            ai_thread.daemon = True  # Đảm bảo luồng kết thúc khi chương trình chính kết thúc
            ai_thread.start()
        else:
            # Kiểm tra xem AI đã tính toán xong chưa
            try:
                # Non-blocking check
                move = result_queue.get_nowait()
                ai_thinking = False
                
                if not move:
                    print("No legal moves available!")
                    break
                
                # Convert move to UCI string
                uci_move = move.uci()
                
                # Get source and target squares
                from_square = chess.parse_square(uci_move[:2])
                to_square = chess.parse_square(uci_move[2:4])
                
                # Get source and target coordinates
                from_col = chess.square_file(from_square)
                from_row = chess.square_rank(from_square)
                to_col = chess.square_file(to_square)
                to_row = chess.square_rank(to_square)
                
                # Make the move
                board.push(move)
                
                # Print move information
                print(f"\n{'White' if board.turn == chess.BLACK else 'Black'} plays: {uci_move}")
                print(f"From: ({from_col}, {from_row})")
                print(f"To: ({to_col}, {to_row})")
                print("\nCurrent position:")
                print(board)
                
                # Thêm một khoảng thời gian nhỏ giữa các nước đi để dễ theo dõi
                time.sleep(0.5)
                
            except queue.Empty:
                # AI vẫn đang tính toán
                pass
        
        # Giới hạn FPS để giảm sử dụng CPU
        clock.tick(30)
    
    # Hiển thị kết quả trò chơi và cập nhật ELO
    if running:
        result = board.outcome()
        if result:
            if result.winner is None:
                print("\nGame ended in a draw!")
                result_text = "Game ended in a draw!"
                # Update ELO for draw
                new_rating1, new_rating2 = elo_system.update_ratings(engine1_id, engine2_id, 0.5)
            else:
                winner = 'White' if result.winner else 'Black'
                print(f"\n{winner} wins by {result.termination.name}!")
                result_text = f"{winner} wins by {result.termination.name}!"
                # Update ELO based on winner
                elo_result = 1.0 if result.winner == chess.WHITE else 0.0
                new_rating1, new_rating2 = elo_system.update_ratings(engine1_id, engine2_id, elo_result)
                
            # Add ELO changes to result text
            result_text += f"\nELO Changes:"
            result_text += f"\nAI 1 (White): {rating1} → {new_rating1} ({'+' if new_rating1 > rating1 else ''}{new_rating1 - rating1})"
            result_text += f"\nAI 2 (Black): {rating2} → {new_rating2} ({'+' if new_rating2 > rating2 else ''}{new_rating2 - rating2})"
        else:
            print("\nGame ended without a result.")
            result_text = "Game ended without a result."
        
        # Hiển thị kết quả trên màn hình
        # Display result as multiple lines
        font = pygame.font.Font(None, 36)
        lines = result_text.split('\n')
        line_height = 40
        start_y = HEIGHT // 2 - (len(lines) * line_height) // 2
        
        for i, line in enumerate(lines):
            text = font.render(line, True, (255, 0, 0))
            text_rect = text.get_rect(center=(WIDTH // 2, start_y + i * line_height))
            screen.blit(text, text_rect)
        
        # Tạo overlay mờ
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        
        # Đợi người dùng đóng cửa sổ
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
    
    pygame.quit()
