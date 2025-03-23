import nuke
import DeadlineGlobals

def RunSanityCheck():
    DeadlineGlobals.initPriority = 50
    DeadlineGlobals.initConcurrentTasks = 4
    DeadlineGlobals.initPool = "nuke"
    DeadlineGlobals.initThreads = 0
    DeadlineGlobals.initReloadPlugin = 1
    DeadlineGlobals.initSeparateJobs = 1
    DeadlineGlobals.initSeparateJobDependencies = 1
    DeadlineGlobals.initSelectedOnly = 1
    DeadlineGlobals.initSubmitScene = 1
    DeadlineGlobals.initContinueOnError = 1
    DeadlineGlobals.initUseNukeX = 0
    DeadlineGlobals.initUseNodeRange = 1

    return True