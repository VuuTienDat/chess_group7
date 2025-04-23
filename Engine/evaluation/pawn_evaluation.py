"""
Pawn structure evaluation functions.
This module evaluates pawn structures with phase-specific weights for a chess engine.
"""

import chess
from .weights import EVALUATION_WEIGHTS, get_weight

class PawnEvaluator:
    def __init__(self, max_hash_size=10000):
        """Initialize the pawn evaluator with a hash table for caching."""
        self.pawn_hash_table = {}
        self.hash_hits = 0
        self.hash_misses = 0
        self.max_hash_size = max_hash_size

    def _compute_pawn_key(self, board, color):
        """Compute a hash key for pawn structure based on pawn and king positions."""
        pawn_positions = board.pieces(chess.PAWN, chess.WHITE) | board.pieces(chess.PAWN, chess.BLACK)
        king_positions = board.king(chess.WHITE) | (board.king(chess.BLACK) << 6 if board.king(chess.BLACK) else 0)
        return (pawn_positions, king_positions, color)

    def evaluate_structure(self, board: chess.Board, color: chess.Color) -> int:
        """Evaluate the pawn structure for a given color using cached results if possible."""
        key = self._compute_pawn_key(board, color)
        if key in self.pawn_hash_table:
            self.hash_hits += 1
            return self.pawn_hash_table[key]
        
        self.hash_misses += 1
        score = self._evaluate_pawn_structure(board, color)
        if len(self.pawn_hash_table) >= self.max_hash_size:
            self.pawn_hash_table.pop(next(iter(self.pawn_hash_table)))  # Remove oldest entry
        self.pawn_hash_table[key] = score
        return score

    def evaluate_promotion_potential(self, board: chess.Board, color: chess.Color) -> int:
        """Evaluate the promotion potential of pawns for a given color."""
        score = 0
        phase, _ = self._get_game_phase(board)
        passed_bonus = get_weight('pawn_structure', 'passed', phase)
        rank_bonuses = EVALUATION_WEIGHTS['pawn_structure']['passed_pawn_rank_bonus']
        for square in board.pieces(chess.PAWN, color):
            if self.is_passed_pawn(board, square, color):
                rank = chess.square_rank(square)
                if color == chess.WHITE:
                    score += rank_bonuses[rank]
                else:
                    score += rank_bonuses[7 - rank]
                score += passed_bonus
        return score

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

    def is_passed_pawn(self, board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
        """Check if a pawn is passed (no enemy pawns can stop it from promoting) using bitboards."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        enemy_pawns = board.pieces(chess.PAWN, not color)
        front_span = chess.BB_FILES[file]
        if file > 0:
            front_span |= chess.BB_FILES[file - 1]
        if file < 7:
            front_span |= chess.BB_FILES[file + 1]
        if color == chess.WHITE:
            front_span &= chess.BB_RANKS[0] << (rank + 1) * 8
        else:
            front_span &= chess.BB_RANKS[7] >> (7 - rank) * 8
        return not (enemy_pawns & front_span)

    def is_isolated_pawn(self, board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
        """Check if a pawn is isolated (no friendly pawns on adjacent files) using bitboards."""
        file = chess.square_file(square)
        friendly_pawns = board.pieces(chess.PAWN, color)
        adjacent_files = 0
        if file > 0:
            adjacent_files |= chess.BB_FILES[file - 1]
        if file < 7:
            adjacent_files |= chess.BB_FILES[file + 1]
        return not (friendly_pawns & adjacent_files)

    def is_doubled_pawn(self, board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
        """Check if a pawn is doubled (another friendly pawn on the same file) using bitboards."""
        file = chess.square_file(square)
        file_mask = chess.BB_FILES[file]
        pawns_on_file = board.pieces(chess.PAWN, color) & file_mask
        return bin(pawns_on_file).count('1') > 1

    def is_backward_pawn(self, board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
        """Check if a pawn is backward (cannot be supported by friendly pawns) using bitboards."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        friendly_pawns = board.pieces(chess.PAWN, color)
        adjacent_files = 0
        if file > 0:
            adjacent_files |= chess.BB_FILES[file - 1]
        if file < 7:
            adjacent_files |= chess.BB_FILES[file + 1]
        if color == chess.WHITE:
            support_area = adjacent_files & (chess.BB_RANKS[0] << (rank + 1) * 8)
        else:
            support_area = adjacent_files & (chess.BB_RANKS[7] >> (7 - rank) * 8)
        return not (friendly_pawns & support_area)

    def is_connected_pawn(self, board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
        """Check if a pawn is connected to other friendly pawns using bitboards."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        friendly_pawns = board.pieces(chess.PAWN, color)
        adjacent_area = 0
        for f in [file - 1, file + 1]:
            if 0 <= f <= 7:
                for r_offset in [-1, 0, 1]:
                    r = rank + r_offset
                    if 0 <= r <= 7:
                        adjacent_area |= 1 << chess.square(f, r)
        return bool(friendly_pawns & adjacent_area)

    def is_central_pawn(self, square: chess.Square) -> bool:
        """Check if a pawn is in the center (d4-e4-d5-e5)."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        return file in [3, 4] and rank in [3, 4]

    def _evaluate_pawn_structure(self, board: chess.Board, color: chess.Color) -> int:
        """Evaluate the pawn structure for a given color with game phase consideration."""
        score = 0
        pawn_files = [0] * 8
        friendly_pawns = board.pieces(chess.PAWN, color)
        enemy_pawns = board.pieces(chess.PAWN, not color)
        phase, taper_factor = self._get_game_phase(board)

        # Precompute pawn counts per file
        for square in friendly_pawns:
            file = chess.square_file(square)
            pawn_files[file] += 1

        # Evaluate individual pawn properties with phase-specific weights
        for square in friendly_pawns:
            rank = chess.square_rank(square)
            if self.is_passed_pawn(board, square, color):
                passed_bonus = get_weight('pawn_structure', 'passed', phase)
                if phase == 'middlegame' and taper_factor < 1.0:
                    endgame_bonus = get_weight('pawn_structure', 'passed', 'endgame')
                    passed_bonus = passed_bonus * taper_factor + endgame_bonus * (1.0 - taper_factor)
                score += passed_bonus
                if color == chess.WHITE:
                    score += rank * 10 * (1.5 if phase == 'endgame' else 1.0)
                else:
                    score += (7 - rank) * 10 * (1.5 if phase == 'endgame' else 1.0)
            if self.is_isolated_pawn(board, square, color):
                score += get_weight('pawn_structure', 'isolated', phase)
            if self.is_doubled_pawn(board, square, color):
                score += get_weight('pawn_structure', 'doubled', phase)
            if self.is_backward_pawn(board, square, color):
                score += get_weight('pawn_structure', 'backward', phase)
            if self.is_connected_pawn(board, square, color):
                score += get_weight('pawn_structure', 'connected', phase)
            if self.is_central_pawn(square):
                score += get_weight('pawn_structure', 'pawn_center', phase)

            # Protected passed pawn bonus
            if self.is_passed_pawn(board, square, color):
                defenders = board.attackers(color, square)
                if defenders:
                    score += get_weight('pawn_structure', 'passed', phase) * 0.4

        # Evaluate pawn islands
        islands = 0
        in_island = False
        for i in range(8):
            if pawn_files[i] > 0:
                if not in_island:
                    islands += 1
                    in_island = True
            else:
                in_island = False
        score += islands * get_weight('pawn_structure', 'pawn_island', phase)

        # Check pawn majority on each flank
        queenside_pawns = sum(pawn_files[0:4])
        kingside_pawns = sum(pawn_files[4:8])
        enemy_queenside = sum(1 for s in enemy_pawns if chess.square_file(s) < 4)
        enemy_kingside = sum(1 for s in enemy_pawns if chess.square_file(s) >= 4)
        majority_bonus = get_weight('pawn_structure', 'majority_bonus', phase)
        if queenside_pawns > enemy_queenside:
            score += majority_bonus
        if kingside_pawns > enemy_kingside:
            score += majority_bonus

        return score
