
#include <bits/stdc++.h>
#include "king_safety.h"
#include "board.h"

using namespace std;

int evaluateKingSafety() {
    int kingSafety = 0;
    for (int i = 0; i < 8; i++) {
        for (int j = 0; j < 8; j++) {
            int piece = board[i][j];
            if (piece == KING && (i > 1 || j < 2 || j > 5)) kingSafety -= 30; // Phạt Vua Trắng không an toàn
            else if (piece == -KING && (i < 6 || j < 2 || j > 5)) kingSafety += 30; // Phạt Vua Đen
            if (piece == KING && i > 0 && board[i - 1][j] == PAWN) kingSafety += 15; // Thưởng khiên Tốt
            else if (piece == -KING && i < 7 && board[i + 1][j] == -PAWN) kingSafety -= 15;
        }
    }
    return kingSafety;
}

