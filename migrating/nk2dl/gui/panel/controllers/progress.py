"""
Progress management controller for coordinating UI progress indication.

This module provides the PanelProgressManager class that manages progress bars,
info labels, and other UI elements during background operations.
"""

from typing import Optional, Dict, List
from collections import deque

from ....common.logging import setup_logging
from ..constants import Timing

try:
    import nuke
    NUKE_AVAILABLE = True
    
    # Detect Nuke version and import appropriate PySide
    nuke_version = nuke.NUKE_VERSION_MAJOR
    if nuke_version >= 16:
        from PySide6 import QtCore, QtWidgets
        PYSIDE_VERSION = "PySide6"
    else:
        from PySide2 import QtCore, QtWidgets
        PYSIDE_VERSION = "PySide2"
        
except ImportError:
    NUKE_AVAILABLE = False
    # Fallback imports for testing without Nuke
    try:
        from PySide6 import QtCore, QtWidgets
        PYSIDE_VERSION = "PySide6"
    except ImportError:
        try:
            from PySide2 import QtCore, QtWidgets
            PYSIDE_VERSION = "PySide2"
        except ImportError:
            raise ImportError("Neither PySide6 nor PySide2 is available")

logger = setup_logging('nk2dl.gui.panel.controllers.progress')


class ProgressTask:
    """Represents a single progress operation."""
    
    def __init__(self, operation_name: str, indeterminate: bool = False):
        self.operation_name = operation_name
        self.indeterminate = indeterminate
        self.status_message = f"{operation_name}..."
        self.progress_percent = 0
        self.is_active = True


