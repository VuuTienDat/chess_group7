# --- search.py ---
import chess
import numpy as np
import time

class Node:
    def __init__(self, board, parent=None, move=None):
        self.board = board
        self.parent = parent
        self.move = move
        self.children = {}
        self.visits = 0
        self.value = 0.0
        self.prior = 0.0

class Search:
    def __init__(self, learner, max_simulations=200, c_puct=1.0, time_limit=3):
        self.learner = learner
        self.max_simulations = max_simulations
        self.c_puct = c_puct
        self.time_limit = time_limit
        self.start_time = None
        self.root = None

    def get_best_move(self, board: chess.Board) -> chess.Move:
        self.start_time = time.time()
        self.root = Node(board.copy())

        for _ in range(self.max_simulations):
            if self.is_timeout():
                break
            node = self.select(self.root)
            value = self.simulate(node)
            self.backpropagate(node, value)

        best_move = None
        max_visits = -1
        for move, child in self.root.children.items():
            if child.visits > max_visits:
                max_visits = child.visits
                best_move = move

        return best_move if best_move else list(board.legal_moves)[0]

    def select(self, node: Node) -> Node:
        while node.children and not node.board.is_game_over():
            move, node = max(
                node.children.items(),
                key=lambda x: x[1].value / (x[1].visits + 1e-8) + self.c_puct * x[1].prior * np.sqrt(node.visits + 1) / (x[1].visits + 1)
            )
        return node

    def simulate(self, node: Node) -> float:
        if node.board.is_game_over():
            if node.board.is_checkmate():
                return -1.0 if node.board.turn else 1.0
            return 0.0

        legal_moves = list(node.board.legal_moves)
        policy, value = self.learner.predict(node.board)

        policy_dict = {move: policy[i] for i, move in enumerate(legal_moves)}

        dirichlet_alpha = 0.3
        epsilon = 0.25
        noise = np.random.dirichlet([dirichlet_alpha] * len(legal_moves))
        for i, move in enumerate(legal_moves):
            policy_dict[move] = (1 - epsilon) * policy_dict[move] + epsilon * noise[i]

        for move in legal_moves:
            node.board.push(move)
            child = Node(node.board.copy(), parent=node, move=move)
            child.prior = policy_dict.get(move, 0.01)
            node.children[move] = child
            node.board.pop()

        return value

    def backpropagate(self, node: Node, value: float):
        while node:
            node.visits += 1
            node.value += value if node.board.turn == chess.WHITE else -value
            node = node.parent

    def is_timeout(self) -> bool:
        return time.time() - self.start_time > self.time_limit
