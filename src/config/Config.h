#pragma once
#include <string>

namespace Config {

    namespace Window {
        inline const std::string TITLE = "FLUGI Maze Game";
        constexpr int TILE_SIZE        = 32;
        constexpr int HUD_HEIGHT       = 48;
        constexpr int FPS              = 60;
    }

    namespace Maze {
        constexpr int WIDTH            = 41;   // Must be odd
        constexpr int HEIGHT           = 25;   // Must be odd
        constexpr int EXTRA_PASSAGES   = 25;   // Random walls removed for loops
    }

    namespace Player {
        inline const std::string NAME  = "Hero";
        constexpr int MAX_HP           = 3;
        constexpr int START_COINS      = 0;
        constexpr bool START_HAS_SHIELD = false;
    }

    namespace Items {
        constexpr int COIN_COUNT       = 10;
        constexpr int SHIELD_COUNT     = 2;    // Scarce - choose wisely
        constexpr int TRAP_COUNT       = 18;   // Deadly minefield
    }

    namespace Difficulty {
        inline const std::string LEVEL = "HARDCORE";
        constexpr int TRAP_DAMAGE      = 1;
        constexpr bool TRAPS_VISIBLE   = true;
    }

    namespace Colors {
        inline const std::string RESET   = "\033[0m";
        inline const std::string WHITE   = "\033[37m";    // info
        inline const std::string BLUE    = "\033[34m";    // debug
        inline const std::string RED     = "\033[31m";    // error
        inline const std::string YELLOW  = "\033[33m";    // warning
        inline const std::string CYAN    = "\033[36m";    // print
        inline const std::string GREEN   = "\033[32m";    // success
        inline const std::string BOLD    = "\033[1m";
    }
}
