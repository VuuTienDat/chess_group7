#include "other_factors.h"
#include "board.h"
#include <bits/stdc++.h>

using namespace std;

int evaluateOtherFactors() {
    int centerControl = 0;
    int threats = 0;
    int space = 0;

    // Kiểm soát trung tâm (D4, E4, D5, E5)
    int centerSquares[4][2] = {{3, 3}, {3, 4}, {4, 3}, {4, 4}};
    for (int k = 0; k < 4; k++) {
        int x = centerSquares[k][0], y = centerSquares[k][1];
        if (board[x][y] > 0) centerControl += 10;
        else if (board[x][y] < 0) centerControl -= 10;
    }

    // Không gian (dựa trên số hàng Tốt tiến)
    for (int j = 0; j < 8; j++) {
        for (int i = 0; i < 8; i++) {
            if (board[i][j] == PAWN && i > 3) space += 5;
            else if (board[i][j] == -PAWN && i < 4) space -= 5;
        }
    }

    return centerControl + threats + space;
}



