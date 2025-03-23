from __future__ import print_function
import os
import sys
import re
import traceback
import subprocess
import ast
import threading
import time
import socket
import locale 

from subprocess import call
from threading import Thread, Lock, Timer
from time import sleep

try:
    # Nuke 11 onwards uses PySide2
    from PySide2 import QtGui, QtCore
except:
    from PySide import QtGui, QtCore

try:
    import ConfigParser
except:
    print( "Could not load ConfigParser module, sticky settings will not be loaded/saved" )

import nuke
import nukescripts

dialog = None
nukeScriptPath = None
deadlineHome = None
deadlineTemp = None
configFile = None

import DeadlineVRayGlobals as DeadlineGlobals

class NukeVrayStandaloneDialog( nukescripts.PythonPanel ):
    pools = []
    groups = []

    def __init__( self, maximumPriority, pools, secondaryPools, groups ):
        super( NukeVrayStandaloneDialog, self ).__init__( "Export V-Ray and Render", "com.thinkboxsoftware.software.deadlinevrayexportdialog" )

        # The environment variables themselves are integers. But since we can't test Nuke 6 to ensure they exist,
        # we have to use their `GlobalsEnvironment`, not a dict, get method which only accepts strings as defaults.
        self.nukeVersion = ( int( nuke.env.get( 'NukeVersionMajor', '6' ) ),
                             int( nuke.env.get( 'NukeVersionMinor', '0' ) ),
                             int( nuke.env.get( 'NukeVersionRelease', '0' ) ), )

        width = 525
        height = 520
        self.setMinimumSize( width, height )

        self.JobID = None
        # In Nuke 11.2.X, Adding a Tab_Knob and showing the dialog hard crashes Nuke. With only 1 tab, we can just remove it.
        if self.nukeVersion < ( 11, 2 ):
            self.jobTab = nuke.Tab_Knob( "DeadlineVRayExport_JobOptionsTab", "Job Options" )
            self.addKnob( self.jobTab )
        
        ##########################################################################################
        ## Job Description
        ##########################################################################################
        
        # Job Name
        self.jobName = nuke.String_Knob( "DeadlineVRayExport_JobName", "Job Name" )
        self.addKnob( self.jobName )
        self.jobName.setTooltip( "The name of your job. This is optional, and if left blank, it will default to 'Untitled'." )
        self.jobName.setValue( "Untitled" )
        
        # Comment
        self.comment = nuke.String_Knob( "DeadlineVRayExport_Comment", "Comment" )
        self.addKnob( self.comment )
        self.comment.setTooltip( "A simple description of your job. This is optional and can be left blank." )
        self.comment.setValue( "" )
        
        # Department
        self.department = nuke.String_Knob( "DeadlineVRayExport_Department", "Department" )
        self.addKnob( self.department )
        self.department.setTooltip( "The department you belong to. This is optional and can be left blank." )
        self.department.setValue( "" )
        
        # Separator
        self.separator1 = nuke.Text_Knob( "DeadlineVRayExport_Separator1", "" )
        self.addKnob( self.separator1 )
        
        ##########################################################################################
        ## Job Scheduling
        ##########################################################################################
        
        # Pool
        self.pool = nuke.Enumeration_Knob( "DeadlineVRayExport_Pool", "Pool", pools )
        self.addKnob( self.pool )
        self.pool.setTooltip( "The pool that your job will be submitted to." )
        self.pool.setValue( "none" )
        
        # Secondary Pool
        self.secondaryPool = nuke.Enumeration_Knob( "DeadlineVRayExport_SecondaryPool", "Secondary Pool", secondaryPools )
        self.addKnob( self.secondaryPool )
        self.secondaryPool.setTooltip( "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Workers." )
        self.secondaryPool.setValue( " " )
        
        # Group
        self.group = nuke.Enumeration_Knob( "DeadlineVRayExport_Group", "Group", groups )
        self.addKnob( self.group )
        self.group.setTooltip( "The group that your job will be submitted to." )
        self.group.setValue( "none" )
        
        # Priority
        self.priority = nuke.Int_Knob( "DeadlineVRayExport_Priority", "Priority" )
        self.addKnob( self.priority )
        self.priority.setTooltip( "A job can have a numeric priority ranging from 0 to " + str(maximumPriority) + ", where 0 is the lowest priority." )
        self.priority.setValue( 50 )
        
        # If the job is interruptible
        self.isInterruptible = nuke.Boolean_Knob( "DeadlineVRayExport_IsInterruptible", "Job Is Interruptible" )
        self.addKnob( self.isInterruptible )
        self.isInterruptible.setTooltip( "If true, the Job can be interrupted during rendering by a Job with higher priority." )
        self.isInterruptible.setValue( False )
        
        # Task Timeout
        self.taskTimeout = nuke.Int_Knob( "DeadlineVRayExport_TaskTimeout", "Task Timeout" )
        self.addKnob( self.taskTimeout )
        self.taskTimeout.setTooltip( "The number of minutes a Worker has to render a task for this job before it requeues it. Specify 0 for no limit." )
        self.taskTimeout.setValue( 0 )
        
        # Auto Task Timeout
        self.autoTaskTimeout = nuke.Boolean_Knob( "Deadline_AutoTaskTimeout", "Enable Auto Task Timeout" )
        self.addKnob( self.autoTaskTimeout )
        self.autoTaskTimeout.setTooltip( "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job." )
        self.autoTaskTimeout.setValue( False )
        
        # Concurrent Tasks
        self.concurrentTasks = nuke.Int_Knob( "Deadline_ConcurrentTasks", "Concurrent Tasks" )
        self.addKnob( self.concurrentTasks )
        self.concurrentTasks.setTooltip( "The number of tasks that can render concurrently on a single Worker. This is useful if the rendering application only uses one thread to render and your Workers have multiple CPUs." )
        self.concurrentTasks.setValue( 1 )
        
        # Limit Concurrent Tasks
        self.limitConcurrentTasks = nuke.Boolean_Knob( "Deadline_LimitConcurrentTasks", "Limit Tasks To Worker's Task Limit" )
        self.addKnob( self.limitConcurrentTasks )
        self.limitConcurrentTasks.setTooltip( "If you limit the tasks to a Worker's task limit, then by default, the Worker won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual Workers by an administrator." )
        self.limitConcurrentTasks.setValue( False )
        
        # Machine Limit
        self.machineLimit = nuke.Int_Knob( "Deadline_MachineLimit", "Machine Limit" )
        self.addKnob( self.machineLimit )
        self.machineLimit.setTooltip( "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit." )
        self.machineLimit.setValue( 0 )
        
        # Machine List Is A Deny List
        self.isBlacklist = nuke.Boolean_Knob( "DeadlineVRayExport_IsBlacklist", "Machine List Is A Deny List" )
        self.addKnob( self.isBlacklist )
        self.isBlacklist.setTooltip( "You can force the job to render on specific machines by using an allow list, or you can avoid specific machines by using a deny list." )
        self.isBlacklist.setValue( False )
        
        # Machine List
        self.machineList = nuke.String_Knob( "DeadlineVRayExport_MachineList", "Machine List" )
        self.addKnob( self.machineList )
        self.machineList.setTooltip( "The list of machines on the deny list or allow list." )
        self.machineList.setValue( "" )
        
        self.machineListButton = nuke.PyScript_Knob( "DeadlineVRayExport_MachineListButton", "Browse" )
        self.addKnob( self.machineListButton )
        
        # Limit Groups
        self.limitGroups = nuke.String_Knob( "DeadlineVRayExport_LimitGroups", "Limits" )
        self.addKnob( self.limitGroups )
        self.limitGroups.setTooltip( "The Limits that your job requires." )
        self.limitGroups.setValue( "" )
        
        self.limitGroupsButton = nuke.PyScript_Knob( "DeadlineVRayExport_LimitGroupsButton", "Browse" )
        self.addKnob( self.limitGroupsButton )
        
        # Dependencies
        self.dependencies = nuke.String_Knob( "Deadline_Dependencies", "Dependencies" )
        self.addKnob( self.dependencies )
        self.dependencies.setTooltip( "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering." )
        self.dependencies.setValue( "" )
        
        self.dependenciesButton = nuke.PyScript_Knob( "Deadline_DependenciesButton", "Browse" )
        self.addKnob( self.dependenciesButton )
        
        # Separator
        self.separator1 = nuke.Text_Knob( "DeadlineVRayExport_Separator1", "" )
        self.addKnob( self.separator1 )
        
        # Frame List
        self.frameListMode = nuke.Enumeration_Knob( "Deadline_FrameListMode", "Frame List", ("Global", "Input", "Custom") )
        self.addKnob( self.frameListMode )
        self.frameListMode.setTooltip( "Select the Global, Input, or Custom frame list mode." )
        self.frameListMode.setValue( "Global" )
        
        self.frameList = nuke.String_Knob( "Deadline_FrameList", "" )
        self.frameList.clearFlag(nuke.STARTLINE)
        self.addKnob( self.frameList )
        self.frameList.setTooltip( "If Custom frame list mode is selected, this is the list of frames to render." )
        self.frameList.setValue( "" )

        # Chunk Size
        self.chunkSize = nuke.Int_Knob( "Deadline_ChunkSize", "Frames Per Task" )
        self.addKnob( self.chunkSize )
        self.chunkSize.setTooltip( "This is the number of frames that will be rendered at a time for each job task." )
        self.chunkSize.setValue( 1 )
        
        self.threads = nuke.Int_Knob( "DeadlineVRayExport_Threads", "Threads" )
        self.threads.clearFlag(nuke.STARTLINE)
        self.addKnob( self.threads )
        self.threads.setTooltip( "The Number of threads that Vray will render using.  If 0 all available threads will be used." )
        self.threads.setValue( 0 )
        
        
        self.outputFilePath = nuke.File_Knob( "Deadline_OutputFile", "Output File" )
        self.addKnob( self.outputFilePath )
        self.outputFilePath.setTooltip( "The output file name for the renders." )
        self.outputFilePath.setValue( "" )
        
    def knobChanged( self, knob ):
        if knob == self.frameList:
            self.frameListMode.setValue( "Custom" )
        
        if knob == self.dependenciesButton:
            GetDependenciesFromDeadline()
            
        if knob == self.frameListMode:
            # In Custom mode, don't change anything
            if self.frameListMode.value() != "Custom":
                startFrame = nuke.Root().firstFrame()
                endFrame = nuke.Root().lastFrame()
                if self.frameListMode.value() == "Input":
                    try:
                        activeInput = nuke.activeViewer().activeInput()
                        startFrame = nuke.activeViewer().node().input(activeInput).frameRange().first()
                        endFrame = nuke.activeViewer().node().input(activeInput).frameRange().last()
                    except:
                        pass
                
                if startFrame == endFrame:
                    self.frameList.setValue( str(startFrame) )
                else:
                    self.frameList.setValue( str(startFrame) + "-" + str(endFrame) )
            
    def ShowDialog( self ):
        return nukescripts.PythonPanel.showModalDialog( self )
        
    def close(self):
        WriteStickySettings()
        return super(NukeVrayStandaloneDialog, self).close()

