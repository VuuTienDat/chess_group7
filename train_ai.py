# --- train_ai.py (KEEP GUI, FASTER TRAINING) ---
import os
import sys
import pygame
import chess
import threading
import math
import time
from Engine.engine import Engine
from stockfish import Stockfish
from queue import Queue

# Paths
WIDTH, HEIGHT = 960, 720
INFO_PANEL_WIDTH = 300  # Độ rộng của bảng thông tin
BOARD_AREA_WIDTH = WIDTH - INFO_PANEL_WIDTH  # Khu vực dành cho các bàn cờ
GAMES_PER_ROW = 2  # Số ván cờ trên mỗi hàng (2 cột)
NUM_ROWS = 1  # Số hàng (1 hàng -> tổng 2 ván)
BOARD_SIZE = min(BOARD_AREA_WIDTH // GAMES_PER_ROW - 20, HEIGHT // NUM_ROWS - 40)  # Kích thước mỗi bàn cờ
SQUARE_SIZE = BOARD_SIZE // 8  # Kích thước mỗi ô trên bàn cờ

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess AI Training")

bundle_dir = os.path.dirname(os.path.abspath(__file__))
model_dir = os.path.join(bundle_dir, "Engine")
elo_file = os.path.join(model_dir, "elo.txt")
result_file = os.path.join(bundle_dir, "result.txt")  # Tệp lưu kết quả các ván đấu
image_path = os.path.join(bundle_dir, "Image")
font_path = os.path.join(bundle_dir, "Font")

# Assets
board_colors = [(240, 217, 181), (181, 136, 99)]
FONT = pygame.font.Font(os.path.join(font_path, "turok.ttf"), 24)

# Tải hình ảnh quân cờ với kích thước phù hợp
images = {}
for color in ["w", "b"]:
    for piece in ["P", "N", "B", "R", "Q", "K"]:
        name = color + piece
        images[name] = pygame.transform.scale(
            pygame.image.load(os.path.join(image_path, f"{name}.png")), (SQUARE_SIZE, SQUARE_SIZE)
        )

WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
GREEN = (34, 139, 34)
RED = (220, 20, 60)
BLUE = (70, 130, 180)
LIGHT_BLUE = (173, 216, 230)

# Elo Functions

def estimate_stockfish_elo(level: int) -> int:
    return 600 + 120 * level

def expected_score(rating1: int, rating2: int) -> float:
    return 1 / (1 + 10 ** ((rating2 - rating1) / 400))

def update_elo(bot_elo: int, opponent_elo: int, actual_score: float, k: int = 32) -> int:
    expected = expected_score(bot_elo, opponent_elo)
    return int(bot_elo + k * (actual_score - expected))

def load_elo() -> int:
    if os.path.exists(elo_file):
        try:
            with open(elo_file, "r") as f:
                return int(f.read().strip())
        except:
            return 1200
    return 1200

def save_elo(elo: int):
    os.makedirs(model_dir, exist_ok=True)
    with open(elo_file, "w") as f:
        f.write(str(elo))

def save_game_result(game_idx: int, result: str):
    """Lưu kết quả ván đấu vào result.txt."""
    mode = "w" if game_idx == 1 else "a"  # Ghi đè nếu là ván đầu tiên, thêm vào nếu không
    try:
        with open(result_file, mode) as f:
            f.write(f"Game {game_idx}: {result}\n")
    except IOError as e:
        print(f"Failed to save game result to {result_file}: {e}")

# Drawing Functions

def draw_board(board, x_offset, y_offset):
    for row in range(8):
        for col in range(8):
            color = board_colors[(row + col) % 2]
            pygame.draw.rect(screen, color, (x_offset + col * SQUARE_SIZE, y_offset + row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces(board, x_offset, y_offset):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            name = ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()
            screen.blit(images[name], (x_offset + col * SQUARE_SIZE, y_offset + row * SQUARE_SIZE))

def draw_info_panel(current_game, num_games, avg_loss, elo, last_result, progress, results_history, active_games):
    panel_x = WIDTH - INFO_PANEL_WIDTH
    pygame.draw.rect(screen, BLACK, (panel_x, 0, INFO_PANEL_WIDTH, HEIGHT))
    info_y = 40

    def draw_text(text, y, color=WHITE):
        label = FONT.render(text, True, color)
        screen.blit(label, (panel_x + 20, y))

    draw_text(f"Training Game: {current_game}/{num_games}", info_y)
    draw_text(f"Active Games: {active_games}", info_y + 30)
    draw_text(f"Avg Loss: {avg_loss}", info_y + 60)
    draw_text(f"Current Elo: {elo}", info_y + 90)
    draw_text(f"Last Result: {last_result}", info_y + 120)

    bar_y = info_y + 180
    pygame.draw.rect(screen, WHITE, (panel_x + 20, bar_y, INFO_PANEL_WIDTH - 40, 30))
    fill_width = int((INFO_PANEL_WIDTH - 40) * progress)
    pygame.draw.rect(screen, GREEN, (panel_x + 20, bar_y, fill_width, 30))

    result_y = bar_y + 70
    draw_text("Results:", result_y)
    for idx, result in enumerate(results_history[-5:]):
        color = GREEN if result == "Win" else RED if result == "Loss" else LIGHT_BLUE
        draw_text(f"{idx + 1}. {result}", result_y + 30 + idx * 30, color)

    return {
        "stop": pygame.Rect(panel_x + 30, result_y + 210, INFO_PANEL_WIDTH - 60, 40),
        "back": pygame.Rect(panel_x + 30, result_y + 270, INFO_PANEL_WIDTH - 60, 40)
    }

# Main Training Screen

def train_ai_screen():
    engine = Engine(max_simulations=200, time_limit=3, model_dir=model_dir)
    stockfish_path = os.path.join(model_dir, "stockfish", "stockfish.exe")
    stockfish = Stockfish(path=stockfish_path)

    elo = load_elo()
    stockfish_level = 1
    stockfish.set_skill_level(stockfish_level)

    num_games = 100
    max_moves = 100
    games_per_batch = 2  # Chạy 2 ván cờ cùng lúc
    current_game = 0
    avg_loss = "N/A"
    last_result = "-"
    progress = 0
    training_complete = False
    stop_training = False
    results_history = []
    active_games = 0

    # Danh sách để lưu trạng thái của các ván cờ đang chạy
    active_boards = [None] * games_per_batch  # Lưu trạng thái bàn cờ
    active_threads = [None] * games_per_batch  # Lưu các luồng đang chạy

    # Hàng đợi để lưu kết quả từ các luồng
    result_queue = Queue()

    def play_game(game_idx, board_idx, result_queue):
        nonlocal elo, stockfish_level
        local_board = chess.Board()
        ai_color = chess.WHITE if game_idx % 2 == 0 else chess.BLACK
        local_engine = Engine(max_simulations=200, time_limit=3, model_dir=model_dir)
        local_stockfish = Stockfish(path=stockfish_path)
        local_stockfish.set_skill_level(stockfish_level)
        stockfish_elo = estimate_stockfish_elo(stockfish_level)
        move_count = 0

        while not local_board.is_game_over() and move_count < max_moves:
            if stop_training:
                break
            # Cập nhật trạng thái bàn cờ để hiển thị
            active_boards[board_idx] = local_board.copy()
            if local_board.turn == ai_color:
                local_engine.set_position(local_board.fen())
                uci_move = local_engine.get_best_move()
                if uci_move:
                    local_board.push(chess.Move.from_uci(uci_move))
            else:
                local_stockfish.set_fen_position(local_board.fen())
                uci_move = local_stockfish.get_best_move()
                if uci_move:
                    local_board.push(chess.Move.from_uci(uci_move))
            move_count += 1

        if local_board.is_checkmate():
            game_result = "Win" if local_board.turn != ai_color else "Loss"
            actual_score = 1.0 if game_result == "Win" else 0.0
        else:
            game_result = "Draw"
            actual_score = 0.5

        # Tính Elo mới
        new_elo = update_elo(elo, stockfish_elo, actual_score)

        # Đặt kết quả vào hàng đợi
        result_queue.put((game_result, actual_score, new_elo))
        active_boards[board_idx] = None  # Xóa trạng thái bàn cờ sau khi hoàn tất

    def train():
        nonlocal current_game, avg_loss, training_complete, progress, elo, last_result, results_history, active_games, stockfish_level

        for batch_start in range(0, num_games, games_per_batch):
            if stop_training:
                break

            # Tính số ván cờ trong batch này
            batch_size = min(games_per_batch, num_games - batch_start)
            active_games = batch_size

            # Chạy các ván cờ song song
            for i in range(batch_size):
                game_idx = batch_start + i
                thread = threading.Thread(target=play_game, args=(game_idx, i, result_queue))
                active_threads[i] = thread
                thread.start()

            # Đợi tất cả các ván cờ trong batch hoàn tất
            for i in range(batch_size):
                active_threads[i].join()
                active_threads[i] = None

            # Tổng hợp kết quả từ hàng đợi
            batch_results = []
            while not result_queue.empty():
                game_result, actual_score, new_elo = result_queue.get()
                batch_results.append((game_result, actual_score, new_elo))

            # Cập nhật Elo, lịch sử kết quả và lưu vào result.txt
            for game_result, actual_score, new_elo in batch_results:
                last_result = game_result
                elo = new_elo
                results_history.append(game_result)
                current_game += 1
                progress = current_game / num_games
                # Lưu kết quả ván đấu vào result.txt
                save_game_result(current_game, game_result)

            # Cập nhật level của Stockfish dựa trên Elo mới nhất
            stockfish_level = min(max((elo - 600) // 120, 1), 20)
            stockfish.set_skill_level(stockfish_level)
            active_games = 0

        avg_loss = "Completed"
        training_complete = True
        save_elo(elo)
        engine.learner.save_model(os.path.join(model_dir, "chess_model.pth"))

    training_thread = threading.Thread(target=train)
    training_thread.start()

    running = True
    while running:
        screen.fill(BLACK)

        # Vẽ 2 bàn cờ (2 cột x 1 hàng)
        for i in range(games_per_batch):
            if active_boards[i] is not None:
                row = i // GAMES_PER_ROW
                col = i % GAMES_PER_ROW
                x_offset = col * (BOARD_SIZE + 20)  # Thêm khoảng cách giữa các cột
                y_offset = row * (BOARD_SIZE + 20) + 20  # Thêm khoảng cách trên cùng
                draw_board(active_boards[i], x_offset, y_offset)
                draw_pieces(active_boards[i], x_offset, y_offset)

        buttons = draw_info_panel(current_game, num_games, avg_loss, elo, last_result, progress, results_history, active_games)

        mouse_pos = pygame.mouse.get_pos()
        pygame.draw.rect(screen, RED, buttons["stop"])
        pygame.draw.rect(screen, BLUE, buttons["back"])
        stop_label = FONT.render("Stop", True, WHITE)
        back_label = FONT.render("Back", True, WHITE)
        screen.blit(stop_label, (buttons["stop"].centerx - stop_label.get_width() // 2, buttons["stop"].centery - 12))
        screen.blit(back_label, (buttons["back"].centerx - back_label.get_width() // 2, buttons["back"].centery - 12))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_elo(elo)
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if buttons["stop"].collidepoint(event.pos) and not training_complete:
                    stop_training = True
                elif buttons["back"].collidepoint(event.pos):
                    stop_training = True
                    training_thread.join()
                    save_elo(elo)
                    stockfish.__del__()
                    return

        pygame.display.flip()

if __name__ == "__main__":
    train_ai_screen()