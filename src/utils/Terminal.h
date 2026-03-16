#pragma once
#include <iostream>

#ifdef _WIN32
#include <windows.h>
#endif

namespace Terminal {

    inline void enableAnsiColors() {

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
    }

    inline void clearScreen() {

        std::cout << "\033[2J\033[H" << std::flush;
    }

}
