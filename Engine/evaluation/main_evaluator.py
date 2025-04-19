"""
Main evaluator module that combines all evaluation aspects.
"""

import chess
from .weights import PIECE_VALUES
from .phase_evaluator import PhaseEvaluator
from .position_evaluation import PositionEvaluator
from .king_evaluation import KingEvaluator
from .pawn_evaluation import PawnEvaluator
from .piece_evaluation import PieceEvaluator

# Piece value constants
PIECE_TYPE_VALUES = {
    chess.PAWN: PIECE_VALUES['P'],
    chess.KNIGHT: PIECE_VALUES['N'],
    chess.BISHOP: PIECE_VALUES['B'],
    chess.ROOK: PIECE_VALUES['R'],
    chess.QUEEN: PIECE_VALUES['Q'],
    chess.KING: PIECE_VALUES['K']
}

class MainEvaluator:
    def __init__(self):
        """Initialize the main evaluator with all sub-evaluators."""
        self.position_evaluator = PositionEvaluator()
        self.king_evaluator = KingEvaluator()
        self.pawn_evaluator = PawnEvaluator()
        self.piece_evaluator = PieceEvaluator()

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
                'material': 100,
                'position': 80,
                'king_safety': 120,
                'pawn_structure': 60,
                'piece_activity': 100,
                'mobility': 90
            },
            'middlegame': {
                'material': 150,
                'position': 100,
                'king_safety': 100,
                'pawn_structure': 80,
                'piece_activity': 80,
                'mobility': 100
            },
            'endgame': {
                'material': 200,
                'position': 60,
                'king_safety': 40,
                'pawn_structure': 120,
                'piece_activity': 50,
                'mobility': 120
            }
        }[phase]
        
        total_score = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1
            
            # Material evaluation
            material_score = 0
            for piece_type in chess.PIECE_TYPES:
                material_score += len(board.pieces(piece_type, color)) * PIECE_TYPE_VALUES[piece_type]
            total_score += material_score * weights['material'] / 100.0 * multiplier
            
            # Position and piece activity evaluation
            position_score = self.position_evaluator.evaluate_center_control(board) * multiplier
            position_score += self.position_evaluator.evaluate_space_control(board, color)
            total_score += position_score * weights['position'] / 100.0 * multiplier
            
            # King safety evaluation
            king_score = self.king_evaluator.evaluate(board, color)
            if phase == 'endgame':
                king_square = board.king(color)
                if king_square is not None:
                    king_score += self.king_evaluator.evaluate_king_activity(board, king_square, color)
            total_score += king_score * weights['king_safety'] / 100.0 * multiplier
            
            # Pawn structure evaluation
            pawn_score = self.pawn_evaluator.evaluate_structure(board, color)
            if phase == 'endgame':
                pawn_score += self.pawn_evaluator.evaluate_promotion_potential(board, color) * 2
            total_score += pawn_score * weights['pawn_structure'] / 100.0 * multiplier
            
            # Piece activity and mobility
            activity_score = self.piece_evaluator.evaluate_activity(board, color)
            mobility_score = self.piece_evaluator.evaluate_mobility(board, color)
            total_score += activity_score * weights['piece_activity'] / 100.0 * multiplier
            total_score += mobility_score * weights['mobility'] / 100.0 * multiplier
            
            # Additional endgame evaluation
            if phase == 'endgame':
                if board.is_check():
                    total_score += 50 * multiplier  # Bonus for giving check in endgame
                passed_pawns = sum(1 for square in board.pieces(chess.PAWN, color)
                                if self.pawn_evaluator.is_passed_pawn(board, square, color))
                total_score += passed_pawns * 30 * multiplier  # Bonus for passed pawns
        
        # Normalize and bound the score
        return max(min(total_score, 1000), -1000)