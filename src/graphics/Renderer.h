#pragma once
#include <SFML/Graphics.hpp>
#include "../maze/Maze.h"
#include "../entities/Player.h"
#include "../entities/Items.h"
#include <vector>
#include <string>

// Renders the maze, entities and HUD into an SFML window
class Renderer {
public:
    Renderer();

    void init(sf::RenderWindow& window);

    void draw(sf::RenderWindow& window,
        const Maze& maze,
        const Player& player,
        const std::vector<Coin>& coins,
        const std::vector<Shield>& shields,
        const std::vector<Trap>& traps,
        const std::string& skipMessage = "");

    void drawMessage(sf::RenderWindow& window, const std::string& title, const std::string& subtitle);

private:

    void drawMaze(sf::RenderWindow& window, const Maze& maze);
    void drawPlayer(sf::RenderWindow& window, const Player& player);

    void drawItems(sf::RenderWindow& window,
        const std::vector<Coin>& coins,
        const std::vector<Shield>& shields,
        const std::vector<Trap>& traps);

    void drawHUD(sf::RenderWindow& window, const Player& player, const Maze& maze);

    sf::RectangleShape tileShape_;
    sf::CircleShape circleShape_;
    sf::Font font_;

    bool fontLoaded_;
    
    int tileSize_;
    int hudHeight_;
};
