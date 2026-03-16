#pragma once
#include "../core/GameObject.h"

class Coin : public GameObject {
public:
    explicit Coin(const Vec2& pos = Vec2())
        : GameObject(pos, 'C', "Coin") {}
};

class Shield : public GameObject {
public:
    explicit Shield(const Vec2& pos = Vec2())
        : GameObject(pos, 'S', "Shield") {}
};

class Trap : public GameObject {
public:
    explicit Trap(const Vec2& pos = Vec2())
        : GameObject(pos, 'T', "Trap") {}

    bool isTriggered() const { return triggered_; }
    void trigger() { triggered_ = true; }

private:
    bool triggered_ = false;
};
