"""
Module for evaluating king safety with advanced features.
This module evaluates king safety and activity with phase-specific weights for a chess engine.
"""

import chess
from .weights import EVALUATION_WEIGHTS, get_weight

class KingEvaluator:
    def __init__(self):
        """Initialize the king safety evaluator."""
        pass

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
            taper_factor = (phase_value - 6) / 12.0  # Linear interpolation
            return 'middlegame', taper_factor

    def get_king_zones(self, king_square):
        """
        Get both the standard and extended zones around the king.
        Args:
            king_square (int): Square index of the king
        Returns:
            tuple: (list of standard zone squares, list of extended zone squares)
        """
        file = chess.square_file(king_square)
        rank = chess.square_rank(king_square)
        standard_zone = []
        extended_zone = []
        for file_offset in range(-2, 3):
            for rank_offset in range(-2, 3):
                target_file = file + file_offset
                target_rank = rank + rank_offset
                if 0 <= target_file <= 7 and 0 <= target_rank <= 7:
                    target_square = chess.square(target_file, target_rank)
                    extended_zone.append(target_square)
                    if abs(file_offset) <= 1 and abs(rank_offset) <= 1:
                        standard_zone.append(target_square)
        return standard_zone, extended_zone

    def evaluate_pawn_shield(self, board, king_square, color, standard_zone, phase):
        """
        Evaluate the pawn shield around the king.
        Args:
            board (chess.Board): Current chess position
            king_square (int): Square index of the king
            color (chess.Color): Color of the king
            standard_zone (list): List of squares in the king's standard zone
            phase (str): Current game phase
        Returns:
            float: Pawn shield score
        """
        score = 0.0
        file = chess.square_file(king_square)
        rank = chess.square_rank(king_square)
        rank_direction = 1 if color == chess.WHITE else -1
        pawn_shield_weight = get_weight('king_safety', 'pawn_shield', phase)
        for rank_offset in [1, 2]:
            for file_offset in [-1, 0, 1]:
                target_file = file + file_offset
                target_rank = rank + (rank_offset * rank_direction)
                if 0 <= target_file <= 7 and 0 <= target_rank <= 7:
                    target = chess.square(target_file, target_rank)
                    piece = board.piece_at(target)
                    if piece and piece.piece_type == chess.PAWN and piece.color == color:
                        score += pawn_shield_weight * (2 - rank_offset)
        return score

    def evaluate_enemy_piece_proximity(self, board, king_square, color, extended_zone, phase):
        """
        Evaluate the proximity of enemy pieces to the king.
        Args:
            board (chess.Board): Current chess position
            king_square (int): Square index of the king
            color (chess.Color): Color of the king
            extended_zone (list): List of squares in the extended king zone
            phase (str): Current game phase
        Returns:
            float: Enemy proximity score
        """
        score = 0.0
        enemy_color = not color
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        proximity_weight = get_weight('king_safety', 'attack_weight', phase)
        for square in extended_zone:
            piece = board.piece_at(square)
            if piece and piece.color == enemy_color:
                distance = abs(chess.square_file(square) - king_file) + abs(chess.square_rank(square) - king_rank)
                score += proximity_weight * (5 - distance) * 0.1
        return score

    def evaluate_attack_paths(self, board, king_square, color, extended_zone, phase):
        """
        Evaluate potential attack paths to the king using a simplified heuristic.
        Args:
            board (chess.Board): Current chess position
            king_square (int): Square index of the king
            color (chess.Color): Color of the king
            extended_zone (list): List of squares in the extended king zone
            phase (str): Current game phase
        Returns:
            float: Attack paths score
        """
        score = 0.0
        enemy_color = not color
        attack_weight = get_weight('king_safety', 'attack_weight', phase)
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP]:
            for attacker in board.pieces(piece_type, enemy_color):
                if attacker in extended_zone:
                    distance = abs(chess.square_file(attacker) - chess.square_file(king_square)) + \
                               abs(chess.square_rank(attacker) - chess.square_rank(king_square))
                    score += attack_weight * (8 - distance) * 0.05
        return score

    def evaluate_pawn_storm(self, board, king_square, color, phase):
        """
        Evaluate potential pawn storm against the king.
        Args:
            board (chess.Board): Current chess position
            king_square (int): Square index of the king
            color (chess.Color): Color of the king
            phase (str): Current game phase
        Returns:
            float: Pawn storm score
        """
        score = 0.0
        enemy_color = not color
        file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        storm_weight = get_weight('king_safety', 'attack_weight', phase) * 0.1
        for file_offset in [-1, 0, 1]:
            target_file = file + file_offset
            if 0 <= target_file <= 7:
                min_distance = float('inf')
                for rank in range(8):
                    square = chess.square(target_file, rank)
                    piece = board.piece_at(square)
                    if piece and piece.piece_type == chess.PAWN and piece.color == enemy_color:
                        distance = abs(rank - king_rank)
                        if distance < min_distance:
                            min_distance = distance
                if min_distance != float('inf'):
                    score += storm_weight * (7 - min_distance)
        return score

    def evaluate_king_activity(self, board, king_square, color, phase):
        """
        Evaluate king's activity and safety of its moves.
        Args:
            board (chess.Board): Current chess position
            king_square (int): Square index of the king
            color (chess.Color): Color of the king
            phase (str): Current game phase
        Returns:
            float: King activity score
        """
        score = 0.0
        king_moves = [move for move in board.legal_moves if move.from_square == king_square]
        enemy_color = not color
        activity_weight = get_weight('king_safety', 'king_activity', phase)
        for move in king_moves:
            target = move.to_square
            if not board.is_attacked_by(enemy_color, target):
                file = chess.square_file(target)
                rank = chess.square_rank(target)
                centralization = abs(3.5 - file) + abs(3.5 - rank)
                score += activity_weight * (8 - centralization) * 0.5
        if phase == 'endgame':
            king_file = chess.square_file(king_square)
            king_rank = chess.square_rank(king_square)
            centralization = abs(3.5 - king_file) + abs(3.5 - king_rank)
            score += (14 - centralization) * activity_weight
            enemy_king = board.king(enemy_color)
            if enemy_king:
                file_distance = abs(king_file - chess.square_file(enemy_king))
                rank_distance = abs(king_rank - chess.square_rank(enemy_king))
                manhattan_distance = file_distance + rank_distance
                if manhattan_distance <= 2:
                    score += activity_weight * 2
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
            return 0.0

        # Compute zones once and reuse
        standard_zone, extended_zone = self.get_king_zones(king_square)
        phase, taper_factor = self._get_game_phase(board)

        score = 0.0
        if phase == 'endgame' or taper_factor < 0.5:
            score += self.evaluate_king_activity(board, king_square, color, phase) * 3
            score += self.evaluate_enemy_piece_proximity(board, king_square, color, extended_zone, phase) * 0.5
        else:
            score += self.evaluate_pawn_shield(board, king_square, color, standard_zone, phase) * 2
            score += self.evaluate_enemy_piece_proximity(board, king_square, color, extended_zone, phase) * 1.5
            score += self.evaluate_attack_paths(board, king_square, color, extended_zone, phase) * 1.5
            score += self.evaluate_pawn_storm(board, king_square, color, phase)
            if board.has_castling_rights(color):
                score += get_weight('king_safety', 'castling', phase)
            if chess.square_file(king_square) in [2, 3, 4, 5] and chess.square_rank(king_square) in [2, 3, 4, 5]:
                score += get_weight('king_safety', 'king_center', phase)

        # Apply overall king safety weight with tapering if needed
        safety_weight = get_weight('phase_importance', 'king_safety', phase)
        if phase == 'middlegame' and taper_factor < 1.0:
            endgame_weight = get_weight('phase_importance', 'king_safety', 'endgame')
            safety_weight = safety_weight * taper_factor + endgame_weight * (1.0 - taper_factor)
        return score * safety_weight
