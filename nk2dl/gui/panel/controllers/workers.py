"""
Unified background workers for nk2dl GUI operations.

This module contains all background worker classes that perform operations
without blocking the UI, including resource fetching and submission.
"""

from typing import Any, Callable, Optional, List, Dict
import logging
import threading
import time

from nk2dl.common.logging import setup_logging

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

logger = setup_logging('nk2dl.gui.panel.controllers.workers')


# ============================================================================
# HELPER CLASSES
# ============================================================================

class ThreadLogHandler(logging.Handler):
    """Custom logging handler that emits log messages via Qt signals."""
    
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        
    def emit(self, record):
        """Emit a log record via Qt signals."""
        try:
            msg = self.format(record)
            level_name = record.levelname.lower()
            
            # Use the submission worker's log_message signal
            self.signals.log_message.emit(msg, level_name)
            
        except Exception:
            self.handleError(record)


# ============================================================================
# BASE WORKER PATTERN
# ============================================================================

class BaseWorkerSignals(QtCore.QObject):
    """Base signals for worker communication."""
    progress_update = QtCore.Signal(str)    # progress message
    error_occurred = QtCore.Signal(str)     # error message
    finished = QtCore.Signal()              # completion signal


class BaseWorker(QtCore.QRunnable):
    """
    Base class for background workers with simplified pattern.
    
    Provides common functionality for background operations:
    - Error handling with logging
    - Progress reporting
    - Standardized signal pattern
    - Thread pool integration
    
    Subclasses only need to implement the do_work() method.
    """
    
    def __init__(self, operation_name: str = "operation"):
        """Initialize the base worker.
        
        Args:
            operation_name: Name of the operation for logging
        """
        super().__init__()
        self.operation_name = operation_name
        self.signals = BaseWorkerSignals()
        logger.debug(f"{self.operation_name} worker initialized")
    
    @QtCore.Slot()
    def run(self):
        """Execute the work in the background thread."""
        try:
            logger.info(f"Starting {self.operation_name}...")
            self.signals.progress_update.emit(f"Starting {self.operation_name}...")
            
            # Call the subclass implementation
            self.do_work()
            
            logger.info(f"{self.operation_name} completed successfully")
            
        except Exception as e:
            error_msg = f"Error during {self.operation_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.signals.error_occurred.emit(error_msg)
        finally:
            # Always emit finished signal
            self.signals.finished.emit()
    
    def do_work(self):
        """Override this method to implement the actual work.
        
        This method runs in a background thread and should:
        - Perform the actual work
        - Use self.signals.progress_update.emit() for progress updates
        - Raise exceptions for errors (they will be caught and handled)
        """
        raise NotImplementedError("Subclasses must implement do_work()")


def start_worker(worker: BaseWorker, 
                progress_callback: Optional[Callable[[str], None]] = None,
                error_callback: Optional[Callable[[str], None]] = None,
                finished_callback: Optional[Callable[[], None]] = None) -> None:
    """
    Convenience function to start a worker with callbacks.
    
    Args:
        worker: The worker instance to start
        progress_callback: Called with progress messages
        error_callback: Called with error messages  
        finished_callback: Called when operation completes
    """
    
    # Connect callbacks if provided
    if progress_callback:
        worker.signals.progress_update.connect(progress_callback, QtCore.Qt.QueuedConnection)
    if error_callback:
        worker.signals.error_occurred.connect(error_callback, QtCore.Qt.QueuedConnection)
    if finished_callback:
        worker.signals.finished.connect(finished_callback, QtCore.Qt.QueuedConnection)
    
    # Start in global thread pool
    QtCore.QThreadPool.globalInstance().start(worker)
    logger.info(f"Started {worker.operation_name} in background thread")


# ============================================================================
# DEADLINE RESOURCE WORKER
# ============================================================================

class DeadlineResourceWorkerSignals(BaseWorkerSignals):
    """Extended signals for deadline resource worker communication."""
    pools_loaded = QtCore.Signal(list)      # pools list
    groups_loaded = QtCore.Signal(list)     # groups list


