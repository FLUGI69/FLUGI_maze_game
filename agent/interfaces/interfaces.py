from ProjectBase import ProjectBase, Logger, loglevel
from config import Config
import typing as t

class Interfaces(ProjectBase):

    class config(Config): pass

    class log(ProjectBase.log):

        class Dashboard(Logger):
            level = loglevel.TRACE
            
            class MazeAgent(Logger):
                level = loglevel.TRACE

        class process_manager(Logger):
            level = loglevel.DEBUG

    if t.TYPE_CHECKING:
        
        from utils.agent import Agent
        class agent(Agent): pass 
        
    if t.TYPE_CHECKING:

        from utils.web import Web
        class web(Web): pass