import chess

class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.selected_square = None

    def get_piece(self, square):
        return self.board.piece_at(square)

    def get_legal_moves(self, square):
        return [move for move in self.board.legal_moves if move.from_square == square]
    
    def move(self, from_square, to_square, promotion=None):
        piece = self.get_piece(from_square)
        is_promotion = (
            piece and
            piece.piece_type == chess.PAWN and
            (
                (piece.color == chess.WHITE and chess.square_rank(to_square) == 7) or
                (piece.color == chess.BLACK and chess.square_rank(to_square) == 0)
            )
        )

        if is_promotion and promotion is None:
            # Kiểm tra xem nước đi phong cấp có hợp lệ với bất kỳ quân nào không
            for prom in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                move = chess.Move(from_square, to_square, promotion=prom)
                if move in self.board.legal_moves:          
                    return {"valid": True, "promotion_required": True, "move": move}
            # Nếu không có nước đi phong cấp nào hợp lệ, trả về thông báo lỗi
            return {"valid": False, "promotion_required": False, "move": None}
        else:
            # Nước đi thường hoặc phong cấp với promotion đã chỉ định
            move = chess.Move(from_square, to_square, promotion=promotion)
            if move in self.board.legal_moves:
                self.board.push(move)    
                return {"valid": True, "promotion_required": False, "move": move}
            
            return {"valid": False, "promotion_required": False, "move": None}

    def undo(self):
        if self.board.move_stack:
            self.board.pop()