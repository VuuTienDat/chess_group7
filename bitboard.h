#ifndef BITBOARD_H
#define BITBOARD_H

#include <cstdint>

using Bitboard = uint64_t;

class Bitboards {
public:
    static Bitboard getSquare(int square);
    static Bitboard getRank(int rank);
    static Bitboard getFile(int file);
    static void init();
};

#endif