#pragma once

struct Vec2 {
    int x;
    int y;

    constexpr Vec2() : x(0), y(0) {}
    constexpr Vec2(int x, int y) : x(x), y(y) {}

    constexpr bool operator==(const Vec2& other) const {
        return x == other.x && y == other.y;
    }

    constexpr bool operator!=(const Vec2& other) const {
        return !(*this == other);
    }

    constexpr Vec2 operator+(const Vec2& other) const {
        return Vec2(x + other.x, y + other.y);
    }
};