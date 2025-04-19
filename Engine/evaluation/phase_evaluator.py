"""
Module for evaluating chess positions based on game phases.
Implements different evaluation strategies for opening, middlegame, and endgame.
"""

import chess
from .king_evaluation import KingEvaluator
from .pawn_evaluation import PawnEvaluator
from .piece_evaluation import PieceEvaluator
from .position_evaluation import PositionEvaluator

class PhaseEvaluator:
    def __init__(self):
        """Initialize the phase evaluator with weights for each game phase."""
        self.opening_weights = {
            'center_control': 1.5,
            'development': 1.2,
            'king_safety': 1.3,
            'pawn_structure': 0.8,
            'mobility': 0.7,
            'piece_activity': 0.6
        }
        
        self.middlegame_weights = {
            'center_control': 1.0,
            'development': 0.8,
            'king_safety': 1.5,
            'pawn_structure': 1.2,
            'mobility': 1.3,
            'piece_activity': 1.4,
            'position': 1.1
        }
        
        self.endgame_weights = {
            'king_activity': 1.5,
            'pawn_promotion': 2.0,
            'piece_activity': 1.2,
            'material': 1.0,
            'position': 0.9
        }
        
        # Initialize all evaluators
        self.king_evaluator = KingEvaluator()
        self.pawn_evaluator = PawnEvaluator()
        self.piece_evaluator = PieceEvaluator()
        self.position_evaluator = PositionEvaluator()

    def get_game_phase(self, board):
        """
        Determine the current game phase based on material and piece count.
        
        Args:
            board (chess.Board): Current chess position
            
        Returns:
            str: Game phase ('opening', 'middlegame', or 'endgame')
        """
        # Count major pieces (queens and rooks)
        major_pieces = len(board.pieces(chess.QUEEN, chess.WHITE)) + \
                      len(board.pieces(chess.QUEEN, chess.BLACK)) + \
                      len(board.pieces(chess.ROOK, chess.WHITE)) + \
                      len(board.pieces(chess.ROOK, chess.BLACK))
        
        # Count minor pieces (knights and bishops)
        minor_pieces = len(board.pieces(chess.KNIGHT, chess.WHITE)) + \
                      len(board.pieces(chess.KNIGHT, chess.BLACK)) + \
                      len(board.pieces(chess.BISHOP, chess.WHITE)) + \
                      len(board.pieces(chess.BISHOP, chess.BLACK))
        
        # Opening: More than 4 major pieces and 6 minor pieces
        if major_pieces > 4 and minor_pieces > 6:
            return 'opening'
        # Endgame: Less than 2 major pieces and 3 minor pieces
        elif major_pieces < 2 and minor_pieces < 3:
            return 'endgame'
        # Middlegame: Everything else
        else:
            return 'middlegame'

    def evaluate_opening(self, board):
        """
        Evaluate position in the opening phase.
        
        Args:
            board (chess.Board): Current chess position
            
        Returns:
            float: Evaluation score
        """
        score = 0
        
        # Center control using position evaluator
        center_score = self.position_evaluator.evaluate_center_control(board)
        score += center_score * self.opening_weights['center_control']
        
        # Development using piece evaluator
        for color in [chess.WHITE, chess.BLACK]:
            development = self.piece_evaluator.evaluate_development(board, color)
            score += development * (1 if color == chess.WHITE else -1) * \
                    self.opening_weights['development']
        
        # King safety using king evaluator
        for color in [chess.WHITE, chess.BLACK]:
            king_safety = self.king_evaluator.evaluate(board, color)
            score += king_safety * (1 if color == chess.WHITE else -1) * \
                    self.opening_weights['king_safety']
        
        # Pawn structure using pawn evaluator
        for color in [chess.WHITE, chess.BLACK]:
            pawn_structure = self.pawn_evaluator.evaluate_structure(board, color)
            score += pawn_structure * (1 if color == chess.WHITE else -1) * \
                    self.opening_weights['pawn_structure']
        
        # Piece activity using piece evaluator
        for color in [chess.WHITE, chess.BLACK]:
            activity = self.piece_evaluator.evaluate_activity(board, color)
            score += activity * (1 if color == chess.WHITE else -1) * \
                    self.opening_weights['piece_activity']
        
        return score

    def evaluate_middlegame(self, board):
        """
        Evaluate position in the middlegame phase.
        
        Args:
            board (chess.Board): Current chess position
            
        Returns:
            float: Evaluation score
        """
        score = 0
        
        # Position evaluation
        position_score = self.position_evaluator.evaluate(board)
        score += position_score * self.middlegame_weights['position']
        
        # Piece activity and mobility
        for color in [chess.WHITE, chess.BLACK]:
            # Mobility
            mobility = self.piece_evaluator.evaluate_mobility(board, color)
            score += mobility * (1 if color == chess.WHITE else -1) * \
                    self.middlegame_weights['mobility']
            
            # Piece activity
            activity = self.piece_evaluator.evaluate_activity(board, color)
            score += activity * (1 if color == chess.WHITE else -1) * \
                    self.middlegame_weights['piece_activity']
        
        # King safety using king evaluator
        for color in [chess.WHITE, chess.BLACK]:
            king_safety = self.king_evaluator.evaluate(board, color)
            score += king_safety * (1 if color == chess.WHITE else -1) * \
                    self.middlegame_weights['king_safety']
        
        # Pawn structure using pawn evaluator
        for color in [chess.WHITE, chess.BLACK]:
            pawn_structure = self.pawn_evaluator.evaluate_structure(board, color)
            score += pawn_structure * (1 if color == chess.WHITE else -1) * \
                    self.middlegame_weights['pawn_structure']
        
        return score

    def evaluate_endgame(self, board):
        """
        Evaluate position in the endgame phase.
        
        Args:
            board (chess.Board): Current chess position
            
        Returns:
            float: Evaluation score
        """
        score = 0
        
        # King activity using king evaluator
        for color in [chess.WHITE, chess.BLACK]:
            king_activity = self.king_evaluator.evaluate_king_activity(board, 
                                                                    board.king(color), 
                                                                    color)
            score += king_activity * (1 if color == chess.WHITE else -1) * \
                    self.endgame_weights['king_activity']
        
        # Pawn promotion potential using pawn evaluator
        for color in [chess.WHITE, chess.BLACK]:
            promotion_potential = self.pawn_evaluator.evaluate_promotion_potential(board, color)
            score += promotion_potential * (1 if color == chess.WHITE else -1) * \
                    self.endgame_weights['pawn_promotion']
        
        # Piece activity using piece evaluator
        for color in [chess.WHITE, chess.BLACK]:
            activity = self.piece_evaluator.evaluate_activity(board, color)
            score += activity * (1 if color == chess.WHITE else -1) * \
                    self.endgame_weights['piece_activity']
        
        # Position evaluation
        position_score = self.position_evaluator.evaluate(board)
        score += position_score * self.endgame_weights['position']
        
        return score

    def evaluate(self, board):
        """
        Evaluate the position based on the current game phase.
        
        Args:
            board (chess.Board): Current chess position
            
        Returns:
            float: Evaluation score
        """
        phase = self.get_game_phase(board)
        
        if phase == 'opening':
            return self.evaluate_opening(board)
        elif phase == 'middlegame':
            return self.evaluate_middlegame(board)
        else:  # endgame
            return self.evaluate_endgame(board) 