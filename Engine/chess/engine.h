#ifndef ENGINE_H
#define ENGINE_H

#include <vector>
#include "board.h"

int evaluatePosition();
Move findBestMove(bool isWhite, int depth);

#endif
