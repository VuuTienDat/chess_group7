import pygame
import chess
from chess_game import ChessGame
import sys
import os
import time
from stockfish import Stockfish
import math

# Assuming Engine is in the Engine directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Engine"))
from Engine.engine import Engine

# Handle resource paths for bundled executable
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

music_path = os.path.join(bundle_dir, "Music")
image_path = os.path.join(bundle_dir, "Image")
font_path = os.path.join(bundle_dir, "Font")

# Window dimensions
WIDTH, HEIGHT = 840, 640
BOARD_WIDTH = 640
CONSOLE_WIDTH = 200
SQUARE_SIZE = BOARD_WIDTH // 8

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bot vs Stockfish")
pygame.mixer.init()

# Load music and sounds with volume set to 0
pygame.mixer.music.load(os.path.join(music_path, "chessmusic.mp3"))
pygame.mixer.music.set_volume(0.0)  # Set music volume to 0
pygame.mixer.music.play(-1)
move_sound = pygame.mixer.Sound(os.path.join(music_path, "Move.mp3"))
move_sound.set_volume(0.0)  # Set move sound volume to 0
capture_sound = pygame.mixer.Sound(os.path.join(music_path, "Capture.mp3"))
capture_sound.set_volume(0.0)  # Set capture sound volume to 0
check_sound = pygame.mixer.Sound(os.path.join(music_path, "Check.mp3"))
check_sound.set_volume(0.0)  # Set check sound volume to 0
checkmate_sound = pygame.mixer.Sound(os.path.join(music_path, "Checkmate.mp3"))
checkmate_sound.set_volume(0.0)  # Set checkmate sound volume to 0

# Board and piece setup
board_colors = [(255, 255, 255), (0, 100, 0)]
images = {}
pieces = ["P", "N", "B", "R", "Q", "K"]
for color in ["w", "b"]:
    for p in pieces:
        name = color + p
        images[name] = pygame.transform.scale(
            pygame.image.load(os.path.join(image_path, f"{name}.png")), (SQUARE_SIZE, SQUARE_SIZE)
        )

# Fonts
FONT = pygame.font.Font(os.path.join(font_path, "turok.ttf"), 40)
VICTORY_FONT = pygame.font.Font(os.path.join(font_path, "turok.ttf"), 120)
CONSOLE_FONT = pygame.font.SysFont('arial', 16)
BOARD_LABEL_FONT = pygame.font.SysFont('arial', 14)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CONSOLE_BG = (50, 50, 50)
LABEL_COLOR = (0, 0, 0)
HIGHLIGHT_COLOR = (100, 149, 237, 128)

# Load background
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