def GetDeadlinePath():
    deadlineBin = ""
    try:
        deadlineBin = os.environ['DEADLINE_PATH']
    except KeyError:
        #if the error is a key error it means that DEADLINE_PATH is not set. however Deadline command may be in the PATH or on OSX it could be in the file /Users/Shared/Thinkbox/DEADLINE_PATH
        pass
        
    # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
    if deadlineBin == "" and  os.path.exists( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with open( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) as f:
            deadlineBin = f.read().strip()
    
    return deadlineBin
        
def StartDeadlineMonitor():
    deadlineCommand = os.path.join( GetDeadlinePath(), "deadlinemonitor" )
            
    environment = {}
    for key in os.environ.keys():
        environment[key] = str(os.environ[key])
        
    # Need to set the PATH, cuz windows seems to load DLLs from the PATH earlier that cwd....
    if os.name == 'nt':
        deadlineCommandDir = os.path.dirname( deadlineCommand )
        if not deadlineCommandDir == "" :
            environment['PATH'] = deadlineCommandDir + os.pathsep + os.environ['PATH']
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen([deadlineMonitor], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment)
    proc.stdin.close()
    proc.stderr.close()
    proc.stdout.close()
    
def CallDeadlineCommand( arguments, hideWindow=True ):
    deadlineCommand = os.path.join( GetDeadlinePath(), "deadlinecommand" )
    
    startupinfo = None
    if hideWindow and os.name == 'nt':
        # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
        if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    environment = {}
    for key in os.environ.keys():
        environment[key] = str(os.environ[key])
        
    # Need to set the PATH, cuz windows seems to load DLLs from the PATH earlier that cwd....
    if os.name == 'nt':
        deadlineCommandDir = os.path.dirname( deadlineCommand )
        if not deadlineCommandDir == "" :
            environment['PATH'] = deadlineCommandDir + os.pathsep + os.environ['PATH']
    
    arguments.insert( 0, deadlineCommand)
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, env=environment)
    proc.stdin.close()
    proc.stderr.close()
    
    output = proc.stdout.read()
    
    return output

