import chess

class Evaluation:
    def __init__(self):
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

    def evaluate(self, board):
        score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.piece_values.get(piece.piece_type, 0)
                if piece.color == chess.WHITE:
                    score += value
                else:
                    score -= value
        return score
    
    # 7
    def evaluate_king_safety(board, game_phase):
        """Tổng hợp yếu tố an toàn Vua (Bot = Đen)"""
        safety_score = 0
        
        # Đánh giá cho cả 2 bên nhưng ưu tiên góc nhìn của Đen
        for color in [chess.BLACK, chess.WHITE]:
            # 1. Điểm nguy hiểm (dương nếu Bot bị đe dọa, âm nếu Người chơi bị đe dọa)
            safety_score += calculate_king_danger(board, color)
            
            # 2. Phạt Vua ở trung tâm (dương nếu Bot bị phạt, âm nếu Người chơi bị phạt)
            safety_score += evaluate_king_center_penalty(board, color, game_phase)
            
            # 3. Điểm nhập thành (dương nếu Bot đã nhập thành, âm nếu Người chơi đã nhập thành)
            safety_score += evaluate_castling(board, color, game_phase)
        
        return safety_score  # Tổng điểm dương = Bot an toàn hơn

    def calculate_king_danger(board, color):
        """Tính nguy hiểm cho Vua (Bot = Đen)"""
        king_square = board.king(color)
        if king_square is None:
            return 0
        
        danger_score = 0
        enemy_color = not color
        attack_weights = {
            chess.PAWN: 2,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 4,
            chess.QUEEN: 5
        }

        # Quét 8 hướng quanh Vua
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Bỏ qua ô Vua đứng
                
                file = chess.square_file(king_square) + dx
                rank = chess.square_rank(king_square) + dy
                
                if 0 <= file < 8 and 0 <= rank < 8:
                    target_square = chess.square(file, rank)
                    attackers = board.attackers(enemy_color, target_square)
                    
                    for attacker in attackers:
                        piece = board.piece_at(attacker)
                        if piece and piece.piece_type in attack_weights:
                            # Điểm dương nếu Bot (Đen) bị tấn công, âm nếu Người chơi bị tấn công
                            danger_score += attack_weights[piece.piece_type]

        # Đảo dấu để điểm dương = Bot (Đen) gặp nguy hiểm
        return danger_score if color == chess.BLACK else -danger_score

    def evaluate_king_center_penalty(board, color, game_phase):
        """Phạt Vua ở trung tâm (Bot = Đen)"""
        if game_phase != 'opening':
            return 0
        
        king_square = board.king(color)
        if king_square is None:
            return 0
        
        CENTER_SQUARES = [chess.D4, chess.E4, chess.D5, chess.E5,
                        chess.D3, chess.E3, chess.D6, chess.E6]
        
        penalty = 0
        if king_square in CENTER_SQUARES:
            penalty = 40  # Phạt Bot (dương)
        elif king_square == (chess.E8 if color == chess.BLACK else chess.E1):
            penalty = 60  # Phạt nặng nếu Bot chưa nhập thành
        
        # Điểm dương nếu Bot bị phạt, âm nếu Người chơi bị phạt
        return penalty if color == chess.BLACK else -penalty

    def evaluate_castling(board, color, game_phase):
        """Đánh giá nhập thành (Bot = Đen)"""
        if game_phase == 'endgame':
            return 0
        
        castling_bonus = 0
        king_square = board.king(color)
        
        # Vị trí nhập thành chuẩn
        castled_positions = {
            chess.BLACK: [chess.G8, chess.C8],
            chess.WHITE: [chess.G1, chess.C1]
        }
        
        if king_square in castled_positions[color]:
            castling_bonus = 35  # Thưởng Bot (dương)
        elif board.has_castling_rights(color):
            castling_bonus = -25  # Phạt Bot (âm)
        
        # Điểm dương nếu Bot an toàn, âm nếu Người chơi an toàn
        return castling_bonus if color == chess.BLACK else -castling_bonus
# 8
    def king_activity_evaluation(board):
            """Đánh giá hoạt động Vua trong tàn cuộc (Bot = Đen)"""
            if get_game_phase(board) != 'endgame':
                return 0
            
            CENTER = (3.5, 3.5)
            MAX_BONUS = 30
            total = 0
            
            for color in [chess.BLACK, chess.WHITE]:  # Duyệt Đen trước
                king_square = board.king(color)
                if not king_square:
                    continue
                
                file = chess.square_file(king_square)
                rank = chess.square_rank(king_square)
                distance = math.sqrt((file - CENTER[0])**2 + (rank - CENTER[1])**2)
                bonus = MAX_BONUS * (1 - distance / 4.95)
                
                # Đảo ngược logic: Thưởng Đen (+), phạt Trắng (-)
                total += bonus if color == chess.BLACK else -bonus
            
            return int(total)
    
    # Định nghĩa lại PIECE_VALUES (Bot = Đen có giá trị dương)
    PIECE_VALUES = {
        'P': -100, 'N': -300, 'B': -300, 'R': -500, 'Q': -900, 'K': 0,  # Trắng
        'p': 100, 'n': 300, 'b': 300, 'r': 500, 'q': 900, 'k': 0         # Đen (bot)
    }

    def get_game_phase(board):
        """Xác định giai đoạn (Bot = Đen)"""
        # Tính tổng giá trị vật chất từ góc nhìn bot (quân Đen là dương)
        material = sum(PIECE_VALUES[p.symbol()] for p in board.piece_map().values())
        
        # Ngưỡng điều chỉnh (ví dụ)
        if material < -2000:    # Khi bot (Đen) mất nhiều quân
            return 'endgame'
        elif material > 2000:   # Khi bot còn nhiều quân
            return 'opening'
        return 'middlegame'