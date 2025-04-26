#include "pawn_structure.h"
#include "board.h"

int evaluatePawnStructure() {
    int pawnStructure = 0;
    for (int j = 0; j < 8; j++) {
        bool whitePawn = false, blackPawn = false;
        for (int i = 0; i < 8; i++) {
            if (board[i][j] == PAWN) {
                if (whitePawn) pawnStructure -= 15; // Phạt Tốt chồng Trắng
                whitePawn = true;
                if (i >= 5) pawnStructure += 20 * (i - 4); // Thưởng Tốt thông tiến xa
            } else if (board[i][j] == -PAWN) {
                if (blackPawn) pawnStructure += 15; // Phạt Tốt chồng Đen
                blackPawn = true;
                if (i <= 2) pawnStructure -= 20 * (3 - i); // Thưởng Tốt thông tiến xa
            }
        }
    }
    return pawnStructure;
}
