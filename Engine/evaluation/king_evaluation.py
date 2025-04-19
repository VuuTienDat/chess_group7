"""
Module for evaluating king safety with advanced features.
"""

import chess
from .weights import KING_SAFETY_WEIGHTS

class KingEvaluator:
    def __init__(self):
        """Initialize the king safety evaluator."""
        self.weights = {
            'pawn_shield': 1.0,
            'piece_shield': 0.8,
            'open_files': -1.2,
            'semi_open_files': -0.6,
            'attacking_pieces': -1.0,
            'king_zone_control': 0.7,
            'king_mobility': 0.5,
            'enemy_piece_proximity': -0.4,
            'attack_paths': -0.9,
            'pawn_storm': -1.1,
            'king_activity': 0.6
        }

    def get_king_zone(self, king_square):
        """
        Get the squares in the king's safety zone (3x3 area around king).
        
        Args:
            king_square (int): Square index of the king
            
        Returns:
            list: List of squares in the king's zone
        """
        file = chess.square_file(king_square)
        rank = chess.square_rank(king_square)
        
        zone = []
        for file_offset in [-1, 0, 1]:
            for rank_offset in [-1, 0, 1]:
                target_file = file + file_offset
                target_rank = rank + rank_offset
                if 0 <= target_file <= 7 and 0 <= target_rank <= 7:
                    zone.append(chess.square(target_file, target_rank))
        return zone

    def get_extended_king_zone(self, king_square):
        """
        Get the extended king zone (5x5 area around king) for evaluating potential attacks.
        
        Args:
            king_square (int): Square index of the king
            
        Returns:
            list: List of squares in the extended king zone
        """
        file = chess.square_file(king_square)
        rank = chess.square_rank(king_square)
        
        zone = []
        for file_offset in [-2, -1, 0, 1, 2]:
            for rank_offset in [-2, -1, 0, 1, 2]:
                target_file = file + file_offset
                target_rank = rank + rank_offset
                if 0 <= target_file <= 7 and 0 <= target_rank <= 7:
                    zone.append(chess.square(target_file, target_rank))
        return zone

    def evaluate_pawn_shield(self, board, king_square, color):
        """
        Evaluate the pawn shield around the king.
        
        Args:
            board (chess.Board): Current chess position
            king_square (int): Square index of the king
            color (chess.Color): Color of the king
            
        Returns:
            float: Pawn shield score
        """
        score = 0
        file = chess.square_file(king_square)
        rank = chess.square_rank(king_square)
        
        # Check pawns in front of king (2 ranks)
        for rank_offset in [1, 2]:
            for file_offset in [-1, 0, 1]:
                target_file = file + file_offset
                target_rank = rank + (rank_offset if color == chess.WHITE else -rank_offset)
                if 0 <= target_file <= 7 and 0 <= target_rank <= 7:
                    target = chess.square(target_file, target_rank)
                    piece = board.piece_at(target)
                    if piece and piece.piece_type == chess.PAWN and piece.color == color:
                        # Pawns closer to king are more valuable
                        score += self.weights['pawn_shield'] * (2 - rank_offset)
        
        return score

    def evaluate_enemy_piece_proximity(self, board, king_square, color):
        """
        Evaluate the proximity of enemy pieces to the king.
        
        Args:
            board (chess.Board): Current chess position
            king_square (int): Square index of the king
            color (chess.Color): Color of the king
            
        Returns:
            float: Enemy proximity score
        """
        score = 0
        enemy_color = not color
        extended_zone = self.get_extended_king_zone(king_square)
        
        # Check enemy pieces in extended zone
        for square in extended_zone:
            piece = board.piece_at(square)
            if piece and piece.color == enemy_color:
                # Calculate Manhattan distance to king
                distance = abs(chess.square_file(square) - chess.square_file(king_square)) + \
                          abs(chess.square_rank(square) - chess.square_rank(king_square))
                # Closer pieces are more dangerous
                score += self.weights['enemy_piece_proximity'] * (5 - distance)
        
        return score

    def evaluate_attack_paths(self, board, king_square, color):
        """
        Evaluate potential attack paths to the king.
        
        Args:
            board (chess.Board): Current chess position
            king_square (int): Square index of the king
            color (chess.Color): Color of the king
            
        Returns:
            float: Attack paths score
        """
        score = 0
        enemy_color = not color
        
        # Check for open files and diagonals
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP]:
            for attacker in board.pieces(piece_type, enemy_color):
                # Check if piece can attack king's zone
                if board.is_attacked_by(piece_type, king_square):
                    # Count squares between attacker and king
                    path_length = len(list(board.attacks(attacker)))
                    score += self.weights['attack_paths'] * (8 - path_length)
        
        return score

    def evaluate_pawn_storm(self, board, king_square, color):
        """
        Evaluate potential pawn storm against the king.
        
        Args:
            board (chess.Board): Current chess position
            king_square (int): Square index of the king
            color (chess.Color): Color of the king
            
        Returns:
            float: Pawn storm score
        """
        score = 0
        enemy_color = not color
        file = chess.square_file(king_square)
        
        # Check enemy pawns on adjacent files
        for file_offset in [-1, 0, 1]:
            target_file = file + file_offset
            if 0 <= target_file <= 7:
                # Find closest enemy pawn on this file
                closest_pawn = None
                min_distance = float('inf')
                
                for rank in range(8):
                    square = chess.square(target_file, rank)
                    piece = board.piece_at(square)
                    if piece and piece.piece_type == chess.PAWN and piece.color == enemy_color:
                        distance = abs(rank - chess.square_rank(king_square))
                        if distance < min_distance:
                            min_distance = distance
                            closest_pawn = square
                
                if closest_pawn:
                    # Pawns closer to king are more dangerous
                    score += self.weights['pawn_storm'] * (7 - min_distance)
        
        return score

    def evaluate_king_activity(self, board, king_square, color):
        """
        Evaluate king's activity and safety of its moves.
        
        Args:
            board (chess.Board): Current chess position
            king_square (int): Square index of the king
            color (chess.Color): Color of the king
            
        Returns:
            float: King activity score
        """
        if king_square is None:
            return 0
            
        score = 0
        
        # Get legal king moves
        king_moves = [move for move in board.legal_moves
                     if move.from_square == king_square]
        
        # Evaluate each possible king move
        for move in king_moves:
            target = move.to_square
            # Check if target square is safe
            if not board.is_attacked_by(not color, target):
                # Calculate centralization of target square
                file = chess.square_file(target)
                rank = chess.square_rank(target)
                centralization = abs(3.5 - file) + abs(3.5 - rank)
                score += self.weights['king_activity'] * (8 - centralization)
        
        # Additional endgame evaluation
        if len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK)) == 0:
            # King centralization becomes more important
            king_file = chess.square_file(king_square)
            king_rank = chess.square_rank(king_square)
            centralization = abs(3.5 - king_file) + abs(3.5 - king_rank)
            score += (14 - centralization) * 3
            
            # Distance to enemy king
            enemy_king = board.king(not color)
            if enemy_king:
                file_distance = abs(chess.square_file(king_square) - chess.square_file(enemy_king))
                rank_distance = abs(chess.square_rank(king_square) - chess.square_rank(enemy_king))
                manhattan_distance = file_distance + rank_distance
                if manhattan_distance <= 2:
                    score += 20  # Bonus for keeping close to enemy king
        
        return score

    def evaluate(self, board, color):
        """
        Main evaluation function for king safety.
        
        Args:
            board (chess.Board): Current chess position
            color (chess.Color): Color to evaluate for
            
        Returns:
            float: Total king safety score
        """
        king_square = board.king(color)
        if not king_square:
            return 0
        
        # Determine game phase based on material
        total_material = 0
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
            total_material += len(board.pieces(piece_type, chess.WHITE))
            total_material += len(board.pieces(piece_type, chess.BLACK))
        
        is_endgame = total_material <= 6  # Less than 3 major pieces per side
        
        score = 0
        if is_endgame:
            # In endgame, prioritize king activity
            score += self.evaluate_king_activity(board, king_square, color) * 3
            score += self.evaluate_enemy_piece_proximity(board, king_square, color) * 0.5
        else:
            # In opening/middlegame, prioritize king safety
            score += self.evaluate_pawn_shield(board, king_square, color) * 2
            score += self.evaluate_enemy_piece_proximity(board, king_square, color) * 1.5
            score += self.evaluate_attack_paths(board, king_square, color) * 1.5
            score += self.evaluate_pawn_storm(board, king_square, color)
            
            # Check castling rights
            if board.has_castling_rights(color):
                score += 30  # Bonus for keeping castling rights
            
            # Penalize exposed king in center
            if chess.square_file(king_square) in [2, 3, 4, 5] and \
               chess.square_rank(king_square) in [2, 3, 4, 5]:
                score -= 50  # Heavy penalty for exposed king in center
        
        return score