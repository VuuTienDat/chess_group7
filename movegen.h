#pragma once
#include "position.h"
#include "bitboard.h"
#include <vector>

namespace Stockfish {

class MoveGenerator {
public:
    MoveGenerator(const Position& pos);
    std::vector<Move> generate_legal_moves();

private:
    const Position& pos_;
    static const int knight_deltas[8];
    static const int king_deltas[8];

    void generate_pawn_moves(std::vector<Move>& moves);
    template<PieceType Pt> void generate_piece_moves(std::vector<Move>& moves);
    template<PieceType Pt> void generate_sliding_moves(std::vector<Move>& moves);
    void generate_castling_moves(std::vector<Move>& moves);
    bool is_legal(Move m);
    bool is_valid_square(Square s) const;
    Rank rank_of(Square s) const;
};

} // namespace Stockfish