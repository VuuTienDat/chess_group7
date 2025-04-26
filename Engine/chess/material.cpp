#include "material.h"
#include "board.h"
#include <bits/stdc++.h>
using namespace std;

int evaluateMaterial() {
    int material = 0;
    for (int i = 0; i < 8; i++) {
        for (int j = 0; j < 8; j++) {
            int piece = board[i][j];
            if (piece != EMPTY) {
                int absPiece = abs(piece);
                int value = PIECE_VALUES[absPiece];
                if (piece > 0) material += value;
                else material -= value;
            }
        }
    }
    return material;
}

int main() {
    cout << "Hello world!" << endl;
}
