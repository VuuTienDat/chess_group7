#include "mobility.h"
#include "board.h"

int countLegalMoves(bool isWhite) {
    int count = 0;
    for (int i = 0; i < 8; i++) {
        for (int j = 0; j < 8; j++) {
            if ((isWhite && board[i][j] > 0) || (!isWhite && board[i][j] < 0)) {
                if (i + 1 < 8 && (board[i + 1][j] == 0 || (isWhite && board[i + 1][j] < 0) || (!isWhite && board[i + 1][j] > 0))) count++;
                if (j + 1 < 8 && (board[i][j + 1] == 0 || (isWhite && board[i][j + 1] < 0) || (!isWhite && board[i][j + 1] > 0))) count++;
            }
        }
    }
    return count;
}

int evaluateMobility() {
    int whiteMoves = countLegalMoves(true);
    int blackMoves = countLegalMoves(false);
    return static_cast<int>((whiteMoves - blackMoves) * 0.1);
}
