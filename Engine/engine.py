import chess
import chess.engine
import os
import sys
import platform

class Engine:
    def __init__(self, depth=4):
        self.depth = depth
        self.engine = None
        self.board = None  # Sẽ được gán từ FEN
        
        # Determine the correct engine path based on the platform
        if getattr(sys, 'frozen', False):
            bundle_dir = sys._MEIPASS
        else:
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Default engine paths based on OS
        if platform.system() == "Windows":
            self.engine_path = os.path.join(bundle_dir, "Kingfish", "build", "kingfish_1.2.0.exe")
        elif platform.system() == "Darwin":  # macOS
            self.engine_path = os.path.join(bundle_dir, "Kingfish", "build", "kingfish_1.2.0")
        else:  # Linux and others
            self.engine_path = os.path.join(bundle_dir, "Kingfish", "build", "kingfish_1.2.0")
        
        # Try to use stockfish if available in system PATH as a fallback
        self.try_connect_engine()

    def try_connect_engine(self):
        try:
            # First try with the specified path
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            print(f"[✓] Successfully connected to engine at {self.engine_path}")
        except FileNotFoundError:
            try:
                # Fallback to stockfish in PATH if available
                print(f"[!] Engine not found at {self.engine_path}")
                print("[!] Trying to use 'stockfish' from system PATH...")
                self.engine = chess.engine.SimpleEngine.popen_uci("stockfish")
                print("[✓] Successfully connected to Stockfish")
            except FileNotFoundError:
                print("[❌] Error: No chess engine found. Please install Stockfish or provide a valid engine path.")
                # Instead of raising an error, we'll provide a simple engine
                print("[!] Using simple built-in evaluation instead")
                self.engine = None
        except Exception as e:
            print(f"[❌] Error initializing engine: {str(e)}")
            self.engine = None

    def __del__(self):
        if self.engine is not None:
            try:
                self.engine.quit()
            except Exception as e:
                print(f"[❌] Error closing engine: {str(e)}")

    def set_position(self, fen):
        try:
            self.board = chess.Board(fen)
        except Exception as e:
            print(f"[❌] Error setting position from FEN: {fen}")
            raise e

    def simple_evaluation(self):
        """A very simple evaluation when no engine is available"""
        if self.board.is_checkmate():
            return None  # No moves available
        
        # Piece values
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
        
        # Find all legal moves
        legal_moves = list(self.board.legal_moves)
        if not legal_moves:
            return None
        
        # Simple evaluation based on piece capture and position
        best_move = legal_moves[0]
        best_score = -float('inf')
        
        for move in legal_moves:
            score = 0
            
            # Captures are good
            if self.board.is_capture(move):
                target_piece = self.board.piece_at(move.to_square)
                if target_piece:
                    score += piece_values.get(target_piece.piece_type, 0)
            
            # Center control is good
            center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
            if move.to_square in center_squares:
                score += 10
            
            # Check is good
            self.board.push(move)
            if self.board.is_check():
                score += 50
            # Checkmate is best
            if self.board.is_checkmate():
                score = float('inf')
            self.board.pop()
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move.uci()

    def get_best_move(self):
        if not self.board:
            raise ValueError("Board position not set. Call set_position(fen) first.")
            
        if self.engine is None:
            return self.simple_evaluation()
            
        try:
            result = self.engine.play(self.board, chess.engine.Limit(depth=self.depth))
            return result.move.uci()  # Return UCI string format
        except Exception as e:
            print(f"[❌] Engine error: {str(e)}")
            print("[!] Falling back to simple evaluation")
            return self.simple_evaluation()

# Test code
if __name__ == "__main__":
    try:
        engine = Engine()
        engine.set_position(chess.STARTING_FEN)
        print("Best move:", engine.get_best_move())
    except Exception as e:
        print(f"[❌] Error: {str(e)}")