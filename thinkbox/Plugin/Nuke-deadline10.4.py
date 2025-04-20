#!/usr/bin/env python3

from __future__ import absolute_import
import re
import os
import sys
from shutil import copyfile

from System import Environment
from System.Diagnostics import ProcessStartInfo, Process, ProcessPriorityClass
from System.IO import Path, Directory, File

from Deadline.Plugins import DeadlinePlugin, PluginType
from Deadline.Scripting import SystemUtils, PathUtils, RepositoryUtils

from FranticX.Processes import ManagedProcess
from six.moves import range

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return NukePlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Nuke plugin.
######################################################################
class NukePlugin (DeadlinePlugin):
    Version = -1.0
    BatchMode = False
    Process = None
    ProcessName = "Nuke"
    
    ## Utility functions
    def WritePython( self, statement ):
        self.FlushMonitoredManagedProcessStdout( self.ProcessName )
        self.WriteStdinToMonitoredManagedProcess( self.ProcessName, statement )
        self.WaitForProcess()
    
    def WaitForProcess( self ):
        self.FlushMonitoredManagedProcessStdout( self.ProcessName )
        self.WriteStdinToMonitoredManagedProcess( self.ProcessName, self.Process.ReadyForInputCommand() )
        while not self.Process.IsReadyForInput():
            self.VerifyMonitoredManagedProcess( self.ProcessName )
            self.FlushMonitoredManagedProcessStdout( self.ProcessName )
            
            blockingDialogMessage = self.CheckForMonitoredManagedProcessPopups( self.ProcessName )
            if( blockingDialogMessage != "" ):
                self.FailRender( blockingDialogMessage )
            
            if self.IsCanceled():
                self.FailRender( "Received cancel task command" )
            
            SystemUtils.Sleep( 100 )
        
        self.Process.ResetReadyForInput()
        
    def scrubLibPath( self, envVar ):
        ldPaths = Environment.GetEnvironmentVariable(envVar)
        if ldPaths:
            ldPaths = ldPaths.split(":")
            newLDPaths = []
            for ldPath in ldPaths:
                if not re.search("Deadline",ldPath):
                    newLDPaths.append(ldPath)
            
            if len(newLDPaths):
                newLDPaths = ":".join(newLDPaths)
            else:
                newLDPaths = ""
            
            self.SetProcessEnvironmentVariable(envVar,newLDPaths)
            del ldPaths
            del newLDPaths
        
    def scrubLibPaths( self ):
        """This solves a library / plugin linking issue with Nuke that occurs
        when Nuke sees the IlmImf library included with Deadline.  It appears that library
        conflicts with the exrWriter and causes it to error out.  This solution
        removes the Deadline library paths from the LD and DYLD library paths
        before Deadline launches Nuke, so Nuke never sees that library.  It seems like
        this fixes the problem. Thanks to Matt Griffith for figuring this one out!"""
        
        self.LogInfo("Scrubbing the LD and DYLD LIBRARY paths")
        
        self.scrubLibPath("LD_LIBRARY_PATH")
        self.scrubLibPath("DYLD_LIBRARY_PATH")
        self.scrubLibPath("DYLD_FALLBACK_LIBRARY_PATH")
        self.scrubLibPath("DYLD_FRAMEWORK_PATH")
        self.scrubLibPath("DYLD_FALLBACK_FRAMEWORK_PATH")
    
    def prepForOFX(self):
        """This solves an issue where Nuke can fail to create the ofxplugincache,
        which causes any script submited to Deadline that uses an OFX plugin to fail.
        Thanks to Matt Griffith for figuring this one out!"""
        
        self.LogInfo("Prepping OFX cache")
        nukeTempPath = ""
        
        # temp path for Nuke
        if SystemUtils.IsRunningOnWindows():
            # on windows, nuke temp path is [Temp]\nuke
            nukeTempPath = Path.Combine( Path.GetTempPath(), "nuke" )
        else:
            # on *nix, nuke temp path is "/var/tmp/nuke-u" + 'id -u'
            id = PathUtils.GetApplicationPath( "id" )
            if len(id) == 0:
                self.LogWarning( "Could not get path for 'id' process, skipping OFX cache prep" )
                return
            
            startInfo = ProcessStartInfo( id, "-u" )
            startInfo.RedirectStandardOutput = True
            startInfo.UseShellExecute = False
            
            idProcess = Process()
            idProcess.StartInfo = startInfo
            idProcess.Start()
            idProcess.WaitForExit()
            
            userId = idProcess.StandardOutput.ReadLine()
            
            idProcess.StandardOutput.Close()
            idProcess.StandardOutput.Dispose()
            idProcess.Close()
            idProcess.Dispose()
            
            if len(userId) == 0:
                self.LogWarning( "Failed to get user id, skipping OFX cache prep" )
                return
            
            nukeTempPath = "/var/tmp/nuke-u" + userId
        
        self.LogInfo( "Checking Nuke temp path: " + nukeTempPath)
        if Directory.Exists(nukeTempPath):
            self.LogInfo( "Path already exists" )
        else:
            self.LogInfo( "Path does not exist, creating it..." )
            Directory.CreateDirectory(nukeTempPath) #creating this level of the nuke temp directory seems to be enough to let the ofxplugincache get created -mg
            
            if Directory.Exists(nukeTempPath):
                self.LogInfo( "Path now exists" )
            else:
                self.LogWarning( "Unable to create path, skipping OFX cache prep" )
                return
        
        self.LogInfo("OFX cache prepped")

    def __init__( self ):
        if sys.version_info.major == 3:
            super().__init__()
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob
        self.InitializeProcessCallback += self.InitializeProcess
        self.IsSingleFramesOnlyCallback += self.IsSingleFramesOnly
    
    def Cleanup(self):
        del self.StartJobCallback
        del self.RenderTasksCallback
        del self.EndJobCallback
        del self.InitializeProcessCallback
        del self.IsSingleFramesOnlyCallback
        
        if self.Process:
            self.Process.Cleanup()
            del self.Process
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Advanced
    
    def StartJob( self ):
        # This fixes a library conflict issue on non-Windows systems.
        if not SystemUtils.IsRunningOnWindows():
            self.scrubLibPaths()
        
        if self.GetBooleanConfigEntryWithDefault( "PrepForOFX", True ):
            # Ensure that OFX plugins will work
            try:
                self.prepForOFX()
            except:
                self.LogWarning( "Prepping of OFX cache failed" )
        
        self.Version = float( self.GetPluginInfoEntry( "Version" ) )
        
        # Since we now support minor versions, we should default to the *.0 version if the *.X version they're using isn't supported yet.
        versionNotSupported = "this version is not supported yet"
        nukeExeList = self.GetConfigEntryWithDefault( "RenderExecutable" + str(self.Version).replace( ".", "_" ), versionNotSupported )
        if nukeExeList == versionNotSupported:
            oldVersion = self.Version
            self.Version = float(int(self.Version))
            
            nukeExeList = self.GetConfigEntryWithDefault( "RenderExecutable" + str(self.Version).replace( ".", "_" ), versionNotSupported )
            if nukeExeList == versionNotSupported:
                self.FailRender( "Nuke major version " + str(int(self.Version)) + " is currently not supported." )
            else:
                self.LogWarning( "Nuke minor version " + str(oldVersion) + " is currently not supported, so version " + str(self.Version) + " will be used instead." )
        
        if int(self.Version) == 7 and SystemUtils.IsRunningOnWindows():
            self.SetProcessEnvironmentVariable( "NUKE_USE_FAST_ALLOCATOR", "1" )
        
        self.BatchMode = self.GetBooleanPluginInfoEntryWithDefault( "BatchMode", True )
        
        self.ScriptJob = self.GetBooleanPluginInfoEntryWithDefault( "ScriptJob", False )
        
        if self.BatchMode:
            self.Process = NukeProcess( self, self.Version, self.BatchMode, self.ScriptJob )
            self.StartMonitoredManagedProcess( self.ProcessName, self.Process )
        else:
            if self.ScriptJob:
                self.FailRender( "Script Jobs are only supported in Batch Mode." )
    
    def IsSingleFramesOnly( self ):
        return self.GetBooleanPluginInfoEntryWithDefault( "WriteNodesAsSeparateJobs", False )
    
    def RenderTasks( self ):
        
        if self.BatchMode and self.ScriptJob:
            scriptFileName = self.GetPluginInfoEntry( "ScriptFilename" ).replace( "\\", "/" )
            
            self.WritePython( f"exec(open('{scriptFileName}').read(), globals(), locals())" )

        else:
            if self.GetBooleanPluginInfoEntryWithDefault( "WriteNodesAsSeparateJobs", False ):
                if self.BatchMode:
                    continueOnError = "True" if self.GetBooleanPluginInfoEntryWithDefault( "ContinueOnError", False ) else "False"
                    
                    frame = str(self.GetStartFrame())
                    writeNodeName = self.GetPluginInfoEntry( "WriteNode" + frame )
                    writeNodeStartFrame = self.GetIntegerPluginInfoEntry( "WriteNode" + frame + "StartFrame" )
                    writeNodeEndFrame = self.GetIntegerPluginInfoEntry( "WriteNode" + frame + "EndFrame" )
                    self.LogInfo( "Rendering write node " + writeNodeName)
                    self.WritePython( "nuke.execute(\"%s\", %d, %d, 1, continueOnError=%s)" % ( writeNodeName, writeNodeStartFrame, writeNodeEndFrame, continueOnError ) )
                else:
                    self.RunManagedProcess( NukeProcess( self, self.Version, self.BatchMode, self.ScriptJob ) )
            else:
                if self.BatchMode:
                    frameCount = 0
                    totalFrames = self.GetEndFrame() - self.GetStartFrame() + 1
                    continueOnError = "True" if self.GetBooleanPluginInfoEntryWithDefault( "ContinueOnError", False ) else "False"
                    
                    # Determine if we are rendering specific write nodes, or if we should just render all of them.
                    writeNodeNames = self.GetPluginInfoEntryWithDefault( "WriteNode", "" )
                    if writeNodeNames != "":
                        totalFrames = totalFrames *len(writeNodeNames.split( ',' ))
                        for writeNodeName in writeNodeNames.split( ',' ):
                            #Render the specified node for the given frames
                            self.LogInfo( "Rendering write node " + writeNodeName)
                            
                            scriptContents = ""
                            if self.GetBooleanPluginInfoEntryWithDefault( "BatchModeIsMovie", True ):
                                # For movie renders, execute as a single chunk, otherwise only the last frame gets written to the output movie file.
                                scriptContents = ("nuke.execute(\"%s\", %d, %d, 1, continueOnError=%s)\n" % (writeNodeName, self.GetStartFrame(), self.GetEndFrame(), continueOnError))
                            else:
                                # Build up a script that contains multiple executes so that we can report progress after each frame.
                                for frame in range(self.GetStartFrame(), self.GetEndFrame()+1):
                                    frameCount = frameCount + 1
                                    scriptContents = scriptContents + ("nuke.execute(\"%s\", %d, %d, 1, continueOnError=%s); print(\"Frame %d (%d of %d)\")\n" % (writeNodeName, frame, frame, continueOnError, frame, frameCount, totalFrames))
                            
                            # Now execute the full script.
                            self.WritePython(scriptContents)
                    else:
                        # Executing the root node will render all the enabled write nodes for the specified frame range
                        self.LogInfo( "Rendering all enabled write nodes" )
                        
                        scriptContents = ""
                        if self.GetBooleanPluginInfoEntryWithDefault( "BatchModeIsMovie", True ):
                            # For movie renders, execute as a single chunk, otherwise only the last frame gets written to the output movie file.
                            scriptContents = ("nuke.execute(nuke.Root(), %d, %d, 1, continueOnError=%s)\n" % (self.GetStartFrame(), self.GetEndFrame(), continueOnError))
                        else:
                            # Build up a script that contains multiple executes so that we can report progress after each frame.
                            for frame in range(self.GetStartFrame(), self.GetEndFrame()+1):
                                frameCount = frameCount + 1
                                scriptContents = scriptContents + ("nuke.execute(nuke.Root(), %d, %d, 1, continueOnError=%s); print(\"Frame %d (%d of %d)\")\n" % (frame, frame, continueOnError, frame, frameCount, totalFrames))
                                
                        # Now execute the full script.
                        self.WritePython(scriptContents)
                else:
                    self.Process = NukeProcess( self, self.Version, self.BatchMode, self.ScriptJob )
                    self.RunManagedProcess( self.Process )
    
    def EndJob( self ):
        if self.BatchMode:
            self.LogInfo( "Ending Nuke Job" )
            
            # Close the script before exiting.
            self.WriteStdinToMonitoredManagedProcess( self.ProcessName, "nuke.scriptClose()" )
            
            # Now close Nuke.
            self.FlushMonitoredManagedProcessStdoutNoHandling( self.ProcessName )
            self.WriteStdinToMonitoredManagedProcess( self.ProcessName, "quit()" )
            self.FlushMonitoredManagedProcessStdoutNoHandling( self.ProcessName )
            self.WaitForMonitoredManagedProcessToExit( self.ProcessName, 5000 )
            self.ShutdownMonitoredManagedProcess( self.ProcessName )

        # Attempt to transfer back any Performance Profiler xml files if "PerformanceProfiler" directory is present in local Worker data directory
        if self.Version >= 9.0 and self.GetBooleanPluginInfoEntryWithDefault( "PerformanceProfiler", False ):
            localDir = Path.Combine( self.GetJobsDataDirectory(), "PerformanceProfiler" )
            if Directory.Exists( localDir ):
                tempPPDir = self.GetPluginInfoEntryWithDefault( "PerformanceProfilerDir", "" )
                serverDir = Path.Combine( tempPPDir, "PerformanceProfiler" )
                self.LogInfo( "Transferring Performance Profiler XML files back to network location" )
                try:
                    if not Directory.Exists( serverDir ):
                        Directory.CreateDirectory( serverDir )

                    fileList = os.listdir( localDir )
                    for file in fileList:
                        copyfile( Path.Combine( localDir, str( file ) ), Path.Combine( serverDir, str( file ) ) )

                    self.LogInfo( "Copied Performance Profiler files to: %s" % serverDir )
                except:
                    self.LogWarning( "Failed to copy Performance Profiler XML files back to: %s" % serverDir )

