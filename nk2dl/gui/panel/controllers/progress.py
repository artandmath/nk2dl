"""
Progress management controller for coordinating UI progress indication.

This module provides the PanelProgressManager class that manages progress bars,
info labels, and other UI elements during background operations.
"""

from typing import Optional

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


class PanelProgressManager:
    """Manager for coordinating progress indication in the panel UI.
    
    This class manages progress bars, info labels, and other UI elements
    during background operations like node data extraction. It provides
    a clean interface for starting, updating, and finishing operations
    while maintaining proper UI state.
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
        
        # State management
        self._is_busy = False
        self._original_info_text = ""
        
        logger.debug("PanelProgressManager initialized")
    
    def start_operation(self, operation_name: str = "Loading"):
        """Start a progress operation.
        
        Args:
            operation_name: Name of the operation for display
        """
        if self._is_busy:
            logger.warning("Starting new operation while another is already in progress")
        
        self._is_busy = True
        
        # Store original info text for restoration
        if self.info_label:
            self._original_info_text = self.info_label.text()
        
        # Reset progress bar
        if self.progress_bar:
            self.progress_bar.setValue(0)
        
        # Set initial status message
        if self.info_label:
            self.info_label.setText(f"{operation_name}...")
        
        logger.debug(f"Started progress operation: {operation_name}")
    
    def update_progress(self, progress_percent: int, status_message: str = ""):
        """Update the progress indication.
        
        Args:
            progress_percent: Progress percentage (0-100)
            status_message: Status message to display
        """
        if not self._is_busy:
            logger.warning("Updating progress when no operation is active")
            return
        
        # Update progress bar
        if self.progress_bar:
            self.progress_bar.setValue(max(0, min(100, progress_percent)))
        
        # Update status message
        if self.info_label and status_message:
            self.info_label.setText(status_message)
        
        logger.debug(f"Progress updated: {progress_percent}% - {status_message}")
    
    def finish_operation(self, success: bool = True, final_message: str = "", 
                        auto_reset_delay: int = Timing.PROGRESS_SUCCESS_DELAY):
        """Finish the progress operation.
        
        Args:
            success: Whether operation completed successfully
            final_message: Final message to display
            auto_reset_delay: Delay in milliseconds before resetting UI (0 = no auto reset)
        """
        if not self._is_busy:
            logger.warning("Finishing operation when none is active")
            return
        
        # Update progress to completion
        if self.progress_bar:
            self.progress_bar.setValue(100 if success else 0)
        
        # Set final message
        if self.info_label:
            if final_message:
                self.info_label.setText(final_message)
            elif success:
                self.info_label.setText("Operation completed successfully")
            else:
                self.info_label.setText("Operation failed")
        
        # Schedule UI reset if requested
        if auto_reset_delay > 0:
            QtCore.QTimer.singleShot(auto_reset_delay, self._reset_ui)
        else:
            self._reset_ui()
        
        operation_status = "successfully" if success else "with errors"
        logger.info(f"Progress operation finished {operation_status}: {final_message}")
    
    def cancel_operation(self, message: str = "Operation cancelled"):
        """Cancel the current operation.
        
        Args:
            message: Cancellation message to display
        """
        if not self._is_busy:
            return
        
        # Update UI to show cancellation
        if self.progress_bar:
            self.progress_bar.setValue(0)
        
        if self.info_label:
            self.info_label.setText(message)
        
        # Reset after a short delay
        QtCore.QTimer.singleShot(Timing.PROGRESS_CANCEL_DELAY, self._reset_ui)
        
        logger.info(f"Progress operation cancelled: {message}")
    
    def _reset_ui(self):
        """Reset the UI to its original state."""
        self._is_busy = False
        
        # Reset progress bar to empty but keep it visible
        if self.progress_bar:
            self.progress_bar.setValue(0)
        
        # Restore original info text
        if self.info_label:
            if self._original_info_text:
                self.info_label.setText(self._original_info_text)
            else:
                self.info_label.setText("Ready")
        
        logger.debug("Progress UI reset to original state")
    
    def is_busy(self) -> bool:
        """Check if an operation is currently in progress.
        
        Returns:
            True if an operation is active, False otherwise
        """
        return self._is_busy
    
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
            if not self._is_busy:
                self._original_info_text = info_label.text()
            logger.debug("Info label widget updated") 