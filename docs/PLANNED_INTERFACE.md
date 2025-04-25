# Nuke Submitter for Thinkbox Deadline - Interface Design Plan

## Overview
This document outlines the design approach for both the Command Line Interface (CLI) and Nuke User Interface for the Deadline submission tool. The goal is to create intuitive, efficient interfaces that cater to both power users (CLI) and artists (Nuke UI).

## Command Line Interface (CLI) Design

### Core Commands
```bash
# Config
nk2dl config --list

# Basic submission
nk2dl submit <script_path> [options]
```
Config options:
--list
   Lists the active key value pairs for the current configuration. Key value pairs are created from various sources
   Configuration is loaded in the following order (later sources override earlier ones):
   1. Default configuration
   2. Project configuration file (from NK2DL_CONFIG or .nk2dl.yaml in project root)
   3. User configuration file (~/.nk2dl/config.yaml)
   4. Environment variables (NK2DL_*)

Submit options:
This may not be a full list of options. The options here should correspond to what is available in nk2dl.nuke.submission. If they are missing from this list we should include them and create them in the style of the following options.

--BatchName
   Optional, string
   Default value: "<nukescript_filename>"
   Usage:
   --BatchName=MyBatch
   --BatchName MyBatch
   --BatchName="My Batch"
   --BatchName "My Batch"

--JobName
   Optional, string
   Default value: "<nukescript_filename>/<write_nodename>"
   Usage:
   --JobName=MyJob
   --JobName MyJob
   --JobName="My Job"
   --JobName "My Job"

--Commment
   Optional, string
   Default value: Nothing
   Usage:
   --Commment="My Comment"
   --Commment "My Comment"

--Department
   Optional, string
   Default value: Nothing
   Usage:
   --Department=Compositing
   --Department Compositing

--Pool
   Optional, string
   Default value: Nothing
   Usage:
   --Pool=nuke
   --Pool nuke

--Group
   Optional, string
   Default value: Nothing
   Usage:
   --Group=workstations
   --Group workstations

--Priority
   Optional, int
   Default value: 50
   Usage:
   --Priority=80
   --Priority 80

--TaskTimeout
   Optional, int, in minutes
   Default value: 0
   Usage:
   --Priority=5
   --Priority 5

--AutoTaskTimeout
   Optional, bool
   Default value: False
   Usage:
   --AutoTaskTimeout
   
--ConcurrentTasks
   Optional, int
   Default value: 1
   Usage:
   --ConcurrentTasks=3
   --ConcurrentTasks 3

--LimitWorkerTasks
   Optional, bool
   Default value: False
   Usage:
   --LimitWorkerTasks
   
--MachineLimit
   Optional, int
   Default value: 0
   Usage:
   --MachineLimit=3
   --MachineLimit 3

--MachineList (optional)
   Optional, string
   Default value: Nothing
   Usage:
   --MachineList=allow:render1,render2
   --MachineList deny:workstation8,workstation3,render4

--Limits
   Optional, string
   Default value: Nothing
   Usage:
   --Limits=license_limit
   --Limits license_limit

--Dependencies
   Optional, string
   Default value: Nothing
   Usage:
   --Dependencies=jobId1,jobId2
   --Dependencies jobId1,jobId2

--SubmitJobsAsSuspended
   Optional, bool
   Default value: False
   Usage:
   --SubmitJobsAsSuspended

--SubmitNukeScript
   Optional, bool
   Submits the nukescript to the render nodes as an auxilary file and the node uses the auxilary file with nuke on the render node
   Default value: False
   Usage:
   --SubmitNukeScript

--WriteNodes --Writes --Nodes -w -n 
   Optional, string
   Default value: all write nodes
   Usage:
   --Writes=Write1,Write2
   -w Write1,Write2

--Frames -f
   Optional, string
   Uses the same syntax as nuke for frameranges.
   Special cases:
      f,first=root.first_frame
      l,last=root.last_frame
      m,middle=(root.first_frame+root.last_frame)/2
      h,hero=hero frames, defaults to f,m,l if no hero frames set
      i,input=write node input range
   Default value: f-l
   Usage:
   --Frames=1001-1100x10
   -f 100,200,900
   -f f-l
   -f=f,m,l

--FramesPerTask, --TaskSize, --ChunkSize, --Chunk
   Optional, int
   Default value: 1
   Usage:
   --FramesPerTask=4
   --ChunkSize 4

-nx --NukeX --UseNukeX
   Optional, bool
   Default value: False
   Usage:
   --NukeX

--BatchMode
   Optional, bool
   Default value: False
   Usage:
   --BatchMode
   
--RenderThreads
   Optional, int
   Default value: 0 (use system default)
   Usage:
   --RenderThreads=4
   --RenderThreads 4

