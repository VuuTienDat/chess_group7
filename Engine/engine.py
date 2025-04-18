import os
import sys
from stockfish import Stockfish

class Engine:
    def __init__(self):
        # Xác định đường dẫn tới thư mục chứa file stockfish.exe
        if getattr(sys, 'frozen', False):
            # Khi chạy file .exe được build bằng PyInstaller
            bundle_dir = sys._MEIPASS
            stockfish_path = os.path.join(bundle_dir, "Engine", "stockfish", "stockfish.exe")
        else:
            # Khi chạy bằng Python bình thường
            current_dir = os.path.dirname(os.path.abspath(__file__))
            stockfish_path = os.path.join(current_dir, "stockfish", "stockfish.exe")

        # Kiểm tra và in debug nếu cần
        if not os.path.exists(stockfish_path):
            print(f"[❌] Không tìm thấy stockfish tại: {stockfish_path}")
        else:
            print(f"[✅] Đã tìm thấy stockfish tại: {stockfish_path}")

        # Khởi tạo Stockfish
        try:
            self.stockfish = Stockfish(path=stockfish_path)
            self.stockfish.set_skill_level(20)  # Mức kỹ năng cao nhất
            self.stockfish.set_depth(15)        # Độ sâu tìm kiếm hợp lý
        except Exception as e:
            print(f"[Lỗi] Khi khởi tạo Stockfish: {e}")
            raise

    def set_position(self, fen):
        """Thiết lập vị trí bàn cờ bằng chuỗi FEN."""
        try:
            self.stockfish.set_fen_position(fen)
        except Exception as e:
            print(f"[Lỗi] Khi thiết lập FEN: {e}")

    def get_best_move(self):
        """Lấy nước đi tốt nhất từ Stockfish ở định dạng UCI."""
        try:
            return self.stockfish.get_best_move()
        except Exception as e:
            print(f"[Lỗi] Khi lấy nước đi: {e}")
            return None