def GetDependenciesFromDeadline():
    global dialog
    output = CallDeadlineCommand( ["-selectdependencies", dialog.dependencies.value()], False )
    output = output.replace( "\r", "" ).replace( "\n", "" )
    if output != "Action was cancelled by user":
        dialog.dependencies.setValue( output )
        
#This will recursively find nodes of the given class (used to find write nodes, even if they're embedded in groups).  
def RecursiveFindNodes(nodeClasses, startNode):
    nodeList = []
    
    if startNode != None:
        if startNode.Class() in nodeClasses:
            nodeList = [startNode]
        elif isinstance(startNode, nuke.Group):
            for child in startNode.nodes():
                nodeList.extend( RecursiveFindNodes(nodeClasses, child) )
        
    return nodeList

def RecursiveFindNodesInPrecomp(nodeClasses, startNode):
    nodeList = []
    
    if startNode != None:
        if startNode.Class() == "Precomp":
            for child in startNode.nodes():
                nodeList.extend( RecursiveFindNodes(nodeClasses, child) )
        elif isinstance(startNode, nuke.Group):
            for child in startNode.nodes():
                nodeList.extend( RecursiveFindNodesInPrecomp(nodeClasses, child) )
    
    return nodeList

def recursiveFindWrites(node=None, group=nuke.root(), writes=None):
    if writes is None:
        writes = set()
    if node is None:
        node = nuke.selectedNode() # Let this error on purpose if no node selected
    for n in node.dependent(nuke.INPUTS | nuke.HIDDEN_INPUTS, False):
        cls = n.Class()
        if cls == 'Write':
            writes.add(n)
        elif cls == 'Group':
            writes = writes.union(recursiveFindReads(node=nuke.allNodes('Output', group=n)[0], group=n, reads=reads))
        else:
            writes = writes.union(recursiveFindReads(node=n, group=group, writes=writes))
    return list(writes)

def GetMachineListFromDeadline():
    global dialog
    output = CallDeadlineCommand( ["-selectmachinelist", dialog.machineList.value()] )
    output = output.replace( "\r", "" ).replace( "\n", "" )
    if output != "Action was cancelled by user":
        dialog.machineList.setValue( output )
    

def GetLimitGroupsFromDeadline():
    global dialog
    output = CallDeadlineCommand( ["-selectlimitgroups", dialog.limitGroups.value()] )
    output = output.replace( "\r", "" ).replace( "\n", "" )
    if output != "Action was cancelled by user":
        dialog.limitGroups.setValue( output )
        
