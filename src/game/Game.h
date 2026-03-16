#pragma once
#include <SFML/Graphics.hpp>
#include "../maze/Maze.h"
#include "../entities/Player.h"
#include "../entities/Items.h"
#include "../graphics/Renderer.h"
#include <vector>

enum class GameState {
    Title,
    Playing,
    Won,
    Dead
};

class Game {
public:

    explicit Game(sf::RenderWindow* window, bool aiMode = false);
    void run();

private:

    void initRound();
    void resetRound();
    void placeItemsStrategically();
    void handleInput(const sf::Event& event);
    void handleAction(int dx, int dy);
    void checkItemCollisions(const Vec2& pos);
    void render();
    void runAI();

    std::string serializeState(bool includeMaze) const;

    sf::RenderWindow* window_;

    Renderer renderer_;

    Maze maze_;

    Player player_;

    std::vector<Coin> coins_;

    std::vector<Shield> shields_;

    std::vector<Trap> traps_;

    GameState state_;

    int moveCount_;
    
    bool aiMode_;
};