class DeadlineResourceWorker(BaseWorker):
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
        # Track what was requested for logging
        tasks = []
        if fetch_pools:
            tasks.append("pools")
        if fetch_groups:
            tasks.append("groups")
        
        super().__init__(operation_name=f"Deadline resource fetching ({', '.join(tasks)})")
        self.fetch_pools = fetch_pools
        self.fetch_groups = fetch_groups
        self.signals = DeadlineResourceWorkerSignals()
    
    def do_work(self):
        """Fetch pools and groups from Deadline."""
        self.signals.progress_update.emit("Connecting to Deadline...")
        
        # Import here to avoid circular imports
        from nk2dl.deadline.connection import get_connection
        
        # Get Deadline connection
        connection = get_connection()
        if not connection:
            raise RuntimeError("Failed to establish Deadline connection")
        
        # Fetch pools if requested
        if self.fetch_pools:
            self._fetch_pools(connection)
        
        # Fetch groups if requested
        if self.fetch_groups:
            self._fetch_groups(connection)
    
    def _fetch_pools(self, connection) -> None:
        """Fetch pools from Deadline.
        
        Args:
            connection: Deadline connection instance
        """
        self.signals.progress_update.emit("Fetching pools from Deadline...")
        logger.debug("Fetching pools from Deadline...")
        
        # Get pools using the get_pools() method
        pools = connection.get_pools()
        
        if pools:
            logger.info(f"Successfully fetched {len(pools)} pools: {pools}")
            self.signals.pools_loaded.emit(pools)
        else:
            logger.warning("No pools returned from Deadline")
            # Emit empty list to indicate successful fetch with no results
            self.signals.pools_loaded.emit([])
    
    def _fetch_groups(self, connection) -> None:
        """Fetch groups from Deadline.
        
        Args:
            connection: Deadline connection instance
        """
        self.signals.progress_update.emit("Fetching groups from Deadline...")
        logger.debug("Fetching groups from Deadline...")
        
        # Get groups using the get_groups() method
        groups = connection.get_groups()
        
        if groups:
            logger.info(f"Successfully fetched {len(groups)} groups: {groups}")
            self.signals.groups_loaded.emit(groups)
        else:
            logger.warning("No groups returned from Deadline")
            # Emit empty list to indicate successful fetch with no results
            self.signals.groups_loaded.emit([])


# Convenience function for creating deadline resource workers
def create_deadline_resource_worker(fetch_pools: bool = True, fetch_groups: bool = True) -> DeadlineResourceWorker:
    """Factory function to create a DeadlineResourceWorker.
    
    Args:
        fetch_pools: Whether to fetch pools from Deadline
        fetch_groups: Whether to fetch groups from Deadline
        
    Returns:
        Configured DeadlineResourceWorker instance
    """
    return DeadlineResourceWorker(fetch_pools=fetch_pools, fetch_groups=fetch_groups)


# ============================================================================
# SUBMISSION WORKER  
# ============================================================================

class SubmissionWorkerSignals(QtCore.QObject):
    """Signals for submission worker communication."""
    log_message = QtCore.Signal(str, str)        # message, level
    progress_update = QtCore.Signal(str)         # status message
    finished = QtCore.Signal(bool, str, object)  # success, result_message, result
    error_occurred = QtCore.Signal(str)          # error message