def WriteStickySettings():
    global configFile
    global dialog
    try:
        print( "Writing sticky settings..." )
        config = ConfigParser.ConfigParser()
        config.add_section( "Sticky" )
        
        config.set( "Sticky", "FrameListMode", dialog.frameListMode.value() )
        config.set( "Sticky", "CustomFrameList", dialog.frameList.value().strip() )
        
        config.set( "Sticky", "Department", dialog.department.value() )
        config.set( "Sticky", "Pool", dialog.pool.value() )
        config.set( "Sticky", "Group", dialog.group.value() )
        config.set( "Sticky", "Priority", str( dialog.priority.value() ) )
        config.set( "Sticky", "IsBlacklist", str( dialog.isBlacklist.value() ) )
        config.set( "Sticky", "MachineList", dialog.machineList.value() )
        config.set( "Sticky", "LimitGroups", dialog.limitGroups.value() )
        config.set( "Sticky", "TaskTimeout", str(dialog.taskTimeout.value()) )
        config.set( "Sticky", "IsInterruptible", str(dialog.isInterruptible.value() ) )
        config.set( "Sticky", "Threads", str(dialog.threads.value()) )
        config.set( "Sticky", "OutputFilename", str(dialog.outputFilePath.value()) )
        config.set( "Sticky", "ChunkSize", str(dialog.chunkSize.value() ) )
        config.set( "Sticky", "MachineLimit", str( dialog.machineLimit.value() ) )
        config.set( "Sticky", "ConcurrentTasks", str( dialog.concurrentTasks.value() ) )
        config.set( "Sticky", "LimitConcurrentTasks", str( dialog.limitConcurrentTasks.value() ) )
        
        fileHandle = open( configFile, "w" )
        config.write( fileHandle )
        fileHandle.close()
        
    except:
        print( "Could not write sticky settings" )
        print( traceback.format_exc() )
    
    try:
    
        #Saves all the sticky setting to the root
        tKnob = buildKnob( "VrayStandaloneFrameListMode" , "frameListMode")
        tKnob.setValue( dialog.frameListMode.value() )
        
        tKnob = buildKnob( "VrayStandaloneCustomFrameList", "customFrameList" )
        tKnob.setValue( dialog.frameList.value().strip() )
        
        #Saves all the sticky setting to the root
        tKnob = buildKnob( "VrayStandaloneDepartment", "department" )
        tKnob.setValue( dialog.department.value() )
        
        tKnob = buildKnob( "VrayStandalonePool", "pool" )
        tKnob.setValue( dialog.pool.value() )
        
        tKnob = buildKnob( "VrayStandaloneGroup", "group" )
        tKnob.setValue( dialog.group.value() )
        
        tKnob = buildKnob( "VrayStandalonePriority", "priority" )
        tKnob.setValue( str( dialog.priority.value() ) )
        
        tKnob = buildKnob( "VrayStandaloneIsBlacklist", "isBlacklist" )
        tKnob.setValue( str( dialog.isBlacklist.value() ) )
        
        tKnob = buildKnob( "VrayStandaloneMachineList", "machineList" )
        tKnob.setValue( dialog.machineList.value() )
        
        tKnob = buildKnob( "VrayStandaloneLimitGroups", "limitGroups" )
        tKnob.setValue( dialog.limitGroups.value() )
        
        tKnob = buildKnob( "VrayStandaloneIsInterruptible", "isInterruptible" )
        tKnob.setValue(str(dialog.isInterruptible.value()))
        
        tKnob = buildKnob( "VrayStandaloneTaskTimeout", "taskTimeout" )
        tKnob.setValue( str(dialog.taskTimeout.value()) )
        
        tKnob = buildKnob( "VrayStandaloneThreads", "threads" )
        tKnob.setValue( str(dialog.threads.value()) )
        
        tKnob = buildKnob( "VrayStandaloneOutputFilename", "outputfilename" )
        tKnob.setValue(str(dialog.outputFilePath.value()))
        
        tKnob = buildKnob( "VrayStandaloneChunkSize", "chunksize" )
        tKnob.setValue( str(dialog.chunkSize.value()) )
        
        tKnob = buildKnob( "MachineLimit", "machineLimit" )
        tKnob.setValue( str( dialog.machineLimit.value() ) )
        
        tKnob = buildKnob( "ConcurrentTasks", "concurrentTasks" ) 
        tKnob.setValue( str( dialog.concurrentTasks.value() ) )
        
        tKnob = buildKnob( "LimitConcurrentTasks", "limitConcurrentTasks" )
        tKnob.setValue( str( dialog.limitConcurrentTasks.value() ) )
        
        root = nuke.Root()
        if root.modified():
            if root.name() != "Root":
                nuke.scriptSave( root.name() )
        
    except:
        print( "Could not write knob settings." )
        print( traceback.format_exc() )
        
    dialog = None
        
def buildKnob(name, abr):
    try:
        root = nuke.Root()
        if "Deadline" not in root.knobs():
            tabKnob = nuke.Tab_Knob("Deadline")
            root.addKnob(tabKnob)
        
        if name in root.knobs():
            return root.knob( name )
        else:
            tKnob = nuke.String_Knob( name, abr )
            root.addKnob ( tKnob )
            return  tKnob
    except:
        print( "Error in knob creation. " + name + " " + abr )
        
