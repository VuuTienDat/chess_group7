"""Position evaluation functions."""

import chess
from .weights import (
    CENTER_BONUS,
    CENTER_SQUARES,
    DEVELOPMENT_BONUS
)

class PositionEvaluator:
    def __init__(self):
        """Initialize the position evaluator."""
        pass

    def evaluate(self, board: chess.Board) -> int:
        """Evaluate overall position."""
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            position_score = evaluate_position(board, color)
            score += position_score * (1 if color == chess.WHITE else -1)
        return score

    def evaluate_center_control(self, board: chess.Board) -> int:
        """Evaluate center control."""
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            center_score = evaluate_center_control(board, color)
            score += center_score * (1 if color == chess.WHITE else -1)
        return score

def evaluate_position(board: chess.Board, color: chess.Color) -> int:
    """Evaluate overall position for a given color."""
    score = 0
    
    # Determine game phase
    total_pieces = 0
    for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
        total_pieces += len(board.pieces(piece_type, chess.WHITE))
        total_pieces += len(board.pieces(piece_type, chess.BLACK))
    
    is_endgame = total_pieces <= 6
    is_opening = total_pieces >= 12 and not board.fullmove_number > 10
    
    # Opening evaluation
    if is_opening:
        # Center control is crucial in opening
        score += evaluate_center_control(board, color) * 2
        # Development is very important
        score += evaluate_development(board, color) * 2
        # Space control less important in opening
        score += evaluate_space_control(board, color) * 0.5
        
        # Penalize early queen moves
        queen_square = chess.D1 if color == chess.WHITE else chess.D8
        for square in board.pieces(chess.QUEEN, color):
            if square != queen_square and board.fullmove_number < 6:
                score -= 30
    
    # Middlegame evaluation
    elif not is_endgame:
        # Balanced evaluation in middlegame
        score += evaluate_center_control(board, color) * 1.5
        score += evaluate_development(board, color)
        score += evaluate_space_control(board, color)
        score += evaluate_piece_coordination(board, color)
        
    # Endgame evaluation
    else:
        # Center control still important but less so
        score += evaluate_center_control(board, color)
        # Space control becomes more important
        score += evaluate_space_control(board, color) * 1.5
        # Add endgame-specific evaluations
        score += evaluate_endgame_position(board, color)
    
    return score

def evaluate_center_control(board: chess.Board, color: chess.Color) -> int:
    """Evaluate center control."""
    score = 0
    
    # Check center squares
    for square in CENTER_SQUARES:
        # Count pieces attacking center
        attackers = len(list(board.attackers(color, square)))
        defenders = len(list(board.attackers(not color, square)))
        
        if attackers > defenders:
            score += CENTER_BONUS * (attackers - defenders)
            
    return score

def evaluate_development(board: chess.Board, color: chess.Color) -> int:
    """Evaluate piece development."""
    score = 0
    
    # Count developed pieces (not on starting squares)
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
            
    # Queen (developed if not on D1/D8)
    queen_square = chess.D1 if color == chess.WHITE else chess.D8
    for square in board.pieces(chess.QUEEN, color):
        if square != queen_square:
            developed_pieces += 1
            
    score += developed_pieces * DEVELOPMENT_BONUS
    
    return score

def evaluate_space_control(board: chess.Board, color: chess.Color) -> int:
    """Evaluate space control and piece placement."""
    score = 0
    enemy_color = not color
    
    # Control of the board half
    enemy_half = chess.BB_RANKS_1234 if color == chess.WHITE else chess.BB_RANKS_5678
    friendly_half = chess.BB_RANKS_5678 if color == chess.WHITE else chess.BB_RANKS_1234
    
    # Evaluate piece control
    for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        for square in board.pieces(piece_type, color):
            attacks = board.attacks(square)
            
            # Count attacks in enemy territory (weighted more)
            enemy_attacks = len(attacks & enemy_half)
            score += enemy_attacks * 3
            
            # Count attacks in own territory
            friendly_attacks = len(attacks & friendly_half)
            score += friendly_attacks
            
            # Bonus for pieces in enemy territory
            if square & enemy_half:
                score += 10
    
    return score

def evaluate_piece_coordination(board: chess.Board, color: chess.Color) -> int:
    """Evaluate how well pieces work together."""
    score = 0
    
    # Evaluate piece pairs
    for square in chess.SQUARES:
        attackers = list(board.attackers(color, square))
        if len(attackers) >= 2:
            score += 5 * (len(attackers) - 1)
    
    # Check piece protection
    for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        for square in board.pieces(piece_type, color):
            if board.is_attacked_by(color, square):
                score += 10  # Bonus for protected pieces
    
    return score

def evaluate_endgame_position(board: chess.Board, color: chess.Color) -> int:
    """Evaluate position specifically for endgame."""
    score = 0
    
    # Get king squares
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
            score += 20  # Bonus for having the opposition
    
    return score