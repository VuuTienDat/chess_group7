import pygame
import chess
from chess_game import ChessGame
import sys
import os
import json
from Engine.engine import Engine
from Engine.search import Search
import json
from Engine.memory import load_memory, save_memory
import chess
    
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

music_path = os.path.join(bundle_dir, "Music")
image_path = os.path.join(bundle_dir, "Image")
font_path = os.path.join(bundle_dir, "Font")
WIDTH, HEIGHT = 640, 720
SQUARE_SIZE = WIDTH // 8

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Game")
pygame.mixer.init()

pygame.mixer.music.load(os.path.join(music_path, "chessmusic.mp3"))
pygame.mixer.music.play(-1)
music_on = True
move_sound = pygame.mixer.Sound(os.path.join(music_path, "Move.mp3"))
capture_sound = pygame.mixer.Sound(os.path.join(music_path, "Capture.mp3"))
check_sound = pygame.mixer.Sound(os.path.join(music_path, "Check.mp3"))
checkmate_sound = pygame.mixer.Sound(os.path.join(music_path, "Checkmate.mp3"))

board_colors = [(240, 217, 181), (181, 136, 99)]

images = {}
pieces = ["P", "N", "B", "R", "Q", "K"]
for color in ["w", "b"]:
    for p in pieces:
        name = color + p
        images[name] = pygame.transform.scale(
            pygame.image.load(os.path.join(image_path, f"{name}.png")), (SQUARE_SIZE, SQUARE_SIZE)
        )

FONT = pygame.font.Font(os.path.join(font_path, "turok.ttf"), 40)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
MENU_COLOR = (100, 100, 100)
HOVER_COLOR = (255, 0, 0)
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
                    main_menu()
        pygame.display.flip()
