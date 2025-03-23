# -- coding: utf-8 --
from __future__ import print_function
import json
import locale
import os
import re
import subprocess
import sys
import threading
import traceback

try:
    import ConfigParser as configparser # Python 2
except ImportError:
    import configparser # type: ignore # Python 3

try:
    import hiero
    from hiero import core as hcore
except ImportError:
    pass

import nuke
import nukescripts

# DeadlineGlobals contains initial values for the submission dialog. These can be modified
# by an external sanity scheck script.
import DeadlineGlobals

# Best-effort import for type annotations
try:
    from typing import Any, Dict, List, Optional, Tuple, Union
except ImportError:
    pass

dialog = None # type: Optional[DeadlineDialog]
submissionInfo = {} # type: Dict
FormatsDict = {} # type: Dict
dlRenderModes = [ "Use Scene Settings", "Render Full Resolution", "Render using Proxies" ] # type: List[str]
dlNonAssetClasses = ["Write","DeepWrite","WriteGeo"] # type: List[str]

class DeadlineDialog(nukescripts.PythonPanel):
    pools = [] # type: List[str]
    groups = [] # type: List[str]
        
    def __init__(self, maximumPriority, pools, secondaryPools, groups):
        super(DeadlineDialog, self).__init__("Submit To Deadline", "com.thinkboxsoftware.software.deadlinedialog")

        self.nukeVersion = DeadlineDialog.getNukeVersion() # type: Tuple[int]

        width = 625 # type: int
        height = 790 # type: int #Nuke v6 or earlier UI height
        if self.nukeVersion >= (7,): # GPU rendering UI
            height += 35
        if self.nukeVersion >= (9,): # Performance Profiler UI
            height += 40
        if self.nukeVersion >= (11, 2,): # Tab removal in 11.2.X
            height -= 40
        self.setMinimumSize(width, height)

        self.integrationKVPs = {} # type: Dict

        # In Nuke 11.2.X, Adding a Tab_Knob and showing the dialog hard crashes Nuke. With only 1 tab, we can just remove it.
        if self.nukeVersion < (11, 2,):
            jobTab = nuke.Tab_Knob("Deadline_JobOptionsTab", "Job Options")
            self.addKnob(jobTab)

        ##########################################################################################
        ## Job Description
        ##########################################################################################
        
        # Job Name
        self.jobName = nuke.String_Knob("Deadline_JobName", "Job Name")
        self.addKnob(self.jobName)
        self.jobName.setTooltip("The name of your job. This is optional, and if left blank, it will default to 'Untitled'.")
        self.jobName.setValue("Untitled")
        
        # Comment
        self.comment = nuke.String_Knob("Deadline_Comment", "Comment")
        self.addKnob(self.comment)
        self.comment.setTooltip("A simple description of your job. This is optional and can be left blank.")
        self.comment.setValue("")
        
        # Department
        self.department = nuke.String_Knob("Deadline_Department", "Department")
        self.addKnob(self.department)
        self.department.setTooltip("The department you belong to. This is optional and can be left blank.")
        self.department.setValue("")
        
        # Separator
        self.separator1 = nuke.Text_Knob("Deadline_Separator1", "")
        self.addKnob(self.separator1)
        
        ##########################################################################################
        ## Job Scheduling
        ##########################################################################################
        
        # Pool
        self.pool = nuke.Enumeration_Knob("Deadline_Pool", "Pool", pools)
        self.addKnob(self.pool)
        self.pool.setTooltip("The pool that your job will be submitted to.")
        self.pool.setValue("none")
        
        # Secondary Pool
        self.secondaryPool = nuke.Enumeration_Knob("Deadline_SecondaryPool", "Secondary Pool", secondaryPools)
        self.addKnob(self.secondaryPool)
        self.secondaryPool.setTooltip("The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Workers.")
        self.secondaryPool.setValue(" ")
        
        # Group
        self.group = nuke.Enumeration_Knob("Deadline_Group", "Group", groups)
        self.addKnob(self.group)
        self.group.setTooltip("The group that your job will be submitted to.")
        self.group.setValue("none")
        
        # Priority
        self.priority = nuke.Int_Knob("Deadline_Priority", "Priority")
        self.addKnob(self.priority)
        self.priority.setTooltip("A job can have a numeric priority ranging from 0 to " + str(maximumPriority) + ", where 0 is the lowest priority.")
        self.priority.setValue(50)
        
        # Task Timeout
        self.taskTimeout = nuke.Int_Knob("Deadline_TaskTimeout", "Task Timeout")
        self.addKnob(self.taskTimeout)
        self.taskTimeout.setTooltip("The number of minutes a Worker has to render a task for this job before it requeues it. Specify 0 for no limit.")
        self.taskTimeout.setValue(0)
        
        # Auto Task Timeout
        self.autoTaskTimeout = nuke.Boolean_Knob("Deadline_AutoTaskTimeout", "Enable Auto Task Timeout")
        self.addKnob(self.autoTaskTimeout)
        self.autoTaskTimeout.setTooltip("If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job.")
        self.autoTaskTimeout.setValue(False)
        
        # Concurrent Tasks
        self.concurrentTasks = nuke.Int_Knob("Deadline_ConcurrentTasks", "Concurrent Tasks")
        self.addKnob(self.concurrentTasks)
        self.concurrentTasks.setTooltip("The number of tasks that can render concurrently on a single Worker. This is useful if the rendering application only uses one thread to render and your Workers have multiple CPUs.")
        self.concurrentTasks.setValue(1)
        
        # Limit Concurrent Tasks
        self.limitConcurrentTasks = nuke.Boolean_Knob("Deadline_LimitConcurrentTasks", "Limit Tasks To Worker's Task Limit")
        self.addKnob(self.limitConcurrentTasks)
        self.limitConcurrentTasks.setTooltip("If you limit the tasks to a Worker's task limit, then by default, the Worker won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual Workers by an administrator.")
        self.limitConcurrentTasks.setValue(False)
        
        # Machine Limit
        self.machineLimit = nuke.Int_Knob("Deadline_MachineLimit", "Machine Limit")
        self.addKnob(self.machineLimit)
        self.machineLimit.setTooltip("Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.")
        self.machineLimit.setValue(0)
        
        # Machine List Is A Deny List
        self.isBlacklist = nuke.Boolean_Knob("Deadline_IsBlacklist", "Machine List Is A Deny List")
        self.addKnob(self.isBlacklist)
        self.isBlacklist.setTooltip("You can force the job to render on specific machines by using an allow list, or you can avoid specific machines by using a deny list.")
        self.isBlacklist.setValue(False)
        
        # Machine List
        self.machineList = nuke.String_Knob("Deadline_MachineList", "Machine List")
        self.addKnob(self.machineList)
        self.machineList.setTooltip("The list of machines on the deny list or allow list.")
        self.machineList.setValue("")
        
        self.machineListButton = nuke.PyScript_Knob("Deadline_MachineListButton", "Browse")
        self.addKnob(self.machineListButton)
        
        # Limit Groups
        self.limitGroups = nuke.String_Knob("Deadline_LimitGroups", "Limits")
        self.addKnob(self.limitGroups)
        self.limitGroups.setTooltip("The Limits that your job requires.")
        self.limitGroups.setValue("")
        
        self.limitGroupsButton = nuke.PyScript_Knob("Deadline_LimitGroupsButton", "Browse")
        self.addKnob(self.limitGroupsButton)
        
        # Dependencies
        self.dependencies = nuke.String_Knob("Deadline_Dependencies", "Dependencies")
        self.addKnob(self.dependencies)
        self.dependencies.setTooltip("Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.")
        self.dependencies.setValue("")
        
        self.dependenciesButton = nuke.PyScript_Knob("Deadline_DependenciesButton", "Browse")
        self.addKnob(self.dependenciesButton)
        
        # On Complete
        self.onComplete = nuke.Enumeration_Knob("Deadline_OnComplete", "On Job Complete", ("Nothing", "Archive", "Delete"))
        self.addKnob(self.onComplete)
        self.onComplete.setTooltip("If desired, you can automatically archive or delete the job when it completes.")
        self.onComplete.setValue("Nothing")
        
        # Submit Suspended
        self.submitSuspended = nuke.Boolean_Knob("Deadline_SubmitSuspended", "Submit Job As Suspended")
        self.addKnob(self.submitSuspended)
        self.submitSuspended.setTooltip("If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render.")
        self.submitSuspended.setValue(False)
        
        # Separator
        self.separator1 = nuke.Text_Knob("Deadline_Separator2", "")
        self.addKnob(self.separator1)
        
        ##########################################################################################
        ## Nuke Options
        ##########################################################################################
        
        # Frame List
        self.frameListMode = nuke.Enumeration_Knob("Deadline_FrameListMode", "Frame List", ("Global", "Input", "Custom"))
        self.addKnob(self.frameListMode)
        self.frameListMode.setTooltip("Select the Global, Input, or Custom frame list mode.")
        self.frameListMode.setValue("Global")
        
        self.frameList = nuke.String_Knob("Deadline_FrameList", "")
        self.frameList.clearFlag(nuke.STARTLINE)
        self.addKnob(self.frameList)
        self.frameList.setTooltip("If Custom frame list mode is selected, this is the list of frames to render.")
        self.frameList.setValue("")
        
        # Chunk Size
        self.chunkSize = nuke.Int_Knob("Deadline_ChunkSize", "Frames Per Task")
        self.addKnob(self.chunkSize)
        self.chunkSize.setTooltip("This is the number of frames that will be rendered at a time for each job task.")
        self.chunkSize.setValue(10)
        
        # NukeX
        self.useNukeX = nuke.Boolean_Knob("Deadline_UseNukeX", "Render With NukeX")
        self.addKnob(self.useNukeX)
        self.useNukeX.setTooltip("If checked, NukeX will be used instead of just Nuke.")
        self.useNukeX.setValue(False)
        
        # Batch Mode
        self.batchMode = nuke.Boolean_Knob("Deadline_BatchMode", "Use Batch Mode")
        self.addKnob(self.batchMode)
        self.batchMode.setTooltip("This uses the Nuke plugin's Batch Mode. It keeps the Nuke script loaded in memory between frames, which reduces the overhead of rendering the job.")
        self.batchMode.setValue(True)
        
        # Threads
        self.threads = nuke.Int_Knob("Deadline_Threads", "Render Threads")
        self.addKnob(self.threads)
        self.threads.setTooltip("The number of threads to use for rendering. Set to 0 to have Nuke automatically determine the optimal thread count.")
        self.threads.setValue(0)
        
        # Choose GPU
        self.chooseGpu = nuke.Int_Knob("Deadline_ChooseGpu", "GPU Override")
        if self.nukeVersion >= (8,):
            self.addKnob(self.chooseGpu)
        self.chooseGpu.setTooltip("The GPU to use when rendering.")
        self.chooseGpu.setValue(0)
        self.chooseGpu.setEnabled(False)
        
        self.useSpecificGpu  = nuke.Boolean_Knob("Deadline_UseSpecificGpu", "Use Specific GPU Override")
        if self.nukeVersion >= (8,):
            self.addKnob(self.useSpecificGpu)
        self.useSpecificGpu.setTooltip("If enabled the specified GPU Index will be used for all Workers. Otherwise each Worker will use it's overrides.")
        self.useSpecificGpu.setValue(False)
        self.useSpecificGpu.setEnabled(False)
        
        # Use GPU
        self.useGpu = nuke.Boolean_Knob("Deadline_UseGpu", "Use The GPU For Rendering")
        if self.nukeVersion >= (7,):
            self.addKnob(self.useGpu)
        self.useGpu.setTooltip("If Nuke should also use the GPU for rendering.")
        self.useGpu.setValue(False)

        # Render Mode
        self.renderMode = nuke.Enumeration_Knob("Deadline_RenderMode", "Render Mode", dlRenderModes)
        self.addKnob(self.renderMode)
        self.renderMode.setTooltip("The mode to render with.")
        self.renderMode.setValue(dlRenderModes[0])
        
        # Memory Usage
        self.memoryUsage = nuke.Int_Knob("Deadline_MemoryUsage", "Maximum RAM Usage")
        self.memoryUsage.setFlag(nuke.STARTLINE)
        self.addKnob(self.memoryUsage)
        self.memoryUsage.setTooltip("The maximum RAM usage (in MB) to be used for rendering. Set to 0 to not enforce a maximum amount of RAM.")
        self.memoryUsage.setValue(0)
        
        # Enforce Write Node Render Order
        self.enforceRenderOrder = nuke.Boolean_Knob("Deadline_EnforceRenderOrder", "Enforce Write Node Render Order")
        self.addKnob(self.enforceRenderOrder)
        self.enforceRenderOrder.setTooltip("Forces Nuke to obey the render order of Write nodes.")
        self.enforceRenderOrder.setValue(False)
        
        # Stack Size
        self.stackSize = nuke.Int_Knob("Deadline_StackSize", "Minimum Stack Size")
        self.addKnob(self.stackSize)
        self.stackSize.setTooltip("The minimum stack size (in MB) to be used for rendering. Set to 0 to not enforce a minimum stack size.")
        self.stackSize.setValue(0)
        
        # Continue On Error
        self.continueOnError = nuke.Boolean_Knob("Deadline_ContinueOnError", "Continue On Error")
        self.addKnob(self.continueOnError)
        self.continueOnError.setTooltip("Enable to allow Nuke to continue rendering if it encounters an error.")
        self.continueOnError.setValue(False)

        # Submit Scene
        self.submitScene = nuke.Boolean_Knob("Deadline_SubmitScene", "Submit Nuke Script File With Job")
        self.addKnob(self.submitScene)
        self.submitScene.setTooltip("If this option is enabled, the Nuke script file will be submitted with the job, and then copied locally to the Worker machine during rendering.")
        self.submitScene.setValue(False)

        # Performance Profiler
        self.performanceProfiler = nuke.Boolean_Knob("Deadline_PerformanceProfiler", "Use Performance Profiler")
        self.performanceProfiler.setFlag(nuke.STARTLINE)
        if self.nukeVersion >= (9,):
            self.addKnob(self.performanceProfiler)
        self.performanceProfiler.setTooltip("If checked, Nuke will profile the performance of the Nuke script whilst rendering and create a *.xml file per task for later analysis.")
        self.performanceProfiler.setValue(False)
        
        #Reload Plugin Between Task
        self.reloadPlugin = nuke.Boolean_Knob("Deadline_ReloadPlugin", "Reload Plugin Between Tasks")
        self.addKnob(self.reloadPlugin)
        self.reloadPlugin.setTooltip("If checked, Nuke will force all memory to be released before starting the next task, but this can increase the overhead time between tasks.")
        self.reloadPlugin.setValue(False)

        # Performance Profiler Path
        self.performanceProfilerPath = nuke.File_Knob("Deadline_PerformanceProfilerDir", "XML Directory")
        if self.nukeVersion >= (9,):
            self.addKnob(self.performanceProfilerPath)
        self.performanceProfilerPath.setTooltip("The directory on the network where the performance profile *.xml files will be saved.")
        self.performanceProfilerPath.setValue("")
        self.performanceProfilerPath.setEnabled(False)

        # Views
        self.chooseViewsToRender = nuke.Boolean_Knob("Deadline_ChooseViewsToRender", "Choose Views To Render")
        self.chooseViewsToRender.setFlag(nuke.STARTLINE)
        self.addKnob(self.chooseViewsToRender)
        self.chooseViewsToRender.setTooltip("Choose the view(s) you wish to render. This is optional.")

        currentViews = nuke.views()
        self.viewToRenderKnobs = [] # type: Dict
        for x, v in enumerate(currentViews):
            currKnob = nuke.Boolean_Knob(('Deadline_ViewToRender_%d' % x), v)
            currKnob.setFlag(0x1000)
            self.viewToRenderKnobs.append((currKnob, v))
            self.addKnob(currKnob)
            currKnob.setValue(True)
            currKnob.setVisible(False) # Hide for now until the checkbox above is enabled.

        # Separator
        self.separator1 = nuke.Text_Knob("Deadline_Separator3", "")
        self.addKnob(self.separator1)
        
        # Separate Jobs
        self.separateJobs = nuke.Boolean_Knob("Deadline_SeparateJobs", "Submit Write Nodes As Separate Jobs")
        self.addKnob(self.separateJobs)
        self.separateJobs.setTooltip("Enable to submit each write node to Deadline as a separate job.")
        self.separateJobs.setValue(False)
        
        # Use Node's Frame List
        self.useNodeRange = nuke.Boolean_Knob("Deadline_UseNodeRange", "Use Node's Frame List")
        self.addKnob(self.useNodeRange)
        self.useNodeRange.setTooltip("If submitting each write node as a separate job, enable this to pull the frame range from the write node, instead of using the global frame range.")
        self.useNodeRange.setValue(True)
        
        #Separate Job Dependencies
        self.separateJobDependencies = nuke.Boolean_Knob("Deadline_SeparateJobDependencies", "Set Dependencies Based on Write Node Render Order")
        self.separateJobDependencies.setFlag(nuke.STARTLINE)
        self.addKnob(self.separateJobDependencies)
        self.separateJobDependencies.setTooltip("Enable each separate job to be dependent on the previous job.")
        self.separateJobDependencies.setValue(False)
        
        # Separate Tasks
        self.separateTasks = nuke.Boolean_Knob("Deadline_SeparateTasks", "Submit Write Nodes As Separate Tasks For The Same Job")
        self.separateTasks.setFlag(nuke.STARTLINE)
        self.addKnob(self.separateTasks)
        self.separateTasks.setTooltip("Enable to submit a job to Deadline where each task for the job represents a different write node, and all frames for that write node are rendered by its corresponding task.")
        self.separateTasks.setValue(False)
        
        # Only Submit Selected Nodes
        self.selectedOnly = nuke.Boolean_Knob("Deadline_SelectedOnly", "Selected Nodes Only")
        self.selectedOnly.setFlag(nuke.STARTLINE)
        self.addKnob(self.selectedOnly)
        self.selectedOnly.setTooltip("If enabled, only the selected Write nodes will be rendered.")
        self.selectedOnly.setValue(False)
        
        # Only Submit Read File Nodes
        self.readFileOnly = nuke.Boolean_Knob("Deadline_ReadFileOnly", "Nodes With 'Read File' Enabled Only")
        self.addKnob(self.readFileOnly)
        self.readFileOnly.setTooltip("If enabled, only the Write nodes that have the 'Read File' option enabled will be rendered.")
        self.readFileOnly.setValue(False)
        
        # Only Submit Selected Nodes
        self.precompFirst = nuke.Boolean_Knob("Deadline_PrecompFirst", "Render Precomp Nodes First")
        self.precompFirst.setFlag(nuke.STARTLINE)
        self.addKnob(self.precompFirst)
        self.precompFirst.setTooltip("If enabled, all write nodes in precomp nodes will be rendered before the main job.")
        self.precompFirst.setValue(False)
        
        # Only Submit Read File Nodes
        self.precompOnly = nuke.Boolean_Knob("Deadline_PrecompOnly", "Only Render Precomp Nodes")
        self.addKnob(self.precompOnly)
        self.precompOnly.setTooltip("If enabled, only the Write nodes that are in precomp nodes will be rendered.")
        self.precompOnly.setValue(False)

        # Only Submit Smart Vector Nodes
        self.smartVectorOnly = nuke.Boolean_Knob("Deadline_SmartVectorOnly", "Only Render Smart Vector Nodes")
        self.smartVectorOnly.setFlag(nuke.STARTLINE)
        self.addKnob(self.smartVectorOnly)
        self.smartVectorOnly.setTooltip("If enabled, only the Smart Vector nodes will be rendered.")
        self.smartVectorOnly.setValue(False)
        
        # Only Simulate Eddy Cache Nodes
        self.eddyCacheOnly = nuke.Boolean_Knob("Deadline_EddyCacheOnly", "Only Simulate Eddy Nodes")
        self.addKnob(self.eddyCacheOnly)
        self.eddyCacheOnly.setTooltip("If enabled, only the Eddy cache nodes will be simulated.")
        self.eddyCacheOnly.setValue(False)
        self.eddyCacheOnly.setFlag(nuke.STARTLINE)

        self.integrationButton = nuke.PyScript_Knob("Opens Pipeline Tools Dialog", "Pipeline Tools")
        self.integrationButton.setFlag(nuke.STARTLINE)
        self.addKnob(self.integrationButton)
        self.pipelineToolsLabel = nuke.Text_Knob("Pipeline tool settings that are currently set.", "")
        self.pipelineToolsLabel.clearFlag(nuke.STARTLINE)
        self.addKnob(self.pipelineToolsLabel)
        
    def IsMovieFromFormat(self, format):
        # type: (str) -> bool
        global FormatsDict
        
        return (FormatsDict[format][1] == 'movie')
        
    def knobChanged(self, knob):
        # type: (Any) -> None
        if knob == self.useGpu:
            self.useSpecificGpu.setEnabled(self.useGpu.value())
        
        if knob == self.useGpu or knob == self.useSpecificGpu:
            self.chooseGpu.setEnabled(self.useGpu.value() and self.useSpecificGpu.value())
            
        if knob == self.machineListButton:
            GetMachineListFromDeadline()
            
        if knob == self.limitGroupsButton:
            GetLimitGroupsFromDeadline()
        
        if knob == self.dependenciesButton:
            GetDependenciesFromDeadline()
        
        if knob == self.frameList:
            self.frameListMode.setValue("Custom")
        
        if knob == self.frameListMode:
            # In Custom mode, don't change anything
            if self.frameListMode.value() != "Custom":
                startFrame = nuke.Root().firstFrame() # type: int
                endFrame = nuke.Root().lastFrame() # type: int
                if self.frameListMode.value() == "Input":
                    try:
                        activeInput = nuke.activeViewer().activeInput()
                        startFrame = nuke.activeViewer().node().input(activeInput).frameRange().first()
                        endFrame = nuke.activeViewer().node().input(activeInput).frameRange().last()
                    except:
                        pass
                
                if startFrame == endFrame:
                    self.frameList.setValue(str(startFrame))
                else:
                    self.frameList.setValue(str(startFrame) + "-" + str(endFrame))
            
        if knob in (self.separateJobs, self.separateTasks):
            self.separateJobs.setEnabled(not self.separateTasks.value())
            self.separateTasks.setEnabled(not self.separateJobs.value())
            self.useNodeRange.setEnabled(self.separateTasks.value() or self.separateJobs.value())
            
            self.separateJobDependencies.setEnabled(self.separateJobs.value())
            if not self.separateJobs.value():
                self.separateJobDependencies.setValue(self.separateJobs.value())
            
            self.frameList.setEnabled(not (self.separateJobs.value() and self.useNodeRange.value()) and not self.separateTasks.value())
            self.chunkSize.setEnabled(not self.separateTasks.value())
        
        if knob in (self.precompFirst, self.precompOnly, self.smartVectorOnly, self.eddyCacheOnly, self.separateJobs, self.separateTasks):
            separateNodes = self.separateJobs.value() or self.separateTasks.value()
            
            precompOnly = self.precompOnly.value()
            precompFirst = self.precompFirst.value()
            smartVector = self.smartVectorOnly.value()
            eddyCache = self.eddyCacheOnly.value()
           
            self.precompFirst.setEnabled(not (precompOnly or smartVector or eddyCache) and separateNodes)
            self.precompOnly.setEnabled(not (precompFirst or smartVector or eddyCache) and separateNodes)
            self.smartVectorOnly.setEnabled(not (precompFirst or precompOnly or eddyCache) and separateNodes and bool(DeadlineGlobals.smartVectorNodes)) # type: ignore
            self.eddyCacheOnly.setEnabled(not (precompFirst or precompOnly or smartVector) and separateNodes)
        
        if knob == self.useNodeRange:
            self.frameListMode.setEnabled(not (self.separateJobs.value() and self.useNodeRange.value()) and not self.separateTasks.value())
            self.frameList.setEnabled(not (self.separateJobs.value() and self.useNodeRange.value()) and not self.separateTasks.value())

        if knob == self.performanceProfiler:
            self.performanceProfilerPath.setEnabled(self.performanceProfiler.value())

        if knob == self.chooseViewsToRender:
            visible = self.chooseViewsToRender.value()
            for vk in self.viewToRenderKnobs:
                vk[0].setVisible(visible)
        
        if knob == self.integrationButton:
            OpenPipelineTools()
    
    def ShowDialog(self):
        return nukescripts.PythonPanel.showModalDialog(self)

    @staticmethod
    def getNukeVersion():
        """
        Grabs the current Nuke version as a tuple of ints.
        :return: Nuke version as a tuple of ints
        """
        # The environment variables themselves are integers. But since we can't test Nuke 6 to ensure they exist,
        # we have to use their `GlobalsEnvironment`, not a dict, get method which only accepts strings as defaults.
        return (int(nuke.env.get('NukeVersionMajor', '6')),
                 int(nuke.env.get('NukeVersionMinor', '0')),
                 int(nuke.env.get('NukeVersionRelease', '0')),)
          
