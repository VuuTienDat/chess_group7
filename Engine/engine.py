import os
import sys
from stockfish import Stockfish

class Engine:
    def __init__(self):
       
        # Xác định đường dẫn tới file Stockfish
        if getattr(sys, 'frozen', False):
            # Chạy dưới dạng file thực thi (ví dụ: PyInstaller)
             bundle_dir = sys._MEIPASS
             stockfish_path = os.path.join(bundle_dir, "Engine", "stockfish", "stockfish.exe")
        else:
            # Chạy dưới dạng script Python thông thường
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Đường dẫn tới file Stockfish trong thư mục Engine/stockfish
        stockfish_path = os.path.join(bundle_dir, "stockfish", "stockfish.exe")
        
        # Khởi tạo Stockfish
        try:
            self.stockfish = Stockfish(path=stockfish_path)
            # Thiết lập tham số cho engine
            self.stockfish.set_skill_level(20)  # Mức kỹ năng cao nhất
            self.stockfish.set_depth(15)  # Độ sâu tìm kiếm hợp lý
        except Exception as e:
            print(f"Lỗi khi khởi tạo Stockfish: {e}")
            raise

    def set_position(self, fen):
        """Thiết lập vị trí bàn cờ bằng chuỗi FEN."""
        try:
            self.stockfish.set_fen_position(fen)
        except Exception as e:
            print(f"Lỗi khi thiết lập FEN: {e}")

    def get_best_move(self):
        """Lấy nước đi tốt nhất từ Stockfish ở định dạng UCI."""
        try:
            return self.stockfish.get_best_move()  # Không dùng tham số time
        except Exception as e:
            print(f"Lỗi khi lấy nước đi: {e}")
            return None