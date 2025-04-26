#pragma once
#include "types.h"
#include "position.h"
#include <vector>
struct TTEntry {
    Key key;
    int value;
    int depth;
    Bound bound;
    Move move;
};

class TranspositionTable {
public:
    TranspositionTable();
    void resize(size_t size_mb);
    TTEntry* probe(Key key) const;
    void store(Key key, int value, int depth, Bound bound, Move move);

private:
    std::vector<TTEntry> table_;
    size_t mask_;
};