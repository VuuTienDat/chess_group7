#ifndef HISTORY_H
#define HISTORY_H

class History {
private:
    int history[2][64][64]; // [side][from][to]
public:
    History();
    void clear();
    void update(int side, int from, int to, int depth);
    int getScore(int side, int from, int to) const;
};

#endif