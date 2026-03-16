#pragma once
#include "Vec2.h"
#include <string>
#include <utility>

class GameObject {
public:
    GameObject() : position_(), symbol_('?'), name_("Unknown"), active_(true) {}

    GameObject(const Vec2& pos, char symbol, std::string name)
        : position_(pos), symbol_(symbol), name_(std::move(name)), active_(true) {}

    virtual ~GameObject() = default;

    const Vec2& getPosition() const { return position_; }

    void setPosition(const Vec2& pos) { position_ = pos; }

    char getSymbol() const { return symbol_; }

    const std::string& getName() const { return name_; }

    bool isActive() const { return active_; }

    void setActive(bool state) { active_ = state; }

protected:
    Vec2 position_;

    char symbol_;

    std::string name_;
    
    bool active_;
};