#include "Game.h"
#include "../config/Config.h"
#include "../utils/ColorLog.h"
#include "../utils/InputHandler.h"
#include <string>
#include <sstream>

Game::Game(sf::RenderWindow* window, bool aiMode)
    : window_(window)
    , state_(GameState::Title)
    , moveCount_(0)
    , aiMode_(aiMode)
{}

void Game::run() {

    if (aiMode_) {
        runAI();
        return;
    }

    renderer_.init(*window_);

    ColorLog::info("Game initialized");

    while (window_->isOpen()) {

        sf::Event event;

        while (window_->pollEvent(event)) {

            if (event.type == sf::Event::Closed) {

                window_->close();
                return;
            }

            switch (state_) {
                case GameState::Title:
                    if (event.type == sf::Event::KeyPressed) {

                        initRound();
                        state_ = GameState::Playing;
                    }
                    break;

                case GameState::Playing:

                    handleInput(event);
                    break;

                case GameState::Won:
                    if (event.type == sf::Event::KeyPressed) {

                        if (event.key.code == sf::Keyboard::R) {
                            initRound();
                            state_ = GameState::Playing;

                        } else if (event.key.code == sf::Keyboard::Escape ||
                            event.key.code == sf::Keyboard::Q) {

                            window_->close();
                            return;
                        }
                    }
                    break;

                case GameState::Dead:
                    if (event.type == sf::Event::KeyPressed) {

                        if (event.key.code == sf::Keyboard::R) {
                            resetRound();
                            state_ = GameState::Playing;

                        } else if (event.key.code == sf::Keyboard::Escape || 
                            event.key.code == sf::Keyboard::Q) {

                            window_->close();
                            return;
                        }
                    }
                    break;
            }
        }

        render();
    }
}

void Game::initRound() {

    maze_.generate();

    ColorLog::info("New maze generated (" + std::to_string(maze_.getWidth()) + "x" + std::to_string(maze_.getHeight()) + ")");

    player_.reset(maze_.getStartPos());
    player_.setTotalCoinsNeeded(Config::Items::COIN_COUNT);
    moveCount_ = 0;

    placeItemsStrategically();

    ColorLog::success("Round started - collect " + std::to_string(Config::Items::COIN_COUNT) + " coins!");
    ColorLog::debug("Start pos: (" + std::to_string(maze_.getStartPos().x) + "," + std::to_string(maze_.getStartPos().y) + ")");
    ColorLog::debug("Exit pos: (" + std::to_string(maze_.getExitPos().x) + "," + std::to_string(maze_.getExitPos().y) + ")");
}

