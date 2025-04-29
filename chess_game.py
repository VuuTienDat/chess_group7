import chess

class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.move_history = []
        self.selected_square = None

    def get_piece(self, square):
        return self.board.piece_at(square)

    def move(self, from_square, to_square, promotion=None):
        print(f"Gọi hàm move: từ {chess.square_name(from_square)} đến {chess.square_name(to_square)}, promotion={promotion}")

        # Kiểm tra xem ô nguồn có quân hay không
        piece = self.get_piece(from_square)
        if not piece:
            print(f"Không có quân tại ô nguồn: {chess.square_name(from_square)}")
            return {"valid": False, "promotion_required": False}

        # Kiểm tra xem quân có đúng màu với lượt đi hiện tại không
        if piece.color != self.board.turn:
            print(f"Không phải lượt của quân {piece.color} (Lượt hiện tại: {'WHITE' if self.board.turn == chess.WHITE else 'BLACK'})")
            return {"valid": False, "promotion_required": False}

        # Kiểm tra xem nước đi có phải là phong quân hay không
        is_promotion = (
            piece.piece_type == chess.PAWN and
            chess.square_rank(to_square) in [0, 7]
        )
        print(f"Là nước đi phong quân: {is_promotion}")

        # Nếu là nước đi phong quân nhưng không có quân được chọn để phong, yêu cầu phong quân
        if is_promotion and promotion is None:
            print(f"Yêu cầu chọn quân để phong tại {chess.square_name(to_square)}")
            return {"valid": False, "promotion_required": True}

        # Tạo nước đi với thông tin phong quân (nếu có)
        move = chess.Move(from_square, to_square, promotion=promotion)

        # Kiểm tra tính hợp lệ của nước đi
        legal_moves = list(self.board.legal_moves)
        print(f"Trạng thái bàn cờ trước khi kiểm tra nước đi: {self.board.fen()}")
        print(f"Thử nước đi: {move.uci()}")
        if move in legal_moves:
            self.board.push(move)
            self.move_history.append(move)
            print(f"Đã thêm nước đi vào lịch sử: {move.uci()}")
            print(f"Lịch sử nước đi hiện tại: {[m.uci() for m in self.move_history]}")
            print(f"Trạng thái bàn cờ FEN: {self.board.fen()}")
            return {"valid": True, "promotion_required": False}
        else:
            print(f"Nước đi không hợp lệ: {move.uci()}")
            # Nếu là nước đi phong quân, kiểm tra tất cả các khả năng phong quân
            if is_promotion:
                promotion_pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
                for promo in promotion_pieces:
                    promo_move = chess.Move(from_square, to_square, promotion=promo)
                    if promo_move in legal_moves:
                        print(f"Nước đi hợp lệ với phong quân {promo}: {promo_move.uci()}")
            print(f"Danh sách nước đi hợp lệ: {[m.uci() for m in legal_moves]}")
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