#include "bitboard.h"
#include "types.h"
#include <cstdint>
// Magic numbers thực tế từ Stockfish (chỉ lấy một số ví dụ)
const Bitboard RookMagicNumbers[SQUARE_NB] = {
    0x0080001020400080ULL, 0x0040001000200040ULL, 0x0020000800100020ULL, 0x0010000400080010ULL,
    0x0008000200040008ULL, 0x0004000100020004ULL, 0x0002000080010002ULL, 0x0001000040008001ULL,
    // ... (Cần thêm đủ 64 số từ Stockfish)
};
const Bitboard BishopMagicNumbers[SQUARE_NB] = {
    0x0002020202020200ULL, 0x0002020202020000ULL, 0x0004010202000000ULL, 0x0004040080000000ULL,
    0x0001104000000000ULL, 0x0000821040000000ULL, 0x0000410410400000ULL, 0x0000104104104000ULL,
    // ... (Cần thêm đủ 64 số từ Stockfish)
};

Bitboard RookTable[SQUARE_NB][4096];
Bitboard BishopTable[SQUARE_NB][512];
Magic RookMagics[SQUARE_NB];
Magic BishopMagics[SQUARE_NB];

Bitboard rook_relevant_occupancy(Square s) {
    Bitboard mask = 0;
    int rank = s / 8, file = s % 8;
    for (int r = rank + 1; r < 7; ++r) mask |= (1ULL << (r * 8 + file));
    for (int r = rank - 1; r > 0; --r) mask |= (1ULL << (r * 8 + file));
    for (int f = file + 1; f < 7; ++f) mask |= (1ULL << (rank * 8 + f));
    for (int f = file - 1; f > 0; --f) mask |= (1ULL << (rank * 8 + f));
    return mask;
}

Bitboard bishop_relevant_occupancy(Square s) {
    Bitboard mask = 0;
    int rank = s / 8, file = s % 8;
    for (int r = rank + 1, f = file + 1; r < 7 && f < 7; ++r, ++f) mask |= (1ULL << (r * 8 + f));
    for (int r = rank + 1, f = file - 1; r < 7 && f > 0; ++r, --f) mask |= (1ULL << (r * 8 + f));
    for (int r = rank - 1, f = file + 1; r > 0 && f < 7; --r, ++f) mask |= (1ULL << (r * 8 + f));
    for (int r = rank - 1, f = file - 1; r > 0 && f > 0; --r, --f) mask |= (1ULL << (r * 8 + f));
    return mask;
}

Bitboard rook_attacks(Square s, Bitboard occupancy) {
    Bitboard attacks = 0;
    int rank = s / 8, file = s % 8;
    for (int r = rank + 1; r < 8; ++r) {
        attacks |= (1ULL << (r * 8 + file));
        if (occupancy & (1ULL << (r * 8 + file))) break;
    }
    for (int r = rank - 1; r >= 0; --r) {
        attacks |= (1ULL << (r * 8 + file));
        if (occupancy & (1ULL << (r * 8 + file))) break;
    }
    for (int f = file + 1; f < 8; ++f) {
        attacks |= (1ULL << (rank * 8 + f));
        if (occupancy & (1ULL << (rank * 8 + f))) break;
    }
    for (int f = file - 1; f >= 0; --f) {
        attacks |= (1ULL << (rank * 8 + f));
        if (occupancy & (1ULL << (rank * 8 + f))) break;
    }
    return attacks;
}

Bitboard bishop_attacks(Square s, Bitboard occupancy) {
    Bitboard attacks = 0;
    int rank = s / 8, file = s % 8;
    for (int r = rank + 1, f = file + 1; r < 8 && f < 8; ++r, ++f) {
        attacks |= (1ULL << (r * 8 + f));
        if (occupancy & (1ULL << (r * 8 + f))) break;
    }
    for (int r = rank + 1, f = file - 1; r < 8 && f >= 0; ++r, --f) {
        attacks |= (1ULL << (r * 8 + f));
        if (occupancy & (1ULL << (r * 8 + f))) break;
    }
    for (int r = rank - 1, f = file + 1; r >= 0 && f < 8; --r, ++f) {
        attacks |= (1ULL << (r * 8 + f));
        if (occupancy & (1ULL << (r * 8 + f))) break;
    }
    for (int r = rank - 1, f = file - 1; r >= 0 && f >= 0; --r, --f) {
        attacks |= (1ULL << (r * 8 + f));
        if (occupancy & (1ULL << (r * 8 + f))) break;
    }
    return attacks;
}

void init_magic_bitboards() {
    for (Square s = SQ_A1; s <= SQ_H8; ++s) {
        RookMagics[s].mask = rook_relevant_occupancy(s);
        RookMagics[s].magic = RookMagicNumbers[s % 8]; // Cần đủ 64 số
        RookMagics[s].attacks = RookTable[s];
        RookMagics[s].shift = 64 - __builtin_popcountll(RookMagics[s].mask);
        int rook_configs = 1 << __builtin_popcountll(RookMagics[s].mask);

        for (int i = 0; i < rook_configs; ++i) {
            Bitboard occupancy = 0;
            int idx = 0;
            Bitboard m = RookMagics[s].mask;
            while (m) {
                Square sq = Square(__builtin_ctzll(m));
                if (i & (1 << idx)) occupancy |= (1ULL << sq);
                m &= m - 1;
                ++idx;
            }
            Bitboard attacks = rook_attacks(s, occupancy);
            int magic_index = (occupancy * RookMagics[s].magic) >> RookMagics[s].shift;
            RookTable[s][magic_index] = attacks;
        }

        BishopMagics[s].mask = bishop_relevant_occupancy(s);
        BishopMagics[s].magic = BishopMagicNumbers[s % 8]; // Cần đủ 64 số
        BishopMagics[s].attacks = BishopTable[s];
        BishopMagics[s].shift = 64 - __builtin_popcountll(BishopMagics[s].mask);
        int bishop_configs = 1 << __builtin_popcountll(BishopMagics[s].mask);

        for (int i = 0; i < bishop_configs; ++i) {
            Bitboard occupancy = 0;
            int idx = 0;
            Bitboard m = BishopMagics[s].mask;
            while (m) {
                Square sq = Square(__builtin_ctzll(m));
                if (i & (1 << idx)) occupancy |= (1ULL << sq);
                m &= m - 1;
                ++idx;
            }
            Bitboard attacks = bishop_attacks(s, occupancy);
            int magic_index = (occupancy * BishopMagics[s].magic) >> BishopMagics[s].shift;
            BishopTable[s][magic_index] = attacks;
        }
    }
}

Bitboard get_rook_attacks(Square s, Bitboard occupancy) {
    occupancy &= RookMagics[s].mask;
    int index = (occupancy * RookMagics[s].magic) >> RookMagics[s].shift;
    return RookMagics[s].attacks[index];
}

Bitboard get_bishop_attacks(Square s, Bitboard occupancy) {
    occupancy &= BishopMagics[s].mask;
    int index = (occupancy * BishopMagics[s].magic) >> BishopMagics[s].shift;
    return BishopMagics[s].attacks[index];
}