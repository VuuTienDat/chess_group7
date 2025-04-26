#pragma once
#include "position.h"
#include "bitboard.h"

namespace Stockfish {

class Evaluator {
public:
    int evaluate(const Position& pos);

private:
    int material_score(const Position& pos) const;
    int piece_square_score(const Position& pos) const;
    int king_safety_score(const Position& pos) const;
    int pawn_structure_score(const Position& pos) const;
};

} // namespace Stockfish