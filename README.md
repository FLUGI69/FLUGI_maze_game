# FLUGI Maze Game

C++17 OOP maze game with SFML graphics, procedural maze generation, and a Python AI agent (rule-based Dijkstra + DQN reinforcement learning with maze skip).

**Difficulty: HARDCORE** - 41×25 maze, 18 traps (2 damage each), only 2 shields, 10 coins. The rule-based bot often dies on impossible mazes; the trained RL agent learns to **skip** unwinnable mazes instead of dying.

---

## Gameplay

- **Procedurally generated maze** - Recursive Backtracking + random wall removal (loops, alternate routes)
- Collect all **coins** (yellow circles) to unlock the exit
- Avoid **traps** (red triangles) - they deal **2 HP damage**. Pick up **shields** (cyan diamonds) first to absorb a hit
- **Death** = restart same maze layout (items reset to original positions)
- **Win** = press R for a brand new maze

## Items

| Visual | Item | Description |
|--------|------|-------------|
| Yellow circle | Coin | Collect all 10 to open the exit |
| Cyan diamond | Shield | Absorbs one trap hit, then breaks (only 2!) |
| Red triangle | Trap | Deals 2 HP damage (or consumes shield) |
| Blue square | Player | That's you! Glows cyan when shielded |
| Green tile | Start | Starting position |
| Red tile | Exit (locked) | Collect all coins first |
| Bright green tile | Exit (open) | Walk here to win |

## Controls

| Key | Action |
|-----|--------|
| **Arrow keys** / **WASD** | Move (up/down/left/right) |
| **R** | Restart maze (on death/win screens) |
| **Q** / **ESC** | Quit game |

---

## Prerequisites