class NukeProcess (ManagedProcess):
    deadlinePlugin = None
    
    TempSceneFilename = ""
    Version = -1.0
    BatchMode = False
    ReadyForInput = False

    #Utility functions
    def pathMappingWithFilePermissionFix( self, inFileName, outFileName, stringsToReplace, newStrings ):
        RepositoryUtils.CheckPathMappingInFileAndReplace( inFileName, outFileName, stringsToReplace, newStrings )
        if SystemUtils.IsRunningOnLinux() or SystemUtils.IsRunningOnMac():
            os.chmod( outFileName, os.stat( inFileName ).st_mode )
            
    def __init__( self, deadlinePlugin, version, batchMode, scriptJob ):
        if sys.version_info.major == 3:
            super().__init__()
        self.deadlinePlugin = deadlinePlugin
        
        self.Version = version
        self.BatchMode = batchMode
        self.ScriptJob = scriptJob
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback
    
    def InitializeProcess( self ):
        # Set the process specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True
        
        # Set the stdout handlers.
        self.AddStdoutHandlerCallback( "READY FOR INPUT" ).HandleCallback +=  self.HandleReadyForInput
        self.AddStdoutHandlerCallback( ".*ERROR:.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( ".*Error:.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( ".*Error :.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( "Eddy\\[ERROR\\]" ).HandleCallback += self.HandleError
        #self.AddStdoutHandler( ".* seconds to execute", self.HandleProgress )
        #self.AddStdoutHandler( ".* took [0-9]*\\.[0-9]* seconds", self.HandleProgress )
        self.AddStdoutHandlerCallback( "Frame [0-9]+ \\(([0-9]+) of ([0-9]+)\\)" ).HandleCallback += self.HandleProgress

        # Handle QuickTime popup dialog
        # "QuickTime does not support the current Display Setting.  Please change it and restart this application."
        self.AddPopupHandler( "Unsupported Display", "OK" )
        self.AddPopupHandler( "Nicht.*", "OK" )
    
    def PreRenderTasks( self ):
        sceneFilename = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "SceneFile", self.deadlinePlugin.GetDataFilename() )
        sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename )

        enablePathMapping = self.deadlinePlugin.GetBooleanConfigEntryWithDefault( "EnablePathMapping", True )
        self.deadlinePlugin.LogInfo( "Enable Path Mapping: %s" % enablePathMapping )
        
        if enablePathMapping:
            tempSceneDirectory = self.deadlinePlugin.CreateTempDirectory( "thread" + str(self.deadlinePlugin.GetThreadNumber()) )

            if SystemUtils.IsRunningOnWindows():
                sceneFilename = sceneFilename.replace( "/", "\\" )
            else:
                sceneFilename = sceneFilename.replace( "\\", "/" )
            
            tempSceneFileName = Path.GetFileName( sceneFilename )
            self.TempSceneFilename = Path.Combine( tempSceneDirectory, tempSceneFileName )
            
            if SystemUtils.IsRunningOnWindows():
                self.TempSceneFilename = self.TempSceneFilename.replace( "/", "\\" )
                if sceneFilename.startswith( "\\" ) and not sceneFilename.startswith( "\\\\" ):
                    sceneFilename = "\\" + sceneFilename
                if sceneFilename.startswith( "/" ) and not sceneFilename.startswith( "//" ):
                    sceneFilename = "/" + sceneFilename
            else:
                self.TempSceneFilename = self.TempSceneFilename.replace( "\\", "/" )
            
            # First, replace all TCL escapes ('\]') with '_TCL_ESCAPE_', then replace the '\' path separators with '/', and then swap back in the orignal TCL escapes.
            # This is so that we don't mess up any embedded TCL statements in the output path.
            self.pathMappingWithFilePermissionFix( sceneFilename, self.TempSceneFilename, ("\\[","\\", "_TCL_ESCAPE_"), ("_TCL_ESCAPE_", "/", "\\[") )
        else:
            if SystemUtils.IsRunningOnWindows():
                self.TempSceneFilename = sceneFilename.replace( "/", "\\" )
            else:
                self.TempSceneFilename = sceneFilename.replace( "\\", "/" )

    def PostRenderTasks( self ):
        if self.deadlinePlugin.GetBooleanConfigEntryWithDefault( "EnablePathMapping", True ):
            File.Delete( self.TempSceneFilename )

    ## Called by Deadline to get the render executable.
    def RenderExecutable( self ):
        exeKey = "RenderExecutable" + str( self.Version ).replace( ".", "_" )
        return self.deadlinePlugin.GetRenderExecutable( exeKey, "Nuke %s" % self.Version )


    ## Called by Deadline to get the render arguments.
    def RenderArgument( self ):
        # Enable verbosity (the '2' option is only available in Nuke 7 and later)
        renderarguments = "-V"
        if self.Version >= 7.0:
            renderarguments += " 2"
        
        if self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "NukeX", False ):
            self.deadlinePlugin.LogInfo( "Rendering with NukeX" )
            renderarguments += " --nukex"
        
        if self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "ContinueOnError", False ):
            self.deadlinePlugin.LogInfo( "An attempt will be made to render subsequent frames in the range if an error occurs" )
            renderarguments += " --cont"
            
        if self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "EnforceRenderOrder", False ):
            self.deadlinePlugin.LogInfo( "Forcing Nuke to obey the render order of Write nodes" )
            renderarguments += " --sro"
        
        
        renderMode = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "RenderMode", "Use Scene Settings" )
        
        if renderMode == "Render using Proxies":
            self.deadlinePlugin.LogInfo( "Rendering using Proxy File Paths" )
            renderarguments += " -p"
        elif renderMode ==  "Render Full Resolution":
            self.deadlinePlugin.LogInfo( "Rendering using Full Resolution" )
            renderarguments += " -f"
        
        gpuOverrides = self.GetGpuOverrides()
        if len(gpuOverrides) > 1:
            gpuOverrides = [ gpuOverrides[ self.deadlinePlugin.GetThreadNumber() ] ]
        
        # GPU option only supported in Nuke 7 and later.
        if self.Version >= 7.0 and self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "UseGpu", False ):
            self.deadlinePlugin.LogInfo( "Enabling GPU rendering" )
            renderarguments += " --gpu"
            if self.Version >= 8.0:
                renderarguments += " %s" % ( ",".join( gpuOverrides ) )
        
        self.deadlinePlugin.SetProcessEnvironmentVariable( "EDDY_DEVICE_LIST", ",".join(gpuOverrides) )
        
        thisSlave = self.deadlinePlugin.GetSlaveName().lower()

        interactiveSlaves = self.deadlinePlugin.GetConfigEntryWithDefault( "InteractiveSlaves", "" ).split( ',' )
        for slave in interactiveSlaves:
            if slave.lower().strip() == thisSlave:
                self.deadlinePlugin.LogInfo( "This Worker is in the interactive license list - an interactive license will be used instead of a render license" )
                renderarguments += " -i"
        
        if self.BatchMode:
            renderarguments += " -t" # start in Terminal mode
        else:
            renderarguments += " -x" # execute the Nuke script (as opposed to editing it)
        
        if self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "WriteNodesAsSeparateJobs", False ):
            if not self.BatchMode:
                frame = str(self.deadlinePlugin.GetStartFrame())
                writeNodeName = self.deadlinePlugin.GetPluginInfoEntry( "WriteNode" + frame )
                self.deadlinePlugin.LogInfo( "Rendering write node " + writeNodeName )
                renderarguments += " -X \"" + writeNodeName + "\""
        else:
            writeNodeName = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "WriteNode", "" )
            if not self.BatchMode and writeNodeName != "":
                self.deadlinePlugin.LogInfo( "Rendering write node(s) " + writeNodeName )
                renderarguments += " -X \"" + writeNodeName + "\""
        
        threads = self.deadlinePlugin.GetIntegerPluginInfoEntryWithDefault( "Threads", 0 )
        if threads > 0:
            self.deadlinePlugin.LogInfo( "Using " + str(threads) + " threads for rendering" )
            renderarguments += " -m " + str(threads)
        
        ramUse = self.deadlinePlugin.GetIntegerPluginInfoEntryWithDefault( "RamUse", 0 )
        if ramUse > 0:
            self.deadlinePlugin.LogInfo( "Limiting RAM usage to " + str(ramUse) + " MB" )
            renderarguments += " -c " + str(ramUse) + "M"
        
        stackSize = self.deadlinePlugin.GetIntegerPluginInfoEntryWithDefault( "StackSize", 0 )
        if stackSize > 0:
            self.deadlinePlugin.LogInfo( "Setting minimum stack size to " + str(ramUse) + " MB" )
            renderarguments += " -s " + str(stackSize * 1024 * 1024)
            
        view = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "Views", "" ).strip()
        if view != "":
            self.deadlinePlugin.LogInfo( "Setting view(s) to render to " + view )
            renderarguments += " --view " + view
        
        # If using Nuke 6 or later, use the -F argument to specify the frame range
        if not self.BatchMode:
            if self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "WriteNodesAsSeparateJobs", False ):
                frame = str(self.deadlinePlugin.GetStartFrame())
                writeNodeStartFrame = self.deadlinePlugin.GetPluginInfoEntry( "WriteNode" + frame + "StartFrame" )
                writeNodeEndFrame = self.deadlinePlugin.GetPluginInfoEntry( "WriteNode" + frame + "EndFrame" )
                renderarguments += " -F " + writeNodeStartFrame + "-" + writeNodeEndFrame
            else:
                renderarguments += " -F " + str(self.deadlinePlugin.GetStartFrame()) + "-" + str(self.deadlinePlugin.GetEndFrame())

        # Performance Profiler option only supported in Nuke 9 and later.
        if self.Version >= 9.0 and self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "PerformanceProfiler", False ):
            self.deadlinePlugin.LogInfo( "Performance Profiler Enabled" )

            # Write Performance Profile xml file to local Worker jobs data directory and copy over at end of job to reduce network storage load.
            tempPPDir = Path.Combine( self.deadlinePlugin.GetJobsDataDirectory(), "PerformanceProfiler" )
            try:
                if not Directory.Exists( tempPPDir ):
                    Directory.CreateDirectory( tempPPDir )
            except:
                self.deadlinePlugin.FailRender( "Failed to create directory: %s" % tempPPDir )

            nukeScriptName = Path.GetFileNameWithoutExtension( self.TempSceneFilename )

            startFrame = str( self.deadlinePlugin.GetStartFrame() )
            endFrame = str( self.deadlinePlugin.GetEndFrame() )

            # 'Standard' Job
            xmlFilename = nukeScriptName + "_" + startFrame + "-" + endFrame + "_thread" + str( self.deadlinePlugin.GetThreadNumber() ) + "_" + thisSlave + ".xml"

            # startFrame and endFrame will be -1 for a batch job, and there'll only be one performance profile per Worker. Thus we take them out and specify batch
            if self.BatchMode:
                xmlFilename = nukeScriptName + "_batch_thread" + str( self.deadlinePlugin.GetThreadNumber() ) + "_" + thisSlave + ".xml"

            # Write Nodes As Separate Tasks Path (entry in plugin is named wrong), means we need to include each Write Node name & frames to be unique
            elif self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "WriteNodesAsSeparateJobs", False ):
                writeNode = self.deadlinePlugin.GetPluginInfoEntry( "WriteNode" + startFrame )
                writeNodeStartFrame = self.deadlinePlugin.GetIntegerPluginInfoEntry( "WriteNode" + startFrame + "StartFrame" )
                writeNodeEndFrame = self.deadlinePlugin.GetIntegerPluginInfoEntry( "WriteNode" + startFrame + "EndFrame" )
                self.deadlinePlugin.LogInfo( "WriteNode: '" + writeNode + "'" )
                xmlFilename = nukeScriptName + "_" + writeNode + "_" + str( writeNodeStartFrame ) + "-" + str( writeNodeEndFrame ) + "_thread" + str( self.deadlinePlugin.GetThreadNumber() ) + "_" + thisSlave + ".xml"

            xmlFile = Path.Combine( tempPPDir, xmlFilename )
            self.deadlinePlugin.LogInfo( "Saving Performance Profiler file to: %s" % xmlFile )

            if File.Exists( xmlFile ):
                try:
                    File.Delete( xmlFile )
                except:
                    self.deadlinePlugin.LogWarning( "Failed to delete pre-existing Performance Profiler xml file: %s" % xmlFile )

            renderarguments += " --Pf \"%s\"" % xmlFile
        
        renderarguments += " \"" + self.TempSceneFilename + "\""
        
        return renderarguments
    
    def GetGpuOverrides( self ):
        useGpu = self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "UseGpu", False )
        if not useGpu:
            return []
        
        useSpecificGpu = self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "UseSpecificGpu", False )
        gpusSelectDevices = ""
        if useSpecificGpu:
            gpusSelectDevices = self.deadlinePlugin.GetPluginInfoEntryWithDefault( "GpuOverride", "0"  )
        
        # If the number of gpus per task is set, then need to calculate the gpus to use.
        gpusPerTask = 0
        resultGPUs = []

        if self.deadlinePlugin.OverrideGpuAffinity():
            overrideGPUs = [ str( gpu ) for gpu in self.deadlinePlugin.GpuAffinity() ]

            if gpusPerTask == 0 and gpusSelectDevices != "":
                gpus = gpusSelectDevices.split( "," )
                notFoundGPUs = []
                for gpu in gpus:
                    if gpu in overrideGPUs:
                        resultGPUs.append( gpu )
                    else:
                        notFoundGPUs.append( gpu )
                
                if len( notFoundGPUs ) > 0:
                    self.deadlinePlugin.LogWarning( "The Worker is overriding its GPU affinity and the following GPUs do not match the Workers affinity so they will not be used: " + ",".join( notFoundGPUs ) )
                if len( resultGPUs ) == 0:
                    self.deadlinePlugin.FailRender( "The Worker does not have affinity for any of the GPUs specified in the job." )
            elif gpusPerTask > 0:
                if gpusPerTask > len( overrideGPUs ):
                    self.deadlinePlugin.LogWarning( "The Worker is overriding its GPU affinity and the Worker only has affinity for " + str( len( overrideGPUs ) ) + " Workers of the " + str( gpusPerTask ) + " requested." )
                    resultGPUs = overrideGPUs
                else:
                    resultGPUs = list( overrideGPUs )[:gpusPerTask]
            else:
                resultGPUs = overrideGPUs
        elif gpusPerTask == 0 and gpusSelectDevices != "":
            resultGPUs = gpusSelectDevices.split( "," )

        elif gpusPerTask > 0:
            gpuList = []
            for i in range( ( self.deadlinePlugin.GetThreadNumber() * gpusPerTask ), ( self.deadlinePlugin.GetThreadNumber() * gpusPerTask ) + gpusPerTask ):
                gpuList.append( str( i ) )
            resultGPUs = gpuList
        else:
            self.deadlinePlugin.LogWarning( "GPU affinity is enabled for Nuke but the Workers GPU affinity has not been set and no overrides have been set. Defaulting to GPU 0." )
            resultGPUs = ["0"]
        
        resultGPUs = list( resultGPUs )
        
        return resultGPUs
    
    def HandleError( self ):
        if( not self.deadlinePlugin.GetBooleanPluginInfoEntryWithDefault( "ContinueOnError", False ) ):
            self.deadlinePlugin.FailRender( self.GetRegexMatch( 0 ) )
        else:
            self.deadlinePlugin.LogWarning( "Skipping error detection as 'Continue On Error' is enabled." )

    def HandleProgress( self ):
        currFrame = int( self.GetRegexMatch( 1 ) )
        totalFrames = int( self.GetRegexMatch( 2 ) )
        if totalFrames != 0:
            self.deadlinePlugin.SetProgress( ( float(currFrame) / float(totalFrames) ) * 100.0 )
        self.deadlinePlugin.SetStatusMessage( self.GetRegexMatch( 0 ) )
    
    def HandleReadyForInput( self ):
        self.ReadyForInput = True
    
    def IsReadyForInput( self ):
        return self.ReadyForInput
    
    def ResetReadyForInput( self ):
        self.ReadyForInput = False
    
    def ReadyForInputCommand( self ):
        return "print( \"READY FOR INPUT\\n\" )"
