import chess
import chess.engine
from Engine.ai import AlphaZeroAI
import os

class Engine:
    def __init__(self, use_stockfish=False):
        self.use_stockfish = use_stockfish
        if self.use_stockfish:
            # Khởi tạo Stockfish
            self.stockfish = chess.engine.SimpleEngine.popen_uci("stockfish/stockfish.exe")
        else:
            # Khởi tạo AlphaZeroAI với AlphaZeroNet_20x256.pt
            self.alpha_zero_ai = AlphaZeroAI(
                os.path.join("Engine","models", "AlphaZeroNet_20x256_finetuned.pt"),
                rollouts=500  # Số lần mô phỏng MCTS
            )
        self.board = None

    def set_position(self, fen):
        self.board = chess.Board(fen)

    def get_best_move(self):
        if self.use_stockfish:
            # Dùng Stockfish
            result = self.stockfish.play(self.board, chess.engine.Limit(time=0.1))
            return result.move.uci() if result.move else None
        else:
            # Dùng AlphaZeroAI
            move = self.alpha_zero_ai.get_move(self.board)
            return move.uci() if move else None

    def quit(self):
        if self.use_stockfish:
            self.stockfish.quit()