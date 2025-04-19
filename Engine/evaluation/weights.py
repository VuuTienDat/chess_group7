"""
Constants and weights for chess position evaluation.
All values are in centipawns (1 pawn = 100 centipawns).
"""

import chess

# Piece values in centipawns
PIECE_VALUES = {
    'P': 100,  # Pawn
    'N': 320,  # Knight
    'B': 330,  # Bishop
    'R': 500,  # Rook
    'Q': 900,  # Queen
    'K': 20000  # King
}

# Center squares (d4, d5, e4, e5)
CENTER_SQUARES = [
    chess.D4, chess.D5, chess.E4, chess.E5
]

# King safety weights
KING_SAFETY_WEIGHTS = {
    'pawn_shield': 20,      # Bonus for pawns protecting king
    'open_file': -15,       # Penalty for king on open file
    'semi_open_file': -10,  # Penalty for king on semi-open file
    'king_activity': 5,     # Bonus for king activity in endgame
    'king_center': -20,     # Penalty for king in center during opening/middlegame
    'castling': 30,         # Bonus for castling
    'safety_zone': 10       # Bonus for king in safety zone
}

# Development weights
DEVELOPMENT_WEIGHTS = {
    'piece_development': 20,    # Bonus for developed pieces
    'center_control': 15,       # Bonus for controlling center squares
    'piece_coordination': 10,   # Bonus for coordinated pieces
    'tempo': 10,                # Bonus for having the move
    'bishop_pair': 30,          # Bonus for having both bishops
    'rook_open_file': 20,       # Bonus for rook on open file
    'rook_semi_open_file': 10,  # Bonus for rook on semi-open file
    'knight_outpost': 25,       # Bonus for knight on outpost
    'queen_early': -10          # Penalty for early queen development
}

# Pawn structure weights
PAWN_STRUCTURE_WEIGHTS = {
    'doubled': -15,         # Penalty for doubled pawns
    'isolated': -20,        # Penalty for isolated pawns
    'passed': 50,           # Bonus for passed pawns
    'connected': 10,        # Bonus for connected pawns
    'backward': -15,        # Penalty for backward pawns
    'pawn_chain': 5,        # Bonus for pawn chains
    'pawn_mobility': 5,     # Bonus for mobile pawns
    'pawn_center': 10,      # Bonus for pawns in center
    'pawn_island': -10      # Penalty for pawn islands
}

# Mobility weights
MOBILITY_WEIGHTS = {
    'knight_mobility': 5,   # Bonus per square for knight
    'bishop_mobility': 3,   # Bonus per square for bishop
    'rook_mobility': 2,     # Bonus per square for rook
    'queen_mobility': 1,    # Bonus per square for queen
    'king_mobility': 1      # Bonus per square for king in endgame
}

# Phase weights (opening, middlegame, endgame)
PHASE_WEIGHTS = {
    'opening': {
        'development': 1.0,
        'center_control': 1.0,
        'king_safety': 0.8,
        'pawn_structure': 0.6,
        'piece_activity': 0.4
    },
    'middlegame': {
        'development': 0.6,
        'center_control': 0.8,
        'king_safety': 1.0,
        'pawn_structure': 0.8,
        'piece_activity': 1.0
    },
    'endgame': {
        'development': 0.2,
        'center_control': 0.4,
        'king_safety': 0.6,
        'pawn_structure': 1.0,
        'piece_activity': 0.8
    }
}

# Position evaluation weights
POSITION_WEIGHTS = {
    'material': 1.0,           # Material balance
    'position': 0.8,           # Piece placement
    'mobility': 0.6,           # Piece mobility
    'pawn_structure': 0.7,     # Pawn structure
    'king_safety': 0.9,        # King safety
    'threats': 0.5,            # Threats and attacks
    'space': 0.4,              # Space control
    'initiative': 0.3          # Initiative and tempo
}

# Positional bonuses/maluses
CENTER_BONUS = 20

# King safety weights
KING_DANGER_WEIGHT = 30
KING_CENTER_PENALTY_WEIGHT = 25
CASTLING_BONUS = 50
KING_SHIELD_BONUS = 15  # Bonus for pawns protecting king
KING_ATTACK_WEIGHT = 40  # Weight for king attack patterns

# Development weights
DEVELOPMENT_BONUS = 20
PIECE_ACTIVITY_WEIGHT = 15
TEMPO_BONUS = 10  # Bonus for having the move
PIECE_COORDINATION_BONUS = 25  # Bonus for pieces working together

# Pawn structure weights
PASSED_PAWN_BONUS = 50
ISOLATED_PAWN_PENALTY = -30
DOUBLED_PAWN_PENALTY = -20
BACKWARD_PAWN_PENALTY = -25
PAWN_CHAIN_BONUS = 15  # Bonus for connected pawns
PAWN_MAJORITY_BONUS = 20  # Bonus for pawn majority on a side

# Mobility weights
MOBILITY_WEIGHT = 10
OUTPOST_BONUS = 25  # Bonus for pieces on outposts
OPEN_FILE_BONUS = 20  # Bonus for rooks on open files
SEMI_OPEN_FILE_BONUS = 10  # Bonus for rooks on semi-open files

# Endgame weights
KING_ACTIVITY_WEIGHT = 30  # Weight for king activity in endgame
PASSED_PAWN_RANK_BONUS = [0, 0, 5, 10, 20, 35, 60, 100]  # Bonus for passed pawns by rank
OPPOSITION_BONUS = 40  # Bonus for having the opposition in king endgames

# Tactical weights
PIN_BONUS = 15  # Bonus for pinned pieces
FORK_BONUS = 25  # Bonus for potential forks
DISCOVERED_ATTACK_BONUS = 20  # Bonus for potential discovered attacks
XRAY_BONUS = 15  # Bonus for x-ray attacks 