import pygame
import chess
from chess_game import ChessGame
import sys
import os
import threading
import queue
import time

# Assuming Engine is in the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
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
WIDTH, HEIGHT = 840, 640  # Adjusted height to fit the board exactly (640x640)
BOARD_WIDTH = 640
CONSOLE_WIDTH = 200
SQUARE_SIZE = BOARD_WIDTH // 8

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Game")
pygame.mixer.init()

# Load music and sounds
pygame.mixer.music.load(os.path.join(music_path, "chessmusic.mp3"))
pygame.mixer.music.play(-1)
music_on = True
move_sound = pygame.mixer.Sound(os.path.join(music_path, "Move.mp3"))
capture_sound = pygame.mixer.Sound(os.path.join(music_path, "Capture.mp3"))
check_sound = pygame.mixer.Sound(os.path.join(music_path, "Check.mp3"))
checkmate_sound = pygame.mixer.Sound(os.path.join(music_path, "Checkmate.mp3"))

# Board and piece setup
board_colors = [(255, 255, 255), (0, 100, 0)]  # Light squares (white), dark squares (dark green)
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
CONSOLE_FONT = pygame.font.SysFont('arial', 16)  # Reduced font size to avoid text clipping
BOARD_LABEL_FONT = pygame.font.SysFont('arial', 14)  # Reduced font size for board labels
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
MENU_COLOR = (100, 100, 100)
HOVER_COLOR = (255, 0, 0)
CONSOLE_BG = (50, 50, 50)
LABEL_COLOR = (0, 0, 0)  # Black for board labels

# Color for highlighting suggested moves (same for both from and to squares)
HIGHLIGHT_COLOR = (100, 149, 237, 128)  # Cornflower Blue with alpha

# Load background
menu_background = pygame.image.load(os.path.join(image_path, "landscape3.jpg"))
menu_background = pygame.transform.scale(menu_background, (WIDTH, HEIGHT))

def draw_text(text, x, y, font=FONT, center=True, color=BLACK):
    label = font.render(text, True, color)
    rect = label.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(label, rect)
    return rect

