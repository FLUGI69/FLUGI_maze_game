@echo off
echo === FLUGI Maze Game - Build (SFML) ===
echo.

set GCC=C:\msys64\ucrt64\bin\g++.exe

if not exist "%GCC%" (
    echo g++ not found at %GCC%
    echo Install: pacman -S mingw-w64-ucrt-x86_64-gcc
    pause
    exit /b 1
)

echo Compiling with SFML...
"%GCC%" -std=c++17 -O2 -Wall -Wextra ^
    -IC:\msys64\ucrt64\include ^
    -LC:\msys64\ucrt64\lib ^
    -o maze_game.exe ^
    main.cpp ^
    src/graphics/Renderer.cpp ^
    src/utils/InputHandler.cpp ^
    src/maze/Maze.cpp ^
    src/entities/Player.cpp ^
    src/game/Game.cpp ^
    -lsfml-graphics -lsfml-window -lsfml-system

if %ERRORLEVEL% == 0 (
    echo Build successful!
    echo.
    maze_game.exe
) else (
    echo Build failed!
)

pause
