"""
Chess Engine module that implements the AI logic for playing chess.
This module uses alpha-beta pruning to find the best move.
"""

import chess
import time
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        self.best_move = None
        self.best_score = float('-inf')
        
        # Basic piece values for material counting
        self.piece_values = {
            'p': 100,   # pawn
            'n': 320,   # knight
            'b': 330,   # bishop
            'r': 500,   # rook
            'q': 900,   # queen
            'k': 20000  # king
        }
        
        # Piece-square tables for positional evaluation
        self.pawn_table = [
            0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5,  5, 10, 25, 25, 10,  5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5, -5,-10,  0,  0,-10, -5,  5,
            5, 10, 10,-20,-20, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0
        ]
        
        self.knight_table = [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50
        ]
        
        self.bishop_table = [
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10, 10, 10, 10, 10, 10, 10,-10,
            -10,  5,  0,  0,  0,  0,  5,-10,
            -20,-10,-10,-10,-10,-10,-10,-20
        ]
        
        self.king_table = [
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -20,-30,-30,-40,-40,-30,-30,-20,
            -10,-20,-20,-20,-20,-20,-20,-10,
            20, 20,  0,  0,  0,  0, 20, 20,
            20, 30, 10,  0,  0, 10, 30, 20
        ]
        
        # Initialize board
        self.board = chess.Board()

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

    def is_endgame(self, board):
        """
        Determine if the current position is an endgame.
        A position is considered an endgame if:
        1. Both sides have no queens, or
        2. One side has no queens and the other has at most one minor piece
        """
        # Count pieces for both sides
        white_queens = len(board.pieces(chess.QUEEN, chess.WHITE))
        black_queens = len(board.pieces(chess.QUEEN, chess.BLACK))
        
        white_minors = len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.WHITE))
        black_minors = len(board.pieces(chess.KNIGHT, chess.BLACK)) + len(board.pieces(chess.BISHOP, chess.BLACK))
        
        # No queens on either side
        if white_queens == 0 and black_queens == 0:
            return True
            
        # One side has no queens and the other has at most one minor piece
        if (white_queens == 0 and black_minors <= 1) or (black_queens == 0 and white_minors <= 1):
            return True
            
        return False

    def evaluate_position(self, board):
        """
        Evaluate the current board position with multiple factors.
        Returns a score from white's perspective.
        """
        score = 0
        
        # Material evaluation
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.piece_values[piece.symbol().lower()]
                # Always evaluate from white's perspective
                score += value if piece.color == chess.WHITE else -value
                
                # Piece-square table evaluation
                if piece.color == chess.WHITE:
                    if piece.symbol().lower() == 'p':
                        score += self.pawn_table[square]
                    elif piece.symbol().lower() == 'n':
                        score += self.knight_table[square]
                    elif piece.symbol().lower() == 'b':
                        score += self.bishop_table[square]
                    elif piece.symbol().lower() == 'k':
                        score += self.king_table[square]
                else:
                    if piece.symbol().lower() == 'p':
                        score -= self.pawn_table[chess.square_mirror(square)]
                    elif piece.symbol().lower() == 'n':
                        score -= self.knight_table[chess.square_mirror(square)]
                    elif piece.symbol().lower() == 'b':
                        score -= self.bishop_table[chess.square_mirror(square)]
                    elif piece.symbol().lower() == 'k':
                        score -= self.king_table[chess.square_mirror(square)]
        
        # Mobility evaluation
        white_mobility = len(list(board.legal_moves))
        board.push(chess.Move.null())
        black_mobility = len(list(board.legal_moves))
        board.pop()
        score += (white_mobility - black_mobility) * 0.1
        
        # Pawn structure evaluation
        white_pawns = board.pieces(chess.PAWN, chess.WHITE)
        black_pawns = board.pieces(chess.PAWN, chess.BLACK)
        
        # Doubled pawns penalty
        for file in range(8):
            white_pawns_in_file = sum(1 for pawn in white_pawns if chess.square_file(pawn) == file)
            black_pawns_in_file = sum(1 for pawn in black_pawns if chess.square_file(pawn) == file)
            if white_pawns_in_file > 1:
                score -= 10 * (white_pawns_in_file - 1)
            if black_pawns_in_file > 1:
                score += 10 * (black_pawns_in_file - 1)
        
        # King safety evaluation
        white_king_square = board.king(chess.WHITE)
        black_king_square = board.king(chess.BLACK)
        
        # Penalize if king is in the center during middle game
        if not self.is_endgame(board):
            if chess.square_file(white_king_square) in [3, 4]:
                score -= 20
            if chess.square_file(black_king_square) in [3, 4]:
                score += 20
        
        # If it's black's turn, negate the score since we want to minimize
        if board.turn == chess.BLACK:
            score = -score
            
        return score

    def order_moves(self, board, moves):
        """
        Order moves to improve alpha-beta pruning efficiency.
        Prioritizes captures and checks.
        """
        move_scores = []
        for move in moves:
            score = 0
            
            # Capture moves
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    score += 10 * self.piece_values[captured_piece.symbol().lower()]
            
            # Check moves
            board.push(move)
            if board.is_check():
                score += 50
            board.pop()
            
            move_scores.append((move, score))
        
        # Sort moves by score in descending order
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in move_scores]

    def alpha_beta(self, board, depth, alpha, beta, maximizing_player):
        """
        Alpha-beta pruning algorithm.
        
        Args:
            board: Current chess position
            depth: Current search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            maximizing_player: True if current player is maximizing
            
        Returns:
            float: Evaluation score
        """
        self.nodes_searched += 1
        
        # Check for terminal conditions
        if depth == 0 or board.is_game_over():
            # Evaluate from the current player's perspective
            score = self.evaluate_position(board)
            # If it's black's turn, negate the score since we want to minimize
            if board.turn == chess.BLACK:
                score = -score
            return score
        
        # Get and order legal moves
        legal_moves = list(board.legal_moves)
        legal_moves = self.order_moves(board, legal_moves)
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in legal_moves:
                board.push(move)
                eval = self.alpha_beta(board, depth - 1, alpha, beta, False)
                board.pop()
                
                if eval > max_eval:
                    max_eval = eval
                    if depth == self.max_depth:  # Root node
                        self.best_move = move
                        self.best_score = eval
                
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break  # Beta cutoff
                    
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval = self.alpha_beta(board, depth - 1, alpha, beta, True)
                board.pop()
                
                if eval < min_eval:
                    min_eval = eval
                    if depth == self.max_depth:  # Root node
                        self.best_move = move
                        self.best_score = eval
                
                beta = min(beta, eval)
                if beta <= alpha:
                    break  # Alpha cutoff
                    
            return min_eval

    def get_best_move(self):
        """Get best move using alpha-beta pruning."""
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
            
            # Initialize search
            self.nodes_searched = 0
            self.start_time = time.time()
            self.best_move = None
            self.best_score = float('-inf')
            
            print(f"[INFO] Starting search with time limit: {self.max_time} seconds")
            
            # Determine if we're maximizing or minimizing
            is_maximizing = self.board.turn == chess.WHITE
            
            # Perform alpha-beta search
            score = self.alpha_beta(self.board, self.max_depth, float('-inf'), float('inf'),
                                  is_maximizing)
            
            # Print final statistics
            time_used = time.time() - self.start_time
            nodes_per_second = self.nodes_searched / max(0.1, time_used)
            
            print(f"[INFO] Search completed:")
            print(f"  - Time used: {time_used:.2f}s")
            print(f"  - Nodes searched: {self.nodes_searched}")
            print(f"  - Nodes per second: {nodes_per_second:.0f}")
            print(f"  - Best move: {self.best_move.uci() if self.best_move else 'None'}")
            print(f"  - Score: {self.best_score}")
            print(f"  - Player: {'White' if is_maximizing else 'Black'}")
            
            return self.best_move if self.best_move else legal_moves[0]
                
        except Exception as e:
            print(f"[ERROR] Failed to get best move: {e}")
            return legal_moves[0] if legal_moves else None

if __name__ == "__main__":
    # Example usage
    engine = Engine(max_depth=4, max_time=10.0)
    engine.set_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    best_move = engine.get_best_move()
    if best_move:
        print(f"Best move: {best_move.uci()}")
    else:
        print("No move found")
