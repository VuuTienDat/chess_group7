import chess
import chess.engine

class StockfishHelper:
    def __init__(self, stockfish_path):
        print(f"Starting Stockfish at: {stockfish_path}")
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            print("Stockfish initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Stockfish: {e}")
            raise

    def set_position(self, fen):
        print(f"Setting position with FEN: {fen}")
        self.board = chess.Board(fen)

    def get_best_move(self, depth=1):
        print(f"Requesting best move with depth {depth}...")
        try:
            limit = chess.engine.Limit(depth=depth)
            result = self.engine.play(self.board, limit)
            best_move = result.move.uci()  # Lấy nước đi dạng UCI (e2e4)
            print(f"Best move received: {best_move}")
            return best_move
        except Exception as e:
            print(f"Error getting best move: {e}")
            return None

    def close(self):
        print("Closing Stockfish...")
        self.engine.quit()