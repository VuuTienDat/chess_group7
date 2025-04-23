"""
Constants and weights for chess position evaluation in centipawns (1 pawn = 100 centipawns).
This file provides a centralized structure for all evaluation weights, organized by category
and game phase where applicable. Weights are used to score various aspects of a chess position
such as material, king safety, piece activity, and pawn structure.

Structure:
- EVALUATION_WEIGHTS: Main dictionary with categories (e.g., 'material', 'king_safety') as keys.
- Each category contains sub-dictionaries for specific features and phase-specific adjustments
  (opening, middlegame, endgame) where relevant.
- Standalone constants (e.g., CENTER_SQUARES) are provided for specific use cases.
"""

import chess

# Central squares (d4, d5, e4, e5) for positional bonuses
CENTER_SQUARES = [chess.D4, chess.D5, chess.E4, chess.E5]

# Unified evaluation weights organized by category and game phase
EVALUATION_WEIGHTS = {
    'material': {
        'default': {
            'pawn': 100,    # Pawn value
            'knight': 320,  # Knight value
            'bishop': 330,  # Bishop value
            'rook': 500,    # Rook value
            'queen': 900,   # Queen value
            'king': 20000   # King value (theoretical)
        }
    },
    'king_safety': {
        'opening': {
            'pawn_shield': 20,      # Bonus for pawns protecting king
            'open_file': -15,       # Penalty for king on open file
            'semi_open_file': -10,  # Penalty for king on semi-open file
            'king_center': -25,     # Penalty for king in center
            'castling': 50,         # Bonus for castling
            'safety_zone': 10,      # Bonus for king in safety zone
            'attack_weight': 40     # Weight for king attack patterns
        },
        'middlegame': {
            'pawn_shield': 15,
            'open_file': -20,
            'semi_open_file': -15,
            'king_center': -30,
            'castling': 30,
            'safety_zone': 5,
            'attack_weight': 50
        },
        'endgame': {
            'pawn_shield': 5,
            'open_file': -10,
            'semi_open_file': -5,
            'king_center': 0,       # No penalty in endgame
            'castling': 10,
            'safety_zone': 0,
            'attack_weight': 20,
            'king_activity': 30     # Bonus for king activity in endgame
        }
    },
    'piece_activity': {
        'opening': {
            'knight_mobility': 3,   # Bonus per square for knight mobility
            'bishop_mobility': 2,   # Bonus per square for bishop mobility
            'rook_mobility': 1,     # Bonus per square for rook mobility
            'queen_mobility': 1,    # Bonus per square for queen mobility
            'center_bonus': 20,     # Bonus for pieces in center
            'outpost_bonus': 25,    # Bonus for pieces on outposts
            'rook_open_file': 15,   # Bonus for rook on open file
            'rook_semi_open': 10,   # Bonus for rook on semi-open file
            'bishop_pair': 30,      # Bonus for having both bishops
            'coordination': 20      # Bonus for pieces working together
        },
        'middlegame': {
            'knight_mobility': 5,
            'bishop_mobility': 3,
            'rook_mobility': 2,
            'queen_mobility': 1,
            'center_bonus': 15,
            'outpost_bonus': 30,
            'rook_open_file': 20,
            'rook_semi_open': 15,
            'bishop_pair': 40,
            'coordination': 25
        },
        'endgame': {
            'knight_mobility': 2,
            'bishop_mobility': 1,
            'rook_mobility': 3,
            'queen_mobility': 2,
            'center_bonus': 10,
            'outpost_bonus': 15,
            'rook_open_file': 25,
            'rook_semi_open': 20,
            'bishop_pair': 20,
            'coordination': 15
        }
    },
    'pawn_structure': {
        'opening': {
            'doubled': -10,         # Penalty for doubled pawns
            'isolated': -15,        # Penalty for isolated pawns
            'passed': 30,           # Bonus for passed pawns
            'connected': 5,         # Bonus for connected pawns
            'backward': -10,        # Penalty for backward pawns
            'pawn_chain': 3,        # Bonus for pawn chains
            'pawn_center': 10,      # Bonus for pawns in center
            'pawn_island': -5,      # Penalty for pawn islands
            'majority_bonus': 10    # Bonus for pawn majority on a side
        },
        'middlegame': {
            'doubled': -15,
            'isolated': -20,
            'passed': 50,
            'connected': 10,
            'backward': -15,
            'pawn_chain': 5,
            'pawn_center': 8,
            'pawn_island': -10,
            'majority_bonus': 15
        },
        'endgame': {
            'doubled': -20,
            'isolated': -30,
            'passed': 100,          # Higher bonus in endgame for passed pawns
            'connected': 15,
            'backward': -25,
            'pawn_chain': 10,
            'pawn_center': 5,
            'pawn_island': -15,
            'majority_bonus': 20
        },
        'passed_pawn_rank_bonus': [0, 0, 5, 10, 20, 35, 60, 100]  # Bonus for passed pawns by rank
    },
    'development': {
        'opening': {
            'piece_development': 20,    # Bonus for developed pieces
            'center_control': 15,       # Bonus for controlling center
            'tempo': 10,                # Bonus for having the move
            'queen_early': -15          # Penalty for early queen development
        },
        'middlegame': {
            'piece_development': 10,
            'center_control': 10,
            'tempo': 5,
            'queen_early': -5
        },
        'endgame': {
            'piece_development': 0,
            'center_control': 5,
            'tempo': 0,
            'queen_early': 0
        }
    },
    'tactical_features': {
        'default': {
            'pin_bonus': 15,            # Bonus for pinned pieces
            'fork_bonus': 25,           # Bonus for potential forks
            'discovered_attack': 20,    # Bonus for potential discovered attacks
            'xray_bonus': 15            # Bonus for x-ray attacks
        }
    },
    'endgame_specific': {
        'default': {
            'opposition_bonus': 40      # Bonus for having opposition in king endgames
        }
    },
    'phase_importance': {
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
}

# Helper function to access weights dynamically based on phase
def get_weight(category, feature, phase='default'):
    """
    Retrieve a weight for a specific category and feature, considering the game phase.
    Args:
        category (str): Evaluation category (e.g., 'king_safety', 'pawn_structure')
        feature (str): Specific feature within the category (e.g., 'pawn_shield')
        phase (str): Game phase ('opening', 'middlegame', 'endgame', or 'default')
    Returns:
        int/float: Weight value for the specified feature and phase
    """
    if category not in EVALUATION_WEIGHTS:
        return 0
    category_weights = EVALUATION_WEIGHTS[category]
    if phase in category_weights:
        return category_weights[phase].get(feature, 0)
    return category_weights.get('default', {}).get(feature, 0)
