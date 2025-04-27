# --- learner.py ---
import torch
import torch.nn as nn
import torch.nn.functional as F
import chess
import numpy as np

class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)

    def forward(self, x):
        residual = x
        x = F.relu(self.conv1(x))
        x = self.conv2(x)
        return F.relu(x + residual)

class ChessNet(nn.Module):
    def __init__(self, num_blocks=5):
        super().__init__()
        self.conv_in = nn.Conv2d(12, 64, kernel_size=3, padding=1)
        self.res_blocks = nn.Sequential(*[ResidualBlock(64) for _ in range(num_blocks)])

        self.policy_conv = nn.Conv2d(64, 2, kernel_size=1)
        self.policy_fc = nn.Linear(2 * 8 * 8, 4096)

        self.value_conv = nn.Conv2d(64, 1, kernel_size=1)
        self.value_fc1 = nn.Linear(8 * 8, 64)
        self.value_fc2 = nn.Linear(64, 1)

    def forward(self, x):
        x = F.relu(self.conv_in(x))
        x = self.res_blocks(x)

        p = F.relu(self.policy_conv(x)).view(-1, 2 * 8 * 8)
        p = self.policy_fc(p)
        policy = torch.softmax(p, dim=-1)

        v = F.relu(self.value_conv(x)).view(-1, 8 * 8)
        v = F.relu(self.value_fc1(v))
        value = torch.tanh(self.value_fc2(v))

        return policy, value

class Learner:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = ChessNet().to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.002)

    def board_to_tensor(self, board: chess.Board) -> torch.Tensor:
        tensor = np.zeros((12, 8, 8), dtype=np.float32)
        for square, piece in board.piece_map().items():
            rank, file = chess.square_rank(square), chess.square_file(square)
            idx = piece.piece_type - 1 + (6 if piece.color == chess.BLACK else 0)
            tensor[idx, rank, file] = 1.0
        return torch.tensor(tensor, dtype=torch.float32).to(self.device)

    def predict(self, board: chess.Board):
        self.model.eval()
        with torch.no_grad():
            state = self.board_to_tensor(board).unsqueeze(0)
            policy, value = self.model(state)
            return policy.cpu().numpy()[0], value.item()

    def train(self, training_data):
        self.model.train()
        batch_size = 64
        for epoch in range(5):
            np.random.shuffle(training_data)
            for i in range(0, len(training_data), batch_size):
                batch = training_data[i:i+batch_size]
                states, moves, results = [], [], []
                for fen, move_uci, result in batch:
                    board = chess.Board(fen)
                    states.append(self.board_to_tensor(board))
                    moves.append(self.move_to_index(board, move_uci))
                    results.append(result)
                states = torch.stack(states).to(self.device)
                moves = torch.tensor(moves, dtype=torch.long).to(self.device)
                results = torch.tensor(results, dtype=torch.float32).to(self.device)

                policy_out, value_out = self.model(states)
                policy_loss = nn.CrossEntropyLoss()(policy_out, moves)
                value_loss = nn.MSELoss()(value_out.squeeze(), results)

                loss = policy_loss + value_loss
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

    def move_to_index(self, board: chess.Board, move_uci: str) -> int:
        legal_moves = list(board.legal_moves)
        move = chess.Move.from_uci(move_uci)
        return legal_moves.index(move) if move in legal_moves else 0

    def save_model(self, path: str):
        torch.save(self.model.state_dict(), path)

    def load_model(self, path: str):
        self.model.load_state_dict(torch.load(path, map_location=self.device))
        self.model.eval()
