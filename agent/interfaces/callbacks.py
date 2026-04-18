from .interfaces import Interfaces
import multiprocessing

class Callbacks:

    def sub_process_exit():

        Interfaces.log.sigint.warning("%s exit" % (str(multiprocessing.current_process().name)))

    def main_process_exit():

        Interfaces.log.sigint.warning("%s exit" % (str(multiprocessing.current_process().name)))

    def main_process_before_exit():
        
        if hasattr(Interfaces, "Agent") and Interfaces.Agent is not None:
           
            if Interfaces.Agent.agent_running == True:
                Interfaces.Agent.agent_running = False
                
                if hasattr(Interfaces.Agent, "process") and Interfaces.Agent.subprocess is not None:
                    
                    try:
                  
                        if Interfaces.Agent.subprocess.poll() is None:
                            
                            try:
                            
                                Interfaces.Agent.subprocess.stdin.write("quit\n")
                                Interfaces.Agent.subprocess.stdin.flush()
                           
                            except Exception:
                                pass
                           
                            try:
                             
                                Interfaces.Agent.subprocess.terminate()
                                Interfaces.Agent.subprocess.wait(timeout = 5)
                           
                            except Exception:
                                
                                try:
                                    Interfaces.Agent.subprocess.kill()
                                except Exception:
                                    pass
                    
                    except Exception:
                        pass
                    
                    for stream in [Interfaces.Agent.subprocess.stdin, Interfaces.Agent.subprocess.stdout]:
                        
                        try:
                          
                            if stream and not stream.closed:
                                stream.close()
                        
                        except Exception:
                            pass
        
        if hasattr(Interfaces, 'Web') and Interfaces.Web is not None:
            Interfaces.Web.process_manager.stop()