void Game::placeItemsStrategically() {

    coins_.clear();
    shields_.clear();
    traps_.clear();

    // Spread coins across the map (random positions)
    auto coinPositions = maze_.getRandomPositions(Config::Items::COIN_COUNT);

    for (const auto& p : coinPositions) {

        coins_.emplace_back(p);

        ColorLog::debug("Coin placed at (" + std::to_string(p.x) + "," + std::to_string(p.y) + ")");
    }

    // Place traps near coins - player must decide: take damage or find a shield first
    std::vector<Vec2> usedPositions(coinPositions.begin(), coinPositions.end());

    usedPositions.push_back(maze_.getStartPos());
    usedPositions.push_back(maze_.getExitPos());

    int trapsPlaced = 0;

    for (const auto& coinPos : coinPositions) {

        if (trapsPlaced >= Config::Items::TRAP_COUNT) break;

        auto nearby = maze_.getPositionsNear(coinPos, 4, 2);

        for (const auto& tp : nearby) {

            if (trapsPlaced >= Config::Items::TRAP_COUNT) break;

            bool conflict = false;

            for (const auto& used : usedPositions) {

                if (used == tp) { conflict = true; break; }
            }

            if (!conflict) {

                traps_.emplace_back(tp);
                usedPositions.push_back(tp);
                trapsPlaced++;

                ColorLog::debug("Trap placed at (" + std::to_string(tp.x) + "," + std::to_string(tp.y) + ") near coin");
            }
        }
    }

    // Fill remaining traps randomly
    if (trapsPlaced < Config::Items::TRAP_COUNT) {

        auto extraTraps = maze_.getRandomPositions(Config::Items::TRAP_COUNT - trapsPlaced + 10);

        for (const auto& tp : extraTraps) {

            if (trapsPlaced >= Config::Items::TRAP_COUNT) break;

            bool conflict = false;

            for (const auto& used : usedPositions) {

                if (used == tp) { conflict = true; break; }
            }
            if (!conflict) {

                traps_.emplace_back(tp);
                usedPositions.push_back(tp);
                trapsPlaced++;
            }
        }
    }

    // Place shields near groups of traps - player must detour to grab shield before engaging traps
    int shieldsPlaced = 0;
    for (const auto& trap : traps_) {

        if (shieldsPlaced >= Config::Items::SHIELD_COUNT) break;

        auto nearby = maze_.getPositionsNear(trap.getPosition(), 6, 3);

        for (const auto& sp : nearby) {

            if (shieldsPlaced >= Config::Items::SHIELD_COUNT) break;

            bool conflict = false;

            for (const auto& used : usedPositions) {

                if (used == sp) { conflict = true; break; }
            }
            if (!conflict) {

                shields_.emplace_back(sp);
                usedPositions.push_back(sp);
                shieldsPlaced++;

                ColorLog::debug("Shield placed at (" + std::to_string(sp.x) + "," + std::to_string(sp.y) + ") near trap");
            }
        }
    }

    // Fill remaining shields randomly
    if (shieldsPlaced < Config::Items::SHIELD_COUNT) {

        auto extraShields = maze_.getRandomPositions(Config::Items::SHIELD_COUNT - shieldsPlaced + 10);

        for (const auto& sp : extraShields) {

            if (shieldsPlaced >= Config::Items::SHIELD_COUNT) break;

            bool conflict = false;

            for (const auto& used : usedPositions) {

                if (used == sp) { conflict = true; break; }
            }

            if (!conflict) {

                shields_.emplace_back(sp);
                usedPositions.push_back(sp);
                shieldsPlaced++;
            }
        }
    }

    ColorLog::info("Items placed: " + std::to_string(coins_.size()) + " coins, "
        + std::to_string(shields_.size()) + " shields, "
        + std::to_string(traps_.size()) + " traps");
}

void Game::resetRound() {

    player_.reset(maze_.getStartPos());
    player_.setTotalCoinsNeeded(Config::Items::COIN_COUNT);

    moveCount_ = 0;

    // Reactivate all items, un-trigger traps
    for (auto& c : coins_)   c.setActive(true);
    for (auto& s : shields_) s.setActive(true);
    for (auto& t : traps_)   { t.setActive(true); t = Trap(t.getPosition()); }

    // Re-close exit
    maze_.closeExit();
    ColorLog::info("Restarting same maze...");
}

void Game::handleInput(const sf::Event& event) {

    InputAction action = InputHandler::poll(event);

    int dx = 0, dy = 0;

    switch (action) {

        case InputAction::MoveUp:    dy = -1; break;
        case InputAction::MoveDown:  dy =  1; break;
        case InputAction::MoveLeft:  dx = -1; break;
        case InputAction::MoveRight: dx =  1; break;

        case InputAction::Quit:
            window_->close();
            return;

        case InputAction::None:
            return;
    }

    handleAction(dx, dy);
}

