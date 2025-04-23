import chess
import chess.pgn
import os
from ai import AlphaZeroAI
from engine import Engine

def play_game(alpha_zero_ai, stockfish_engine, game_number):
    board = chess.Board()
    game = chess.pgn.Game()
    game.headers["Event"] = f"AlphaZero vs Stockfish Game {game_number}"
    game.headers["White"] = "AlphaZero"
    game.headers["Black"] = "Stockfish"
    node = game

    while not board.is_game_over():
        if board.turn == chess.WHITE:
            # Lượt của AlphaZero (trắng)
            move = alpha_zero_ai.get_move(board)
            print(f"AlphaZero move: {move}")
            if move is None:
                break
            board.push(move)
        else:
            # Lượt của Stockfish (đen)
            stockfish_engine.set_position(board.fen())
            uci_move = stockfish_engine.get_best_move()
            if uci_move:
                move = chess.Move.from_uci(uci_move)
                board.push(move)
            else:
                break
        node = node.add_variation(move)

    game.headers["Result"] = board.result()
    return game

def save_games(games, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "a") as f:
        for game in games:
            # Tạo StringExporter mà không truyền file object
            exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
            # Chuyển game thành chuỗi PGN
            pgn_string = game.accept(exporter)
            # Ghi chuỗi PGN vào file
            f.write(pgn_string)
            f.write("\n\n")

def main():
    # Khởi tạo AlphaZeroAI và Stockfish
    alpha_zero_ai = AlphaZeroAI(os.path.join("models", "AlphaZeroNet_20x256.pt"))
    stockfish_engine = Engine(use_stockfish=True)

    # Số ván cờ để tạo dữ liệu
    num_games = 10
    games = []

    print(f"Đang tạo {num_games} ván cờ giữa AlphaZero và Stockfish...")
    for i in range(num_games):
        game = play_game(alpha_zero_ai, stockfish_engine, i + 1)
        games.append(game)
        if (i + 1) % 10 == 0:
            print(f"Đã hoàn thành {i + 1} ván cờ.")

    # Lưu các ván cờ vào file
    save_games(games, os.path.join("Data", "games.pgn"))
    print("Đã lưu dữ liệu vào Data/games.pgn")

if __name__ == "__main__":
    main()