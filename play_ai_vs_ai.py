import pygame
import chess
from chess_game import ChessGame
from Engine.engine import Engine
from utils import (
    WIDTH, HEIGHT, screen, images, menu_background, game_font, sounds,
    draw_board, draw_pieces, draw_button
)
from notification import handle_move_outcome

def play_ai_vs_ai():
    """Main AI vs AI game loop."""
    game = ChessGame()
    try:
        engine_white = Engine()  # Engine for white pieces
        engine_black = Engine()  # Engine for black pieces
        print("[INFO] Both AI engines initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize AI engines: {e}")
        return

    running = True
    move_delay = 1000  # Delay between moves in milliseconds
    last_move_time = pygame.time.get_ticks()
    
    while running:
        # Draw board and pieces
        draw_board(screen, menu_background)
        draw_pieces(screen, game, images)
        
        mouse_pos = pygame.mouse.get_pos()
        btn_back = draw_button(screen, game_font, "Back", WIDTH - 110, 675, 100, 40, 
                             (200, 50, 50), (255, 100, 100), mouse_pos)
        
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event.pos):
                    running = False
                    
        # Make AI moves with delay
        if current_time - last_move_time >= move_delay:
            if game.board.is_game_over():
                if game.board.is_checkmate():
                    winner = "White" if game.board.turn == chess.BLACK else "Black"
                    handle_move_outcome(game, None)
                elif game.board.is_stalemate():
                    handle_move_outcome(game, None)
                elif game.board.is_insufficient_material():
                    handle_move_outcome(game, None)
                else:
                    handle_move_outcome(game, None)
                game.board.reset()
            else:
                # Get current engine based on turn
                current_engine = engine_white if game.board.turn == chess.WHITE else engine_black
                
                # Get AI move
                try:
                    current_engine.set_position(game.board.fen())
                    uci_move = current_engine.get_best_move()
                    
                    if not uci_move:
                        print("[WARNING] AI couldn't find a move")
                        continue
                except Exception as e:
                    print(f"[ERROR] Failed to get AI move: {e}")
                    continue

                if uci_move:
                    from_square = chess.square(
                        ord(uci_move[0]) - ord('a'),
                        int(uci_move[1]) - 1
                    )
                    to_square = chess.square(
                        ord(uci_move[2]) - ord('a'),
                        int(uci_move[3]) - 1
                    )
                    
                    # Initialize promotion as None by default
                    promotion = None
                    
                    # Handle promotion
                    if len(uci_move) == 5:
                        promotion_piece = uci_move[4].upper()
                        promotion = {
                            'Q': chess.QUEEN,
                            'R': chess.ROOK,
                            'B': chess.BISHOP,
                            'N': chess.KNIGHT
                        }.get(promotion_piece)
                    
                    # Create move object for validation
                    move = chess.Move(from_square, to_square, promotion=promotion)
                    
                    if move in game.board.legal_moves:
                        result = game.move(from_square, to_square, promotion)
                        if result["valid"]:
                            target_piece = game.get_piece(to_square)
                            handle_move_outcome(game, target_piece)
                            last_move_time = current_time
        
        pygame.display.flip()