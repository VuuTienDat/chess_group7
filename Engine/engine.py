import chess
from Engine.evaluation import Evaluation
from Engine.search import Search  # Giả định Search đã dùng Evaluation bên trong

class Engine:
    def __init__(self, depth=3):
        self.evaluator = Evaluation()
        self.depth = depth
        self.board = chess.Board()
        self.search = Search(self.evaluator, depth)

    def set_position(self, fen: str):
        """Thiết lập bàn cờ từ chuỗi FEN"""
        self.board = chess.Board(fen)

    def get_best_move(self) -> str:
        """Tìm nước đi tốt nhất dưới dạng UCI"""
        best_move = self.search.get_best_move(self.board)
        return best_move.uci() if best_move else None

    def evaluate_position(self) -> int:
        """Đánh giá vị trí hiện tại trên bàn cờ"""
        return self.evaluator.evaluate(self.board)

    def make_move(self, move_uci: str):
        """Thực hiện một nước đi từ chuỗi UCI"""
        move = chess.Move.from_uci(move_uci)
        if move in self.board.legal_moves:
            self.board.push(move)
        else:
            raise ValueError(f"Nước đi không hợp lệ: {move_uci}")

    def undo_move(self):
        """Hoàn tác nước đi vừa rồi"""
        if self.board.move_stack:
            self.board.pop()

    def get_fen(self) -> str:
        """Trả về chuỗi FEN hiện tại"""
        return self.board.fen()

    def is_game_over(self) -> bool:
        """Kiểm tra xem ván cờ đã kết thúc chưa"""
        return self.board.is_game_over()
