#ifndef SCORE_H
#define SCORE_H

#include <cstdint>

using Score = int32_t;

class Scores {
public:
    static const Score MATE = 32000;
    static const Score MATE_IN_MAX = MATE - 1000;
    static Score normalize(Score score);
};

#endif