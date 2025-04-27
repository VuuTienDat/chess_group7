import chess

class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.move_history = []
        self.selected_square = None

    def get_piece(self, square):
        return self.board.piece_at(square)

    def move(self, from_square, to_square, promotion=None):
        # Kiểm tra xem ô nguồn có quân hay không
        piece = self.get_piece(from_square)
        if not piece:
            print(f"Không có quân tại ô nguồn: {chess.square_name(from_square)}")
            return {"valid": False, "promotion_required": False}

        # Kiểm tra xem quân có đúng màu với lượt đi hiện tại không
        if piece.color != self.board.turn:
            print(f"Không phải lượt của quân {piece.color} (Lượt hiện tại: {'WHITE' if self.board.turn == chess.WHITE else 'BLACK'})")
            return {"valid": False, "promotion_required": False}

        move = chess.Move(from_square, to_square, promotion=promotion)
        if move in self.board.legal_moves:
            self.board.push(move)
            self.move_history.append(move)
            print(f"Đã thêm nước đi vào lịch sử: {move.uci()}")
            print(f"Lịch sử nước đi hiện tại: {[m.uci() for m in self.move_history]}")
            print(f"Trạng thái bàn cờ FEN: {self.board.fen()}")
            promotion_required = (self.get_piece(to_square).piece_type == chess.PAWN and
                                 chess.square_rank(to_square) in [0, 7] and
                                 promotion is None)
            return {"valid": True, "promotion_required": promotion_required}
        else:
            print(f"Nước đi không hợp lệ: {move.uci()}")
            return {"valid": False, "promotion_required": False}

    def undo(self):
        if self.board.move_stack:
            move = self.board.pop()
            if move in self.move_history:
                self.move_history.remove(move)
            print(f"Đã xóa nước đi khỏi lịch sử: {move.uci()}")
            print(f"Lịch sử nước đi sau khi undo: {[m.uci() for m in self.move_history]}")
            print(f"Trạng thái bàn cờ FEN sau undo: {self.board.fen()}")
        else:
            print("Không có nước đi để undo")