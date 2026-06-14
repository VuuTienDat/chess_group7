import pygame
import chess
import chess.pgn
from chess_game import ChessGame
import sys
import os
import time
import math

# Đường dẫn tới Engine
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Engine"))
from Engine.engine import Engine

# Xử lý đường dẫn tài nguyên
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

music_path = os.path.join(bundle_dir, "Music")
image_path = os.path.join(bundle_dir, "Image")
font_path = os.path.join(bundle_dir, "Font")

# Kích thước cửa sổ
WIDTH, HEIGHT = 640, 640
BOARD_WIDTH = 400
CONSOLE_WIDTH = 200
SQUARE_SIZE = BOARD_WIDTH // 8
MARGIN = 20

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bot vs Bot - 1 Game")
pygame.mixer.init()

# Tải nhạc và âm thanh (âm lượng = 0)
pygame.mixer.music.load(os.path.join(music_path, "chessmusic.mp3"))
pygame.mixer.music.set_volume(0.0)
pygame.mixer.music.play(-1)
move_sound = pygame.mixer.Sound(os.path.join(music_path, "Move.mp3"))
move_sound.set_volume(0.0)
capture_sound = pygame.mixer.Sound(os.path.join(music_path, "Capture.mp3"))
capture_sound.set_volume(0.0)
check_sound = pygame.mixer.Sound(os.path.join(music_path, "Check.mp3"))
check_sound.set_volume(0.0)
checkmate_sound = pygame.mixer.Sound(os.path.join(music_path, "Checkmate.mp3"))
checkmate_sound.set_volume(0.0)

# Thiết lập bàn cờ và quân cờ
board_colors = [(255, 255, 255), (0, 100, 0)]
images = {}
pieces = ["P", "N", "B", "R", "Q", "K"]
for color in ["w", "b"]:
    for p in pieces:
        name = color + p
        images[name] = pygame.transform.scale(
            pygame.image.load(os.path.join(image_path, f"{name}.png")), (SQUARE_SIZE, SQUARE_SIZE)
        )

# Font chữ
FONT = pygame.font.Font(os.path.join(font_path, "turok.ttf"), 40)
VICTORY_FONT = pygame.font.Font(os.path.join(font_path, "turok.ttf"), 30)
CONSOLE_FONT = pygame.font.SysFont('arial', 16)
BOARD_LABEL_FONT = pygame.font.SysFont('arial', 12)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CONSOLE_BG = (50, 50, 50)
LABEL_COLOR = (0, 0, 0)
BORDER_COLOR = (150, 150, 150)
MESSAGE_BG = (0, 0, 0, 180)

# Tải background
menu_background = pygame.image.load(os.path.join(image_path, "landscape3.jpg"))
menu_background = pygame.transform.scale(menu_background, (WIDTH, HEIGHT))

def draw_text(text, x, y, font=FONT, center=True, color=BLACK, outline_color=None):
    label = font.render(text, True, color)
    rect = label.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    if outline_color:
        outline = font.render(text, True, outline_color)
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                if dx != 0 or dy != 0:
                    outline_rect = outline.get_rect(center=(x + dx, y + dy))
                    screen.blit(outline, outline_rect)
    screen.blit(label, rect)
    return rect

