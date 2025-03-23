from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import subprocess
import traceback
import errno

import nuke
import nukescripts

# Best-effort import for type annotations
try:
    from typing import Any, List, Optional, Tuple, Union
except ImportError:
    pass


def GetDeadlineCommand():
    # type: () -> str
    deadlineBin = "" # type: str
    try:
        deadlineBin = os.environ['DEADLINE_PATH']
    except KeyError:
        #if the error is a key error it means that DEADLINE_PATH is not set. however Deadline command may be in the PATH or on OSX it could be in the file /Users/Shared/Thinkbox/DEADLINE_PATH
        pass
        
    # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
    if deadlineBin == "" and  os.path.exists( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with open( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) as f:
            deadlineBin = f.read().strip()

    deadlineCommand = os.path.join(deadlineBin, "deadlinecommand") # type: str
    
    return deadlineCommand

def GetRepositoryPath(subdir = None):
    # # type: (Optional[str]) -> str
    deadlineCommand = GetDeadlineCommand() # type: str
    
    startupinfo = None  # type: Optional[subprocess.STARTUPINFO]
    if os.name == 'nt':
        # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
        if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    args = [deadlineCommand, "-GetRepositoryPath "] # type: List[str]
    if subdir != None and subdir != "":
        args.append(subdir)
    
    attempts = 0 # type: int
    path = "" # type: Union[str, bytes]
    while attempts < 10 and path == "":
        try:
            proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo) # type: subprocess.Popen
            path, errors = proc.communicate() # type: Tuple[Union[str, bytes], Any]

            if sys.version_info[0] > 2:
                path = path.decode()

            path = path.replace("\n","").replace("\r","")
        except (OSError, IOError) as e:
            if e.errno == errno.EINTR:
                attempts += 1
                if attempts == 10:
                    nuke.message( "Failed to get results from Deadline command 10 times. Please try again" )
                continue
            raise
    return path

def main():
    # type: () -> None
    # Get the repository path
    path = GetRepositoryPath("submission/Nuke/Main") # type: str
    if path != "":
        path = path.replace( "\\", "/" )

        # Add the path to the system path
        if path not in sys.path :
            print( "Appending \"" + path + "\" to system path to import SubmitNukeToDeadline module" )
            sys.path.append( path )
        else:
            print( "\"%s\" is already in the system path" % path )

        # Import the script and call the main() function
        try:
            import SubmitNukeToDeadline
            SubmitNukeToDeadline.SubmitToDeadline( )
        except:
            print( traceback.format_exc() )
            nuke.message( traceback.format_exc() + "The SubmitNukeToDeadline.py failed with the following error message. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository.\n\n"+traceback.format_exc() )
    else:
        nuke.message( "The environment variable DEADLINE_PATH has not been set up on this machine. Please make sure that the Deadline Client has been installed on this machine." )
