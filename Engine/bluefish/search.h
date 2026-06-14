#ifndef SRC_SEARCH_H_
#define SRC_SEARCH_H_

#include "position.h"

namespace Search {

	// Constants
	constexpr int MATE_SCORE = 99000;
	constexpr int MAX_DEPTH = 32;

	/*
	 * Search info struct.
	 */
	struct Search_info {
		int depth;
		int time_to_search;
		long long start_time;
		long long nodes;
		bool stop;
	};

	/*
	 * Seach the position to a certain depth
	 * depending on the options specified in the
	 * search info.
	 * Prints the best move found.
	 */
	void search(Position &pos, Search_info &search_info);
}

#endif /* SRC_SEARCH_H_ */