class DeadlineContainerDialog(DeadlineDialog):
    def __init__(self, maximumPriority, pools, secondaryPools, groups, projects, hasComp):
        # type: (int, List[str], List[str], List[str], List, bool) -> None
        super(DeadlineContainerDialog, self).__init__(maximumPriority, pools, secondaryPools, groups)
        self.projects = projects
        self.hasComp = hasComp

        if self.nukeVersion < (11, 2,):
            self.studioTab = nuke.Tab_Knob("Deadline_StudioTab", "Studio Sequence Options")
            self.addKnob(self.studioTab)
        
        #If we should submit separate jobs for each comp
        self.submitSequenceJobs = nuke.Boolean_Knob("Deadline_SubmitSequenceJobs", "Submit Jobs for Comps in Sequence")
        self.addKnob(self.submitSequenceJobs)
        self.submitSequenceJobs.setValue(False)
        self.submitSequenceJobs.setTooltip("If selected a separate job will be submitted for each comp in the sequence.")
        
        projectNames = [] # type: List[str]
        first = "" # type: str
        for project in self.projects:
            projectNames.append(str(project.name()))
        
        #The project
        if len(projectNames) > 0:
            first = str(projectNames[0])
        self.studioProject = nuke.Enumeration_Knob("Deadline_StudioProject", "Project", projectNames)
        self.addKnob(self.studioProject)
        self.studioProject.setTooltip("The Nuke Studio Project to submit the containers from.")
        self.studioProject.setValue(first)
        
        #The comps to render
        self.chooseCompsToRender = nuke.Boolean_Knob("Deadline_ChooseSequencesToRender", "Choose Sequences To Render")
        self.chooseCompsToRender.setFlag(nuke.STARTLINE)
        self.addKnob(self.chooseCompsToRender)
        self.chooseCompsToRender.setTooltip("Choose the sequence(s) you wish to render. This is optional.")

        #Get the sequences and their comps
        self.projectSequences = {} # type: Dict[str, List[str]]
        self.validSequenceNames = [] # type: List[str]
        self.validComps = {} # type: Dict[str, Dict[str, List]]
        for project in self.projects:
            self.projectSequences[project.name()] = []
            self.validComps[project.name()] = {}
            #This is the current project, grab its sequences
            sequences = project.sequences()
            for sequence in sequences:
                comps = []
                tracks = sequence.binItem().activeItem().items()
                for track in tracks:
                    items = track.items()
                    for item in items:
                        if item.isMediaPresent():
                            infos = item.source().mediaSource().fileinfos()
                            for info in infos:
                                comps.append(info)
                
                #If there are any comps saved, this is a valid sequence
                self.projectSequences[project.name()].append(sequence.name())
                self.validComps[project.name()][sequence.name()]=comps
                
        self.sequenceKnobs = []
        for pname in projectNames:
            sequences = self.projectSequences[pname]
            for x, s in enumerate(sequences):
                seqKnob = nuke.Boolean_Knob(('Deadline_Sequence_%d' % x), s)
                seqKnob.setFlag(nuke.STARTLINE)
                self.sequenceKnobs.append((seqKnob, (s,pname)))
                self.addKnob(seqKnob)
                seqKnob.setValue(True)
                seqKnob.setVisible(False)
        
    def toggledContainerMode(self):
        # type: () -> None
        self.frameListMode.setEnabled(self.hasComp and (not (self.separateJobs.value() and self.useNodeRange.value()) and not self.separateTasks.value()))
        self.chooseViewsToRender.setEnabled(self.hasComp)
        self.selectedOnly.setEnabled(self.hasComp)
        self.frameList.setEnabled(self.hasComp and (not (self.separateJobs.value() and self.useNodeRange.value()) and not self.separateTasks.value()))
        self.chunkSize.setEnabled(self.hasComp and not self.separateTasks.value())
        self.separateJobs.setEnabled(self.hasComp and not self.separateTasks.value())
        self.separateTasks.setEnabled(self.hasComp and not self.separateJobs.value())

        if self.submitSequenceJobs.value():
            self.studioProject.setEnabled(True)
            self.chooseCompsToRender.setEnabled(True)
            for sk in self.sequenceKnobs:
                sk[0].setEnabled(True)
        else:
            self.studioProject.setEnabled(False)
            self.chooseCompsToRender.setEnabled(False)
            for sk in self.sequenceKnobs:
                sk[0].setEnabled(False)
        
    def knobChanged(self, knob):
        # type: (Any) -> None
        super(DeadlineContainerDialog, self).knobChanged(knob)
        
        if knob == self.submitSequenceJobs:
            self.toggledContainerMode()
            
        if knob == self.chooseCompsToRender:
            self.populateSequences()
                
        if knob == self.studioProject:
            self.populateSequences()
            
    def populateSequences(self):
        # type: () -> None
        visible = self.chooseCompsToRender.value() # type: bool
        projectName = self.studioProject.value() # type: str
        
        for sk in self.sequenceKnobs:
            if sk[1][1] == projectName:
                sk[0].setVisible(visible)
            else:
                sk[0].setVisible(False)
            
    def ShowDialog(self):
        # type: () -> bool
        self.toggledContainerMode()
        return nukescripts.PythonPanel.showModalDialog(self)

def safeSetValue(knob, value):
    # type: (Any, Any) -> None
    if isinstance(knob,(nuke.Enumeration_Knob,nuke.String_Knob)) and sys.version_info[0] < 3 and isinstance(value, unicode):
        knob.setValue(value.encode("utf8",errors="replace"))
    else:
        knob.setValue(value)

def GetDeadlineCommand():
    # type: () -> str
    deadlineBin = "" # type: str
    try:
        deadlineBin = os.environ['DEADLINE_PATH']
    except KeyError:
        #if the error is a key error it means that DEADLINE_PATH is not set. however Deadline command may be in the PATH or on OSX it could be in the file /Users/Shared/Thinkbox/DEADLINE_PATH
        pass
        
    # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
    if deadlineBin == "" and  os.path.exists("/Users/Shared/Thinkbox/DEADLINE_PATH"):
        with open("/Users/Shared/Thinkbox/DEADLINE_PATH") as f:
            deadlineBin = f.read().strip()

    deadlineCommand = os.path.join(deadlineBin, "deadlinecommand") # type: str
    
    return deadlineCommand
        
