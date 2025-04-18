import pygame
import chess
from chess_game import ChessGame
import sys
import os
from Engine.engine import Engine

import json

import chess

class HeuristicEvaluator:
    def __init__(self):
        self.piece_values = {
            'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
        }
        self._init_piece_square_tables()
        self.game_phase_weights = {
            'opening': {'material': 1.0, 'position': 0.8, 'pawn_structure': 0.6, 
                       'mobility': 0.7, 'threats': 0.9},
            'endgame': {'material': 0.8, 'position': 0.5, 'pawn_structure': 1.2, 
                       'king_activity': 1.5, 'threats': 1.1}
        }

    def _init_piece_square_tables(self):
        self.tables = {
            'P': [
                0,   5,   5, -10, -10,   5,   5,   0,
                5,  10,  10,   0,   0,  10,  10,   5,
                5,  10,  20,  20,  20,  20,  10,   5,
                10,  20,  20,  30,  30,  20,  20,  10,
                10,  20,  20,  30,  30,  20,  20,  10,
                5,  10,  20,  20,  20,  20,  10,   5,
                5,  10,  10,   0,   0,  10,  10,   5,
                0,   5,   5, -10, -10,   5,   5,   0,
            ],
            'N': [
                -50,-40,-30,-30,-30,-30,-40,-50,
                -40,-20,  0,   5,   5,  0,-20,-40,
                -30,  5, 10,  15,  15, 10,  5,-30,
                -30,  0, 15,  20,  20, 15,  0,-30,
                -30,  5, 15,  20,  20, 15,  5,-30,
                -30,  0, 10,  15,  15, 10,  0,-30,
                -40,-20,  0,   0,   0,  0,-20,-40,
                -50,-40,-30,-30,-30,-30,-40,-50,
            ],
            'B': [
                -20,-10,-10,-10,-10,-10,-10,-20,
                -10,  5,  0,   0,   0,  0,  5,-10,
                -10, 10, 10,  10,  10, 10, 10,-10,
                -10,  0, 10,  10,  10, 10,  0,-10,
                -10,  5,  5,  10,  10,  5,  5,-10,
                -10,  0,  5,  10,  10,  5,  0,-10,
                -10,  0,  0,   0,   0,  0,  0,-10,
                -20,-10,-10,-10,-10,-10,-10,-20,
            ],
            'R': [
                0,   0,   5,  10,  10,   5,   0,   0,
                0,   0,   5,  10,  10,   5,   0,   0,
                0,   0,   5,  10,  10,   5,   0,   0,
                0,   0,   5,  10,  10,   5,   0,   0,
                0,   0,   5,  10,  10,   5,   0,   0,
                0,   0,   5,  10,  10,   5,   0,   0,
                25,  25,  25,  25,  25,  25,  25,  25,
                0,   0,   5,  10,  10,   5,   0,   0,
            ],
            'Q': [
                -20,-10,-10, -5,  -5,-10,-10,-20,
                -10,  0,  0,   0,   0,  0,  0,-10,
                -10,  0,  5,   5,   5,  5,  0,-10,
                -5,  0,  5,   5,   5,  5,  0, -5,
                0,  0,  5,   5,   5,  5,  0, -5,
                -10,  5,  5,   5,   5,  5,  0,-10,
                -10,  0,  5,   0,   0,  0,  0,-10,
                -20,-10,-10, -5,  -5,-10,-10,-20,
            ],
            'K': [
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -20,-30,-30,-40,-40,-30,-30,-20,
                -10,-20,-20,-20,-20,-20,-20,-10,
                20, 20,  0,   0,   0,  0, 20, 20,
                20, 30, 10,   0,   0, 10, 30, 20,
            ]
        }

    def evaluate_board(self, board):
        game_phase = self._detect_game_phase(board)
        weights = self.game_phase_weights[game_phase]
        
        score = 0
        score += self._calculate_material(board) * weights['material']
        score += self._piece_square_evaluation(board) * weights['position']
        score += self._evaluate_pawn_structure(board) * weights.get('pawn_structure', 1.0)
        score += self._mobility_evaluation(board) * weights.get('mobility', 1.0)
        score += self._evaluate_hanging_pieces(board) * weights.get('threats', 1.0)
        score += self._safety_evaluation(board)  # Thành phần an toàn quân thêm vào

        if game_phase == 'endgame':
            score += self._king_activity_evaluation(board) * weights['king_activity']
        
        if board.is_repetition(count=2):
            score -= 500 if board.turn == chess.WHITE else -500
            
        return score
    
    def _safety_evaluation(self, board):
        safety_penalty = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                attackers = board.attackers(not piece.color, square)
                defenders = board.attackers(piece.color, square)
                # Nếu quân bị tấn công nhiều hơn được bảo vệ
                if len(attackers) > len(defenders):
                    # Áp dụng phạt theo giá trị quân
                    value = self.piece_values.get(piece.symbol().upper(), 0)
                    penalty = (len(attackers) - len(defenders)) * value * 0.02  # điều chỉnh hệ số phù hợp
                    safety_penalty += penalty if piece.color == chess.WHITE else -penalty
        return safety_penalty

    def _detect_game_phase(self, board):
        queen_count = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
        minor_pieces = len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.BLACK)) + \
                      len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.BLACK))
        return 'endgame' if queen_count == 0 and minor_pieces <= 2 else 'opening'

    def _evaluate_hanging_pieces(self, board):
        hanging_score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                attackers = board.attackers(not piece.color, square)
                defenders = board.attackers(piece.color, square)
                # Nếu số tấn công vượt quá số bảo vệ, quân đó đang "treo"
                if len(attackers) > len(defenders):
                    value = self.piece_values.get(piece.symbol().upper(), 0)
                    # Nếu quân là quan trọng (ví dụ: Q, R) thì phạt cao hơn
                    if piece.symbol().upper() in ['Q', 'R']:
                        factor = 0.5
                    else:
                        factor = 0.3
                    # Cộng dồn phạt theo màu: bên tấn công sẽ được cộng (hoặc trừ điểm đối với đối thủ)
                    hanging_score += value * factor if piece.color == chess.WHITE else -value * factor
        return hanging_score

    def _mobility_evaluation(self, board):
        mobility = 0
        for color in [chess.WHITE, chess.BLACK]:
            temp_board = board.copy(stack=False)
            temp_board.turn = color
            attack_weight = 0
            for move in temp_board.legal_moves:
                if temp_board.is_capture(move):
                    captured_piece = temp_board.piece_at(move.to_square)
                    if captured_piece:
                        base_value = self.piece_values.get(captured_piece.symbol().upper(), 0)
                        multiplier = 0.1
                        # Giả lập nước đi và kiểm tra an toàn của quân bắt
                        temp_board.push(move)
                        # Nếu ô mà quân vừa di chuyển không bị tấn công bởi quân đối phương, tăng multiplier
                        if not temp_board.attackers(not color, move.to_square):
                            multiplier *= 1.5
                        # Nếu ô đó bị ít các cuộc tấn công hơn so với số lượng bảo vệ, tăng thêm một chút
                        else:
                            attackers = temp_board.attackers(not color, move.to_square)
                            defenders = temp_board.attackers(color, move.to_square)
                            if len(defenders) >= len(attackers):
                                multiplier *= 1.2
                        temp_board.pop()
                        attack_weight += base_value * multiplier
            mobility += attack_weight * (1 if color == chess.WHITE else -1)
        return mobility * 50

    def _calculate_material(self, board):
        material = 0
        for piece in board.piece_map().values():
            value = self.piece_values.get(piece.symbol().upper(), 0)
            material += value if piece.color == chess.WHITE else -value
        return material

    def _piece_square_evaluation(self, board):
        position_score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                symbol = piece.symbol().upper()
                table = self.tables.get(symbol)
                if table:
                    pos = square if piece.color == chess.WHITE else chess.square_mirror(square)
                    position_score += table[pos] if piece.color == chess.WHITE else -table[pos]
        return position_score

    def _evaluate_pawn_structure(self, board):
        # Placeholder for pawn structure logic
        return 0

    
