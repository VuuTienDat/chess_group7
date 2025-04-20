import chess
from Engine.search import Search # type: ignore

class Engine:
    def __init__(self, depth=4):
        """Khởi tạo engine cờ vua với độ sâu tìm kiếm."""
        try:
            self.board = chess.Board()
            self.search = Search(depth=depth)
            print("[✅] Đã khởi tạo ChessEngine với độ sâu tìm kiếm:", depth)
        except Exception as e:
            print(f"[❌] Lỗi khi khởi tạo ChessEngine: {e}")
            raise

    def set_position(self, fen):
        """Thiết lập vị trí bàn cờ bằng chuỗi FEN."""
        try:
            self.board.set_fen(fen)
            print("[✅] Đã thiết lập vị trí FEN:", fen)
        except Exception as e:
            print(f"[❌] Lỗi khi thiết lập FEN: {e}")
            raise

    def get_best_move(self):
        """Lấy nước đi tốt nhất ở định dạng UCI."""
        try:
            move = self.search.get_best_move(self.board)
            if move is None:
                print("[⚠] Không tìm thấy nước đi hợp lệ")
                return None
            uci_move = move.uci()
            print("[✅] Nước đi tốt nhất:", uci_move)
            return uci_move
        except Exception as e:
            print(f"[❌] Lỗi khi lấy nước đi: {e}")
            return None

if __name__ == "__main__":
    # Kiểm tra engine
    engine = Engine(depth=3)
    # Vị trí khai cuộc
    engine.set_position("r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 0 1")
    print("Nước đi tốt nhất:", engine.get_best_move())
    # Vị trí trung cuộc
    engine.set_position("rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1")
    print("Nước đi tốt nhất:", engine.get_best_move())
    # Vị trí tàn cuộc
    engine.set_position("8/5k2/8/8/8/8/2K5/8 w - - 0 1")
    print("Nước đi tốt nhất:", engine.get_best_move())