def CallDeadlineCommand(arguments, hideWindow=True):
    # type: (List[str], bool) -> str
    deadlineCommand = GetDeadlineCommand() # type: str
    
    startupinfo = None # type: ignore # this is only a windows option
    if hideWindow and os.name == 'nt':
        # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
        if hasattr(subprocess, '_subprocess') and hasattr(subprocess._subprocess, 'STARTF_USESHOWWINDOW'): # type: ignore # this is only a windows option
            startupinfo = subprocess.STARTUPINFO() # type: ignore # this is only a windows option
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW # type: ignore # this is only a windows option
        elif hasattr(subprocess, 'STARTF_USESHOWWINDOW'):
            startupinfo = subprocess.STARTUPINFO() # type: ignore # this is only a windows option
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW # type: ignore # this is only a windows option
    
    environment = {} # type: Dict[str, str]
    for key in os.environ.keys():
        environment[key] = str(os.environ[key])
        
    # Need to set the PATH, cuz windows seems to load DLLs from the PATH earlier that cwd....
    if os.name == 'nt':
        deadlineCommandDir = os.path.dirname(deadlineCommand)
        if not deadlineCommandDir == "" :
            environment['PATH'] = deadlineCommandDir + os.pathsep + os.environ['PATH']
    
    arguments.insert(0, deadlineCommand)
    output = "" # type: Union[bytes, str]
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, env=environment)
    output, errors = proc.communicate()

    if sys.version_info[0] > 2 and type(output) is bytes:
        output = output.decode()

    return output # type: ignore

def retrievePipelineToolStatus():
    # type: () -> str
    """
    Grabs a status message from the JobWriter that indicates which pipeline tools have settings enabled for the current scene.
    Returns:
        statusMessage (str): Representing the status of the pipeline tools for the current scene.
    """
    integrationPath = submissionInfo["RepoDirs"]["submission/Integration/Main"].strip() # type: str
    jobWriterPath = os.path.join(integrationPath, "JobWriter.py") # type: str

    scenePath = nuke.root().knob('name').value() # type: str
    argArray = ["-ExecuteScript", jobWriterPath, "Nuke", "--status", "--scene-path", scenePath] # type: List[str]
    statusMessage = CallDeadlineCommand(argArray, hideWindow=False)
    return statusMessage

def updatePipelineToolStatusLabel(statusMessage):
    # type: (str) -> None
    """Perform error handling on the pipeline tool status message and set the status message.
    Arguments:
        statusMessage (str): Representing the status of the pipeline tools for the current scene.
    """
    if not statusMessage:
        raise ValueError('The status message for the pipeline tools label is not allowed to be empty.')

    if dialog is not None and statusMessage.startswith('Error'):
        dialog.pipelineToolsLabel.setValue("Pipeline Tools Error")
        print(statusMessage)
        nuke.executeInMainThread(nuke.message, "Encountered the following error with Pipeline Tools:\n\n%s" % statusMessage)
        
        dialog.pipelineToolsLabel.setValue(statusMessage.split('\n')[0])

def OpenPipelineTools():
    # type: () -> None
    """
    Launches a graphical interface for the pipeline tools, attempts to grab local project management info from the scene, and updates the
    Pipeline Tools status label indicating which project management tools are being used.
    """

    global submissionInfo

    integrationPath = submissionInfo["RepoDirs"]["submission/Integration/Main"].strip() # type: str
    scenePath = nuke.root().knob('name').value() # type: str
    integrationScript = os.path.join(integrationPath, "IntegrationUIStandAlone.py") # type: str
    argArray = ["-ExecuteScript", integrationScript, "-v", "2", "Nuke", "-d", "Shotgun", "FTrack", "NIM", "--path", scenePath] # type: List[str]
    statusMessage = CallDeadlineCommand(argArray, False) # type: str
    updatePipelineToolStatusLabel(statusMessage)

def ConcatenatePipelineSettingsToJob(jobInfoPath, batchName):
    # type: (Any, str) -> None
    """Concatenate pipeline tool settings for the scene to the .job file.
    Arguments:
        jobInfoPath (str): Path to the .job file.
        batchName (str): Value of the 'batchName' job info entry, if it is required.
    """
    global submissionInfo
    integrationPath = submissionInfo["RepoDirs"]["submission/Integration/Main"].strip() # type: str
    scenePath = nuke.root().knob('name').value() # type: str
    jobWriterPath = os.path.join(integrationPath, "JobWriter.py") # type: str
    argArray = ["-ExecuteScript", jobWriterPath, "Nuke", "--write", "--scene-path", scenePath, "--job-path",
                jobInfoPath, "--batch-name", batchName] # type: ignore # ignoring because of unicode vs string in python 2 vs 3
    CallDeadlineCommand(argArray, hideWindow=False) # type: ignore # ignoring because of unicode vs string in python 2 vs 3

def GetMachineListFromDeadline():
    # type: () -> None
    global dialog
    
    if dialog is not None:
        output = CallDeadlineCommand(["-selectmachinelist", dialog.machineList.value()], False) # type: str
        output = output.replace("\r", "").replace("\n", "")
        if output != "Action was cancelled by user":
            dialog.machineList.setValue(output)
    
def GetLimitGroupsFromDeadline():
    # type: () -> None
    global dialog
    if dialog is not None:
        output = CallDeadlineCommand(["-selectlimitgroups", dialog.limitGroups.value()], False) # type: str
        output = output.replace("\r", "").replace("\n", "")
        if output != "Action was cancelled by user":
            dialog.limitGroups.setValue(output)

def GetDependenciesFromDeadline():
     # type: () -> None
    global dialog
    if dialog is not None:
        output = CallDeadlineCommand(["-selectdependencies", dialog.dependencies.value()], False) # type: str
        output = output.replace("\r", "").replace("\n", "")
        if output != "Action was cancelled by user":
            dialog.dependencies.setValue(output)

# Checks a path to make sure it has an extension
def HasExtension(path):
    # type: (str) -> bool
    filename = os.path.basename(path) # type: str
    
    return filename.rfind(".") > -1

# Checks if path is local (c, d, or e drive).
def IsPathLocal(path):
    # type: (str) -> bool
    lowerPath = path.lower() # type: str
    return lowerPath.startswith("c:") or lowerPath.startswith("d:") or lowerPath.startswith("e:")

# Checks if the given filename ends with a movie extension
def IsMovie(path):
    # type: (str) -> bool
    lowerPath = path.lower() # type: str
    return lowerPath.endswith(".mov")

# Checks if the filename is padded (ie: \\output\path\filename_%04.tga).
def IsPadded(path):
    # type: (str) -> Optional[Any]
    #Check for padding in the file
    paddingRe = re.compile("(#+)|%(\d*)d", re.IGNORECASE)
    return paddingRe.search(path)

# Checks if the filename is padded (ie: \\output\path\filename_%04.tga).
def ReplacePadding(path):
    # type: (str) -> str
    #Check for padding in the file
    paddingRe = re.compile("%(\d*)d", re.IGNORECASE)
    paddingResults = paddingRe.search(path) # type: Optional[Any]
    if paddingResults != None:
        paddingSize = paddingResults.group(1) # type: ignore
        paddingSize = int("0" + paddingSize)
        
        padding = "#"
        while len(padding) < paddingSize:
            padding += "#"
        
        path = paddingRe.sub(padding, path, 1)
        
    return path
    
def RightReplace(s, old, new, occurrence):
    # type: (str, str, str, int) -> str
    li = s.rsplit(old, occurrence) # type: List[str]
    return new.join(li)

def StrToBool(str_):
    # type: (str) -> bool
    return str_.lower() in ("yes", "true", "t", "1", "on")

# Parses through the filename looking for the last padded pattern, replaces
# it with the correct number of #'s, and returns the new padded filename.
def GetPaddedPath(path):
    # type: (str) -> str
    # paddingRe = re.compile("%([0-9]+)d", re.IGNORECASE)
    
    # paddingMatch = paddingRe.search(path)
    # if paddingMatch != None:
        # paddingSize = int(paddingMatch.lastgroup)
        
        # padding = ""
        # while len(padding) < paddingSize:
            # padding = padding + "#"
        
        # path = paddingRe.sub(padding, path, 1)
    
    paddingRe = re.compile("([0-9]+)", re.IGNORECASE)
    
    paddingMatches = paddingRe.findall(path)
    if paddingMatches != None and len(paddingMatches) > 0:
        paddingString = paddingMatches[ len(paddingMatches) - 1 ] # type: str
        paddingSize = len(paddingString) # type: int
        
        padding = "" # type: str
        while len(padding) < paddingSize:
            padding = padding + "#"
        
        path = RightReplace(path, paddingString, padding, 1)
    
    return path
    
def buildKnob(name, abr):
    # type: (str, str) -> Any
    try:
        root = nuke.Root()
        if "Deadline" not in root.knobs():
            tabKnob = nuke.Tab_Knob("Deadline")
            root.addKnob(tabKnob)
        
        if name in root.knobs():
            return root.knob(name)
        else:
            tKnob = nuke.String_Knob(name, abr)
            root.addKnob (tKnob)
            return  tKnob
    except:
        print("Error in knob creation. " + name + " " + abr)
        
def WriteStickySettings(dialog, configFile):
    # type: (DeadlineDialog, str) -> None
    WriteMachineStickySettings(configFile)
    WriteSceneStickySettings(dialog)

def WriteMachineStickySettings(configFile):
    # type: (str) -> None
    if dialog is not None:
        try:
            print("Writing sticky settings...")
            config = configparser.ConfigParser() # type: configparser.ConfigParser
            config.add_section("Sticky")
            
            config.set("Sticky", "FrameListMode", dialog.frameListMode.value())
            config.set("Sticky", "CustomFrameList", dialog.frameList.value().strip())
            
            config.set("Sticky", "Department", dialog.department.value())
            config.set("Sticky", "Pool", dialog.pool.value())
            config.set("Sticky", "SecondaryPool", dialog.secondaryPool.value())
            config.set("Sticky", "Group", dialog.group.value())
            config.set("Sticky", "Priority", str(dialog.priority.value()))
            config.set("Sticky", "MachineLimit", str(dialog.machineLimit.value()))
            config.set("Sticky", "IsBlacklist", str(dialog.isBlacklist.value()))
            config.set("Sticky", "MachineList", dialog.machineList.value())
            config.set("Sticky", "LimitGroups", dialog.limitGroups.value())
            config.set("Sticky", "SubmitSuspended", str(dialog.submitSuspended.value()))
            config.set("Sticky", "ChunkSize", str(dialog.chunkSize.value()))
            config.set("Sticky", "ConcurrentTasks", str(dialog.concurrentTasks.value()))
            config.set("Sticky", "LimitConcurrentTasks", str(dialog.limitConcurrentTasks.value()))
            config.set("Sticky", "Threads", str(dialog.threads.value()))
            config.set("Sticky", "SubmitScene", str(dialog.submitScene.value()))
            config.set("Sticky", "BatchMode", str(dialog.batchMode.value()))
            config.set("Sticky", "ContinueOnError", str(dialog.continueOnError.value()))
            config.set("Sticky", "SeparateJobs", str(dialog.separateJobs.value()))
            config.set("Sticky", "UseNodeRange", str(dialog.useNodeRange.value()))
            config.set("Sticky", "UseGpu", str(dialog.useGpu.value()))
            config.set("Sticky", "UseSpecificGpu", str(dialog.useSpecificGpu.value()))
            config.set("Sticky", "ChooseGpu", str(dialog.chooseGpu.value()))
            config.set("Sticky", "EnforceRenderOrder", str(dialog.enforceRenderOrder.value()))
            config.set("Sticky", "RenderMode", str(dialog.renderMode.value()))
            config.set("Sticky", "PerformanceProfiler", str(dialog.performanceProfiler.value()))
            config.set("Sticky", "ReloadPlugin", str(dialog.reloadPlugin.value()))
            config.set("Sticky", "PerformanceProfilerPath", dialog.performanceProfilerPath.value())

            fileHandle = open(configFile, "w")
            config.write(fileHandle)
            fileHandle.close()
        except:
            print("Could not write sticky settings")
            print(traceback.format_exc())

def WriteSceneStickySettings(dialog):
    # type: (DeadlineDialog) -> None
    try:
        #Saves all the sticky setting to the root
        tKnob = buildKnob("FrameListMode" , "frameListMode")
        tKnob.setValue(dialog.frameListMode.value())
        
        tKnob = buildKnob("CustomFrameList", "customFrameList")
        tKnob.setValue(dialog.frameList.value().strip())
        
        tKnob = buildKnob("Department", "department")
        tKnob.setValue(dialog.department.value())
        
        tKnob = buildKnob("Pool", "pool")
        tKnob.setValue(dialog.pool.value())
        
        tKnob = buildKnob("SecondaryPool", "secondaryPool")
        tKnob.setValue(dialog.secondaryPool.value())
        
        tKnob = buildKnob("Group", "group")
        tKnob.setValue(dialog.group.value())
        
        tKnob = buildKnob("Priority", "priority")
        tKnob.setValue(str(dialog.priority.value()))
        
        tKnob = buildKnob("MachineLimit", "machineLimit")
        tKnob.setValue(str(dialog.machineLimit.value()))
        
        tKnob = buildKnob("IsBlacklist", "isBlacklist")
        tKnob.setValue(str(dialog.isBlacklist.value()))
        
        tKnob = buildKnob("MachineList", "machineList")
        tKnob.setValue(dialog.machineList.value())
        
        tKnob = buildKnob("LimitGroups", "limitGroups")
        tKnob.setValue(dialog.limitGroups.value())
        
        tKnob = buildKnob("SubmitSuspended", "submitSuspended")
        tKnob.setValue(str(dialog.submitSuspended.value()))
        
        tKnob = buildKnob("ChunkSize", "chunkSize")
        tKnob.setValue(str(dialog.chunkSize.value()))
        
        tKnob = buildKnob("ConcurrentTasks", "concurrentTasks")
        tKnob.setValue(str(dialog.concurrentTasks.value()))
        
        tKnob = buildKnob("LimitConcurrentTasks", "limitConcurrentTasks")
        tKnob.setValue(str(dialog.limitConcurrentTasks.value()))
        
        tKnob = buildKnob("Threads", "threads")
        tKnob.setValue(str(dialog.threads.value()))
        
        tKnob = buildKnob("SubmitScene", "submitScene")
        tKnob.setValue(str(dialog.submitScene.value()))
        
        tKnob = buildKnob("BatchMode", "batchMode")
        tKnob.setValue(str(dialog.batchMode.value()))
        
        tKnob = buildKnob("ContinueOnError", "continueOnError")
        tKnob.setValue(str(dialog.continueOnError.value()))

        tKnob = buildKnob("SeparateJobs", "separateJobs")
        tKnob.setValue(str(dialog.separateJobs.value()))
                        
        tKnob = buildKnob("UseNodeRange", "useNodeRange")
        tKnob.setValue(str(dialog.useNodeRange.value()))
        
        tKnob = buildKnob("UseGpu", "useGpu")
        tKnob.setValue(str(dialog.useGpu.value()))
        
        tKnob = buildKnob("UseSpecificGpu", "useSpecificGpu")
        tKnob.setValue(str(dialog.useSpecificGpu.value()))
        
        tKnob = buildKnob("ChooseGpu", "chooseGpu")
        tKnob.setValue(str(dialog.chooseGpu.value()))
        
        tKnob = buildKnob("EnforceRenderOrder", "enforceRenderOrder")
        tKnob.setValue(str(dialog.enforceRenderOrder.value()))
        
        tKnob = buildKnob("DeadlineRenderMode", "deadlineRenderMode")
        tKnob.setValue(str(dialog.renderMode.value()))
        
        tKnob = buildKnob("PerformanceProfiler", "performanceProfiler")
        tKnob.setValue(str(dialog.performanceProfiler.value()))
        
        tKnob = buildKnob("ReloadPlugin", "reloadPlugin")
        tKnob.setValue(str(dialog.reloadPlugin.value()))

        tKnob = buildKnob("PerformanceProfilerPath", "performanceProfilerPath")
        tKnob.setValue(dialog.performanceProfilerPath.value())

        # If the Nuke script has been modified, then save it to preserve SG settings.
        root = nuke.Root()
        if root.modified():
            if root.name() != "Root":
                nuke.scriptSave(root.name())
        
    except:
        print("Could not write knob settings.")
        print(traceback.format_exc())

