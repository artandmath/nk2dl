"""
Background worker for fetching Deadline resources (pools and groups).

This module provides the DeadlineResourceWorker class that fetches pool and group
information from Deadline in background threads without blocking the UI.
"""

from typing import List, Optional
import logging

from ....common.logging import setup_logging
from ....deadline.connection import get_connection

try:
    import nuke
    NUKE_AVAILABLE = True
    
    # Detect Nuke version and import appropriate PySide
    nuke_version = nuke.NUKE_VERSION_MAJOR
    if nuke_version >= 16:
        from PySide6 import QtCore
        PYSIDE_VERSION = "PySide6"
    else:
        from PySide2 import QtCore
        PYSIDE_VERSION = "PySide2"
        
except ImportError:
    NUKE_AVAILABLE = False
    # Fallback imports for testing without Nuke
    try:
        from PySide6 import QtCore
        PYSIDE_VERSION = "PySide6"
    except ImportError:
        try:
            from PySide2 import QtCore
            PYSIDE_VERSION = "PySide2"
        except ImportError:
            raise ImportError("Neither PySide6 nor PySide2 is available")

logger = setup_logging('nk2dl.gui.panel.controllers.deadline_resources')


class DeadlineResourceWorkerSignals(QtCore.QObject):
    """Signals for deadline resource worker communication."""
    pools_loaded = QtCore.Signal(list)      # pools list
    groups_loaded = QtCore.Signal(list)     # groups list
    error_occurred = QtCore.Signal(str)     # error message
    progress_update = QtCore.Signal(str)    # progress message
    finished = QtCore.Signal()              # completion signal


class DeadlineResourceWorker(QtCore.QRunnable):
    """Background worker for fetching pools and groups from Deadline.
    
    This worker runs in a background thread to fetch available pools and groups
    from Deadline without blocking the UI. It emits signals to communicate
    results back to the main thread.
    """
    
    def __init__(self, fetch_pools: bool = True, fetch_groups: bool = True):
        """Initialize the resource worker.
        
        Args:
            fetch_pools: Whether to fetch pools from Deadline
            fetch_groups: Whether to fetch groups from Deadline
        """
        super().__init__()
        self.fetch_pools = fetch_pools
        self.fetch_groups = fetch_groups
        self.signals = DeadlineResourceWorkerSignals()
        
        # Track what was requested for logging
        tasks = []
        if fetch_pools:
            tasks.append("pools")
        if fetch_groups:
            tasks.append("groups")
        
        logger.debug(f"DeadlineResourceWorker initialized to fetch: {', '.join(tasks)}")
    
    @QtCore.Slot()
    def run(self):
        """Execute the resource fetching in the background thread."""
        try:
            logger.info("Starting Deadline resource fetching...")
            self.signals.progress_update.emit("Connecting to Deadline...")
            
            # Get Deadline connection
            connection = get_connection()
            if not connection:
                error_msg = "Failed to establish Deadline connection"
                logger.error(error_msg)
                self.signals.error_occurred.emit(error_msg)
                return
            
            # Fetch pools if requested
            if self.fetch_pools:
                self._fetch_pools(connection)
            
            # Fetch groups if requested
            if self.fetch_groups:
                self._fetch_groups(connection)
            
            logger.info("Deadline resource fetching completed successfully")
            self.signals.finished.emit()
            
        except Exception as e:
            error_msg = f"Unexpected error during resource fetching: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.signals.error_occurred.emit(error_msg)
        finally:
            # Always emit finished signal
            self.signals.finished.emit()
    
    def _fetch_pools(self, connection) -> None:
        """Fetch pools from Deadline.
        
        Args:
            connection: Deadline connection instance
        """
        try:
            self.signals.progress_update.emit("Fetching pools from Deadline...")
            logger.debug("Fetching pools from Deadline...")
            
            # Get pools using the new get_pools() method
            pools = connection.get_pools()
            
            if pools:
                logger.info(f"Successfully fetched {len(pools)} pools: {pools}")
                self.signals.pools_loaded.emit(pools)
            else:
                logger.warning("No pools returned from Deadline")
                # Emit empty list to indicate successful fetch with no results
                self.signals.pools_loaded.emit([])
                
        except Exception as e:
            error_msg = f"Failed to fetch pools from Deadline: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.signals.error_occurred.emit(error_msg)
    
    def _fetch_groups(self, connection) -> None:
        """Fetch groups from Deadline.
        
        Args:
            connection: Deadline connection instance
        """
        try:
            self.signals.progress_update.emit("Fetching groups from Deadline...")
            logger.debug("Fetching groups from Deadline...")
            
            # Get groups using the existing get_groups() method
            groups = connection.get_groups()
            
            if groups:
                logger.info(f"Successfully fetched {len(groups)} groups: {groups}")
                self.signals.groups_loaded.emit(groups)
            else:
                logger.warning("No groups returned from Deadline")
                # Emit empty list to indicate successful fetch with no results
                self.signals.groups_loaded.emit([])
                
        except Exception as e:
            error_msg = f"Failed to fetch groups from Deadline: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.signals.error_occurred.emit(error_msg)


def create_deadline_resource_worker(fetch_pools: bool = True, fetch_groups: bool = True) -> DeadlineResourceWorker:
    """Factory function to create a DeadlineResourceWorker.
    
    Args:
        fetch_pools: Whether to fetch pools from Deadline
        fetch_groups: Whether to fetch groups from Deadline
        
    Returns:
        Configured DeadlineResourceWorker instance
    """
    return DeadlineResourceWorker(fetch_pools=fetch_pools, fetch_groups=fetch_groups) 