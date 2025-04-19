import pygame
import sys
import chess
from utils import (
    WIDTH, HEIGHT, screen, menu_background, game_font,
    sounds, WHITE, draw_text, draw_button
)

def show_notification(game, message):
    """Display a notification message with a back button."""
    color = (255, 0, 0)  # Default red color for notifications
    while True:
        screen.blit(menu_background, (0, 0))
        draw_text(screen, game_font, message, WIDTH // 2, HEIGHT // 2, color=color)
        mouse_pos = pygame.mouse.get_pos()
        btn_back = draw_button(screen, game_font, "Back", WIDTH - 110, 660, 100, 40,
                             (200, 50, 50), (255, 100, 100), mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event.pos):
                    game.board.reset()
                    game.move_history.clear()
                    from main_menu import main_menu
                    main_menu()
                    
        pygame.display.flip()

def handle_move_outcome(game, target_piece=None):
    """Handle the outcome of a move (checkmate, stalemate, etc)."""

    if game.board.is_checkmate():
        sounds['checkmate'].play()
        winner = "White" if game.board.turn == chess.BLACK else "Black"
        show_notification(game, f"Checkmate! {winner} wins!")
    elif game.board.is_stalemate():
        show_notification(game, "Stalemate!")
    elif game.board.is_insufficient_material():
        show_notification(game, "Draw: Insufficient material!")
    elif game.board.is_seventyfive_moves():
        show_notification(game, "Draw: 75 move rule!")
    elif game.board.is_fivefold_repetition():
        show_notification(game, "Draw: Fivefold repetition!")
    
    if target_piece:
        sounds['capture'].play()
    else:
        sounds['move'].play()
    if game.board.is_check():
        sounds['check'].play()
    game.selected_square = None