def LoadStickySettings(dialog):
    global configFile
    print( "Reading sticky settings from %s" % configFile )
    try:
        if os.path.isfile( configFile ):
            config = ConfigParser.ConfigParser()
            config.read( configFile )
            
            if config.has_section( "Sticky" ):
                if config.has_option( "Sticky", "Department" ):
                    DeadlineGlobals.initDepartment = config.get( "Sticky", "Department" )
                if config.has_option( "Sticky", "Pool" ):
                    DeadlineGlobals.initPool = config.get( "Sticky", "Pool" )
                if config.has_option( "Sticky", "Group" ):
                    DeadlineGlobals.initGroup = config.get( "Sticky", "Group" )
                if config.has_option( "Sticky", "Priority" ):
                    DeadlineGlobals.initPriority = config.getint( "Sticky", "Priority" )
                if config.has_option( "Sticky", "IsBlacklist" ):
                    DeadlineGlobals.initIsBlacklist = config.getboolean( "Sticky", "IsBlacklist" )
                if config.has_option( "Sticky", "MachineList" ):
                    DeadlineGlobals.initMachineList = config.get( "Sticky", "MachineList" )
                if config.has_option( "Sticky", "LimitGroups" ):
                    DeadlineGlobals.initLimitGroups = config.get( "Sticky", "LimitGroups" )
                if config.has_option("Sticky", "IsInterruptible"):
                    DeadlineGlobals.initIsInterruptible = config.get("Sticky", "IsInterruptible" )
                if config.has_option( "Sticky", "TaskTimeout"):
                    DeadlineGlobals.initTaskTimeout = config.getint( "Sticky", "TaskTimeout" )
                if config.has_option( "Sticky", "FrameListMode" ):
                    initFrameListMode = config.get( "Sticky", "FrameListMode" )
                if config.has_option( "Sticky", "CustomFrameList" ):
                    initCustomFrameList = config.get( "Sticky", "CustomFrameList" )
                if config.has_option( "Sticky", "ConcurrentTasks" ):
                    DeadlineGlobals.initConcurrentTasks = config.getint( "Sticky", "ConcurrentTasks" )
                if config.has_option( "Sticky", "Threads" ):
                    DeadlineGlobals.initThreads = config.getint( "Sticky", "Threads" )
                if config.has_option( "Sticky", "OutputFilename" ):
                    DeadlineGlobals.initOutputFilename = config.get( "Sticky", "OutputFilename" )
                if config.has_option( "Sticky", "ChunkSize" ):
                    DeadlineGlobals.initChunkSize = config.getint( "Sticky", "ChunkSize" )
                    
                if config.has_option( "Sticky", "MachineLimit" ):
                    DeadlineGlobals.initMachineLimit = config.getint( "Sticky", "MachineLimit" )
                if config.has_option( "Sticky", "ConcurrentTasks" ):
                    DeadlineGlobals.initConcurrentTasks = config.getint( "Sticky", "ConcurrentTasks" )
                if config.has_option( "Sticky", "LimitConcurrentTasks" ):
                    DeadlineGlobals.initLimitConcurrentTasks = config.getboolean( "Sticky", "LimitConcurrentTasks" )
                    
    except:
        print( "Could not read sticky settings" )
        print( traceback.format_exc() )
    
    try:
        root = nuke.Root()
            
        if "VrayStandaloneDepartment" in root.knobs():
            DeadlineGlobals.initDepartment = ( root.knob( "VrayStandaloneDepartment" ) ).value()
            
        if "VrayStandalonePool" in root.knobs():
            DeadlineGlobals.initPool = ( root.knob( "VrayStandalonePool" ) ).value()
            
        if "VrayStandaloneGroup" in root.knobs():
            DeadlineGlobals.initGroup = ( root.knob( "VrayStandaloneGroup" ) ).value()
            
        if "VrayStandalonePriority" in root.knobs():
            DeadlineGlobals.initPriority = int( ( root.knob( "VrayStandalonePriority" ) ).value() )
            
        if "VrayStandaloneIsBlacklist" in root.knobs():
            DeadlineGlobals.initIsBlacklist = StrToBool( ( root.knob( "VrayStandaloneIsBlacklist" ) ).value() )
            
        if "VrayStandaloneIsInterruptible" in root.knobs():
            DeadlineGlobals.initIsInterruptible = StrToBool( (root.knob( "VrayStandaloneIsInterruptible" )).value() )
        
        if "VrayStandaloneMachineList" in root.knobs():
            DeadlineGlobals.initMachineList = ( root.knob( "VrayStandaloneMachineList" ) ).value()
        
        if "VrayStandaloneLimitGroups" in root.knobs():
            DeadlineGlobals.initLimitGroups = ( root.knob( "VrayStandaloneLimitGroups" ) ).value()
        
        if "VrayStandaloneTaskTimeout" in root.knobs():
            DeadlineGlobals.initTaskTimeout = int( ( root.knob( "VrayStandaloneTaskTimeout" ) ).value() )
            
        if "VrayStandaloneFrameListMode" in root.knobs():
            initFrameListMode = ( root.knob( "VrayStandaloneFrameListMode" ) ).value() 
            
        if "VrayStandaloneCustomFrameList" in root.knobs():
            initCustomFrameList = ( root.knob( "VrayStandaloneCustomFrameList" ) ).value() 
        
        if "VrayStandaloneThreads" in root.knobs():
            DeadlineGlobals.initThreads = int( ( root.knob( "VrayStandaloneThreads" ) ).value() )
            
        if "VrayStandaloneOutputFilename" in root.knobs():
            DeadlineGlobals.initOutputFilename = ( root.knob( "VrayStandaloneOutputFilename" ) ).value() 
        
        if "VrayStandaloneChunkSize" in root.knobs():
            DeadlineGlobals.initChunkSize = int( ( root.knob( "VrayStandaloneChunkSize" ) ).value() )
            
        if "VrayStandaloneMachineLimit" in root.knobs():
                DeadlineGlobals.initMachineLimit = int( ( root.knob( "VrayStandaloneMachineLimit" ) ).value() )
                
        if "VrayStandaloneConcurrentTasks" in root.knobs():
            DeadlineGlobals.initConcurrentTasks = int( ( root.knob( "VrayStandaloneConcurrentTasks" ) ).value() )
        
        if "VrayStandaloneLimitConcurrentTasks" in root.knobs():
            DeadlineGlobals.initLimitConcurrentTasks = StrToBool( ( root.knob( "VrayStandaloneLimitConcurrentTasks" ) ).value() )
                                    
    except:
        print( "Could not read knob settings." )
        print( traceback.format_exc() )
        
