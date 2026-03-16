"""FLUGI Maze Game - AI Agent"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from obj.launcher import Launcher

if __name__ == "__main__":
    
    Launcher().run()
