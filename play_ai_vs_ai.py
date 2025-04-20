import pygame
import chess
from chess_game import ChessGame
from Engine.engine import Engine
from Engine.elo_system import EloSystem
from utils import (
    WIDTH, HEIGHT, screen, images, menu_background, game_font, sounds,
    draw_board, draw_pieces, draw_button
)
import time
import threading
import queue

def ai_move_thread(engine, board_fen, result_queue):
    """Chạy trong luồng riêng để tính nước đi AI."""
    try:
        engine.set_position(board_fen)
        move = engine.get_best_move()
        result_queue.put(move)
    except Exception:
        result_queue.put(None)

def play_ai_vs_ai():
    """Chơi giữa hai AI với nút Back hoạt động."""
    # Khởi tạo bàn cờ và engine
    board = chess.Board()
    engine1 = Engine(max_depth=4, max_time=10.0)
    engine2 = Engine(max_depth=4, max_time=10.0)
    
    # Khởi tạo hệ thống ELO
    elo_system = EloSystem()
    engine1_id = "AI_1"
    engine2_id = "AI_2"
    rating1 = elo_system.get_rating(engine1_id)
    rating2 = elo_system.get_rating(engine2_id)
    
    # Tạo queue cho kết quả nước đi AI
    result_queue = queue.Queue()
    
    # Theo dõi trạng thái AI
    ai_thinking = False
    ai_thread = None
    
    # Đặt tiêu đề cửa sổ
    pygame.display.set_caption("Trận Cờ AI vs AI")
    clock = pygame.time.Clock()
    
    # Định nghĩa nút Back
    back_button_text = "Back"
    
    running = True
    while running and not board.is_game_over():
        # Xử lý sự kiện
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                btn_back = pygame.Rect(WIDTH - 110, 675, 100, 40)
                if btn_back.collidepoint(event.pos):
                    sounds['move'].play()
                    running = False
        
        # Vẽ bàn cờ và quân cờ
        draw_board(screen, menu_background)
        game = ChessGame()
        game.board = board
        draw_pieces(screen, game, images)
        
        # Vẽ chỉ báo lượt đi
        turn_text = f"Lượt: {'Trắng' if board.turn == chess.WHITE else 'Đen'}"
        font = pygame.font.Font(None, 36)
        text = font.render(turn_text, True, (255, 255, 255))
        screen.blit(text, (20, 20))
        
        # Vẽ chỉ báo AI đang nghĩ
        if ai_thinking:
            thinking_text = "AI đang nghĩ" + "." * (int(pygame.time.get_ticks() / 500) % 4)
            thinking_surface = font.render(thinking_text, True, (255, 0, 0))
            screen.blit(thinking_surface, (WIDTH // 2 - 100, 20))
        
        # Vẽ nút Back (cuối cùng)
        draw_button(screen, game_font, back_button_text, WIDTH - 110, 675, 100, 40,
                    (200, 50, 50), (255, 100, 100), mouse_pos)
        
        pygame.display.flip()
        
        # Xử lý tính toán nước đi AI
        if not ai_thinking:
            current_engine = engine1 if board.turn == chess.WHITE else engine2
            ai_thinking = True
            ai_thread = threading.Thread(
                target=ai_move_thread,
                args=(current_engine, board.fen(), result_queue)
            )
            ai_thread.daemon = True
            ai_thread.start()
        else:
            try:
                move = result_queue.get_nowait()
                ai_thinking = False
                
                if not move:
                    break
                
                # Xử lý nước đi
                board.push(move)
                time.sleep(0.5)
                
            except queue.Empty:
                pass
        
        clock.tick(30)
    
    # Hiển thị kết quả và cập nhật ELO
    if running:
        result = board.outcome()
        if result:
            if result.winner is None:
                result_text = "Trò chơi kết thúc hòa!"
                new_rating1, new_rating2 = elo_system.update_ratings(engine1_id, engine2_id, 0.5)
            else:
                winner = 'Trắng' if result.winner else 'Đen'
                result_text = f"{winner} thắng bằng {result.termination.name}!"
                elo_result = 1.0 if result.winner == chess.WHITE else 0.0
                new_rating1, new_rating2 = elo_system.update_ratings(engine1_id, engine2_id, elo_result)
                
            result_text += f"\nThay đổi ELO:"
            result_text += f"\nAI 1 (Trắng): {rating1} → {new_rating1} ({'+' if new_rating1 > rating1 else ''}{new_rating1 - rating1})"
            result_text += f"\nAI 2 (Đen): {rating2} → {new_rating2} ({'+' if new_rating2 > rating2 else ''}{new_rating2 - rating2})"
        else:
            result_text = "Trò chơi kết thúc không có kết quả."
        
        # Hiển thị kết quả
        font = pygame.font.Font(None, 36)
        lines = result_text.split('\n')
        line_height = 40
        start_y = HEIGHT // 2 - (len(lines) * line_height) // 2
        
        waiting = True
        while waiting:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    btn_back = pygame.Rect(WIDTH - 110, 675, 100, 40)
                    if btn_back.collidepoint(event.pos):
                        sounds['move'].play()
                        waiting = False
            
            # Vẽ bàn cờ và quân cờ
            draw_board(screen, menu_background)
            game = ChessGame()
            game.board = board
            draw_pieces(screen, game, images)
            
            # Vẽ văn bản kết quả
            for i, line in enumerate(lines):
                text = font.render(line, True, (255, 0, 0))
                text_rect = text.get_rect(center=(WIDTH // 2, start_y + i * line_height))
                screen.blit(text, text_rect)
            
            # Vẽ lớp phủ
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))
            
            # Vẽ nút Back (sau lớp phủ)
            draw_button(screen, game_font, back_button_text, WIDTH - 110, 675, 100, 40,
                        (200, 50, 50), (255, 100, 100), mouse_pos)
            
            pygame.display.flip()
            clock.tick(30)
    
    # Quay lại menu chính
    from main_menu import main_menu
    main_menu()