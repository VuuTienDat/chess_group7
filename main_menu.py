import pygame
import sys
from utils import (
    WIDTH, HEIGHT, WHITE, BLACK, HOVER_COLOR,
    screen, menu_background, game_font, sounds,
    draw_text, draw_button
)

def toggle_music():
    """Allow user to adjust music volume using a slider."""
    running = True
    slider_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 20, 300, 40)
    handle_radius = 10
    slider_min = slider_rect.x
    clock = pygame.time.Clock()
    volume = pygame.mixer.music.get_volume()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_x, _ = event.pos
                    back_rect = pygame.Rect(WIDTH//2 - 50, slider_rect.y + slider_rect.height + 40, 100, 40)
                    if back_rect.collidepoint(event.pos):
                        running = False
                    elif slider_rect.collidepoint(event.pos):
                        volume = (mouse_x - slider_min) / slider_rect.width
                        volume = max(0.0, min(volume, 1.0))
                        pygame.mixer.music.set_volume(volume)
            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[0]:
                    mouse_x, _ = event.pos
                    if slider_rect.collidepoint(event.pos):
                        volume = (mouse_x - slider_min) / slider_rect.width
                        volume = max(0.0, min(volume, 1.0))
                        pygame.mixer.music.set_volume(volume)

        screen.blit(menu_background, (0, 0))
        draw_text(screen, game_font, "Adjust Volume", WIDTH//2, 100, color=BLACK)
        
        pygame.draw.rect(screen, (200, 200, 200), slider_rect)
        fill_width = int(slider_rect.width * volume)
        fill_rect = pygame.Rect(slider_min, slider_rect.y, fill_width, slider_rect.height)
        pygame.draw.rect(screen, (100, 100, 100), fill_rect)
        
        handle_x = slider_min + fill_width
        handle_y = slider_rect.y + slider_rect.height // 2
        pygame.draw.circle(screen, (255, 0, 0), (handle_x, handle_y), handle_radius)
        
        back_rect = pygame.Rect(WIDTH//2 - 50, slider_rect.y + slider_rect.height + 40, 100, 40)
        pygame.draw.rect(screen, HOVER_COLOR, back_rect)
        draw_text(screen, game_font, "Back", *back_rect.center, color=WHITE)

        pygame.display.flip()
        clock.tick(60)

def main_menu():
    """Display and handle the main menu interface."""
    from play_1vs1 import play_1vs1
    from play_vs_ai import play_vs_ai
    from play_ai_vs_ai import play_ai_vs_ai

    running = True
    while running:
        screen.blit(menu_background, (0, 0))
        draw_text(screen, game_font, "Chess Game", WIDTH // 2, 80, color=BLACK)

        btn_1v1 = draw_text(screen, game_font, "Play 1 vs 1", WIDTH // 2, 200)
        btn_vs_ai = draw_text(screen, game_font, "Play vs AI", WIDTH // 2, 270)
        btn_ai_vs_ai = draw_text(screen, game_font, "AI vs AI", WIDTH // 2, 340)
        btn_music = draw_text(screen, game_font, "Music", WIDTH // 2, 410)
        btn_quit = draw_text(screen, game_font, "Exit", WIDTH // 2, 480)

        mouse_x, mouse_y = pygame.mouse.get_pos()

        if btn_1v1.collidepoint(mouse_x, mouse_y):
            draw_text(screen, game_font, "Play 1 vs 1", WIDTH // 2, 200, color=HOVER_COLOR)
        if btn_vs_ai.collidepoint(mouse_x, mouse_y):
            draw_text(screen, game_font, "Play vs AI", WIDTH // 2, 270, color=HOVER_COLOR)
        if btn_ai_vs_ai.collidepoint(mouse_x, mouse_y):
            draw_text(screen, game_font, "AI vs AI", WIDTH // 2, 340, color=HOVER_COLOR)
        if btn_music.collidepoint(mouse_x, mouse_y):
            draw_text(screen, game_font, "Music", WIDTH // 2, 410, color=HOVER_COLOR)
        if btn_quit.collidepoint(mouse_x, mouse_y):
            draw_text(screen, game_font, "Exit", WIDTH // 2, 480, color=HOVER_COLOR)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_1v1.collidepoint(event.pos):
                    play_1vs1()
                elif btn_vs_ai.collidepoint(event.pos):
                    play_vs_ai()
                elif btn_ai_vs_ai.collidepoint(event.pos):
                    play_ai_vs_ai()
                elif btn_music.collidepoint(event.pos):
                    toggle_music()
                elif btn_quit.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

if __name__ == "__main__":
    from game import init_game
    init_game()
    main_menu()