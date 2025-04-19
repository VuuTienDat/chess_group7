import pygame
import chess

# Global resources (initialized by game.py)
screen = None
game_font = None
menu_background = None
images = {}
sounds = {}

# Paths (set by game.py)
MUSIC_PATH = None
IMAGE_PATH = None
FONT_PATH = None

# Global resources (set by game.py)
screen = None
images = None
menu_background = None
game_font = None
sounds = None

# Display constants
WIDTH, HEIGHT = 640, 720
SQUARE_SIZE = WIDTH // 8

# Colors
BOARD_COLORS = [(240, 217, 181), (181, 136, 99)]
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
MENU_COLOR = (100, 100, 100)
HOVER_COLOR = (255, 0, 0)

# Initialize pygame
pygame.init()


def draw_text(screen, font, text, x, y, center=True, color=BLACK):
    """Draw text on screen with optional centering."""
    label = font.render(text, True, color)
    rect = label.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(label, rect)
    return rect

def draw_board(screen, menu_background, flipped=False):
    """Draw the chess board with optional flipping."""
    font = pygame.font.SysFont('arial', 20)
    screen.blit(menu_background, (0, 0))
    
    for row in range(8):
        for col in range(8):
            display_row = 7 - row if flipped else row
            display_col = 7 - col if flipped else col
            color = BOARD_COLORS[(row + col) % 2]
            pygame.draw.rect(screen, color, 
                           (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE, 
                            SQUARE_SIZE, SQUARE_SIZE))

    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']

    if flipped:
        files = files[::-1]
        ranks = ranks[::-1]

    for col in range(8):
        label = font.render(files[col], True, BLACK)
        screen.blit(label, (col * SQUARE_SIZE + SQUARE_SIZE // 2 - 10, 
                           8 * SQUARE_SIZE + 5))

    for row in range(8):
        label = font.render(ranks[row], True, BLACK)
        screen.blit(label, (5, row * SQUARE_SIZE + SQUARE_SIZE // 2 - 10))

def draw_pieces(screen, game, images, flipped=False):
    """Draw chess pieces on the board."""
    for square in chess.SQUARES:
        piece = game.get_piece(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            display_col = 7 - col if flipped else col
            display_row = 7 - row if flipped else row
            name = ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()
            screen.blit(images[name], (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE))

def draw_button(screen, font, text, x, y, w, h, color, hover_color, mouse_pos):
    """Draw an interactive button."""
    rect = pygame.Rect(x, y, w, h)
    if rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, hover_color, rect)
    else:
        pygame.draw.rect(screen, color, rect)
    draw_text(screen, font, text, x + w // 2, y + h // 2, center=True, color=WHITE)
    return rect

def get_square_from_mouse(pos, flipped=False):
    """Convert mouse position to chess square coordinates."""
    x, y = pos
    col = x // SQUARE_SIZE
    row = y // SQUARE_SIZE
    
    if flipped:
        col = 7 - col
        row = 7 - row
    row = 7 - row
    
    if not (0 <= col < 8 and 0 <= row < 8):
        return None
    return chess.square(col, row)

def draw_move_hints(screen, game, selected_square, flipped=False):
    """Draw circles indicating legal moves for selected piece."""
    if selected_square is None:
        return
    for move in game.board.legal_moves:
        if move.from_square == selected_square:
            to_square = move.to_square
            col = chess.square_file(to_square)
            row = 7 - chess.square_rank(to_square)
            display_col = 7 - col if flipped else col
            display_row = 7 - row if flipped else row
            center = (display_col * SQUARE_SIZE + SQUARE_SIZE // 2, 
                     display_row * SQUARE_SIZE + SQUARE_SIZE // 2)
            pygame.draw.circle(screen, (120, 150, 100), center, 15)