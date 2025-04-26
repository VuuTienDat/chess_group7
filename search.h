#pragma once
#include "position.h"
#include "movegen.h"
#include "evaluate.h"
#include "tt.h"

class Search {
public:
    Search(Position& pos);
    Move search(int depth);

private:
    Position& pos_;
    Move best_move_;
    Evaluator eval_;
    TranspositionTable tt_;
    int alpha_beta(int alpha, int beta, int depth);
};