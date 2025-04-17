import chess
from Engine.search import Search

class Engine:
    def __init__(self):
        self.board = chess.Board()
        self.search = Search(depth=3)

    def set_position(self, fen):
        self.board.set_fen(fen)

    def get_best_move(self):
        move = self.search.get_best_move(self.board)
        if move:
            return move.uci()  # Trả về nước đi dạng UCI (e2e4, e7e8q, v.v.)
        return None