def ReadStickySettings(configFile):
    # type: (str) -> None
    ReadMachineStickySettings(configFile)
    ReadSceneStickySettings()
    
def ReadMachineStickySettings(configFile):
    # type: (str) -> None
    # Read In Sticky Settings
    print("Reading sticky settings from %s" % configFile)

    try:
        if os.path.isfile(configFile):
            config = configparser.ConfigParser() # type: configparser.ConfigParser
            config.read(configFile)
            
            if config.has_section("Sticky"):
                if config.has_option("Sticky", "FrameListMode"):
                    initFrameListMode = config.get("Sticky", "FrameListMode")
                if config.has_option("Sticky", "CustomFrameList"):
                    initCustomFrameList = config.get("Sticky", "CustomFrameList")
                if config.has_option("Sticky", "Department"):
                    DeadlineGlobals.initDepartment = config.get("Sticky", "Department") # type: ignore
                if config.has_option("Sticky", "Pool"):
                    DeadlineGlobals.initPool = config.get("Sticky", "Pool") # type: ignore
                if config.has_option("Sticky", "SecondaryPool"):
                    DeadlineGlobals.initSecondaryPool = config.get("Sticky", "SecondaryPool") # type: ignore
                if config.has_option("Sticky", "Group"):
                    DeadlineGlobals.initGroup = config.get("Sticky", "Group") # type: ignore
                if config.has_option("Sticky", "Priority"):
                    DeadlineGlobals.initPriority = config.getint("Sticky", "Priority") # type: ignore
                if config.has_option("Sticky", "MachineLimit"):
                    DeadlineGlobals.initMachineLimit = config.getint("Sticky", "MachineLimit") # type: ignore
                if config.has_option("Sticky", "IsBlacklist"):
                    DeadlineGlobals.initIsBlacklist = config.getboolean("Sticky", "IsBlacklist") # type: ignore
                if config.has_option("Sticky", "MachineList"):
                    DeadlineGlobals.initMachineList = config.get("Sticky", "MachineList") # type: ignore
                if config.has_option("Sticky", "LimitGroups"):
                    DeadlineGlobals.initLimitGroups = config.get("Sticky", "LimitGroups") # type: ignore
                if config.has_option("Sticky", "SubmitSuspended"):
                    DeadlineGlobals.initSubmitSuspended = config.getboolean("Sticky", "SubmitSuspended") # type: ignore
                if config.has_option("Sticky", "ChunkSize"):
                    DeadlineGlobals.initChunkSize = config.getint("Sticky", "ChunkSize") # type: ignore
                if config.has_option("Sticky", "ConcurrentTasks"):
                    DeadlineGlobals.initConcurrentTasks = config.getint("Sticky", "ConcurrentTasks") # type: ignore
                if config.has_option("Sticky", "LimitConcurrentTasks"):
                    DeadlineGlobals.initLimitConcurrentTasks = config.getboolean("Sticky", "LimitConcurrentTasks") # type: ignore
                if config.has_option("Sticky", "Threads"):
                    DeadlineGlobals.initThreads = config.getint("Sticky", "Threads") # type: ignore
                if config.has_option("Sticky", "SubmitScene"):
                    DeadlineGlobals.initSubmitScene = config.getboolean("Sticky", "SubmitScene") # type: ignore
                if config.has_option("Sticky", "BatchMode"):
                    DeadlineGlobals.initBatchMode = config.getboolean("Sticky", "BatchMode") # type: ignore
                if config.has_option("Sticky", "ContinueOnError"):
                    DeadlineGlobals.initContinueOnError = config.getboolean("Sticky", "ContinueOnError") # type: ignore
                if config.has_option("Sticky", "SeparateJobs"):
                    DeadlineGlobals.initSeparateJobs = config.getboolean("Sticky", "SeparateJobs") # type: ignore
                if config.has_option("Sticky", "UseNodeRange"):
                    DeadlineGlobals.initUseNodeRange = config.getboolean("Sticky", "UseNodeRange") # type: ignore
                if config.has_option("Sticky", "UseGpu"):
                    DeadlineGlobals.initUseGpu = config.getboolean("Sticky", "UseGpu") # type: ignore
                if config.has_option("Sticky", "UseSpecificGpu"):
                    DeadlineGlobals.initUseSpecificGpu = config.getboolean("Sticky", "UseSpecificGpu") # type: ignore
                if config.has_option("Sticky", "ChooseGpu"):
                    DeadlineGlobals.initChooseGpu = config.getint("Sticky", "ChooseGpu") # type: ignore
                if config.has_option("Sticky", "EnforceRenderOrder"):
                    DeadlineGlobals.initEnforceRenderOrder = config.getboolean("Sticky", "EnforceRenderOrder") # type: ignore
                if config.has_option("Sticky", "RenderMode"):
                    DeadlineGlobals.initRenderMode = config.get("Sticky", "RenderMode") # type: ignore
                if config.has_option("Sticky", "PerformanceProfiler"):
                    DeadlineGlobals.initPerformanceProfiler = config.getboolean("Sticky", "PerformanceProfiler") # type: ignore
                if config.has_option("Sticky", "ReloadPlugin"):
                    DeadlineGlobals.initReloadPlugin = config.getboolean("Sticky", "ReloadPlugin") # type: ignore
                if config.has_option("Sticky", "PerformanceProfilerPath"):
                    DeadlineGlobals.initPerformanceProfilerPath = config.get("Sticky", "PerformanceProfilerPath") # type: ignore
                if config.has_option("Sticky", "PrecompFirst"):
                    DeadlineGlobals.initPrecompFirst = config.getboolean("Sticky", "PrecompFirst") # type: ignore
                if config.has_option("Sticky", "PrecompOnly"):
                    DeadlineGlobals.initPrecompOnly = config.get("Sticky", "PrecompOnly") # type: ignore
                if config.has_option("Sticky", "SmartVectorOnly"):
                    DeadlineGlobals.initSmartVectorOnly = config.get("Sticky", "SmartVectorOnly") # type: ignore
                if config.has_option("Sticky", "EddyCacheOnly"):
                    DeadlineGlobals.initEddyCacheOnly = config.get("Sticky", "EddyCacheOnly") # type: ignore
    except:
        print("Could not read sticky settings")
        print(traceback.format_exc())

def ReadSceneStickySettings():
    # type: () -> None
    try:
        root = nuke.Root()
        if "FrameListMode" in root.knobs():
            initFrameListMode = (root.knob("FrameListMode")).value()
            
        if "CustomFrameList" in root.knobs():
            initCustomFrameList = (root.knob("CustomFrameList")).value()
            
        if "Department" in root.knobs():
            DeadlineGlobals.initDepartment = (root.knob("Department")).value() # type: ignore
            
        if "Pool" in root.knobs():
            DeadlineGlobals.initPool = (root.knob("Pool")).value() # type: ignore
            
        if "SecondaryPool" in root.knobs():
            DeadlineGlobals.initSecondaryPool = (root.knob("SecondaryPool")).value() # type: ignore
            
        if "Group" in root.knobs():
            DeadlineGlobals.initGroup = (root.knob("Group")).value() # type: ignore
            
        if "Priority" in root.knobs():
            DeadlineGlobals.initPriority = int((root.knob("Priority")).value()) # type: ignore
            
        if "MachineLimit" in root.knobs():
            DeadlineGlobals.initMachineLimit = int((root.knob("MachineLimit")).value()) # type: ignore
            
        if "IsBlacklist" in root.knobs():
            DeadlineGlobals.initIsBlacklist = StrToBool((root.knob("IsBlacklist")).value()) # type: ignore
        
        if "MachineList" in root.knobs():
            DeadlineGlobals.initMachineList = (root.knob("MachineList")).value() # type: ignore
        
        if "LimitGroups" in root.knobs():
            DeadlineGlobals.initLimitGroups = (root.knob("LimitGroups")).value() # type: ignore
        
        if "SubmitSuspended" in root.knobs():
            DeadlineGlobals.initSubmitSuspended = StrToBool((root.knob("SubmitSuspended")).value()) # type: ignore
        
        if "ChunkSize" in root.knobs():
            DeadlineGlobals.initChunkSize = int((root.knob("ChunkSize")).value()) # type: ignore
        
        if "ConcurrentTasks" in root.knobs():
            DeadlineGlobals.initConcurrentTasks = int((root.knob("ConcurrentTasks")).value()) # type: ignore
        
        if "LimitConcurrentTasks" in root.knobs():
            DeadlineGlobals.initLimitConcurrentTasks = StrToBool((root.knob("LimitConcurrentTasks")).value()) # type: ignore
        
        if "Threads" in root.knobs():
            DeadlineGlobals.initThreads = int((root.knob("Threads")).value()) # type: ignore
        
        if "SubmitScene" in root.knobs():
            DeadlineGlobals.initSubmitScene = StrToBool((root.knob("SubmitScene")).value()) # type: ignore
        
        if "BatchMode" in root.knobs():
            DeadlineGlobals.initBatchMode = StrToBool((root.knob("BatchMode")).value()) # type: ignore
        
        if "ContinueOnError" in root.knobs():
            DeadlineGlobals.initContinueOnError = StrToBool((root.knob("ContinueOnError")).value()) # type: ignore

        if "SeparateJobs" in root.knobs():
            DeadlineGlobals.initSeparateJobs = StrToBool((root.knob ("SeparateJobs")).value()) # type: ignore

        if "UseNodeRange" in root.knobs():
            DeadlineGlobals.initUseNodeRange = StrToBool((root.knob("UseNodeRange")).value()) # type: ignore
        
        if "UseGpu" in root.knobs():
            DeadlineGlobals.initUseGpu = StrToBool((root.knob("UseGpu")).value()) # type: ignore
        
        if "UseSpecificGpu" in root.knobs():
            DeadlineGlobals.initUseSpecificGpu = StrToBool((root.knob("UseSpecificGpu")).value()) # type: ignore
        
        if "ChooseGpu" in root.knobs():
            DeadlineGlobals.initChooseGpu = int((root.knob("ChooseGpu")).value()) # type: ignore
            
        if "EnforceRenderOrder" in root.knobs():
            DeadlineGlobals.initEnforceRenderOrder = StrToBool((root.knob("EnforceRenderOrder")).value()) # type: ignore

        if "DeadlineRenderMode" in root.knobs():
            DeadlineGlobals.initRenderMode = root.knob("DeadlineRenderMode").value() # type: ignore

        if "PerformanceProfiler" in root.knobs():
            DeadlineGlobals.initPerformanceProfiler = StrToBool((root.knob("PerformanceProfiler")).value()) # type: ignore
        
        if "ReloadPlugin" in root.knobs():
            DeadlineGlobals.initReloadPlugin = StrToBool((root.knob("ReloadPlugin")).value()) # type: ignore
        
        if "PerformanceProfilerPath" in root.knobs():
            DeadlineGlobals.initPerformanceProfilerPath = (root.knob("PerformanceProfilerPath")).value() # type: ignore
            
        if "PrecompFirst" in root.knobs():
            DeadlineGlobals.initPrecompFirst = (root.knob("PrecompFirst")).value() # type: ignore
            
        if "PrecompOnly" in root.knobs():
            DeadlineGlobals.initPrecompOnly = (root.knob("PrecompOnly")).value() # type: ignore
            
        if "SmartVectorOnly" in root.knobs():
            DeadlineGlobals.initSmartVectorOnly = (root.knob("SmartVectorOnly")).value() # type: ignore
            
        if "EddyCacheOnly" in root.knobs():
            DeadlineGlobals.initEddyCacheOnly = (root.knob("EddyCacheOnly")).value() # type: ignore
    except:
        print("Could not read knob settings.")
        print(traceback.format_exc())

