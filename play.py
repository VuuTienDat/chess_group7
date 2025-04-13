import pygame
import sys
import os
import chess

# Khởi tạo Pygame
pygame.init()
WIDTH, HEIGHT = 640, 720
SQUARE_SIZE = WIDTH // 8
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Game")

# Xác định đường dẫn tài nguyên
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

# Màu sắc
BOARD_COLORS = [(240, 217, 181), (181, 136, 99)]
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
MENU_COLOR = (100, 100, 100)
HOVER_COLOR = (255, 0, 0)

# Tải tài nguyên
image_path = os.path.join(bundle_dir, "Image")
font_path = os.path.join(bundle_dir, "Font")
menu_background = pygame.transform.scale(
    pygame.image.load(os.path.join(image_path, "landscape4.png")), (WIDTH, HEIGHT)
)
FONT = pygame.font.Font(os.path.join(font_path, "turok.ttf"), 40)

# Tải ảnh quân cờ
PIECES = ["wp", "wn", "wb", "wr", "wq", "wk", "bp", "bn", "bb", "br", "bq", "bk"]
images = {}
for piece in PIECES:
    images[piece] = pygame.transform.scale(
        pygame.image.load(os.path.join(image_path, f"{piece}.png")), (SQUARE_SIZE, SQUARE_SIZE)
    )

# Lớp quản lý trò chơi
class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.move_history = []
        self.selected_square = None

    def get_piece(self, square):
        return self.board.piece_at(square)

    def get_legal_moves(self, square):
        return [move for move in self.board.legal_moves if move.from_square == square]

    def move(self, from_square, to_square):
        move = chess.Move(from_square, to_square)
        # Xử lý phong hậu cho tốt
        piece = self.get_piece(from_square)
        if piece and piece.piece_type == chess.PAWN:
            if chess.square_rank(to_square) in (0, 7):
                move = chess.Move(from_square, to_square, promotion=chess.QUEEN)
        if move in self.board.legal_moves:
            self.move_history.append(self.board.fen())
            self.board.push(move)
            return True
        return False

    def undo(self):
        if self.move_history:
            last_fen = self.move_history.pop()
            self.board.set_fen(last_fen)
            self.selected_square = None

# Hàm vẽ
def draw_board():
    for row in range(8):
        for col in range(8):
            color = BOARD_COLORS[(row + col) % 2]
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces(game):
    for square in range(64):
        piece = game.get_piece(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            piece_name = ("w" if piece.color == chess.WHITE else "b") + piece.symbol().lower()
            screen.blit(images[piece_name], (col * SQUARE_SIZE, row * SQUARE_SIZE))

def draw_move_hints(game, selected_square):
    if selected_square is not None:
        for move in game.get_legal_moves(selected_square):
            to_square = move.to_square
            col = chess.square_file(to_square)
            row = 7 - chess.square_rank(to_square)
            center = (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2)
            pygame.draw.circle(screen, (120, 150, 100), center, 15)

def draw_text(text, x, y, center=True, color=BLACK):
    label = FONT.render(text, True, color)
    rect = label.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(label, rect)
    return rect

def draw_button(text, x, y, w, h, color, hover_color, mouse_pos):
    rect = pygame.Rect(x, y, w, h)
    if rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, hover_color, rect)
    else:
        pygame.draw.rect(screen, color, rect)
    draw_text(text, x + w // 2, y + h // 2, center=True, color=WHITE)
    return rect

# Hàm thông báo
def notification(game, message):
    while True:
        screen.blit(menu_background, (0, 0))
        draw_text(message, WIDTH // 2, HEIGHT // 2, color=(255, 0, 0))
        mouse_pos = pygame.mouse.get_pos()
        btn_back = draw_button("Back", WIDTH - 110, 660, 100, 40, (200, 50, 50), (255, 100, 100), mouse_pos)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event.pos):
                    game.board.reset()
                    game.move_history.clear()
                    return
        pygame.display.flip()

# Chế độ chơi 1 vs 1
def play_1vs1():
    game = ChessGame()
    running = True
    while running:
        draw_board()
        draw_pieces(game)
        mouse_pos = pygame.mouse.get_pos()
        btn_undo = draw_button("Undo", 10, 660, 100, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
        btn_back = draw_button("Back", WIDTH - 110, 660, 100, 40, (200, 50, 50), (255, 100, 100), mouse_pos)
        draw_move_hints(game, game.selected_square)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_undo.collidepoint(event.pos):
                    game.undo()
                elif btn_back.collidepoint(event.pos):
                    running = False
                else:
                    x, y = event.pos
                    col = x // SQUARE_SIZE
                    row = 7 - (y // SQUARE_SIZE)
                    if not (0 <= col < 8 and 0 <= row < 8):
                        continue
                    square = chess.square(col, row)
                    piece = game.get_piece(square)
                    
                    if game.selected_square is not None:
                        if game.move(game.selected_square, square):
                            if game.board.is_checkmate():
                                winner = "White" if game.board.turn == chess.BLACK else "Black"
                                notification(game, f"Checkmate! {winner} wins!")
                            elif game.board.is_stalemate():
                                notification(game, "Stalemate!")
                            elif game.board.is_insufficient_material():
                                notification(game, "Draw: Insufficient material!")
                            elif game.board.is_seventyfive_moves():
                                notification(game, "Draw: 75-move rule!")
                            elif game.board.is_fivefold_repetition():
                                notification(game, "Draw: Fivefold repetition!")
                            game.selected_square = None
                        else:
                            game.selected_square = square if piece and piece.color == game.board.turn else None
                    else:
                        game.selected_square = square if piece and piece.color == game.board.turn else None
        
        pygame.display.flip()

# Menu chính
def main_menu():
    running = True
    while running:
        screen.blit(menu_background, (0, 0))
        draw_text("Chess Game", WIDTH // 2, 80, color=BLACK)
        btn_1v1 = draw_text("Play 1 vs 1", WIDTH // 2, 200)
        btn_quit = draw_text("Exit", WIDTH // 2, 270)
        mouse_pos = pygame.mouse.get_pos()
        if btn_1v1.collidepoint(mouse_pos):
            draw_text("Play 1 vs 1", WIDTH // 2, 200, color=HOVER_COLOR)
        if btn_quit.collidepoint(mouse_pos):
            draw_text("Exit", WIDTH // 2, 270, color=HOVER_COLOR)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_1v1.collidepoint(event.pos):
                    play_1vs1()
                elif btn_quit.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
        pygame.display.flip()

if __name__ == "__main__":
    main_menu()