#!/usr/bin/env python
"""
Utility script for adding Deadline submission metadata to Nuke write nodes.

This script provides functions to add or remove Deadline-related metadata
from write nodes in Nuke. Metadata keys will be prefixed with:
- 'input/deadline/jobInfo/' for job settings
- 'input/deadline/pluginInfo/' for plugin settings

The parameter names should match the Deadline parameter names exactly:
- ChunkSize
- Priority
- Threads
- UseGpu

Usage:
    1. Load this script in the Nuke Script Editor
    2. Select the write nodes you want to modify
    3. Call one of the provided functions
    
Example:
    # Add ChunkSize=30 to the selected write node
    add_job_metadata("ChunkSize", 30)
"""
import nuke


def add_job_metadata(key, value):
    """
    Add a JobInfo metadata key to selected write nodes.
    
    Args:
        key: The JobInfo parameter name (e.g., "ChunkSize", "Priority", etc.)
        value: The value to set
    """
    for node in nuke.selectedNodes():
        if node.Class() not in ["Write", "DeepWrite", "WriteGeo"]:
            print(f"Warning: {node.name()} is not a Write node")
            continue
            
        metadata_key = f"input/deadline/jobInfo/{key}"
        node.addMetadata(metadata_key, str(value))
        print(f"Added metadata to {node.name()}: {metadata_key}={value}")


def add_plugin_metadata(key, value):
    """
    Add a PluginInfo metadata key to selected write nodes.
    
    Args:
        key: The PluginInfo parameter name (e.g., "Threads", "RamUse", etc.)
        value: The value to set
    """
    for node in nuke.selectedNodes():
        if node.Class() not in ["Write", "DeepWrite", "WriteGeo"]:
            print(f"Warning: {node.name()} is not a Write node")
            continue
            
        metadata_key = f"input/deadline/pluginInfo/{key}"
        node.addMetadata(metadata_key, str(value))
        print(f"Added metadata to {node.name()}: {metadata_key}={value}")


def list_metadata():
    """
    List all Deadline-related metadata for selected write nodes.
    """
    for node in nuke.selectedNodes():
        if node.Class() not in ["Write", "DeepWrite", "WriteGeo"]:
            print(f"Warning: {node.name()} is not a Write node")
            continue
            
        # Get current metadata
        try:
            metadata = node.metadata()
            if not metadata:
                print(f"No metadata found for {node.name()}")
                continue
        except:
            print(f"Error reading metadata for {node.name()}")
            continue
        
        # Find Deadline metadata
        job_prefix = "input/deadline/jobInfo/"
        plugin_prefix = "input/deadline/pluginInfo/"
        
        job_info = {}
        plugin_info = {}
        
        for key in metadata:
            if key.startswith(job_prefix):
                param_name = key[len(job_prefix):]
                job_info[param_name] = metadata[key]
            elif key.startswith(plugin_prefix):
                param_name = key[len(plugin_prefix):]
                plugin_info[param_name] = metadata[key]
        
        # Print results
        print(f"\nDeadline metadata for {node.name()}:")
        
        if job_info:
            print("\nJobInfo parameters:")
            for key, value in job_info.items():
                print(f"  {key} = {value}")
        else:
            print("\nNo JobInfo parameters")
            
        if plugin_info:
            print("\nPluginInfo parameters:")
            for key, value in plugin_info.items():
                print(f"  {key} = {value}")
        else:
            print("\nNo PluginInfo parameters")


def remove_metadata():
    """
    Remove all Deadline metadata from selected write nodes.
    """
    for node in nuke.selectedNodes():
        if node.Class() not in ["Write", "DeepWrite", "WriteGeo"]:
            print(f"Warning: {node.name()} is not a Write node")
            continue
            
        # Get current metadata
        try:
            metadata = node.metadata()
            if not metadata:
                print(f"No metadata found for {node.name()}")
                continue
        except:
            print(f"Error reading metadata for {node.name()}")
            continue
        
        # Find keys to remove
        keys_to_remove = []
        job_prefix = "input/deadline/jobInfo/"
        plugin_prefix = "input/deadline/pluginInfo/"
        
        for key in metadata:
            if key.startswith(job_prefix) or key.startswith(plugin_prefix):
                keys_to_remove.append(key)
        
        # Remove the keys
        for key in keys_to_remove:
            node.removeMetadata(key)
            print(f"Removed metadata from {node.name()}: {key}")


# Example usage - uncomment one of these examples to run
if __name__ == "__main__":
    # Example: Add ChunkSize=30 to selected write nodes
    add_job_metadata("ChunkSize", 30)
    
    # List metadata on selected write nodes
    list_metadata()
    
    # Example: Remove all metadata from selected write nodes
    # remove_metadata() 