#pragma once
#include <iostream>
#include <string>
#include "../config/Config.h"

// Console-only debug logger with colored output
// info=white, debug=blue, error=red, warning=yellow, print=cyan

class ColorLog {
public:
    static inline bool useStderr = false;
    static inline bool silent = false;

    static void info(const std::string& msg) {

        if (silent) return;

        auto& out = useStderr ? std::cerr : std::cout;
        out << Config::Colors::WHITE << "[INFO] " << msg << Config::Colors::RESET << std::endl;
    }

    static void debug(const std::string& msg) {

        if (silent) return;

        auto& out = useStderr ? std::cerr : std::cout;
        out << Config::Colors::BLUE << "[DEBUG] " << msg << Config::Colors::RESET << std::endl;
    }

    static void error(const std::string& msg) {

        if (silent) return;

        auto& out = useStderr ? std::cerr : std::cout;
        out << Config::Colors::RED << "[ERROR] " << msg << Config::Colors::RESET << std::endl;
    }

    static void warning(const std::string& msg) {

        if (silent) return;

        auto& out = useStderr ? std::cerr : std::cout;
        out << Config::Colors::YELLOW << "[WARN] " << msg << Config::Colors::RESET << std::endl;
    }

    static void print(const std::string& msg) {

        if (silent) return;

        auto& out = useStderr ? std::cerr : std::cout;
        out << Config::Colors::CYAN << msg << Config::Colors::RESET << std::endl;
    }

    static void success(const std::string& msg) {

        if (silent) return;
        
        auto& out = useStderr ? std::cerr : std::cout;
        out << Config::Colors::GREEN << "[OK] " << msg << Config::Colors::RESET << std::endl;
    }
};
