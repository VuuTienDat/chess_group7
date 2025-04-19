"""
Chess Engine module that implements the AI logic for playing chess.
This module uses the evaluation function to make decisions about moves.
"""

import chess
import time
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import our modules
from Engine.evaluation.main_evaluator import MainEvaluator
from Engine.evaluation.weights import PIECE_VALUES

class Engine:
    def __init__(self, max_depth=4, max_time=10.0):
        """
        Initialize the chess engine.
        
        Args:
            max_depth (int): Maximum depth for move search
            max_time (float): Maximum time in seconds to spend on a move (default: 10.0)
        """
        self.max_depth = max_depth
        self.max_time = max_time
        self.nodes_searched = 0
        self.start_time = 0
        self.best_move = None  # Track current best move
        self.transposition_table = {}  # Cache for evaluated positions
        self.killer_moves = [[None, None] for _ in range(100)]  # Store killer moves for each ply
        self.history_heuristic = {}  # Store move history for move ordering
        self.time_control = {
            'hard_limit': max_time,  # Maximum time allowed (10 seconds)
            'soft_limit': max_time * 0.8,  # Target time to complete search (8 seconds)
            'time_used': 0,  # Time used in current search
            'nodes_per_second': 0,  # Search speed estimate
            'last_depth_completed': 0,  # Last depth that completed
            'best_move': None,  # Best move found so far
            'best_score': float('-inf'),  # Best score found so far
            'warnings': {
                'time_warning': max_time * 0.9,  # Warning at 9 seconds
                'depth_skip_threshold': max_time * 0.7,  # Skip depth after 7 seconds
            }
        }
        
        # Initialize evaluator and board
        self.evaluator = MainEvaluator()
        self.board = chess.Board()  # Initialize with starting position

    def set_position(self, fen):
        """Set board position using FEN string."""
        try:
            self.board = chess.Board(fen)
            return True
        except ValueError as e:
            print(f"[ERROR] Invalid FEN string: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to set position: {e}")
            return False

    def get_best_move(self):
        """Get best move using our custom evaluation system."""
        if not self.board:
            print("[ERROR] Board not initialized")
            return None
            
        try:
            # Check if game is over
            if self.board.is_game_over():
                print("[INFO] Game is over")
                return None
                
            # Get legal moves
            legal_moves = list(self.board.legal_moves)
            if not legal_moves:
                print("[INFO] No legal moves available")
                return None
                
            # If only one move is possible, play it immediately
            if len(legal_moves) == 1:
                print("[INFO] Only one legal move available")
                return legal_moves[0]
                
            # Find best move using our evaluation system
            best_move = self.make_move(self.board)
            
            # Ensure we have a valid move
            if best_move and isinstance(best_move, chess.Move):
                print(f"[INFO] Found best move: {best_move.uci()}")
                return best_move
            elif self.time_control['best_move'] and isinstance(self.time_control['best_move'], chess.Move):
                print(f"[INFO] Using time control best move: {self.time_control['best_move'].uci()}")
                return self.time_control['best_move']
            else:
                print("[WARNING] No best move found, selecting first legal move")
                return legal_moves[0]
                
        except Exception as e:
            print(f"[ERROR] Failed to get best move: {e}")
            # If something goes wrong but we have a valid move from time control, use it
            if self.time_control['best_move'] and isinstance(self.time_control['best_move'], chess.Move):
                return self.time_control['best_move']
            # Otherwise try to return the first legal move
            legal_moves = list(self.board.legal_moves)
            return legal_moves[0] if legal_moves else None

    def order_moves(self, board, moves, ply):
        """
        Order moves to improve alpha-beta pruning efficiency.
        
        Args:
            board (chess.Board): Current chess position
            moves (list): List of legal moves
            ply (int): Current search depth
            
        Returns:
            list: Ordered moves
        """
        move_scores = []
        for move in moves:
            score = 0
            
            # 1. Check if move is a capture
            if board.is_capture(move):
                # MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
                victim = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                if victim and attacker:
                    score += 10 * PIECE_VALUES[victim.symbol()] - PIECE_VALUES[attacker.symbol()]
            
            # 2. Check if move is a killer move
            if move in self.killer_moves[ply]:
                score += 9000  # Killer move bonus
            
            # 3. Check history heuristic
            move_key = (move.from_square, move.to_square)
            if move_key in self.history_heuristic:
                score += self.history_heuristic[move_key]
            
            # 4. Check if move is a promotion
            if move.promotion:
                score += 10000  # Promotion bonus
            
            move_scores.append((move, score))
        
        # Sort moves by score in descending order
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in move_scores]

    def quiescence_search(self, board, alpha, beta, color):
        """
        Perform quiescence search to handle tactical positions.
        
        Args:
            board (chess.Board): Current chess position
            alpha (float): Alpha value for pruning
            beta (float): Beta value for pruning
            color (chess.Color): Color to move
            
        Returns:
            float: Evaluation score
        """
        # Stand pat evaluation
        stand_pat = self.evaluator.evaluate(board)
        if color == chess.WHITE:
            if stand_pat >= beta:
                return beta
            if alpha < stand_pat:
                alpha = stand_pat
        else:
            if stand_pat <= alpha:
                return alpha
            if beta > stand_pat:
                beta = stand_pat
        
        # Only consider captures
        captures = [move for move in board.legal_moves if board.is_capture(move)]
        captures = self.order_moves(board, captures, 0)  # Use ply 0 for quiescence
        
        for move in captures:
            board.push(move)
            score = self.quiescence_search(board, alpha, beta, not color)
            board.pop()
            
            if color == chess.WHITE:
                if score >= beta:
                    return beta
                if score > alpha:
                    alpha = score
            else:
                if score <= alpha:
                    return alpha
                if score < beta:
                    beta = score
        
        return alpha if color == chess.WHITE else beta

    def minimax(self, board, depth, alpha, beta, maximizing_player, ply=0):
        """
        Optimized minimax algorithm with alpha-beta pruning.
        
        Args:
            board (chess.Board): Current chess position
            depth (int): Current search depth
            alpha (float): Alpha value for pruning
            beta (float): Beta value for pruning
            maximizing_player (bool): True if maximizing player's turn
            ply (int): Current ply in the search tree
            
        Returns:
            float: Evaluation score
        """
        self.nodes_searched += 1
        
        # Check for terminal conditions
        if depth == 0:
            return self.quiescence_search(board, alpha, beta, board.turn)
        
        if board.is_game_over():
            result = board.outcome()
            if result.winner is None:
                return 0  # Draw
            return float('inf') if result.winner == maximizing_player else float('-inf')
        
        # Check transposition table
        board_key = board.fen()
        if board_key in self.transposition_table:
            entry = self.transposition_table[board_key]
            if entry['depth'] >= depth:
                return entry['score']
        
        # Get and order legal moves
        legal_moves = list(board.legal_moves)
        legal_moves = self.order_moves(board, legal_moves, ply)
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, False, ply + 1)
                board.pop()
                
                if eval > max_eval:
                    max_eval = eval
                    if ply == 0:  # Root node
                        self.best_move = move
                
                alpha = max(alpha, eval)
                if beta <= alpha:
                    # Update killer moves
                    if move not in self.killer_moves[ply]:
                        self.killer_moves[ply][1] = self.killer_moves[ply][0]
                        self.killer_moves[ply][0] = move
                    # Update history heuristic
                    move_key = (move.from_square, move.to_square)
                    self.history_heuristic[move_key] = self.history_heuristic.get(move_key, 0) + depth * depth
                    break
            
            # Store in transposition table
            self.transposition_table[board_key] = {
                'depth': depth,
                'score': max_eval
            }
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, True, ply + 1)
                board.pop()
                
                if eval < min_eval:
                    min_eval = eval
                    if ply == 0:  # Root node
                        self.best_move = move
                
                beta = min(beta, eval)
                if beta <= alpha:
                    # Update killer moves
                    if move not in self.killer_moves[ply]:
                        self.killer_moves[ply][1] = self.killer_moves[ply][0]
                        self.killer_moves[ply][0] = move
                    # Update history heuristic
                    move_key = (move.from_square, move.to_square)
                    self.history_heuristic[move_key] = self.history_heuristic.get(move_key, 0) + depth * depth
                    break
            
            # Store in transposition table
            self.transposition_table[board_key] = {
                'depth': depth,
                'score': min_eval
            }
            return min_eval

    def should_stop_search(self):
        """
        Check if the search should be stopped based on time and progress.
        
        Returns:
            bool: True if search should be stopped
        """
        current_time = time.time() - self.start_time
        
        # Update time control stats
        self.time_control['time_used'] = current_time
        if self.nodes_searched > 0:
            self.time_control['nodes_per_second'] = self.nodes_searched / current_time
        
        # Check hard time limit (10 seconds)
        if current_time >= self.time_control['hard_limit']:
            print(f"[INFO] Reached hard time limit of {self.time_control['hard_limit']} seconds")
            return True
            
        # Check if we're running out of time
        if current_time > self.time_control['soft_limit']:
            # If we haven't completed any depth, continue
            if self.time_control['last_depth_completed'] == 0:
                return False
                
            # Estimate time for next depth
            estimated_time = current_time * 2  # Rough estimate that each depth takes 2x longer
            if estimated_time > self.time_control['hard_limit']:
                print(f"[INFO] Estimated time for next depth ({estimated_time:.2f}s) exceeds limit")
                return True
                
        # Warning when approaching time limit
        if current_time > self.time_control['warnings']['time_warning']:
            print(f"[WARNING] Approaching time limit: {current_time:.2f}s used")
                
        return False

    def make_move(self, board):
        """
        Make the best move for the current position using iterative deepening.
        
        Args:
            board (chess.Board): Current chess position
            
        Returns:
            chess.Move: The best move found
        """
        try:
            self.nodes_searched = 0
            self.start_time = time.time()
            self.transposition_table.clear()
            self.time_control.update({
                'time_used': 0,
                'nodes_per_second': 0,
                'last_depth_completed': 0,
                'best_move': None,
                'best_score': float('-inf')
            })
            
            # Get all legal moves
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                return None
                
            # If only one move is possible, play it immediately
            if len(legal_moves) == 1:
                return legal_moves[0]
            
            # Initialize iterative deepening
            current_depth = 1
            best_move = None
            
            print(f"[INFO] Starting search with time limit: {self.max_time} seconds")
            
            while current_depth <= self.max_depth:
                # Clear killer moves and history heuristic for new depth
                self.killer_moves = [[None, None] for _ in range(100)]
                self.history_heuristic.clear()
                
                print(f"[INFO] Searching at depth {current_depth}")
                
                # Perform search at current depth
                score = self.minimax(board, current_depth, float('-inf'), float('inf'), 
                                   board.turn == chess.WHITE)
                
                # Update best move if we found a better one
                # Update best move based on player perspective
                if (board.turn == chess.WHITE and score > self.time_control['best_score']) or \
                   (board.turn == chess.BLACK and score < self.time_control['best_score']):
                    self.time_control['best_score'] = score
                    self.time_control['best_move'] = self.best_move
                    best_move = self.best_move
                    print(f"[INFO] Found better move with score: {score}")
                
                # Check if we should stop searching
                if self.should_stop_search():
                    print(f"[INFO] Stopping search at depth {current_depth}")
                    break
                    
                # Check for mate
                if abs(score) == float('inf'):
                    print("[INFO] Found forced mate!")
                    break
                    
                # Update last completed depth
                self.time_control['last_depth_completed'] = current_depth
                
                # Increment depth
                current_depth += 1
                
                # If we're running low on time, skip to next depth
                current_time = time.time() - self.start_time
                if current_time > self.time_control['warnings']['depth_skip_threshold']:
                    print(f"[INFO] Running low on time, skipping depth {current_depth}")
                    current_depth += 1
                    continue  # Skip directly to next iteration
            
            # Print final statistics
            print(f"[INFO] Search completed:")
            print(f"  - Time used: {self.time_control['time_used']:.2f}s")
            print(f"  - Nodes searched: {self.nodes_searched}")
            print(f"  - Nodes per second: {self.time_control['nodes_per_second']:.0f}")
            print(f"  - Maximum depth reached: {self.time_control['last_depth_completed']}")
            
            # Return the best move found
            if best_move and isinstance(best_move, chess.Move):
                return best_move
            elif self.time_control['best_move'] and isinstance(self.time_control['best_move'], chess.Move):
                return self.time_control['best_move']
            else:
                return legal_moves[0] if legal_moves else None
                
        except Exception as e:
            print(f"[ERROR] Failed to make move: Unexpected error during search: {e}")
            # If we have a valid move from earlier iterations, use it
            if self.time_control['best_move'] and isinstance(self.time_control['best_move'], chess.Move):
                return self.time_control['best_move']
            # Otherwise try first legal move
            return legal_moves[0] if legal_moves else None

    def get_move_time(self):
        """Get the time spent on the last move in seconds."""
        return time.time() - self.start_time

    def get_nodes_searched(self):
        """Get the number of positions evaluated in the last search."""
        return self.nodes_searched

# Example usage:
if __name__ == "__main__":
    # Create a new chess board
    board = chess.Board()
    
    # Create the engine
    engine = Engine(max_depth=4, max_time=10.0)
    
    # Make a move
    move = engine.make_move(board)
    if move:
        print(f"Engine plays: {move.uci()}")
        board.push(move)
        print(f"Time spent: {engine.get_move_time():.2f} seconds")
        print(f"Positions evaluated: {engine.get_nodes_searched()}")
        print("\nCurrent position:")
        print(board)
    else:
        print("No legal moves available!")
