#include "uci.h"
#include "bitboard.h"
#include "position.h"

int main() {
    init_magic_bitboards();
    init_zobrist();
    UCIEngine uci;
    uci.loop();
    return 0;
}