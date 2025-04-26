#include "position.h"
#include <sstream>

namespace Stockfish {

// Khóa Zobrist ngẫu nhiên (giả lập, cần tạo ngẫu nhiên trong thực tế)
Key ZobristTable[SQUARE_NB][PIECE_NB];
Key ZobristSide;
Key ZobristCastling[16];
Key ZobristEp[SQUARE_NB];

void init_zobrist() {
    // Giả lập các giá trị ngẫu nhiên (trong thực tế cần dùng PRNG)
    for (Square s = SQ_A1; s <= SQ_H8; ++s)
        for (Piece p = NO_PIECE; p < PIECE_NB; ++p)
            ZobristTable[s][p] = (Key(s) << 32) ^ Key(p); // Giả lập
    ZobristSide = 0x123456789ABCDEF0ULL;
    for (int i = 0; i < 16; ++i) ZobristCastling[i] = Key(i) << 48;
    for (Square s = SQ_A1; s <= SQ_H8; ++s) ZobristEp[s] = Key(s) << 40;
}

Move::Move() : from_(SQ_NONE), to_(SQ_NONE), promotion_(NO_PIECE_TYPE) {}
Move::Move(Square from, Square to, PieceType promotion) : from_(from), to_(to), promotion_(promotion) {}
Square Move::from() const { return from_; }
Square Move::to() const { return to_; }
PieceType Move::promotion() const { return promotion_; }
bool Move::is_ok() const { return from_ != to_ && from_ != SQ_NONE; }

Position::Position() { clear(); }

void Position::clear() {
    std::fill(std::begin(board_), std::end(board_), NO_PIECE);
    std::fill(std::begin(by_type_), std::end(by_type_), 0);
    std::fill(std::begin(by_color_), std::end(by_color_), 0);
    side_to_move_ = WHITE;
    si_ = nullptr;
    game_ply_ = 0;
}

void Position::set(const std::string& fen, StateInfo* si) {
    clear();
    si_ = si;
    si->ep_square = SQ_NONE;
    si->rule50 = 0;
    si->castling_rights = 0;
    si->key = 0;

    std::istringstream ss(fen);
    std::string token;
    
    Square sq = SQ_A8;
    ss >> token;
    for (char c : token) {
        if (c == '/') sq -= 16;
        else if (isdigit(c)) sq += (c - '0');
        else {
            put_piece(char_to_piece(c), sq);
            si->key ^= ZobristTable[sq][board_[sq]];
            ++sq;
        }
    }

    ss >> token;
    side_to_move_ = (token == "w") ? WHITE : BLACK;
    if (side_to_move_ == BLACK) si->key ^= ZobristSide;

    ss >> token;
    for (char c : token) {
        if (c == 'K') si->castling_rights |= (1 << 0);
        if (c == 'Q') si->castling_rights |= (1 << 1);
        if (c == 'k') si->castling_rights |= (1 << 2);
        if (c == 'q') si->castling_rights |= (1 << 3);
    }
    si->key ^= ZobristCastling[si->castling_rights];

    ss >> token;
    si->ep_square = (token == "-") ? SQ_NONE : square_from_string(token);
    if (si->ep_square != SQ_NONE) si->key ^= ZobristEp[si->ep_square];

    ss >> si->rule50 >> game_ply_;
    game_ply_ = std::max(2 * (game_ply_ - 1), 0) + (side_to_move_ == BLACK);
}

void Position::put_piece(Piece pc, Square s) {
    board_[s] = pc;
    by_color_[color_of(pc)] |= (1ULL << s);
    by_type_[type_of(pc)] |= (1ULL << s);
}

void Position::remove_piece(Square s) {
    Piece pc = board_[s];
    by_color_[color_of(pc)] ^= (1ULL << s);
    by_type_[type_of(pc)] ^= (1ULL << s);
    board_[s] = NO_PIECE;
}

void Position::do_move(Move m, StateInfo& new_st) {
    new_st = *si_;
    new_st.captured_piece = board_[m.to()];
    new_st.ep_square = SQ_NONE;
    new_st.rule50 = (type_of(board_[m.from()]) == PAWN || new_st.captured_piece != NO_PIECE) ? 0 : si_->rule50 + 1;
    new_st.key = si_->key ^ ZobristSide;

    if (si_->ep_square != SQ_NONE) new_st.key ^= ZobristEp[si_->ep_square];

    Piece pc = board_[m.from()];
    new_st.key ^= ZobristTable[m.from()][pc];
    if (new_st.captured_piece != NO_PIECE) {
        new_st.key ^= ZobristTable[m.to()][new_st.captured_piece];
        remove_piece(m.to());
    }

    // Cập nhật nhập thành
    if (type_of(pc) == KING) {
        if (side_to_move_ == WHITE) {
            new_st.castling_rights &= ~0x3; // Mất quyền nhập thành trắng
        } else {
            new_st.castling_rights &= ~0xC; // Mất quyền nhập thành đen
        }
    }
    if (m.from() == SQ_A1 || m.to() == SQ_A1) new_st.castling_rights &= ~0x2;
    if (m.from() == SQ_H1 || m.to() == SQ_H1) new_st.castling_rights &= ~0x1;
    if (m.from() == SQ_A8 || m.to() == SQ_A8) new_st.castling_rights &= ~0x8;
    if (m.from() == SQ_H8 || m.to() == SQ_H8) new_st.castling_rights &= ~0x4;
    new_st.key ^= ZobristCastling[si_->castling_rights] ^ ZobristCastling[new_st.castling_rights];

    // Di chuyển quân
    remove_piece(m.from());
    put_piece(pc, m.to());

    // Xử lý nhập thành
    if (type_of(pc) == KING && abs(m.to() - m.from()) == 2) {
        Square rook_from = (m.to() > m.from()) ? (side_to_move_ == WHITE ? SQ_H1 : SQ_H8) : (side_to_move_ == WHITE ? SQ_A1 : SQ_A8);
        Square rook_to = (m.to() > m.from()) ? (side_to_move_ == WHITE ? SQ_F1 : SQ_F8) : (side_to_move_ == WHITE ? SQ_D1 : SQ_D8);
        Piece rook = make_piece(side_to_move_, ROOK);
        new_st.key ^= ZobristTable[rook_from][rook] ^ ZobristTable[rook_to][rook];
        remove_piece(rook_from);
        put_piece(rook, rook_to);
    }

    // Xử lý bắt tốt qua đường
    if (type_of(pc) == PAWN && m.to() == si_->ep_square) {
        Square cap_sq = Square(m.to() + (side_to_move_ == WHITE ? SOUTH : NORTH));
        new_st.captured_piece = board_[cap_sq];
        new_st.key ^= ZobristTable[cap_sq][new_st.captured_piece];
        remove_piece(cap_sq);
    }

    // Xử lý phong cấp
    if (m.promotion() != NO_PIECE_TYPE) {
        remove_piece(m.to());
        put_piece(make_piece(side_to_move_, m.promotion()), m.to());
        new_st.key ^= ZobristTable[m.to()][pc] ^ ZobristTable[m.to()][board_[m.to()]];
    }

    // Cập nhật nước đi tốt qua đường
    if (type_of(pc) == PAWN && abs(m.to() - m.from()) == 16) {
        new_st.ep_square = Square((m.from() + m.to()) / 2);
        new_st.key ^= ZobristEp[new_st.ep_square];
    }

    side_to_move_ = ~side_to_move_;
    si_ = &new_st;
    ++game_ply_;
}

void Position::undo_move(Move m) {
    side_to_move_ = ~side_to_move_;
    Piece pc = board_[m.to()];
    if (m.promotion() != NO_PIECE_TYPE) {
        pc = make_piece(side_to_move_, PAWN);
        remove_piece(m.to());
        put_piece(pc, m.to());
    }

    remove_piece(m.to());
    put_piece(pc, m.from());

    if (si_->captured_piece != NO_PIECE) {
        put_piece(si_->captured_piece, m.to());
    }

    if (type_of(pc) == PAWN && m.to() == si_->ep_square) {
        Square cap_sq = Square(m.to() + (side_to_move_ == WHITE ? SOUTH : NORTH));
        put_piece(make_piece(~side_to_move_, PAWN), cap_sq);
    }

    if (type_of(pc) == KING && abs(m.to() - m.from()) == 2) {
        Square rook_from = (m.to() > m.from()) ? (side_to_move_ == WHITE ? SQ_H1 : SQ_H8) : (side_to_move_ == WHITE ? SQ_A1 : SQ_A8);
        Square rook_to = (m.to() > m.from()) ? (side_to_move_ == WHITE ? SQ_F1 : SQ_F8) : (side_to_move_ == WHITE ? SQ_D1 : SQ_D8);
        remove_piece(rook_to);
        put_piece(make_piece(side_to_move_, ROOK), rook_from);
    }

    si_ = si_->previous;
    --game_ply_;
}

Piece Position::piece_on(Square s) const { return board_[s]; }
Color Position::side_to_move() const { return side_to_move_; }
Square Position::ep_square() const { return si_->ep_square; }
int Position::rule50_count() const { return si_->rule50; }
int Position::castling_rights() const { return si_->castling_rights; }
Bitboard Position::pieces(Color c, PieceType pt) const { return by_color_[c] & by_type_[pt]; }
Bitboard Position::pieces(Color c) const { return by_color_[c]; }
Bitboard Position::pieces(PieceType pt) const { return by_type_[pt]; }
Bitboard Position::pieces() const { return by_color_[WHITE] | by_color_[BLACK]; }
Square Position::square(PieceType pt, Color c) const {
    Bitboard b = pieces(c, pt);
    return b ? lsb(b) : SQ_NONE;
}
Key Position::key() const { return si_->key; }

bool Position::in_check() const {
    Square ksq = square(KING, side_to_move());
    return attacked(ksq, ~side_to_move_);
}

bool Position::attacked(Square s, Color attacker) const {
    Bitboard occupancy = pieces();

    if (pawn_attacks_bb(~attacker, s) & pieces(attacker, PAWN))
        return true;

    if (attacks_bb(KNIGHT, s, occupancy) & pieces(attacker, KNIGHT))
        return true;

    if (attacks_bb(BISHOP, s, occupancy) & (pieces(attacker, BISHOP) | pieces(attacker, QUEEN)))
        return true;

    if (attacks_bb(ROOK, s, occupancy) & (pieces(attacker, ROOK) | pieces(attacker, QUEEN)))
        return true;

    if (attacks_bb(KING, s, occupancy) & pieces(attacker, KING))
        return true;

    return false;
}

Piece Position::char_to_piece(char c) const {
    const std::string piece_to_char = " PNBRQK  pnbrqk";
    size_t idx = piece_to_char.find(c);
    return idx == std::string::npos ? NO_PIECE : Piece(idx);
}

Square Position::square_from_string(const std::string& s) const {
    File f = File(s[0] - 'a');
    Rank r = Rank(s[1] - '1');
    return make_square(f, r);
}

PieceType Position::type_of(Piece pc) const { return PieceType(pc % 8); }
Color Position::color_of(Piece pc) const { return pc < B_PAWN ? WHITE : BLACK; }
Piece Position::make_piece(Color c, PieceType pt) const { return Piece(pt + (c == BLACK ? 7 : 0)); }

} // namespace Stockfish