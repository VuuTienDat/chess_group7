#include "search.h"

Search::Search(Position& pos) : pos_(pos) {
    tt_.resize(16 * 1024 * 1024); // 16MB
}

Move Search::search(int depth) {
    best_move_ = Move();
    alpha_beta(-10000, 10000, depth);
    return best_move_;
}

int Search::alpha_beta(int alpha, int beta, int depth) {
    Key pos_key = pos_.key();
    TTEntry* entry = tt_.probe(pos_key);
    if (entry && entry->depth >= depth) {
        if (entry->bound == BOUND_EXACT) return entry->value;
        if (entry->bound == BOUND_LOWER && entry->value >= beta) return entry->value;
        if (entry->bound == BOUND_UPPER && entry->value <= alpha) return entry->value;
    }

    if (depth == 0) return eval_.evaluate(pos_);

    MoveGenerator gen(pos_);
    std::vector<Move> moves = gen.generate_legal_moves();
    if (moves.empty()) return pos_.side_to_move() == WHITE ? -10000 : 10000;

    int best_value = -10000;
    Move best_move;
    StateInfo st;
    for (Move m : moves) {
        pos_.do_move(m, st);
        int value = -alpha_beta(-beta, -alpha, depth - 1);
        pos_.undo_move(m);
        if (value > best_value) {
            best_value = value;
            best_move = m;
            if (depth == 3) best_move_ = m;
        }
        alpha = std::max(alpha, best_value);
        if (alpha >= beta) break;
    }

    Bound bound = best_value >= beta ? BOUND_LOWER : (best_value <= alpha ? BOUND_UPPER : BOUND_EXACT);
    tt_.store(pos_key, best_value, depth, bound, best_move);
    return best_value;
}