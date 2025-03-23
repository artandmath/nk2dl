"""
NukePluginInfo class for handling Nuke-specific Deadline settings.
"""
import os
from typing import Dict, Optional, Union, Tuple


class NukePluginInfo:
    """
    Class to handle Nuke-specific plugin settings for Deadline.
    This generates the plugin info file that Deadline uses for Nuke-specific settings.
    """
    def __init__(self) -> None:
        # Required settings
        self.scene_file: str = ""
        self.version: Tuple[int, int] = (0, 0)  # Major.Minor version
        
        # Optional settings with defaults
        self.threads: int = 0  # 0 means auto-detect
        self.ram_usage: int = 0  # MB, 0 means no limit
        self.batch_mode: bool = True
        self.use_gpu: bool = False
        self.use_specific_gpu: bool = False
        self.gpu_override: int = 0
        self.render_mode: str = "Use Scene Settings"  # or "Use Proxy Mode" or "Use Full Resolution"
        self.enforce_render_order: bool = False
        self.performance_profiler: bool = False
        self.performance_profiler_dir: str = ""
        self.stack_size: int = 0  # MB, 0 means default
        self.continue_on_error: bool = False
        self.use_nukex: bool = False
        
    def to_file(self, filepath: str) -> None:
        """
        Write plugin settings to a .job file that Deadline can understand.
        
        Args:
            filepath: Path where the plugin file should be written
        """
        if not self.scene_file:
            raise ValueError("Scene file path must be set")
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w") as f:
            # Write required settings
            f.write(f"SceneFile={self.scene_file}\n")
            f.write(f"Version={self.version[0]}.{self.version[1]}\n")
            
            # Write optional settings
            f.write(f"Threads={self.threads}\n")
            f.write(f"RamUse={self.ram_usage}\n")
            f.write(f"BatchMode={str(self.batch_mode)}\n")
            f.write(f"BatchModeIsMovie=False\n")  # We don't support movie output yet
            
            f.write(f"NukeX={str(self.use_nukex)}\n")
            f.write(f"UseGpu={str(self.use_gpu)}\n")
            f.write(f"UseSpecificGpu={str(self.use_specific_gpu)}\n")
            f.write(f"GpuOverride={self.gpu_override}\n")
            
            f.write(f"RenderMode={self.render_mode}\n")
            f.write(f"EnforceRenderOrder={str(self.enforce_render_order)}\n")
            f.write(f"ContinueOnError={str(self.continue_on_error)}\n")
            
            f.write(f"PerformanceProfiler={str(self.performance_profiler)}\n")
            if self.performance_profiler_dir:
                f.write(f"PerformanceProfilerDir={self.performance_profiler_dir}\n")
                
            f.write(f"StackSize={self.stack_size}\n")
            
    def update(self, settings: Dict[str, Union[str, int, bool, Tuple[int, int]]]) -> None:
        """
        Update multiple plugin settings at once using a dictionary.
        
        Args:
            settings: Dictionary of setting names and values to update
        """
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown plugin setting: {key}")
                
    @staticmethod
    def parse_version(version_str: str) -> Tuple[int, int]:
        """
        Parse a version string into a tuple of (major, minor).
        
        Args:
            version_str: Version string in format "X.Y" or "X.Y.Z"
            
        Returns:
            Tuple of (major, minor) version numbers
        """
        parts = version_str.split(".")
        if len(parts) >= 2:
            return (int(parts[0]), int(parts[1]))
        else:
            raise ValueError(f"Invalid version string format: {version_str}") 