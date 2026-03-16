#include "Player.h"
#include "../config/Config.h"
#include "../utils/ColorLog.h"
#include <string>

Player::Player()
    : GameObject(Vec2(1, 1), '@', Config::Player::NAME)
    , hp_(Config::Player::MAX_HP)
    , coins_(Config::Player::START_COINS)
    , hasShield_(Config::Player::START_HAS_SHIELD)
    , totalCoinsNeeded_(Config::Items::COIN_COUNT)
{}

void Player::reset(const Vec2& startPos) {
    position_ = startPos;
    hp_ = Config::Player::MAX_HP;
    coins_ = 0;
    hasShield_ = false;
    active_ = true;
}

Vec2 Player::getMoveTarget(int dx, int dy) const {
    return Vec2(position_.x + dx, position_.y + dy);
}

void Player::moveTo(const Vec2& pos) {
    position_ = pos;
}

void Player::collectCoin() {
    coins_++;
    ColorLog::info("Coin collected! (" + std::to_string(coins_) + "/" + std::to_string(totalCoinsNeeded_) + ")");
}

void Player::collectShield() {
    hasShield_ = true;
    ColorLog::info("Shield acquired! You are now protected.");
}

bool Player::triggerTrap() {

    if (hasShield_) {

        hasShield_ = false;

        ColorLog::warning("Shield blocked the trap! (Shield consumed)");

        return false;
    }

    hp_ -= Config::Difficulty::TRAP_DAMAGE;

    ColorLog::warning("Trap hit! HP: " + std::to_string(hp_) + "/" + std::to_string(Config::Player::MAX_HP));

    if (hp_ <= 0) {

        active_ = false;

        ColorLog::warning("Player died! All coins lost...");

        return true;
    }

    return false;
}

bool Player::hasAllCoins() const { return coins_ >= totalCoinsNeeded_; }
int Player::getHp() const { return hp_; }
int Player::getCoins() const { return coins_; }
int Player::getTotalCoinsNeeded() const { return totalCoinsNeeded_; }
bool Player::hasShield() const { return hasShield_; }
bool Player::isAlive() const { return hp_ > 0 && active_; }
void Player::setTotalCoinsNeeded(int total) { totalCoinsNeeded_ = total; }
