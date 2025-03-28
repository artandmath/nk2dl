#!/usr/bin/env python
"""
Example script demonstrating how to use ScriptAnalyzer with DeadlineSubmitter.

This script should be run from within Nuke:

1. Load this script in the Nuke Script Editor
2. Select the write nodes you want to submit
3. Run the script

It will:
1. Analyze the script for write nodes and dependencies
2. Submit each write node as a separate job with proper dependencies
"""
import nuke
from nk2dl.core.parser import ScriptAnalyzer
from nk2dl.core.submission import DeadlineSubmitter


def submit_selected_write_nodes(
    priority=50,
    pool="nuke",
    frames=None,
    chunk_size=10,
    threads=0,
    ram_usage=0,
    use_gpu=False,
    version=None
):
    """
    Submit selected write nodes as separate jobs with proper dependencies.
    
    Args:
        priority: Job priority (0-100)
        pool: Deadline pool name
        frames: Frame range (if None, use script range)
        chunk_size: Number of frames per task
        threads: Number of threads to use (0 = auto)
        ram_usage: RAM limit in MB (0 = no limit)
        use_gpu: Whether to use GPU for rendering
        version: Nuke version to use as tuple (major, minor)
    
    Returns:
        Dictionary mapping write node names to job IDs
    """
    # Get current script path
    script_path = nuke.root().name()
    if not script_path:
        nuke.message("Please save the script before submitting")
        return None
    
    # Get frame range if not specified
    if frames is None:
        first = int(nuke.root().firstFrame())
        last = int(nuke.root().lastFrame())
        frames = f"{first}-{last}"
    
    # Get Nuke version if not specified
    if version is None:
        version = (nuke.NUKE_VERSION_MAJOR, nuke.NUKE_VERSION_MINOR)
    
    # Analyze script for write nodes and dependencies
    analyzer = ScriptAnalyzer()
    
    # Get selected write nodes
    write_nodes = analyzer.get_write_nodes(selected_only=True)
    
    if not write_nodes:
        nuke.message("No write nodes selected")
        return None
    
    # Analyze dependencies between write nodes
    dependencies = analyzer.analyze_dependencies(write_nodes)
    
    # Print dependency info
    print("\nWrite Node Dependencies:")
    for node_name, deps in dependencies.items():
        if deps:
            print(f"{node_name} depends on: {', '.join(deps)}")
        else:
            print(f"{node_name} has no dependencies")
    
    # Show confirmation dialog
    nodes_text = "\n".join([node.fullName() for node in write_nodes])
    confirm = nuke.ask(f"Submit {len(write_nodes)} write nodes?\n\n{nodes_text}")
    
    if not confirm:
        return None
    
    # Create and configure submitter
    submitter = DeadlineSubmitter()
    
    # Submit write nodes as separate jobs with dependencies
    job_ids = submitter.submit_job(
        script_path,
        write_nodes=write_nodes,
        dependencies=dependencies,
        name=f"Nuke: {nuke.root().name()}",
        frames=frames,
        chunk_size=chunk_size,
        priority=priority,
        pool=pool,
        threads=threads,
        ram_usage=ram_usage,
        use_gpu=use_gpu,
        version=version
    )
    
    # Print job IDs
    print("\nSubmitted Jobs:")
    for node_name, job_id in job_ids.items():
        print(f"{node_name}: {job_id}")
    
    return job_ids


# Example usage
if __name__ == "__main__":
    # Submit selected write nodes with custom settings
    job_ids = submit_selected_write_nodes(
        priority=75,
        pool="nuke_farm",
        chunk_size=5,
        threads=8,
        ram_usage=16384,  # 16GB
        use_gpu=True
    )
    
    if job_ids:
        nuke.message(f"Successfully submitted {len(job_ids)} jobs to Deadline") 