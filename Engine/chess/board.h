#include <bits/stdc++.h>
#ifndef BOARD_H
#define BOARD_H

const int EMPTY = 0;
const int PAWN = 1;
const int KNIGHT = 2;
const int BISHOP = 3;
const int ROOK = 4;
const int QUEEN = 5;
const int KING = 6;

const int PIECE_VALUES[7] = {0, 100, 320, 330, 500, 900, 20000};

extern int board[8][8];

struct Move {
    int fromX, fromY, toX, toY;
    Move(int fx, int fy, int tx, int ty) : fromX(fx), fromY(fy), toX(tx), toY(ty) {}
};

std::vector<Move> generateMoves(bool isWhite);

#endif
