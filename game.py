import pygame
import chess
from chess_game import ChessGame
import sys

WIDTH, HEIGHT = 640, 720
SQUARE_SIZE = WIDTH // 8

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Game")
pygame.mixer.init()
pygame.mixer.music.load("Music/chessmusic.mp3")  # đường dẫn tới file nhạc
pygame.mixer.music.play(-1)  # lặp vô hạn
music_on = True  # Biến để kiểm soát trạng thái nhạc
move_sound = pygame.mixer.Sound("Music/Move.mp3")
capture_sound = pygame.mixer.Sound("Music/Capture.mp3")
check_sound = pygame.mixer.Sound("Music/Check.mp3")
checkmate_sound = pygame.mixer.Sound("Music/Checkmate.mp3")
# move_sound.set_volume(0.5)  # Giảm âm lượng xuống 50%
# pygame.mixer.music.set_volume(0.5)  # Giảm âm lượng nhạc xuống 50%
board_colors = [(240, 217, 181), (181, 136, 99)]

# Load ảnh quân cờ
images = {}
pieces = ["P", "N", "B", "R", "Q", "K"]
for color in ["w", "b"]:
    for p in pieces:
        name = color + p
        images[name] = pygame.transform.scale(
            pygame.image.load(f"Image/{name}.png"), (SQUARE_SIZE, SQUARE_SIZE)
        )

FONT = pygame.font.Font("Font/turok.ttf",40)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
MENU_COLOR = (100, 100, 100)  # Default button color
HOVER_COLOR = (255, 0, 0)     # Hover color for buttons
menu_background = pygame.image.load("Image/landscape4.png")
menu_background = pygame.transform.scale(menu_background, (WIDTH, HEIGHT))

def draw_text(text, x, y, center=True, color=BLACK):
    label = FONT.render(text, True, color)
    rect = label.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(label, rect)
    return rect

def draw_board():
    for row in range(8):
        for col in range(8):
            color = board_colors[(row + col) % 2]
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces(game):
    for square in chess.SQUARES:
        piece = game.get_piece(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            name = ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()
            screen.blit(images[name], (col * SQUARE_SIZE, row * SQUARE_SIZE))

def get_square_from_mouse(pos):
    x, y = pos
    col = x // SQUARE_SIZE
    row = 7 - (y // SQUARE_SIZE)
    return chess.square(col, row)
def draw_move_hints(game, selected_square):
    for move in game.board.legal_moves:
        if move.from_square == selected_square:
            to_square = move.to_square
            col = chess.square_file(to_square)
            row = 7 - chess.square_rank(to_square)
            center = (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2)
            pygame.draw.circle(screen, (120, 150, 100), center, 15)

def draw_button(text, x, y, w, h, color, hover_color, mouse_pos):
    rect = pygame.Rect(x, y, w, h)
    if rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, hover_color, rect)
    else:
        pygame.draw.rect(screen, color, rect)
    draw_text(text, x + w // 2, y + h // 2, center=True, color=WHITE)
    return rect


def play_1vs1():
    game = ChessGame()
    selected = None
    running = True
    while running:
        
        draw_board()
        draw_pieces(game)
        mouse_pos = pygame.mouse.get_pos()
        btn_undo = draw_button("Undo", 10, 660, 100, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
        btn_back = draw_button("Back", WIDTH - 110, 660, 100, 40, (200, 50, 50), (255, 100, 100), mouse_pos)

        if selected:
            draw_move_hints(game, selected)  # <-- Thêm dòng này ở đây
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit() 
           

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_undo.collidepoint(event.pos):
                    game.undo()  
                elif btn_back.collidepoint(event.pos):
                    running = False

                square = get_square_from_mouse(event.pos)
                piece = game.get_piece(square)

                if selected:                   
                    # Kiểm tra nếu có quân ở ô đích trước khi đi
                    target_piece = game.get_piece(square)
                    move_successful = game.move(selected, square)

                    if move_successful:
                        if game.board.is_checkmate():  # Nếu chiếu hết
                            checkmate_sound.play()
                        elif target_piece:  # Nếu có quân → ăn quân
                            capture_sound.play()
                        elif game.board.is_check():  # Sau khi đi xong, kiểm tra chiếu
                            check_sound.play()
                        else:
                            move_sound.play()
                        selected = None
                    else:
                        selected = square if piece and piece.color == game.board.turn else None
                else:
                    selected = square if piece and piece.color == game.board.turn else None
        pygame.display.flip()



# ------------------- MENU --------------------
running = True
while running:
    screen.blit(menu_background, (0, 0))
    title = FONT.render("Chess Game", True, BLACK)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))

    # Draw the buttons and check if the mouse is hovering over them
    btn_1v1 = draw_text("Play 1 vs 1", WIDTH // 2, 200)
    btn_vs_ai = draw_text("Play vs AI", WIDTH // 2, 270)
    btn_music = draw_text("Music", WIDTH // 2, 340)
    btn_quit = draw_text("Exit", WIDTH // 2, 410)

    # Get mouse position
    mouse_x, mouse_y = pygame.mouse.get_pos()

    # Check if the mouse is hovering over any button and change color
    if btn_1v1.collidepoint(mouse_x, mouse_y):
        draw_text("Play 1 vs 1", WIDTH // 2, 200, color=HOVER_COLOR)
    if btn_vs_ai.collidepoint(mouse_x, mouse_y):
        draw_text("Play vs AI", WIDTH // 2, 270, color=HOVER_COLOR)
    if btn_music.collidepoint(mouse_x, mouse_y):
        draw_text("Music", WIDTH // 2, 340, color=HOVER_COLOR)
    if btn_quit.collidepoint(mouse_x, mouse_y):
        draw_text("Exit", WIDTH // 2, 410, color=HOVER_COLOR)

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if btn_1v1.collidepoint(event.pos):
                play_1vs1()
            elif btn_vs_ai.collidepoint(event.pos):
                print("Start vs AI (chưa làm)")
            elif btn_music.collidepoint(event.pos):
                print("Toggle Music (chưa làm)")
                music_on = not music_on
                if music_on:
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.pause()
            elif btn_quit.collidepoint(event.pos):
                pygame.quit()
                sys.exit()

pygame.quit()
sys.exit()
