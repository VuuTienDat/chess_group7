import pygame
import chess
import threading
import queue
from chess_game import ChessGame
from Engine.engine import Engine
from utils import (
    WIDTH, HEIGHT, SQUARE_SIZE, screen, images, menu_background, game_font, sounds,
    draw_text, draw_board, draw_pieces, draw_button,
    draw_move_hints, get_square_from_mouse
)
from notification import handle_move_outcome

# Tạo queue để truyền dữ liệu giữa các luồng
ai_move_queue = queue.Queue()

def ai_move_thread(board_fen, engine):
    """Hàm xử lý nước đi của AI trong một luồng riêng biệt"""
    try:
        engine.set_position(board_fen)
        move = engine.get_best_move()
        if move:
            ai_move_queue.put(move)
        else:
            print("[WARNING] AI couldn't find a move")
            ai_move_queue.put(None)
    except Exception as e:
        print(f"[ERROR] Failed to get AI move: {e}")
        ai_move_queue.put(None)

def choose_player_color():
    """
    Display interface for user to choose white or black pieces.
    Returns the color chosen (chess.WHITE or chess.BLACK).
    """
    running = True
    while running:
        screen.blit(menu_background, (0, 0))
        draw_text(screen, game_font, "Choose Your Color", WIDTH // 2, HEIGHT // 2 - 100, color=(0, 0, 0))
        mouse_pos = pygame.mouse.get_pos()

        # Draw buttons
        btn_white = draw_button(screen, game_font, "White", WIDTH // 2 - 100, HEIGHT // 2 - 40, 
                              200, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
        btn_black = draw_button(screen, game_font, "Black", WIDTH // 2 - 100, HEIGHT // 2 + 20, 
                              200, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
        btn_back = draw_button(screen, game_font, "Back", WIDTH // 2 - 100, HEIGHT // 2 + 80, 
                             200, 40, (200, 50, 50), (255, 100, 100), mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_white.collidepoint(event.pos):
                    return chess.WHITE
                elif btn_black.collidepoint(event.pos):
                    return chess.BLACK
                elif btn_back.collidepoint(event.pos):
                    return None

        pygame.display.flip()

def play_vs_ai():
    """Main player vs AI game loop."""
    
    # Display color choice interface
    player_color = choose_player_color()
    if player_color is None:  # User clicked "Back"
        return

    game = ChessGame()
    try:
        engine = Engine()
        print("[INFO] AI engine initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize AI engine: {e}")
        return

    running = True
    suggested_move = None
    promotion_dialog = False
    promotion_from = None
    promotion_to = None
    
    # Biến để theo dõi trạng thái AI
    game.ai_thinking = False
    
    while running:
        # Flip board if player chose black
        flipped = (player_color == chess.BLACK)
        draw_board(screen, menu_background, flipped=flipped)
        draw_pieces(screen, game, images, flipped=flipped)
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw buttons
        btn_undo = draw_button(screen, game_font, "Undo", 10, 675, 100, 40, 
                             (50, 50, 200), (100, 100, 255), mouse_pos)
        btn_help = draw_button(screen, game_font, "Help", 120, 675, 100, 40, 
                             (50, 200, 50), (100, 255, 100), mouse_pos)
        btn_back = draw_button(screen, game_font, "Back", WIDTH - 110, 675, 100, 40, 
                             (200, 50, 50), (255, 100, 100), mouse_pos)
        
        # Draw move hints
        draw_move_hints(screen, game, game.selected_square, flipped=flipped)
        
        # Hiển thị chỉ báo AI đang suy nghĩ
        if game.ai_thinking:
            thinking_text = "AI is thinking" + "." * (int(pygame.time.get_ticks() / 500) % 4)
            draw_text(screen, game_font, thinking_text, WIDTH // 2, 20, color=(255, 0, 0))
        
        # Highlight suggested move if any
        if suggested_move:
            from_square = suggested_move.from_square
            from_col = chess.square_file(from_square)
            from_row = 7 - chess.square_rank(from_square)
            display_from_col = 7 - from_col if flipped else from_col
            display_from_row = 7 - from_row if flipped else from_row
            from_center = (display_from_col * SQUARE_SIZE + SQUARE_SIZE // 2, 
                         display_from_row * SQUARE_SIZE + SQUARE_SIZE // 2)
            pygame.draw.circle(screen, (0, 0, 255), from_center, 20, 3)
            
            to_square = suggested_move.to_square
            to_col = chess.square_file(to_square)
            to_row = 7 - chess.square_rank(to_square)
            display_to_col = 7 - to_col if flipped else to_col
            display_to_row = 7 - to_row if flipped else to_row
            to_center = (display_to_col * SQUARE_SIZE + SQUARE_SIZE // 2, 
                        display_to_row * SQUARE_SIZE + SQUARE_SIZE // 2)
            pygame.draw.circle(screen, (255, 255, 0), to_center, 20, 3)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if promotion_dialog:
                    if btn_queen.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.QUEEN)
                        promotion_dialog = False
                        handle_move_outcome(game, None)
                    elif btn_rook.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.ROOK)
                        promotion_dialog = False
                        handle_move_outcome(game, None)
                    elif btn_bishop.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.BISHOP)
                        promotion_dialog = False
                        handle_move_outcome(game, None)
                    elif btn_knight.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.KNIGHT)
                        promotion_dialog = False
                        handle_move_outcome(game, None)
                else:
                    if btn_undo.collidepoint(event.pos):
                        if len(game.board.move_stack) >= 2:
                            game.undo()  # Undo AI's move
                            game.undo()  # Undo player's move
                        elif len(game.board.move_stack) == 1:
                            game.undo()  # Undo single move
                        suggested_move = None
                    elif btn_help.collidepoint(event.pos):
                        if game.board.turn == player_color:
                            try:
                                engine.set_position(game.board.fen())
                                uci_move = engine.get_best_move()
                                if not uci_move:
                                    print("[WARNING] AI couldn't suggest a move")
                                    continue
                                
                                from_square = chess.square(ord(uci_move[0]) - ord('a'), int(uci_move[1]) - 1)
                                to_square = chess.square(ord(uci_move[2]) - ord('a'), int(uci_move[3]) - 1)
                                promotion = None
                                if len(uci_move) == 5:
                                    promotion_piece = uci_move[4].upper()
                                    promotion = {
                                        'Q': chess.QUEEN,
                                        'R': chess.ROOK,
                                        'B': chess.BISHOP,
                                        'N': chess.KNIGHT
                                    }.get(promotion_piece)
                                suggested_move = chess.Move(from_square, to_square, promotion=promotion)
                            except Exception as e:
                                print(f"[ERROR] Failed to get move suggestion: {e}")
                                continue
                    elif btn_back.collidepoint(event.pos):
                        running = False
                    else:
                        if game.board.turn == player_color:
                            square = get_square_from_mouse(event.pos, flipped=flipped)
                            if square is None:
                                continue
                            
                            if game.selected_square is not None:
                                target_piece = game.get_piece(square)
                                move = chess.Move(game.selected_square, square)
                                if move in game.board.legal_moves:
                                    if game.get_piece(game.selected_square).piece_type == chess.PAWN:
                                        # Check for pawn promotion
                                        if (game.board.turn == chess.WHITE and chess.square_rank(square) == 7) or \
                                           (game.board.turn == chess.BLACK and chess.square_rank(square) == 0):
                                            promotion_dialog = True
                                            promotion_from = game.selected_square
                                            promotion_to = square
                                            continue
                                    
                                    result = game.move(game.selected_square, square)
                                    if result["valid"]:
                                        suggested_move = None
                                        handle_move_outcome(game, target_piece)
                                else:
                                    game.selected_square = square if game.get_piece(square) and game.get_piece(square).color == game.board.turn else None
                            else:
                                piece = game.get_piece(square)
                                game.selected_square = square if piece and piece.color == game.board.turn else None
        
        if promotion_dialog:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            draw_text(screen, game_font, "Choose", WIDTH // 2, HEIGHT // 2 - 150, color=(255, 255, 255))
            btn_queen = draw_button(screen, game_font, "Queen", WIDTH // 2 - 50, HEIGHT // 2 - 100, 
                                  100, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
            btn_rook = draw_button(screen, game_font, "Rook", WIDTH // 2 - 50, HEIGHT // 2 - 40, 
                                 100, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
            btn_bishop = draw_button(screen, game_font, "Bishop", WIDTH // 2 - 50, HEIGHT // 2 + 20, 
                                   100, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
            btn_knight = draw_button(screen, game_font, "Knight", WIDTH // 2 - 50, HEIGHT // 2 + 80, 
                                   100, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
        
        pygame.display.flip()
        
        # Xử lý nước đi của AI trong đa luồng
        if game.board.turn != player_color and not promotion_dialog:
            if not game.ai_thinking:
                # Khởi động luồng AI nếu chưa đang suy nghĩ
                game.ai_thinking = True
                ai_thread = threading.Thread(
                    target=ai_move_thread, 
                    args=(game.board.fen(), engine)
                )
                ai_thread.daemon = True  # Đảm bảo luồng kết thúc khi chương trình chính kết thúc
                ai_thread.start()
            else:
                # Kiểm tra xem AI đã tính toán xong chưa
                try:
                    # Non-blocking check
                    move = ai_move_queue.get_nowait()
                    if move and move in game.board.legal_moves:
                        game.board.push(move)
                        target_piece = game.get_piece(move.to_square)
                        handle_move_outcome(game, target_piece)
                    game.ai_thinking = False
                except queue.Empty:
                    # AI vẫn đang tính toán
                    pass