void Game::handleAction(int dx, int dy) {

    Vec2 target = player_.getMoveTarget(dx, dy);

    if (!maze_.isWalkable(target)) return;

    player_.moveTo(target);
    moveCount_++;

    ColorLog::debug("Move #" + std::to_string(moveCount_) + " -> (" 
        + std::to_string(target.x) + "," + std::to_string(target.y) 
        + ") HP:" + std::to_string(player_.getHp())
        + " Shield:" + (player_.hasShield() ? "ON" : "OFF")
        + " Coins:" + std::to_string(player_.getCoins()) + "/" + std::to_string(player_.getTotalCoinsNeeded()
    ));

    checkItemCollisions(target);

    if (maze_.isExit(target) && maze_.isExitOpen()) {
        state_ = GameState::Won;
        ColorLog::success("You escaped the maze in " + std::to_string(moveCount_) + " moves!");
    }

    if (!player_.isAlive()) {
        state_ = GameState::Dead;
    }
}

void Game::checkItemCollisions(const Vec2& pos) {
    for (auto& coin : coins_) {

        if (coin.isActive() && coin.getPosition() == pos) {

            coin.setActive(false);
            player_.collectCoin();

            if (player_.hasAllCoins()) {

                maze_.openExit();
                ColorLog::success("All coins collected! EXIT is now OPEN!");
            }
            return;
        }
    }

    for (auto& shield : shields_) {

        if (shield.isActive() && shield.getPosition() == pos) {

            shield.setActive(false);
            player_.collectShield();
            return;
        }
    }

    for (auto& trap : traps_) {

        if (trap.isActive() && !trap.isTriggered() && trap.getPosition() == pos) {

            trap.trigger();
            player_.triggerTrap();
            return;
        }
    }
}

void Game::render() {
    switch (state_) {

        case GameState::Title:
            renderer_.drawMessage(*window_, "FLUGI MAZE GAME", "Press any key to start");
            break;

        case GameState::Playing:
            renderer_.draw(*window_, maze_, player_, coins_, shields_, traps_);
            break;

        case GameState::Won:
            renderer_.drawMessage(*window_, "YOU WIN!", "Press R for new maze  |  ESC to quit");
            break;

        case GameState::Dead:
            renderer_.drawMessage(*window_, "GAME OVER", "Press R to retry  |  ESC to quit");
            break;
    }
}

// --- AI mode: pipe-based communication with Python agent ---

void Game::runAI() {
    ColorLog::info("AI mode started");

    initRound();
    state_ = GameState::Playing;

    bool sendFull = true;
    int prevCoins = 0, prevShields = 0, prevTraps = 0;

    while (true) {

        if (sendFull) {
            std::cout << serializeState(true) << "\n" << std::flush;
            sendFull = false;
            prevCoins = 0;
            for (const auto& c : coins_) if (c.isActive()) prevCoins++;
            prevShields = 0;
            for (const auto& s : shields_) if (s.isActive()) prevShields++;
            prevTraps = 0;
            for (const auto& t : traps_) if (t.isActive() && !t.isTriggered()) prevTraps++;
        } else {
            const Vec2& pp = player_.getPosition();

            int nc = 0, ns = 0, nt = 0;
            for (const auto& c : coins_) if (c.isActive()) nc++;
            for (const auto& s : shields_) if (s.isActive()) ns++;
            for (const auto& t : traps_) if (t.isActive() && !t.isTriggered()) nt++;

            bool itemsDiff = (nc != prevCoins || ns != prevShields || nt != prevTraps);

            std::cout << pp.x << '\t' << pp.y << '\t'
                      << player_.getHp() << '\t'
                      << player_.getCoins() << '\t'
                      << (player_.hasShield() ? 1 : 0) << '\t'
                      << (maze_.isExitOpen() ? 1 : 0) << '\t'
                      << static_cast<int>(state_) << '\t'
                      << moveCount_;

            if (itemsDiff) {

                std::cout << '\t';

                bool first = true;

                for (const auto& c : coins_) {

                    if (!c.isActive()) continue;

                    if (!first) std::cout << ',';

                    std::cout << c.getPosition().x << ',' << c.getPosition().y;
                    first = false;
                }

                std::cout << '\t';

                first = true;


                for (const auto& s : shields_) {
                    if (!s.isActive()) continue;

                    if (!first) std::cout << ',';

                    std::cout << s.getPosition().x << ',' << s.getPosition().y;
                    first = false;
                }

                std::cout << '\t';

                first = true;

                for (const auto& t : traps_) {

                    if (!t.isActive() || t.isTriggered()) continue;

                    if (!first) std::cout << ',';

                    std::cout << t.getPosition().x << ',' << t.getPosition().y;
                    first = false;
                }

                prevCoins = nc;
                prevShields = ns;
                prevTraps = nt;
            }

            std::cout << '\n' << std::flush;
        }

        // Block-read action from stdin
        std::string action;

        if (!std::getline(std::cin, action)) {
            return;
        }

        if (action == "quit") {
            return;
        }

        if (action == "new") {

            initRound();
            state_ = GameState::Playing;
            sendFull = true;

        } else if (action == "restart") {

            resetRound();
            state_ = GameState::Playing;
            sendFull = true;

        } else if (state_ == GameState::Playing) {

            int dx = 0, dy = 0;

            if (action == "up")    dy = -1;
            else if (action == "down")  dy =  1;
            else if (action == "left")  dx = -1;
            else if (action == "right") dx =  1;

            if (dx != 0 || dy != 0) {
                handleAction(dx, dy);
            }
        }
    }
}

