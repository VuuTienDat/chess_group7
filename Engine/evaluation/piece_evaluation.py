"""Piece activity and mobility evaluation functions."""

import chess
from functools import lru_cache
from .weights import (
    PIECE_ACTIVITY_WEIGHT,
    MOBILITY_WEIGHT,
    CENTER_BONUS,
    CENTER_SQUARES,
    OUTPOST_BONUS,
    OPEN_FILE_BONUS,
    SEMI_OPEN_FILE_BONUS,
    PIN_BONUS,
    FORK_BONUS,
    DISCOVERED_ATTACK_BONUS,
    XRAY_BONUS,
    PIECE_COORDINATION_BONUS,
    DEVELOPMENT_BONUS
)

class PieceEvaluator:
    def __init__(self):
        """Initialize the piece evaluator."""
        pass

    def evaluate_activity(self, board: chess.Board, color: chess.Color) -> int:
        """Evaluate piece activity for a given color."""
        return evaluate_piece_activity(board, color)

    def evaluate_mobility(self, board: chess.Board, color: chess.Color) -> int:
        """Evaluate piece mobility for a given color."""
        score = 0
        for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            for square in board.pieces(piece_type, color):
                attacks = get_piece_attacks(square, piece_type, color)
                # Count all legal moves, not just attacks
                mobility = len(attacks & ~board._board.occupied_co[color])
                if piece_type == chess.KNIGHT:
                    score += mobility * 3
                elif piece_type == chess.BISHOP:
                    score += mobility * 2
                elif piece_type == chess.ROOK:
                    score += mobility * 1
                elif piece_type == chess.QUEEN:
                    score += mobility * 1
        return score

    def evaluate_development(self, board: chess.Board, color: chess.Color) -> int:
        """Evaluate piece development for a given color."""
        return evaluate_development(board, color)

# Cache for piece attacks
@lru_cache(maxsize=64)
def get_piece_attacks(square: chess.Square, piece_type: chess.PieceType, color: chess.Color) -> chess.SquareSet:
    """Get cached piece attacks."""
    board = chess.Board()
    board.set_piece_at(square, chess.Piece(piece_type, color))
    return board.attacks(square)

def evaluate_piece_activity(board: chess.Board, color: chess.Color) -> int:
    """Evaluate piece activity for a given color."""
    score = 0
    
    # Cache piece positions
    piece_positions = {
        chess.KNIGHT: list(board.pieces(chess.KNIGHT, color)),
        chess.BISHOP: list(board.pieces(chess.BISHOP, color)),
        chess.ROOK: list(board.pieces(chess.ROOK, color)),
        chess.QUEEN: list(board.pieces(chess.QUEEN, color))
    }
    
    # Evaluate each piece type
    for piece_type, squares in piece_positions.items():
        for square in squares:
            # Get cached attacks
            attacks = get_piece_attacks(square, piece_type, color)
            
            # Calculate mobility using cached attacks
            mobility = len(attacks & board._board.occupied_co[not color])
            score += mobility * MOBILITY_WEIGHT
            
            # Center control bonus
            if square in CENTER_SQUARES:
                score += CENTER_BONUS
                
            # Piece-specific evaluation
            if piece_type == chess.KNIGHT:
                score += evaluate_knight_position(board, square, color)
            elif piece_type == chess.BISHOP:
                score += evaluate_bishop_position(board, square, color)
            elif piece_type == chess.ROOK:
                score += evaluate_rook_position(board, square, color)
            elif piece_type == chess.QUEEN:
                score += evaluate_queen_position(board, square, color)
                
    # Evaluate piece coordination
    score += evaluate_piece_coordination(board, color)
    
    # Evaluate tactical features
    score += evaluate_tactical_features(board, color)
    
    return score * PIECE_ACTIVITY_WEIGHT

def evaluate_knight_position(board: chess.Board, square: chess.Square, color: chess.Color) -> int:
    """Evaluate knight position."""
    score = 0
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    
    # Knights are better in the center
    if file in [2, 3, 4, 5] and rank in [2, 3, 4, 5]:
        score += 20
        
    # Knights are worse on the edge
    if file in [0, 7] or rank in [0, 7]:
        score -= 10
        
    # Check for outpost
    if is_knight_outpost(board, square, color):
        score += OUTPOST_BONUS
        
    return score

