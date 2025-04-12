import chess

class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.selected_square = None
        self.move_history = []

    def get_piece(self, square):
        return self.board.piece_at(square)

    def get_legal_moves(self, square):
        return [move for move in self.board.legal_moves if move.from_square == square]
    def undo(self):
        if self.move_history:
            last_fen = self.move_history.pop()
            self.board.set_fen(last_fen)

    def move(self, from_square, to_square):
        move = chess.Move(from_square, to_square)

        # Nếu là tốt đi đến hàng cuối và là nước promotion
        if self.board.piece_at(from_square).piece_type == chess.PAWN:
            if chess.square_rank(to_square) == 0 or chess.square_rank(to_square) == 7:
                move = chess.Move(from_square, to_square, promotion=chess.QUEEN)

        if move in self.board.legal_moves:
            self.move_history.append(self.board.fen())
            self.board.push(move)
            return True
        return False


    
