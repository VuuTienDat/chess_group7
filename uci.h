#ifndef UCI_H
#define UCI_H

#include "position.h"
#include "search.h"
#include <string>

class UCI {
private:
    Position position;
    Search search;
public:
    UCI();
    void loop();
    void processCommand(const std::string& command);
};

#endif