class PanelProgressManager:
    """Manager for coordinating progress indication in the panel UI.
    
    This class manages progress bars, info labels, and other UI elements
    during background operations. It supports multiple concurrent operations
    with a task queue system.
    """
    
    def __init__(self, progress_bar: Optional[QtWidgets.QProgressBar] = None, 
                 info_label: Optional[QtWidgets.QLabel] = None):
        """Initialize the progress manager.
        
        Args:
            progress_bar: Progress bar widget to manage (optional)
            info_label: Info label widget to manage (optional)
        """
        self.progress_bar = progress_bar
        self.info_label = info_label
        
        # Task queue management
        self._task_queue = deque()
        self._original_info_text = ""
        
        logger.debug("PanelProgressManager initialized")
    
    def start_operation(self, operation_name: str = "Loading", indeterminate: bool = False) -> str:
        """Start a progress operation.
        
        Args:
            operation_name: Name of the operation for display
            indeterminate: Whether to show indeterminate progress (crawling zebra pattern)
            
        Returns:
            Task ID for tracking this operation
        """
        # Create new task
        task = ProgressTask(operation_name, indeterminate)
        task_id = f"{operation_name}_{id(task)}"
        
        # Add to queue
        self._task_queue.append((task_id, task))
        
        # Update UI
        self._update_ui()
        
        logger.debug(f"Started progress operation: {operation_name} (indeterminate: {indeterminate})")
        return task_id
    
    def update_progress(self, progress_percent: int, status_message: str = "", task_id: str = None):
        """Update the progress indication.
        
        Args:
            progress_percent: Progress percentage (0-100)
            status_message: Status message to display
            task_id: Task ID to update (if None, updates the first active task)
        """
        task = self._get_task(task_id)
        if not task:
            logger.warning("Updating progress when no operation is active")
            return
        
        task.progress_percent = max(0, min(100, progress_percent))
        if status_message:
            task.status_message = status_message
        
        self._update_ui()
        logger.debug(f"Progress updated: {progress_percent}% - {status_message}")
    
    def update_status_message(self, status_message: str, task_id: str = None):
        """Update only the status message without affecting progress bar.
        
        This is useful for indeterminate operations where you want to update
        the status message but keep the crawling zebra pattern.
        
        Args:
            status_message: Status message to display
            task_id: Task ID to update (if None, updates the first active task)
        """
        task = self._get_task(task_id)
        if not task:
            logger.warning("Updating status message when no operation is active")
            return
        
        task.status_message = status_message
        self._update_ui()
        logger.debug(f"Status message updated: {status_message}")
    
    def finish_operation(self, success: bool = True, final_message: str = "", 
                        auto_reset_delay: int = Timing.PROGRESS_SUCCESS_DELAY, task_id: str = None):
        """Finish the progress operation.
        
        Args:
            success: Whether operation completed successfully
            final_message: Final message to display
            auto_reset_delay: Delay in milliseconds before resetting UI (0 = no auto reset)
            task_id: Task ID to finish (if None, finishes the first active task)
        """
        task = self._get_task(task_id)
        if not task:
            logger.warning("Finishing operation when none is active")
            return
        
        # Mark task as inactive
        task.is_active = False
        
        # Set final message
        if final_message:
            task.status_message = final_message
        elif success:
            task.status_message = "Operation completed successfully"
        else:
            task.status_message = "Operation failed"
        
        # Update UI immediately
        self._update_ui()
        
        # Schedule task removal if requested
        if auto_reset_delay > 0:
            QtCore.QTimer.singleShot(auto_reset_delay, lambda: self._remove_task(task_id))
        else:
            self._remove_task(task_id)
        
        operation_status = "successfully" if success else "with errors"
        logger.info(f"Progress operation finished {operation_status}: {final_message}")
    
    def cancel_operation(self, message: str = "Operation cancelled", task_id: str = None):
        """Cancel the current operation.
        
        Args:
            message: Cancellation message to display
            task_id: Task ID to cancel (if None, cancels the first active task)
        """
        task = self._get_task(task_id)
        if not task:
            return
        
        # Mark task as inactive
        task.is_active = False
        task.status_message = message
        
        # Update UI immediately
        self._update_ui()
        
        # Schedule task removal
        QtCore.QTimer.singleShot(Timing.PROGRESS_CANCEL_DELAY, lambda: self._remove_task(task_id))
        
        logger.info(f"Progress operation cancelled: {message}")
    
    def _get_task(self, task_id: str = None) -> Optional[ProgressTask]:
        """Get a task by ID or the first active task.
        
        Args:
            task_id: Task ID to find (if None, returns first active task)
            
        Returns:
            ProgressTask instance or None if not found
        """
        if not self._task_queue:
            return None
        
        if task_id:
            # Find specific task
            for tid, task in self._task_queue:
                if tid == task_id and task.is_active:
                    return task
            return None
        else:
            # Return first active task
            for tid, task in self._task_queue:
                if task.is_active:
                    return task
            return None
    
    def _remove_task(self, task_id: str):
        """Remove a task from the queue.
        
        Args:
            task_id: Task ID to remove
        """
        # Remove the task
        self._task_queue = deque((tid, task) for tid, task in self._task_queue if tid != task_id)
        
        # Update UI
        self._update_ui()
    
    def _update_ui(self):
        """Update the UI based on current task queue state."""
        # Get the first active task
        active_task = self._get_task()
        
        if not active_task:
            # No active tasks - reset to original state
            self._reset_ui()
            return
        
        # Configure progress bar
        if self.progress_bar:
            if active_task.indeterminate:
                # Set range to (0, 0) for indeterminate "crawling zebra" pattern
                self.progress_bar.setRange(0, 0)
            else:
                # Set normal range for determinate progress
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(active_task.progress_percent)
        
        # Update status message
        if self.info_label:
            # Build composite message from all active tasks
            active_tasks = [task for tid, task in self._task_queue if task.is_active]
            if len(active_tasks) == 1:
                # Single task - show its message
                self.info_label.setText(active_task.status_message)
            else:
                # Multiple tasks - show combined message
                task_messages = [task.status_message for task in active_tasks]
                combined_message = ", ".join(task_messages)
                self.info_label.setText(combined_message)
    
    def _reset_ui(self):
        """Reset the UI to its original state."""
        # Reset progress bar to determinate mode and empty
        if self.progress_bar:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
        
        # Restore original info text
        if self.info_label:
            if self._original_info_text:
                self.info_label.setText(self._original_info_text)
            else:
                self.info_label.setText("Ready")
        
        logger.debug("Progress UI reset to original state")
    
    def is_busy(self) -> bool:
        """Check if any operation is currently in progress.
        
        Returns:
            True if any operation is active, False otherwise
        """
        return self._get_task() is not None
    
    def get_active_task_count(self) -> int:
        """Get the number of currently active tasks.
        
        Returns:
            Number of active tasks
        """
        return len([task for tid, task in self._task_queue if task.is_active])
    
    def set_widgets(self, progress_bar: Optional[QtWidgets.QProgressBar] = None,
                   info_label: Optional[QtWidgets.QLabel] = None):
        """Set or update the managed widgets.
        
        Args:
            progress_bar: Progress bar widget to manage
            info_label: Info label widget to manage
        """
        if progress_bar is not None:
            self.progress_bar = progress_bar
            logger.debug("Progress bar widget updated")
        
        if info_label is not None:
            self.info_label = info_label
            # Store current text as original if not busy
            if not self.is_busy():
                self._original_info_text = info_label.text()
            logger.debug("Info label widget updated") 