def StrToBool(str):
    return str.lower() in ("yes", "true", "t", "1", "on")

def IsPathLocal( path ):
    lowerPath = path.lower()
    if lowerPath.startswith( "c:" ) or lowerPath.startswith( "d:" ) or lowerPath.startswith( "e:" ):
        return True
    return False

def IsPadded( path ):
    #Check for padding in the file
    paddingRe = re.compile( "%([0-9]+)d", re.IGNORECASE )
    if paddingRe.search( path ) != None:
        return True
    elif path.find( "#" ) > -1:
        return True
    return False

def SubmitJob( dialog, root, node, writeNode, framelist, tempJobName, jobCount ):
    
    currentCompressed = node.knob("trans_compressed").value()
    currentMeshHex = node.knob("trans_mesh_in_hex").value()
    currentOnlyExport = node.knob("trans_only_export").value()
    currentExport = node.knob("trans_export_on").value()
    currentTransformHex = node.knob("trans_transform_in_hex").value()
    
    currentFilename = node.knob( "trans_file_name" ).value()
    currentUseLimit = writeNode.knob( "use_limit" ).value()
    
    sceneFile = node.knob( "trans_file_name" ).value()
        
    node.knob("trans_compressed").setValue( True )
    node.knob("trans_mesh_in_hex").setValue( True )
    node.knob("trans_only_export").setValue( True )
    node.knob("trans_export_on").setValue( True )
    node.knob("trans_transform_in_hex").setValue( True )
    
    writeNode.knob( "use_limit" ).setValue(False)
    
    firstFrame = None
    framesRE = re.compile( "(-?[0-9]+)-(-?[0-9]+)", re.IGNORECASE )
    for frame in framelist:
        
        startFrame = 0
        endFrame = 0
        match = framesRE.search(frame)
        if match != None:
            startFrame = int( match.group( 1 ) )
            endFrame = int( match.group( 2 ) )
        else:
            startFrame = int( frame )
            endFrame = int( frame )
        if firstFrame == None:
            firstFrame = startFrame
        nuke.execute( writeNode, startFrame, endFrame )
        
    paddingRe = re.compile( "%([0-9]+)d", re.IGNORECASE )
    match =  paddingRe.search( sceneFile )
    if match != None:
        paddingLength = int( match.group(1) )
        paddedFrame = str(firstFrame)
        while len( paddedFrame ) < paddingLength:
            paddedFrame = "0"+paddedFrame
        
        sceneFile = paddingRe.sub( paddedFrame, sceneFile )
    
    batchName = dialog.jobName.value()

    # Create the submission info file (append job count since we're submitting multiple jobs at the same time in different threads)
    jobInfoFile = unicode(deadlineTemp, "utf-8") + (u"/nuke_vray_standalone_submit_info%d.job" % jobCount)
    fileHandle = open( jobInfoFile, "w" )
    fileHandle.write( "Plugin=Vray\n" )
    fileHandle.write( "Name=%s\n" % tempJobName )
    fileHandle.write( "Comment=%s\n" % dialog.comment.value() )
    fileHandle.write( "Department=%s\n" % dialog.department.value() )
    fileHandle.write( "Pool=%s\n" % dialog.pool.value() )
    if dialog.secondaryPool.value() == "":
        fileHandle.write( "SecondaryPool=\n" )
    else:
        fileHandle.write( "SecondaryPool=%s\n" % dialog.secondaryPool.value() )
    fileHandle.write( "Group=%s\n" % dialog.group.value() )
    fileHandle.write( "Priority=%s\n" % dialog.priority.value() )
    fileHandle.write( "MachineLimit=%s\n" % dialog.machineLimit.value() )
    fileHandle.write( "TaskTimeoutMinutes=%s\n" % dialog.taskTimeout.value() )
    fileHandle.write( "EnableAutoTimeout=%s\n" % dialog.autoTaskTimeout.value() )
    fileHandle.write( "ConcurrentTasks=%s\n" % dialog.concurrentTasks.value() )
    fileHandle.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % dialog.limitConcurrentTasks.value() )
    fileHandle.write( "LimitGroups=%s\n" % dialog.limitGroups.value() )
    fileHandle.write( "JobDependencies=%s\n" %  dialog.dependencies.value() )
    #fileHandle.write( "OnJobComplete=%s\n" % dialog.onComplete.value() )
    #fileHandle.write( "ForceReloadPlugin=%s\n" % dialog.reloadPlugin.value() )
    fileHandle.write( "Frames=%s\n" % dialog.frameList.value() )
    fileHandle.write( "ChunkSize=%s\n" % dialog.chunkSize.value() )
    fileHandle.close()
    
    pluginInfoFile = unicode(deadlineTemp, "utf-8") + (u"/nuke_vray_standalone_plugin_info%d.job" % jobCount)
    fileHandle = open( pluginInfoFile, "w" )
    fileHandle.write( "InputFilename=%s\n" % sceneFile )
    fileHandle.write( "Threads=%s\n" % dialog.threads.value() )
    fileHandle.write( "OutputFilename=%s\n" % dialog.outputFilePath.value() )
    fileHandle.write( "SeparateFilesPerFrame=True\n" )
    fileHandle.write( "CommandLineOptions=\n" )
    fileHandle.close()
    
    args = []
    args.append( jobInfoFile.encode(locale.getpreferredencoding() ) )
    args.append( pluginInfoFile.encode(locale.getpreferredencoding() ) )
    
    tempResults = CallDeadlineCommand( args )
    
    node.knob("trans_compressed").setValue( currentCompressed )
    node.knob("trans_mesh_in_hex").setValue( currentMeshHex )
    node.knob("trans_only_export").setValue( currentOnlyExport )
    node.knob("trans_export_on").setValue( currentExport )
    node.knob("trans_transform_in_hex").setValue( currentTransformHex )
    writeNode.knobs()["use_limit"].setValue(currentUseLimit)
    
    return tempResults

    
