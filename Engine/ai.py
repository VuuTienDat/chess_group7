import chess
import torch
import numpy as np
import os
import random
from Engine.AlphaZeroNet import AlphaZeroNet

class AlphaZeroAI:
    def __init__(self, model_path, rollouts=100):
        self.model = AlphaZeroNet(num_blocks=20, num_filters=256)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Không tìm thấy file mô hình tại: {model_path}")
        self.model.load_state_dict(torch.load(model_path, map_location="cpu"))
        self.model.eval()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.move_mapping, self.idx_to_move = self._create_move_mapping()
        self.rollouts = rollouts

    def _create_move_mapping(self):
        """
        Tạo ánh xạ nước đi cho 4608 chiều.
        - 64 x 64 = 4096 nước đi thông thường (ô nguồn x ô đích).
        - 512 nước đi thăng quân (8 ô x 4 loại thăng quân x 2 phía x 8 hướng).
        """
        move_mapping = {}
        idx_to_move = {}
        idx = 0

        # 1. Nước đi thông thường (64 x 64 = 4096)
        for from_square in range(64):
            for to_square in range(64):
                move = chess.Move(from_square, to_square)
                move_mapping[move] = idx
                idx_to_move[idx] = move
                idx += 1

        # 2. Nước đi thăng quân (promotion)
        for from_square in range(8, 16):  # Hàng 2 (trắng)
            for to_square in range(56, 64):  # Hàng 8 (đen)
                for promotion in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                    move = chess.Move(from_square, to_square, promotion=promotion)
                    move_mapping[move] = idx
                    idx_to_move[idx] = move
                    idx += 1

        for from_square in range(48, 56):  # Hàng 7 (đen)
            for to_square in range(0, 8):  # Hàng 1 (trắng)
                for promotion in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                    move = chess.Move(from_square, to_square, promotion=promotion)
                    move_mapping[move] = idx
                    idx_to_move[idx] = move
                    idx += 1

        assert idx <= 4608, f"Move mapping exceeded 4608 moves: {idx}"
        return move_mapping, idx_to_move

    def board_to_input(self, board):
        # Chuyển bàn cờ thành ma trận 8x8x16
        board_array = np.zeros((16, 8, 8), dtype=np.float32)

        # 12 kênh đầu tiên: Trạng thái bàn cờ (6 loại quân cho trắng, 6 loại quân cho đen)
        for piece in chess.PIECE_TYPES:
            for square in board.pieces(piece, chess.WHITE):
                idx = np.unravel_index(square, (8, 8))
                board_array[piece - 1][7 - idx[0]][idx[1]] = 1
            for square in board.pieces(piece, chess.BLACK):
                idx = np.unravel_index(square, (8, 8))
                board_array[piece + 5][7 - idx[0]][idx[1]] = 1

        # Kênh 13: Lượt đi (1 nếu trắng, 0 nếu đen)
        board_array[12] = 1.0 if board.turn == chess.WHITE else 0.0

        # Kênh 14: Quyền nhập thành bên vua của trắng
        board_array[13] = 1.0 if board.has_kingside_castling_rights(chess.WHITE) else 0.0

        # Kênh 15: Quyền nhập thành bên hậu của trắng
        board_array[14] = 1.0 if board.has_queenside_castling_rights(chess.WHITE) else 0.0

        # Kênh 16: Quyền nhập thành bên vua của đen
        board_array[15] = 1.0 if board.has_kingside_castling_rights(chess.BLACK) else 0.0

        return torch.tensor(board_array).unsqueeze(0).to(self.device)

    def create_policy_mask(self, board):
        # Tạo policy mask cho các nước đi hợp lệ (tensor 4608 chiều)
        policy_mask = torch.zeros(4608, dtype=torch.bool)
        legal_moves = list(board.legal_moves)

        for move in legal_moves:
            if move in self.move_mapping:
                idx = self.move_mapping[move]
                policy_mask[idx] = 1

        # Đảm bảo policy_mask có shape (1, 4608)
        return policy_mask.unsqueeze(0).to(self.device)

    def mcts(self, board, rollouts):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        visits = {move: 1 for move in legal_moves}
        values = {move: 0.0 for move in legal_moves}

        for _ in range(rollouts):
            ucb_scores = {}
            total_visits = sum(visits.values())
            for move in legal_moves:
                if move in self.move_mapping:
                    q = values[move] / visits[move]
                    u = np.sqrt(np.log(total_visits) / visits[move])
                    ucb_scores[move] = q + 0.7 * u

            if not ucb_scores:
                continue

            selected_move = max(ucb_scores, key=ucb_scores.get)
            
            board_copy = board.copy()
            board_copy.push(selected_move)
            input_tensor = self.board_to_input(board_copy)
            policy_mask = self.create_policy_mask(board_copy)

            with torch.no_grad():
                value, _ = self.model(input_tensor, policyMask=policy_mask)  # Sửa thứ tự

            # Kiểm tra shape của value và lấy giá trị
            if value.shape != torch.Size([1, 1]):
                raise ValueError(f"Expected value shape [1, 1], but got {value.shape}")
            value = value.item()

            visits[selected_move] += 1
            values[selected_move] += value

        best_move = max(visits, key=visits.get)
        return best_move

    def get_move(self, board):
        move = self.mcts(board, self.rollouts)
        if move is not None:
            return move

        input_tensor = self.board_to_input(board)
        policy_mask = self.create_policy_mask(board)
        with torch.no_grad():
            _, policy_softmax = self.model(input_tensor, policyMask=policy_mask)  # Sửa thứ tự

        legal_moves = list(board.legal_moves)
        move_probs = []

        for move in legal_moves:
            if move in self.move_mapping:
                move_idx = self.move_mapping[move]
                prob = policy_softmax[0][move_idx].item()
                move_probs.append((move, prob))

        if not move_probs:
            return random.choice(legal_moves) if legal_moves else None

        return max(move_probs, key=lambda x: x[1])[0]