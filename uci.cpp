#include "uci.h"
#include <iostream>
#include <sstream>

UCI::UCI() : search(position) {}

void UCI::loop() {
    std::string command;
    while (std::getline(std::cin, command)) {
        processCommand(command);
    }
}

void UCI::processCommand(const std::string& command) {
    std::istringstream iss(command);
    std::string token;
    iss >> token;

    if (token == "uci") {
        std::cout << "id name SimpleChessEngine\n";
        std::cout << "id author YourName\n";
        std::cout << "uciok\n";
    } else if (token == "isready") {
        std::cout << "readyok\n";
    } else if (token == "ucinewgame") {
        position.setupInitialPosition();
    } else if (token == "position") {
        std::string fen;
        bool isStartpos = false;
        iss >> token;
        if (token == "startpos") {
            isStartpos = true;
            position.setupInitialPosition();
        } else if (token == "fen") {
            while (iss >> token && token != "moves") {
                fen += token + " ";
            }
            // TODO: position.setPositionFromFEN(fen);
        }
        if (token == "moves") {
            std::string move;
            while (iss >> move) {
                position.makeMove(move);
            }
        }
    } else if (token == "go") {
        int depth = 4;
        std::string bestMove = search.findBestMove(depth);
        std::cout << "bestmove " << bestMove << "\n";
    } else if (token == "quit") {
        exit(0);
    }
}