def SubmitSequenceJobs(dialog, deadlineTemp, tempDependencies, semaphore, extraInfo):
    # type: (DeadlineDialog, str, str, threading.Semaphore, List[str]) -> None
    global ResolutionsDict, FormatsDict

    projectName = dialog.studioProject.value() # type: str
    #Get the comps that will be submitted for the project selected in the dialog
    comps = dialog.validComps[projectName] # type: Dict[str, List]
    
    node = None
    
    #Get the sequences that will be submitted
    sequenceKnobs = dialog.sequenceKnobs
    allSequences = not dialog.chooseCompsToRender.value()
    
    sequences = [] # type: List
    for knobTuple in sequenceKnobs:
        if knobTuple[1][1] == projectName:
            if not allSequences:
                if knobTuple[0].value():
                    sequences.append(knobTuple[1][0])
            else:
                sequences.append(knobTuple[1][0])
                
    allComps = [] # type: List
    for sequence in sequences:
        for comp in comps[sequence]:
            allComps.append(comp)
                
    batchName = str(str(dialog.jobName.value())+" ("+projectName + ")") # type: str
    
    jobCount = len(allComps) # type: int
    currentJobIndex = 1 # type: int
    
    previousJobId = "" # type: str
    #Submit all comps in each sequence
    for sequence in sequences:
        compNum = 1 # type: int
        for comp in comps[sequence]:
            print("Preparing job #%d for submission.." % currentJobIndex)
            
            progressTask = nuke.ProgressTask("Job Submission") # type: nuke.ProgressTask
            progressTask.setMessage("Creating Job Info File")
            progressTask.setProgress(0)
            if len(comps[sequence]) > 1:
                name = sequence + " - Comp "+str(compNum) # type: str
            else:
                name = sequence
              
            if dialog.separateJobDependencies.value():
                if len(previousJobId) > 1 and jobCount > 1 and not tempDependencies == "":
                    tempDependencies = tempDependencies + "," + previousJobId
                elif tempDependencies == "":
                    tempDependencies = previousJobId
                
            # Create the submission info file (append job count since we're submitting multiple jobs at the same time in different threads)
            jobInfoFile = os.path.join(deadlineTemp, u"nuke_submit_info%d.job" % currentJobIndex) # type: ignore
            fileHandle = open(jobInfoFile, "w")
            fileHandle.write("Plugin=Nuke\n")
            fileHandle.write("Name={}({})\n".format(dialog.jobName.value(), name))
            fileHandle.write("Comment={}\n".format(dialog.comment.value()))
            fileHandle.write("Department={}\n".format(dialog.department.value()))
            fileHandle.write("Pool={}\n".format(dialog.pool.value()))
            if dialog.secondaryPool.value() == "":
                fileHandle.write("SecondaryPool=\n")
            else:
                fileHandle.write("SecondaryPool={}\n".format(dialog.secondaryPool.value()))
            fileHandle.write("Group={}\n".format(dialog.group.value()))
            fileHandle.write("Priority={}\n".format(dialog.priority.value()))
            fileHandle.write("MachineLimit={}\n".format(dialog.machineLimit.value()))
            fileHandle.write("TaskTimeoutMinutes={}\n".format(dialog.taskTimeout.value()))
            fileHandle.write("EnableAutoTimeout={}\n".format(dialog.autoTaskTimeout.value()))
            fileHandle.write("ConcurrentTasks={}\n".format(dialog.concurrentTasks.value()))
            fileHandle.write("LimitConcurrentTasksToNumberOfCpus={}\n".format(dialog.limitConcurrentTasks.value()))
            fileHandle.write("LimitGroups={}\n".format(dialog.limitGroups.value()))
            fileHandle.write("JobDependencies={}\n".format(tempDependencies))
            fileHandle.write("OnJobComplete={}\n".format(dialog.onComplete.value()))
            
            tempFrameList = str(int(comp.startFrame())) + "-" + str(int(comp.endFrame())) # type: str
            
            fileHandle.write("Frames={}\n".format(tempFrameList))
            fileHandle.write("ChunkSize=1\n")
            
            if dialog.submitSuspended.value():
                fileHandle.write("InitialStatus=Suspended\n")
            
            if dialog.isBlacklist.value():
                fileHandle.write("Blacklist={}\n".format(dialog.machineList.value()))
            else:
                fileHandle.write("Whitelist={}\n".format(dialog.machineList.value()))

            #NOTE: We're not writing out NIM/FTrack/Shotgun or Draft extra info here because we do not have a defined output file to operate on in this case.
                
            if jobCount > 1:
                fileHandle.write("BatchName={}\n".format(batchName))
            
            fileHandle.close()
            
            # Update task progress
            progressTask.setMessage("Creating Plugin Info File")
            progressTask.setProgress(10)
            
            # Create the plugin info file
            pluginInfoFile = os.path.join(deadlineTemp, u"nuke_plugin_info{}.job".format(currentJobIndex))
            fileHandle = open(pluginInfoFile, "w")
            fileHandle.write("SceneFile={}\n".format(comp.filename()))
            fileHandle.write("Version={0}.{1}\n".format(*dialog.nukeVersion))
            fileHandle.write("Threads={}\n".format(dialog.threads.value()))
            fileHandle.write("RamUse={}\n".format(dialog.memoryUsage.value()))
            fileHandle.write("BatchMode={}\n".format(dialog.batchMode.value()))
            fileHandle.write("BatchModeIsMovie={}\n".format(False))
            
            fileHandle.write("NukeX={}\n".format(dialog.useNukeX.value()))

            if dialog.nukeVersion >= (7,):
                fileHandle.write("UseGpu={}\n".format(dialog.useGpu.value()))
            
            if dialog.nukeVersion >= (8,):
                fileHandle.write("UseSpecificGpu={}\n".format(dialog.useSpecificGpu.value()))
                fileHandle.write("GpuOverride={}\n".format(dialog.chooseGpu.value()))
            
            fileHandle.write("RenderMode={}\n".format(dialog.renderMode.value()))
            fileHandle.write("EnforceRenderOrder={}\n".format(dialog.enforceRenderOrder.value()))
            fileHandle.write("ContinueOnError={}\n".format(dialog.continueOnError.value()))

            if dialog.nukeVersion >= (9,):
                fileHandle.write("PerformanceProfiler={}\n".format(dialog.performanceProfiler.value()))
                fileHandle.write("PerformanceProfilerDir={}\n".format(dialog.performanceProfilerPath.value()))
                
            fileHandle.write("StackSize={}\n".format(dialog.stackSize.value()))
            fileHandle.close()
            
            # Update task progress
            progressTask.setMessage("Submitting Job {} to Deadline".format(currentJobIndex))
            progressTask.setProgress(30)
            
            # Submit the job to Deadline
            args = [] # type: List[str]

            if sys.version_info[0] > 2:
                args.append(jobInfoFile)
                args.append(pluginInfoFile)
            else:
                args.append(jobInfoFile.encode(locale.getpreferredencoding()))
                args.append(jobInfoFile.encode(locale.getpreferredencoding()))
            
            args.append(comp.filename())
            
            tempResults = "" # type: str
            
            # Submit Job
            progressTask.setProgress(50)
            
            # If submitting multiple jobs, acquire the semaphore so that only one job is submitted at a time.
            if semaphore:
                semaphore.acquire()

            try:
                tempResults = CallDeadlineCommand(args)
            finally:
                # Update task progress
                progressTask.setMessage("Complete!")
                progressTask.setProgress(100)
                print("Job submission #%d complete" % currentJobIndex)

                # If submitting multiple jobs, just print the results to the console and release the semaphore. Otherwise show results to the user.
                if semaphore:
                    print(tempResults)
                    semaphore.release()
                else:
                    nuke.executeInMainThread(nuke.message, tempResults)

            currentJobIndex += 1
            compNum += 1
            
            for line in tempResults.splitlines():
                if line.startswith("JobID="):
                    previousJobId = line[6:]
                    break
            
    nuke.executeInMainThread(nuke.message, "Sequence Job Submission complete. "+str(jobCount)+" Job(s) submitted to Deadline.")

def SubmitJob(dialog, root, node, writeNodes, deadlineTemp, tempJobName, tempFrameList, tempDependencies, tempChunkSize, tempIsMovie, jobCount, semaphore,  extraInfo):
    # type: (DeadlineDialog, Any, Any, List, str, str, str, str, int, bool, int, threading.Semaphore, List[str]) -> str
    global ResolutionsDict, FormatsDict
    
    viewsToRender = [] # type: List
    if dialog.chooseViewsToRender.value():
        for vk in dialog.viewToRenderKnobs:
            if vk[0].value():
                viewsToRender.append(vk[1])
    else:
        viewsToRender = nuke.views()
        
        
    print("Preparing job #%d for submission.." % jobCount)
    
    # Create a task in Nuke's progress  bar dialog
    progressTask = nuke.ProgressTask("Job Submission") # type: nuke.ProgressTask
    progressTask.setMessage("Creating Job Info File")
    progressTask.setProgress(0)
    
    batchName = dialog.jobName.value()
    # Create the submission info file (append job count since we're submitting multiple jobs at the same time in different threads)
    jobInfoFile = os.path.join(deadlineTemp, u"nuke_submit_info%d.job" % jobCount)
    fileHandle = open(jobInfoFile, "w")
    fileHandle.write("Plugin=Nuke\n")
    fileHandle.write("Name={}\n".format(tempJobName))
    fileHandle.write("Comment={}\n".format(dialog.comment.value()))
    fileHandle.write("Department={}\n".format(dialog.department.value()))
    fileHandle.write("Pool={}\n".format(dialog.pool.value()))
    if dialog.secondaryPool.value() == "":
        fileHandle.write("SecondaryPool=\n")
    else:
        fileHandle.write("SecondaryPool={}\n".format(dialog.secondaryPool.value()))
    fileHandle.write("Group={}\n".format(dialog.group.value()))
    fileHandle.write("Priority={}\n".format(dialog.priority.value()))
    fileHandle.write("MachineLimit={}\n".format(dialog.machineLimit.value()))
    fileHandle.write("TaskTimeoutMinutes={}\n".format(dialog.taskTimeout.value()))
    fileHandle.write("EnableAutoTimeout={}\n".format(dialog.autoTaskTimeout.value()))
    fileHandle.write("ConcurrentTasks={}\n".format(dialog.concurrentTasks.value()))
    fileHandle.write("LimitConcurrentTasksToNumberOfCpus={}\n".format(dialog.limitConcurrentTasks.value()))
    fileHandle.write("LimitGroups={}\n".format(dialog.limitGroups.value()))
    fileHandle.write("JobDependencies={}\n".format(tempDependencies))
    fileHandle.write("OnJobComplete={}\n".format(dialog.onComplete.value()))
    fileHandle.write("ForceReloadPlugin={}\n".format(dialog.reloadPlugin.value()))
    
    if dialog.separateTasks.value():
        writeNodeCount = 0 # type: int
        for tempNode in writeNodes:
            if not tempNode.knob('disable').value():
                enterLoop = True # type: bool
                if dialog.readFileOnly.value() and tempNode.knob('reading'):
                    enterLoop = enterLoop and tempNode.knob('reading').value()
                if dialog.selectedOnly.value():
                    enterLoop = enterLoop and IsNodeOrParentNodeSelected(tempNode)
                
                if enterLoop:
                    writeNodeCount += 1
        
        fileHandle.write("Frames=0-%s\n" % (writeNodeCount-1))
        fileHandle.write("ChunkSize=1\n")
    else:
        fileHandle.write("Frames=%s\n" % tempFrameList)
        fileHandle.write("ChunkSize=%s\n" % tempChunkSize)
    
    if dialog.submitSuspended.value():
        fileHandle.write("InitialStatus=Suspended\n")
    
    if dialog.isBlacklist.value():
        fileHandle.write("Blacklist=%s\n" % dialog.machineList.value())
    else:
        fileHandle.write("Whitelist=%s\n" % dialog.machineList.value())
    
    extraKVPIndex = 0 # type: int
    
    index = 0 # type: int
    
    for v in viewsToRender:
        if dialog.separateJobs.value():
            
            #gets the filename/proxy filename and evaluates TCL + vars, but *doesn't* swap frame padding
            fileValue = get_filename(node) # type: str
            evaluatedValue = evaluate_filename_knob(node, view=v)
            if fileValue and evaluatedValue:
                tempPath, tempFilename = os.path.split(evaluatedValue) # type: Tuple[str, str]
                if IsPadded(os.path.basename(fileValue)):
                    tempFilename = GetPaddedPath(tempFilename)
                    
                paddedPath = os.path.join(tempPath, tempFilename) # type: str
                #Handle cases where file name might start with an escape character
                paddedPath = paddedPath.replace("\\", "/")

                fileHandle.write("OutputFilename%i=%s\n" % (index, paddedPath))
                
                #Check if the Write Node will be modifying the output's Frame numbers
                if node.knob('frame_mode'):
                    if (node.knob('frame_mode').value() == "offset"):
                        fileHandle.write("ExtraInfoKeyValue%d=OutputFrameOffset%i=%s\n" % (extraKVPIndex,index, str(int(node.knob('frame').value()))))
                        extraKVPIndex += 1
                    elif (node.knob('frame_mode').value() == "start at" or node.knob('frame_mode').value() == "start_at"):
                        franges = nuke.FrameRanges(tempFrameList)
                        fileHandle.write("ExtraInfoKeyValue%d=OutputFrameOffset%i=%s\n" % (extraKVPIndex,index, str(int(node.knob('frame').value()) - franges.minFrame())))
                        extraKVPIndex += 1
                    else:
                        #TODO: Handle 'expression'? Would be much harder
                        pass
                index+=1
        else:
            for tempNode in writeNodes:
                if not tempNode.knob('disable').value():
                    enterLoop = True
                    if tempNode.Class() != "SmartVector" and dialog.readFileOnly.value() and tempNode.knob('reading'):
                        enterLoop = enterLoop and tempNode.knob('reading').value()
                    if dialog.selectedOnly.value():
                        enterLoop = enterLoop and IsNodeOrParentNodeSelected(tempNode)
                    
                    if enterLoop:
                        fileValue = get_filename(tempNode) # str
                        evaluatedValue = evaluate_filename_knob(tempNode, view=v) # str
                        if fileValue and evaluatedValue:
                            tempPath, tempFilename = os.path.split(evaluatedValue) # Tuple[str, str]
                            
                            if dialog.separateTasks.value():
                                fileHandle.write("OutputDirectory%s=%s\n" % (index, tempPath))
                            else:
                                if IsPadded(os.path.basename(fileValue)):
                                    tempFilename = GetPaddedPath(tempFilename)
                                    
                                paddedPath = os.path.join(tempPath, tempFilename)
                                #Handle escape character cases
                                paddedPath = paddedPath.replace("\\", "/")

                                fileHandle.write("OutputFilename%s=%s\n" % (index, paddedPath))
                                
                                #Check if the Write Node will be modifying the output's Frame numbers
                                if tempNode.knob('frame_mode'):
                                    frameVal = tempNode.knob('frame').value()
                                    if frameVal != "":
                                        if (tempNode.knob('frame_mode').value() == "offset"):
                                            fileHandle.write("ExtraInfoKeyValue%d=OutputFrameOffset%s=%s\n" % (extraKVPIndex, index, str(int(frameVal))))
                                            extraKVPIndex += 1
                                        elif (tempNode.knob('frame_mode').value() == "start at" or tempNode.knob('frame_mode').value() == "start_at"):
                                            franges = nuke.FrameRanges(tempFrameList)
                                            fileHandle.write("ExtraInfoKeyValue%d=OutputFrameOffset%s=%s\n" % (extraKVPIndex, index, str(int(frameVal) - franges.minFrame())))
                                            extraKVPIndex += 1
                                        else:
                                            #TODO: Handle 'expression'? Would be much harder
                                            pass
                                
                            index += 1
        
    # Write the shotgun data.
    groupBatch = False # type: bool

    for i, extraInfoVal in enumerate(extraInfo):
        fileHandle.write("ExtraInfo%d=%s\n" % (i, extraInfoVal))
    
    nukeAssets = FindAssetPaths(nuke.root())
    for assetId, asset in enumerate(nukeAssets):
        fileHandle.write("AWSAssetFile%s=%s\n" % (assetId, asset))
    
    if groupBatch or dialog.separateJobs.value():
        fileHandle.write("BatchName=%s\n" % batchName)
    
    fileHandle.close()
    # Write pipeline tool settings to .job file
    ConcatenatePipelineSettingsToJob(jobInfoFile, batchName)
    # Update task progress
    progressTask.setMessage("Creating Plugin Info File")
    progressTask.setProgress(10)
    
    # Create the plugin info file
    pluginInfoFile = os.path.join(deadlineTemp, u"nuke_plugin_info%d.job" % jobCount) # type: ignore
    fileHandle = open(pluginInfoFile, "w")
    if not dialog.submitScene.value():
        fileHandle.write("SceneFile=%s\n" % root.name())
    
    fileHandle.write("Version={0}.{1}\n".format(*dialog.nukeVersion))
    fileHandle.write("Threads=%s\n" % dialog.threads.value())
    fileHandle.write("RamUse=%s\n" % dialog.memoryUsage.value())
    fileHandle.write("BatchMode=%s\n" % dialog.batchMode.value())
    fileHandle.write("BatchModeIsMovie=%s\n" % tempIsMovie)
    
    if dialog.separateJobs.value():
        #we need the fullName of the node here, otherwise write nodes that are embedded in groups won't work
        fileHandle.write("WriteNode=%s\n" % node.fullName())
    elif dialog.separateTasks.value():
        fileHandle.write("WriteNodesAsSeparateJobs=True\n")
        
        writeNodeIndex = 0 # type: int
        for tempNode in writeNodes:
            if not tempNode.knob('disable').value():
                enterLoop = True
                if dialog.readFileOnly.value() and tempNode.knob('reading'):
                    enterLoop = enterLoop and tempNode.knob('reading').value()
                if dialog.selectedOnly.value():
                    enterLoop = enterLoop and IsNodeOrParentNodeSelected(tempNode)
                
                if enterLoop:
                    startFrame = endFrame = None
                    #we need the fullName of the node here, otherwise write nodes that are embedded in groups won't work
                    fileHandle.write("WriteNode%s=%s\n" % (writeNodeIndex,tempNode.fullName()))
                    
                    startFrame, endFrame = GetNodeFrameRange(tempNode)
                    if startFrame is None or endFrame is None:
                        startFrame = nuke.Root().firstFrame()
                        endFrame = nuke.Root().lastFrame()

                        if dialog.frameListMode.value() == "Input":
                            try:
                                activeInput = nuke.activeViewer().activeInput()
                                startFrame = nuke.activeViewer().node().input(activeInput).frameRange().first()
                                endFrame = nuke.activeViewer().node().input(activeInput).frameRange().last()
                            except:
                                pass
                    
                    fileHandle.write("WriteNode%sStartFrame=%s\n" % (writeNodeIndex,startFrame))
                    fileHandle.write("WriteNode%sEndFrame=%s\n" % (writeNodeIndex,endFrame))
                    writeNodeIndex += 1
    else:
        if dialog.readFileOnly.value() or dialog.selectedOnly.value():
            writeNodesStr = ""
            
            for tempNode in writeNodes:
                if not tempNode.knob('disable').value():
                    enterLoop = True
                    if dialog.readFileOnly.value() and tempNode.knob('reading'):
                        enterLoop = enterLoop and tempNode.knob('reading').value()
                    if dialog.selectedOnly.value():
                        enterLoop = enterLoop and IsNodeOrParentNodeSelected(tempNode)
                    
                    if enterLoop:
                        #we need the fullName of the node here, otherwise write nodes that are embedded in groups won't work
                        writeNodesStr += ("%s," % tempNode.fullName())
                        
            writeNodesStr = writeNodesStr.strip(",")
            fileHandle.write("WriteNode=%s\n" % writeNodesStr)

    fileHandle.write("NukeX=%s\n" % dialog.useNukeX.value())

    if dialog.nukeVersion >= (7,):
        fileHandle.write("UseGpu=%s\n" % dialog.useGpu.value())
    
    if dialog.nukeVersion >= (8,):
        fileHandle.write("UseSpecificGpu=%s\n" % dialog.useSpecificGpu.value())
        fileHandle.write("GpuOverride=%s\n" % dialog.chooseGpu.value())
    
    fileHandle.write("RenderMode=%s\n" % dialog.renderMode.value())
    fileHandle.write("EnforceRenderOrder=%s\n" % dialog.enforceRenderOrder.value())
    fileHandle.write("ContinueOnError=%s\n" % dialog.continueOnError.value())
        
    if dialog.nukeVersion >= (9,):
        fileHandle.write("PerformanceProfiler=%s\n" % dialog.performanceProfiler.value())
        fileHandle.write("PerformanceProfilerDir=%s\n" % dialog.performanceProfilerPath.value())

    if dialog.chooseViewsToRender.value():
        fileHandle.write("Views=%s\n" % ','.join(viewsToRender))
    else:
        fileHandle.write("Views=\n")

    fileHandle.write("StackSize=%s\n" % dialog.stackSize.value())

    fileHandle.close()
    
    # Update task progress
    progressTask.setMessage("Submitting Job %d to Deadline" % jobCount)
    progressTask.setProgress(30)
    
    # Submit the job to Deadline
    args = [] # type: List[str]

    if sys.version_info[0] > 2:
        args.append(jobInfoFile)
        args.append(pluginInfoFile)
    else:
        args.append(jobInfoFile.encode(locale.getpreferredencoding()))
        args.append(pluginInfoFile.encode(locale.getpreferredencoding()))

    if dialog.submitScene.value():
        args.append(root.name())
    
    tempResults = "" # type: str
    
    # Submit Job
    progressTask.setProgress(50)
    
    # If submitting multiple jobs, acquire the semaphore so that only one job is submitted at a time.
    if semaphore:
        semaphore.acquire()
        
    try:
        tempResults = CallDeadlineCommand(args)
    finally:
        # If submitting multiple jobs, just print the results to the console and release the semaphore. Otherwise show it to the user.
        if semaphore:
            print(tempResults)
            semaphore.release()
        else:
            nuke.executeInMainThread(nuke.message, tempResults)

    # Update task progress
    progressTask.setMessage("Complete!")
    progressTask.setProgress(100)
    print("Job submission #%d complete" % jobCount)

    return tempResults

