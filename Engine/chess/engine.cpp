#include "engine.h"
#include "material.h"
#include "piece_position.h"
#include "pawn_structure.h"
#include "king_safety.h"
#include "mobility.h"
#include "other_factors.h"
#include "alpha_beta.h"
#include <climits>

int board[8][8] = {
    {-ROOK, -KNIGHT, -BISHOP, -QUEEN, -KING, -BISHOP, -KNIGHT, -ROOK},
    {-PAWN, -PAWN, -PAWN, -PAWN, -PAWN, -PAWN, -PAWN, -PAWN},
    {0, 0, 0, 0, 0, 0, 0, 0},
    {0, 0, 0, 0, 0, 0, 0, 0},
    {0, 0, 0, 0, 0, 0, 0, 0},
    {0, 0, 0, 0, 0, 0, 0, 0},
    {PAWN, PAWN, PAWN, PAWN, PAWN, PAWN, PAWN, PAWN},
    {ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK}
};

std::vector<Move> generateMoves(bool isWhite) {
    std::vector<Move> moves;
    for (int i = 0; i < 8; i++) {
        for (int j = 0; j < 8; j++) {
            if ((isWhite && board[i][j] > 0) || (!isWhite && board[i][j] < 0)) {
                if (i + 1 < 8 && (board[i + 1][j] == 0 || (isWhite && board[i + 1][j] < 0) || (!isWhite && board[i + 1][j] > 0))) 
                    moves.push_back(Move(i, j, i + 1, j));
                if (j + 1 < 8 && (board[i][j + 1] == 0 || (isWhite && board[i][j + 1] < 0) || (!isWhite && board[i][j + 1] > 0))) 
                    moves.push_back(Move(i, j, i, j + 1));
            }
        }
    }
    return moves;
}

int evaluatePosition() {
    int material = evaluateMaterial();
    int piecePosition = evaluatePiecePosition();
    int pawnStructure = evaluatePawnStructure();
    int kingSafety = evaluateKingSafety();
    int mobility = evaluateMobility();
    int otherFactors = evaluateOtherFactors();

    // Tổng hợp điểm với trọng số (giá trị vật chất chiếm 70-80%)
    return (material * 8) / 10 + piecePosition + pawnStructure + kingSafety + mobility + otherFactors;
}

Move findBestMove(bool isWhite, int depth) {
    std::vector<Move> moves = generateMoves(isWhite);
    Move bestMove(0, 0, 0, 0);
    int bestValue = isWhite ? INT_MIN : INT_MAX;
    for (const auto& move : moves) {
        int temp = board[move.toX][move.toY];
        board[move.toX][move.toY] = board[move.fromX][move.fromY];
        board[move.fromX][move.fromY] = EMPTY;
        int moveValue = alphaBeta(depth - 1, INT_MIN, INT_MAX, !isWhite);
        board[move.fromX][move.fromY] = board[move.toX][move.toY];
        board[move.toX][move.toY] = temp;
        if (isWhite && moveValue > bestValue) {
            bestValue = moveValue;
            bestMove = move;
        } else if (!isWhite && moveValue < bestValue) {
            bestValue = moveValue;
            bestMove = move;
        }
    }
    return bestMove;
}
