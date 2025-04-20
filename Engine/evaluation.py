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
        """Khởi tạo các tham số đánh giá"""
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
                'blocked_penalty': -15
            },
            'knight': {
                'rim_penalty': -20,
                'trapped_penalty': -40,
                'outpost_bonus': 30
            },
            'rook': {
                'open_file_bonus': 25,
                'semi_open_bonus': 15,
                'connected_bonus': 20,
                'seventh_rank_bonus': 40
            },
            'queen': {
                'early_penalty': -20,
                'mobility_weight': 0.4
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
        """Hàm đánh giá tổng hợp chính"""
        # Kiểm tra trạng thái kết thúc ván cờ
        if board.is_checkmate():
            return -self.MATE_SCORE if board.turn == chess.WHITE else self.MATE_SCORE
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        # Xác định giai đoạn ván cờ
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
        
        # 5. Thưởng nhịp điệu (tempo)
        if board.turn == chess.WHITE:
            score += self.PARAMS['tempo_bonus']
        else:
            score -= self.PARAMS['tempo_bonus']
        #6. Thưởng cấu trúc tốt
        score += self.evaluate_pawn_structure(board)

        #7. Đánh giá độ linh động quân
        score += self.evaluate_mobility(board, game_phase)
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
        """Đánh giá đặc điểm riêng từng quân"""
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
                
                elif piece_type == chess.BISHOP:
                    bishops.append(square)
                    if self.is_bad_bishop(board, square, color):
                        score += self.PARAMS['bishop']['bad_penalty']
                    if self.is_blocked_bishop(board, square):
                        score += self.PARAMS['bishop']['blocked_penalty']
                
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
        """Đánh giá nhập thành trong khai cuộc: thưởng nếu đã nhập thành, phạt nếu mất quyền nhập thành."""
        if game_phase != 'opening':
            return 0

        score = 0
        king_square = board.king(color)
        # Kiểm tra xem vua đã nhập thành chưa
        if color == chess.WHITE:
            if king_square == chess.G1 or king_square == chess.C1:
                score += 40  # Thưởng đã nhập thành
            elif not board.has_kingside_castling_rights(chess.WHITE) and not board.has_queenside_castling_rights(chess.WHITE):
                score -= 20  # Phạt nếu đã mất quyền nhập thành
        else:
            if king_square == chess.G8 or king_square == chess.C8:
                score -= 40  # Thưởng đã nhập thành (trừ vì đang tính điểm cho đen)
            elif not board.has_kingside_castling_rights(chess.BLACK) and not board.has_queenside_castling_rights(chess.BLACK):
                score += 20  # Phạt nếu đã mất quyền nhập thành (cộng vì là bên đen)

        return score    

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

    def evaluate_pawn_structure(self, board):
        """Đánh giá cấu trúc tốt của cả hai bên: isolated, doubled, backward pawns và pawn chains"""
        score = 0

        for color in [chess.WHITE, chess.BLACK]:
            pawn_squares = board.pieces(chess.PAWN, color)
            files = [chess.square_file(sq) for sq in pawn_squares]

            isolated_penalty = 10
            doubled_penalty = 15
            backward_penalty = 8
            chain_bonus = 5

            color_score = 0

            # Đếm số lượng quân tốt trên mỗi file
            file_count = [0] * 8
            for f in files:
                file_count[f] += 1

            for square in pawn_squares:
                file = chess.square_file(square)
                rank = chess.square_rank(square) if color == chess.WHITE else 7 - chess.square_rank(square)

                # Isolated pawn
                is_isolated = True
                if file > 0 and file_count[file - 1] > 0:
                    is_isolated = False
                if file < 7 and file_count[file + 1] > 0:
                    is_isolated = False
                if is_isolated:
                    color_score -= isolated_penalty

                # Doubled pawn
                if file_count[file] > 1:
                    color_score -= doubled_penalty

                # Backward pawn (đơn giản hóa)
                is_backward = True
                for adj_file in [file - 1, file + 1]:
                    if 0 <= adj_file < 8:
                        for r in range(rank):
                            adj_sq = chess.square(adj_file, r if color == chess.WHITE else 7 - r)
                            if adj_sq in pawn_squares:
                                is_backward = False
                                break
                if is_backward:
                    color_score -= backward_penalty

                # Pawn chain (kiểm tra quân tốt ở phía sau chéo)
                for dx in [-1, 1]:
                    behind_file = file + dx
                    behind_rank = rank - 1
                    if 0 <= behind_file < 8 and behind_rank >= 0:
                        behind_sq = chess.square(behind_file, behind_rank if color == chess.WHITE else 7 - behind_rank)
                        if behind_sq in pawn_squares:
                            color_score += chain_bonus
                            break  # chỉ cộng bonus một lần là đủ

            score += color_score if color == chess.WHITE else -color_score

        return score


    def evaluate_mobility(self, board, game_phase):
        """Đánh giá độ cơ động cho cả hai bên, chủ yếu trong midgame"""
        if game_phase == 'endgame':
            return 0

        mobility_score = 0
        piece_weights = {
            chess.KNIGHT: 2,
            chess.BISHOP: 2,
            chess.ROOK: 1,
            chess.QUEEN: 1,
        }

        for color in [chess.WHITE, chess.BLACK]:
            color_score = 0

            for piece_type, weight in piece_weights.items():
                for square in board.pieces(piece_type, color):
                    legal_moves = list(board.generate_legal_moves(from_mask=chess.BB_SQUARES[square]))
                    move_count = sum(
                        1 for move in legal_moves
                        if board.piece_at(move.to_square) is None or board.piece_at(move.to_square).color != color
                    )
                    color_score += weight * move_count

            if color == chess.WHITE:
                mobility_score += color_score
            else:
                mobility_score -= color_score

        return mobility_score


if __name__ == "__main__":
    evaluator = Evaluation()
    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 0 1")
    print("Điểm đánh giá:", evaluator.evaluate(board))