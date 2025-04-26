#include "tt.h"
#include <vector>
#include <cstring>

TranspositionTable::TranspositionTable() : mask_(0) {}

void TranspositionTable::resize(size_t size_mb) {
    size_t num_entries = (size_mb * 1024 * 1024) / sizeof(TTEntry);
    num_entries = 1ULL << (63 - __builtin_clzll(num_entries - 1));
    table_.resize(num_entries);
    mask_ = num_entries - 1;
    std::memset(table_.data(), 0, num_entries * sizeof(TTEntry));
}

TTEntry* TranspositionTable::probe(Key key) const {
    size_t index = key & mask_;
    TTEntry* entry = &table_[index];
    if (entry->key == (key >> 32)) return entry;
    return nullptr;
}

void TranspositionTable::store(Key key, int value, int depth, Bound bound, Move move) {
    size_t index = key & mask_;
    TTEntry* entry = &table_[index];
    if (entry->depth <= depth || entry->key == 0) {
        entry->key = key >> 32;
        entry->value = value;
        entry->depth = depth;
        entry->bound = bound;
        entry->move = move;
    }
}