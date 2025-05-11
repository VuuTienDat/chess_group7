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
VICTORY_FONT = pygame.font.Font(os.path.join(font_path, "turok.ttf"), 120)  # 3 times larger for victory message
TITLE_FONT = pygame.font.Font(os.path.join(font_path, "turok.ttf"), 48)  # Larger font for "Chess Game"
CONSOLE_FONT = pygame.font.SysFont('arial', 16)  # Reduced font size to avoid text clipping
BOARD_LABEL_FONT = pygame.font.SysFont('arial', 14)  # Reduced font size for board labels
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
MENU_COLOR = (100, 100, 100)
HOVER_COLOR = (0, 128, 0)  # Dark green for hover
CONSOLE_BG = (50, 50, 50)
LABEL_COLOR = (0, 0, 0)  # Black for board labels
BORDER_COLOR = (255, 255, 255)  # White border for promotion buttons

# Color for highlighting suggested moves (same for both from and to squares)
HIGHLIGHT_COLOR = (100, 149, 237, 128)  # Cornflower Blue with alpha

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
    
    # Draw outline if specified (used for black text to ensure visibility)
    if outline_color:
        outline = font.render(text, True, outline_color)
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                if dx != 0 or dy != 0:
                    outline_rect = outline.get_rect(center=(x + dx, y + dy))
                    screen.blit(outline, outline_rect)
    
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
        screen.blit(label, (display_col * SQUARE_SIZE + 2, (7 * SQUARE_SIZE) + SQUARE_SIZE - 20))  # Adjusted to raise labels up
    
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
    
    TITLE_COLOR = (255, 215, 0)

    # --- Panel chess ---
    # Title
    title = CONSOLE_FONT.render("Panel chess", True, TITLE_COLOR)
    title_rect = title.get_rect(center=(BOARD_WIDTH + CONSOLE_WIDTH // 2, 10 + title.get_height() // 2))
    screen.blit(title, title_rect)

    # Game state info
    y_offset = 40
    turn = "WHITE" if game.board.turn == chess.WHITE else "BLACK"

    # Define colors for WHITE and BLACK
    WHITE_TURN_COLOR = (255, 255, 255)  # Bright white for WHITE
    BLACK_TURN_COLOR = (150, 150, 150)  # Dark gray for BLACK
    turn_color = WHITE_TURN_COLOR if turn == "WHITE" else BLACK_TURN_COLOR

    # Render "Turn:" and the turn value ("WHITE" or "BLACK") separately
    turn_label = CONSOLE_FONT.render("Turn: ", True, WHITE)  # "Turn:" in default white
    turn_value = CONSOLE_FONT.render(turn, True, turn_color)  # "WHITE" or "BLACK" with specific color

    # Calculate positions to display them side by side
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
    # Move history (White Black in columns)
    white_label = CONSOLE_FONT.render("White", True, WHITE)
    black_label = CONSOLE_FONT.render("Black", True, WHITE)
    screen.blit(white_label, (BOARD_WIDTH + 10, y_offset))
# "Black" aligned to the right (adjust based on console width)
    black_label_width = black_label.get_width()
    screen.blit(black_label, (BOARD_WIDTH + CONSOLE_WIDTH - black_label_width - 10, y_offset))  # 10 pixels padding from right edge

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
            black_move_width = black_move_label.get_width()
            screen.blit(black_move_label, (BOARD_WIDTH + CONSOLE_WIDTH - black_move_width - 10, y_offset))  # Align black move to the right
        y_offset += 20

    # Display total moves at the bottom
    total_moves = len(paired_moves)  # Will be 0 if no moves yet
    draw_text(f"Total moves: {total_moves}", BOARD_WIDTH + 10, y_offset, font=CONSOLE_FONT, center=False, color=WHITE)

    # --- Panel AI (only in AI mode) ---
    if is_ai_mode:
        y_offset = panel_height + 10
        title = CONSOLE_FONT.render("Panel AI", True, TITLE_COLOR)
        title_rect = title.get_rect(center=(BOARD_WIDTH + CONSOLE_WIDTH // 2, y_offset + title.get_height() // 2))
        screen.blit(title, title_rect)

        y_offset += 25
        algorithm = "MORA (Alpha Beta)"
        draw_text(f"Algorithm: {algorithm}", BOARD_WIDTH + 10, y_offset, 
                  font=CONSOLE_FONT, center=False, color=WHITE)

        y_offset += 25
        depth = ai_stats.get("depth", "-") if ai_stats else "-"
        draw_text(f"DEPTH: {depth}", BOARD_WIDTH + 10, y_offset, 
                  font=CONSOLE_FONT, center=False, color=WHITE)

        y_offset += 25
        max_score = ai_stats.get("score", "-") if ai_stats else "-"
        draw_text(f"MAX SCORE: {max_score}", BOARD_WIDTH + 10, y_offset, 
                  font=CONSOLE_FONT, center=False, color=WHITE)

        y_offset += 25
        if ai_stats and "nodes" in ai_stats:
            nodes_header = "NODES".ljust(10)
            time_header = "TIME".ljust(8)
            draw_text(f"{nodes_header}{time_header}", BOARD_WIDTH + 10, y_offset, 
                      font=CONSOLE_FONT, center=False, color=WHITE)
            y_offset += 20
            nodes = str(ai_stats.get("nodes", 0)).ljust(10)
            time_taken = f"{ai_stats.get('time', 0.0):.4f}".ljust(8)
            draw_text(f"{nodes}{time_taken}", BOARD_WIDTH + 10, y_offset, 
                      font=CONSOLE_FONT, center=False, color=WHITE)

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

    # Highlight both the "from" and to squares with the same color
    highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    
    # Highlight the "from" square
    highlight_surface.fill(HIGHLIGHT_COLOR)
    screen.blit(highlight_surface, (display_from_col * SQUARE_SIZE, display_from_row * SQUARE_SIZE))
    
    # Highlight the "to" square
    highlight_surface.fill(HIGHLIGHT_COLOR)
    screen.blit(highlight_surface, (display_to_col * SQUARE_SIZE, display_to_row * SQUARE_SIZE))

def draw_button(text, x, y, w, h, color, hover_color, mouse_pos, text_color=WHITE, border=False):
    rect = pygame.Rect(x, y, w, h)
    if rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, hover_color, rect)
    else:
        pygame.draw.rect(screen, color, rect)
    if border:
        pygame.draw.rect(screen, BORDER_COLOR, rect, 2)  # Draw border (now white)
    draw_text(text, x + w // 2, y + h // 2, center=True, color=text_color, font=CONSOLE_FONT)
    return rect

def notification(game, message, color=(255, 0, 0), is_victory=False, outline_color=None):
    while True:
        screen.blit(menu_background, (0, 0))
        # Use VICTORY_FONT for victory messages, otherwise use FONT
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
                    game.move_history.clear()  # Clear move history on reset
                    main_menu()
        pygame.display.flip()

def choose_player_color():
    running = True
    while running:
        screen.blit(menu_background, (0, 0))
        draw_text("Choose Your Color", WIDTH // 2, HEIGHT // 2 - 100, color=BLACK)
        mouse_pos = pygame.mouse.get_pos()
        btn_white = draw_button("White", WIDTH // 2 - 100, HEIGHT // 2 - 40, 200, 40, (255, 255, 255), (200, 200, 200), mouse_pos, text_color=BLACK)
        btn_black = draw_button("Black", WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 40, (0, 0, 0), (50, 50, 50), mouse_pos, text_color=WHITE)
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
    promotion_dialog_just_activated = False
    ai_thinking = False
    move_queue = queue.Queue()
    ai_thread = None
    ai_stats = {}

    def get_ai_move():
        print("AI is thinking!...")
        start_time = time.time()
        engine.set_position(game.board.fen())
        result = engine.get_best_move_with_stats()
        end_time = time.time()
        time_taken = end_time - start_time
        print("Move from engine:", result["move"])
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
                print(f"Nhấp chuột tại tọa độ: {event.pos}")
                if promotion_dialog:
                    print(f"Xử lý sự kiện phong quân: promotion_from={chess.square_name(promotion_from) if promotion_from is not None else 'None'}, promotion_to={chess.square_name(promotion_to) if promotion_to is not None else 'None'}")
                    print(f"Trạng thái bàn cờ trước khi phong quân: {game.board.fen()}")
                    if btn_queen.collidepoint(event.pos):
                        print(f"Nhấp vào nút Queen, tọa độ: {event.pos}")
                        move_result = game.move(promotion_from, promotion_to, promotion=chess.QUEEN)
                        print(f"Kết quả phong quân QUEEN: {move_result}")
                        if move_result["valid"]:
                            promotion_dialog = False
                            promotion_dialog_just_activated = False
                            suggested_move = None
                            target_piece = game.get_piece(promotion_to)
                            handle_move_outcome(game, target_piece, is_ai_mode=True, player_color=player_color)
                            print(f"After promotion - History: {[m.uci() for m in game.move_history]}")
                            print(f"After promotion - FEN: {game.board.fen()}")
                        else:
                            print(f"Phong quân thất bại: từ {chess.square_name(promotion_from)} đến {chess.square_name(promotion_to)}, QUEEN")
                    elif btn_rook.collidepoint(event.pos):
                        print(f"Nhấp vào nút Rook, tọa độ: {event.pos}")
                        move_result = game.move(promotion_from, promotion_to, promotion=chess.ROOK)
                        print(f"Kết quả phong quân ROOK: {move_result}")
                        if move_result["valid"]:
                            promotion_dialog = False
                            promotion_dialog_just_activated = False
                            suggested_move = None
                            target_piece = game.get_piece(promotion_to)
                            handle_move_outcome(game, target_piece, is_ai_mode=True, player_color=player_color)
                            print(f"After promotion - History: {[m.uci() for m in game.move_history]}")
                            print(f"After promotion - FEN: {game.board.fen()}")
                        else:
                            print(f"Phong quân thất bại: từ {chess.square_name(promotion_from)} đến {chess.square_name(promotion_to)}, ROOK")
                    elif btn_bishop.collidepoint(event.pos):
                        print(f"Nhấp vào nút Bishop, tọa độ: {event.pos}")
                        move_result = game.move(promotion_from, promotion_to, promotion=chess.BISHOP)
                        print(f"Kết quả phong quân BISHOP: {move_result}")
                        if move_result["valid"]:
                            promotion_dialog = False
                            promotion_dialog_just_activated = False
                            suggested_move = None
                            target_piece = game.get_piece(promotion_to)
                            handle_move_outcome(game, target_piece, is_ai_mode=True, player_color=player_color)
                            print(f"After promotion - History: {[m.uci() for m in game.move_history]}")
                            print(f"After promotion - FEN: {game.board.fen()}")
                        else:
                            print(f"Phong quân thất bại: từ {chess.square_name(promotion_from)} đến {chess.square_name(promotion_to)}, BISHOP")
                    elif btn_knight.collidepoint(event.pos):
                        print(f"Nhấp vào nút Knight, tọa độ: {event.pos}")
                        move_result = game.move(promotion_from, promotion_to, promotion=chess.KNIGHT)
                        print(f"Kết quả phong quân KNIGHT: {move_result}")
                        if move_result["valid"]:
                            promotion_dialog = False
                            promotion_dialog_just_activated = False
                            suggested_move = None
                            target_piece = game.get_piece(promotion_to)
                            handle_move_outcome(game, target_piece, is_ai_mode=True, player_color=player_color)
                            print(f"After promotion - History: {[m.uci() for m in game.move_history]}")
                            print(f"After promotion - FEN: {game.board.fen()}")
                        else:
                            print(f"Phong quân thất bại: từ {chess.square_name(promotion_from)} đến {chess.square_name(promotion_to)}, KNIGHT")
                    else:
                        print(f"Nhấp chuột ngoài các nút phong quân, tọa độ: {event.pos}")
                else:
                    if btn_undo.collidepoint(event.pos):
                        if len(game.board.move_stack) >= 2:
                            game.undo()
                            game.undo()
                        elif len(game.board.move_stack) == 1:
                            game.undo()
                        game.selected_square = None  # Reset selected_square after undo
                        suggested_move = None
                        ai_thinking = False
                        move_queue = queue.Queue()
                        ai_stats.clear()
                        print("Đã hoàn tác nước đi, đặt lại selected_square về None")
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
                        square = get_square_from_mouse(event.pos, flipped=flipped)
                        if square is None:
                            print(f"Nhấp chuột ngoài bàn cờ: {event.pos}")
                            continue
                        
                        # If a square is already selected, attempt to move
                        if game.selected_square is not None:
                            print(f"Ô nguồn đã chọn: {chess.square_name(game.selected_square)}")
                            print(f"Ô đích được chọn: {chess.square_name(square)}")
                            print(f"Thử nước đi: từ {chess.square_name(game.selected_square)} đến {chess.square_name(square)}")
                            print(f"Before move - FEN: {game.board.fen()}")
                            # Check if the move is legal by matching from_square and to_square
                            legal_moves = list(game.board.legal_moves)
                            promotion_required = False
                            move_is_legal = False
                            for legal_move in legal_moves:
                                if (legal_move.from_square == game.selected_square and
                                    legal_move.to_square == square):
                                    move_is_legal = True
                                    if legal_move.promotion is not None:
                                        promotion_required = True
                                    break
                            
                            if move_is_legal:
                                if promotion_required:
                                    promotion_dialog = True
                                    promotion_dialog_just_activated = True
                                    promotion_from = game.selected_square
                                    promotion_to = square
                                    print(f"Promotion dialog activated: từ {chess.square_name(promotion_from)} đến {chess.square_name(promotion_to)}")
                                    game.selected_square = None
                                else:
                                    move_result = game.move(game.selected_square, square)
                                    print(f"Kết quả nước đi: {move_result}")
                                    if move_result["valid"]:
                                        suggested_move = None
                                        target_piece = game.get_piece(square)
                                        handle_move_outcome(game, target_piece, is_ai_mode=True, player_color=player_color)
                                        print(f"After player's move - History: {[m.uci() for m in game.move_history]}")
                                        print(f"After player's move - FEN: {game.board.fen()}")
                                    game.selected_square = None
                            else:
                                print(f"Invalid move: từ {chess.square_name(game.selected_square)} đến {chess.square_name(square)}")
                                game.selected_square = None  # Reset selected_square on invalid move
                            print(f"Trạng thái promotion_dialog sau khi xử lý: {promotion_dialog}")
                        else:
                            # Select a new square if none is selected
                            piece = game.get_piece(square)
                            if piece and piece.color == game.board.turn:
                                game.selected_square = square
                                print(f"Selected source square: {square} ({chess.square_name(square)}), piece: {piece}")
                            else:
                                print(f"Không chọn ô nguồn: Ô {chess.square_name(square)} không có quân hợp lệ")
                                game.selected_square = None
                        print(f"Trạng thái selected_square sau khi xử lý: {chess.square_name(game.selected_square) if game.selected_square is not None else 'None'}")
        
        if game.board.turn != player_color and not promotion_dialog and not ai_thinking:
            print("AI's turn. Turn123:", "Black" if game.board.turn == chess.BLACK else "White")
            print("FEN sent to engine:", game.board.fen())
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
                    handle_move_outcome(game, target_piece, is_ai_mode=True, player_color=player_color)
                    print(f"After AI's move - History: {[m.uci() for m in game.move_history]}")
                    print(f"After AI's move - FEN: {game.board.fen()}")
                else:
                    print(f"Invalid move from engine: {uci_move}")
            else:
                print("Engine did not return a valid move.")
                if game.board.is_checkmate():
                    winner = "You" if game.board.turn != player_color else "AI"
                    winner_color = WHITE if game.board.turn != player_color else BLACK
                    outline = WHITE if winner_color == BLACK else None
                    notification(game, f"{winner} Wins!", color=winner_color, is_victory=True, outline_color=outline)
                elif game.board.is_stalemate():
                    notification(game, "Stalemate!")
                elif game.board.is_insufficient_material():
                    notification(game, "Draw: Insufficient material!")
                else:
                    notification(game, "No valid moves. Game over.")
                game.board.reset()
                game.move_history.clear()
                ai_stats.clear()
        
        if promotion_dialog:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            draw_text("Choose Promotion", WIDTH // 2, HEIGHT // 2 - 180, FONT, True, (255, 255, 255))
            btn_queen = draw_button("Queen", WIDTH // 2 - 75, HEIGHT // 2 - 120, 150, 50, (50, 50, 200), (100, 100, 255), mouse_pos, border=True)
            btn_rook = draw_button("Rook", WIDTH // 2 - 75, HEIGHT // 2 - 60, 150, 50, (50, 50, 200), (100, 100, 255), mouse_pos, border=True)
            btn_bishop = draw_button("Bishop", WIDTH // 2 - 75, HEIGHT // 2, 150, 50, (50, 50, 200), (100, 100, 255), mouse_pos, border=True)
            btn_knight = draw_button("Knight", WIDTH // 2 - 75, HEIGHT // 2 + 60, 150, 50, (50, 50, 200), (100, 100, 255), mouse_pos, border=True)
            if promotion_dialog_just_activated:
                print("Vẽ hộp thoại phong quân")
                print(f"Vị trí nút Queen: {btn_queen}")
                print(f"Vị trí nút Rook: {btn_rook}")
                print(f"Vị trí nút Bishop: {btn_bishop}")
                print(f"Vị trí nút Knight: {btn_knight}")
                promotion_dialog_just_activated = False
        
        pygame.display.flip()
    
    if ai_thread and ai_thread.is_alive():
        ai_thread.join()

def handle_move_outcome(game, target_piece=None, is_ai_mode=False, player_color=None):
    if game.board.is_checkmate():
        checkmate_sound.play()
        if is_ai_mode:
            # In AI mode, determine if the player or AI wins
            winner = "You" if game.board.turn != player_color else "AI"
            winner_color = WHITE if game.board.turn != player_color else BLACK
            outline = WHITE if winner_color == BLACK else None
            notification(game, f"{winner} Wins!", color=winner_color, is_victory=True, outline_color=outline)
        else:
            # In 1v1 mode, determine if White or Black wins
            winner = "White" if game.board.turn == chess.BLACK else "Black"
            winner_color = WHITE if winner == "White" else BLACK
            outline = WHITE if winner_color == BLACK else None
            notification(game, f"{winner} Wins!", color=winner_color, is_victory=True, outline_color=outline)
    elif game.board.is_stalemate():
        notification(game, "Stalemate!")
    elif game.board.is_insufficient_material():
        notification(game, "Draw: Insufficient material!")
    elif game.board.is_seventyfive_moves():
        notification(game, "Draw: 75-move rule!")
    elif game.board.is_fivefold_repetition():
        notification(game, "Draw: Fivefold repetition!")
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
    promotion_dialog_just_activated = False
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
                print(f"Nhấp chuột tại tọa độ: {event.pos}")
                if promotion_dialog:
                    print(f"Xử lý sự kiện phong quân: promotion_from={chess.square_name(promotion_from) if promotion_from is not None else 'None'}, promotion_to={chess.square_name(promotion_to) if promotion_to is not None else 'None'}")
                    print(f"Trạng thái bàn cờ trước khi phong quân: {game.board.fen()}")
                    if btn_queen.collidepoint(event.pos):
                        print(f"Nhấp vào nút Queen, tọa độ: {event.pos}")
                        move_result = game.move(promotion_from, promotion_to, promotion=chess.QUEEN)
                        print(f"Kết quả phong quân QUEEN: {move_result}")
                        if move_result["valid"]:
                            promotion_dialog = False
                            promotion_dialog_just_activated = False
                            suggested_move = None
                            target_piece = game.get_piece(promotion_to)
                            handle_move_outcome(game, target_piece, is_ai_mode=False)
                            print(f"After promotion - History: {[m.uci() for m in game.move_history]}")
                            print(f"After promotion - FEN: {game.board.fen()}")
                        else:
                            print(f"Phong quân thất bại: từ {chess.square_name(promotion_from)} đến {chess.square_name(promotion_to)}, QUEEN")
                    elif btn_rook.collidepoint(event.pos):
                        print(f"Nhấp vào nút Rook, tọa độ: {event.pos}")
                        move_result = game.move(promotion_from, promotion_to, promotion=chess.ROOK)
                        print(f"Kết quả phong quân ROOK: {move_result}")
                        if move_result["valid"]:
                            promotion_dialog = False
                            promotion_dialog_just_activated = False
                            suggested_move = None
                            target_piece = game.get_piece(promotion_to)
                            handle_move_outcome(game, target_piece, is_ai_mode=False)
                            print(f"After promotion - History: {[m.uci() for m in game.move_history]}")
                            print(f"After promotion - FEN: {game.board.fen()}")
                        else:
                            print(f"Phong quân thất bại: từ {chess.square_name(promotion_from)} đến {chess.square_name(promotion_to)}, ROOK")
                    elif btn_bishop.collidepoint(event.pos):
                        print(f"Nhấp vào nút Bishop, tọa độ: {event.pos}")
                        move_result = game.move(promotion_from, promotion_to, promotion=chess.BISHOP)
                        print(f"Kết quả phong quân BISHOP: {move_result}")
                        if move_result["valid"]:
                            promotion_dialog = False
                            promotion_dialog_just_activated = False
                            suggested_move = None
                            target_piece = game.get_piece(promotion_to)
                            handle_move_outcome(game, target_piece, is_ai_mode=False)
                            print(f"After promotion - History: {[m.uci() for m in game.move_history]}")
                            print(f"After promotion - FEN: {game.board.fen()}")
                        else:
                            print(f"Phong quân thất bại: từ {chess.square_name(promotion_from)} đến {chess.square_name(promotion_to)}, BISHOP")
                    elif btn_knight.collidepoint(event.pos):
                        print(f"Nhấp vào nút Knight, tọa độ: {event.pos}")
                        move_result = game.move(promotion_from, promotion_to, promotion=chess.KNIGHT)
                        print(f"Kết quả phong quân KNIGHT: {move_result}")
                        if move_result["valid"]:
                            promotion_dialog = False
                            promotion_dialog_just_activated = False
                            suggested_move = None
                            target_piece = game.get_piece(promotion_to)
                            handle_move_outcome(game, target_piece, is_ai_mode=False)
                            print(f"After promotion - History: {[m.uci() for m in game.move_history]}")
                            print(f"After promotion - FEN: {game.board.fen()}")
                        else:
                            print(f"Phong quân thất bại: từ {chess.square_name(promotion_from)} đến {chess.square_name(promotion_to)}, KNIGHT")
                    else:
                        print(f"Nhấp chuột ngoài các nút phong quân, tọa độ: {event.pos}")
                else:
                    if btn_undo.collidepoint(event.pos):
                        game.undo()
                        game.selected_square = None  # Reset selected_square after undo
                        suggested_move = None
                        print("Đã hoàn tác nước đi, đặt lại selected_square về None")
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
                            print(f"Nhấp chuột ngoài bàn cờ: {event.pos}")
                            continue
                        # If a square is already selected, attempt to move
                        if game.selected_square is not None:
                            print(f"Ô nguồn đã chọn: {chess.square_name(game.selected_square)}")
                            print(f"Ô đích được chọn: {chess.square_name(square)}")
                            print(f"Thử nước đi: từ {chess.square_name(game.selected_square)} đến {chess.square_name(square)}")
                            print(f"Before move - FEN: {game.board.fen()}")
                            # Check if the move is legal by matching from_square and to_square
                            legal_moves = list(game.board.legal_moves)
                            promotion_required = False
                            move_is_legal = False
                            for legal_move in legal_moves:
                                if (legal_move.from_square == game.selected_square and
                                    legal_move.to_square == square):
                                    move_is_legal = True
                                    if legal_move.promotion is not None:
                                        promotion_required = True
                                    break
                            
                            if move_is_legal:
                                if promotion_required:
                                    promotion_dialog = True
                                    promotion_dialog_just_activated = True
                                    promotion_from = game.selected_square
                                    promotion_to = square
                                    print(f"Promotion dialog activated: từ {chess.square_name(promotion_from)} đến {chess.square_name(promotion_to)}")
                                    game.selected_square = None
                                else:
                                    move_result = game.move(game.selected_square, square)
                                    print(f"Kết quả nước đi: {move_result}")
                                    if move_result["valid"]:
                                        suggested_move = None
                                        target_piece = game.get_piece(square)
                                        handle_move_outcome(game, target_piece, is_ai_mode=False)
                                        print(f"After move - History: {[m.uci() for m in game.move_history]}")
                                        print(f"After move - FEN: {game.board.fen()}")
                                    game.selected_square = None
                            else:
                                print(f"Invalid move: từ {chess.square_name(game.selected_square)} đến {chess.square_name(square)}")
                                game.selected_square = None  # Reset selected_square on invalid move
                            print(f"Trạng thái promotion_dialog sau khi xử lý: {promotion_dialog}")
                        else:
                            # Select a new square if none is selected
                            piece = game.get_piece(square)
                            if piece and piece.color == game.board.turn:
                                game.selected_square = square
                                print(f"Selected source square: {square} ({chess.square_name(square)}), piece: {piece}")
                            else:
                                print(f"Không chọn ô nguồn: Ô {chess.square_name(square)} không có quân hợp lệ")
                                game.selected_square = None
                        print(f"Trạng thái selected_square sau khi xử lý: {chess.square_name(game.selected_square) if game.selected_square is not None else 'None'}")
        if promotion_dialog:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            draw_text("Choose Promotion", WIDTH // 2, HEIGHT // 2 - 180, FONT, True, (255, 255, 255))
            btn_queen = draw_button("Queen", WIDTH // 2 - 75, HEIGHT // 2 - 120, 150, 50, (50, 50, 200), (100, 100, 255), mouse_pos, border=True)
            btn_rook = draw_button("Rook", WIDTH // 2 - 75, HEIGHT // 2 - 60, 150, 50, (50, 50, 200), (100, 100, 255), mouse_pos, border=True)
            btn_bishop = draw_button("Bishop", WIDTH // 2 - 75, HEIGHT // 2, 150, 50, (50, 50, 200), (100, 100, 255), mouse_pos, border=True)
            btn_knight = draw_button("Knight", WIDTH // 2 - 75, HEIGHT // 2 + 60, 150, 50, (50, 50, 200), (100, 100, 255), mouse_pos, border=True)
            if promotion_dialog_just_activated:
                print("Vẽ hộp thoại phong quân")
                print(f"Vị trí nút Queen: {btn_queen}")
                print(f"Vị trí nút Rook: {btn_rook}")
                print(f"Vị trí nút Bishop: {btn_bishop}")
                print(f"Vị trí nút Knight: {btn_knight}")
                promotion_dialog_just_activated = False
        pygame.display.flip()

def main_menu():
    running = True
    while running:
        screen.blit(menu_background, (0, 0))
        title = TITLE_FONT.render("Chess Game", True, BLACK)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        btn_1v1 = draw_text("Play 1 vs 1", WIDTH // 2, 250)
        btn_vs_ai = draw_text("Play vs AI", WIDTH // 2, 320)
        btn_music = draw_text("Music", WIDTH // 2, 390)
        btn_quit = draw_text("Exit", WIDTH // 2, 460)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if btn_1v1.collidepoint(mouse_x, mouse_y):
            draw_text("Play 1 vs 1", WIDTH // 2, 250, color=HOVER_COLOR)
        if btn_vs_ai.collidepoint(mouse_x, mouse_y):
            draw_text("Play vs AI", WIDTH // 2, 320, color=HOVER_COLOR)
        if btn_music.collidepoint(mouse_x, mouse_y):
            draw_text("Music", WIDTH // 2, 390, color=HOVER_COLOR)
        if btn_quit.collidepoint(mouse_x, mouse_y):
            draw_text("Exit", WIDTH // 2, 460, color=HOVER_COLOR)
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
        pygame.draw.circle(screen, (0, 128, 0), (handle_x, handle_y), handle_radius)
        back_rect = pygame.Rect(WIDTH//2 - 50, slider_rect.y + slider_rect.height + 40, 100, 40)
        pygame.draw.rect(screen, HOVER_COLOR, back_rect)
        back_text = FONT.render("Back", True, WHITE)
        back_text_rect = back_text.get_rect(center=back_rect.center)
        screen.blit(back_text, back_text_rect)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main_menu()