class SubmissionWorker(QtCore.QRunnable):
    """Background worker for nuke script submission using QRunnable."""
    
    def __init__(self, script_path, selected_nodes, current_ui_state, settings_storage):
        super().__init__()
        self.script_path = script_path
        self.selected_nodes = selected_nodes
        self.current_ui_state = current_ui_state
        self.settings_storage = settings_storage
        self.signals = SubmissionWorkerSignals()
        
    @QtCore.Slot()
    def run(self):
        """Execute the submission in the background thread."""
        try:
            self.signals.progress_update.emit("Starting submission...")
            
            # Set up comprehensive logging redirection to capture all output
            log_handler = ThreadLogHandler(self.signals)
            log_handler.setLevel(logging.DEBUG)
            
            # Get all relevant loggers and add handler to each
            loggers_to_capture = [
                logging.getLogger(),  # Root logger
                logging.getLogger('nk2dl'),
                logging.getLogger('nk2dl.submission'),
                logging.getLogger('nk2dl.deadline'),
                logging.getLogger('nk2dl.deadline.connection'),
                logging.getLogger('nk2dl.nuke'),
                logging.getLogger('nk2dl.nuke.submission'),
            ]
            
            # Add handler to all loggers and set appropriate levels
            for logger_obj in loggers_to_capture:
                logger_obj.addHandler(log_handler)
                logger_obj.setLevel(logging.DEBUG)
            
            # Store reference to loggers for cleanup
            self.loggers_with_handler = loggers_to_capture
            
            try:
                self.signals.progress_update.emit("Building submission arguments...")
                
                # Build submission arguments
                submission_args = self.settings_storage.build_submission_args(
                    script_path=self.script_path,
                    write_nodes=self.selected_nodes,
                    **self.current_ui_state
                )
                
                self.signals.progress_update.emit("Submitting to Deadline...")
                
                # Submit to Deadline
                from nk2dl.nuke.submission import submit_nuke_script
                result = submit_nuke_script(**submission_args)
                
                # Parse result - handle different return types
                # Result is a list of job dictionaries from successful submissions
                if result and isinstance(result, list) and len(result) > 0:
                    # Check if any jobs were submitted successfully
                    job_ids = [job_dict.get('job_id') for job_dict in result if job_dict.get('job_id')]
                    if job_ids:
                        self.signals.finished.emit(True, f"Submission completed successfully! Job IDs: {', '.join(job_ids)}", result)
                    else:
                        self.signals.finished.emit(False, "Submission completed but no job IDs returned", result)
                else:
                    self.signals.finished.emit(False, "Submission completed - check console for details", result)
                    
            finally:
                # Clean up logging handlers from all loggers
                if hasattr(self, 'loggers_with_handler'):
                    for logger_obj in self.loggers_with_handler:
                        try:
                            logger_obj.removeHandler(log_handler)
                        except ValueError:
                            pass  # Handler wasn't in this logger
                    delattr(self, 'loggers_with_handler')
                
        except Exception as e:
            error_msg = f"Submission error: {str(e)}"
            import traceback
            detailed_error = f"{error_msg}\n{traceback.format_exc()}"
            self.signals.error_occurred.emit(detailed_error)
            self.signals.finished.emit(False, error_msg, None)


# ============================================================================
# NODE DATA WORKER
# ============================================================================

class NodeDataWorkerSignals(QtCore.QObject):
    """Signals for node data worker communication."""
    data_ready = QtCore.Signal(list)            # Emitted when node data extraction is complete
    progress_update = QtCore.Signal(int, str)   # Emitted with progress percentage and status message
    error_occurred = QtCore.Signal(str)         # Emitted when an error occurs during extraction
    debug_info = QtCore.Signal(str)             # Emitted with debug information for troubleshooting
    finished = QtCore.Signal()                  # Emitted when operation completes


