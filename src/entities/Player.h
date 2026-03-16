#pragma once
#include "../core/GameObject.h"

class Player : public GameObject {
public:
    Player();

    void reset(const Vec2& startPos);

    Vec2 getMoveTarget(int dx, int dy) const;
    void moveTo(const Vec2& pos);

    void collectCoin();
    void collectShield();
    bool triggerTrap();

    bool hasAllCoins() const;
    int getHp() const;
    int getCoins() const;
    int getTotalCoinsNeeded() const;
    bool hasShield() const;
    bool isAlive() const;

    void setTotalCoinsNeeded(int total);

private:
    int hp_;
    int coins_;
    bool hasShield_;
    int totalCoinsNeeded_;
};