def FindAssetPaths(curNode):
    # type: (Any) -> List[str]
    global dlNonAssetClasses
    assetPaths = [] # type: List[str]
    if curNode is None:
        return assetPaths
    
    readknob = curNode.knob("reading")
    ignoreNonAsset = False # type: bool
    if readknob:
        if readknob.value():
            ignoreNonAsset = True
    
    if not curNode.Class() in dlNonAssetClasses or ignoreNonAsset:
        nodeKnobs = curNode.allKnobs()
        for knob in nodeKnobs:
            if knob.Class() == "File_Knob":
                if knob.value() != "":
                    assetPath = knob.value()
                    assetPaths.append(ReplacePadding(assetPath))
    
    if isinstance(curNode, nuke.Group):
        for child in curNode.nodes():
            assetPaths.extend(FindAssetPaths(child))

    return assetPaths
  
#This will recursively find nodes of the given class (used to find write nodes, even if they're embedded in groups).  
def RecursiveFindNodes(nodeClasses, startNode):
    # type: (Union[List[str], str], Any) -> List[Any]
    nodeList = [] # type: List[Any]
    
    if startNode != None:
        if startNode.Class() in nodeClasses:
            nodeList = [startNode]
        elif isinstance(startNode, nuke.Group):
            for child in startNode.nodes():
                nodeList.extend(RecursiveFindNodes(nodeClasses, child))
        
    return nodeList

def RecursiveFindNodesInPrecomp(nodeClasses, startNode):
    # type: (List[str], Any) -> List[Any]
    nodeList = [] # type: List[Any]
    
    if startNode != None:
        if startNode.Class() == "Precomp":
            for child in startNode.nodes():
                nodeList.extend(RecursiveFindNodes(nodeClasses, child))
        elif isinstance(startNode, nuke.Group):
            for child in startNode.nodes():
                nodeList.extend(RecursiveFindNodesInPrecomp(nodeClasses, child))
    
    return nodeList
    
def FindNodesHasNoRenderOrder(nodes):
    # type: (List[Any]) -> Tuple[str, int]
    noRenderOrderNodes = filter(lambda node:'render_order' not in node.knobs(), nodes) # type: ignore # loop through all nodes find all nodes doesn't have 'render_order'
    noRenderOrderNodesNames = map(lambda node:node.name(), noRenderOrderNodes) # type: ignore # loop through nodes in the list created in previous line and collect all names 

    num_nodes = 0 # type: int

    if sys.version_info[0] > 2:
        num_nodes = len(list(noRenderOrderNodesNames))
    else:
        num_nodes = len(noRenderOrderNodesNames)

    return ','.join(noRenderOrderNodesNames), num_nodes # return the names of nodes in one string and number of nodes


def IsNodeReadingOrDisabled(node):
    # type: (Any) -> bool
    reading = False # type: bool
    if node.knob('reading'):
        reading = node.knob('reading').value()

    return reading or node.knob('disable').value()

def GetNodeFrameRange(node):
    # type: (Any) -> Tuple[int, int]
    startFrame = 0 # type: int
    endFrame = 0 # type: int

    if node.Class() == "SmartVector":
        if node.knob("render_range").value() == "custom":
            startFrame = int(node.knob("file.first_frame").value())
            endFrame = int(node.knob("file.last_frame").value())
    elif node.Class() == "EddyCacheNode":
        if node.knob("use_range").value():
            startFrame = int(node.knob("start_frame").value())
            endFrame = int(node.knob("end_frame").value())
    else:
        if node.knob("use_limit").value():
            startFrame =  int(node.knob("first").value())
            endFrame = int(node.knob("last").value())

    return startFrame, endFrame


def GetFrameList(node=None):
    # type: (Optional[Any]) -> Optional[str]
    global dialog

    frameList = None # type: Optional[str]

    if dialog is not None:
        # Check if the write node is overriding the frame range
        if node is not None and (dialog.separateJobs.value() or dialog.separateTasks.value()) and dialog.useNodeRange.value():
            startFrame, endFrame = GetNodeFrameRange(node)
            if startFrame is not None and endFrame is not None:
                frameList = "%s-%s" % (startFrame, endFrame)

        if frameList == None:
            frameList = dialog.frameList.value().strip()

    return frameList


def get_filename(node):
    # type: (Any) -> str
    """
    Utility function to get the filename from a node
    """
    if is_eddy_cache_node_v1(node):
        # Eddy for Nuke 1 used a special-cased knob, 'VDBFileName'
        # Eddy for Nuke 2 uses the standard knob, 'file', which allows nuke.filname(node) to find it
        return node.knob('VDBFileName').value()
    else:
        #nuke.filename will evaluate embedded TCL, but leave the frame padding
        return nuke.filename(node)
    
def evaluate_filename_knob(node, view):
    # type: (Any, Any) -> str
    """
    Utility function to evaluate a node's filename knob with a given view.
    """
    root = nuke.Root() # type: Any

    knob_name = 'file' # type: str
    if root.proxy() and node.knob('proxy').value():
        knob_name = 'proxy'
    elif is_eddy_cache_node_v1(node):
        knob_name = 'VDBFileName'

    return node.knob(knob_name).evaluate(view=view)

def is_eddy_cache_node_v1(node):
    # type: (Any) -> bool
    """
    Utility function to determine if a node is an "Eddy Cache Node" from "Eddy for Nuke 1". In version 2,
    the "VDBFileName" knob was marked as obsolete, so we can check it this way.
    """
    return node.Class() == 'EddyCacheNode' and not isinstance(node.knob('VDBFileName'), nuke.Obsolete_Knob)

def is_node_rendered(node):
    # type: (Any) -> bool
    """
    Utility function to check if nodes like smart-vectors or eddy cache node have rendered
    """
    # Can short-circuit if this node doesn't render or is disabled, since it won't have output
    if IsNodeReadingOrDisabled(node):
        return False

    filename = get_filename(node) # type: str
    frame_list = GetFrameList(node) # type: Optional[str]

    # Get the padding info
    padding_regex = re.compile("(#+)|%(\d*)d")
    found_padding = padding_regex.search(filename)
    if found_padding:
        if found_padding.group(1): # (#+)
            padding_length = len(found_padding.group(1)) # type: int
        else: # %(\d*)d
            padding_length = int(found_padding.group(2))

        # Get list of frames
        frames_string = CallDeadlineCommand(["-ParseFrameList", frame_list, "False"]).strip() # type: ignore
        frames = [i.strip() for i in frames_string.split(",")] # type: List[str]
        
        # Evaluate the padding filename for each frame
        for frame in frames:
            padded_frame = frame.zfill(padding_length)
            padded_filename = padding_regex.sub(padded_frame, filename) # type: str
            if not os.path.isfile(padded_filename):
                print("Cannot find '%s'" % padded_filename)
                return False
    elif not os.path.isfile(filename):
        print("Cannot find '%s'" % filename)
        return False

    return True