--Gpu --UseGPU
   Optional, bool
   Default value: False
   Usage:
   --UseGPU

--RAM
   Optional, int (in GB)
   Default value: 0 (use system default)
   Usage:
   --RAM=16
   --RAM 16

--RenderOrderDependencies
   Optional, bool
   Default value: False
   Usage:
   --RenderOrderDependencies

--ContinueOnError
   Optional, bool
   Default value: False
   Usage:
   --ContinueOnError

--ReloadBetweenTasks, --ReloadBetweenChunks
   Optional, bool
   Default value: False
   Usage:
   --ReloadBetweenTasks
   --ReloadBetweenChunks

--PerformanceProfiler
   Optional, bool
   Default value: False
   Usage:
   --PerformanceProfiler

--XMLDirectory, --XMLDir
   Optional, string
   Default value: None
   Usage:
   --XMLDirectory=/path/to/xml
   --XMLDir "/path/to/xml"

--Proxy
   Optional, bool
   Default value: False
   Usage:
   --Proxy

--Views
   Optional, string
   Default value: None (all views)
   Usage:
   --Views=main,left,right
   --Views main,left,right

--WritesAsSeparateJobs
   Optional, bool
   Default value: False
   Usage:
   --WritesAsSeparateJobs

--WritesAsSeparateTasks
   Optional, bool
   Default value: False
   Usage:
   --WritesAsSeparateTasks

--NodeFrameRange
   Optional, bool
   Default value: False (use script frame range)
   Usage:
   --NodeFrameRange

--MetadataOverrides
   Optional, bool
   Default value: None
   Usage:
   --MetadataOverrides

--OnJobComplete
   Optional, string
   Default value: Nothing
   Values: Nothing, Archive, Delete
   Usage:
   --OnJobComplete=Archive
   --OnJobComplete Delete

--Var, --Variable, --GSV
   Optional, string
   Default value: Nothing
   Graph scope viables (Avaialble in nuke 15.2 and later)
   Can be used multiple times to create batches from variables
   Brackets can be used to create batches from variables
   The colon in "var:" denotes variable name, values after "var:" are comma delimeted variable values until next colon is encounted, which then denotes the next variable name.
   If no variable value is specified, all items for that variable are rendered
   Usage:
   --Var sequence:ABC,shot:
      submit all shots under sequence ABC
   --Var (sequence:XYZ,shot:143,123,890)(sequnce:RST,shot:334,999)
      submit XYZ142 XYZ123 XYZ890 RST334 RST999
   --Var=sequence:XYZ,shot:143,123,890 --Var=sequnce:RST,shot:334,999
      submit XYZ142 XYZ123 XYZ890 RST334 RST999

-V, -VV, -Verbose, -Verbosity, -Logging
   Optional, string
   Default value: INFO
   Values: INFO, DEBUG, NOTSET
      -V, -Verbose are shorthand for -Logging DEBUG
      -VV is shorthand for -Logging NOTSET
      -Logging and -Verbosity can be used interchangeably
   Usage:
      -Logging DEBUG
      -Verbosity=DEBUG

The options are case insensitive on the left side of the argument, and case sensitive on the second side. For example the following arguments are the same:
   --WriteNodes=Write4,Write6
   --writenodes=Write4,Write6

Defaults can be overridden with aan environment variable pointed to a .yaml config
   $DL2NK_CONFIG=/path/to/config.yaml

### Example Usage
```bash
# Basic submission
nk2dl submit comp_v001.nk --priority 75 --chunk 10
```

## Nuke Python API

## Nuke User Interface Design

## Shared Features

1. **Configuration System**
   - Shared configuration format (YAML) for defaults
   - Environment variable support (DL2NK_CONFIG)
   - User-specific configuration override

2. **Logging System**
   - Consistent logging format across CLI and API
   - Configurable verbosity levels
   - Output to console and/or file

4. **Job Validation**
   - Pre-submission validation of options
   - Nuke script validation
   - Write node validation 

5. **Frame Range Parsing**
   - Common frame range syntax parser
   - Special token support (f, l, m, hero)
   - Frame sequence optimization

6. **Submission Engine**
   - Core job submission logic
   - Dependency management
   - Job lifecycle hooks

7. **Error Handling**
   - Standardized error codes
   - Detailed error messages
   - Recovery mechanisms

8. **Job Monitoring**
   - Status polling capabilities
   - Progress reporting
   - Completion notification

9. **Template System**
   - Job templates
   - Batch submission templates
   - Custom parameter templates

10. **Extensibility**
    - Plugin architecture for custom functionality
    - Pre/post submission hooks
    - Custom validators
