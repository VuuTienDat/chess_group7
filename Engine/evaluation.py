import chess
import numpy as np
import math

class Evaluation:
    def __init__(self):
        # Khởi tạo bảng và tham số
        self.init_pst_tables()
        self.init_evaluation_parameters()
        
        # Các hằng số đánh giá
        self.MATE_SCORE = 99999
        self.MATE_THRESHOLD = 90000

    def init_pst_tables(self):
        """Khởi tạo bảng Piece-Square Tables cho khai cuộc và tàn cuộc"""
        self.pst_opening = {
            chess.PAWN: [
                0,   0,   0,   0,   0,   0,   0,   0,
                50,  50,  50,  50,  50,  50,  50,  50,
                10,  10,  20,  30,  30,  20,  10,  10,
                5,   5,  10,  25,  25,  10,   5,   5,
                0,   0,   0,  20,  20,   0,   0,   0,
                5,  -5, -10,   0,   0, -10,  -5,   5,
                5,  10,  10, -20, -20,  10,  10,   5,
                0,   0,   0,   0,   0,   0,   0,   0
            ],
            chess.KNIGHT: [
                -50, -40, -30, -30, -30, -30, -40, -50,
                -40, -20,   0,   0,   0,   0, -20, -40,
                -30,   0,  10,  15,  15,  10,   0, -30,
                -30,   5,  15,  20,  20,  15,   5, -30,
                -30,   0,  15,  20,  20,  15,   0, -30,
                -30,   5,  10,  15,  15,  10,   5, -30,
                -40, -20,   0,   5,   5,   0, -20, -40,
                -50, -40, -30, -30, -30, -30, -40, -50
            ],
            chess.BISHOP: [
                -20, -10, -10, -10, -10, -10, -10, -20,
                -10,   0,   0,   0,   0,   0,   0, -10,
                -10,   0,   5,  10,  10,   5,   0, -10,
                -10,   5,   5,  10,  10,   5,   5, -10,
                -10,   0,  10,  10,  10,  10,   0, -10,
                -10,  10,  10,  10,  10,  10,  10, -10,
                -10,   5,   0,   0,   0,   0,   5, -10,
                -20, -10, -10, -10, -10, -10, -10, -20
            ],
            chess.ROOK: [
                0,   0,   0,   0,   0,   0,   0,   0,
                5,  10,  10,  10,  10,  10,  10,   5,
                -5,   0,   0,   0,   0,   0,   0,  -5,
                -5,   0,   0,   0,   0,   0,   0,  -5,
                -5,   0,   0,   0,   0,   0,   0,  -5,
                -5,   0,   0,   0,   0,   0,   0,  -5,
                -5,   0,   0,   0,   0,   0,   0,  -5,
                0,   0,   0,   5,   5,   0,   0,   0
            ],
            chess.QUEEN: [
                -20, -10, -10,  -5,  -5, -10, -10, -20,
                -10,   0,   0,   0,   0,   0,   0, -10,
                -10,   0,   5,   5,   5,   5,   0, -10,
                -5,   0,   5,   5,   5,   5,   0,  -5,
                0,   0,   5,   5,   5,   5,   0,  -5,
                -10,   5,   5,   5,   5,   5,   0, -10,
                -10,   0,   5,   0,   0,   0,   0, -10,
                -20, -10, -10,  -5,  -5, -10, -10, -20
            ],
            chess.KING: [
                -30, -40, -40, -50, -50, -40, -40, -30,
                -30, -40, -40, -50, -50, -40, -40, -30,
                -30, -40, -40, -50, -50, -40, -40, -30,
                -30, -40, -40, -50, -50, -40, -40, -30,
                -20, -30, -30, -40, -40, -30, -30, -20,
                -10, -20, -20, -20, -20, -20, -20, -10,
                20,  20,   0,   0,   0,   0,  20,  20,
                20,  30,  10,   0,   0,  10,  30,  20
            ]
        }

        self.pst_endgame = {
            chess.KING: [
                -50, -40, -30, -20, -20, -30, -40, -50,
                -30, -20, -10,   0,   0, -10, -20, -30,
                -30, -10,  20,  30,  30,  20, -10, -30,
                -30, -10,  30,  40,  40,  30, -10, -30,
                -30, -10,  30,  40,  40,  30, -10, -30,
                -30, -10,  20,  30,  30,  20, -10, -30,
                -30, -30,   0,   0,   0,   0, -30, -30,
                -50, -30, -30, -30, -30, -30, -30, -50
            ],
            chess.PAWN: [
                0,   0,   0,   0,   0,   0,   0,   0,
                80,  80,  80,  80,  80,  80,  80,  80,
                50,  50,  50,  50,  50,  50,  50,  50,
                30,  30,  30,  30,  30,  30,  30,  30,
                20,  20,  20,  20,  20,  20,  20,  20,
                10,  10,  10,  10,  10,  10,  10,  10,
                10,  10,  10,  10,  10,  10,  10,  10,
                0,   0,   0,   0,   0,   0,   0,   0
            ]
        }

    def init_evaluation_parameters(self):
        """Khởi tạo các tham số đánh giá, bổ sung thêm tham số mới"""
        self.PARAMS = {
            'piece_values': {
                chess.PAWN: 100,
                chess.KNIGHT: 320,
                chess.BISHOP: 330,
                chess.ROOK: 500,
                chess.QUEEN: 900,
                chess.KING: 20000
            },
            'bishop': {
                'pair_bonus': 50,
                'bad_penalty': -25,
                'blocked_penalty': -15,
                'mobility_weight': 0.5  # Thêm trọng số di động
            },
            'knight': {
                'rim_penalty': -20,
                'trapped_penalty': -40,
                'outpost_bonus': 30,
                'mobility_weight': 0.6
            },
            'rook': {
                'open_file_bonus': 25,
                'semi_open_bonus': 15,
                'connected_bonus': 20,
                'seventh_rank_bonus': 40,
                'mobility_weight': 0.4
            },
            'queen': {
                'early_penalty': -20,
                'mobility_weight': 0.4
            },
            'pawn_structure': {  # Thêm tham số cho cấu trúc Tốt
                'isolated_penalty': -20,
                'doubled_penalty': -15,
                'passed_bonus': 50,
                'backward_penalty': -10,
                'chain_bonus': 10
            },
            'center_control': {
                'pawn_center_bonus': 20,
                'piece_center_bonus': 10
            },
            'game_phase_threshold': 8,
            'tempo_bonus': 10
        }

    def get_game_phase(self, board):
        """Xác định giai đoạn ván cờ"""
        total_material = sum(
            len(board.pieces(pt, chess.WHITE)) + len(board.pieces(pt, chess.BLACK))
            for pt in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        )
        return "endgame" if total_material <= self.PARAMS['game_phase_threshold'] else "opening"

    def evaluate(self, board):
        """Hàm đánh giá tổng hợp chính, bổ sung các yếu tố mới"""
        if board.is_checkmate():
            return -self.MATE_SCORE if board.turn == chess.WHITE else self.MATE_SCORE
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        game_phase = self.get_game_phase(board)
        score = 0

        # 1. Đánh giá vật chất và vị trí quân
        score += self.evaluate_material_and_position(board, game_phase)
    
        # 2. Đánh giá đặc điểm riêng từng quân
        score += self.evaluate_piece_specific_features(board, chess.WHITE, game_phase)
        score -= self.evaluate_piece_specific_features(board, chess.BLACK, game_phase)
    
        # 3. Đánh giá an toàn Vua
        score += self.evaluate_king_safety(board, game_phase)
    
        # 4. Đánh giá hoạt động Vua trong tàn cuộc
        score += self.king_activity_evaluation(board)
    
        # 5. Đánh giá cấu trúc Tốt
        score += self.evaluate_pawn_structure(board, chess.WHITE)
        score -= self.evaluate_pawn_structure(board, chess.BLACK)
    
        # 6. Đánh giá kiểm soát trung tâm
        score += self.evaluate_center_control(board, chess.WHITE)
        score -= self.evaluate_center_control(board, chess.BLACK)
    
        # 7. Thưởng nhịp điệu (tempo)
        if board.turn == chess.WHITE:
            score += self.PARAMS['tempo_bonus']
        else:
            score -= self.PARAMS['tempo_bonus']
        
        return score

    def evaluate_material_and_position(self, board, game_phase):
        """Đánh giá vật chất và vị trí quân"""
        score = 0
        white_bishops = 0
        black_bishops = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if not piece:
                continue
                
            value = self.PARAMS['piece_values'][piece.piece_type]
            value += self.get_pst_value(piece, square, game_phase)
            
            if piece.piece_type == chess.BISHOP:
                if piece.color == chess.WHITE:
                    white_bishops += 1
                else:
                    black_bishops += 1
            
            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value
        
        if white_bishops >= 2:
            score += self.PARAMS['bishop']['pair_bonus']
        if black_bishops >= 2:
            score -= self.PARAMS['bishop']['pair_bonus']
            
        return score

    def evaluate_piece_specific_features(self, board, color, game_phase):
        """Đánh giá đặc điểm riêng từng quân, bổ sung tính di động"""
        score = 0
        bishops = []
        rooks = []
    
        for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            for square in board.pieces(piece_type, color):
                if piece_type == chess.KNIGHT:
                    file = chess.square_file(square)
                    if file == 0 or file == 7:
                        score += self.PARAMS['knight']['rim_penalty']
                    if self.is_trapped_knight(board, square, color):
                        score += self.PARAMS['knight']['trapped_penalty']
                    if self.is_knight_outpost(board, square, color):
                        score += self.PARAMS['knight']['outpost_bonus']
                    # Tính di động
                    mobility = len(list(board.attacks(square)))
                    score += mobility * self.PARAMS['knight']['mobility_weight']
            
                elif piece_type == chess.BISHOP:
                    bishops.append(square)
                    if self.is_bad_bishop(board, square, color):
                        score += self.PARAMS['bishop']['bad_penalty']
                    if self.is_blocked_bishop(board, square):
                        score += self.PARAMS['bishop']['blocked_penalty']
                    # Tính di động
                    mobility = len(list(board.attacks(square)))
                    score += mobility * self.PARAMS['bishop']['mobility_weight']
            
                elif piece_type == chess.ROOK:
                    rooks.append(square)
                    file_status = self.get_file_status(board, square, color)
                    if file_status == 'open':
                        score += self.PARAMS['rook']['open_file_bonus']
                    elif file_status == 'semi_open':
                        score += self.PARAMS['rook']['semi_open_bonus']
                    rank = chess.square_rank(square)
                    if (color == chess.WHITE and rank == 6) or (color == chess.BLACK and rank == 1):
                        score += self.PARAMS['rook']['seventh_rank_bonus']
                    # Tính di động
                    mobility = len(list(board.attacks(square)))
                    score += mobility * self.PARAMS['rook']['mobility_weight']
            
                elif piece_type == chess.QUEEN:
                    if game_phase == 'opening' and chess.square_rank(square) > 1:
                        score += self.PARAMS['queen']['early_penalty']
                    mobility = len(list(board.attacks(square)))
                    score += mobility * self.PARAMS['queen']['mobility_weight']
    
        if len(rooks) >= 2 and self.are_connected_rooks(rooks, board, color):
            score += self.PARAMS['rook']['connected_bonus']
        
        return score

    def evaluate_king_safety(self, board, game_phase):
        """Tổng hợp yếu tố an toàn Vua"""
        safety_score = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            safety_score += self.calculate_king_danger(board, color)
            safety_score += self.evaluate_king_center_penalty(board, color, game_phase)
            safety_score += self.evaluate_castling(board, color, game_phase)
        
        return safety_score

    def calculate_king_danger(self, board, color):
        """Tính nguy hiểm cho Vua"""
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

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                file = chess.square_file(king_square) + dx
                rank = chess.square_rank(king_square) + dy
                if 0 <= file < 8 and 0 <= rank < 8:
                    target_square = chess.square(file, rank)
                    attackers = board.attackers(enemy_color, target_square)
                    for attacker in attackers:
                        piece = board.piece_at(attacker)
                        if piece and piece.piece_type in attack_weights:
                            danger_score += attack_weights[piece.piece_type]
        
        return danger_score if color == chess.WHITE else -danger_score

    def evaluate_king_center_penalty(self, board, color, game_phase):
        """Phạt Vua ở trung tâm"""
        if game_phase != 'opening':
            return 0
        
        king_square = board.king(color)
        if king_square is None:
            return 0
        
        CENTER_SQUARES = [chess.D4, chess.E4, chess.D5, chess.E5,
                         chess.D3, chess.E3, chess.D6, chess.E6]
        
        penalty = 0
        if king_square in CENTER_SQUARES:
            penalty = 40
        elif king_square == (chess.E1 if color == chess.WHITE else chess.E8):
            penalty = 60
        
        return penalty if color == chess.WHITE else -penalty

    def evaluate_castling(self, board, color, game_phase):
        """Đánh giá nhập thành"""
        if game_phase == 'endgame':
            return 0
        
        castling_bonus = 0
        king_square = board.king(color)
        
        castled_positions = {
            chess.WHITE: [chess.G1, chess.C1],
            chess.BLACK: [chess.G8, chess.C8]
        }
        
        if king_square in castled_positions[color]:
            castling_bonus = 35
        elif board.has_castling_rights(color):
            castling_bonus = -25
        
        return castling_bonus if color == chess.WHITE else -castling_bonus

    def king_activity_evaluation(self, board):
        """Đánh giá hoạt động Vua trong tàn cuộc"""
        if self.get_game_phase(board) != 'endgame':
            return 0
        
        CENTER = (3.5, 3.5)
        MAX_BONUS = 30
        total = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            king_square = board.king(color)
            if not king_square:
                continue
            file = chess.square_file(king_square)
            rank = chess.square_rank(king_square)
            distance = math.sqrt((file - CENTER[0])**2 + (rank - CENTER[1])**2)
            bonus = MAX_BONUS * (1 - distance / 4.95)
            total += bonus if color == chess.WHITE else -bonus
        
        return int(total)

    def get_pst_value(self, piece, square, game_phase):
        """Lấy giá trị từ bảng PST"""
        table = self.pst_endgame if (game_phase == "endgame" and piece.piece_type in self.pst_endgame) else self.pst_opening
        pst = table.get(piece.piece_type, [0] * 64)
        adjusted_square = square if piece.color == chess.WHITE else chess.square_mirror(square)
        return pst[adjusted_square]

    def is_trapped_knight(self, board, square, color):
        """Kiểm tra Mã bị mắc kẹt"""
        safe_moves = 0
        for move in board.attacks(square):
            if not board.is_attacked_by(not color, move):
                safe_moves += 1
        return safe_moves <= 2

    def is_knight_outpost(self, board, square, color):
        """Kiểm tra Mã ở vị trí tiền đồn"""
        rank = chess.square_rank(square)
        file = chess.square_file(square)
        
        if color == chess.WHITE and rank < 4:
            return False
        if color == chess.BLACK and rank > 3:
            return False
            
        for delta in [-1, 1]:
            if 0 <= file + delta < 8:
                pawn_rank = rank - 1 if color == chess.WHITE else rank + 1
                if 0 <= pawn_rank < 8:  # Kiểm tra rank hợp lệ
                    pawn_square = chess.square(file + delta, pawn_rank)
                    piece = board.piece_at(pawn_square)
                    if piece and piece.piece_type == chess.PAWN and piece.color != color:
                        return False
        return True

    def is_bad_bishop(self, board, square, color):
        """Kiểm tra Tượng bị chặn bởi Tốt cùng màu"""
        pawns = list(board.pieces(chess.PAWN, color))
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        bishop_color = (file + rank) % 2
        blocked_count = 0
        for pawn_sq in pawns:
            p_file = chess.square_file(pawn_sq)
            p_rank = chess.square_rank(pawn_sq)
            if (p_file + p_rank) % 2 == bishop_color:
                blocked_count += 1
            if blocked_count >= 2:
                return True
        return False

    def is_blocked_bishop(self, board, square):
        """Kiểm tra Tượng bị cản đường"""
        for delta in [-9, -7, 7, 9]:
            target = square + delta
            while 0 <= target < 64 and abs(chess.square_file(target) - chess.square_file(target - delta)) == 1:
                piece = board.piece_at(target)
                if piece and piece.color == board.color_at(square):
                    return True
                if piece:
                    break
                target += delta
        return False

    def get_file_status(self, board, square, color):
        """Xác định loại cột"""
        file = chess.square_file(square)
        our_pawns = any(chess.square_file(pawn_sq) == file for pawn_sq in board.pieces(chess.PAWN, color))
        their_pawns = any(chess.square_file(pawn_sq) == file for pawn_sq in board.pieces(chess.PAWN, not color))
        
        if not our_pawns and not their_pawns:
            return 'open'
        elif not our_pawns and their_pawns:
            return 'semi_open'
        return 'closed'

    def are_connected_rooks(self, rooks, board, color):
        """Kiểm tra Xe kết nối"""
        return board.is_attacked_by(color, rooks[1]) or board.is_attacked_by(color, rooks[0])
    
    def evaluate_pawn_structure(self, board, color):
        """Đánh giá cấu trúc Tốt"""
        score = 0
        pawns = list(board.pieces(chess.PAWN, color))
        enemy_pawns = list(board.pieces(chess.PAWN, not color))
    
        # Kiểm tra từng Tốt
        for pawn_sq in pawns:
            file = chess.square_file(pawn_sq)
            rank = chess.square_rank(pawn_sq)
        
            # 1. Tốt yếu (Isolated Pawn)
            is_isolated = True
            for adj_file in [file - 1, file + 1]:
                if 0 <= adj_file < 8:
                    for adj_pawn in pawns:
                        if chess.square_file(adj_pawn) == adj_file:
                            is_isolated = False
                            break
                if not is_isolated:
                    break
            if is_isolated:
                score += self.PARAMS['pawn_structure']['isolated_penalty']
        
            # 2. Tốt đôi (Doubled Pawn)
            same_file_pawns = sum(1 for p in pawns if chess.square_file(p) == file)
            if same_file_pawns > 1:
                score += self.PARAMS['pawn_structure']['doubled_penalty'] * (same_file_pawns - 1)
        
            # 3. Tốt qua sông (Passed Pawn)
            is_passed = True
            for enemy_pawn in enemy_pawns:
                e_file = chess.square_file(enemy_pawn)
                e_rank = chess.square_rank(enemy_pawn)
                if abs(e_file - file) <= 1:
                    if (color == chess.WHITE and e_rank >= rank) or (color == chess.BLACK and e_rank <= rank):
                        is_passed = False
                        break
            if is_passed:
                score += self.PARAMS['pawn_structure']['passed_bonus']
        
            # 4. Tốt lạc hậu (Backward Pawn)
            is_backward = True
            for adj_file in [file - 1, file + 1]:
                if 0 <= adj_file < 8:
                    for adj_pawn in pawns:
                        if chess.square_file(adj_pawn) == adj_file:
                            adj_rank = chess.square_rank(adj_pawn)
                            if (color == chess.WHITE and adj_rank > rank) or (color == chess.BLACK and adj_rank < rank):
                                is_backward = False
                                break
                if not is_backward:
                    break
            if is_backward:
                next_rank = rank + 1 if color == chess.WHITE else rank - 1
                if 0 <= next_rank < 8:
                    next_square = chess.square(file, next_rank)
                    if board.is_attacked_by(not color, next_square):
                        score += self.PARAMS['pawn_structure']['backward_penalty']
        
            # 5. Chuỗi Tốt (Pawn Chain)
            for delta in [-9, 7]:  # Các hướng chéo
                adj_square = pawn_sq + delta
                if 0 <= adj_square < 64 and abs(chess.square_file(adj_square) - file) == 1:
                    adj_piece = board.piece_at(adj_square)
                    if adj_piece and adj_piece.piece_type == chess.PAWN and adj_piece.color == color:
                        score += self.PARAMS['pawn_structure']['chain_bonus']
    
        return score
    
    def evaluate_center_control(self, board, color):
        """Đánh giá kiểm soát trung tâm"""
        score = 0
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    
        for square in center_squares:
            # 1. Tốt ở trung tâm
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN and piece.color == color:
                score += self.PARAMS['center_control']['pawn_center_bonus']
        
            # 2. Quân kiểm soát ô trung tâm
            if board.is_attacked_by(color, square):
                score += self.PARAMS['center_control']['piece_center_bonus']
    
        return score

if __name__ == "__main__":
    evaluator = Evaluation()
    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 0 1")
    print("Điểm đánh giá:", evaluator.evaluate(board))