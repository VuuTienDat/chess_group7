#pragma once
#include "types.h"
#include "bitboard.h"
#include <string>

namespace Stockfish {

struct StateInfo {
    Square ep_square;
    int rule50;
    int castling_rights;
    Piece captured_piece;
    StateInfo* previous;
    Key key; // Khóa Zobrist
};

class Move {
public:
    Move();
    Move(Square from, Square to, PieceType promotion = NO_PIECE_TYPE);
    Square from() const;
    Square to() const;
    PieceType promotion() const;
    bool is_ok() const;
private:
    Square from_, to_;
    PieceType promotion_;
};

class Position {
public:
    Position();
    void clear();
    void set(const std::string& fen, StateInfo* si);
    void put_piece(Piece pc, Square s);
    void remove_piece(Square s);
    void do_move(Move m, StateInfo& new_st);
    void undo_move(Move m);
    Piece piece_on(Square s) const;
    Color side_to_move() const;
    Square ep_square() const;
    int rule50_count() const;
    int castling_rights() const;
    Bitboard pieces(Color c, PieceType pt) const;
    Bitboard pieces(Color c) const;
    Bitboard pieces(PieceType pt) const;
    Bitboard pieces() const;
    Square square(PieceType pt, Color c) const;
    Key key() const;
    bool in_check() const;
    bool attacked(Square s, Color attacker) const;

private:
    Piece board_[SQUARE_NB];
    Bitboard by_type_[PIECE_TYPE_NB];
    Bitboard by_color_[COLOR_NB];
    Color side_to_move_;
    StateInfo* si_;
    int game_ply_;

    Piece char_to_piece(char c) const;
    Square square_from_string(const std::string& s) const;
    PieceType type_of(Piece pc) const;
    Color color_of(Piece pc) const;
    Piece make_piece(Color c, PieceType pt) const;
};

} // namespace Stockfish