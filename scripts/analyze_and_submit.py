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
import time
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
    version=None,
    metadata_overrides=False
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
        metadata_overrides: Whether to use metadata from write nodes to override job settings
    
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
    
    # Create progress dialog
    task = nuke.ProgressTask("Deadline Submission")
    task.setMessage("Analyzing script...")
    task.setProgress(0)
    
    # Force UI update
    time.sleep(0.1)
    
    # Analyze script for write nodes and dependencies
    analyzer = ScriptAnalyzer()
    
    # Get selected write nodes
    write_nodes = analyzer.get_write_nodes(selected_only=True)
    
    if not write_nodes:
        task.setProgress(100)
        nuke.message("No write nodes selected")
        return None
    
    # Update progress
    task.setMessage("Analyzing dependencies...")
    task.setProgress(10)
    
    # Force UI update
    time.sleep(0.1)
    
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
        task.setProgress(100)
        return None
    
    # Create and configure submitter
    submitter = DeadlineSubmitter()
    
    # Update progress for submission start
    task.setMessage("Preparing job submission...")
    task.setProgress(20)
    
    # Force UI update
    time.sleep(0.1)
    
    # Track submission progress
    global current_step, total_steps
    total_steps = len(write_nodes)
    current_step = 0
    
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
        version=version,
        metadata_overrides=metadata_overrides,
        progress_callback=lambda node_name, job_id: _update_progress(task, node_name, job_id)
    )
    
    # Complete progress
    task.setProgress(100)
    
    # Print job IDs
    print("\nSubmitted Jobs:")
    for node_name, job_id in job_ids.items():
        print(f"{node_name}: {job_id}")
    
    return job_ids


def _update_progress(task, node_name, job_id):
    """Update progress bar with current submission status."""
    global current_step, total_steps
    current_step += 1
    progress_percent = int(20 + (current_step / total_steps) * 80)  # Scale to 20-100% range
    task.setMessage(f"Submitting {node_name}...")
    task.setProgress(progress_percent)
    print(f"Submitted job {job_id} for {node_name} ({current_step}/{total_steps})")
    
    # Force UI update
    time.sleep(0.1)


# Example usage
if __name__ == "__main__":
    # Submit selected write nodes with custom settings
    job_ids = submit_selected_write_nodes(
        priority=50,
        pool="nuke",
        chunk_size=5,
        threads=8,
        ram_usage=16384,  # 16GB
        use_gpu=True,
        metadata_overrides=True
    )
    
    if job_ids:
        nuke.message(f"Successfully submitted {len(job_ids)} jobs to Deadline") 