def play_vs_ai():
    game = ChessGame()
    engine = Engine()
    running = True
    suggested_move = None
    promotion_dialog = False
    promotion_from = None
    promotion_to = None
    
    while running:
        draw_board()
        draw_pieces(game)
        mouse_pos = pygame.mouse.get_pos()
        
        # Vẽ các nút
        btn_undo = draw_button("Undo", 10, 660, 100, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
        btn_help = draw_button("Help", 120, 660, 100, 40, (50, 200, 50), (100, 255, 100), mouse_pos)
        btn_back = draw_button("Back", WIDTH - 110, 660, 100, 40, (200, 50, 50), (255, 100, 100), mouse_pos)
        
        # Vẽ gợi ý nước đi cho ô được chọn
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
                        target_piece = game.get_piece(square)
                        if game.move(game.selected_square, square):
                            if game.board.is_checkmate():
                                checkmate_sound.play()
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
                            if target_piece:
                                capture_sound.play()
                            else:
                                move_sound.play()
                            if game.board.is_check():
                                check_sound.play()
                            game.selected_square = None
                        else:
                            game.selected_square = square if piece and piece.color == game.board.turn else None
                    else:
                        game.selected_square = square if piece and piece.color == game.board.turn else None
        
        pygame.display.flip()

        # AI đưa ra nước đi khi đến lượt của nó
        if game.board.turn == chess.BLACK:
            engine.set_position(game.board.fen())
            uci_move = engine.get_best_move()
            if uci_move:
                from_square = chess.square(
                    ord(uci_move[0]) - ord('a'),
                    int(uci_move[1]) - 1
                )
                to_square = chess.square(
                    ord(uci_move[2]) - ord('a'),
                    int(uci_move[3]) - 1
                )
                move = chess.Move(from_square, to_square)
                # Xử lý phong cấp
                if len(uci_move) == 5:  # UCI move có phong cấp (e7e8q)
                    promotion_piece = uci_move[4].upper()
                    if promotion_piece == 'Q':
                        move = chess.Move(from_square, to_square, promotion=chess.QUEEN)
                    elif promotion_piece == 'R':
                        move = chess.Move(from_square, to_square, promotion=chess.ROOK)
                    elif promotion_piece == 'B':
                        move = chess.Move(from_square, to_square, promotion=chess.BISHOP)
                    elif promotion_piece == 'N':
                        move = chess.Move(from_square, to_square, promotion=chess.KNIGHT)
                if move in game.board.legal_moves:
                    target_piece = game.get_piece(to_square)
                    game.board.push(move)
                    if game.board.is_check():
                        check_sound.play()
                    if target_piece:
                        capture_sound.play()
                    else:
                        move_sound.play()
                else:
                    print(f"Invalid move from engine: {uci_move}")
            else:
                if game.board.is_checkmate():
                    notification(game, "Checkmate! You lost.")
                elif game.board.is_stalemate():
                    notification(game, "Stalemate!")
                elif game.board.is_insufficient_material():
                    notification(game, "Draw: Insufficient material.")
                else:
                    notification(game, "No legal move. Game Over.")
                game.board.reset()

        pygame.display.flip()

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
    engine = Engine()  # Thêm engine để gợi ý nước đi
    running = True
    suggested_move = None
    promotion_dialog = False
    promotion_from = None
    promotion_to = None
    
    while running:
        draw_board()
        draw_pieces(game)
        mouse_pos = pygame.mouse.get_pos()
        
        # Vẽ các nút
        btn_undo = draw_button("Undo", 10, 660, 100, 40, (50, 50, 200), (100, 100, 255), mouse_pos)
        btn_help = draw_button("Help", 120, 660, 100, 40, (50, 200, 50), (100, 255, 100), mouse_pos)  # Nút Help mới
        btn_back = draw_button("Back", WIDTH - 110, 660, 100, 40, (200, 50, 50), (255, 100, 100), mouse_pos)
        
        # Vẽ gợi ý nước đi cho ô được chọn
        draw_move_hints(game, game.selected_square)
        
        # Tô sáng nước đi gợi ý nếu có
        if suggested_move:
            # Tô sáng ô nguồn (from_square)
            from_square = suggested_move.from_square
            from_col = chess.square_file(from_square)
            from_row = 7 - chess.square_rank(from_square)
            from_center = (from_col * SQUARE_SIZE + SQUARE_SIZE // 2, from_row * SQUARE_SIZE + SQUARE_SIZE // 2)
            pygame.draw.circle(screen, (0, 0, 255), from_center, 20, 3)  # Vòng tròn xanh lam cho ô nguồn
            
            # Tô sáng ô đích (to_square)
            to_square = suggested_move.to_square
            to_col = chess.square_file(to_square)
            to_row = 7 - chess.square_rank(to_square)
            to_center = (to_col * SQUARE_SIZE + SQUARE_SIZE // 2, to_row * SQUARE_SIZE + SQUARE_SIZE // 2)
            pygame.draw.circle(screen, (255, 255, 0), to_center, 20, 3)  # Vòng tròn vàng cho ô đích
        
      
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if promotion_dialog:
                    # Xử lý chọn quân phong cấp
                    
                    if btn_queen.collidepoint(event.pos):
                        game.move(promotion_from, promotion_to, promotion=chess.QUEEN)
                        promotion_dialog = False
                        suggested_move = None  # Xóa gợi ý sau khi đi
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
                    screen.blit(menu_background, (0, 0))
                else:
                    if btn_undo.collidepoint(event.pos):
                        game.undo()
                        suggested_move = None
                    elif btn_help.collidepoint(event.pos):
                        # Gợi ý nước đi cho lượt hiện tại (Trắng hoặc Đen)
                        engine.set_position(game.board.fen())
                        uci_move = engine.get_best_move()
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
                        x, y = event.pos
                        col = x // SQUARE_SIZE
                        row = 7 - (y // SQUARE_SIZE)
                        if not (0 <= col < 8 and 0 <= row < 8):
                            continue
                        square = chess.square(col, row)
                        piece = game.get_piece(square)
                        
                        
                        if game.selected_square is not None:
                            piece = game.get_piece(game.selected_square)
                            target_piece = game.get_piece(square)
                            move_result = game.move(game.selected_square, square)
                            if move_result["valid"]:
                                if move_result["promotion_required"]:
                                    # Nếu nước đi là phong cấp, hiển thị hộp thoại phong cấp
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
            #Vẽ giao diện chọn phong cấp
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            draw_text("Choose", WIDTH // 2, HEIGHT // 2 - 150, FONT, (255, 255, 255))
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