"""
Main evaluator module that combines all evaluation aspects.
"""

import chess
from .weights import PIECE_VALUES
from .phase_evaluator import PhaseEvaluator
from .position_evaluation import PositionEvaluator

class MainEvaluator:
    def __init__(self):
        """Initialize the main evaluator with all sub-evaluators."""
        self.phase_evaluator = PhaseEvaluator()
        self.position_evaluator = PositionEvaluator()

    def get_game_phase(self, board):
        """Determine the game phase based on material and moves."""
        total_pieces = 0
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
            total_pieces += len(board.pieces(piece_type, chess.WHITE))
            total_pieces += len(board.pieces(piece_type, chess.BLACK))
        
        if total_pieces <= 6:
            return 'endgame'
        elif total_pieces >= 12 and board.fullmove_number <= 10:
            return 'opening'
        else:
            return 'middlegame'

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
            score += (white_pieces - black_pieces) * PIECE_VALUES[piece_type]
        return score

    def evaluate(self, board):
        """
        Main evaluation function that combines all aspects.
        
        Args:
            board (chess.Board): Current chess position
            
        Returns:
            float: Total evaluation score
        """
        phase = self.get_game_phase(board)
        
        # Phase-specific weights
        weights = {
            'opening': {
                'material': 1.0,
                'position': 0.8,
                'king_safety': 1.2,
                'pawn_structure': 0.6,
                'piece_activity': 1.0
            },
            'middlegame': {
                'material': 1.5,
                'position': 1.0,
                'king_safety': 1.0,
                'pawn_structure': 0.8,
                'piece_activity': 0.8
            },
            'endgame': {
                'material': 2.0,
                'position': 0.6,
                'king_safety': 0.4,
                'pawn_structure': 1.2,
                'piece_activity': 0.5
            }
        }[phase]
        
        # Calculate component scores
        total_score = 0
        
        # Material evaluation
        material_score = self.evaluate_material(board)
        total_score += material_score * weights['material']
        
        # Position evaluation
        position_score = self.position_evaluator.evaluate(board)
        total_score += position_score * weights['position']
        
        # Evaluate each color's pieces
        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1
            
            # King safety evaluation
            king_score = self.phase_evaluator.king_evaluator.evaluate(board, color)
            total_score += king_score * weights['king_safety'] * multiplier
            
            # Pawn structure evaluation
            pawn_score = self.phase_evaluator.pawn_evaluator.evaluate_structure(board, color)
            if phase == 'endgame':
                pawn_score += self.phase_evaluator.pawn_evaluator.evaluate_promotion_potential(board, color)
            total_score += pawn_score * weights['pawn_structure'] * multiplier
            
            # Piece activity
            piece_score = self.position_evaluator.evaluate_space_control(board, color)
            if phase == 'endgame':
                piece_score += self.position_evaluator.evaluate_endgame_position(board, color)
            total_score += piece_score * weights['piece_activity'] * multiplier
        
        # Normalize score to centipawns and ensure reasonable bounds
        total_score = total_score / 100.0
        return max(min(total_score, 1000), -1000)  # Limit extreme evaluations