def draw_board(flipped=False):
    screen.blit(menu_background, (0, 0), (0, 0, BOARD_WIDTH, HEIGHT))
    pygame.draw.rect(screen, CONSOLE_BG, (BOARD_WIDTH, 0, CONSOLE_WIDTH, HEIGHT))
    for row in range(8):
        for col in range(8):
            display_row = 7 - row if flipped else row
            display_col = 7 - col if flipped else col
            color = board_colors[(row + col) % 2]
            pygame.draw.rect(screen, color,
                            (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    
    # Draw labels on the board
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    if flipped:
        files = files[::-1]
        ranks = ranks[::-1]
    
    # Draw file labels (a-h) only on bottom rank (rank 1)
    for col in range(8):
        label = BOARD_LABEL_FONT.render(files[col], True, LABEL_COLOR)
        display_col = 7 - col if flipped else col
        screen.blit(label, (display_col * SQUARE_SIZE + 2, (7 * SQUARE_SIZE) + SQUARE_SIZE - 15))  # Closer to bottom and left
    
    # Draw rank labels (1-8) only on left file (file a)
    for row in range(8):
        label = BOARD_LABEL_FONT.render(ranks[row], True, LABEL_COLOR)
        display_row = 7 - row if flipped else row
        screen.blit(label, (2, display_row * SQUARE_SIZE + 2))  # Closer to left and top

def draw_pieces(game, flipped=False):
    for square in chess.SQUARES:
        piece = game.get_piece(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            display_col = 7 - col if flipped else col
            display_row = 7 - row if flipped else row
            name = ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()
            screen.blit(images[name], (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE))

def draw_console(game, is_ai_mode=False, ai_stats=None, mouse_pos=(0, 0), ai_thinking=False):
    # Clear the console area
    pygame.draw.rect(screen, CONSOLE_BG, (BOARD_WIDTH, 0, CONSOLE_WIDTH, HEIGHT))

    # Split the console into two panels
    panel_height = HEIGHT // 2  # 320 pixels each with HEIGHT=640

    # --- Panel chess ---
    # Title
    title = CONSOLE_FONT.render("Panel chess", True, WHITE)
    screen.blit(title, (BOARD_WIDTH + 10, 10))

    # Game state info
    y_offset = 40
    turn = "WHITE" if game.board.turn == chess.WHITE else "BLACK"
    draw_text(f"Turn: {turn}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 25
    possible_moves = len(list(game.board.legal_moves))
    draw_text(f"Possible moves: {possible_moves}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 25
    in_check = game.board.is_check()
    draw_text(f"In Check: {in_check}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 25
    # Move history (White Black in columns)
    white_label = CONSOLE_FONT.render("White", True, WHITE)
    black_label = CONSOLE_FONT.render("Black", True, WHITE)
    screen.blit(white_label, (BOARD_WIDTH + 10, y_offset))
    screen.blit(black_label, (BOARD_WIDTH + 80, y_offset))

    y_offset += 25
    # Get moves in UCI format directly from move_history
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
            screen.blit(black_move_label, (BOARD_WIDTH + 80, y_offset))
        y_offset += 20

    # Display total moves at the bottom
    if paired_moves:
        total_moves = len(paired_moves)
        draw_text(f"Total moves: {total_moves}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    # --- Panel AI (only in AI mode) ---
    y_offset = panel_height + 10
    title = CONSOLE_FONT.render("Panel AI", True, WHITE)
    screen.blit(title, (BOARD_WIDTH + 10, y_offset))

    y_offset += 25
    algorithm = "MORA (Alpha Beta)"
    draw_text(f"Algorithm: {algorithm}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 25
    # Only show DEPTH if ai_stats has data
    depth = ai_stats.get("depth", "-") if ai_stats else "-"
    draw_text(f"DEPTH: {depth}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 25
    max_score = ai_stats.get("score", "-") if ai_stats else "-"
    draw_text(f"MAX SCORE: {max_score}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    y_offset += 25
    # Only display the table if ai_stats has actual data, and only show NODES and TIME
    if ai_stats and "nodes" in ai_stats:
        nodes_header = "NODES".ljust(10)
        time_header = "TIME".ljust(8)
        draw_text(f"{nodes_header}{time_header}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)
        y_offset += 20
        nodes = str(ai_stats.get("nodes", 0)).ljust(10)
        time_taken = f"{ai_stats.get('time', 0.0):.4f}".ljust(8)
        draw_text(f"{nodes}{time_taken}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    # Draw "AI is thinking" above the buttons if AI is thinking, centered and with more space
    if ai_thinking:
        draw_text("AI Thinking...", BOARD_WIDTH + 70, HEIGHT - 120, font=CONSOLE_FONT, center=False, color=WHITE)

    # Draw buttons in the console area (below Panel AI), centered in the console
    y_offset = HEIGHT - 60  # Adjusted for new height to avoid overlap
    btn_undo = draw_button("Undo", 655, y_offset, 50, 30, (50, 50, 200), (100, 100, 255), mouse_pos)  # Reduced size
    btn_help = draw_button("Help", 715, y_offset, 50, 30, (50, 200, 50), (100, 255, 100), mouse_pos)  # Reduced size
    btn_back = draw_button("Back", 775, y_offset, 50, 30, (200, 50, 50), (255, 100, 100), mouse_pos)  # Reduced size

    return btn_undo, btn_help, btn_back

def get_square_from_mouse(pos, flipped=False):
    x, y = pos
    if x >= BOARD_WIDTH:
        return None
    col = x // SQUARE_SIZE
    row = y // SQUARE_SIZE
    if flipped:
        col = 7 - col
        row = 7 - row
    row = 7 - row
    if not (0 <= col < 8 and 0 <= row < 8):
        return None
    return chess.square(col, row)

def draw_move_hints(game, selected_square, flipped=False):
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

def draw_suggested_move(suggested_move, flipped=False):
    if not suggested_move:
        return

    # Get the from and to squares
    from_square = suggested_move.from_square
    to_square = suggested_move.to_square

    # Calculate display positions
    from_col = chess.square_file(from_square)
    from_row = 7 - chess.square_rank(from_square)
    to_col = chess.square_file(to_square)
    to_row = 7 - chess.square_rank(to_square)

    # Adjust for flipped board
    display_from_col = 7 - from_col if flipped else from_col
    display_from_row = 7 - from_row if flipped else from_row
    display_to_col = 7 - to_col if flipped else to_col
    display_to_row = 7 - to_row if flipped else to_row

    # Highlight both the from and to squares with the same color
    highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    
    # Highlight the "from" square
    highlight_surface.fill(HIGHLIGHT_COLOR)
    screen.blit(highlight_surface, (display_from_col * SQUARE_SIZE, display_from_row * SQUARE_SIZE))
    
    # Highlight the "to" square
    highlight_surface.fill(HIGHLIGHT_COLOR)
    screen.blit(highlight_surface, (display_to_col * SQUARE_SIZE, display_to_row * SQUARE_SIZE))

def draw_button(text, x, y, w, h, color, hover_color, mouse_pos):
    rect = pygame.Rect(x, y, w, h)
    if rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, hover_color, rect)
    else:
        pygame.draw.rect(screen, color, rect)
    draw_text(text, x + w // 2, y + h // 2, center=True, color=WHITE, font=CONSOLE_FONT)
    return rect

def notification(game, message):
    while True:
        screen.blit(menu_background, (0, 0))
        draw_text(message, WIDTH // 2, HEIGHT // 2, color=(255, 0, 0))
        mouse_pos = pygame.mouse.get_pos()
        btn_back = draw_button("Back", WIDTH - 110, HEIGHT - 50, 100, 40, (200, 50, 50), (255, 100, 100), mouse_pos)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.collidepoint(event.pos):
                    game.board.reset()
                    game.move_history.clear()  # Clear move history on reset
                    main_menu()
        pygame.display.flip()

def choose_player_color():
    running = True
    while running:
        screen.blit(menu_background, (0, 0))
        draw_text("Choose Your Color", WIDTH // 2, HEIGHT // 2 - 100, color=BLACK)
        mouse_pos = pygame.mouse.get_pos()
        btn_white = draw_button("White", WIDTH // 2 - 100, HEIGHT // 2 - 40, 200, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
        btn_black = draw_button("Black", WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
        btn_back = draw_button("Back", WIDTH // 2 - 100, HEIGHT // 2 + 80, 200, 40, (200, 50, 50), (255, 100, 100), mouse_pos)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_white.collidepoint(event.pos):
                    return chess.WHITE
                elif btn_black.collidepoint(event.pos):
                    return chess.BLACK
                elif btn_back.collidepoint(event.pos):
                    main_menu()
                    return None
        pygame.display.flip()

def play_vs_ai():
    player_color = choose_player_color()
    if player_color is None:
        return
    game = ChessGame()
    engine = Engine()
    running = True
    suggested_move = None
    promotion_dialog = False
    promotion_from = None
    promotion_to = None
    ai_thinking = False
    move_queue = queue.Queue()
    ai_thread = None
    ai_stats = {}  # To store AI statistics

    def get_ai_move():
        print("AI đang suy nghĩ...")
        start_time = time.time()  # Start timing
        engine.set_position(game.board.fen())
        result = engine.get_best_move_with_stats()
        end_time = time.time()  # End timing
        time_taken = end_time - start_time
        print("Nước đi từ engine:", result["move"])
        # Update AI stats with values from engine
        ai_stats.update({
            "depth": result.get("depth", "-"),
            "score": result.get("score", -60),
            "nodes": result.get("nodes", 0),
            "cutoffs": result.get("cutoffs", 0),
            "evals": result.get("evals", 0),
            "time": time_taken
        })
        move_queue.put(result["move"])

    while running:
        flipped = (player_color == chess.BLACK)
        screen.fill((0, 0, 0))
        draw_board(flipped=flipped)
        draw_pieces(game, flipped=flipped)
        mouse_pos = pygame.mouse.get_pos()
        btn_undo, btn_help, btn_back = draw_console(game, is_ai_mode=True, ai_stats=ai_stats, mouse_pos=mouse_pos, ai_thinking=ai_thinking)
        draw_move_hints(game, game.selected_square, flipped=flipped)
        draw_suggested_move(suggested_move, flipped=flipped)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if promotion_dialog:
                    if btn_queen.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.QUEEN)
                        promotion_dialog = False
                        handle_move_outcome(game)
                    elif btn_rook.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.ROOK)
                        promotion_dialog = False
                        handle_move_outcome(game)
                    elif btn_bishop.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.BISHOP)
                        promotion_dialog = False
                        handle_move_outcome(game)
                    elif btn_knight.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.KNIGHT)
                        promotion_dialog = False
                        handle_move_outcome(game)
                else:
                    if btn_undo.collidepoint(event.pos):
                        if len(game.board.move_stack) >= 2:
                            game.undo()
                            game.undo()
                        elif len(game.board.move_stack) == 1:
                            game.undo()
                        suggested_move = None
                        ai_thinking = False
                        move_queue = queue.Queue()
                        ai_stats.clear()  # Clear AI stats on undo
                    elif btn_help.collidepoint(event.pos):
                        if game.board.turn == player_color:
                            engine.set_position(game.board.fen())
                            result = engine.get_best_move_with_stats()
                            uci_move = result["move"]
                            if uci_move:
                                from_square = chess.square(ord(uci_move[0]) - ord('a'), int(uci_move[1]) - 1)
                                to_square = chess.square(ord(uci_move[2]) - ord('a'), int(uci_move[3]) - 1)
                                promotion = None
                                if len(uci_move) == 5:
                                    promotion_piece = uci_move[4].upper()
                                    promotion = {
                                        'Q': chess.QUEEN,
                                        'R': chess.ROOK,
                                        'B': chess.BISHOP,
                                        'N': chess.KNIGHT
                                    }.get(promotion_piece)
                                suggested_move = chess.Move(from_square, to_square, promotion=promotion)
                    elif btn_back.collidepoint(event.pos):
                        running = False
                        ai_thinking = False
                        move_queue = queue.Queue()
                    else:
                        if game.board.turn == player_color:
                            square = get_square_from_mouse(event.pos, flipped=flipped)
                            if square is None:
                                continue
                            piece = game.get_piece(square)
                            if game.selected_square is not None:
                                piece = game.get_piece(game.selected_square)
                                target_piece = game.get_piece(square)
                                print(f"Trước nước đi - FEN: {game.board.fen()}")
                                move_result = game.move(game.selected_square, square)
                                if move_result["valid"]:
                                    if move_result["promotion_required"]:
                                        promotion_dialog = True
                                        promotion_from = game.selected_square
                                        promotion_to = square
                                    else:
                                        suggested_move = None
                                        handle_move_outcome(game, target_piece)
                                        print(f"Sau nước đi của người chơi - Lịch sử: {[m.uci() for m in game.move_history]}")
                                        print(f"Sau nước đi của người chơi - FEN: {game.board.fen()}")
                                else:
                                    print(f"Nước đi không hợp lệ: từ {chess.square_name(game.selected_square)} đến {chess.square_name(square)}")
                                    game.selected_square = square if game.get_piece(square) and game.get_piece(square).color == game.board.turn else None
                            else:
                                piece = game.get_piece(square)
                                game.selected_square = square if piece and piece.color == game.board.turn else None
                                print(f"Chọn ô nguồn: {square} ({chess.square_name(square)}), quân: {piece}")
                        else:
                            print(f"Không phải lượt của bạn. Đến lượt: {'BLACK' if game.board.turn == chess.BLACK else 'WHITE'}")
                            print(f"Trạng thái bàn cờ FEN: {game.board.fen()}")
        if game.board.turn != player_color and not promotion_dialog and not ai_thinking:
            print("Đến lượt AI. Turn:", "Black" if game.board.turn == chess.BLACK else "White")
            print("FEN gửi cho engine:", game.board.fen())
            ai_thinking = True
            ai_thread = threading.Thread(target=get_ai_move)
            ai_thread.start()
        if ai_thinking and not move_queue.empty():
            uci_move = move_queue.get()
            ai_thinking = False
            if uci_move:
                from_square = chess.square(ord(uci_move[0]) - ord('a'), int(uci_move[1]) - 1)
                to_square = chess.square(ord(uci_move[2]) - ord('a'), int(uci_move[3]) - 1)
                promotion = None
                if len(uci_move) == 5:
                    promotion_piece = uci_move[4].upper()
                    promotion = {
                        'Q': chess.QUEEN,
                        'R': chess.ROOK,
                        'B': chess.BISHOP,
                        'N': chess.KNIGHT
                    }.get(promotion_piece)
                move_result = game.move(from_square, to_square, promotion=promotion)
                if move_result["valid"]:
                    target_piece = game.get_piece(to_square)
                    handle_move_outcome(game, target_piece)
                    print(f"Sau nước đi của AI - Lịch sử: {[m.uci() for m in game.move_history]}")
                    print(f"Sau nước đi của AI - FEN: {game.board.fen()}")
                else:
                    print(f"Nước đi không hợp lệ từ engine: {uci_move}")
            else:
                print("Engine không trả về nước đi hợp lệ.")
                if game.board.is_checkmate():
                    winner = "AI" if game.board.turn != player_color else "Bạn"
                    notification(game, f"Chiếu hết! {winner} thắng.")
                elif game.board.is_stalemate():
                    notification(game, "Hòa cờ!")
                elif game.board.is_insufficient_material():
                    notification(game, "Hòa: Không đủ quân!")
                else:
                    notification(game, "Không có nước đi hợp lệ. Kết thúc ván.")
                game.board.reset()
                game.move_history.clear()
                ai_stats.clear()  # Clear AI stats on game end
        pygame.display.flip()
    if ai_thread and ai_thread.is_alive():
        ai_thread.join()

def handle_move_outcome(game, target_piece=None):
    if game.board.is_checkmate():
        checkmate_sound.play()
        winner = "Trắng" if game.board.turn == chess.BLACK else "Đen"
        notification(game, f"Chiếu hết! {winner} thắng!")
    elif game.board.is_stalemate():
        notification(game, "Hòa cờ!")
    elif game.board.is_insufficient_material():
        notification(game, "Hòa: Không đủ quân!")
    elif game.board.is_seventyfive_moves():
        notification(game, "Hòa: Quy tắc 75 nước!")
    elif game.board.is_fivefold_repetition():
        notification(game, "Hòa: Lặp lại 5 lần!")
    if target_piece:
        capture_sound.play()
    else:
        move_sound.play()
    if game.board.is_check():
        check_sound.play()
    game.selected_square = None

def play_1vs1():
    game = ChessGame()
    engine = Engine()
    running = True
    suggested_move = None
    promotion_dialog = False
    promotion_from = None
    promotion_to = None
    while running:
        flipped = game.board.turn == chess.BLACK
        screen.fill((0, 0, 0))
        draw_board(flipped=flipped)
        draw_pieces(game, flipped=flipped)
        mouse_pos = pygame.mouse.get_pos()
        btn_undo, btn_help, btn_back = draw_console(game, is_ai_mode=False, mouse_pos=mouse_pos, ai_thinking=False)
        draw_move_hints(game, game.selected_square, flipped=flipped)
        draw_suggested_move(suggested_move, flipped=flipped)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if promotion_dialog:
                    if btn_queen.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.QUEEN)
                        promotion_dialog = False
                        suggested_move = None
                        handle_move_outcome(game)
                    elif btn_rook.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.ROOK)
                        promotion_dialog = False
                        suggested_move = None
                        handle_move_outcome(game)
                    elif btn_bishop.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.BISHOP)
                        promotion_dialog = False
                        suggested_move = None
                        handle_move_outcome(game)
                    elif btn_knight.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.KNIGHT)
                        promotion_dialog = False
                        suggested_move = None
                        handle_move_outcome(game)
                else:
                    if btn_undo.collidepoint(event.pos):
                        game.undo()
                        suggested_move = None
                    elif btn_help.collidepoint(event.pos):
                        engine.set_position(game.board.fen())
                        result = engine.get_best_move_with_stats()
                        uci_move = result["move"]
                        if uci_move:
                            from_square = chess.square(ord(uci_move[0]) - ord('a'), int(uci_move[1]) - 1)
                            to_square = chess.square(ord(uci_move[2]) - ord('a'), int(uci_move[3]) - 1)
                            promotion = None
                            if len(uci_move) == 5:
                                promotion_piece = uci_move[4].upper()
                                promotion = {
                                    'Q': chess.QUEEN,
                                    'R': chess.ROOK,
                                    'B': chess.BISHOP,
                                    'N': chess.KNIGHT
                                }.get(promotion_piece)
                            suggested_move = chess.Move(from_square, to_square, promotion=promotion)
                    elif btn_back.collidepoint(event.pos):
                        running = False
                    else:
                        square = get_square_from_mouse(event.pos, flipped=flipped)
                        if square is None:
                            continue
                        piece = game.get_piece(square)
                        if game.selected_square is not None:
                            piece = game.get_piece(game.selected_square)
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
                                print(f"Nước đi không hợp lệ: từ {chess.square_name(game.selected_square)} đến {chess.square_name(square)}")
                                game.selected_square = square if game.get_piece(square) and game.get_piece(square).color == game.board.turn else None
                        else:
                            piece = game.get_piece(square)
                            game.selected_square = square if piece and piece.color == game.board.turn else None
                            print(f"Chọn ô nguồn: {square} ({chess.square_name(square)}), quân: {piece}")
        if promotion_dialog:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            draw_text("Choose", WIDTH // 2, HEIGHT // 2 - 150, FONT, True, (255, 255, 255))
            btn_queen = draw_button("Queen", WIDTH // 2 - 50, HEIGHT // 2 - 100, 100, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
            btn_rook = draw_button("Rook", WIDTH // 2 - 50, HEIGHT // 2 - 40, 100, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
            btn_bishop = draw_button("Bishop", WIDTH // 2 - 50, HEIGHT // 2 + 20, 100, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
            btn_knight = draw_button("Knight", WIDTH // 2 - 50, HEIGHT // 2 + 80, 100, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
        pygame.display.flip()

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
        title = FONT.render("Adjust Volume", True, BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        pygame.draw.rect(screen, (200, 200, 200), slider_rect)
        fill_width = int(slider_rect.width * volume)
        fill_rect = pygame.Rect(slider_min, slider_rect.y, fill_width, slider_rect.height)
        pygame.draw.rect(screen, (100, 100, 100), fill_rect)
        handle_x = slider_min + fill_width
        handle_y = slider_rect.y + slider_rect.height // 2
        pygame.draw.circle(screen, (255, 0, 0), (handle_x, handle_y), handle_radius)
        back_rect = pygame.Rect(WIDTH//2 - 50, slider_rect.y + slider_rect.height + 40, 100, 40)
        pygame.draw.rect(screen, HOVER_COLOR, back_rect)
        back_text = FONT.render("Back", True, WHITE)
        back_text_rect = back_text.get_rect(center=back_rect.center)
        screen.blit(back_text, back_text_rect)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main_menu()