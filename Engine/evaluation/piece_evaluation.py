"""
Piece activity and mobility evaluation functions.
This module evaluates piece activity, mobility, and development with phase-specific weights.
"""

import chess
from functools import lru_cache
from .weights import EVALUATION_WEIGHTS, get_weight

class PieceEvaluator:
    def __init__(self):
        """Initialize the piece evaluator."""
        pass

    def evaluate_activity(self, board: chess.Board, color: chess.Color) -> int:
        """Evaluate piece activity for a given color."""
        return self._evaluate_piece_activity(board, color)

    def evaluate_mobility(self, board: chess.Board, color: chess.Color) -> int:
        """Evaluate piece mobility for a given color."""
        score = 0
        phase, _ = self._get_game_phase(board)
        # Reuse cached attacks from activity evaluation if available
        if hasattr(board, '_cached_attacks') and board._cached_attacks.get(color):
            attacks_data = board._cached_attacks[color]
        else:
            attacks_data = self._compute_attacks(board, color)
            if not hasattr(board, '_cached_attacks'):
                board._cached_attacks = {}
            board._cached_attacks[color] = attacks_data

        for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            mobility_key = f"{chess.piece_name(piece_type).split()[0]}_mobility"
            weight = get_weight('piece_activity', mobility_key, phase)
            for square, attacks in attacks_data.get(piece_type, {}).items():
                mobility = len(attacks & ~board.occupied_co[color])
                score += mobility * weight
        return score

    def evaluate_development(self, board: chess.Board, color: chess.Color) -> int:
        """Evaluate piece development for a given color."""
        return self._evaluate_development(board, color)

    def _get_game_phase(self, board):
        """
        Determine the current game phase using a weighted piece value system.
        Args:
            board (chess.Board): Current chess position
        Returns:
            tuple: (str: Game phase ('opening', 'middlegame', 'endgame'), float: taper factor)
        """
        phase_value = 0
        phase_weights = {
            chess.QUEEN: 4,
            chess.ROOK: 2,
            chess.BISHOP: 1,
            chess.KNIGHT: 1,
            chess.PAWN: 0
        }
        for piece_type in chess.PIECE_TYPES:
            if piece_type == chess.KING:
                continue
            phase_value += (len(board.pieces(piece_type, chess.WHITE)) +
                           len(board.pieces(piece_type, chess.BLACK))) * phase_weights.get(piece_type, 0)

        if phase_value >= 18:
            return 'opening', 1.0
        elif phase_value <= 6:
            return 'endgame', 0.0
        else:
            taper_factor = (phase_value - 6) / 12.0  # Linear interpolation
            return 'middlegame', taper_factor

    @lru_cache(maxsize=2048)
    def _get_piece_attacks(self, square: chess.Square, piece_type: chess.PieceType, board_fen: str) -> chess.SquareSet:
        """Get cached piece attacks using board FEN to handle dynamic states."""
        temp_board = chess.Board(board_fen)
        temp_board.clear()
        temp_board.set_piece_at(square, chess.Piece(piece_type, chess.WHITE))
        return temp_board.attacks(square)

    def _compute_attacks(self, board: chess.Board, color: chess.Color) -> dict:
        """Compute and cache attacks for all pieces of a color."""
        attacks_data = {
            chess.KNIGHT: {},
            chess.BISHOP: {},
            chess.ROOK: {},
            chess.QUEEN: {}
        }
        board_fen = board.fen()
        for piece_type in attacks_data.keys():
            for square in board.pieces(piece_type, color):
                attacks_data[piece_type][square] = self._get_piece_attacks(square, piece_type, board_fen)
        return attacks_data

    def _evaluate_piece_activity(self, board: chess.Board, color: chess.Color) -> int:
        """Evaluate piece activity for a given color with game phase adjustment."""
        score = 0
        phase, taper_factor = self._get_game_phase(board)

        # Cache attacks for reuse
        attacks_data = self._compute_attacks(board, color)
        if not hasattr(board, '_cached_attacks'):
            board._cached_attacks = {}
        board._cached_attacks[color] = attacks_data

        # Evaluate each piece type with phase-specific weights
        for piece_type, data in attacks_data.items():
            mobility_key = f"{chess.piece_name(piece_type).split()[0]}_mobility"
            weight = get_weight('piece_activity', mobility_key, phase)
            for square, attacks in data.items():
                mobility = len(attacks & board.occupied_co[not color])
                score += mobility * weight
                # Center control bonus
                if square in [chess.D4, chess.D5, chess.E4, chess.E5]:
                    score += get_weight('piece_activity', 'center_bonus', phase)
                # Piece-specific evaluation
                if piece_type == chess.KNIGHT:
                    score += self._evaluate_knight_position(board, square, color, phase)
                elif piece_type == chess.BISHOP:
                    score += self._evaluate_bishop_position(board, square, color, phase)
                elif piece_type == chess.ROOK:
                    score += self._evaluate_rook_position(board, square, color, phase)
                elif piece_type == chess.QUEEN:
                    score += self._evaluate_queen_position(board, square, color, phase)

        # Evaluate piece coordination and tactical features
        score += self._evaluate_piece_coordination(board, color, phase)
        score += self._evaluate_tactical_features(board, color, phase)

        # Apply overall activity weight with tapering if needed
        activity_weight = get_weight('phase_importance', 'piece_activity', phase)
        if phase == 'middlegame' and taper_factor < 1.0:
            endgame_weight = get_weight('phase_importance', 'piece_activity', 'endgame')
            activity_weight = activity_weight * taper_factor + endgame_weight * (1.0 - taper_factor)
        return int(score * activity_weight)

    def _evaluate_knight_position(self, board: chess.Board, square: chess.Square, color: chess.Color, phase: str) -> int:
        """Evaluate knight position with phase-specific bonuses."""
        score = 0
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        # Knights are better in the center
        if file in [2, 3, 4, 5] and rank in [2, 3, 4, 5]:
            score += get_weight('piece_activity', 'center_bonus', phase) * 0.5
        # Knights are worse on the edge
        if file in [0, 7] or rank in [0, 7]:
            score -= get_weight('piece_activity', 'center_bonus', phase) * 0.3
        # Check for outpost
        if self._is_outpost(board, square, color, chess.KNIGHT):
            score += get_weight('piece_activity', 'outpost_bonus', phase)
        return score

    def _evaluate_bishop_position(self, board: chess.Board, square: chess.Square, color: chess.Color, phase: str) -> int:
        """Evaluate bishop position with phase-specific bonuses."""
        score = 0
        # Bishop pair bonus
        if len(board.pieces(chess.BISHOP, color)) == 2:
            score += get_weight('piece_activity', 'bishop_pair', phase)
        # Open diagonals are better
        attacks = self._get_piece_attacks(square, chess.BISHOP, board.fen())
        mobility = len(attacks & board.occupied_co[not color])
        score += mobility * get_weight('piece_activity', 'bishop_mobility', phase) * 0.5
        # Check for bishop outpost
        if self._is_outpost(board, square, color, chess.BISHOP):
            score += get_weight('piece_activity', 'outpost_bonus', phase)
        return score

    def _evaluate_rook_position(self, board: chess.Board, square: chess.Square, color: chess.Color, phase: str) -> int:
        """Evaluate rook position with phase-specific bonuses."""
        score = 0
        file = chess.square_file(square)
        # Check file status using bitboard operations
        file_mask = chess.BB_FILES[file]
        white_pawns = board.pieces(chess.PAWN, chess.WHITE) & file_mask
        black_pawns = board.pieces(chess.PAWN, chess.BLACK) & file_mask
        if not (white_pawns | black_pawns):
            score += get_weight('piece_activity', 'rook_open_file', phase)
        elif not (white_pawns if color == chess.WHITE else black_pawns):
            score += get_weight('piece_activity', 'rook_semi_open', phase)
        # Rooks are better on 7th rank
        if (color == chess.WHITE and chess.square_rank(square) == 6) or \
           (color == chess.BLACK and chess.square_rank(square) == 1):
            score += get_weight('piece_activity', 'rook_open_file', phase) * 0.5
        # Consider material at risk
        defenders = board.attackers(not color, square)
        if defenders and not board.attackers(color, square):
            score -= get_weight('piece_activity', 'center_bonus', phase) * 0.5  # Penalty for risk
        return score

    def _evaluate_queen_position(self, board: chess.Board, square: chess.Square, color: chess.Color, phase: str) -> int:
        """Evaluate queen position with phase-specific bonuses."""
        score = 0
        # Queen mobility using cached attacks
        attacks = self._get_piece_attacks(square, chess.QUEEN, board.fen())
        mobility = len(attacks & board.occupied_co[not color])
        score += mobility * get_weight('piece_activity', 'queen_mobility', phase) * 0.5
        # Queen is better in the center
        if square in [chess.D4, chess.D5, chess.E4, chess.E5]:
            score += get_weight('piece_activity', 'center_bonus', phase) * 0.3
        return score

    def _is_outpost(self, board: chess.Board, square: chess.Square, color: chess.Color, piece_type: chess.PieceType) -> bool:
        """Check if a piece (knight or bishop) is on an outpost."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        # Check if square is protected by own pawns
        protected = False
        for f in [file - 1, file + 1]:
            if 0 <= f <= 7:
                pawn_square = chess.square(f, rank + (1 if color == chess.WHITE else -1))
                if board.piece_at(pawn_square) == chess.Piece(chess.PAWN, color):
                    protected = True
                    break
        if not protected:
            return False
        # Check if square can be attacked by enemy pawns
        for f in [file - 1, file + 1]:
            if 0 <= f <= 7:
                pawn_square = chess.square(f, rank + (-1 if color == chess.WHITE else 1))
                if board.piece_at(pawn_square) == chess.Piece(chess.PAWN, not color):
                    return False
        return True

    def _evaluate_piece_coordination(self, board: chess.Board, color: chess.Color, phase: str) -> int:
        """Evaluate how well pieces work together using bitboards."""
        score = 0
        # Use bitboard operations for faster attack counting
        for square in chess.SQUARES:
            attackers = board.attackers(color, square)
            attacker_count = bin(attackers).count('1')
            if attacker_count >= 2:
                score += get_weight('piece_activity', 'coordination', phase) * (attacker_count - 1)
        return score

    def _evaluate_tactical_features(self, board: chess.Board, color: chess.Color, phase: str) -> int:
        """Evaluate tactical features like pins and forks using bitboards."""
        score = 0
        enemy_color = not color
        # Check for pins using bitboard operations
        for queen_square in board.pieces(chess.QUEEN, color):
            queen_attacks = self._get_piece_attacks(queen_square, chess.QUEEN, board.fen())
            for piece_type in [chess.QUEEN, chess.ROOK]:
                for square in board.pieces(piece_type, enemy_color):
                    if square in queen_attacks and self._is_pinned(board, square, queen_square, color):
                        score += get_weight('tactical_features', 'pin_bonus', 'default')
        # Check for potential forks
        for piece_type in [chess.KNIGHT, chess.QUEEN]:
            for square in board.pieces(piece_type, color):
                attacks = self._get_piece_attacks(square, piece_type, board.fen())
                valuable_targets = sum(1 for target in attacks if board.piece_at(target) and
                                      board.piece_at(target).color == enemy_color and
                                      board.piece_at(target).piece_type in [chess.QUEEN, chess.ROOK])
                if valuable_targets >= 2:
                    score += get_weight('tactical_features', 'fork_bonus', 'default')
        return score

    def _is_pinned(self, board: chess.Board, square: chess.Square, pinner: chess.Square, color: chess.Color) -> bool:
        """Check if a piece is pinned to the king using bitboards."""
        piece = board.piece_at(square)
        if not piece or piece.color == color:
            return False
        king_square = board.king(color)
        if not king_square:
            return False
        # Check if piece is on the same line as king and pinner
        file_s, rank_s = chess.square_file(square), chess.square_rank(square)
        file_k, rank_k = chess.square_file(king_square), chess.square_rank(king_square)
        file_p, rank_p = chess.square_file(pinner), chess.square_rank(pinner)
        if (file_s == file_k == file_p) or (rank_s == rank_k == rank_p) or \
           (abs(file_s - file_k) == abs(rank_s - rank_k) == abs(file_p - file_k)):
            return True
        return False

    def _evaluate_development(self, board: chess.Board, color: chess.Color) -> int:
        """Evaluate piece development for a given color with phase-specific weights."""
        score = 0
        phase, _ = self._get_game_phase(board)
        # Penalty for undeveloped knights and bishops
        for piece_type in [chess.KNIGHT, chess.BISHOP]:
            for square in board.pieces(piece_type, color):
                rank = chess.square_rank(square)
                if (color == chess.WHITE and rank == 0) or (color == chess.BLACK and rank == 7):
                    score -= get_weight('development', 'piece_development', phase) * 0.5
        # Bonus for castling
        if board.has_castling_rights(color):
            score += get_weight('development', 'piece_development', phase) * 0.8
        return score
