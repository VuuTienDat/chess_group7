#include "evaluate.h"
#include "bitboard.h"

namespace Stockfish {

// Giá trị vật chất (theo centipawns)
const int piece_value[PIECE_TYPE_NB] = { 0, 100, 320, 330, 500, 900, 0 };

// Bảng piece-square (giá trị ví dụ, có thể lấy từ Stockfish)
const int pawn_table[SQUARE_NB] = {
     0,   0,   0,   0,   0,   0,   0,   0,
     5,  10,  10, -20, -20,  10,  10,   5,
     5,  -5, -10,   0,   0, -10,  -5,   5,
     0,   0,   0,  20,  20,   0,   0,   0,
     5,   5,  10,  25,  25,  10,   5,   5,
    10,  10,  20,  30,  30,  20,  10,  10,
    50,  50,  50,  50,  50,  50,  50,  50,
     0,   0,   0,   0,   0,   0,   0,   0
};

const int knight_table[SQUARE_NB] = {
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
};

const int bishop_table[SQUARE_NB] = {
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20
};

const int rook_table[SQUARE_NB] = {
     0,   0,   0,   5,   5,   0,   0,   0,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
     5,  10,  10,  10,  10,  10,  10,   5,
     0,   0,   0,   0,   0,   0,   0,   0
};

const int queen_table[SQUARE_NB] = {
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   5,   0, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
     0,   0,   5,   5,   5,   5,   0,  -5,
    -5,   0,   5,   5,   5,   5,   0,  -5,
    -10,   0,   5,   5,   5,   5,   0, -10,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20
};

const int king_table[SQUARE_NB] = {
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
     20,  20,   0,   0,   0,   0,  20,  20,
     20,  30,  10,   0,   0,  10,  30,  20
};

int Evaluator::material_score(const Position& pos) const {
    int score = 0;
    for (Color c : {WHITE, BLACK}) {
        int material = 0;
        for (PieceType pt : {PAWN, KNIGHT, BISHOP, ROOK, QUEEN}) {
            material += piece_value[pt] * popcount(pos.pieces(c, pt));
        }
        score += (c == WHITE ? 1 : -1) * material;
    }
    return score;
}

int Evaluator::piece_square_score(const Position& pos) const {
    int score = 0;
    for (Color c : {WHITE, BLACK}) {
        // Tốt
        Bitboard pawns = pos.pieces(c, PAWN);
        while (pawns) {
            Square s = pop_lsb(pawns);
            int idx = (c == WHITE) ? s : (SQUARE_NB - 1 - s);
            score += (c == WHITE ? 1 : -1) * pawn_table[idx];
        }

        // Mã
        Bitboard knights = pos.pieces(c, KNIGHT);
        while (knights) {
            Square s = pop_lsb(knights);
            int idx = (c == WHITE) ? s : (SQUARE_NB - 1 - s);
            score += (c == WHITE ? 1 : -1) * knight_table[idx];
        }

        // Tượng
        Bitboard bishops = pos.pieces(c, BISHOP);
        while (bishops) {
            Square s = pop_lsb(bishops);
            int idx = (c == WHITE) ? s : (SQUARE_NB - 1 - s);
            score += (c == WHITE ? 1 : -1) * bishop_table[idx];
        }

        // Xe
        Bitboard rooks = pos.pieces(c, ROOK);
        while (rooks) {
            Square s = pop_lsb(rooks);
            int idx = (c == WHITE) ? s : (SQUARE_NB - 1 - s);
            score += (c == WHITE ? 1 : -1) * rook_table[idx];
        }

        // Hậu
        Bitboard queens = pos.pieces(c, QUEEN);
        while (queens) {
            Square s = pop_lsb(queens);
            int idx = (c == WHITE) ? s : (SQUARE_NB - 1 - s);
            score += (c == WHITE ? 1 : -1) * queen_table[idx];
        }

        // Vua
        Bitboard kings = pos.pieces(c, KING);
        while (kings) {
            Square s = pop_lsb(kings);
            int idx = (c == WHITE) ? s : (SQUARE_NB - 1 - s);
            score += (c == WHITE ? 1 : -1) * king_table[idx];
        }
    }
    return score;
}

int Evaluator::king_safety_score(const Position& pos) const {
    int score = 0;
    Bitboard occupancy = pos.pieces();
    for (Color c : {WHITE, BLACK}) {
        Square ksq = pos.square(KING, c);
        Bitboard attacks = attacks_bb(ROOK, ksq, occupancy) | attacks_bb(BISHOP, ksq, occupancy);
        int attackers = popcount(attacks & pos.pieces(~c));
        score += (c == WHITE ? -1 : 1) * attackers * 10; // Phạt nếu vua bị tấn công
    }
    return score;
}

int Evaluator::pawn_structure_score(const Position& pos) const {
    int score = 0;
    for (Color c : {WHITE, BLACK}) {
        Bitboard pawns = pos.pieces(c, PAWN);
        for (File f = FILE_A; f <= FILE_H; ++f) {
            Bitboard file_pawns = pawns & file_bb(f);
            int count = popcount(file_pawns);
            if (count == 0) continue;
            if (count > 1) score += (c == WHITE ? -1 : 1) * 10; // Phạt tốt chồng

            // Phạt tốt cô lập
            Bitboard adjacent_files = (f > FILE_A ? file_bb(File(f - 1)) : 0) | (f < FILE_H ? file_bb(File(f + 1)) : 0);
            if (!(pawns & adjacent_files)) score += (c == WHITE ? -1 : 1) * 15; // Tốt cô lập

            // Phạt tốt lạc hậu
            Bitboard behind = (c == WHITE) ? shift<SOUTH>(file_pawns) : shift<NORTH>(file_pawns);
            if (file_pawns && !(pawns & behind)) score += (c == WHITE ? -1 : 1) * 10; // Tốt lạc hậu
        }
    }
    return score;
}

int Evaluator::evaluate(const Position& pos) {
    int score = 0;
    score += material_score(pos);
    score += piece_square_score(pos);
    score += king_safety_score(pos);
    score += pawn_structure_score(pos);
    score -= score * pos.rule50_count() / 212; // Giảm điểm nếu gần hòa 50 nước
    if (pos.side_to_move() == BLACK) score = -score;
    return std::clamp(score, -10000 + 1, 10000 - 1);
}

} // namespace Stockfish