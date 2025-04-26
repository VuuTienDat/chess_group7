#include <iostream>
#include "engine.h"

int main() {
    int searchDepth = 5; // Độ sâu tìm kiếm để đạt ELO ~2000
    bool isWhite = true;
    std::cout << "Chess Engine started. White's turn.\n";
    Move bestMove = findBestMove(isWhite, searchDepth);
    std::cout << "Best move: (" << bestMove.fromX << "," << bestMove.fromY << ") to ("
              << bestMove.toX << "," << bestMove.toY << ")\n";
    return 0;
}
