from interfaces import Init, Interfaces
import traceback

try:

    Init.setup_project_base(__file__)
    
    Init.setup_modules()
 
    Interfaces.Web.run()

    Interfaces.exit()

except KeyboardInterrupt:
    pass

except:

    Interfaces.exit(
        msg = traceback.format_exc(),
        is_error = True,
        error_notify = False
    )
