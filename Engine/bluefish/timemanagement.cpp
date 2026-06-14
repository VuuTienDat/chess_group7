#include <chrono>
#include <ctime>

#include "timemanagement.h"

using namespace std::chrono; // @suppress("Symbol is not resolved")

namespace Time {

	// Helpers
	int get_sudden_death_time(int time_left, int moves_so_far);
	int get_regular_time(int time_left, int moves_to_go, int moves_so_far);

	int get_time_to_search(Time_options &options, int moves_so_far) {
		if (options.infinite)
			return max_time_to_search;
		if (options.moves_to_go == -1)
			return get_sudden_death_time(options.time_left, moves_so_far);
		else
			return get_regular_time(options.time_left, options.moves_to_go, moves_so_far);
	}

	/*
	 * Returns the time assigned for the search of
	 * the next move in a regular time control.
	 */
	int get_regular_time(int time_left, int moves_to_go, int moves_so_far) {
		float factor = 1;
		if (moves_so_far < 40)
			factor = 1.5;
		return factor * (time_left / moves_to_go);
	}

	/*
	 * Returns the time assigned for the search of
	 * the next move in a sudden death time control.
	 */
	int get_sudden_death_time(int time_left, int moves_so_far) {
		int moves_to_go = 15;
		if (moves_so_far <= 80)
			moves_to_go = ((-5 * moves_so_far ) / 16) + 40;
		float factor = 1;
		if (moves_so_far < 40)
			factor = 1.5;
		return factor * (time_left / moves_to_go);
	}

	/*
	 * Returns the current time in milliseconds.
	 */
	long long get_current_time_in_milliseconds() {
	    milliseconds now = duration_cast<milliseconds>( // @suppress("Type cannot be resolved") // @suppress("Symbol is not resolved")
	        steady_clock::now().time_since_epoch() // @suppress("Function cannot be resolved") // @suppress("Method cannot be resolved")
	    );
	    return now.count(); // @suppress("Method cannot be resolved")
	}

	/*
	 * Returns true if timeout.
	 */
	bool time_out(long long start_time, int time_to_search) {
		long long current_time = get_current_time_in_milliseconds();
		return current_time - 100 >= start_time + time_to_search; // 100 is a safety margin
	}

	/*
	 * Returns true if there's time for the next search iteration.
	 */
	bool time_for_next_iteration(long long start_time, int time_to_search) {
		long long current_time = get_current_time_in_milliseconds();
		return ((current_time - start_time) * 2) <= time_to_search;
	}
}
