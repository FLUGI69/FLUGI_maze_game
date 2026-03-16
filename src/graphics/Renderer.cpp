#include "Renderer.h"
#include "../config/Config.h"
#include "../utils/ColorLog.h"
#include <string>

Renderer::Renderer()
    : fontLoaded_(false)
    , tileSize_(Config::Window::TILE_SIZE)
    , hudHeight_(Config::Window::HUD_HEIGHT)
{}

void Renderer::init(sf::RenderWindow& window) {
    (void)window;

    // Try to load a system font
    const char* fontPaths[] = {
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        nullptr
    };

    for (int i = 0; fontPaths[i] != nullptr; i++) {
        if (font_.loadFromFile(fontPaths[i])) {
            fontLoaded_ = true;
            ColorLog::debug("Font loaded: " + std::string(fontPaths[i]));
            break;
        }
    }

    if (!fontLoaded_) {
        ColorLog::warning("No font found - HUD text will be disabled");
    }

    tileShape_.setSize(sf::Vector2f(static_cast<float>(tileSize_), static_cast<float>(tileSize_)));
    circleShape_.setRadius(static_cast<float>(tileSize_) / 3.0f);
}

void Renderer::draw(sf::RenderWindow& window,
                    const Maze& maze,
                    const Player& player,
                    const std::vector<Coin>& coins,
                    const std::vector<Shield>& shields,
                    const std::vector<Trap>& traps) {
    window.clear(sf::Color(30, 30, 30));
    drawMaze(window, maze);
    drawItems(window, coins, shields, traps);
    drawPlayer(window, player);
    drawHUD(window, player, maze);
    window.display();
}

void Renderer::drawMaze(sf::RenderWindow& window, const Maze& maze) {
    float yOff = static_cast<float>(hudHeight_);

    for (int y = 0; y < maze.getHeight(); y++) {
        for (int x = 0; x < maze.getWidth(); x++) {

            float px = static_cast<float>(x * tileSize_);
            float py = yOff + static_cast<float>(y * tileSize_);

            tileShape_.setPosition(px, py);

            CellType cell = maze.getCell(x, y);

            switch (cell) {
                case CellType::WALL:
                    tileShape_.setFillColor(sf::Color(60, 60, 80));
                    tileShape_.setOutlineColor(sf::Color(40, 40, 55));
                    tileShape_.setOutlineThickness(1.0f);
                    break;
                case CellType::PATH:
                    tileShape_.setFillColor(sf::Color(180, 180, 170));
                    tileShape_.setOutlineThickness(0);
                    break;
                case CellType::START:
                    tileShape_.setFillColor(sf::Color(100, 200, 100));
                    tileShape_.setOutlineThickness(0);
                    break;
                case CellType::EXIT_CLOSED:
                    tileShape_.setFillColor(sf::Color(200, 60, 60));
                    tileShape_.setOutlineThickness(0);
                    break;
                case CellType::EXIT_OPEN:
                    tileShape_.setFillColor(sf::Color(60, 220, 60));
                    tileShape_.setOutlineThickness(0);
                    break;
            }
            window.draw(tileShape_);
        }
    }
}

void Renderer::drawPlayer(sf::RenderWindow& window, const Player& player) {

    float yOff = static_cast<float>(hudHeight_);

    const Vec2& pos = player.getPosition();

    float margin = static_cast<float>(tileSize_) * 0.15f;

    sf::RectangleShape body;
    body.setSize(sf::Vector2f(static_cast<float>(tileSize_) - margin * 2,
        static_cast<float>(tileSize_) - margin * 2));
    body.setPosition(static_cast<float>(pos.x * tileSize_) + margin,
        yOff + static_cast<float>(pos.y * tileSize_) + margin);
    body.setFillColor(sf::Color(50, 120, 255));

    // Shield glow
    if (player.hasShield()) {

        body.setOutlineColor(sf::Color(0, 255, 255, 180));
        body.setOutlineThickness(3.0f);

    } else {

        body.setOutlineThickness(0);
    }

    window.draw(body);
}

