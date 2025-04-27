# --- engine.py ---
import chess
import os
from Engine.search import Search
from Engine.learner import Learner

class Engine:
    def __init__(self, max_simulations=200, time_limit=3, model_dir="Engine"):
        self.board = chess.Board()
        self.learner = Learner()
        self.search = Search(self.learner, max_simulations, time_limit)
        self.move_history = []
        self.fen_history = {}
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, "chess_model.pth")
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.learner.load_model(self.model_path)
                print(f"Loaded model from {self.model_path}")
            except Exception as e:
                print(f"Failed to load model ({e}), starting with fresh model.")
        else:
            print(f"No model found at {self.model_path}, starting with fresh model.")


    def set_position(self, fen: str):
        self.board = chess.Board(fen)
        self.move_history.clear()
        self.fen_history = {fen: 1}

    def get_best_move(self) -> str:
        if self.board.is_game_over():
            return None
        move = self.search.get_best_move(self.board)
        return move.uci() if move else None

    def make_move(self, move_uci: str):
        move = chess.Move.from_uci(move_uci)
        if move in self.board.legal_moves:
            self.board.push(move)
            self.move_history.append(move)
            fen = self.board.fen()
            self.fen_history[fen] = self.fen_history.get(fen, 0) + 1
            if self.fen_history[fen] >= 3:
                raise ValueError("Threefold repetition")
        else:
            raise ValueError(f"Illegal move: {move_uci}")

    def self_play(self, num_games=500, max_moves_per_game=100):
        training_data = []
        for _ in range(num_games):
            self.board.reset()
            self.fen_history = {self.board.fen(): 1}
            game_states = []
            move_count = 0

            while not self.board.is_game_over() and move_count < max_moves_per_game:
                move = self.get_best_move()
                if not move:
                    break
                game_states.append((self.board.fen(), move))
                try:
                    self.make_move(move)
                except ValueError:
                    break
                move_count += 1

            result = 0.0
            if self.board.is_checkmate():
                result = 1.0 if self.board.turn == chess.BLACK else -1.0

            for fen, move in game_states:
                training_data.append((fen, move, result))

        self.learner.train(training_data)
        os.makedirs(self.model_dir, exist_ok=True)
        self.learner.save_model(self.model_path)
        print(f"Self-play completed, model saved to {self.model_path}")
        return training_data
