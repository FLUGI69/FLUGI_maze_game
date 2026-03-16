#pragma once
#include "../core/Vec2.h"
#include <vector>
#include <random>

enum class CellType {
    WALL,
    PATH,
    START,
    EXIT_CLOSED,
    EXIT_OPEN
};

class Maze {
public:
    Maze();

    void generate();

    std::vector<Vec2> getRandomPositions(int count);
    std::vector<Vec2> getPositionsNear(const Vec2& center, int radius, int count);

    bool isWalkable(const Vec2& pos) const;
    bool isExit(const Vec2& pos) const;
    bool isExitOpen() const;

    void openExit();
    void closeExit();

    CellType getCell(int x, int y) const;

    int getWidth() const;
    int getHeight() const;

    const Vec2& getStartPos() const;
    const Vec2& getExitPos() const;

private:

    Vec2 findNearestPath(const Vec2& from) const;
    std::vector<Vec2> getFreePaths() const;

    void removeRandomWalls(int count);

    int width_;
    int height_;

    std::vector<std::vector<CellType>> grid_;

    Vec2 startPos_;
    Vec2 exitPos_;

    bool exitOpen_;
    
    std::mt19937 rng_;
};