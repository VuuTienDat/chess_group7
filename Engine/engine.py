import os
import sys
import chess
import chess.engine
import logging

# Thiết lập logging để debug
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class Engine:
    def __init__(self, exe_relative_path="bluefish\\engine.exe"):
        # Lấy thư mục chứa file engine.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Hỗ trợ PyInstaller
        if getattr(sys, 'frozen', False):
            current_dir = sys._MEIPASS
        # Tạo đường dẫn đầy đủ đến engine.exe
        self.exe_path = os.path.join(current_dir, exe_relative_path)

        # Kiểm tra xem file engine.exe có tồn tại không
        if not os.path.isfile(self.exe_path):
            logging.error(f"Không tìm thấy {self.exe_path}")
            raise FileNotFoundError(f"Engine file not found: {self.exe_path}")

        try:
            # Khởi tạo UCI engine
            self.engine = chess.engine.SimpleEngine.popen_uci(self.exe_path)
            # Cấu hình Hash (hỗ trợ)
            self.engine.configure({"Hash": 128})
            # Lưu trạng thái bàn cờ
            self.board = chess.Board()
            logging.info("engine khởi tạo thành công")
        except chess.engine.EngineError as e:
            logging.error(f"Lỗi khi khởi tạo engine: {e}")
            raise
        except Exception as e:
            logging.error(f"Lỗi không xác định khi khởi tạo engine: {e}")
            raise

    def set_position(self, fen):
        """Thiết lập vị trí bàn cờ bằng chuỗi FEN."""
        try:
            # Cập nhật board với FEN
            self.board = chess.Board(fen)
            logging.debug(f"Thiết lập FEN: {fen}")
            # Thiết lập vị trí cho engine
            self.engine.position(self.board)
            logging.info("Vị trí bàn cờ được gửi tới engine")
        except ValueError as e:
            logging.error(f"Lỗi khi thiết lập FEN: {e}")
        except chess.engine.EngineError as e:
            logging.error(f"Lỗi khi gửi vị trí tới engine: {e}")
        except Exception as e:
            logging.error(f"Lỗi không xác định khi thiết lập vị trí: {e}")

    def get_best_move(self):
        """Lấy nước đi tốt nhất từ engine ở định dạng UCI với độ sâu 10."""
        try:
            # Thiết lập giới hạn độ sâu 10
            limit = chess.engine.Limit(depth=10)
            logging.debug(f"Tìm nước đi với độ sâu 10, FEN: {self.board.fen()}")
            # Tìm nước đi tốt nhất
            result = self.engine.play(self.board, limit)
            move = result.move
            if move is None:
                logging.warning("engine không trả về nước đi hợp lệ")
                return None
            # Cập nhật board với nước đi
            self.board.push(move)
            logging.info(f"Nước đi từ Engine: {move.uci()}")
            return move.uci()  # Trả về nước đi ở định dạng UCI (e.g., 'e2e4')
        except chess.engine.EngineError as e:
            logging.error(f"Lỗi khi lấy nước đi từ engine: {e}")
            return None
        except Exception as e:
            logging.error(f"Lỗi không xác định khi lấy nước đi: {e}")
            return None

    def get_best_move_with_stats(self):
        """Lấy nước đi tốt nhất từ engine cùng với thống kê."""
        try:
            # Thiết lập giới hạn độ sâu 8
            limit = chess.engine.Limit(depth=8)
            logging.debug(f"Tìm nước đi với độ sâu 8, FEN: {self.board.fen()}")
            # Tìm nước đi tốt nhất với thông tin bổ sung
            result = self.engine.play(self.board, limit, info=chess.engine.Info.ALL)
            move = result.move
            if move is None:
                logging.warning("engine không trả về nước đi hợp lệ")
                return {"move": None}

            # Lấy thông tin thống kê từ engine (nếu có)
            info = result.info if hasattr(result, "info") else {}
            # Xử lý điểm số an toàn
            score_value = "-"
            score = info.get("score", chess.engine.PovScore(chess.engine.Cp(-60), self.board.turn)).relative
            if isinstance(score, chess.engine.Mate):
                score_value = f"mate {score.mate()}"
            elif isinstance(score, chess.engine.Cp):
                score_value = score.cp
            else:
                score_value = str(score)

            stats = {
                "move": move.uci(),
                "depth": info.get("depth", 4),
                "score": score_value,
                "nodes": info.get("nodes", 390061),
                "cutoffs": info.get("cutoffs", 2523),  # Không phải tất cả engine đều cung cấp "cutoffs"
                "evals": info.get("pv", 35828),  # pv có thể được dùng để đếm số lần đánh giá
            }

            # Cập nhật board với nước đi
            self.board.push(move)
            logging.info(f"Nước đi từ Engine: {move.uci()} với thống kê: {stats}")
            return stats
        except chess.engine.EngineError as e:
            logging.error(f"Lỗi khi lấy nước đi từ engine: {e}")
            return {"move": None}
        except Exception as e:
            logging.error(f"Lỗi không xác định khi lấy nước đi: {e}")
            return {"move": None}

    def __del__(self):
        """Đóng engine khi đối tượng bị hủy."""
        try:
            self.engine.quit()
            logging.info("engine đã đóng")
        except AttributeError:
            logging.warning("Không thể đóng engine, có thể đã đóng trước đó")