def draw_board(x_offset, y_offset, game, message=""):
    pygame.draw.rect(screen, BORDER_COLOR,
                     (x_offset - 2, y_offset - 2, BOARD_WIDTH + 4, BOARD_WIDTH + 4))
    for row in range(8):
        for col in range(8):
            color = board_colors[(row + col) % 2]
            pygame.draw.rect(screen, color,
                             (x_offset + col * SQUARE_SIZE, y_offset + row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    for col in range(8):
        label = BOARD_LABEL_FONT.render(files[col], True, LABEL_COLOR)
        screen.blit(label, (x_offset + col * SQUARE_SIZE + 2, y_offset + (7 * SQUARE_SIZE) + SQUARE_SIZE - 15))
    for row in range(8):
        label = BOARD_LABEL_FONT.render(ranks[row], True, LABEL_COLOR)
        screen.blit(label, (x_offset + 2, y_offset + row * SQUARE_SIZE + 2))

    if message:
        message_surface = pygame.Surface((BOARD_WIDTH - 20, 60), pygame.SRCALPHA)
        message_surface.fill(MESSAGE_BG)
        screen.blit(message_surface, (x_offset + 10, y_offset + BOARD_WIDTH // 2 - 30))
        color = WHITE if "Bot1 Wins" in message else BLACK if "Bot2 Wins" in message else WHITE
        outline = WHITE if color == BLACK else None
        draw_text(message, x_offset + BOARD_WIDTH // 2, y_offset + BOARD_WIDTH // 2,
                  font=VICTORY_FONT, color=color, outline_color=outline)

def draw_pieces(game, x_offset, y_offset):
    for square in chess.SQUARES:
        piece = game.get_piece(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            name = ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()
            screen.blit(images[name], (x_offset + col * SQUARE_SIZE, y_offset + row * SQUARE_SIZE))

def draw_console(game, bot1_stats, bot2_stats, mouse_pos, bot1_color):
    pygame.draw.rect(screen, CONSOLE_BG, (BOARD_WIDTH + 2 * MARGIN, 0, CONSOLE_WIDTH, HEIGHT))
    y_offset = 10

    turn = "White" if game.board.turn == chess.WHITE else "Black"
    turn_color = WHITE if turn == "White" else (150, 150, 150)
    turn_label = CONSOLE_FONT.render("Turn: ", True, WHITE)
    turn_value = CONSOLE_FONT.render(turn, True, turn_color)
    screen.blit(turn_label, (BOARD_WIDTH + 2 * MARGIN + 10, y_offset))
    screen.blit(turn_value, (BOARD_WIDTH + 2 * MARGIN + 10 + turn_label.get_width(), y_offset))

    y_offset += 20
    possible_moves = len(list(game.board.legal_moves))
    draw_text(f"Moves: {possible_moves}", BOARD_WIDTH + 2 * MARGIN + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 20
    in_check = game.board.is_check()
    draw_text(f"Check: {in_check}", BOARD_WIDTH + 2 * MARGIN + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 20
    bot1_label = CONSOLE_FONT.render(f"Bot1 ({'White' if bot1_color == chess.WHITE else 'Black'})", True, WHITE)
    screen.blit(bot1_label, (BOARD_WIDTH + 2 * MARGIN + 10, y_offset))

    y_offset += 20
    bot1_depth = bot1_stats.get("depth", "-")
    draw_text(f"Depth: {bot1_depth}", BOARD_WIDTH + 2 * MARGIN + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 20
    bot1_score = bot1_stats.get("score", "-")
    draw_text(f"Score: {bot1_score}", BOARD_WIDTH + 2 * MARGIN + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 25
    bot2_label = CONSOLE_FONT.render(f"Bot2 ({'White' if bot1_color == chess.BLACK else 'Black'})", True, WHITE)
    screen.blit(bot2_label, (BOARD_WIDTH + 2 * MARGIN + 10, y_offset))

    y_offset += 20
    bot2_depth = bot2_stats.get("depth", "-")
    draw_text(f"Depth: {bot2_depth}", BOARD_WIDTH + 2 * MARGIN + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 20
    bot2_score = bot2_stats.get("score", "-")
    draw_text(f"Score: {bot2_score}", BOARD_WIDTH + 2 * MARGIN + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    btn_back = draw_button("Back", BOARD_WIDTH + 2 * MARGIN + 50, HEIGHT - 60, 100, 30, (200, 50, 50), (255, 100, 100), mouse_pos)
    return btn_back

def draw_button(text, x, y, w, h, color, hover_color, mouse_pos, text_color=WHITE):
    rect = pygame.Rect(x, y, w, h)
    if rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, hover_color, rect)
    else:
        pygame.draw.rect(screen, color, rect)
    draw_text(text, x + w // 2, y + h // 2, center=True, color=text_color, font=CONSOLE_FONT)
    return rect

def show_results(bot1_wins, draws, bot2_wins, bot1_elo, pgn_file):
    while True:
        screen.blit(menu_background, (0, 0))
        y_offset = 100
        draw_text("Match Results", WIDTH // 2, y_offset, font=FONT, color=BLACK)
        y_offset += 60
        draw_text(f"Bot1 Wins: {bot1_wins}", WIDTH // 2, y_offset, font=CONSOLE_FONT, color=WHITE)
        y_offset += 30
        draw_text(f"Draws: {draws}", WIDTH // 2, y_offset, font=CONSOLE_FONT, color=WHITE)
        y_offset += 30
        draw_text(f"Bot2 Wins: {bot2_wins}", WIDTH // 2, y_offset, font=CONSOLE_FONT, color=WHITE)
        y_offset += 30
        draw_text(f"Bot1 ELO: {bot1_elo:.0f}", WIDTH // 2, y_offset, font=CONSOLE_FONT, color=WHITE)
        y_offset += 30
        draw_text(f"PGN: {os.path.basename(pgn_file)}", WIDTH // 2, y_offset, font=CONSOLE_FONT, color=WHITE)
        mouse_pos = pygame.mouse.get_pos()
        btn_back = draw_button("Back", WIDTH - 110, HEIGHT - 50, 100, 40, (200, 50, 50), (255, 100, 100), mouse_pos)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event.pos):
                    main_menu()
        pygame.display.flip()

def calculate_elo(wins, draws, losses, opponent_elo=2000):
    if losses + 0.5 * draws == 0:
        return opponent_elo
    performance_ratio = (wins + 0.5 * draws) / (losses + 0.5 * draws)
    if performance_ratio == 0:
        return opponent_elo - 400
    elo_diff = 400 * math.log10(performance_ratio)
    return opponent_elo + elo_diff

def handle_move_outcome(game, target_piece=None, bot1_color=chess.WHITE):
    if game.board.is_checkmate():
        checkmate_sound.play()
        winner = "Bot1" if game.board.turn != bot1_color else "Bot2"
        return "checkmate", winner, f"{winner} Wins!"
    elif game.board.is_stalemate():
        return "stalemate", None, "Stalemate!"
    elif game.board.is_insufficient_material():
        return "draw", None, "Draw: Insufficient material!"
    if target_piece:
        capture_sound.play()
    else:
        move_sound.play()
    if game.board.is_check():
        check_sound.play()
    return None, None, ""

def export_pgn(game, bot1_color):
    pgn_file = os.path.join(bundle_dir, "game_records.pgn")
    with open(pgn_file, "w", encoding="utf-8") as f:
        pgn_game = chess.pgn.Game()
        pgn_game.headers["Event"] = "Bot vs Bot"
        pgn_game.headers["Site"] = "Local"
        pgn_game.headers["Date"] = time.strftime("%Y.%m.%d")
        pgn_game.headers["Round"] = "1"
        pgn_game.headers["White"] = "Bot1" if bot1_color == chess.WHITE else "Bot2"
        pgn_game.headers["Black"] = "Bot2" if bot1_color == chess.WHITE else "Bot1"
        node = pgn_game
        for move in game.move_history:
            node = node.add_variation(move)
        pgn_game.headers["Result"] = (
            "1-0" if game.board.is_checkmate() and game.board.turn == chess.BLACK else
            "0-1" if game.board.is_checkmate() and game.board.turn == chess.WHITE else
            "1/2-1/2" if game.board.is_game_over() else "*"
        )
        print(pgn_game, file=f)
    return pgn_file

def bot_vs_bot():
    bot1_wins, draws, bot2_wins = 0, 0, 0
    game = ChessGame()
    bot1 = Engine()
    bot2 = Engine()
    bot1_color = chess.WHITE
    bot1_stats = {}
    bot2_stats = {}
    game_active = True
    game_message = ""

    def get_bot_move(game, bot, stats):
        try:
            start_time = time.time()
            bot.set_position(game.board.fen())
            result = bot.get_best_move_with_stats()
            end_time = time.time()
            move = result.get("move")
            stats.update({
                "depth": result.get("depth", "-"),
                "score": "-",
                "nodes": result.get("nodes", 0),
                "time": end_time - start_time
            })
            return move
        except Exception as e:
            print(f"Lỗi Bot: {e}")
            return None

    running = True
    board_position = (MARGIN, MARGIN)
    while running and game_active:
        screen.blit(menu_background, (0, 0))
        x_offset, y_offset = board_position
        draw_board(x_offset, y_offset, game, game_message)
        draw_pieces(game, x_offset, y_offset)

        mouse_pos = pygame.mouse.get_pos()
        btn_back = draw_console(game, bot1_stats, bot2_stats, mouse_pos, bot1_color)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event.pos):
                    running = False

        if not running:
            break

        if game.board.is_game_over():
            outcome, winner, message = handle_move_outcome(game, bot1_color=bot1_color)
            game_message = message
            if outcome == "checkmate":
                if winner == "Bot1":
                    bot1_wins += 1
                else:
                    bot2_wins += 1
            elif outcome in ["stalemate", "draw"]:
                draws += 1
            game_active = False
            continue

        current_bot = bot1 if game.board.turn == bot1_color else bot2
        current_stats = bot1_stats if game.board.turn == bot1_color else bot2_stats
        uci_move = get_bot_move(game, current_bot, current_stats)

        if uci_move:
            from_square = chess.square(ord(uci_move[0]) - ord('a'), int(uci_move[1]) - 1)
            to_square = chess.square(ord(uci_move[2]) - ord('a'), int(uci_move[3]) - 1)
            promotion = None
            if len(uci_move) == 5:
                promotion_piece = uci_move[4].upper()
                promotion = {'Q': chess.QUEEN, 'R': chess.ROOK, 'B': chess.BISHOP, 'N': chess.KNIGHT}.get(promotion_piece)
            move_result = game.move(from_square, to_square, promotion=promotion)
            if move_result["valid"]:
                target_piece = game.get_piece(to_square)
                outcome, winner, message = handle_move_outcome(game, target_piece, bot1_color=bot1_color)
                game_message = message

        pygame.display.flip()
        pygame.time.wait(100)

    pgn_file = export_pgn(game, bot1_color)
    bot1_elo = calculate_elo(bot1_wins, draws, bot2_wins)
    show_results(bot1_wins, draws, bot2_wins, bot1_elo, pgn_file)

def main_menu():
    running = True
    while running:
        screen.blit(menu_background, (0, 0))
        title = FONT.render("Bot vs Bot", True, BLACK)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        btn_start = draw_text("Start Match", WIDTH // 2, 250)
        btn_quit = draw_text("Exit", WIDTH // 2, 320)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if btn_start.collidepoint(mouse_x, mouse_y):
            draw_text("Start Match", WIDTH // 2, 250, color=(0, 128, 0))
        if btn_quit.collidepoint(mouse_x, mouse_y):
            draw_text("Exit", WIDTH // 2, 320, color=(0, 128, 0))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_start.collidepoint(event.pos):
                    bot_vs_bot()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_quit.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()

if __name__ == "__main__":
    main_menu()