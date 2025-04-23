"""
Module for evaluating chess positions based on game phases.
Implements different evaluation strategies for opening, middlegame, and endgame with tapered evaluation.
"""

import chess
from .king_evaluation import KingEvaluator
from .pawn_evaluation import PawnEvaluator
from .piece_evaluation import PieceEvaluator
from .position_evaluation import PositionEvaluator
from .weights import EVALUATION_WEIGHTS, get_weight

class PhaseEvaluator:
    def __init__(self):
        """Initialize the phase evaluator with evaluators for each aspect."""
        # Initialize all evaluators
        self.king_evaluator = KingEvaluator()
        self.pawn_evaluator = PawnEvaluator()
        self.piece_evaluator = PieceEvaluator()
        self.position_evaluator = PositionEvaluator()

    def get_game_phase(self, board):
        """
        Determine the current game phase based on material and piece count with a weighted system.
        Args:
            board (chess.Board): Current chess position
        Returns:
            tuple: (str: Game phase ('opening', 'middlegame', or 'endgame'), float: phase factor for tapering)
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
        
        # Maximum phase value for initial position is roughly 24 (2Q, 4R, 4B, 4N)
        if phase_value >= 18:
            return 'opening', 1.0
        elif phase_value <= 6:
            return 'endgame', 0.0
        else:
            # Calculate a tapering factor between middlegame and endgame
            taper_factor = (phase_value - 6) / 12.0  # Linear interpolation between 6 and 18
            return 'middlegame', taper_factor

    def evaluate_phase_specific(self, board, phase, taper_factor):
        """
        Evaluate the position based on the current game phase with tapering for transitions.
        Args:
            board (chess.Board): Current chess position
            phase (str): Current game phase
            taper_factor (float): Factor for tapering evaluation between phases
        Returns:
            float: Evaluation score
        """
        score = 0.0
        phase_weights = EVALUATION_WEIGHTS['phase_importance'][phase]

        if phase == 'opening':
            center_score = self.position_evaluator.evaluate_center_control(board)
            score += center_score * phase_weights['center_control']
            for color in [chess.WHITE, chess.BLACK]:
                multiplier = 1 if color == chess.WHITE else -1
                development = self.piece_evaluator.evaluate_development(board, color)
                score += development * multiplier * phase_weights['development']
                king_safety = self.king_evaluator.evaluate(board, color)
                score += king_safety * multiplier * phase_weights['king_safety']
                pawn_structure = self.pawn_evaluator.evaluate_structure(board, color)
                score += pawn_structure * multiplier * phase_weights['pawn_structure']
                activity = self.piece_evaluator.evaluate_activity(board, color)
                score += activity * multiplier * phase_weights['piece_activity']
        elif phase == 'middlegame':
            position_score = self.position_evaluator.evaluate(board)
            score += position_score * phase_weights['center_control']
            for color in [chess.WHITE, chess.BLACK]:
                multiplier = 1 if color == chess.WHITE else -1
                mobility = self.piece_evaluator.evaluate_mobility(board, color)
                score += mobility * multiplier * phase_weights['piece_activity']
                activity = self.piece_evaluator.evaluate_activity(board, color)
                score += activity * multiplier * phase_weights['piece_activity']
                king_safety = self.king_evaluator.evaluate(board, color)
                score += king_safety * multiplier * phase_weights['king_safety']
                pawn_structure = self.pawn_evaluator.evaluate_structure(board, color)
                score += pawn_structure * multiplier * phase_weights['pawn_structure']
            # Apply tapering to blend with endgame evaluation if needed
            if taper_factor < 1.0:
                endgame_score = self.evaluate_phase_specific(board, 'endgame', 0.0)
                endgame_weight = EVALUATION_WEIGHTS['phase_importance']['endgame']
                score = score * taper_factor + endgame_score * (1.0 - taper_factor)
        else:  # endgame
            position_score = self.position_evaluator.evaluate(board)
            score += position_score * phase_weights['center_control']
            for color in [chess.WHITE, chess.BLACK]:
                multiplier = 1 if color == chess.WHITE else -1
                king_activity = self.king_evaluator.evaluate_king_activity(board, board.king(color), color)
                score += king_activity * multiplier * phase_weights['king_safety']
                promotion_potential = self.pawn_evaluator.evaluate_promotion_potential(board, color)
                score += promotion_potential * multiplier * phase_weights['pawn_structure']
                activity = self.piece_evaluator.evaluate_activity(board, color)
                score += activity * multiplier * phase_weights['piece_activity']
        return score

    def evaluate(self, board):
        """
        Evaluate the position based on the current game phase.
        Args:
            board (chess.Board): Current chess position
        Returns:
            float: Evaluation score
        """
        phase, taper_factor = self.get_game_phase(board)
        return self.evaluate_phase_specific(board, phase, taper_factor)
