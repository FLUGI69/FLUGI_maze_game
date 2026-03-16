cmake_minimum_required(VERSION 3.10)
project(FLUGI_MazeGame LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(SFML 2.5 COMPONENTS graphics window system REQUIRED)

add_executable(maze_game
    main.cpp
    src/graphics/Renderer.cpp
    src/utils/InputHandler.cpp
    src/maze/Maze.cpp
    src/entities/Player.cpp
    src/game/Game.cpp
)

target_link_libraries(maze_game sfml-graphics sfml-window sfml-system)
