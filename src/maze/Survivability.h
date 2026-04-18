#pragma once
#include "../core/Vec2.h"
#include "../config/Config.h"
#include "../maze/Maze.h"
#include "../entities/Items.h"
#include <algorithm>
#include <map>
#include <vector>
#include <queue>
#include <set>

// Header-only survivability checker: determines whether the current maze
// can be completed (all coins collected + reach exit) without dying.
// Uses A* with trap penalty + greedy strategy (shield-first when low HP).

class Survivability {
public:

    static bool check(
        const std::vector<std::vector<CellType>>& grid,
        int width, int height,
        Vec2 playerPos, int hp, bool hasShield,
        const std::vector<Coin>& coins,
        const std::vector<Shield>& shields,
        const std::vector<Trap>& traps,
        Vec2 exitPos
    ) {
        // Build walkable set and item coordinate sets
        std::set<Vec2> remainingCoins;
        for (const auto& c : coins)

            if (c.isActive()) remainingCoins.insert(c.getPosition());

        std::set<Vec2> remainingShields;
        for (const auto& s : shields)

            if (s.isActive()) remainingShields.insert(s.getPosition());

        std::set<Vec2> activeTraps;
        for (const auto& t : traps)

            if (t.isActive() && !t.isTriggered()) activeTraps.insert(t.getPosition());

        Vec2 pos = playerPos;
        int currentHp = hp;
        bool currentShield = hasShield;
        int trapDamage = Config::Difficulty::TRAP_DAMAGE;

        int maxIter = static_cast<int>(remainingCoins.size() + remainingShields.size() + 2);

        for (int i = 0; i < maxIter; i++) {

            if (remainingCoins.empty()) break;

            // Low HP without shield -> try to grab a shield first
            if (currentHp <= trapDamage && !currentShield && !remainingShields.empty()) {

                auto path = findPath(grid, width, height, pos,

                    std::vector<Vec2>(remainingShields.begin(), remainingShields.end()),
                    activeTraps);

                if (!path.empty()) {

                    walk(
                        path, 
                        currentHp, 
                        currentShield, 
                        activeTraps,
                        remainingShields, 
                        remainingCoins, 
                        trapDamage
                    );
                    pos = path.back();

                    if (currentHp <= 0) return false;
                    continue;
                }
            }

            // Go to nearest coin
            auto path = findPath(grid, width, height, pos,

                std::vector<Vec2>(remainingCoins.begin(), remainingCoins.end()),
                activeTraps);

            if (path.empty()) return false;

            walk(
                path, 
                currentHp, 
                currentShield, 
                activeTraps,
                remainingShields, 
                remainingCoins, 
                trapDamage
            );
            pos = path.back();

            if (currentHp <= 0) return false;
        }

        if (!remainingCoins.empty()) return false;

        // Head to exit
        auto path = findPath(grid, width, height, pos, {exitPos}, activeTraps);

        if (path.empty()) return false;

        walk(
            path, 
            currentHp, 
            currentShield,
            activeTraps,
            remainingShields, 
            remainingCoins, 
            trapDamage
        );

        return currentHp > 0;
    }

private:

    struct Node {
        int cost;
        int x, y;
        bool operator>(const Node& o) const { return cost > o.cost; }
    };

    static constexpr int DX[] = {0, 0, -1, 1};
    static constexpr int DY[] = {-1, 1, 0, 0};

    static bool isWalkable(const std::vector<std::vector<CellType>>& grid,
        int width, int height, int x, int y) {

        if (x < 0 || x >= width || y < 0 || y >= height) return false;

        CellType c = grid[y][x];

        return c != CellType::WALL;
    }

    static std::vector<Vec2> findPath(
        const std::vector<std::vector<CellType>>& grid,
        int width, int height,
        Vec2 start,
        const std::vector<Vec2>& goals,
        const std::set<Vec2>& traps
    ) {
        std::set<Vec2> goalSet(goals.begin(), goals.end());

        std::priority_queue<Node, std::vector<Node>, std::greater<Node>> heap;
        heap.push({0, start.x, start.y});

        // came_from: maps position -> previous position
        std::map<Vec2, Vec2> cameFrom;
        std::map<Vec2, int> bestCost;

        bestCost[start] = 0;

        constexpr int TRAP_PENALTY = 20;

        while (!heap.empty()) {

            Node cur = heap.top();
            heap.pop();

            Vec2 curPos(cur.x, cur.y);

            {
                auto it = bestCost.find(curPos);
                if (it != bestCost.end() && cur.cost > it->second) continue;
            }

            if (goalSet.count(curPos)) {
                // Reconstruct path
                std::vector<Vec2> path;
                Vec2 p = curPos;

                while (!(p == start)) {
                    path.push_back(p);
                    p = cameFrom[p];
                }

                std::reverse(path.begin(), path.end());
                return path;
            }

            for (int d = 0; d < 4; d++) {
                int nx = cur.x + DX[d];
                int ny = cur.y + DY[d];

                if (!isWalkable(grid, width, height, nx, ny)) continue;

                Vec2 np(nx, ny);

                int penalty = traps.count(np) ? TRAP_PENALTY : 0;
                int newCost = cur.cost + 1 + penalty;

                auto it = bestCost.find(np);
                if (it == bestCost.end() || newCost < it->second) {

                    bestCost[np] = newCost;
                    cameFrom[np] = curPos;
                    heap.push({newCost, nx, ny});
                }
            }
        }

        return {}; // no path
    }

    static void walk(
        const std::vector<Vec2>& path,
        int& hp, bool& shield,
        std::set<Vec2>& activeTraps,
        std::set<Vec2>& remainingShields,
        std::set<Vec2>& remainingCoins,
        int trapDamage
    ) {
        for (const auto& step : path) {

            if (activeTraps.count(step)) {

                if (shield) {

                    shield = false;

                } else {

                    hp -= trapDamage;
                }
                activeTraps.erase(step);
                if (hp <= 0) return;
            }

            if (remainingShields.count(step)) {

                remainingShields.erase(step);
                shield = true;
            }

            if (remainingCoins.count(step)) {

                remainingCoins.erase(step);
            }
        }
    }
};