void Renderer::drawItems(sf::RenderWindow& window,

    const std::vector<Coin>& coins,
    const std::vector<Shield>& shields,
    const std::vector<Trap>& traps) {

    float yOff = static_cast<float>(hudHeight_);
    float radius = static_cast<float>(tileSize_) / 3.0f;
    float offset = (static_cast<float>(tileSize_) - radius * 2) / 2.0f;

    // Coins - yellow circles
    for (const auto& coin : coins) {

        if (!coin.isActive()) continue;

        const Vec2& p = coin.getPosition();

        circleShape_.setRadius(radius);
        circleShape_.setFillColor(sf::Color(255, 215, 0));
        circleShape_.setPosition(static_cast<float>(p.x * tileSize_) + offset,
            yOff + static_cast<float>(p.y * tileSize_) + offset);

        window.draw(circleShape_);
    }

    for (const auto& shield : shields) {

        if (!shield.isActive()) continue;

        const Vec2& p = shield.getPosition();

        sf::RectangleShape diamond;

        float size = static_cast<float>(tileSize_) * 0.45f;

        diamond.setSize(sf::Vector2f(size, size));
        diamond.setOrigin(size / 2, size / 2);
        diamond.setRotation(45.0f);
        diamond.setFillColor(sf::Color(0, 220, 255));
        diamond.setPosition(static_cast<float>(p.x * tileSize_) + static_cast<float>(tileSize_) / 2,
            yOff + static_cast<float>(p.y * tileSize_) + static_cast<float>(tileSize_) / 2);
        window.draw(diamond);
    }

    if (Config::Difficulty::TRAPS_VISIBLE) {

        for (const auto& trap : traps) {

            if (!trap.isActive() || trap.isTriggered()) continue;

            const Vec2& p = trap.getPosition();

            float cx = static_cast<float>(p.x * tileSize_) + static_cast<float>(tileSize_) / 2;
            float cy = yOff + static_cast<float>(p.y * tileSize_) + static_cast<float>(tileSize_) / 2;
            float s = static_cast<float>(tileSize_) * 0.35f;

            sf::ConvexShape tri;

            tri.setPointCount(3);
            tri.setPoint(0, sf::Vector2f(cx, cy - s));
            tri.setPoint(1, sf::Vector2f(cx - s, cy + s * 0.7f));
            tri.setPoint(2, sf::Vector2f(cx + s, cy + s * 0.7f));
            tri.setFillColor(sf::Color(220, 50, 50));

            window.draw(tri);
        }
    }
}

void Renderer::drawHUD(sf::RenderWindow& window, const Player& player, const Maze& maze) {

    if (!fontLoaded_) return;

    sf::RectangleShape bar;

    bar.setSize(sf::Vector2f(static_cast<float>(window.getSize().x), static_cast<float>(hudHeight_)));
    bar.setFillColor(sf::Color(20, 20, 30));

    window.draw(bar);

    float textY = static_cast<float>(hudHeight_) / 2 - 10;
    float x = 10;

    for (int i = 0; i < Config::Player::MAX_HP; i++) {

        sf::CircleShape heart(8.0f);

        heart.setPosition(x + static_cast<float>(i) * 22, textY);
        heart.setFillColor(i < player.getHp() ? sf::Color(220, 30, 30) : sf::Color(80, 30, 30));

        window.draw(heart);
    }

    x += static_cast<float>(Config::Player::MAX_HP) * 22 + 20;

    sf::Text coinText;

    coinText.setFont(font_);
    coinText.setCharacterSize(16);
    coinText.setFillColor(sf::Color(255, 215, 0));
    coinText.setString("Coins: " + std::to_string(player.getCoins()) + "/" + std::to_string(player.getTotalCoinsNeeded()));
    coinText.setPosition(x, textY);

    window.draw(coinText);

    x += coinText.getLocalBounds().width + 30;

    sf::Text shieldText;

    shieldText.setFont(font_);
    shieldText.setCharacterSize(16);
    shieldText.setFillColor(player.hasShield() ? sf::Color(0, 220, 255) : sf::Color(100, 100, 100));
    shieldText.setString(player.hasShield() ? "Shield: ON" : "Shield: --");
    shieldText.setPosition(x, textY);

    window.draw(shieldText);

    x += shieldText.getLocalBounds().width + 30;

    sf::Text exitText;

    exitText.setFont(font_);
    exitText.setCharacterSize(16);
    exitText.setFillColor(maze.isExitOpen() ? sf::Color(60, 220, 60) : sf::Color(200, 60, 60));
    exitText.setString(maze.isExitOpen() ? "Exit: OPEN" : "Exit: LOCKED");
    exitText.setPosition(x, textY);

    window.draw(exitText);
}

void Renderer::drawMessage(sf::RenderWindow& window, const std::string& title, const std::string& subtitle) {

    window.clear(sf::Color(20, 20, 30));

    if (!fontLoaded_) {

        window.display();
        return;
    }

    float winW = static_cast<float>(window.getSize().x);
    float winH = static_cast<float>(window.getSize().y);

    sf::Text titleText;

    titleText.setFont(font_);
    titleText.setCharacterSize(36);
    titleText.setFillColor(sf::Color::White);
    titleText.setStyle(sf::Text::Bold);
    titleText.setString(title);

    sf::FloatRect tb = titleText.getLocalBounds();

    titleText.setPosition((winW - tb.width) / 2, winH / 2 - 50);

    window.draw(titleText);

    sf::Text subText;

    subText.setFont(font_);
    subText.setCharacterSize(18);
    subText.setFillColor(sf::Color(180, 180, 180));
    subText.setString(subtitle);

    sf::FloatRect sb = subText.getLocalBounds();

    subText.setPosition((winW - sb.width) / 2, winH / 2 + 10);

    window.draw(subText);

    window.display();
}
