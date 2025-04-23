"""
Main evaluator module that combines all evaluation aspects.
This module integrates material and positional evaluations from sub-evaluators with phase-specific weights.
"""

import chess
from .weights import EVALUATION_WEIGHTS
from .phase_evaluator import PhaseEvaluator
from .position_evaluation import PositionEvaluator
from .king_evaluation import KingEvaluator
from .pawn_evaluation import PawnEvaluator
from .piece_evaluation import PieceEvaluator

class MainEvaluator:
    def __init__(self):
        """Initialize the main evaluator with all sub-evaluators."""
        self.phase_evaluator = PhaseEvaluator()
        self.position_evaluator = PositionEvaluator()
        self.king_evaluator = KingEvaluator()
        self.pawn_evaluator = PawnEvaluator()
        self.piece_evaluator = PieceEvaluator()

    def get_game_phase(self, board):
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

    def evaluate_material(self, board):
        """
        Evaluate material balance.
        Args:
            board (chess.Board): Current chess position
        Returns:
            float: Material score
        """
        score = 0
        for piece_type in chess.PIECE_TYPES:
            white_pieces = len(board.pieces(piece_type, chess.WHITE))
            black_pieces = len(board.pieces(piece_type, chess.BLACK))
            piece_value = EVALUATION_WEIGHTS['material']['default'].get(
                chess.piece_name(piece_type).lower(), 0)
            score += (white_pieces - black_pieces) * piece_value
        return score

    def evaluate(self, board):
        """
        Main evaluation function that combines material and positional aspects from all sub-evaluators.
        Args:
            board (chess.Board): Current chess position
        Returns:
            float: Total evaluation score
        """
        phase, taper_factor = self.get_game_phase(board)
        total_score = 0

        # Material evaluation with phase-specific weighting
        material_score = self.evaluate_material(board)
        material_weight = EVALUATION_WEIGHTS['phase_importance'][phase].get('material', 1.0)
        if phase == 'middlegame' and taper_factor < 1.0:
            endgame_weight = EVALUATION_WEIGHTS['phase_importance']['endgame'].get('material', 1.0)
            material_weight = material_weight * taper_factor + endgame_weight * (1.0 - taper_factor)
        total_score += material_score * material_weight

        # Positional and phase-specific evaluations using sub-evaluators
        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1

            # King safety evaluation
            king_score = self.king_evaluator.evaluate(board, color)
            king_weight = EVALUATION_WEIGHTS['phase_importance'][phase].get('king_safety', 1.0)
            if phase == 'middlegame' and taper_factor < 1.0:
                endgame_weight = EVALUATION_WEIGHTS['phase_importance']['endgame'].get('king_safety', 1.0)
                king_weight = king_weight * taper_factor + endgame_weight * (1.0 - taper_factor)
            total_score += king_score * king_weight * multiplier

            # Pawn structure evaluation
            pawn_score = self.pawn_evaluator.evaluate_structure(board, color)
            if phase == 'endgame':
                pawn_score += self.pawn_evaluator.evaluate_promotion_potential(board, color) * 2
            pawn_weight = EVALUATION_WEIGHTS['phase_importance'][phase].get('pawn_structure', 1.0)
            if phase == 'middlegame' and taper_factor < 1.0:
                endgame_weight = EVALUATION_WEIGHTS['phase_importance']['endgame'].get('pawn_structure', 1.0)
                pawn_weight = pawn_weight * taper_factor + endgame_weight * (1.0 - taper_factor)
            total_score += pawn_score * pawn_weight * multiplier

            # Piece activity and mobility evaluation
            activity_score = self.piece_evaluator.evaluate_activity(board, color)
            mobility_score = self.piece_evaluator.evaluate_mobility(board, color)
            activity_weight = EVALUATION_WEIGHTS['phase_importance'][phase].get('piece_activity', 1.0)
            if phase == 'middlegame' and taper_factor < 1.0:
                endgame_weight = EVALUATION_WEIGHTS['phase_importance']['endgame'].get('piece_activity', 1.0)
                activity_weight = activity_weight * taper_factor + endgame_weight * (1.0 - taper_factor)
            total_score += (activity_score + mobility_score) * activity_weight * multiplier

            # Position evaluation (center control and space)
            position_score = self.position_evaluator.evaluate_center_control(board) * multiplier
            position_score += self.position_evaluator.evaluate(board)
            position_weight = EVALUATION_WEIGHTS['phase_importance'][phase].get('center_control', 1.0)
            if phase == 'middlegame' and taper_factor < 1.0:
                endgame_weight = EVALUATION_WEIGHTS['phase_importance']['endgame'].get('center_control', 1.0)
                position_weight = position_weight * taper_factor + endgame_weight * (1.0 - taper_factor)
            total_score += position_score * position_weight * multiplier

        # Additional endgame bonuses
        if phase == 'endgame':
            for color in [chess.WHITE, chess.BLACK]:
                multiplier = 1 if color == chess.WHITE else -1
                if board.is_check():
                    total_score += 50 * multiplier  # Bonus for giving check in endgame
                passed_pawns = sum(1 for square in board.pieces(chess.PAWN, color)
                                 if self.pawn_evaluator.is_passed_pawn(board, square, color))
                total_score += passed_pawns * 30 * multiplier  # Bonus for passed pawns

        # Normalize and bound the score
        return max(min(total_score, 1000), -1000)
