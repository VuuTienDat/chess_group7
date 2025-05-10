#include "types.h"
#include "bitboards.h"


#ifndef SRC_ATTACKS_H_
#define SRC_ATTACKS_H_

namespace Attacks {

	/*
	 * Attack tables for non sliding pieces.
	 */
	extern Bitboard knight_attacks[SQUARES];
	extern Bitboard pawn_attacks[PLAYERS][SQUARES];
	extern Bitboard king_attacks[SQUARES];
	extern Bitboard king_castling[PLAYERS][SQUARES];

	/*
	 * Struct for magic bitboards move generation.
	 */
	struct Magic {
		Bitboard mask;
		Bitboard magic_number;
	};

	/*
	 * Magic multipliers for bishops and rooks.
	 */
	extern Magic bishop_magic_table[SQUARES];
	extern Magic rook_magic_table[SQUARES];

	/*
	 * Attack tables for sliding pieces.
	 */
	extern Bitboard bishop_attacks[512][SQUARES]; // 256 KB
	extern Bitboard rook_attacks[4096][SQUARES]; // 2MB

	/*
	 * Precomputed mobility for bishops and rooks (also used for queens)
	 */
	extern int bishop_mobility[512][SQUARES];
	extern int rook_mobility[4096][SQUARES];

	// Initialization
	void init();

	/*
	 * Return queen attacks.
	 */
	Bitboard get_queen_attacks(Bitboard occupancy, int square);

	/*
	 * Return bishop attacks.
	 */
	Bitboard get_bishop_attacks(Bitboard occupancy, int square);

	/*
	 * Return rook attacks.
	 */
	Bitboard get_rook_attacks(Bitboard occupancy, int square);
}

#endif /* SRC_ATTACKS_H_ */