- **MSYS2 ucrt64** - [https://www.msys2.org](https://www.msys2.org)
- **g++ 14+** - `pacman -S mingw-w64-ucrt-x86_64-gcc`
- **SFML 2** - `pacman -S mingw-w64-ucrt-x86_64-sfml`
- **Python 3.11+** - [https://www.python.org](https://www.python.org)
- **NVIDIA GPU + CUDA** (optional) - for faster DQN training

---

## Step-by-Step Setup

### Step 1 - Clone the repository

```bash
git clone <repository-url>
cd FLUGI_maze_game
```

### Step 2 - Compile the C++ game

Open **PowerShell** and add MSYS2 to PATH:

```powershell
$env:Path = "C:\msys64\ucrt64\bin;" + $env:Path
```

Compile:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -o maze_game.exe main.cpp src/graphics/Renderer.cpp src/utils/InputHandler.cpp src/maze/Maze.cpp src/entities/Player.cpp src/game/Game.cpp -lsfml-graphics -lsfml-window -lsfml-system
```

> **Note:** In AI training mode (`--ai` flag), the game runs headless - no SFML window is created. The SFML window only opens for human play and `--play` mode.

### Step 3 - Copy SFML DLLs

The following DLLs must be in the same folder as `maze_game.exe`:

| DLL file | Source (MSYS2 default) |
|----------|----------------------|
| `libsfml-graphics-2.dll` | `C:\msys64\ucrt64\bin\` |
| `libsfml-window-2.dll` | `C:\msys64\ucrt64\bin\` |
| `libsfml-system-2.dll` | `C:\msys64\ucrt64\bin\` |

Copy them:

```powershell
Copy-Item C:\msys64\ucrt64\bin\libsfml-graphics-2.dll, C:\msys64\ucrt64\bin\libsfml-window-2.dll, C:\msys64\ucrt64\bin\libsfml-system-2.dll .
```

> **Note:** Without these DLLs the game will not start (missing DLL error). They are not included in the repository - you must install SFML via MSYS2 and copy them yourself.

### Step 4 - Set up the Python environment

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

This installs: `torch` (CPU), `numpy`, `matplotlib`.

### Step 5 - Install CUDA PyTorch (optional, recommended)

If you have an NVIDIA GPU, install the CUDA-enabled PyTorch for significantly faster training:

```powershell
pip install torch --index-url https://download.pytorch.org/whl/cu128 --force-reinstall
```

Verify:

```powershell
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

> **Note:** The `cu128` index supports CUDA 12.8+ drivers. Check your driver version with `nvidia-smi`. For older drivers, use `cu124` or `cu121` instead.

### Step 6 - Verify

```bash
.\maze_game.exe                    # Should open the game window
python -m agent                    # Should run the AI agent (rule-based bot)
python -m agent --train --gpu      # Should start DQN training on GPU
```

---

## How to Use

### 1. Play the game yourself

```bash
.\maze_game.exe
```

Use arrow keys or WASD to navigate the maze. Collect all 10 coins, avoid traps, grab shields. Press R after win/death.

### 2. Watch the rule-based bot

```bash
python -m agent
```

The Dijkstra-based bot plays 5 rounds automatically. In **hardcore mode** it often dies - the traps deal 2 damage and there are only 2 shields for 18 traps. It **blindly attempts every maze**, even impossible ones.

### 3. Pre-train the CNN (supervised)

```bash
python -m agent --pretrain              # auto-detect GPU/CPU
python -m agent --pretrain --gpu        # force GPU
```

Before RL training, teach the CNN to recognize **impossible vs survivable** mazes:

- Generates **3000 random mazes** from the game
- Labels each with the pathfinder's `check_survivability()` analysis
- Trains a binary classifier on the CNN backbone (~93% impossible, ~7% survivable)
- Reaches **100% accuracy** in ~10 epochs (~7 seconds on GPU)
- Saves conv+fc weights to `models/pretrained.pt`

The RL trainer automatically loads `pretrained.pt` if it exists, so the agent starts with a CNN that already **understands maze structure**.

### 4. Train a DQN agent

```bash
python -m agent --train              # auto-detect GPU/CPU
python -m agent --train --gpu        # force GPU (CUDA)
python -m agent --train --cpu        # force CPU
```

The DQN (Deep Q-Network) learns to navigate the maze through trial and error:

- **5 actions**: up, down, left, right, **skip** (request new maze)
- **Skip action** - the RL agent learns to recognize impossible/unwinnable mazes and **skip** them instead of dying. This is the key differentiator vs the rule-based bot
- **Smart skip** - only rewarded when the maze was truly unwinnable (verified by survivability analysis). Skipping a winnable maze is penalized
- **No SFML window** - training runs headless (console + matplotlib chart only)
- **Live chart** - 2×2 matplotlib window: reward, epsilon, win rate + skip rate, loss
- **Speed metrics** - each episode shows ep/s and step/s in the log
- **1000 episodes** by default, **2000 steps max** per episode (timeout penalty)
- Models saved to `models/`: `best.pt`, `final.pt`, `checkpoint_*.pt`
- Chart saved as `training_chart.png`

**Stopping training:**

- **Close the chart window** - cleanly stops training and saves `final.pt`
- **Ctrl+C** - interrupts training and saves `final.pt`

### 5. Play with the trained model

```bash
python -m agent --play
```

Loads `models/best.pt` and plays **1000 mazes** using the trained policy network (greedy, no exploration). Skipped mazes don't count — the win rate is calculated from actually played (won + lost) mazes only.

---

## Reward Shaping

The DQN agent receives the following rewards during training:

| Event | Reward | Purpose |
|-------|--------|---------|
| Win (reach exit) | +50.0 | Ultimate goal |
| **Good skip** (impossible maze) | +2.0 | Smart decision - avoid certain death |
| Collect coin | +5.0 | Encourage collecting |
| Pick up shield | +2.0 | Encourage shield use |
| Exit opens | +3.0 | Milestone reward |
| Step cost | -0.01 | Encourage efficiency |
| Revisit tile | -0.1 | Don't go in circles |
| Wall bump (no move) | -0.5 | Don't walk into walls |
| Shield consumed | -1.0 | Shield is finite |
| HP loss (trap hit) | -10.0 | Avoid traps |
| Timeout (2000 steps) | -10.0 | Don't wander forever |
| **Bad skip** (winnable maze) | -30.0 | Don't skip doable mazes |
| Death | -30.0 | Avoid dying |

### Skip vs Pathfinder

The skip action is what makes the RL agent smarter than the rule-based Dijkstra bot:

| | Rule-based bot | RL agent |
|---|---|---|
| **Impossible maze** | Blindly tries → dies | Recognizes danger → **skips** |
| **Winnable maze** | Finds path → completes | Navigates → completes |
| **Result** | Low win rate (dies often) | Higher effective win rate |

The RL agent learns to evaluate the maze layout and decide: *"Can I survive this, or should I skip?"* This is tracked as 3 outcomes: **WON**, **GOOD SKIP** (correctly skipped impossible maze), **BAD SKIP** (incorrectly skipped).

**Win rate calculation:** only actually played mazes count. `win_rate = wins / (wins + losses)`. Skipped mazes are excluded — the agent can skip as many impossible mazes as it wants without hurting its win rate.

### Training Pipeline

```
1. --pretrain     →  CNN learns maze structure (supervised, ~7s)
2. --train --gpu  →  RL fine-tunes navigation + skip decisions (1000 episodes)
3. --play         →  Evaluate on 1000 mazes, compare win rate to rule-based bot
```

---

## Project Structure

```
FLUGI_maze_game/
├── main.cpp                        # Entry point, SFML window, --ai flag
├── src/
│   ├── config/Config.h             # C++ config (namespaces)
│   ├── core/
│   │   ├── Vec2.h                  # 2D position struct
│   │   └── GameObject.h            # Base entity class
│   ├── entities/
│   │   ├── Player.h/.cpp           # Player (HP, coins, shield)
│   │   └── Items.h                 # Coin, Shield, Trap classes
│   ├── maze/
│   │   └── Maze.h/.cpp             # Procedural maze generation
│   ├── graphics/
│   │   └── Renderer.h/.cpp         # SFML rendering (tiles, items, HUD)
│   ├── game/
│   │   └── Game.h/.cpp             # Game loop, state machine, AI mode (runAI)
│   └── utils/
│       ├── ColorLog.h              # Colored ANSI console log (silent in AI mode)
│       └── InputHandler.h/.cpp     # SFML keyboard input
│
├── agent/                          # Python AI agent package
│   ├── __main__.py                 # Entry point (python -m agent)
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py               # Config(object) - all settings
│   ├── obj/
│   │   ├── __init__.py
│   │   ├── launcher.py             # Launcher - CLI dispatch + colored logging
│   │   ├── agent.py                # Agent - rule-based Dijkstra bot
│   │   ├── rl_player.py            # RLPlayer - plays with trained model
│   │   ├── game_process.py         # GameProcess - subprocess pipe management
│   │   ├── game_state.py           # GameState - JSON → Python object
│   │   ├── pathfinder.py           # Pathfinder - Dijkstra pathfinding + survivability check
│   │   └── strategist.py           # Strategist - rule-based decision maker
│   └── training/
│       ├── __init__.py
│       ├── pretrain.py             # Pretrainer - supervised CNN pre-training
│       ├── trainer.py              # Trainer - DQN training loop (GPU/CPU)
│       ├── environment.py          # MazeEnvironment - gym-like wrapper
│       ├── dqn.py                  # DQN(nn.Module) - CNN + FC network (5 actions)
│       ├── replay_memory.py        # ReplayMemory - deque-based
│       └── chart.py                # TrainingChart - live matplotlib chart
│
├── requirements.txt                # torch, numpy, matplotlib
├── .gitignore
└── README.md
```

## Configuration

### C++ (`src/config/Config.h`)

| Namespace | Parameter | Value | Description |
|-----------|-----------|-------|-------------|
| `Maze` | `WIDTH` / `HEIGHT` | 41 × 25 | Maze dimensions (must be odd) |
| `Maze` | `EXTRA_PASSAGES` | 25 | Extra walls removed for loops |
| `Items` | `COIN_COUNT` | 10 | Number of coins |
| `Items` | `SHIELD_COUNT` | 2 | Number of shields (scarce!) |
| `Items` | `TRAP_COUNT` | 18 | Number of traps (deadly!) |
| `Difficulty` | `TRAP_DAMAGE` | 2 | Damage per trap hit |
| `Player` | `MAX_HP` | 3 | Starting health |

### Python (`agent/config/config.py`)

| Class | Parameter | Value | Description |
|-------|-----------|-------|-------------|
| `agent` | `max_mazes` | 1000 | Total mazes to play (for win rate comparison) |
| `agent` | `max_steps` | 800 | Max steps per maze (rule-based bot) |
| `pathfinder` | `trap_penalty` | 20 | Dijkstra path cost for trap tiles |
| `training` | `episodes` | 1000 | Training episodes |
| `training` | `max_steps` | 2000 | Max steps per episode (timeout) |
| `training` | `good_skip_reward` | 2.0 | Reward for correctly skipping impossible maze |
| `training` | `bad_skip_reward` | -30.0 | Penalty for skipping a winnable maze |
| `training` | `learning_rate` | 0.001 | Adam optimizer LR |
| `training` | `epsilon_start/end` | 1.0 / 0.05 | Exploration range |
| `training` | `epsilon_decay` | 0.995 | Epsilon multiplier per episode |
| `training` | `batch_size` | 128 | Replay memory batch |
| `training` | `memory_size` | 50000 | Replay memory capacity |
| `training` | `target_sync` | 10 | Target net sync interval (episodes) |
| `chart` | `update_interval` | 10 | Chart refresh frequency |
| `log` | `level` | INFO | Logging level |

## CLI Flags

| Flag | Description |
|------|-------------|
| `--pretrain` | Supervised CNN pre-training (maze classification) |
| `--train` | Start DQN reinforcement learning |
| `--play` | Play 1000 mazes with trained model (best.pt) |
| `--gpu` | Force CUDA GPU |
| `--cpu` | Force CPU |
| *(none)* | Run rule-based Dijkstra bot (1000 mazes) |

## Communication Protocol (C++ ↔ Python)

AI mode (`--ai` flag) communicates via stdin/stdout pipe:

1. **C++ → Python** (stdout): JSON state every step
   ```json
   {
        "state": "playing",
        "player": { 
            "x": 1, 
            "y": 1, 
            "hp": 3, 
            "coins": 0, 
            "totalCoins": 10, 
            "shield": false 
        },
        "maze": { 
            "width": 41, 
            "height": 25, 
            "grid": [[0,1,...], ...] 
        },
        "coins": [{
            "x": 5, 
            "y": 3
        }, ...],
        "shields": [{
            "x": 10, 
            "y": 7
        }, ...],
        "traps": [{
            "x": 8, 
            "y": 5
        }, ...],
        "exit": { 
            "x": 39, 
            "y": 23, 
            "open": false 
        },
        "moves": 0
   }
   ```

2. **Python → C++** (stdin): action string
   - `up`, `down`, `left`, `right` - movement
   - `new` - new maze (after win or skip)
   - `restart` - restart maze (after death)
   - `quit` - exit

> **Note:** The RL agent's "skip" action is handled in Python - it sends `new` to the C++ game to get a fresh maze. The skip decision is made by the neural network based on the maze layout.
