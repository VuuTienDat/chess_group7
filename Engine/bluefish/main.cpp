#include <iostream>

#include "position.h"
#include "bitboards.h"
#include "attacks.h"
#include "uci.h"
#include "transpositiontable.h"
#include "pawnhashtable.h"

using namespace std;

int main() {

	// Initialization
	Position::init();
	Bitboards::init();
	Attacks::init();
	Search::init();
	Evaluation::init();

	// UCI Protocol


	return 0;
}
