import chess

class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.move_history = []
        self.selected_square = None

    def get_piece(self, square):
        return self.board.piece_at(square)

    def get_legal_moves(self, square):
        return [move for move in self.board.legal_moves if move.from_square == square]

    def move(self, from_square, to_square):
        move = chess.Move(from_square, to_square)
        # Xử lý phong hậu cho tốt
        piece = self.get_piece(from_square)
        if piece and piece.piece_type == chess.PAWN:
            if chess.square_rank(to_square) in (0, 7):
                move = chess.Move(from_square, to_square, promotion=chess.QUEEN)
        if move in self.board.legal_moves:
            self.move_history.append(self.board.fen())
            self.board.push(move)
            return True
        return False

    def undo(self):
        if self.move_history:
            last_fen = self.move_history.pop()
            self.board.set_fen(last_fen)
            self.selected_square = None
    
