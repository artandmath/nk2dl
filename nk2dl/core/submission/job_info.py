"""
JobInfo class for handling Deadline job metadata.
"""
import os
from typing import Dict, Optional, Union


class JobInfo:
    """
    Class to handle Deadline job information and metadata.
    This generates the job info file that Deadline uses for job settings.
    """
    def __init__(self) -> None:
        # Required settings
        self.plugin: str = "Nuke"
        self.name: str = "Untitled"
        self.frames: str = "1"
        self.chunk_size: int = 1
        
        # Optional settings with defaults
        self.comment: str = ""
        self.department: str = ""
        self.pool: str = "none"
        self.secondary_pool: str = ""
        self.group: str = "none"
        self.priority: int = 50
        self.task_timeout: int = 0
        self.auto_task_timeout: bool = False
        self.concurrent_tasks: int = 1
        self.limit_concurrent_tasks: bool = True
        self.machine_limit: int = 0
        self.machine_list: str = ""
        self.is_blacklist: bool = False
        self.limit_groups: str = ""
        self.dependencies: str = ""
        self.on_complete: str = "Nothing"
        self.submit_suspended: bool = False
        
    def to_file(self, filepath: str) -> None:
        """
        Write job settings to a .job file that Deadline can understand.
        
        Args:
            filepath: Path where the job file should be written
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w") as f:
            # Write required settings
            f.write(f"Plugin={self.plugin}\n")
            f.write(f"Name={self.name}\n")
            f.write(f"Frames={self.frames}\n")
            f.write(f"ChunkSize={self.chunk_size}\n")
            
            # Write optional settings
            if self.comment:
                f.write(f"Comment={self.comment}\n")
            if self.department:
                f.write(f"Department={self.department}\n")
            
            f.write(f"Pool={self.pool}\n")
            if self.secondary_pool:
                f.write(f"SecondaryPool={self.secondary_pool}\n")
            else:
                f.write("SecondaryPool=\n")
                
            f.write(f"Group={self.group}\n")
            f.write(f"Priority={self.priority}\n")
            f.write(f"TaskTimeoutMinutes={self.task_timeout}\n")
            f.write(f"EnableAutoTimeout={str(self.auto_task_timeout)}\n")
            f.write(f"ConcurrentTasks={self.concurrent_tasks}\n")
            f.write(f"LimitConcurrentTasksToNumberOfCpus={str(self.limit_concurrent_tasks)}\n")
            f.write(f"MachineLimit={self.machine_limit}\n")
            
            if self.machine_list:
                if self.is_blacklist:
                    f.write(f"Blacklist={self.machine_list}\n")
                else:
                    f.write(f"Whitelist={self.machine_list}\n")
                    
            if self.limit_groups:
                f.write(f"LimitGroups={self.limit_groups}\n")
            if self.dependencies:
                f.write(f"JobDependencies={self.dependencies}\n")
            
            f.write(f"OnJobComplete={self.on_complete}\n")
            
            if self.submit_suspended:
                f.write("InitialStatus=Suspended\n")
                
    def update(self, settings: Dict[str, Union[str, int, bool]]) -> None:
        """
        Update multiple job settings at once using a dictionary.
        
        Args:
            settings: Dictionary of setting names and values to update
        """
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown job setting: {key}") 