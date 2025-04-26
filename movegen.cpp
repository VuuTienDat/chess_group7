#include "movegen.h"
#include "bitboard.h"

namespace Stockfish {

const int MoveGenerator::knight_deltas[8] = { -17, -15, -10, -6, 6, 10, 15, 17 };
const int MoveGenerator::king_deltas[8] = { -9, -8, -7, -1, 1, 7, 8, 9 };

MoveGenerator::MoveGenerator(const Position& pos) : pos_(pos) {}

std::vector<Move> MoveGenerator::generate_legal_moves() {
    std::vector<Move> moves;
    generate_pawn_moves(moves);
    generate_piece_moves<KNIGHT>(moves);
    generate_sliding_moves<BISHOP>(moves);
    generate_sliding_moves<ROOK>(moves);
    generate_sliding_moves<QUEEN>(moves);
    generate_piece_moves<KING>(moves);
    generate_castling_moves(moves);

    std::vector<Move> legal_moves;
    StateInfo st;
    for (Move m : moves) {
        if (is_legal(m)) legal_moves.push_back(m);
    }
    return legal_moves;
}

void MoveGenerator::generate_pawn_moves(std::vector<Move>& moves) {
    Color us = pos_.side_to_move();
    Bitboard pawns = pos_.pieces(us, PAWN);
    Bitboard occupancy = pos_.pieces();
    Bitboard enemies = pos_.pieces(~us);
    Direction up = (us == WHITE) ? NORTH : SOUTH;
    Rank start_rank = (us == WHITE) ? RANK_2 : RANK_7;
    Rank promotion_rank = (us == WHITE) ? RANK_8 : RANK_1;

    // Nước đi tiến 1 ô
    Bitboard single_moves = shift<Direction(up)>(pawns) & ~occupancy;
    while (single_moves) {
        Square to = pop_lsb(single_moves);
        Square from = Square(to - up);
        if (rank_of(to) == promotion_rank) {
            moves.push_back(Move(from, to, QUEEN));
            moves.push_back(Move(from, to, ROOK));
            moves.push_back(Move(from, to, BISHOP));
            moves.push_back(Move(from, to, KNIGHT));
        } else {
            moves.push_back(Move(from, to));
        }
    }

    // Nước đi tiến 2 ô
    Bitboard double_moves = shift<Direction(up)>(single_moves) & ~occupancy & (us == WHITE ? Rank4BB : Rank5BB);
    while (double_moves) {
        Square to = pop_lsb(double_moves);
        Square from = Square(to - 2 * up);
        moves.push_back(Move(from, to));
    }

    // Nước đi bắt
    Bitboard captures = pawn_attacks_bb(us, pawns) & enemies;
    while (captures) {
        Square to = pop_lsb(captures);
        Square from = (us == WHITE) ?
            (file_of(to) > file_of(Square(to - NORTH_WEST)) ? Square(to - NORTH_WEST) : Square(to - NORTH_EAST)) :
            (file_of(to) > file_of(Square(to - SOUTH_WEST)) ? Square(to - SOUTH_WEST) : Square(to - SOUTH_EAST));
        if (rank_of(to) == promotion_rank) {
            moves.push_back(Move(from, to, QUEEN));
            moves.push_back(Move(from, to, ROOK));
            moves.push_back(Move(from, to, BISHOP));
            moves.push_back(Move(from, to, KNIGHT));
        } else {
            moves.push_back(Move(from, to));
        }
    }

    // Bắt tốt qua đường
    if (pos_.ep_square() != SQ_NONE) {
        Bitboard ep_capturers = pawn_attacks_bb(~us, pos_.ep_square()) & pawns;
        while (ep_capturers) {
            Square from = pop_lsb(ep_capturers);
            moves.push_back(Move(from, pos_.ep_square()));
        }
    }
}

template<PieceType Pt>
void MoveGenerator::generate_piece_moves(std::vector<Move>& moves) {
    Color us = pos_.side_to_move();
    Bitboard pieces = pos_.pieces(us, Pt);
    Bitboard not_own = ~pos_.pieces(us);
    Bitboard occupancy = pos_.pieces();

    while (pieces) {
        Square from = pop_lsb(pieces);
        Bitboard attacks = attacks_bb(Pt, from, occupancy);
        attacks &= not_own;
        while (attacks) {
            Square to = pop_lsb(attacks);
            moves.push_back(Move(from, to));
        }
    }
}

template<PieceType Pt>
void MoveGenerator::generate_sliding_moves(std::vector<Move>& moves) {
    Color us = pos_.side_to_move();
    Bitboard pieces = pos_.pieces(us, Pt);
    Bitboard not_own = ~pos_.pieces(us);
    Bitboard occupancy = pos_.pieces();

    while (pieces) {
        Square from = pop_lsb(pieces);
        Bitboard attacks = attacks_bb(Pt, from, occupancy);
        attacks &= not_own;
        while (attacks) {
            Square to = pop_lsb(attacks);
            moves.push_back(Move(from, to));
        }
    }
}

void MoveGenerator::generate_castling_moves(std::vector<Move>& moves) {
    Color us = pos_.side_to_move();
    if (pos_.in_check()) return;

    int castling_rights = pos_.castling_rights();
    Square ksq = pos_.square(KING, us);
    if (us == WHITE) {
        if (castling_rights & 1) { // Nhập thành ngắn
            if (pos_.piece_on(SQ_F1) == NO_PIECE && pos_.piece_on(SQ_G1) == NO_PIECE &&
                !pos_.attacked(SQ_F1, BLACK) && !pos_.attacked(SQ_G1, BLACK)) {
                moves.push_back(Move(ksq, SQ_G1));
            }
        }
        if (castling_rights & 2) { // Nhập thành dài
            if (pos_.piece_on(SQ_D1) == NO_PIECE && pos_.piece_on(SQ_C1) == NO_PIECE && pos_.piece_on(SQ_B1) == NO_PIECE &&
                !pos_.attacked(SQ_D1, BLACK) && !pos_.attacked(SQ_C1, BLACK)) {
                moves.push_back(Move(ksq, SQ_C1));
            }
        }
    } else {
        if (castling_rights & 4) { // Nhập thành ngắn
            if (pos_.piece_on(SQ_F8) == NO_PIECE && pos_.piece_on(SQ_G8) == NO_PIECE &&
                !pos_.attacked(SQ_F8, WHITE) && !pos_.attacked(SQ_G8, WHITE)) {
                moves.push_back(Move(ksq, SQ_G8));
            }
        }
        if (castling_rights & 8) { // Nhập thành dài
            if (pos_.piece_on(SQ_D8) == NO_PIECE && pos_.piece_on(SQ_C8) == NO_PIECE && pos_.piece_on(SQ_B8) == NO_PIECE &&
                !pos_.attacked(SQ_D8, WHITE) && !pos_.attacked(SQ_C8, WHITE)) {
                moves.push_back(Move(ksq, SQ_C8));
            }
        }
    }
}

bool MoveGenerator::is_legal(Move m) {
    StateInfo st;
    Position& pos = const_cast<Position&>(pos_);
    pos.do_move(m, st);
    bool in_check = pos.in_check();
    pos.undo_move(m);
    return !in_check;
}

bool MoveGenerator::is_valid_square(Square s) const { return s >= SQ_A1 && s <= SQ_H8; }
Rank MoveGenerator::rank_of(Square s) const { return Rank(s / 8); }

} // namespace Stockfish