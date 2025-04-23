import chess
import chess.pgn
import torch
import torch.optim as optim
import numpy as np
import os
from AlphaZeroNet import AlphaZeroNet

def load_games(filename):
    games = []
    with open(filename, "r") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            games.append(game)
    return games

def _create_move_mapping(board):
    move_mapping = {}
    idx = 0

    for from_square in range(64):
        for to_square in range(64):
            move = chess.Move(from_square, to_square)
            if move in board.legal_moves:
                move_mapping[move] = idx
            idx += 1

    for from_square in range(8, 16):
        for to_square in range(56, 64):
            for promotion in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                move = chess.Move(from_square, to_square, promotion=promotion)
                if move in board.legal_moves:
                    move_mapping[move] = idx
                idx += 1

    for from_square in range(48, 56):
        for to_square in range(0, 8):
            for promotion in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                move = chess.Move(from_square, to_square, promotion=promotion)
                if move in board.legal_moves:
                    move_mapping[move] = idx
                idx += 1

    return move_mapping

def board_to_input(board):
    board_array = np.zeros((16, 8, 8), dtype=np.float32)
    for piece in chess.PIECE_TYPES:
        for square in board.pieces(piece, chess.WHITE):
            idx = np.unravel_index(square, (8, 8))
            board_array[piece - 1][7 - idx[0]][idx[1]] = 1
        for square in board.pieces(piece, chess.BLACK):
            idx = np.unravel_index(square, (8, 8))
            board_array[piece + 5][7 - idx[0]][idx[1]] = 1

    board_array[12] = 1.0 if board.turn == chess.WHITE else 0.0
    board_array[13] = 1.0 if board.has_kingside_castling_rights(chess.WHITE) else 0.0
    board_array[14] = 1.0 if board.has_queenside_castling_rights(chess.WHITE) else 0.0
    board_array[15] = 1.0 if board.has_kingside_castling_rights(chess.BLACK) else 0.0

    return torch.tensor(board_array).unsqueeze(0)

def prepare_data(games):
    training_data = []
    for game in games:
        board = game.board()
        node = game
        result = game.headers.get("Result", "*")
        if result == "1-0":
            game_value = 1.0
        elif result == "0-1":
            game_value = -1.0
        else:
            game_value = 0.0

        while node.variations:
            move = node.variations[0].move
            if board.turn == chess.BLACK:
                move_mapping = _create_move_mapping(board)
                if move in move_mapping:
                    board_input = board_to_input(board)
                    move_idx = move_mapping[move]
                    value_target = game_value if board.turn == chess.WHITE else -game_value
                    training_data.append((board_input, move_idx, value_target))
            board.push(move)
            node = node.variations[0]
    return training_data

def finetune_model(model, training_data, epochs=10, lr=0.001):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    model.train()
    for epoch in range(epochs):
        total_value_loss = 0
        total_policy_loss = 0
        for board_input, target_move, value_target in training_data:
            board_input = board_input.to(device)
            target_move = torch.tensor([target_move], dtype=torch.long).to(device)
            # Định dạng lại value_target để có shape (1, 1) thay vì (1,)
            value_target = torch.tensor([value_target], dtype=torch.float32).unsqueeze(0).to(device)
            
            optimizer.zero_grad()
            value_loss, policy_loss = model(board_input, valueTarget=value_target, policyTarget=target_move)
            total_loss = value_loss + policy_loss
            total_loss.backward()
            optimizer.step()
            
            total_value_loss += value_loss.item()
            total_policy_loss += policy_loss.item()
        print(f"Epoch {epoch + 1}/{epochs}, Value Loss: {total_value_loss / len(training_data)}, Policy Loss: {total_policy_loss / len(training_data)}")

def main():
    model = AlphaZeroNet(num_blocks=20, num_filters=256)
    model_path = os.path.join("models", "AlphaZeroNet_20x256.pt")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Không tìm thấy file mô hình tại: {model_path}")
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    
    games = load_games(os.path.join("Data", "games.pgn"))
    training_data = prepare_data(games)
    
    print("Bắt đầu tinh chỉnh mô hình...")
    finetune_model(model, training_data, epochs=5)
    
    output_path = os.path.join("models", "AlphaZeroNet_20x256_finetuned.pt")
    torch.save(model.state_dict(), output_path)
    print(f"Đã lưu mô hình tinh chỉnh vào {output_path}")

if __name__ == "__main__":
    main()