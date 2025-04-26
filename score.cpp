#include "score.h"

Score Scores::normalize(Score score) {
    if (score >= Scores::MATE_IN_MAX)
        return Scores::MATE;
    if (score <= -Scores::MATE_IN_MAX)
        return -Scores::MATE;
    return score;
}