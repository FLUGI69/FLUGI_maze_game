#pragma once
#include <SFML/Window.hpp>

enum class InputAction {
    MoveUp, 
    MoveDown, 
    MoveLeft, 
    MoveRight,
    Skip, 
    Quit, 
    None
};

class InputHandler {
public:
    static InputAction poll(const sf::Event& event);
};
