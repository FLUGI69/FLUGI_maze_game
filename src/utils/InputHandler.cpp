#include "InputHandler.h"

InputAction InputHandler::poll(const sf::Event& event) {

    if (event.type != sf::Event::KeyPressed) return InputAction::None;

    switch (event.key.code) {

        case sf::Keyboard::Escape:
        case sf::Keyboard::Q:

            return InputAction::Quit;

        case sf::Keyboard::W:
        case sf::Keyboard::Up:

            return InputAction::MoveUp;

        case sf::Keyboard::S:
        case sf::Keyboard::Down:

            return InputAction::MoveDown;

        case sf::Keyboard::A:
        case sf::Keyboard::Left:

            return InputAction::MoveLeft;

        case sf::Keyboard::D:
        case sf::Keyboard::Right:

            return InputAction::MoveRight;

        default:
        
            return InputAction::None;
    }
}
