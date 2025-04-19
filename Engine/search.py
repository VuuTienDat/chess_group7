import chess
from evaluation import Evaluation

class Search:
    def __init__(self, depth):
        self.depth = depth
        self.evaluation = Evaluation()

    def alpha_beta(self, board, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return self.evaluation.evaluate(board)

        moves = list(board.legal_moves)
        if not moves:
            if board.is_checkmate():
                return -float('inf') if maximizing_player else float('inf')
            return 0  # Hòa cờ

        if maximizing_player:
            max_eval = -float('inf')
            for move in moves:
                board.push(move)
                eval_score = self.alpha_beta(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                board.push(move)
                eval_score = self.alpha_beta(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def get_best_move(self, board):
        moves = list(board.legal_moves)
        if not moves:
            return None

        best_move = None
        best_score = -float('inf') if board.turn == chess.WHITE else float('inf')
        alpha = -float('inf')
        beta = float('inf')
        maximizing_player = board.turn == chess.WHITE

        for move in moves:
            board.push(move)
            score = self.alpha_beta(board, self.depth - 1, alpha, beta, not maximizing_player)
            board.pop()

            if maximizing_player:
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, best_score)
            else:
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, best_score)

        return best_move