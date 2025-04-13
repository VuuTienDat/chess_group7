import pygame
import chess
from chess_game import ChessGame
import sys
import os

if getattr(sys, 'frozen', False):  # Đang chạy từ .exe
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

# Sử dụng bundle_dir để tham chiếu đến các file bên trong .exe
music_path = os.path.join(bundle_dir, "Music")
image_path = os.path.join(bundle_dir, "Image")
font_path = os.path.join(bundle_dir, "Font")
WIDTH, HEIGHT = 640, 720
SQUARE_SIZE = WIDTH // 8

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Game")
pygame.mixer.init()

# Đảm bảo bạn tham chiếu đúng các tài nguyên từ sys._MEIPASS
pygame.mixer.music.load(os.path.join(music_path, "chessmusic.mp3"))  # đường dẫn tới file nhạc
pygame.mixer.music.play(-1)  # lặp vô hạn
music_on = True  # Biến để kiểm soát trạng thái nhạc
move_sound = pygame.mixer.Sound(os.path.join(music_path, "Move.mp3"))
capture_sound = pygame.mixer.Sound(os.path.join(music_path, "Capture.mp3"))
check_sound = pygame.mixer.Sound(os.path.join(music_path, "Check.mp3"))
checkmate_sound = pygame.mixer.Sound(os.path.join(music_path, "Checkmate.mp3"))

board_colors = [(240, 217, 181), (181, 136, 99)]

# Load ảnh quân cờ từ sys._MEIPASS
images = {}
pieces = ["P", "N", "B", "R", "Q", "K"]
for color in ["w", "b"]:
    for p in pieces:
        name = color + p
        images[name] = pygame.transform.scale(
            pygame.image.load(os.path.join(image_path, f"{name}.png")), (SQUARE_SIZE, SQUARE_SIZE)
        )

FONT = pygame.font.Font(os.path.join(font_path, "turok.ttf"), 40)  # Cập nhật đường dẫn font
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
MENU_COLOR = (100, 100, 100)  # Default button color
HOVER_COLOR = (255, 0, 0)     # Hover color for buttons
menu_background = pygame.image.load(os.path.join(image_path, "landscape4.png"))
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

def evaluate_board(board):
    piece_values = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
    }
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values.get(piece.symbol().upper(), 0)
            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value
    return score
def minimax(board, depth, maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    legal_moves = list(board.legal_moves)
    if maximizing_player:
        max_eval = float('-inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, False)  # Tới lượt đối thủ
            max_eval = max(max_eval, eval)
            board.pop()
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, True)  # Tới lượt mình
            min_eval = min(min_eval, eval)
            board.pop()
        return min_eval
def iterative_deepening(board, max_depth):
    best_move = None
    for depth in range(1, max_depth + 1):
        best_eval = float('-inf')
        legal_moves = list(board.legal_moves)
        for move in legal_moves:
            board.push(move)
            move_eval = minimax(board, depth - 1, False)
            if move_eval > best_eval:
                best_eval = move_eval
                best_move = move
            board.pop()
    return best_move
def notification(message):
    text = FONT.render(message, True, (255, 0, 0))
    rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    while True:
        screen.blit(menu_background, (0, 0))
        screen.blit(text, rect)
        mouse_pos = pygame.mouse.get_pos()
        btn_back = draw_button("Back", WIDTH - 110, 660, 100, 40, (200, 50, 50), (255, 100, 100), mouse_pos)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                return  # người chơi nhấn phím để thoát khỏi hàm
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event.pos):
                    main_menu()  # Quay lại menu chính

        
        
        pygame.display.flip()


def play_vs_ai():
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
            draw_move_hints(game, selected)

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
                    target_piece = game.get_piece(square)
                    move_successful = game.move(selected, square)

                    if move_successful:
                        if game.board.is_checkmate():  # Nếu chiếu hết
                            checkmate_sound.play()
                        if target_piece:  # Nếu có quân → ăn quân
                            capture_sound.play()
                        else: move_sound.play()  # Nếu không có quân → đi quân
                        
                        if game.board.is_check():  # Sau khi đi xong, kiểm tra chiếu
                            check_sound.play()
                        selected = None
                    else:
                        selected = square if piece and piece.color == game.board.turn else None
                else:
                    selected = square if piece and piece.color == game.board.turn else None

        # AI đưa ra nước đi khi đến lượt của nó
        if game.board.turn == chess.BLACK:  # AI chơi màu đen
            best_move = iterative_deepening(game.board, 3)  # Giới hạn độ sâu tối đa là 3
            if best_move:
                game.board.push(best_move)
                
            else:
                if game.board.is_checkmate():
                    notification("Checkmate! You lost.")
                elif game.board.is_stalemate():
                    notification("Stalemate!")
                elif game.board.is_insufficient_material():
                    notification("Draw: Insufficient material.")
                else:
                    notification("No legal move. Game Over.")

                # reset board nếu muốn chơi lại
                game.board.reset()

        pygame.display.flip()

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
                            notification("Checkmate!")
                        elif game.board.is_stalemate():  # Nếu hòa thế cờ
                            notification("Stalemate!")
                        elif game.board.is_insufficient_material():  # Nếu hòa do thiếu quân
                            notification("Draw: Insufficient material.")
                        if target_piece:  # Nếu có quân → ăn quân
                            capture_sound.play()
                        else: move_sound.play()  # Nếu không có quân → đi quân
                        
                        if game.board.is_check():  # Sau khi đi xong, kiểm tra chiếu
                            check_sound.play()
                        
                        selected = None
                    else:
                        selected = square if piece and piece.color == game.board.turn else None
                else:
                    selected = square if piece and piece.color == game.board.turn else None
        pygame.display.flip()



# ------------------- MENU --------------------
def main_menu():
    running = True
    while running:
        screen.blit(menu_background, (0, 0))
        title = FONT.render("Chess Game", True, BLACK)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))

        btn_1v1 = draw_text("Play 1 vs 1", WIDTH // 2, 200)
        btn_vs_ai = draw_text("Play vs AI", WIDTH // 2, 270)
        btn_music = draw_text("Music", WIDTH // 2, 340)
        btn_quit = draw_text("Exit", WIDTH // 2, 410)

        mouse_x, mouse_y = pygame.mouse.get_pos()

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
                    play_vs_ai()
                elif btn_music.collidepoint(event.pos):
                    toggle_music()
                elif btn_quit.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
def toggle_music():
    global music_on
    music_on = not music_on
    if music_on:
        pygame.mixer.music.unpause()
    else:
        pygame.mixer.music.pause()
if __name__ == "__main__":
    main_menu()