std::string Game::serializeState(bool includeMaze) const {
    std::ostringstream o;

    auto stateStr = [&]() {
        if (state_ == GameState::Playing) return "playing";
        if (state_ == GameState::Won)     return "won";
        if (state_ == GameState::Dead)    return "dead";
        return "title";
    };

    auto pos = [&](const Vec2& p) {
        o << "{\"x\":" << p.x << ",\"y\":" << p.y << "}";
    };

    // State
    o << "{\"state\":\"" << stateStr() << "\",";

    // Player
    const Vec2& pp = player_.getPosition();
    o << "\"player\":{\"x\":" << pp.x
      << ",\"y\":" << pp.y
      << ",\"hp\":" << player_.getHp()
      << ",\"coins\":" << player_.getCoins()
      << ",\"totalCoins\":" << player_.getTotalCoinsNeeded()
      << ",\"shield\":" << (player_.hasShield() ? "true" : "false")
      << "},";

    // Maze grid (only on first message per episode)
    int w = maze_.getWidth(), h = maze_.getHeight();
    o << "\"maze\":{\"width\":" << w << ",\"height\":" << h;

    if (includeMaze) {
        o << ",\"grid\":[";
        for (int y = 0; y < h; y++) {
            if (y > 0) o << ",";
            o << "[";
            for (int x = 0; x < w; x++) {
                if (x > 0) o << ",";
                o << static_cast<int>(maze_.getCell(x, y));
            }
            o << "]";
        }
        o << "]";
    }
    o << "},";

    // Coins
    o << "\"coins\":[";
    bool first = true;
    for (const auto& c : coins_) {
        if (!c.isActive()) continue;
        if (!first) o << ",";
        pos(c.getPosition());
        first = false;
    }
    o << "],";

    // Shields
    o << "\"shields\":[";
    first = true;
    for (const auto& s : shields_) {
        if (!s.isActive()) continue;
        if (!first) o << ",";
        pos(s.getPosition());
        first = false;
    }
    o << "],";

    // Traps
    o << "\"traps\":[";
    first = true;
    for (const auto& t : traps_) {
        if (!t.isActive() || t.isTriggered()) continue;
        if (!first) o << ",";
        pos(t.getPosition());
        first = false;
    }
    o << "],";

    // Exit
    const Vec2& ep = maze_.getExitPos();
    o << "\"exit\":{\"x\":" << ep.x
      << ",\"y\":" << ep.y
      << ",\"open\":" << (maze_.isExitOpen() ? "true" : "false")
      << "},";

    // Move count
    o << "\"moves\":" << moveCount_ << "}";

    return o.str();
}