def draw_board():
    screen.blit(menu_background, (0, 0), (0, 0, BOARD_WIDTH, HEIGHT))
    pygame.draw.rect(screen, CONSOLE_BG, (BOARD_WIDTH, 0, CONSOLE_WIDTH, HEIGHT))
    for row in range(8):
        for col in range(8):
            color = board_colors[(row + col) % 2]
            pygame.draw.rect(screen, color,
                            (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    for col in range(8):
        label = BOARD_LABEL_FONT.render(files[col], True, LABEL_COLOR)
        screen.blit(label, (col * SQUARE_SIZE + 2, (7 * SQUARE_SIZE) + SQUARE_SIZE - 20))
    for row in range(8):
        label = BOARD_LABEL_FONT.render(ranks[row], True, LABEL_COLOR)
        screen.blit(label, (2, row * SQUARE_SIZE + 2))

def draw_pieces(game):
    for square in chess.SQUARES:
        piece = game.get_piece(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            name = ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()
            screen.blit(images[name], (col * SQUARE_SIZE, row * SQUARE_SIZE))

def draw_console(game, bot_stats=None, stockfish_stats=None, mouse_pos=(0, 0), bot_color=chess.WHITE):
    pygame.draw.rect(screen, CONSOLE_BG, (BOARD_WIDTH, 0, CONSOLE_WIDTH, HEIGHT))
    panel_height = HEIGHT // 2
    TITLE_COLOR = (255, 215, 0)

    # Panel Game
    title = CONSOLE_FONT.render("Panel Game", True, TITLE_COLOR)
    title_rect = title.get_rect(center=(BOARD_WIDTH + CONSOLE_WIDTH // 2, 10 + title.get_height() // 2))
    screen.blit(title, title_rect)

    y_offset = 40
    turn = "WHITE" if game.board.turn == chess.WHITE else "BLACK"
    WHITE_TURN_COLOR = (255, 255, 255)
    BLACK_TURN_COLOR = (150, 150, 150)
    turn_color = WHITE_TURN_COLOR if turn == "WHITE" else BLACK_TURN_COLOR
    turn_label = CONSOLE_FONT.render("Turn: ", True, WHITE)
    turn_value = CONSOLE_FONT.render(turn, True, turn_color)
    screen.blit(turn_label, (BOARD_WIDTH + 10, y_offset))
    turn_label_width = turn_label.get_width()
    screen.blit(turn_value, (BOARD_WIDTH + 10 + turn_label_width, y_offset))

    y_offset += 25
    possible_moves = len(list(game.board.legal_moves))
    draw_text(f"Possible moves: {possible_moves}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 25
    in_check = game.board.is_check()
    draw_text(f"In Check: {in_check}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 25
    bot_label = CONSOLE_FONT.render(f"Bot ({'White' if bot_color == chess.WHITE else 'Black'})", True, WHITE)
    stockfish_label = CONSOLE_FONT.render(f"Stockfish ({'Black' if bot_color == chess.WHITE else 'White'})", True, WHITE)
    screen.blit(bot_label, (BOARD_WIDTH + 10, y_offset))
    stockfish_label_width = stockfish_label.get_width()
    screen.blit(stockfish_label, (BOARD_WIDTH + CONSOLE_WIDTH - stockfish_label_width - 10, y_offset))

    y_offset += 25
    moves = [move.uci() for move in game.move_history]
    paired_moves = []
    for i in range(0, len(moves), 2):
        white_move = moves[i]
        black_move = moves[i + 1] if i + 1 < len(moves) else ""
        paired_moves.append((white_move, black_move))
    max_moves = (panel_height - y_offset - 10) // 20
    start_index = max(0, len(paired_moves) - max_moves)
    for white_move, black_move in paired_moves[start_index:]:
        white_move_label = CONSOLE_FONT.render(white_move, True, WHITE)
        black_move_label = CONSOLE_FONT.render(black_move, True, WHITE) if black_move else None
        screen.blit(white_move_label, (BOARD_WIDTH + 10, y_offset))
        if black_move_label:
            black_move_width = black_move_label.get_width()
            screen.blit(black_move_label, (BOARD_WIDTH + CONSOLE_WIDTH - black_move_width - 10, y_offset))
        y_offset += 20

    total_moves = len(paired_moves)
    draw_text(f"Total moves: {total_moves}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    # Panel Stats
    y_offset = panel_height + 10
    title = CONSOLE_FONT.render("Panel Stats", True, TITLE_COLOR)
    title_rect = title.get_rect(center=(BOARD_WIDTH + CONSOLE_WIDTH // 2, y_offset + title.get_height() // 2))
    screen.blit(title, title_rect)

    y_offset += 25
    draw_text(f"Bot ({'White' if bot_color == chess.WHITE else 'Black'})", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)
    y_offset += 20
    bot_depth = bot_stats.get("depth", "-") if bot_stats else "-"
    draw_text(f"DEPTH: {bot_depth}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)
    y_offset += 20
    bot_score = bot_stats.get("score", "-") if bot_stats else "-"
    draw_text(f"SCORE: {bot_score}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)
    y_offset += 20
    if bot_stats and "nodes" in bot_stats:
        nodes = str(bot_stats.get("nodes", 0)).ljust(10)
        time_taken = f"{bot_stats.get('time', 0.0):.4f}".ljust(8)
        draw_text(f"NODES: {nodes} TIME: {time_taken}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 30
    draw_text(f"Stockfish ({'Black' if bot_color == chess.WHITE else 'White'})", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)
    y_offset += 20
    stockfish_depth = stockfish_stats.get("depth", "-") if stockfish_stats else "-"
    draw_text(f"DEPTH:isks {stockfish_depth}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)
    y_offset += 20
    stockfish_score = stockfish_stats.get("score", "-") if stockfish_stats else "-"
    draw_text(f"SCORE: {stockfish_score}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset = HEIGHT - 60
    btn_back = draw_button("Back", 715, y_offset, 100, 30, (200, 50, 50), (255, 100, 100), mouse_pos)
    return btn_back

def draw_button(text, x, y, w, h, color, hover_color, mouse_pos, text_color=WHITE):
    rect = pygame.Rect(x, y, w, h)
    if rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, hover_color, rect)
    else:
        pygame.draw.rect(screen, color, rect)
    draw_text(text, x + w // 2, y + h // 2, center=True, color=text_color, font=CONSOLE_FONT)
    return rect

def notification(game, message, color=(255, 0, 0), is_victory=False, outline_color=None):
    while True:
        screen.blit(menu_background, (0, 0))
        font_to_use = VICTORY_FONT if is_victory else FONT
        draw_text(message, WIDTH // 2, HEIGHT // 2, font=font_to_use, color=color, outline_color=outline_color)
        mouse_pos = pygame.mouse.get_pos()
        btn_back = draw_button("Back", WIDTH - 110, HEIGHT - 50, 100, 40, (200, 50, 50), (255, 100, 100), mouse_pos)
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

def show_results(wins, draws, losses, bot_elo):
    while True:
        screen.blit(menu_background, (0, 0))
        y_offset = 100
        draw_text("Match Results", WIDTH // 2, y_offset, font=FONT, color=BLACK)
        y_offset += 60
        draw_text(f"Wins: {wins}", WIDTH // 2, y_offset, font=CONSOLE_FONT, color=WHITE)
        y_offset += 30
        draw_text(f"Draws: {draws}", WIDTH // 2, y_offset, font=CONSOLE_FONT, color=WHITE)
        y_offset += 30
        draw_text(f"Losses: {losses}", WIDTH // 2, y_offset, font=CONSOLE_FONT, color=WHITE)
        y_offset += 30
        draw_text(f"Bot ELO: {bot_elo:.0f}", WIDTH // 2, y_offset, font=CONSOLE_FONT, color=WHITE)
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

def calculate_elo(wins, draws, losses, opponent_elo=3200):
    if losses + 0.5 * draws == 0:
        return opponent_elo  # Avoid division by zero
    performance_ratio = (wins + 0.5 * draws) / (losses + 0.5 * draws)
    if performance_ratio == 0:
        return opponent_elo - 400  # Arbitrary lower bound for no wins/draws
    elo_diff = 400 * math.log10(performance_ratio)
    return opponent_elo + elo_diff

def handle_move_outcome(game, target_piece=None, bot_color=chess.WHITE):
    if game.board.is_checkmate():
        checkmate_sound.play()  # Will not play due to volume set to 0
        winner = "Bot" if game.board.turn != bot_color else "Stockfish"
        winner_color = WHITE if winner == "Bot" else BLACK
        outline = WHITE if winner_color == BLACK else None
        notification(game, f"{winner} Wins!", color=winner_color, is_victory=True, outline_color=outline)
        return "checkmate", winner
    elif game.board.is_stalemate():
        notification(game, "Stalemate!")
        return "stalemate", None
    elif game.board.is_insufficient_material():
        notification(game, "Draw: Insufficient material!")
        return "draw", None
    if target_piece:
        capture_sound.play()  # Will not play due to volume set to 0
    else:
        move_sound.play()  # Will not play due to volume set to 0
    if game.board.is_check():
        check_sound.play()  # Will not play due to volume set to 0
    return None, None

def bot_vs_stockfish():
    wins, draws, losses = 0, 0, 0
    stockfish_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Engine", "stockfish", "stockfish.exe")
    if not os.path.isfile(stockfish_path):
        raise FileNotFoundError(f"Không tìm thấy file stockfish.exe tại {stockfish_path}.")
    stockfish = Stockfish(path=stockfish_path, depth=15)
    stockfish.set_elo_rating(3200)

    for game_num in range(4):
        bot_color = chess.WHITE if game_num % 2 == 0 else chess.BLACK
        game = ChessGame()
        bot = Engine()
        bot_stats = {}
        stockfish_stats = {}
        running = True

        def get_bot_move():
            start_time = time.time()
            bot.set_position(game.board.fen())
            result = bot.get_best_move_with_stats()
            end_time = time.time()
            move = result.get("move")
            bot_stats.update({
                "depth": result.get("depth", "-"),
                "score": "-",
                "nodes": result.get("nodes", 0),
                "time": end_time - start_time
            })
            return move

        def get_stockfish_move():
            try:
                stockfish.set_fen_position(game.board.fen())
                start_time = time.time()
                best_move = stockfish.get_best_move_time(10000)
                end_time = time.time()
                evaluation = stockfish.get_evaluation()
                score = "-"
                if isinstance(evaluation, dict):
                    eval_type = evaluation.get("type", "")
                    eval_value = evaluation.get("value", "")
                    if eval_type == "cp":
                        score = eval_value
                    elif eval_type == "mate":
                        score = f"mate {eval_value}"
                stockfish_stats.update({
                    "depth": stockfish.get_parameters().get("depth", "-"),
                    "score": score,
                    "time": end_time - start_time
                })
                return best_move
            except Exception as e:
                print(f"Lỗi khi lấy nước đi từ Stockfish: {e}")
                return None

        while running:
            if game.board.is_game_over():
                outcome, winner = handle_move_outcome(game, bot_color=bot_color)
                if outcome == "checkmate":
                    if winner == "Bot":
                        wins += 1
                    else:
                        losses += 1
                elif outcome in ["stalemate", "draw"]:
                    draws += 1
                running = False
                break

            screen.fill((0, 0, 0))
            draw_board()
            draw_pieces(game)
            mouse_pos = pygame.mouse.get_pos()
            btn_back = draw_console(game, bot_stats=bot_stats, stockfish_stats=stockfish_stats, mouse_pos=mouse_pos, bot_color=bot_color)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    stockfish.__del__()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_back.collidepoint(event.pos):
                        running = False

            if not running:
                break

            if game.board.turn == bot_color:
                uci_move = get_bot_move()
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
                        handle_move_outcome(game, target_piece, bot_color=bot_color)
            else:
                uci_move = get_stockfish_move()
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
                        handle_move_outcome(game, target_piece, bot_color=bot_color)

            pygame.display.flip()
            pygame.time.wait(500)

    stockfish.__del__()
    bot_elo = calculate_elo(wins, draws, losses)
    show_results(wins, draws, losses, bot_elo)

def main_menu():
    running = True
    while running:
        screen.blit(menu_background, (0, 0))
        title = FONT.render("Bot vs Stockfish", True, BLACK)
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
                    bot_vs_stockfish()
                elif btn_quit.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

if __name__ == "__main__":
    main_menu()