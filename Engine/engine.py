import chess
import chess.engine
import time
import sys
import os
import threading
import queue
import random

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Engine:
    def __init__(self, engine_type="kingfish", max_depth=4, max_time=10.0, num_threads=4):
        """
        Initialize the chess engine.
        
        Args:
            engine_type (str): Type of engine to use ("kingfish" for kingfish.exe, "custom" for alpha-beta engine)
            max_depth (int): Maximum depth for custom engine search
            max_time (float): Maximum time in seconds to spend on a move (default: 10.0)
            num_threads (int): Number of threads for custom engine (default: 4)
        """
        self.engine_type = engine_type
        self.max_depth = max_depth
        self.max_time = max_time
        self.num_threads = max(1, num_threads)
        
        if self.engine_type == "kingfish":
            # Initialize Kingfish engine
            self.engine_path = "C:\\Users\\ducal\\Documents\\chess_group7\\engines\\kingfish.exe"
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
                print(f"[INFO] Initialized Kingfish engine at {self.engine_path}")
            except Exception as e:
                print(f"[ERROR] Failed to initialize Kingfish engine: {e}")
                self.engine = None
        else:
            # Initialize custom alpha-beta engine
            self.nodes_searched = 0
            self.start_time = 0
            self.best_move = None
            self.best_score = float('-inf')
            
            # Thread synchronization
            self.abort_search = False
            self.move_lock = threading.Lock()
            self.nodes_lock = threading.Lock()
            self.tt_lock = threading.Lock()
            
            # Shared transposition table
            self.transposition_table = {}
            
            # Piece values
            self.piece_values = {
                'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000
            }
            
            # Piece-square tables
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
            
            # Initialize board for custom engine
            self.board = chess.Board()

    def set_position(self, fen):
        """Set board position using FEN string."""
        if self.engine_type == "kingfish":
            # Kingfish engine handles position internally via UCI
            self.board = chess.Board(fen)
            return True
        else:
            # Custom engine
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
        """Determine if the current position is an endgame (for custom engine)."""
        white_queens = len(board.pieces(chess.QUEEN, chess.WHITE))
        black_queens = len(board.pieces(chess.QUEEN, chess.BLACK))
        
        white_minors = len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.WHITE))
        black_minors = len(board.pieces(chess.KNIGHT, chess.BLACK)) + len(board.pieces(chess.BISHOP, chess.BLACK))
        
        if white_queens == 0 and black_queens == 0:
            return True
        if (white_queens == 0 and black_minors <= 1) or (black_queens == 0 and white_minors <= 1):
            return True
        return False

    def evaluate_position(self, board):
        """Evaluate the current board position (for custom engine)."""
        score = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.piece_values[piece.symbol().lower()]
                score += value if piece.color == chess.WHITE else -value
                
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
        
        white_mobility = len(list(board.legal_moves))
        board.push(chess.Move.null())
        black_mobility = len(list(board.legal_moves))
        board.pop()
        score += (white_mobility - black_mobility) * 0.1
        
        white_pawns = board.pieces(chess.PAWN, chess.WHITE)
        black_pawns = board.pieces(chess.PAWN, chess.BLACK)
        
        for file in range(8):
            white_pawns_in_file = sum(1 for pawn in white_pawns if chess.square_file(pawn) == file)
            black_pawns_in_file = sum(1 for pawn in black_pawns if chess.square_file(pawn) == file)
            if white_pawns_in_file > 1:
                score -= 10 * (white_pawns_in_file - 1)
            if black_pawns_in_file > 1:
                score += 10 * (black_pawns_in_file - 1)
        
        white_king_square = board.king(chess.WHITE)
        black_king_square = board.king(chess.BLACK)
        
        if not self.is_endgame(board):
            if chess.square_file(white_king_square) in [3, 4]:
                score -= 20
            if chess.square_file(black_king_square) in [3, 4]:
                score += 20
        
        if board.turn == chess.BLACK:
            score = -score
        return score

    def order_moves(self, board, moves, thread_id=0):
        """Order moves for custom engine."""
        move_scores = []
        for move in moves:
            score = 0
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    score += 10 * self.piece_values[captured_piece.symbol().lower()]
            board.push(move)
            if board.is_check():
                score += 50
            board.pop()
            if thread_id > 0:
                score += random.uniform(-0.1, 0.1) * thread_id
            move_scores.append((move, score))
        
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in move_scores]

    def check_time(self):
        """Check time limit for custom engine."""
        return time.time() - self.start_time >= self.max_time

    def probe_tt(self, board_fen, depth):
        """Probe transposition table for custom engine."""
        with self.tt_lock:
            key = (board_fen, depth)
            if key in self.transposition_table:
                return self.transposition_table[key]
        return None

    def store_tt(self, board_fen, depth, value, best_move):
        """Store in transposition table for custom engine."""
        with self.tt_lock:
            key = (board_fen, depth)
            self.transposition_table[key] = (value, best_move)

    def alpha_beta(self, board, depth, alpha, beta, maximizing_player, thread_id=0):
        """Alpha-beta pruning for custom engine."""
        with self.nodes_lock:
            self.nodes_searched += 1
        
        if self.abort_search or self.check_time():
            return 0
        
        if depth == 0 or board.is_game_over():
            score = self.evaluate_position(board)
            if board.turn == chess.BLACK:
                score = -score
            return score
        
        board_fen = board.fen()
        tt_result = self.probe_tt(board_fen, depth)
        if tt_result:
            return tt_result[0]
        
        legal_moves = list(board.legal_moves)
        legal_moves = self.order_moves(board, legal_moves, thread_id)
        
        best_move = None
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in legal_moves:
                board.push(move)
                eval = self.alpha_beta(board, depth - 1, alpha, beta, False, thread_id)
                board.pop()
                
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                    if depth == self.max_depth:
                        with self.move_lock:
                            if eval > self.best_score:
                                self.best_move = move
                                self.best_score = eval
                
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            
            self.store_tt(board_fen, depth, max_eval, best_move)
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval = self.alpha_beta(board, depth - 1, alpha, beta, True, thread_id)
                board.pop()
                
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                    if depth == self.max_depth:
                        with self.move_lock:
                            if eval < self.best_score:
                                self.best_move = move
                                self.best_score = eval
                
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            
            self.store_tt(board_fen, depth, min_eval, best_move)
            return min_eval

    def search_thread(self, board, depth, alpha, beta, maximizing_player, thread_id, result_queue):
        """Thread function for custom engine."""
        try:
            board_copy = chess.Board(board.fen())
            depth_adjustment = 0
            if thread_id % 2 == 0 and depth > 1:
                depth_adjustment = -1
            score = self.alpha_beta(board_copy, depth + depth_adjustment, alpha, beta, maximizing_player, thread_id)
            result_queue.put((thread_id, score, self.best_move))
        except Exception as e:
            print(f"[ERROR] Thread {thread_id} failed: {e}")
            result_queue.put((thread_id, None, None))

    def get_best_move(self):
        """Get best move using either Kingfish or custom engine."""
        if self.engine_type == "kingfish":  
            if not self.engine:
                print("[ERROR] Kingfish engine not initialized")
                return None
            try:
                # Check if game is over
                if self.board.is_game_over():
                    print("[INFO] Game is over")
                    return None
                
                # Use Kingfish engine
                result = self.engine.play(
                    self.board,
                    chess.engine.Limit(time=self.max_time, depth=self.max_depth)
                )
                move = result.move
                if move in self.board.legal_moves:
                    return move
                else:
                    print(f"[ERROR] Invalid move from Kingfish: {move}")
                    return None
            except Exception as e:
                print(f"[ERROR] Failed to get move from Kingfish: {e}")
                return None
        else:
            # Custom engine
            if not self.board:
                print("[ERROR] Board not initialized")
                return None
            
            try:
                if self.board.is_game_over():
                    print("[INFO] Game is over")
                    return None
                
                legal_moves = list(self.board.legal_moves)
                if not legal_moves:
                    print("[INFO] No legal moves available")
                    return None
                
                if len(legal_moves) == 1:
                    print("[INFO] Only one legal move available")
                    return legal_moves[0]
                
                self.nodes_searched = 0
                self.start_time = time.time()
                self.best_move = None
                self.best_score = float('-inf') if self.board.turn == chess.WHITE else float('inf')
                self.abort_search = False
                self.transposition_table = {}
                
                print(f"[INFO] Starting Lazy SMP search with {self.num_threads} threads")
                print(f"[INFO] Time limit: {self.max_time} seconds, Depth: {self.max_depth}")
                
                is_maximizing = self.board.turn == chess.WHITE
                
                threads = []
                result_queue = queue.Queue()
                
                for i in range(self.num_threads):
                    t = threading.Thread(
                        target=self.search_thread,
                        args=(self.board, self.max_depth, float('-inf'), float('inf'), is_maximizing, i, result_queue)
                    )
                    t.daemon = True
                    threads.append(t)
                    t.start()
                
                end_time = self.start_time + self.max_time
                running = True
                
                while running and time.time() < end_time:
                    all_done = all(not t.is_alive() for t in threads)
                    if all_done:
                        running = False
                    time.sleep(0.01)
                
                self.abort_search = True
                
                for t in threads:
                    t.join(0.1)
                
                results = []
                while not result_queue.empty():
                    try:
                        results.append(result_queue.get_nowait())
                    except queue.Empty:
                        break
                
                time_used = time.time() - self.start_time
                nodes_per_second = self.nodes_searched / max(0.1, time_used)
                
                print(f"[INFO] Lazy SMP search completed:")
                print(f"  - Time used: {time_used:.2f}s")
                print(f"  - Nodes searched: {self.nodes_searched}")
                print(f"  - Nodes per second: {nodes_per_second:.0f}")
                print(f"  - Threads used: {self.num_threads}")
                print(f"  - Best move: {self.best_move.uci() if self.best_move else 'None'}")
                print(f"  - Score: {self.best_score}")
                print(f"  - Player: {'White' if is_maximizing else 'Black'}")
                
                return self.best_move if self.best_move else legal_moves[0]
                    
            except Exception as e:
                print(f"[ERROR] Failed to get best move: {e}")
                return legal_moves[0] if legal_moves else None

    def quit(self):
        """Clean up engine resources."""
        if self.engine_type == "kingfish" and self.engine:
            try:
                self.engine.quit()
                print("[INFO] Kingfish engine closed")
            except Exception as e:
                print(f"[ERROR] Failed to close Kingfish engine: {e}")

if __name__ == "__main__":
    # Example usage with Kingfish engine
    engine = Engine(engine_type="kingfish", max_depth=4, max_time=10.0)
    engine.set_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    best_move = engine.get_best_move()
    if best_move:
        print(f"Best move: {best_move.uci()}")
    else:
        print("No move found")
    engine.quit()

    # Example usage with custom engine
    engine = Engine(engine_type="custom", max_depth=4, max_time=10.0, num_threads=4)
    engine.set_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    best_move = engine.get_best_move()
    if best_move:
        print(f"Best move: {best_move.uci()}")
    else:
        print("No move found")