# The main submission function.
def SubmitToDeadline():
    # type: () -> None
    global dialog, submissionInfo
   
    # Get the root node.
    root = nuke.Root() # type: Any
    studio = False # type: bool
    noRoot = False # type: bool
    if 'studio' in nuke.env.keys() and nuke.env[ 'studio' ]:
        studio = True
    # If the Nuke script hasn't been saved, its name will be 'Root' instead of the file name.
    if root.name() == "Root":
        noRoot = True
        if not studio:
            nuke.message("The Nuke script must be saved before it can be submitted to Deadline.")
            return
        
    nuke_projects = [] # type: List[Any]
    valid_projects = [] # type: List[Any]
    
    if studio:
        #Get the projects and check if we have any comps in any of them
        nuke_projects = hcore.projects()
        if len(nuke_projects) < 1 and not noRoot:
            nuke.message("The Nuke script or Nuke project must be saved before it can be submitted to Deadline.")
            return
        
        if len(nuke_projects) > 0:
            foundScripts = False # type: bool
            for project in nuke_projects:
                sequences = project.sequences()
                for sequence in sequences:
                    tracks = sequence.binItem().activeItem().items()
                    for track in tracks:
                        items = track.items()
                        for item in items:
                            if item.isMediaPresent():
                                source = item.source()
                                name = source.mediaSource().filename()
                                if ".nk" in name:
                                    foundScripts = True
                                    break
                        if foundScripts:
                            break
                    if foundScripts:
                        break
                if foundScripts:
                    foundScripts = False
                    valid_projects.append(project)
            
            if len(valid_projects) < 1 and noRoot:
                nuke.message("The current Nuke project contains no saved comps that can be rendered. Please save any existing Nuke scripts before submitting to Deadline.")
                return
    
    # If the Nuke script has been modified, then save it.
    if root.modified() and not noRoot:
        if root.name() != "Root":
            nuke.scriptSave(root.name())

    print("Grabbing submitter info...")
    try:
        output = json.loads(CallDeadlineCommand([ "-prettyJSON", "-GetSubmissionInfo", "Pools", "Groups", "MaxPriority", "UserHomeDir", "RepoDir:submission/Nuke/Main", "RepoDir:submission/Integration/Main", ])) # type: Dict
    except:
        print("Unable to get submitter info from Deadline:\n\n" + traceback.format_exc())
        raise
    
    if output[ "ok" ]:
        submissionInfo = output[ "result" ]
    else:
        print("DeadlineCommand returned a bad result and was unable to grab the submitter info.\n\n" + output[ "result" ])
        raise Exception(output[ "result" ])

    deadlineHome = submissionInfo[ "UserHomeDir" ].strip() # type: str
    deadlineSettings = os.path.join(deadlineHome, "settings") # typs: str
    deadlineTemp = os.path.join(deadlineHome, "temp") # type: str

    # Get maximum priority
    maximumPriority = int(submissionInfo.get("MaxPriority", 100)) # type: int

    # Get pools
    pools = [] # type: List[str]
    secondaryPools = [" "]  # type: List[str] # empty string cannot be reselected
    for pool in submissionInfo[ "Pools" ]:
        pool = pool.strip()
        pools.append(pool)
        secondaryPools.append(pool)

    if len(pools) == 0:
        pools.append("none")
        secondaryPools.append("none")

    # Get groups
    groups = [] # type: List[str]
    for group in submissionInfo[ "Groups" ]:
        groups.append(group.strip())

    if len(groups) == 0:
        groups.append("none")

    initFrameListMode = "Global" # type: str
    initCustomFrameList = None # type: Optional[str]
    
    # Set initial settings for submission dialog.
    if noRoot:
        DeadlineGlobals.initJobName = "Untitled" # type: ignore
    else:
        DeadlineGlobals.initJobName = os.path.basename(nuke.Root().name()) # type: ignore
    DeadlineGlobals.initComment = "" # type: ignore
    
    DeadlineGlobals.initDepartment = "" # type: ignore
    DeadlineGlobals.initPool = "none" # type: ignore
    DeadlineGlobals.initSecondaryPool = " " # type: ignore
    DeadlineGlobals.initGroup = "none" # type: ignore
    DeadlineGlobals.initPriority = 50 # type: ignore
    DeadlineGlobals.initTaskTimeout = 0 # type: ignore
    DeadlineGlobals.initAutoTaskTimeout = False # type: ignore
    DeadlineGlobals.initConcurrentTasks = 1 # type: ignore
    DeadlineGlobals.initLimitConcurrentTasks = True # type: ignore
    DeadlineGlobals.initMachineLimit = 0 # type: ignore
    DeadlineGlobals.initIsBlacklist = False # type: ignore
    DeadlineGlobals.initMachineList = "" # type: ignore
    DeadlineGlobals.initLimitGroups = "" # type: ignore
    DeadlineGlobals.initDependencies = "" # type: ignore
    DeadlineGlobals.initOnComplete = "Nothing" # type: ignore
    DeadlineGlobals.initSubmitSuspended = False # type: ignore
    DeadlineGlobals.initChunkSize = 10 # type: ignore
    DeadlineGlobals.initThreads = 0 # type: ignore
    DeadlineGlobals.initMemoryUsage = 0 # type: ignore
    DeadlineGlobals.initSeparateJobs = False # type: ignore
    DeadlineGlobals.initSeparateJobDependencies = False # type: ignore
    DeadlineGlobals.initSeparateTasks = False # type: ignore
    DeadlineGlobals.initUseNodeRange = True # type: ignore
    DeadlineGlobals.initReadFileOnly = False # type: ignore
    DeadlineGlobals.initSelectedOnly = False # type: ignore
    DeadlineGlobals.initSubmitScene = False # type: ignore
    DeadlineGlobals.initBatchMode = True # type: ignore
    DeadlineGlobals.initContinueOnError = False # type: ignore
    DeadlineGlobals.initUseGpu = False # type: ignore
    DeadlineGlobals.initUseSpecificGpu = False # type: ignore
    DeadlineGlobals.initChooseGpu = 0 # type: ignore
    DeadlineGlobals.initEnforceRenderOrder = False # type: ignore
    DeadlineGlobals.initStackSize = 0 # type: ignore
    DeadlineGlobals.initRenderMode = dlRenderModes[0] # type: ignore
    DeadlineGlobals.initPerformanceProfiler = False # type: ignore
    DeadlineGlobals.initReloadPlugin = False # type: ignore
    DeadlineGlobals.initPerformanceProfilerPath = "" # type: ignore
    DeadlineGlobals.initPrecompFirst = False # type: ignore
    DeadlineGlobals.initPrecompOnly = False # type: ignore
    DeadlineGlobals.initSmartVectorOnly = False # type: ignore
    DeadlineGlobals.initEddyCacheOnly = False # type: ignore
    DeadlineGlobals.initExtraInfo0 = "" # type: ignore
    DeadlineGlobals.initExtraInfo1 = "" # type: ignore
    DeadlineGlobals.initExtraInfo2 = "" # type: ignore
    DeadlineGlobals.initExtraInfo3 = "" # type: ignore
    DeadlineGlobals.initExtraInfo4 = "" # type: ignore
    DeadlineGlobals.initExtraInfo5 = "" # type: ignore
    DeadlineGlobals.initExtraInfo6 = "" # type: ignore
    DeadlineGlobals.initExtraInfo7 = "" # type: ignore
    DeadlineGlobals.initExtraInfo8 = "" # type: ignore
    DeadlineGlobals.initExtraInfo9 = "" # type: ignore

    DeadlineGlobals.initUseNukeX = False # type: ignore
    if nuke.env[ 'nukex' ]:
        DeadlineGlobals.initUseNukeX = True # type: ignore
        
    configFile = os.path.join(deadlineSettings, "nuke_py_submission.ini")  # type: str
    
    ReadStickySettings(configFile)
    
    if initFrameListMode != "Custom":
        startFrame = nuke.Root().firstFrame() # type: int
        endFrame = nuke.Root().lastFrame() # type: int
        if initFrameListMode == "Input":
            try:
                activeInput = nuke.activeViewer().activeInput()
                startFrame = nuke.activeViewer().node().input(activeInput).frameRange().first()
                endFrame = nuke.activeViewer().node().input(activeInput).frameRange().last()
            except:
                pass
        
        if startFrame == endFrame:
            DeadlineGlobals.initFrameList = str(startFrame) # type: ignore
        else:
            DeadlineGlobals.initFrameList = str(startFrame) + "-" + str(endFrame) # type: ignore
    else:
        if initCustomFrameList == None or initCustomFrameList.strip() == "": # type: ignore
            startFrame = nuke.Root().firstFrame()
            endFrame = nuke.Root().lastFrame()
            if startFrame == endFrame:
                DeadlineGlobals.initFrameList = str(startFrame) # type: ignore
            else:
                DeadlineGlobals.initFrameList = str(startFrame) + "-" + str(endFrame) # type: ignore
        else:
            DeadlineGlobals.initFrameList = initCustomFrameList.strip() # type: ignore
    
    # Run the sanity check script if it exists, which can be used to set some initial values.
    sanityCheckFile = os.path.join(submissionInfo[ "RepoDirs" ][ "submission/Nuke/Main" ].strip(), "CustomSanityChecks.py") # type: str
    if os.path.isfile(sanityCheckFile):
        print("Running sanity check script: " + sanityCheckFile)
        try:
            import CustomSanityChecks
            sanityResult = CustomSanityChecks.RunSanityCheck() # type: bool
            if not sanityResult:
                print("Sanity check returned false, exiting")
                return
        except:
            print("Could not run CustomSanityChecks.py script")
            print(traceback.format_exc())
    
    if DeadlineGlobals.initPriority > maximumPriority: # type: ignore
        DeadlineGlobals.initPriority = (maximumPriority // 2) # type: ignore
    
    # Both of these can't be enabled!
    if DeadlineGlobals.initSeparateJobs and DeadlineGlobals.initSeparateTasks: # type: ignore
        DeadlineGlobals.initSeparateTasks = False # type: ignore

    extraInfo = [ "" ] * 10 # type: List[str]
    extraInfo[ 0 ] = DeadlineGlobals.initExtraInfo0 # type: ignore
    extraInfo[ 1 ] = DeadlineGlobals.initExtraInfo1 # type: ignore
    extraInfo[ 2 ] = DeadlineGlobals.initExtraInfo2 # type: ignore
    extraInfo[ 3 ] = DeadlineGlobals.initExtraInfo3 # type: ignore
    extraInfo[ 4 ] = DeadlineGlobals.initExtraInfo4 # type: ignore
    extraInfo[ 5 ] = DeadlineGlobals.initExtraInfo5 # type: ignore
    extraInfo[ 6 ] = DeadlineGlobals.initExtraInfo6 # type: ignore
    extraInfo[ 7 ] = DeadlineGlobals.initExtraInfo7 # type: ignore
    extraInfo[ 8 ] = DeadlineGlobals.initExtraInfo8 # type: ignore
    extraInfo[ 9 ] = DeadlineGlobals.initExtraInfo9 # type: ignore

    
    # Check for potential issues and warn user about any that are found.
    warningMessages = "" # type: str
    nodeClasses = [ "Write", "DeepWrite", "WriteGeo" ] # type: List[str]
    writeNodes = RecursiveFindNodes(nodeClasses, nuke.Root())
    precompWriteNodes = RecursiveFindNodesInPrecomp(nodeClasses, nuke.Root())
    eddyCacheNodes = RecursiveFindNodes("EddyCacheNode", nuke.Root())

    print("Found a total of %d write nodes" % len(writeNodes))
    print("Found a total of %d write nodes within precomp nodes" % len(precompWriteNodes))
    print("Found a total of %d nodes within Eddy cache nodes" % len(eddyCacheNodes))

    # Smart Vectors no longer render as of 11.2, so we disable all smart vector render functionality here.
    smartVectorNodes = [ ] # type: List
    if DeadlineDialog.getNukeVersion() < (11, 2):
        smartVectorNodes = RecursiveFindNodes("SmartVector", nuke.Root())
        print("Found a total of %d nodes within smart vector nodes" % len(smartVectorNodes))
    DeadlineGlobals.smartVectorNodes = smartVectorNodes # type: ignore
    
    # Check all the output filenames if they are local or not padded (non-movie files only).
    outputCount = 0 # type: int
    
    for node in (writeNodes + smartVectorNodes + eddyCacheNodes):
        # Need at least one write node that is enabled, and not set to read in as well.
        if not IsNodeReadingOrDisabled(node):
            outputCount += 1
            filename = get_filename(node)

            if not filename:
                if node.Class() != "SmartVector":
                    warningMessages = warningMessages + "Output path for '%s' node '%s' is empty\n\n" % (node.Class(), node.name())
            else:
                if node.Class() == "SmartVector" or node.Class() == "EddyCacheNode":
                    fileType = os.path.splitext(filename) # type: ignore
                else:
                    fileType = node.knob('file_type').value()

                if IsPathLocal(filename):
                    warningMessages = warningMessages + "Output path for '%s' node '%s' is local:\n%s\n\n" % (node.Class(), node.name(), filename)
                if not HasExtension(filename) and fileType.strip() == "": # type: ignore
                    warningMessages = warningMessages + "Output path for '%s' node '%s' has no extension:\n%s\n\n" % (node.Class(), node.name(), filename)
                if not IsMovie(filename) and not IsPadded(os.path.basename(filename)):
                    warningMessages = warningMessages + "Output path for '%s' node '%s' is not padded:\n%s\n\n" % (node.Class(), node.name(), filename)

    # Warn if there are no write nodes.
    if outputCount == 0 and not noRoot:
        warningMessages = warningMessages + "At least one enabled write node that has 'read file' disabled is required to render\n\n"
    
    if len(nuke.views())  == 0:
        warningMessages = warningMessages + "At least one view is required to render\n\n"
    
    # If there are any warning messages, show them to the user.
    if warningMessages != "":
        warningMessages = warningMessages + "Do you still wish to submit this job to Deadline?"
        answer = nuke.ask(warningMessages)
        if not answer:
            return
    print("Creating submission dialog...")
    
    # Create an instance of the submission dialog.
    if len(valid_projects) > 0:
        dialog = DeadlineContainerDialog(maximumPriority, pools, secondaryPools, groups, valid_projects, not noRoot)
    else:
        dialog = DeadlineDialog(maximumPriority, pools, secondaryPools, groups)
    
    # Set the initial values.
    safeSetValue(dialog.jobName, DeadlineGlobals.initJobName) # type: ignore
    safeSetValue(dialog.comment, DeadlineGlobals.initComment) # type: ignore
    safeSetValue(dialog.department, DeadlineGlobals.initDepartment) # type: ignore
    
    safeSetValue(dialog.pool, DeadlineGlobals.initPool) # type: ignore
    safeSetValue(dialog.secondaryPool, DeadlineGlobals.initSecondaryPool) # type: ignore
    safeSetValue(dialog.group, DeadlineGlobals.initGroup) # type: ignore
    safeSetValue(dialog.priority, DeadlineGlobals.initPriority) # type: ignore
    safeSetValue(dialog.taskTimeout, DeadlineGlobals.initTaskTimeout) # type: ignore
    safeSetValue(dialog.autoTaskTimeout, DeadlineGlobals.initAutoTaskTimeout) # type: ignore
    safeSetValue(dialog.concurrentTasks, DeadlineGlobals.initConcurrentTasks) # type: ignore
    safeSetValue(dialog.limitConcurrentTasks, DeadlineGlobals.initLimitConcurrentTasks) # type: ignore
    safeSetValue(dialog.machineLimit, DeadlineGlobals.initMachineLimit) # type: ignore
    safeSetValue(dialog.isBlacklist, DeadlineGlobals.initIsBlacklist) # type: ignore
    safeSetValue(dialog.machineList, DeadlineGlobals.initMachineList) # type: ignore
    safeSetValue(dialog.limitGroups, DeadlineGlobals.initLimitGroups) # type: ignore
    safeSetValue(dialog.dependencies, DeadlineGlobals.initDependencies) # type: ignore
    safeSetValue(dialog.onComplete, DeadlineGlobals.initOnComplete) # type: ignore
    safeSetValue(dialog.submitSuspended, DeadlineGlobals.initSubmitSuspended) # type: ignore
    
    safeSetValue(dialog.frameListMode, initFrameListMode)
    safeSetValue(dialog.frameList, DeadlineGlobals.initFrameList) # type: ignore
    safeSetValue(dialog.chunkSize, DeadlineGlobals.initChunkSize) # type: ignore
    safeSetValue(dialog.threads, DeadlineGlobals.initThreads) # type: ignore
    safeSetValue(dialog.memoryUsage, DeadlineGlobals.initMemoryUsage) # type: ignore
    safeSetValue(dialog.separateJobs, DeadlineGlobals.initSeparateJobs) # type: ignore
    safeSetValue(dialog.separateJobDependencies, DeadlineGlobals.initSeparateJobDependencies) # type: ignore
    safeSetValue(dialog.separateTasks, DeadlineGlobals.initSeparateTasks) # type: ignore
    safeSetValue(dialog.readFileOnly, DeadlineGlobals.initReadFileOnly) # type: ignore
    safeSetValue(dialog.selectedOnly, DeadlineGlobals.initSelectedOnly) # type: ignore
    safeSetValue(dialog.submitScene, DeadlineGlobals.initSubmitScene) # type: ignore
    safeSetValue(dialog.useNukeX, DeadlineGlobals.initUseNukeX) # type: ignore
    safeSetValue(dialog.continueOnError, DeadlineGlobals.initContinueOnError) # type: ignore
    safeSetValue(dialog.batchMode, DeadlineGlobals.initBatchMode) # type: ignore
    safeSetValue(dialog.useNodeRange, DeadlineGlobals.initUseNodeRange) # type: ignore
    safeSetValue(dialog.useGpu, DeadlineGlobals.initUseGpu) # type: ignore
    safeSetValue(dialog.useSpecificGpu, DeadlineGlobals.initUseSpecificGpu) # type: ignore
    safeSetValue(dialog.chooseGpu, DeadlineGlobals.initChooseGpu) # type: ignore
    safeSetValue(dialog.enforceRenderOrder, DeadlineGlobals.initEnforceRenderOrder) # type: ignore
    safeSetValue(dialog.renderMode, DeadlineGlobals.initRenderMode) # type: ignore
    safeSetValue(dialog.performanceProfiler, DeadlineGlobals.initPerformanceProfiler) # type: ignore
    safeSetValue(dialog.reloadPlugin, DeadlineGlobals.initReloadPlugin) # type: ignore
    safeSetValue(dialog.performanceProfilerPath, DeadlineGlobals.initPerformanceProfilerPath) # type: ignore
    safeSetValue(dialog.precompFirst, DeadlineGlobals.initPrecompFirst) # type: ignore
    safeSetValue(dialog.precompOnly, DeadlineGlobals.initPrecompOnly) # type: ignore
    safeSetValue(dialog.smartVectorOnly, DeadlineGlobals.initSmartVectorOnly) # type: ignore
    safeSetValue(dialog.eddyCacheOnly, DeadlineGlobals.initEddyCacheOnly) # type: ignore
    safeSetValue(dialog.stackSize, DeadlineGlobals.initStackSize) # type: ignore
    
    dialog.separateJobs.setEnabled(len(writeNodes) + len(smartVectorNodes) > 0)
    dialog.separateTasks.setEnabled(len(writeNodes) + len(smartVectorNodes) > 0)
    
    dialog.separateJobDependencies.setEnabled(dialog.separateJobs.value())
    dialog.useNodeRange.setEnabled(dialog.separateJobs.value() or dialog.separateTasks.value())
    dialog.precompFirst.setEnabled(dialog.separateJobs.value() or dialog.separateTasks.value())
    dialog.precompOnly.setEnabled(dialog.separateJobs.value() or dialog.separateTasks.value())
    dialog.smartVectorOnly.setEnabled(dialog.separateJobs.value() or dialog.separateTasks.value())
    dialog.eddyCacheOnly.setEnabled(dialog.separateJobs.value() or dialog.separateTasks.value())
    dialog.frameList.setEnabled(not (dialog.separateJobs.value() and dialog.useNodeRange.value()) and not dialog.separateTasks.value())

    dialog.useSpecificGpu.setEnabled(dialog.useGpu.value())
    dialog.chooseGpu.setEnabled(dialog.useGpu.value() and dialog.useSpecificGpu.value())

    statusMessage = retrievePipelineToolStatus() # type: str
    updatePipelineToolStatusLabel(statusMessage)

    # Show the dialog.
    success = False # type: bool
    while not success:
        success = dialog.ShowDialog()
        if not success:
            WriteStickySettings(dialog, configFile)
            return
        
        errorMessages = "" # type: str
        warningMessages = ""
        
        # Check that frame range is valid.
        if dialog.frameList.value().strip() == "":
            errorMessages = errorMessages + "No frame list has been specified.\n\n"
        
        # If submitting separate write nodes, make sure there are jobs to submit
        if dialog.readFileOnly.value() or dialog.selectedOnly.value():
            validNodeFound = False
            if not dialog.precompOnly.value():
                for node in writeNodes:
                    if not node.knob('disable').value():
                        validNodeFound = True
                        if dialog.readFileOnly.value():
                            if node.knob('reading') and not node.knob('reading').value():
                                validNodeFound = False
                        if dialog.selectedOnly.value() and not IsNodeOrParentNodeSelected(node):
                            validNodeFound = False
                        
                        if validNodeFound:
                            break
            else:
                for node in precompWriteNodes:
                    if not node.knob('disable').value():
                        validNodeFound = True
                        if dialog.readFileOnly.value():
                            if node.knob('reading') and not node.knob('reading').value():
                                validNodeFound = False
                        if dialog.selectedOnly.value() and not IsNodeOrParentNodeSelected(node):
                            validNodeFound = False
                        
                        if validNodeFound:
                            break
                    
            if not validNodeFound:
                if dialog.readFileOnly.value() and dialog.selectedOnly.value():
                    errorMessages = errorMessages + "There are no selected write nodes with 'Read File' enabled, so there are no jobs to submit.\n\n"
                elif dialog.readFileOnly.value():
                    errorMessages = errorMessages + "There are no write nodes with 'Read File' enabled, so there are no jobs to submit.\n\n"
                elif dialog.selectedOnly.value():
                    errorMessages = errorMessages + "There are no selected write nodes, so there are no jobs to submit.\n\n"

        if dialog.smartVectorOnly.value() and len(smartVectorNodes) == 0:
            errorMessages = errorMessages + "There are no smart vector nodes, so there are no jobs to submit.\n\n"
        
        if dialog.eddyCacheOnly.value() and len(eddyCacheNodes) == 0:
            errorMessages = errorMessages + "There are no Eddy cache nodes, so there are no jobs to submit.\n\n"
        
        # Check if at least one view has been selected.
        if dialog.chooseViewsToRender.value():
            viewCount = 0
            for vk in dialog.viewToRenderKnobs:
                if vk[0].value():
                    viewCount += 1
                    
            if viewCount == 0:
                errorMessages = errorMessages + "There are no views selected.\n\n"
                
        if len(valid_projects) > 0:
            #We need to check if there is a root comp, or if sequences have been specified
            if noRoot and not dialog.submitSequenceJobs.value():
                errorMessages = errorMessages + "There is no saved comp selected in the node graph and Sequence Job Submission is disabled.\n\n"
            
            elif noRoot and dialog.chooseCompsToRender.value():
                #Check if any sequences were selected
                found = False
                for knob in dialog.sequenceKnobs:
                    if knob[0].value() and knob[1][1] == dialog.studioProject.value():
                        found = True
                        break
                
                if not found:
                    errorMessages = errorMessages + "Sequence Job Submission and Choose Sequences To Render are enabled but no sequences have been selected. Please select some sequences to render or disable Choose Sequences To Render.\n\n"
        
        # Check if proxy mode is enabled and Render using Proxy Mode is disabled, then warn the user.
        if root.proxy() and dialog.renderMode.value() == dlRenderModes[0]:
            warningMessages = warningMessages + "Proxy Mode is enabled and the scene is being rendered using scene settings, which may cause problems when rendering through Deadline.\n\n"
        
        # Check if the script file is local and not being submitted to Deadline.
        if not dialog.submitScene.value():
            if IsPathLocal(root.name()):
                warningMessages = warningMessages + "Nuke script path is local and is not being submitted to Deadline:\n" + root.name() + "\n\n"

        # Check Performance Profile Path
        if dialog.performanceProfiler.value():
            if not os.path.exists(dialog.performanceProfilerPath.value()):
                errorMessages += "Performance Profiler is enabled, but an XML directory has not been selected (or it does not exist). Either select a valid network path, or disable Performance Profiling.\n\n"
        
        if dialog.separateTasks.value() and dialog.frameListMode.value() == "Custom" and not dialog.useNodeRange.value():
            errorMessages += "Custom frame list is not supported when submitting write nodes as separate tasks. Please choose Global or Input, or enable Use Node's Frame List.\n\n"

        if len(smartVectorNodes) > 0:
            smartVectorsMissingFrames = []
            for node in smartVectorNodes:
                if not nuke.filename(node):
                    print("Warning: %s is missing an output path" % node.name())
                elif not is_node_rendered(node):
                    smartVectorsMissingFrames.append(node.name())
            
            if len(smartVectorsMissingFrames) > 0 and not (dialog.separateJobs.value() or dialog.separateTasks.value()):
                warningMessages += 'The following Smart Vectors are missing output: \n%s\n\n Please make sure that you render the Smart Vectors or enable either "Submit Write Nodes As Separate Jobs" or "Submit Write Nodes As Separate Tasks For The Same Job.\n\n' % "\n".join(smartVectorsMissingFrames)
        
        if len(eddyCacheNodes) > 0:
            EddyCacheMissingFrames = []
            for node in eddyCacheNodes:
                if not get_filename(node):
                    print("Warning: %s is missing an output path" % node.name())
                elif not is_node_rendered(node):
                    EddyCacheMissingFrames.append(node.name())
            
            if len(EddyCacheMissingFrames) > 0 and not (dialog.separateJobs.value() or dialog.separateTasks.value()):
                warningMessages += 'The following Eddy caches are missing output: \n%s\n\n Please make sure that you render the Eddy caches or enable either "Submit Write Nodes As Separate Jobs" or "Submit Write Nodes As Separate Tasks For The Same Job.\n\n' % "\n".join(EddyCacheMissingFrames)
        
        # Alert the user of any errors.
        if errorMessages != "":
            errorMessages = errorMessages + "Please fix these issues and submit again."
            nuke.message(errorMessages)
            success = False
        
        # Alert the user of any warnings.
        if success and warningMessages != "":
            warningMessages = warningMessages + "Do you still wish to submit this job to Deadline?"
            answer = nuke.ask(warningMessages)
            if not answer:
                WriteStickySettings(dialog, configFile)
                return
    
    #Save sticky settings
    WriteStickySettings(dialog, configFile)
    
    tempJobName = dialog.jobName.value()
    tempDependencies = dialog.dependencies.value() # type: str
    tempFrameList = dialog.frameList.value().strip()
    tempChunkSize = dialog.chunkSize.value() # type: int
    tempIsMovie = False # type: bool
    semaphore = threading.Semaphore() # type: threading.Semaphore
            
    if len(valid_projects) > 0 and dialog.submitSequenceJobs.value():
        SubmitSequenceJobs(dialog, deadlineTemp, tempDependencies, semaphore, extraInfo)
    else:
        # Check if we should be submitting a separate job for each write node.
        if dialog.separateJobs.value():
            jobCount = 0 # type: int
            previousJobId = "" # type: str
            submitThreads = [] # type: List[threading.Thread]
            
            tempwriteNodes = [] # type: List[Any]
            
            if dialog.selectedOnly.value():
                writeNodes = list(filter(IsNodeOrParentNodeSelected, writeNodes)) # type: ignore
            
            nodeNames, num = FindNodesHasNoRenderOrder(writeNodes)
            
            if num > 0 and not nuke.ask('No render order nodes found: %s \n\n' % (nodeNames) + 
                                        'Do you still wish to submit this job to Deadline?'):
                return
            
            if dialog.precompOnly.value():
                tempWriteNodes = sorted(precompWriteNodes, key = lambda node: getRenderOrder(node))
            elif dialog.precompFirst.value():
                tempWriteNodes = sorted(precompWriteNodes, key = lambda node: getRenderOrder(node))
                
                additionalNodes = [item for item in writeNodes if item not in precompWriteNodes] # type: List[Any]
                additionalNodes = sorted(additionalNodes, key = lambda node: getRenderOrder(node))
                tempWriteNodes.extend(additionalNodes)
            elif dialog.smartVectorOnly.value():
                tempWriteNodes = smartVectorNodes
            elif dialog.eddyCacheOnly.value():
                tempWriteNodes = eddyCacheNodes
            else:
                innerTempNodes  = sorted(smartVectorNodes + eddyCacheNodes, key = lambda node: getRenderOrder(node)) # type: List[Any]

                tempWriteNodes = sorted(writeNodes, key = lambda node: getRenderOrder(node))
                innerTempNodes.extend(tempWriteNodes)
                tempWriteNodes = innerTempNodes
            
            for node in tempWriteNodes:
                print("Now processing %s" % node.name())
                #increment job count -- will be used so not all submissions try to write to the same .job files simultaneously
                jobCount += 1
                    
                # Check if we should enter the loop for this node.
                enterLoop = False # type: bool
                if not node.knob('disable').value():
                    enterLoop = True
                    if dialog.readFileOnly.value() and node.knob('reading'):
                        enterLoop = enterLoop and node.knob('reading').value()
                    if dialog.selectedOnly.value():
                        enterLoop = enterLoop and IsNodeOrParentNodeSelected(node)
                
                if enterLoop:
                    tempJobName = dialog.jobName.value() + " - " + node.name()
                    tempFrameList = GetFrameList(node)
                    
                    if node.Class() == "EddyCacheNode":
                        tempChunkSize = 1000000
                        tempIsMovie = False
                    elif IsMovie(get_filename(node)):
                        tempChunkSize = 1000000
                        tempIsMovie = True
                    else:
                        tempChunkSize = dialog.chunkSize.value()
                        tempIsMovie = False
                    
                    #if creating sequential dependencies, parse for JobId to be used for the next Job's dependencies
                    if dialog.separateJobDependencies.value():
                        if jobCount > 1 and not tempDependencies == "":
                            tempDependencies = tempDependencies + "," + previousJobId
                        elif tempDependencies == "":
                            tempDependencies = previousJobId
                            
                        submitJobResults = SubmitJob(dialog, root, node, tempWriteNodes, deadlineTemp, tempJobName, tempFrameList, tempDependencies, tempChunkSize, tempIsMovie, jobCount, semaphore, extraInfo)                         
                        for line in submitJobResults.splitlines():
                            if line.startswith("JobID="):
                                previousJobId = line[6:]
                                break
                        tempDependencies = dialog.dependencies.value() #reset dependencies
                    else: #Create a new thread to do the submission
                        print("Spawning submission thread #%d..." % jobCount)
                        submitThread = threading.Thread(None, SubmitJob, args = (dialog, root, node, tempWriteNodes, deadlineTemp, tempJobName, tempFrameList, tempDependencies, tempChunkSize, tempIsMovie, jobCount, semaphore, extraInfo)) # type: threading.Thread
                        submitThread.start()
                        submitThreads.append(submitThread)
            
            if not dialog.separateJobDependencies.value():
                print("Spawning results thread...")
                resultsThread = threading.Thread(None, WaitForSubmissions, args = (submitThreads,))
                resultsThread.start()
                
        elif dialog.separateTasks.value():
            #Create a new thread to do the submission
            tempWriteNodes = []
            if dialog.precompOnly.value():
                tempWriteNodes = sorted(precompWriteNodes, key = lambda node: getRenderOrder(node))
            elif dialog.precompFirst.value():
                tempWriteNodes = sorted(precompWriteNodes, key = lambda node: getRenderOrder(node))
                additionalNodes = [item for item in writeNodes if item not in precompWriteNodes]
                additionalNodes = sorted(additionalNodes, key = lambda node: getRenderOrder(node))
                tempWriteNodes.extend(additionalNodes)
            elif dialog.smartVectorOnly.value():
                tempWriteNodes = smartVectorNodes
            elif dialog.eddyCacheOnly.value():
                tempWriteNodes = eddyCacheNodes
            else:
                innerTempNodes = sorted(smartVectorNodes + eddyCacheNodes, key = lambda node: getRenderOrder(node))

                tempWriteNodes = sorted(writeNodes, key = lambda node: getRenderOrder(node))
                innerTempNodes.extend(tempWriteNodes)
                tempWriteNodes = innerTempNodes
                            
            print("Spawning submission thread...")
            submitThread = threading.Thread(None, SubmitJob, None, (dialog, root, None, tempWriteNodes, deadlineTemp, tempJobName, tempFrameList, tempDependencies, tempChunkSize, tempIsMovie, 1, None, extraInfo))
            submitThread.start()
        else:
            for tempNode in writeNodes:
                if not tempNode.knob('disable').value():
                    enterLoop = True
                    if dialog.readFileOnly.value() and tempNode.knob('reading'):
                        enterLoop = enterLoop and tempNode.knob('reading').value()
                    if dialog.selectedOnly.value():
                        enterLoop = enterLoop and IsNodeOrParentNodeSelected(tempNode)
                    
                    if enterLoop:
                        if IsMovie(tempNode.knob('file').value()):
                            tempChunkSize = 1000000
                            tempIsMovie = True
                            break

            smartVectorNodes.extend(writeNodes)
            writeNodes = smartVectorNodes
            
            #Create a new thread to do the submission
            print("Spawning submission thread...")
            submitThread = threading.Thread(None, SubmitJob, None, (dialog, root, None, writeNodes, deadlineTemp, tempJobName, tempFrameList, tempDependencies, tempChunkSize, tempIsMovie, 1, None, extraInfo))
            submitThread.start()  
    
    print("Main Deadline thread exiting")

def getRenderOrder(node):
    # type: (Any) -> int
    try:
        value = node[ 'render_order' ].value()
    except NameError:
        # maxint was removed from sys in python 3
        if sys.version_info[0] > 2:
            value = sys.maxsize
        else:
            value = sys.maxint
    return value

def IsNodeOrParentNodeSelected(node):
    # type: (Any) -> bool
    if node.isSelected():
        return True
    
    parentNode = nuke.toNode('.'.join(node.fullName().split('.')[:-1]))
    if parentNode:
        return IsNodeOrParentNodeSelected(parentNode)
    
    return False

def WaitForSubmissions(submitThreads):
    # type: (List[Any]) -> None
    for thread in submitThreads:
        thread.join()
    
    results = "Job submission complete. See the Script Editor output window for more information." # type: str
    nuke.executeInMainThread(nuke.message, results)
    
    print("Results thread exiting")

################################################################################
## DEBUGGING
################################################################################
#
# # Get the repository root
# path = CallDeadlineCommand(["-GetRepositoryPath", "submission/Nuke/Main"]).replace("\\", "/")
# if path:
#     # Add the path to the system path
#     if path not in sys.path:
#         print("Appending \"" + path + "\" to system path to import SubmitNukeToDeadline module")
#         sys.path.append(path)
#
#     # Call the main function to begin job submission.
#     SubmitToDeadline()
# else:
#     nuke.message(
#         "The SubmitNukeToDeadline.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository.")
