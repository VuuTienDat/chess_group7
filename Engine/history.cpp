#include "history.h"

History::History() {
    clear();
}

void History::clear() {
    for (int side = 0; side < 2; ++side)
        for (int from = 0; from < 64; ++from)
            for (int to = 0; to < 64; ++to)
                history[side][from][to] = 0;
}

void History::update(int side, int from, int to, int depth) {
    history[side][from][to] += depth * depth;
}

int History::getScore(int side, int from, int to) const {
    return history[side][from][to];
}