class NodeDataWorker(QtCore.QObject):
    """Worker for extracting write node data from Nuke scripts with threading support.
    
    This class handles the discovery and extraction of write node data from the current
    Nuke script in a background thread to avoid blocking the UI.
    
    Note: This worker uses Python threading instead of Qt's QRunnable because it needs
    extensive interaction with the Nuke API during data extraction.
    """
    
    def __init__(self, parent=None):
        """Initialize the node data worker.
        
        Args:
            parent: Parent QObject for Qt hierarchy
        """
        super().__init__(parent)
        self.signals = NodeDataWorkerSignals()
        self._should_cancel = False
        self._current_thread = None
        
        logger.debug("NodeDataWorker initialized")
    
    def refresh_data_async(self):
        """Start background thread to refresh node data.
        
        This method starts a new thread to extract node data from the current
        Nuke script. Progress is reported via the progress_update signal, and
        results are returned via the data_ready signal.
        """
        # Cancel any existing operation
        self.cancel_operation()
        
        # Start new background thread
        self._should_cancel = False
        self._current_thread = threading.Thread(target=self._refresh_worker, daemon=True)
        self._current_thread.start()
        
        logger.info("Started background thread for node data extraction")
    
    def cancel_operation(self):
        """Cancel the current background operation if running.
        
        Sets the cancellation flag and waits for the current thread to complete.
        """
        if self._current_thread and self._current_thread.is_alive():
            logger.info("Cancelling background node data operation")
            self._should_cancel = True
            
            # Wait for thread to finish (with timeout)
            self._current_thread.join(timeout=2.0)
            
            if self._current_thread.is_alive():
                logger.warning("Background thread did not finish within timeout")
        
        self._current_thread = None
        self._should_cancel = False
    
    def _refresh_worker(self):
        """Background worker thread method for extracting node data.
        
        This method runs in a background thread and extracts write node data
        from the current Nuke script. It reports progress and handles cancellation.
        """
        try:
            logger.debug("Starting node data extraction in background thread")
            logger.debug(f"Thread ID: {threading.get_ident()}")
            
            # Phase 1: Discovery (50% of progress)
            self.signals.progress_update.emit(0, "Discovering write nodes...")
            
            if self._should_cancel:
                logger.debug("Operation cancelled during discovery phase")
                return
            
            # Get write nodes from main thread
            logger.debug("Calling _get_write_nodes_data_sync() for node discovery")
            write_nodes_data = self._get_write_nodes_data_sync()
            logger.debug(f"Node discovery completed, found {len(write_nodes_data)} write nodes")
            
            if self._should_cancel:
                logger.debug("Operation cancelled after node discovery")
                return
            
            self.signals.progress_update.emit(50, f"Found {len(write_nodes_data)} write nodes")
            
            # Small delay to allow UI updates and check for cancellation
            time.sleep(0.1)
            
            if self._should_cancel:
                logger.debug("Operation cancelled before data extraction")
                return
            
            # Phase 2: Data extraction (50% of progress)
            logger.debug("Starting data extraction phase")
            extracted_data = []
            
            for i, node_data in enumerate(write_nodes_data):
                if self._should_cancel:
                    logger.debug("Operation cancelled during data extraction")
                    return
                
                # Extract data for this node
                logger.debug(f"Processing node {i+1}/{len(write_nodes_data)}: {node_data['name']}")
                try:
                    extracted_node_data = self._extract_node_data(node_data['node'], node_data['name'])
                    extracted_data.append(extracted_node_data)
                    logger.debug(f"Successfully extracted data for node {node_data['name']}")
                    
                    # Update progress (50% base + 50% * progress through nodes)
                    progress = 50 + int((i + 1) / len(write_nodes_data) * 50)
                    self.signals.progress_update.emit(progress, f"Extracting data from {node_data['name']}...")
                    
                    # Only add delay every 10 nodes for cancellation responsiveness  
                    if i % 10 == 0:
                        time.sleep(0.01)
                    
                except Exception as e:
                    logger.error(f"Error extracting data from node {node_data['name']}: {e}", exc_info=True)
                    # Continue with next node instead of failing completely
                    continue
            
            if self._should_cancel:
                logger.debug("Operation cancelled after data extraction")
                return
            
            logger.debug(f"Data extraction phase completed, extracted data for {len(extracted_data)} nodes")
            self.signals.progress_update.emit(100, f"Extraction complete - {len(extracted_data)} nodes processed")
            
            # Log a summary of extracted data
            logger.debug("=== EXTRACTION SUMMARY ===")
            for i, data in enumerate(extracted_data):
                summary_msg = f"Node {i+1}: {data.get('Node', 'Unknown')} - Order: {data.get('Order', 'Unknown')} - Filename: {data.get('Filename', 'Unknown')}"
                logger.debug(summary_msg)
            
            # Emit results
            logger.debug("Emitting data_ready signal with extracted data")
            self.signals.data_ready.emit(extracted_data)
            logger.info(f"Node data extraction completed successfully - {len(extracted_data)} nodes")
            
        except Exception as e:
            error_msg = f"Error during node data extraction: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.signals.error_occurred.emit(error_msg)
        finally:
            self.signals.finished.emit()
    
    def _get_write_nodes_data_sync(self) -> List[Dict[str, Any]]:
        """Get write nodes from the current Nuke script (must run in main thread).
        
        This method must be called from the main thread as it accesses Nuke nodes.
        
        Returns:
            List of dictionaries containing node references and basic info
        """
        try:
            if not NUKE_AVAILABLE:
                raise RuntimeError("Nuke not available for node data extraction")
            
            # Get write node types from config  
            write_node_types = self._get_write_node_types()
            logger.debug(f"Looking for write node types: {write_node_types}")
            
            # Find all write nodes
            write_nodes_data = []
            all_nodes = nuke.allNodes()
            logger.debug(f"Total nodes in script: {len(all_nodes)}")
            
            for node in all_nodes:
                logger.debug(f"Checking node: {node.fullName()} (class: {node.Class()})")
                
                if node.Class() in write_node_types:
                    logger.debug(f"Node {node.fullName()} is a write node type")
                    
                    # Check if node is disabled
                    disabled = False
                    try:
                        disabled = node['disable'].value()
                        logger.debug(f"Node {node.fullName()}: disabled = {disabled}")
                    except Exception as e:
                        logger.debug(f"Node {node.fullName()}: no disable knob or error checking: {e}")
                        pass  # Some nodes might not have disable knob
                    
                    if not disabled:
                        node_info = {
                            'node': node,
                            'name': node.fullName(),
                            'class': node.Class()
                        }
                        write_nodes_data.append(node_info)
                        logger.debug(f"Added enabled write node: {node.fullName()} (class: {node.Class()})")
                    else:
                        logger.debug(f"Skipped disabled write node: {node.fullName()}")
            
            logger.debug(f"Found {len(write_nodes_data)} enabled write nodes")
            return write_nodes_data
            
        except Exception as e:
            logger.error(f"Error during write nodes discovery: {e}", exc_info=True)
            raise
    
    def _extract_node_data(self, node, node_name: str) -> Dict[str, Any]:
        """Extract data from a write node for table display.
        
        Args:
            node: Nuke node reference
            node_name: Node name
            
        Returns:
            Dictionary containing extracted node data
        """
        try:
            extracted_data = {
                'Node': node_name,
                'Filename': self._get_filename_only(node),
                'Order': self._get_render_order(node),
                'Render': True,  # Default to enabled for rendering
            }
            
            logger.debug(f"Extracted data for {node_name}: {extracted_data}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting data from node {node_name}: {e}", exc_info=True)
            # Return basic data if extraction fails
            return {
                'Node': node_name,
                'Filename': 'ERROR',
                'Order': 'ERROR',
                'Render': False,
            }
    
    def _get_filename_only(self, node) -> str:
        """Get the filename portion only from a write node's file path.
        
        Args:
            node: Nuke write node
            
        Returns:
            Just the filename portion of the file path
        """
        try:
            # Get the file knob
            file_knob = node['file']
            
            if not file_knob:
                return "No file specified"
            
            # Get the file path
            file_path = file_knob.value()
            
            if not file_path:
                return "No file specified"
            
            # Import the utility function
            from nk2dl.nuke.utils import node_pretty_path
            
            # Use the utility function to get a pretty version of the path
            pretty_path = node_pretty_path(node)
            
            # Extract just the filename from the pretty path
            from pathlib import Path
            filename = Path(pretty_path).name
            
            logger.debug(f"Node {node.fullName()}: file_path={file_path}, pretty_path={pretty_path}, filename={filename}")
            
            return filename
            
        except Exception as e:
            logger.debug(f"Error getting filename for node {node.fullName()}: {e}")
            return f"Error: {str(e)}"
    
    def _get_render_order(self, node) -> str:
        """Get the render order for a write node.
        
        Args:
            node: Nuke write node
            
        Returns:
            Render order as string
        """
        try:
            # Check if the node has the standard render_order knob
            render_order_knob = None
            try:
                render_order_knob = node['render_order']
            except (NameError, KeyError):
                # Knob doesn't exist
                pass
            
            if render_order_knob is not None:
                # Knob exists, get its value
                render_order = render_order_knob.value()
                logger.debug(f"Node {node.fullName()}: render order = {render_order}")
                return str(int(render_order))
            
            # No render_order knob found, use default of 0
            # This matches the behavior in the submission code
            logger.debug(f"Node {node.fullName()}: no render_order knob found, using default 0")
            return "0"
            
        except Exception as e:
            logger.debug(f"Error getting render order for node {node.fullName()}: {e}")
            return "0"  # Fallback to order 0
    

    
    def _get_write_node_types(self) -> List[str]:
        """Get write node types from configuration.
        
        Returns:
            List of write node class names to look for
        """
        # Import here to avoid circular imports
        from nk2dl.common.config import config
        
        # Get node types from config
        node_types = ['Write', 'DeepWrite']  # Default types
        custom_types = config.get('submission.custom_write_classes', [])
        
        if custom_types:
            node_types.extend(custom_types)
        
        return node_types


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Helper classes
    'ThreadLogHandler',
    
    # Base pattern
    'BaseWorker',
    'BaseWorkerSignals', 
    'start_worker',
    
    # Specific workers
    'DeadlineResourceWorker',
    'DeadlineResourceWorkerSignals',
    'create_deadline_resource_worker',
    'SubmissionWorker',
    'SubmissionWorkerSignals',
    'NodeDataWorker',
    'NodeDataWorkerSignals',
] 