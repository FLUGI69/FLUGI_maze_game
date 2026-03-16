#include <SFML/Graphics.hpp>
#include "src/config/Config.h"
#include "src/utils/ColorLog.h"
#include "src/game/Game.h"
#include <cstring>

#ifdef _WIN32
#include <windows.h>
#endif

int main(int argc, char* argv[]) {

    bool aiMode = false;

    for (int i = 1; i < argc; i++) {

        if (std::strcmp(argv[i], "--ai") == 0) aiMode = true;
    }

    if (aiMode) {
        ColorLog::useStderr = true;
        ColorLog::silent = true;
    }

    // Enable ANSI colors in the debug console
    #ifdef _WIN32
    SetConsoleOutputCP(65001);
    HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);

    if (hOut != INVALID_HANDLE_VALUE) {

        DWORD dwMode = 0;

        if (GetConsoleMode(hOut, &dwMode)) {

            SetConsoleMode(hOut, dwMode | ENABLE_VIRTUAL_TERMINAL_PROCESSING);
        }
    }
    #endif

    ColorLog::info("Starting FLUGI Maze Game...");

    if (aiMode) {

        Game game(nullptr, true);
        game.run();

    } else {

        const int winW = Config::Maze::WIDTH * Config::Window::TILE_SIZE;
        const int winH = Config::Maze::HEIGHT * Config::Window::TILE_SIZE + Config::Window::HUD_HEIGHT;

        sf::RenderWindow window(
            sf::VideoMode(winW, winH),
            Config::Window::TITLE,
            sf::Style::Titlebar | sf::Style::Close
        );
        window.setFramerateLimit(Config::Window::FPS);

        Game game(&window, false);
        game.run();
    }

    ColorLog::info("Game closed. Goodbye!");
    return 0;
}
