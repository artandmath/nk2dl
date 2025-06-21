"""
Node data provider repository for extracting write node data from Nuke scripts.

This module handles the threaded extraction of write node data from the current
Nuke script, providing signals for progress updates and completion.
"""

import threading
import time
import os
import re
from typing import List, Dict, Any, Optional

from ....common.logging import setup_logging
from ....common.config import config
from ....nuke.utils import nuke_module, node_pretty_path
from ..constants import TableColumns

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

logger = setup_logging('nk2dl.gui.panel.repositories.node_data')


class NodeDataProvider(QtCore.QObject):
    """Provider for extracting write node data from Nuke scripts with threading support.
    
    This class handles the discovery and extraction of write node data from the current
    Nuke script in a background thread to avoid blocking the UI.
    
    Signals:
        dataReady (list): Emitted when node data extraction is complete
        progressUpdate (int, str): Emitted with progress percentage and status message
        errorOccurred (str): Emitted when an error occurs during extraction
        debugInfo (str): Emitted with debug information for troubleshooting
    """
    
    # Qt Signals
    dataReady = QtCore.Signal(list)
    progressUpdate = QtCore.Signal(int, str)
    errorOccurred = QtCore.Signal(str)
    debugInfo = QtCore.Signal(str)
    
    def __init__(self, parent=None):
        """Initialize the node data provider.
        
        Args:
            parent: Parent QObject for Qt hierarchy
        """
        super().__init__(parent)
        self._should_cancel = False
        self._current_thread = None
        
        logger.debug("NodeDataProvider initialized")
    

    
    def refresh_data_async(self):
        """Start background thread to refresh node data.
        
        This method starts a new thread to extract node data from the current
        Nuke script. Progress is reported via the progressUpdate signal, and
        results are returned via the dataReady signal.
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
            self.progressUpdate.emit(0, "Discovering write nodes...")
            
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
            
            self.progressUpdate.emit(50, f"Found {len(write_nodes_data)} write nodes")
            
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
                    self.progressUpdate.emit(progress, f"Extracting data from {node_data['name']}...")
                    
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
            self.progressUpdate.emit(100, f"Extraction complete - {len(extracted_data)} nodes processed")
            
            # Log a summary of extracted data
            logger.debug("=== EXTRACTION SUMMARY ===")
            for i, data in enumerate(extracted_data):
                summary_msg = f"Node {i+1}: {data.get('Node', 'Unknown')} - Order: {data.get('Order', 'Unknown')} - Filename: {data.get('Filename', 'Unknown')}"
                logger.debug(summary_msg)
            
            # Emit results
            logger.debug("Emitting dataReady signal with extracted data")
            self.dataReady.emit(extracted_data)
            logger.info(f"Node data extraction completed successfully - {len(extracted_data)} nodes")
            
        except Exception as e:
            error_msg = f"Error during node data extraction: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.errorOccurred.emit(error_msg)
    
    def _get_write_nodes_data_sync(self) -> List[Dict[str, Any]]:
        """Get write nodes from the current Nuke script (must run in main thread).
        
        This method must be called from the main thread as it accesses Nuke nodes.
        
        Returns:
            List of dictionaries containing node references and basic info
        """
        try:
            nuke = nuke_module()
            
            # Get write node types from config
            write_node_types = self._get_write_node_types()
            logger.debug(f"Looking for write node types: {write_node_types}")
            
            # Find all write nodes
            write_nodes_data = []
            all_nodes = nuke.allNodes()
            logger.debug(f"Total nodes in script: {len(all_nodes)}")
            
            for node in all_nodes:
                logger.debug(f"Checking node: {node.name()} (class: {node.Class()})")
                
                if node.Class() in write_node_types:
                    logger.debug(f"Node {node.name()} is a write node type")
                    
                    # Check if node is disabled
                    disabled = False
                    try:
                        disabled = node['disable'].value()
                        logger.debug(f"Node {node.name()}: disabled = {disabled}")
                    except Exception as e:
                        logger.debug(f"Node {node.name()}: no disable knob or error checking: {e}")
                        pass  # Some nodes might not have disable knob
                    
                    if not disabled:
                        node_info = {
                            'node': node,
                            'name': node.name(),
                            'class': node.Class()
                        }
                        write_nodes_data.append(node_info)
                        logger.debug(f"Added enabled write node: {node.name()} (class: {node.Class()})")
                    else:
                        logger.debug(f"Skipped disabled write node: {node.name()}")
                else:
                    logger.debug(f"Node {node.name()} is not a write node type (class: {node.Class()})")
            
            logger.info(f"Discovered {len(write_nodes_data)} enabled write nodes")
            for node_info in write_nodes_data:
                logger.debug(f"Final write node list: {node_info['name']} (class: {node_info['class']})")
                
            return write_nodes_data
            
        except Exception as e:
            logger.error(f"Error discovering write nodes: {e}", exc_info=True)
            raise
    
    def _extract_node_data(self, node, node_name: str) -> Dict[str, Any]:
        """Extract data from a single write node.
        
        Args:
            node: The Nuke node object
            node_name: Name of the node
            
        Returns:
            Dictionary containing extracted node data
        """
        try:
            logger.debug(f"Extracting data from node: {node_name}")
            
            # Get render order
            render_order = self._get_render_order(node)
            
            # Get filename
            filename = self._get_filename_only(node)
            
            # Initialize with default values (None means inherit from settings)
            node_data = {
                "Order": render_order,
                "Node": node_name,
                "Filename": filename,
                "Priority": None,
                "ChunkSize": None,
                "Frames": None,
                "NodesFrames": None,
                "TaskTimeout": None,
                "AutoTimeout": None,
                "RenderMode": None,
                "NukeX": None,
                "BatchMode": None,
                "ReloadPlugin": None,
                "Pool": None,
                "SecondaryPool": None,
                "Group": None,
                "Threads": None,
                "MinRam": None,
                "MaxRam": None,
                "UseGPU": None,
                "GPUId": None,
                "ConcurrentTasks": None,
                "WorkerTaskLimit": None,
                "MachineList": None,
                "Limits": None
            }
            
            logger.debug(f"Extracted data for {node_name}: Order={render_order}, Filename={filename}")
            return node_data
            
        except Exception as e:
            logger.error(f"Error extracting data from node {node_name}: {e}", exc_info=True)
            # Return minimal data with just node name
            fallback_data = {
                "Order": "1000",  # Default order
                "Node": node_name,
                "Filename": "",
                # All other values will be None (inherited)
                **{col: None for col in TableColumns.HEADERS[3:]},  # Skip Order, Node, Filename
            }
            logger.debug(f"Using fallback data for {node_name}: Order=1000, Filename=''")
            return fallback_data
    
    def _get_filename_only(self, node) -> str:
        """Get the filename from a write node's file path.
        
        Uses node['file'].evaluate() and restores #### and %04d patterns
        in the filename only (not directories).
        
        Args:
            node: The Nuke node object
            
        Returns:
            Just the filename part of the file path with frame patterns restored
        """
        try:
            logger.debug(f"Getting filename for node: {node.name()}")
            
            if 'file' not in node.knobs():
                logger.debug(f"Node {node.name()}: no 'file' knob found")
                return ""
            
            logger.debug(f"Node {node.name()}: 'file' knob exists, extracting path")
            
            # Use the existing pretty path function that handles evaluate() and pattern restoration
            full_path = node_pretty_path(node)
            logger.debug(f"Node {node.name()}: full_path from node_pretty_path = '{full_path}'")
            
            if full_path:
                filename = os.path.basename(full_path)
                logger.debug(f"Node {node.name()}: extracted filename = '{filename}'")
                return filename
            else:
                logger.debug(f"Node {node.name()}: node_pretty_path returned empty/None")
                return ""
                
        except Exception as e:
            logger.error(f"Error getting filename from node {node.name()}: {e}", exc_info=True)
            return ""
    
    def _get_render_order(self, node) -> str:
        """Get or create the render order for a write node.
        
        Args:
            node: The Nuke node object
            
        Returns:
            Render order as string
        """
        try:
            logger.debug(f"Getting render order for node: {node.name()}")
            
            # Check if render order knob exists
            if 'render_order' in node.knobs():
                order = node['render_order'].value()
                
                if order is not None:
                    # Convert float to int if needed, then to string
                    try:
                        # Handle different numeric types
                        if isinstance(order, (int, float)):
                            order_int = int(order)
                            order_str = str(order_int)
                            return order_str
                        else:
                            # Try to parse as string
                            order_float = float(str(order))
                            order_int = int(order_float)
                            order_str = str(order_int)
                            return order_str
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Could not convert render_order '{order}' to int: {e}")
                        # Fall through to default handling
            else:
                # Create render_order knob if it doesn't exist
                try:
                    nuke = nuke_module()
                    # Add integer knob for render order
                    render_order_knob = nuke.Int_Knob('render_order', 'Render Order')
                    render_order_knob.setValue(1000)  # Default value
                    node.addKnob(render_order_knob)
                    logger.debug(f"Created render_order knob on node {node.name()} with default value 1000")
                    return "1000"
                except Exception as e:
                    logger.warning(f"Could not create render_order knob on node {node.name()}: {e}")
            
            # Fallback to default
            return "1000"
            
        except Exception as e:
            logger.error(f"Error getting render order from node {node.name()}: {e}", exc_info=True)
            return "1000"
    
    def _get_write_node_types(self) -> List[str]:
        """Get the list of write node types from configuration.
        
        Returns:
            List of write node class names to look for
        """
        try:
            # Default node types
            node_types = ['Write', 'DeepWrite']
            
            # Add custom write classes from config
            custom_classes = config.get('submission.custom_write_classes', [])
            if custom_classes:
                node_types.extend(custom_classes)
                logger.debug(f"Added custom write classes: {custom_classes}")
            
            return node_types
            
        except Exception as e:
            logger.warning(f"Error getting write node types from config: {e}")
            # Fallback to standard types
            return ['Write', 'DeepWrite'] 