def SubmitToDeadline( currNukeScriptPath ):
    try:
        global dialog
        global nukeScriptPath
        global deadlineHome
        global deadlineTemp
        global configFile
        
        noRoot = False
        # If the Nuke script hasn't been saved, its name will be 'Root' instead of the file name.
        if nuke.Root().name() == "Root":
            noRoot = True
            nuke.message( "The Nuke script must be saved before it can be submitted to Deadline." )
            return
            
        # Add the current nuke script path to the system path.
        nukeScriptPath = currNukeScriptPath
        sys.path.append( nukeScriptPath )
        
        # Get the current user Deadline home directory, which we'll use to store settings and temp files.
        deadlineHome = CallDeadlineCommand( ["-GetCurrentUserHomeDirectory",] )
        
        deadlineHome = deadlineHome.replace( "\n", "" ).replace( "\r", "" )
        deadlineSettings = deadlineHome + "/settings"
        deadlineTemp = deadlineHome + "/temp"
        
        nodeClasses = [ "VRayRenderer" ]
        VRayRenderNodes = RecursiveFindNodes( nodeClasses, nuke.Root() )
        
        print( "Found a total of %d VRay Render Nodes" % len( VRayRenderNodes ) )
        if len( VRayRenderNodes ) == 0:
            nuke.message( "Error: No Vray Render Nodes in the current scene." )
            return

        outputCount = 0
        warningMessages = ""
        errorMessages = ""
        for node in VRayRenderNodes:            
            # Need at least one write node that is enabled, and not set to read in as well.
            if not node.knob( 'disable' ).value():
                outputCount = outputCount + 1
                
                filename = node.knob( "trans_file_name" ).value()
                
                if filename == "":
                    warningMessages = warningMessages + "No output path for vray render node '" + node.name() + "' is defined\n\n"
                else:
                    if IsPathLocal( filename ):
                        warningMessages = warningMessages + "Output path for vray render node '" + node.name() + "' is local:\n" + filename + "\n\n"
                    if not IsPadded( os.path.basename( filename ) ):
                        warningMessages = warningMessages + "Output path for vray render node '" + node.name() + "' is not padded:\n" + filename + "\n\n"

                writes = recursiveFindWrites( node )
                if not len( writes ) == 1:
                    warningMessages = warningMessages + "The Vray Render Node '" + node.name() + "' is not connected to a write node.:\n" + filename + "\n\n"

        #if outPut
        
        
        # If there are any warning messages, show them to the user.
        if warningMessages != "":
            warningMessages = warningMessages + "Do you still wish to submit this job to Deadline?"
            answer = nuke.ask( warningMessages )
            if not answer:
                return

        #writeNodes = recursiveFindWrites( VRayRenderNodes[0] )

        configFile = deadlineSettings + "/nuke_vray_standalone_submission.ini"
        
        # Run the sanity check script if it exists, which can be used to set some initial values.
        sanityCheckFile = nukeScriptPath + "/CustomSanityChecks.py"
        if os.path.isfile( sanityCheckFile ):
            print( "Running sanity check script: " + sanityCheckFile )
            try:
                import CustomSanityChecks
                sanityResult = CustomSanityChecks.RunSanityCheck()
                if not sanityResult:
                    print( "Sanity check returned false, exiting" )
                    return
            except:
                print( "Could not run CustomSanityChecks.py script" )
                print( traceback.format_exc() )
        
        # Get the maximum priority.
        try:
            output = CallDeadlineCommand( ["-getmaximumpriority",] )
            maximumPriority = int(output)
        except:
            maximumPriority = 100
        
        # Get the pools.
        output = CallDeadlineCommand( ["-pools",] )
        pools = output.splitlines()
        
        secondaryPools = []
        secondaryPools.append(" ")
        for currPool in pools:
            secondaryPools.append(currPool)
        
        # Get the groups.
        output = CallDeadlineCommand( ["-groups",] )
        groups = output.splitlines()
        
        initCustomFrameList = None
        
        # DeadlineFRGlobals contains initial values for the submission dialog. These can be modified
        # by an external sanity check script.
        if noRoot:
            DeadlineGlobals.initJobName = "Untitled"
        else:
            DeadlineGlobals.initJobName = os.path.basename( nuke.Root().name() )
        
        
        DeadlineGlobals.initDepartment = ""
        DeadlineGlobals.initPool = "none"
        DeadlineGlobals.initGroup = "none"
        DeadlineGlobals.initPriority = 50
        DeadlineGlobals.initTaskTimeout = 0
        DeadlineGlobals.initIsBlacklist = False
        DeadlineGlobals.initMachineList = ""
        DeadlineGlobals.initLimitGroups = ""
        DeadlineGlobals.initIsInterruptible = False
        DeadlineGlobals.initDependencies = ""
        
        DeadlineGlobals.initMachineLimit = 0
        DeadlineGlobals.initAutoTaskTimeout = False
        DeadlineGlobals.initConcurrentTasks = 1
        DeadlineGlobals.initLimitConcurrentTasks = True
        
        initFrameListMode = "Global"
        initCustomFrameList = ""
        
        DeadlineGlobals.initThreads = 0
        DeadlineGlobals.initOutputFilename = ""
        DeadlineGlobals.initChunkSize = 1
        
        dialog = NukeVrayStandaloneDialog(maximumPriority, pools, secondaryPools, groups, )
        LoadStickySettings(dialog)
                
        dialog.jobName.setValue( DeadlineGlobals.initJobName )
        dialog.department.setValue( DeadlineGlobals.initDepartment )
        dialog.pool.setValue( DeadlineGlobals.initPool )
        dialog.group.setValue( DeadlineGlobals.initGroup )
        dialog.priority.setValue( DeadlineGlobals.initPriority )
        dialog.taskTimeout.setValue( DeadlineGlobals.initTaskTimeout )
        dialog.isBlacklist.setValue( DeadlineGlobals.initIsBlacklist )
        dialog.machineList.setValue( DeadlineGlobals.initMachineList )
        dialog.limitGroups.setValue( DeadlineGlobals.initLimitGroups )
        dialog.isInterruptible.setValue( DeadlineGlobals.initIsInterruptible )
        dialog.threads.setValue( DeadlineGlobals.initThreads )
        dialog.outputFilePath.setValue( DeadlineGlobals.initOutputFilename )
        dialog.chunkSize.setValue( DeadlineGlobals.initChunkSize )
        dialog.dependencies.setValue( DeadlineGlobals.initDependencies )
        dialog.machineLimit.setValue( DeadlineGlobals.initMachineLimit )
        dialog.autoTaskTimeout.setValue( DeadlineGlobals.initAutoTaskTimeout )
        dialog.concurrentTasks.setValue( DeadlineGlobals.initConcurrentTasks )
        dialog.limitConcurrentTasks.setValue( DeadlineGlobals.initLimitConcurrentTasks )
        
        
        if initFrameListMode != "Custom":
            startFrame = nuke.Root().firstFrame()
            endFrame = nuke.Root().lastFrame()
            if initFrameListMode == "Input":
                try:
                    activeInput = nuke.activeViewer().activeInput()
                    startFrame = nuke.activeViewer().node().input(activeInput).frameRange().first()
                    endFrame = nuke.activeViewer().node().input(activeInput).frameRange().last()
                except:
                    pass
            
            if startFrame == endFrame:
                DeadlineGlobals.initFrameList = str(startFrame)
            else:
                DeadlineGlobals.initFrameList = str(startFrame) + "-" + str(endFrame)
        else:
            if DeadlineGlobals.initCustomFrameList == None or DeadlineGlobals.initCustomFrameList.strip() == "":
                startFrame = nuke.Root().firstFrame()
                endFrame = nuke.Root().lastFrame()
                if startFrame == endFrame:
                    DeadlineGlobals.initFrameList = str(startFrame)
                else:
                    DeadlineGlobals.initFrameList = str(startFrame) + "-" + str(endFrame)
            else:
                DeadlineGlobals.initFrameList = DeadlineGlobals.initCustomFrameList.strip()
        
        dialog.frameListMode.setValue( initFrameListMode )
        dialog.frameList.setValue( DeadlineGlobals.initFrameList )
                
        success = False
        while not success:
            success = dialog.ShowDialog()
            if not success:
                return
        
            errorMessages = ""
            warningMessages = ""
            
            # Check that frame range is valid.
            if dialog.frameList.value().strip() == "":
                errorMessages = errorMessages + "No frame list has been specified.\n\n"
                
            # Alert the user of any errors.
            if errorMessages != "":
                errorMessages = errorMessages + "Please fix these issues and submit again."
                nuke.message( errorMessages )
                success = False
            
        tempJobName = dialog.jobName.value()
        tempFrameList = dialog.frameList.value().strip()
        tempChunkSize = dialog.chunkSize.value()
        
        submitCounter = 0
        parsedFrames = CallDeadlineCommand( ["-ParseFrameList",tempFrameList ] )
        parsedFrames = parsedFrames.strip().split(",")
        for node in VRayRenderNodes:
            if not node.knob( 'disable' ).value():
                writes = recursiveFindWrites( node )
                if len( writes ) == 1:
                    writeNode = writes[ 0 ]
                    SubmitJob( dialog, nuke.Root(), node, writeNode, parsedFrames, ( tempJobName+" - "+node.name()), submitCounter )
                    submitCounter += 1
                    #def SubmitJob( dialog, root, node, writeNode, framelist, tempJobName ):
            
            
        #Save sticky settings
        WriteStickySettings( )
         
        
    except:
        nuke.message(traceback.format_exc())