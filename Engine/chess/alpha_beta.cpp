#include "alpha_beta.h"
#include "board.h"
#include "engine.h"

int alphaBeta(int depth, int alpha, int beta, bool maximizingPlayer) {
    if (depth == 0) {
        return evaluatePosition();
    }
    std::vector<Move> moves = generateMoves(maximizingPlayer);
    if (moves.empty()) {
        return maximizingPlayer ? INT_MIN : INT_MAX;
    }
    if (maximizingPlayer) {
        int maxEval = INT_MIN;
        for (const auto& move : moves) {
            int temp = board[move.toX][move.toY];
            board[move.toX][move.toY] = board[move.fromX][move.fromY];
            board[move.fromX][move.fromY] = EMPTY;
            int eval = alphaBeta(depth - 1, alpha, beta, false);
            board[move.fromX][move.fromY] = board[move.toX][move.toY];
            board[move.toX][move.toY] = temp;
            maxEval = std::max(maxEval, eval);
            alpha = std::max(alpha, eval);
            if (beta <= alpha) break;
        }
        return maxEval;
    } else {
        int minEval = INT_MAX;
        for (const auto& move : moves) {
            int temp = board[move.toX][move.toY];
            board[move.toX][move.toY] = board[move.fromX][move.fromY];
            board[move.fromX][move.fromY] = EMPTY;
            int eval = alphaBeta(depth - 1, alpha, beta, true);
            board[move.fromX][move.fromY] = board[move.toX][move.toY];
            board[move.toX][move.toY] = temp;
            minEval = std::min(minEval, eval);
            beta = std::min(beta, eval);
            if (beta <= alpha) break;
        }
        return minEval;
    }
}