def is_knight_outpost(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    """Check if a knight is on an outpost."""
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    
    # Check if square is protected by own pawn
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

def evaluate_bishop_position(board: chess.Board, square: chess.Square, color: chess.Color) -> int:
    """Evaluate bishop position."""
    score = 0
    
    # Bishop pair bonus
    if len(board.pieces(chess.BISHOP, color)) == 2:
        score += 30
        
    # Open diagonals are better
    attacks = get_piece_attacks(square, chess.BISHOP, color)
    mobility = len(attacks & board._board.occupied_co[not color])
    score += mobility * 5
    
    # Check for bishop outpost
    if is_bishop_outpost(board, square, color):
        score += OUTPOST_BONUS
        
    return score

def is_bishop_outpost(board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
    """Check if a bishop is on an outpost."""
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

def evaluate_rook_position(board: chess.Board, square: chess.Square, color: chess.Color) -> int:
    """Evaluate rook position."""
    score = 0
    file = chess.square_file(square)
    
    # Check file status using bitboard operations
    file_mask = chess.BB_FILES[file]
    white_pawns = board.pieces(chess.PAWN, chess.WHITE) & file_mask
    black_pawns = board.pieces(chess.PAWN, chess.BLACK) & file_mask
    
    if not (white_pawns | black_pawns):
        score += 10  # Reduced from OPEN_FILE_BONUS
    elif not (white_pawns if color == chess.WHITE else black_pawns):
        score += 5   # Reduced from SEMI_OPEN_FILE_BONUS
        
    # Rooks are better on 7th rank (but not as much as before)
    if (color == chess.WHITE and chess.square_rank(square) == 6) or \
       (color == chess.BLACK and chess.square_rank(square) == 1):
        score += 5   # Reduced from 15
        
    # Consider material at risk
    attacks = get_piece_attacks(square, chess.ROOK, color)
    defenders = board.attackers(not color, square)
    if defenders and not board.attackers(color, square):
        score -= 20  # Penalty for being under attack without defense
        
    return score

def evaluate_queen_position(board: chess.Board, square: chess.Square, color: chess.Color) -> int:
    """Evaluate queen position."""
    score = 0
    
    # Queen mobility using cached attacks
    attacks = get_piece_attacks(square, chess.QUEEN, color)
    mobility = len(attacks & board._board.occupied_co[not color])
    score += mobility * 2
    
    # Queen is better in the center
    if square in CENTER_SQUARES:
        score += 10
        
    return score

def evaluate_piece_coordination(board: chess.Board, color: chess.Color) -> int:
    """Evaluate how well pieces work together."""
    score = 0
    
    # Use bitboard operations for faster attack counting
    for square in chess.SQUARES:
        attackers = bin(board.attackers(color, square)).count('1')
        if attackers >= 2:
            score += PIECE_COORDINATION_BONUS * (attackers - 1)
            
    return score

def evaluate_tactical_features(board: chess.Board, color: chess.Color) -> int:
    """Evaluate tactical features like pins, forks, etc."""
    score = 0
    
    # Cache enemy pieces
    enemy_pieces = {
        chess.QUEEN: list(board.pieces(chess.QUEEN, not color)),
        chess.ROOK: list(board.pieces(chess.ROOK, not color))
    }
    
    # Check for pins using bitboard operations
    for queen_square in board.pieces(chess.QUEEN, color):
        queen_attacks = get_piece_attacks(queen_square, chess.QUEEN, color)
        for piece_type in [chess.QUEEN, chess.ROOK]:
            for square in enemy_pieces[piece_type]:
                if square in queen_attacks and is_pinned(board, square, queen_square, color):
                    score += PIN_BONUS
                    
    # Check for potential forks
    for piece_type in [chess.KNIGHT, chess.QUEEN]:
        for square in board.pieces(piece_type, color):
            attacks = get_piece_attacks(square, piece_type, color)
            valuable_targets = 0
            for target in attacks:
                piece = board.piece_at(target)
                if piece and piece.color != color:
                    if piece.piece_type in [chess.QUEEN, chess.ROOK]:
                        valuable_targets += 1
            if valuable_targets >= 2:
                score += FORK_BONUS
                
    return score

def is_pinned(board: chess.Board, square: chess.Square, pinner: chess.Square, color: chess.Color) -> bool:
    """Check if a piece is pinned to the king."""
    piece = board.piece_at(square)
    if not piece or piece.color == color:
        return False
        
    # Use bitboard operations for faster pin detection
    king_square = board.king(color)
    if not king_square:
        return False
        
    # Check if piece is on the same line as king and pinner
    if (chess.square_file(square) == chess.square_file(king_square) == chess.square_file(pinner) or
        chess.square_rank(square) == chess.square_rank(king_square) == chess.square_rank(pinner) or
        (chess.square_file(square) - chess.square_file(king_square)) == 
        (chess.square_rank(square) - chess.square_rank(king_square)) ==
        (chess.square_file(pinner) - chess.square_file(king_square))):
        return True
        
    return False 