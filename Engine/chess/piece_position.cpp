#include "piece_position.h"
#include "board.h"

const int PAWN_POS_SCORES[8][8] = {
    {0,  0,  0,  0,  0,  0,  0,  0},
    {50, 50, 50, 50, 50, 50, 50, 50},
    {10, 10, 20, 30, 30, 20, 10, 10},
    {5,  5, 10, 25, 25, 10,  5,  5},
    {0,  0,  0, 20, 20,  0,  0,  0},
    {5, -5,-10,  0,  0,-10, -5,  5},
    {5, 10, 10,-20,-20, 10, 10,  5},
    {0,  0,  0,  0,  0,  0,  0,  0}
};

const int KNIGHT_POS_SCORES[8][8] = {
    {-50,-40,-30,-30,-30,-30,-40,-50},
    {-40,-20,  0,  0,  0,  0,-20,-40},
    {-30,  0, 10, 15, 15, 10,  0,-30},
    {-30,  5, 15, 20, 20, 15,  5,-30},
    {-30,  0, 15, 20, 20, 15,  0,-30},
    {-30,  5, 10, 15, 15, 10,  5,-30},
    {-40,-20,  0,  5,  5,  0,-20,-40},
    {-50,-40,-30,-30,-30,-30,-40,-50}
};

int evaluatePiecePosition() {
    int piecePosition = 0;
    for (int i = 0; i < 8; i++) {
        for (int j = 0; j < 8; j++) {
            int piece = board[i][j];
            if (piece != EMPTY) {
                int absPiece = abs(piece);
                if (absPiece == PAWN) {
                    piecePosition += (piece > 0) ? PAWN_POS_SCORES[i][j] : -PAWN_POS_SCORES[7 - i][j];
                } else if (absPiece == KNIGHT) {
                    piecePosition += (piece > 0) ? KNIGHT_POS_SCORES[i][j] : -KNIGHT_POS_SCORES[7 - i][j];
                }
            }
        }
    }
    return piecePosition;
}
