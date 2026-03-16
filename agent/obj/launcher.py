import sys
import logging

from config import Config

class _ColoredFormatter(logging.Formatter):

    _colors = {
        logging.DEBUG:    "\033[34m",
        logging.INFO:     "\033[37m",
        logging.WARNING:  "\033[33m",
        logging.ERROR:    "\033[31m",
        logging.CRITICAL: "\033[1;31m",
    }
    _reset = "\033[0m"

    def format(self, record):
        
        color = self._colors.get(record.levelno, self._reset)
        msg = super().format(record)
        
        return "%s%s%s" % (color, msg, self._reset)


class Launcher:

    _modes = {
        "--train": "_train",
        "--play":  "_play",
        "--pretrain": "_pretrain",
    }

    def __init__(self):
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self._mode = self._resolve_mode()
        self._device = self._resolve_device()

    def run(self):
        
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_ColoredFormatter(Config.log.format))
        
        logging.root.setLevel(getattr(logging, Config.log.level))
        logging.root.addHandler(handler)

        for lib in ("matplotlib", "PIL", "torch", "numpy"):
            
            logging.getLogger(lib).setLevel(logging.WARNING)
        
        self.log.info("starting in %s mode" % (self._mode))
        
        getattr(self, self._modes.get(self._mode, "_agent"))()

    def _resolve_mode(self) -> str:
        
        for arg in sys.argv:
            
            if arg in self._modes:
                return arg
            
        return "--agent"

    def _resolve_device(self) -> str:
        
        for arg in sys.argv:
            
            if arg == "--cpu":
                return "cpu"
            
            if arg == "--gpu":
                return "gpu"
        
        return "auto"

    def _train(self):
        
        from training.trainer import Trainer

        trainer = Trainer(self._device)
        trainer.train()

    def _pretrain(self):
        
        from training.pretrain import Pretrainer

        pretrainer = Pretrainer(self._device)
        pretrainer.run()

    def _play(self):
        
        from obj.rl_player import RLPlayer

        player = RLPlayer()
        player.run()

    def _agent(self):
        
        from obj.agent import Agent

        agent = Agent()
        agent.run()
