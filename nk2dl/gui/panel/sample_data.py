# -*- coding: utf-8 -*-
"""Sample data for nk2dl panel demonstration.

This module contains sample table data used to demonstrate the panel functionality
with various inheritance patterns and explicit value scenarios.
"""

SAMPLE_TABLE_DATA = [
    {
        # Row 1: Mix of explicit values and inheritance (None = inherited)
        "Order": "3999", "Node": "Write4", "Filename": "Some_path1_v002.%04d.exr", 
        "Priority": "75", "ChunkSize": None, "Frames": None,  # Priority moved before ChunkSize
        "NodesFrames": None, "TaskTimeout": None, "AutoTimeout": None, "RenderMode": "Full", 
        "NukeX": None, "BatchMode": None, "ReloadPlugin": None,
        # Machine settings - some explicit, some inherited
        "Pool": "lighting",  # Override default "comp"
        "SecondaryPool": None, "Group": None, "Threads": None, "MinRam": None, "MaxRam": None,
        "UseGPU": "Yes",  # Override default False
        "GPUId": None, "ConcurrentTasks": None, "WorkerTaskLimit": None,
        "MachineList": None, "Limits": None
    },
    {
        # Row 2: Mostly explicit values (will show in bold)
        "Order": "3100", "Node": "Write30", "Filename": "Some_path3_v002.%04d.exr", 
        "Priority": "40", "ChunkSize": "3", "Frames": "1500-2000", "NodesFrames": "No",  # Custom frame range
        "TaskTimeout": "10", "AutoTimeout": "No", "RenderMode": "Proxy", "NukeX": "No", 
        "BatchMode": "No", "ReloadPlugin": "No",
        # Machine settings with explicit values
        "Pool": "lighting", "SecondaryPool": "render", "Group": "high_priority",
        "Threads": "4", "MinRam": "16", "MaxRam": "64", "UseGPU": "No",
        "GPUId": "0", "ConcurrentTasks": "2", "WorkerTaskLimit": "No",
        "MachineList": None, "Limits": None
    },
    {
        # Row 3: Mostly inherited values (None = inherited)
        "Order": "3050", "Node": "Write27", "Filename": "Some_path5_v002.%04d.exr", 
        "Priority": None, "ChunkSize": None, "Frames": None,  # Frames inherits from job settings
        "NodesFrames": None, "TaskTimeout": None, "AutoTimeout": None, "RenderMode": None, 
        "NukeX": None, "BatchMode": None, "ReloadPlugin": None,
        # Machine settings - mostly inherited
        "Pool": None, "SecondaryPool": None, "Group": None, "Threads": "8",  # Override threads
        "MinRam": None, "MaxRam": None, "UseGPU": None, "GPUId": None,
        "ConcurrentTasks": None, "WorkerTaskLimit": None, "MachineList": None, "Limits": None
    },
    {
        # Row 4: Mixed inheritance and overrides
        "Order": "3000", "Node": "Write9", "Filename": "Some_path6_v002.%04d.exr", 
        "Priority": "60", "ChunkSize": "8", "Frames": "1350-1650",  # Custom frame range override
        "NodesFrames": "No", "TaskTimeout": "5", "AutoTimeout": "No", "RenderMode": "Both", 
        "NukeX": "No", "BatchMode": None, "ReloadPlugin": None,  # Mix of explicit and inherited
        # Machine settings
        "Pool": "fx", "SecondaryPool": "general", "Group": "weekend",
        "Threads": "16", "MinRam": "32", "MaxRam": "128", "UseGPU": None,  # Inherit UseGPU
        "GPUId": "2", "ConcurrentTasks": "1", "WorkerTaskLimit": None,
        "MachineList": "workstation03", "Limits": "arnold_license:1"
    },
    {
        # Row 5: Demonstrate inheritance for all mapped columns (None = inherited)
        "Order": "2999", "Node": "Write3", "Filename": "Some_path9_v002.%04d.exr", 
        "Priority": None, "ChunkSize": None, "Frames": None,  # All job settings inherited (including frames)
        "NodesFrames": None, "TaskTimeout": None, "AutoTimeout": None, "RenderMode": None, 
        "NukeX": None, "BatchMode": None, "ReloadPlugin": None,
        # All machine settings inherited
        "Pool": None, "SecondaryPool": None, "Group": None, "Threads": None,
        "MinRam": None, "MaxRam": None, "UseGPU": None, "GPUId": None,
        "ConcurrentTasks": None, "WorkerTaskLimit": None, "MachineList": None, "Limits": None
    },
    {
        # Row 6: Explicit values including matching values (should still be bold)
        "Order": "2900", "Node": "Write5", "Filename": "Some_path10_v002.%04d.exr", 
        "Priority": "50", "ChunkSize": "1", "Frames": "1001-2315",  # Explicit 1001-2315 (matches setting but should be bold)
        "NodesFrames": "No", "TaskTimeout": "0", "AutoTimeout": "No", "RenderMode": "Full", 
        "NukeX": "No", "BatchMode": "No", "ReloadPlugin": "No",
        # Machine settings with explicit values including empty strings
        "Pool": "comp", "SecondaryPool": "", "Group": "none", "Threads": "4",  # Empty string is explicit
        "MinRam": "0", "MaxRam": "0", "UseGPU": "No", "GPUId": "0",
        "ConcurrentTasks": "2", "WorkerTaskLimit": "No", "MachineList": "", "Limits": ""  # Empty strings are explicit
    }
] 