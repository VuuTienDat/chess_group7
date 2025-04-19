"""Pawn structure evaluation functions."""

import chess
from .weights import (
    PASSED_PAWN_BONUS,
    ISOLATED_PAWN_PENALTY,
    DOUBLED_PAWN_PENALTY,
    BACKWARD_PAWN_PENALTY,
    PAWN_CHAIN_BONUS,
    PAWN_MAJORITY_BONUS,
    PASSED_PAWN_RANK_BONUS
)

class PawnEvaluator:
    def __init__(self):
        """Initialize the pawn evaluator."""
        pass

    def evaluate_structure(self, board: chess.Board, color: chess.Color) -> int:
        """Evaluate the pawn structure for a given color."""
        return evaluate_pawn_structure(board, color)

    def evaluate_promotion_potential(self, board: chess.Board, color: chess.Color) -> int:
        """Evaluate the promotion potential of pawns for a given color."""
        score = 0
        for square in board.pieces(chess.PAWN, color):
            if is_passed_pawn(board, square, color):
                rank = chess.square_rank(square)
                if color == chess.WHITE:
                    score += PASSED_PAWN_RANK_BONUS[rank]
                else:
                    score += PASSED_PAWN_RANK_BONUS[7 - rank]
        return score

def is_passed_pawn(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    """Check if a pawn is passed (no enemy pawns can stop it from promoting)."""
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    
    # Check squares in front of the pawn
    for r in range(rank + 1, 8):
        for f in [file - 1, file, file + 1]:
            if 0 <= f <= 7:
                square = chess.square(f, r)
                if board.piece_at(square) == chess.Piece(chess.PAWN, not color):
                    return False
    return True

def is_isolated_pawn(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    """Check if a pawn is isolated (no friendly pawns on adjacent files)."""
    file = chess.square_file(square)
    
    # Check adjacent files
    for f in [file - 1, file + 1]:
        if 0 <= f <= 7:
            if any(board.pieces(chess.PAWN, color) & chess.BB_FILES[f]):
                return False
    return True

def is_doubled_pawn(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    """Check if a pawn is doubled (another friendly pawn on the same file)."""
    file = chess.square_file(square)
    file_mask = chess.BB_FILES[file]
    pawns_on_file = board.pieces(chess.PAWN, color) & file_mask
    return bin(pawns_on_file).count('1') > 1

def is_backward_pawn(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    """Check if a pawn is backward (cannot be supported by friendly pawns)."""
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    
    # Check if there are friendly pawns on adjacent files that can support
    for f in [file - 1, file + 1]:
        if 0 <= f <= 7:
            for r in range(rank + 1, 8):
                square = chess.square(f, r)
                if board.piece_at(square) == chess.Piece(chess.PAWN, color):
                    return False
    return True

def is_connected_pawn(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    """Check if a pawn is connected to other friendly pawns."""
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    
    # Check diagonally adjacent squares
    for f in [file - 1, file + 1]:
        if 0 <= f <= 7:
            for r in [rank - 1, rank, rank + 1]:
                if 0 <= r <= 7:
                    target = chess.square(f, r)
                    if board.piece_at(target) == chess.Piece(chess.PAWN, color):
                        return True
    return False

def is_central_pawn(square: chess.Square) -> bool:
    """Check if a pawn is in the center (d4-e4-d5-e5)."""
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    return (file in [3, 4] and rank in [3, 4])

def evaluate_pawn_structure(board: chess.Board, color: chess.Color) -> int:
    """Evaluate the pawn structure for a given color."""
    score = 0
    pawn_files = [0] * 8  # Track pawns on each file
    
    # Iterate through all pawns of the given color
    for square in board.pieces(chess.PAWN, color):
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        pawn_files[file] += 1
        
        # Basic structure evaluation
        if is_passed_pawn(board, square, color):
            score += PASSED_PAWN_BONUS
            # Increase bonus for advanced passed pawns
            if color == chess.WHITE:
                score += rank * 10
            else:
                score += (7 - rank) * 10
                
        if is_isolated_pawn(board, square, color):
            score += ISOLATED_PAWN_PENALTY
        if is_doubled_pawn(board, square, color):
            score += DOUBLED_PAWN_PENALTY
        if is_backward_pawn(board, square, color):
            score += BACKWARD_PAWN_PENALTY
            
        # Additional evaluations
        if is_connected_pawn(board, square, color):
            score += PAWN_CHAIN_BONUS
        if is_central_pawn(square):
            score += 15  # Bonus for controlling center
            
        # Protected passed pawn bonus
        if is_passed_pawn(board, square, color):
            defenders = board.attackers(color, square)
            if defenders:
                score += 20  # Extra bonus for protected passed pawns
                
    # Evaluate pawn islands and majorities
    islands = sum(1 for i in range(7) if pawn_files[i] == 0 and pawn_files[i + 1] > 0)
    score -= islands * 10  # Penalty for each pawn island
    
    # Check pawn majority on each flank
    queenside_pawns = sum(pawn_files[0:4])
    kingside_pawns = sum(pawn_files[4:8])
    enemy_queenside = len([s for s in board.pieces(chess.PAWN, not color)
                          if chess.square_file(s) < 4])
    enemy_kingside = len([s for s in board.pieces(chess.PAWN, not color)
                         if chess.square_file(s) >= 4])
    
    if queenside_pawns > enemy_queenside:
        score += PAWN_MAJORITY_BONUS
    if kingside_pawns > enemy_kingside:
        score += PAWN_MAJORITY_BONUS
            
    return score