def save_human_move(fen, move):
    """
    Lưu trạng thái FEN và nước đi của người chơi vào file human_memory.json.
    """
    memory_file = "human_memory.json"
    try:
        with open(memory_file, "r") as f:
            memory = json.load(f)
    except FileNotFoundError:
        memory = {}

    memory[fen] = move.uci()

    with open(memory_file, "w") as f:
        json.dump(memory, f, indent=4)

def load_human_memory():
    """
    Tải dữ liệu từ file human_memory.json.
    """
    memory_file = "human_memory.json"
    try:
        with open(memory_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_memory(fen, best_move):
    """
    Lưu trạng thái FEN và nước đi (dạng UCI) vào file memory.json.
    Nếu file chưa tồn tại, tạo mới.
    
    Tham số:
      fen (str): Trạng thái FEN của bàn cờ.
      best_move (chess.Move): Nước đi mà AI đã chọn, sẽ được chuyển về dạng UCI.
    """
    memory_file = "memory.json"

    # Tải dữ liệu đã có
    try:
        with open(memory_file, "r") as f:
            memory = json.load(f)
    except FileNotFoundError:
        memory = {}

    # Lưu trạng thái FEN và nước đi tương ứng (convert move về UCI string)
    memory[fen] = best_move.uci()

    # Ghi lại dữ liệu vào file memory.json
    with open(memory_file, "w") as f:
        json.dump(memory, f, indent=4)

def load_memory():
    """
    Tải dữ liệu từ file memory.json.
    
    Trả về:
      dict: Bản đồ {FEN: best_move_uci, ...}
    """
    memory_file = "memory.json"
    try:
        with open(memory_file, "r") as f:
            memory = json.load(f)
        return memory
    except FileNotFoundError:
        return {}
if getattr(sys, 'frozen', False):  # Đang chạy từ .exe
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

#def evaluate_board(board):
    # Giá trị quân cờ (đơn vị điểm cơ bản)
    piece_values = {
        'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
    }
    # Bảng điểm vị trí (piece-square tables) cho từng quân (định nghĩa theo từng ô từ a1 đến h8)
    pawn_table = [
         0,   5,   5, -10, -10,   5,   5,   0,
         5,  10,  10,   0,   0,  10,  10,   5,
         5,  10,  20,  20,  20,  20,  10,   5,
        10,  20,  20,  30,  30,  20,  20,  10,
        10,  20,  20,  30,  30,  20,  20,  10,
         5,  10,  20,  20,  20,  20,  10,   5,
         5,  10,  10,   0,   0,  10,  10,   5,
         0,   5,   5, -10, -10,   5,   5,   0,
    ]
    knight_table = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,   5,   5,  0,-20,-40,
        -30,  5, 10,  15,  15, 10,  5,-30,
        -30,  0, 15,  20,  20, 15,  0,-30,
        -30,  5, 15,  20,  20, 15,  5,-30,
        -30,  0, 10,  15,  15, 10,  0,-30,
        -40,-20,  0,   0,   0,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ]
    bishop_table = [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  5,  0,   0,   0,  0,  5,-10,
        -10, 10, 10,  10,  10, 10, 10,-10,
        -10,  0, 10,  10,  10, 10,  0,-10,
        -10,  5,  5,  10,  10,  5,  5,-10,
        -10,  0,  5,  10,  10,  5,  0,-10,
        -10,  0,  0,   0,   0,  0,  0,-10,
        -20,-10,-10,-10,-10,-10,-10,-20,
    ]
    rook_table = [
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
        25,  25,  25,  25,  25,  25,  25,  25,
         0,   0,   5,  10,  10,   5,   0,   0,
    ]
    queen_table = [
        -20,-10,-10, -5,  -5,-10,-10,-20,
        -10,  0,  0,   0,   0,  0,  0,-10,
        -10,  0,  5,   5,   5,  5,  0,-10,
         -5,  0,  5,   5,   5,  5,  0, -5,
          0,  0,  5,   5,   5,  5,  0, -5,
        -10,  5,  5,   5,   5,  5,  0,-10,
        -10,  0,  5,   0,   0,  0,  0,-10,
        -20,-10,-10, -5,  -5,-10,-10,-20,
    ]
    king_table = [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
         20, 20,  0,   0,   0,  0, 20, 20,
         20, 30, 10,   0,   0, 10, 30, 20,
    ]
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            symbol = piece.symbol().upper()
            value = piece_values.get(symbol, 0)
            # Với quân trắng dùng trực tiếp vị trí, với quân đen dùng vị trí được đảo qua square_mirror
            if piece.color == chess.WHITE:
                if symbol == 'P':
                    table_value = pawn_table[square]
                elif symbol == 'N':
                    table_value = knight_table[square]
                elif symbol == 'B':
                    table_value = bishop_table[square]
                elif symbol == 'R':
                    table_value = rook_table[square]
                elif symbol == 'Q':
                    table_value = queen_table[square]
                elif symbol == 'K':
                    table_value = king_table[square]
                score += value + table_value
            else:
                mirror = chess.square_mirror(square)
                if symbol == 'P':
                    table_value = pawn_table[mirror]
                elif symbol == 'N':
                    table_value = knight_table[mirror]
                elif symbol == 'B':
                    table_value = bishop_table[mirror]
                elif symbol == 'R':
                    table_value = rook_table[mirror]
                elif symbol == 'Q':
                    table_value = queen_table[mirror]
                elif symbol == 'K':
                    table_value = king_table[mirror]
                score -= value + table_value
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
            elif event.type == pygame. MOUSEBUTTONDOWN:
                # Kiểm tra nút Undo, Back trước
                if btn_undo.collidepoint(event.pos):
                    game.undo()
                elif btn_back.collidepoint(event.pos):
                    running = False
                else:
                    square = get_square_from_mouse(event.pos)
                    piece = game.get_piece(square)
                    if game.selected_square:  # Đã chọn quân trước đó
                        target_piece = game.get_piece(square)
                        move_successful = game.move(game.selected_square, square)
                        if move_successful:
                            if game.board.is_checkmate():
                                checkmate_sound.play()
                            elif target_piece:
                                capture_sound.play()
                            else:
                                move_sound.play()
                            
                            if game.board.is_check():
                                check_sound.play()
                            game.selected_square = None
                        else:
                            # Nếu nước đi không hợp lệ, chuyển lựa chọn nếu có quân của mình
                            if piece and piece.color == game.board.turn:
                                game.selected_square = square
                            else:
                                game.selected_square = None
                    else:
                        # Nếu chưa chọn, chọn quân nếu đúng lượt
                        if piece and piece.color == game.board.turn:
                            game.selected_square = square
        
        pygame.display.flip()

        # AI turn dùng alpha-beta search nếu đến lượt của ai (màu đen)
        if game.board.turn == chess.BLACK:
            current_fen = game.board.fen()
            memory = load_memory()
    # Nếu trạng thái đã có trong memory, sử dụng nước đi đã lưu
            if current_fen in memory:
                best_move = chess.Move.from_uci(memory[current_fen])
            else:
                best_move = alpha_beta_search(game.board, 3)  # hoặc thuật toán khác
        # Sau khi tìm được nước đi, lưu vào memory
            if best_move:
                save_memory(current_fen, best_move)
                game.board.push(best_move)
                last_ai_move = best_move  # Cập nhật nước đi của AI
            #else:
            #    notification("No legal move. Game Over.")
            #   game.board.reset()

        pygame.display.flip()

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