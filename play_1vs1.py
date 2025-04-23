import pygame
import chess
from chess_game import ChessGame
from Engine.engine import Engine
from utils import (
    WIDTH, HEIGHT, SQUARE_SIZE, screen, images, menu_background, game_font, sounds,
    draw_board, draw_pieces, draw_button, draw_text,
    draw_move_hints, get_square_from_mouse
)
from notification import handle_move_outcome

def play_1vs1():
    """Main player vs player game loop."""
    game = ChessGame()
    try:
        engine = Engine()
    except Exception as e:
        print(f"[ERROR] Failed to initialize AI engine: {e}")
        return
    
    running = True
    suggested_move = None
    promotion_dialog = False
    promotion_from = None
    promotion_to = None
    
    while running:
        # Flip board based on current turn
        flipped = game.board.turn == chess.BLACK
        
        # Draw board and pieces
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
                        suggested_move = None
                        handle_move_outcome(game, None)
                    elif btn_rook.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.ROOK)
                        promotion_dialog = False
                        suggested_move = None
                        handle_move_outcome(game, None)
                    elif btn_bishop.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.BISHOP)
                        promotion_dialog = False
                        suggested_move = None
                        handle_move_outcome(game, None)
                    elif btn_knight.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.KNIGHT)
                        promotion_dialog = False
                        suggested_move = None
                        handle_move_outcome(game, None)
                    
                else:
                    if btn_undo.collidepoint(event.pos):
                        game.undo()
                        suggested_move = None
                    elif btn_help.collidepoint(event.pos):
                        try:
                            engine.set_position(game.board.fen())
                            move = engine.get_best_move()
                            print(f"[DEBUG] Move type: {type(move)}, Move: {move.uci() if move else None}")
                            if move:
                                suggested_move = move
                            else:
                                print("[WARNING] AI couldn't suggest a move")
                        except Exception as e:
                            print(f"[ERROR] Failed to get move suggestion: {e}")
                    elif btn_back.collidepoint(event.pos):
                        running = False
                    else:
                        square = get_square_from_mouse(event.pos, flipped=flipped)
                        if square is None:
                            continue
                        
                        if game.selected_square is not None:
                            target_piece = game.get_piece(square)
                            move_result = game.move(game.selected_square, square)
                            if move_result["valid"]:
                                if move_result["promotion_required"]:
                                    promotion_dialog = True
                                    promotion_from = game.selected_square
                                    promotion_to = square
                                else:
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