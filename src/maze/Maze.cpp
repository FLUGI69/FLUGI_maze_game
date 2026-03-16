#include "Maze.h"
#include "../config/Config.h"
#include <stack>
#include <algorithm>
#include <ctime>

Maze::Maze()
    : width_(Config::Maze::WIDTH)
    , height_(Config::Maze::HEIGHT)
    , exitOpen_(false)
{
    if (width_ % 2 == 0) width_++;
    if (height_ % 2 == 0) height_++;
    rng_.seed(static_cast<unsigned>(std::time(nullptr)));
}

Vec2 Maze::findNearestPath(const Vec2& from) const {

    for (int y = from.y; y > 0; y--) {
        for (int x = from.x; x > 0; x--) {

            if (grid_[y][x] == CellType::PATH) {

                return Vec2(x, y);
            }
        }
    }
    return Vec2(1, 1);
}

void Maze::generate() {

    grid_.assign(height_, std::vector<CellType>(width_, CellType::WALL));

    exitOpen_ = false;

    const Vec2 start(1, 1);

    grid_[start.y][start.x] = CellType::PATH;

    std::stack<Vec2> stack;

    stack.push(start);

    constexpr Vec2 directions[] = {
        Vec2(2, 0), Vec2(0, 2), Vec2(-2, 0), Vec2(0, -2)
    };

    while (!stack.empty()) {

        Vec2 current = stack.top();

        std::vector<Vec2> unvisited;

        for (const auto& dir : directions) {

            Vec2 next = current + dir;

            if (next.x > 0 && next.x < width_ - 1 &&
                next.y > 0 && next.y < height_ - 1 &&
                grid_[next.y][next.x] == CellType::WALL) {
                unvisited.push_back(dir);
            }
        }

        if (unvisited.empty()) {

            stack.pop();
            continue;
        }

        std::uniform_int_distribution<int> dist(0, static_cast<int>(unvisited.size()) - 1);

        const Vec2& dir = unvisited[dist(rng_)];

        Vec2 wall(current.x + dir.x / 2, current.y + dir.y / 2);
        Vec2 next = current + dir;

        grid_[wall.y][wall.x] = CellType::PATH;
        grid_[next.y][next.x] = CellType::PATH;

        stack.push(next);
    }

    startPos_ = Vec2(1, 1);

    grid_[startPos_.y][startPos_.x] = CellType::START;

    exitPos_ = Vec2(width_ - 2, height_ - 2);

    if (grid_[exitPos_.y][exitPos_.x] == CellType::WALL) {

        exitPos_ = findNearestPath(exitPos_);
    }

    grid_[exitPos_.y][exitPos_.x] = CellType::EXIT_CLOSED;

    // Create loops and alternate routes for strategic gameplay
    removeRandomWalls(Config::Maze::EXTRA_PASSAGES);
}

void Maze::removeRandomWalls(int count) {

    std::vector<Vec2> candidates;

    for (int y = 2; y < height_ - 2; y++) {
        for (int x = 2; x < width_ - 2; x++) {

            if (grid_[y][x] != CellType::WALL) continue;

            bool horizBridge = (grid_[y][x - 1] == CellType::PATH && grid_[y][x + 1] == CellType::PATH);
            bool vertBridge  = (grid_[y - 1][x] == CellType::PATH && grid_[y + 1][x] == CellType::PATH);

            if (horizBridge || vertBridge) {

                candidates.emplace_back(x, y);
            }
        }
    }
    std::shuffle(candidates.begin(), candidates.end(), rng_);

    int removed = std::min(count, static_cast<int>(candidates.size()));

    for (int i = 0; i < removed; i++) {

        grid_[candidates[i].y][candidates[i].x] = CellType::PATH;
    }
}

std::vector<Vec2> Maze::getFreePaths() const {

    std::vector<Vec2> paths;

    for (int y = 0; y < height_; y++) {
        for (int x = 0; x < width_; x++) {

            if (grid_[y][x] == CellType::PATH) {

                paths.emplace_back(x, y);
            }
        }
    }
    return paths;
}

std::vector<Vec2> Maze::getRandomPositions(int count) {

    auto paths = getFreePaths();

    std::shuffle(paths.begin(), paths.end(), rng_);

    count = std::min(count, static_cast<int>(paths.size()));

    return {paths.begin(), paths.begin() + count};
}

std::vector<Vec2> Maze::getPositionsNear(const Vec2& center, int radius, int count) {

    std::vector<Vec2> nearby;
    for (int y = 0; y < height_; y++) {
        for (int x = 0; x < width_; x++) {

            if (grid_[y][x] != CellType::PATH) continue;

            int dist = std::abs(x - center.x) + std::abs(y - center.y);

            if (dist > 0 && dist <= radius) {

                nearby.emplace_back(x, y);
            }
        }
    }
    std::shuffle(nearby.begin(), nearby.end(), rng_);

    count = std::min(count, static_cast<int>(nearby.size()));

    return {nearby.begin(), nearby.begin() + count};
}

bool Maze::isWalkable(const Vec2& pos) const {

    if (pos.x < 0 || pos.x >= width_ || pos.y < 0 || pos.y >= height_) return false;

    return grid_[pos.y][pos.x] != CellType::WALL;
}

bool Maze::isExit(const Vec2& pos) const {

    return pos == exitPos_;
}

bool Maze::isExitOpen() const { return exitOpen_; }

void Maze::openExit() {

    exitOpen_ = true;
    grid_[exitPos_.y][exitPos_.x] = CellType::EXIT_OPEN;
}

void Maze::closeExit() {

    exitOpen_ = false;
    grid_[exitPos_.y][exitPos_.x] = CellType::EXIT_CLOSED;
}

CellType Maze::getCell(int x, int y) const { return grid_[y][x]; }

int Maze::getWidth() const { return width_; }
int Maze::getHeight() const { return height_; }

const Vec2& Maze::getStartPos() const { return startPos_; }
const Vec2& Maze::getExitPos() const { return exitPos_; }
