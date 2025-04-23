"""
Position evaluation functions for a chess engine.
This module evaluates positional aspects of a chess position, including center control,
development, space control, and piece coordination, with phase-specific weights.
"""

import chess
from .weights import EVALUATION_WEIGHTS, get_weight

class PositionEvaluator:
    def __init__(self):
        """Initialize the position evaluator."""
        pass

    def evaluate(self, board: chess.Board) -> int:
        """
        Evaluate the overall position for both colors.
        Args:
            board (chess.Board): Current chess position
        Returns:
            int: Total evaluation score (positive for White advantage, negative for Black)
        """
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            position_score = self._evaluate_position(board, color)
            score += position_score * (1 if color == chess.WHITE else -1)
        return score

    def evaluate_center_control(self, board: chess.Board) -> int:
        """
        Evaluate center control for both colors.
        Args:
            board (chess.Board): Current chess position
        Returns:
            int: Center control score
        """
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            center_score = self._evaluate_center_control(board, color)
            score += center_score * (1 if color == chess.WHITE else -1)
        return score

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
            taper_factor = (phase_value - 6) / 12.0  # Linear interpolation between 6 and 18
            return 'middlegame', taper_factor

    def _evaluate_position(self, board: chess.Board, color: chess.Color) -> int:
        """
        Evaluate the overall position for a given color with tapered evaluation.
        Args:
            board (chess.Board): Current chess position
            color (chess.Color): Color to evaluate for
        Returns:
            int: Positional score for the given color
        """
        phase, taper_factor = self._get_game_phase(board)
        score = 0

        # Evaluate components with phase-specific weights
        center_score = self._evaluate_center_control(board, color)
        development_score = self._evaluate_development(board, color)
        space_score = self._evaluate_space_control(board, color)
        coordination_score = self._evaluate_piece_coordination(board, color)

        # Apply phase-specific weights from weights.py
        phase_weights = EVALUATION_WEIGHTS['phase_importance'][phase]
        score += center_score * phase_weights['center_control']
        score += development_score * phase_weights['development']
        score += space_score * phase_weights['piece_activity']
        score += coordination_score * phase_weights['piece_activity']

        # Endgame-specific evaluation
        if phase == 'endgame' or taper_factor < 1.0:
            endgame_score = self._evaluate_endgame_position(board, color)
            if phase == 'endgame':
                score += endgame_score * phase_weights['king_safety']
            else:
                # Taper between middlegame and endgame
                score += endgame_score * (1.0 - taper_factor) * phase_weights['king_safety']

        return score

    def _evaluate_center_control(self, board: chess.Board, color: chess.Color) -> int:
        """
        Evaluate control of central squares (d4, d5, e4, e5).
        Args:
            board (chess.Board): Current chess position
            color (chess.Color): Color to evaluate for
        Returns:
            int: Center control score
        """
        score = 0
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        for square in center_squares:
            attackers = len(list(board.attackers(color, square)))
            defenders = len(list(board.attackers(not color, square)))
            if attackers > defenders:
                score += get_weight('piece_activity', 'center_bonus') * (attackers - defenders)
        return score

    def _evaluate_development(self, board: chess.Board, color: chess.Color) -> int:
        """
        Evaluate piece development (pieces moved from starting squares).
        Args:
            board (chess.Board): Current chess position
            color (chess.Color): Color to evaluate for
        Returns:
            int: Development score
        """
        score = 0
        developed_pieces = 0

        # Knights
        knight_squares = [chess.B1, chess.G1] if color == chess.WHITE else [chess.B8, chess.G8]
        for square in board.pieces(chess.KNIGHT, color):
            if square not in knight_squares:
                developed_pieces += 1

        # Bishops
        bishop_squares = [chess.C1, chess.F1] if color == chess.WHITE else [chess.C8, chess.F8]
        for square in board.pieces(chess.BISHOP, color):
            if square not in bishop_squares:
                developed_pieces += 1

        # Queen (developed if not on starting square)
        queen_square = chess.D1 if color == chess.WHITE else chess.D8
        for square in board.pieces(chess.QUEEN, color):
            if square != queen_square:
                developed_pieces += 1

        score += developed_pieces * get_weight('development', 'piece_development', 'opening')
        return score

    def _evaluate_space_control(self, board: chess.Board, color: chess.Color) -> int:
        """
        Evaluate space control using bitboards for efficiency.
        Args:
            board (chess.Board): Current chess position
            color (chess.Color): Color to evaluate for
        Returns:
            int: Space control score
        """
        score = 0
        enemy_half = chess.BB_RANKS_1234 if color == chess.WHITE else chess.BB_RANKS_5678
        friendly_half = chess.BB_RANKS_5678 if color == chess.WHITE else chess.BB_RANKS_1234

        for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            for square in board.pieces(piece_type, color):
                attacks = board.attacks(square)
                enemy_attacks = bin(attacks & enemy_half).count('1')
                score += enemy_attacks * 3
                friendly_attacks = bin(attacks & friendly_half).count('1')
                score += friendly_attacks
                if square & enemy_half:
                    score += 10
        return score

    def _evaluate_piece_coordination(self, board: chess.Board, color: chess.Color) -> int:
        """
        Evaluate how well pieces work together using bitboards.
        Args:
            board (chess.Board): Current chess position
            color (chess.Color): Color to evaluate for
        Returns:
            int: Coordination score
        """
        score = 0
        for square in chess.SQUARES:
            attackers = board.attackers(color, square)
            attacker_count = bin(attackers).count('1')
            if attacker_count >= 2:
                score += get_weight('piece_activity', 'coordination') * (attacker_count - 1)

        for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            for square in board.pieces(piece_type, color):
                if board.is_attacked_by(color, square):
                    score += 10  # Bonus for protected pieces
        return score

    def _evaluate_endgame_position(self, board: chess.Board, color: chess.Color) -> int:
        """
        Evaluate position specifically for endgame scenarios.
        Args:
            board (chess.Board): Current chess position
            color (chess.Color): Color to evaluate for
        Returns:
            int: Endgame-specific score
        """
        score = 0
        king_square = board.king(color)
        enemy_king_square = board.king(not color)

        if king_square and enemy_king_square:
            # King centralization
            king_file, king_rank = chess.square_file(king_square), chess.square_rank(king_square)
            king_center_distance = abs(3.5 - king_file) + abs(3.5 - king_rank)
            score += (14 - king_center_distance) * 10

            # King opposition
            file_distance = abs(chess.square_file(king_square) - chess.square_file(enemy_king_square))
            rank_distance = abs(chess.square_rank(king_square) - chess.square_rank(enemy_king_square))
            if file_distance + rank_distance == 2:
                score += get_weight('endgame_specific', 'opposition_bonus')

        return score
