"""
Script analyzer for Nuke scripts.

Provides functionality to analyze Nuke scripts for write nodes,
their dependencies, render order, and other relevant information.
"""
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import os
import nuke


class ScriptAnalyzer:
    """
    Analyzes Nuke scripts for write nodes, dependencies, and render order.
    
    This class is responsible for:
    - Finding all write nodes in a script
    - Filtering write nodes based on criteria
    - Determining render order and dependencies
    - Organizing write nodes for submission
    """
    
    def __init__(self) -> None:
        """Initialize the script analyzer."""
        self._write_nodes = []
        self._dependencies = {}
        self._render_order = {}
        
    def get_write_nodes(self, 
                       selected_only: bool = False) -> List[Any]:
        """
        Get all write nodes in the current Nuke script matching the criteria.
        
        Args:
            selected_only: If True, only return selected write nodes
            
        Returns:
            List of write nodes matching criteria
        """
        # Find all write nodes in the script
        all_write_nodes = self._find_all_write_nodes()
        
        # Filter based on criteria
        filtered_nodes = []
        for node in all_write_nodes:
            # Skip disabled nodes
            if node['disable'].value():
                continue
                
            # Check selection status if needed
            if selected_only and not self._is_node_or_parent_selected(node):
                continue
                
            filtered_nodes.append(node)
            
        # Store the filtered nodes
        self._write_nodes = filtered_nodes
        return self._write_nodes
    
    def analyze_dependencies(self, write_nodes: Optional[List[Any]] = None) -> Dict[str, List[str]]:
        """
        Analyze dependencies between write nodes based on render order.
        
        Dependencies are determined by the render order value:
        - Nodes with the same render order can render in parallel
        - Nodes with higher render order values depend on nodes with lower values
        - Nodes without a render order value are treated as having order 0
        - Only direct dependencies are created (no transitive dependencies)
        
        Args:
            write_nodes: Optional list of write nodes to analyze. If None, 
                         will use all write nodes in the script.
                         
        Returns:
            Dictionary mapping write node names to their dependent write nodes
        """
        if write_nodes is None:
            write_nodes = self._write_nodes
            
        if not write_nodes:
            # No write nodes to analyze
            return {}
            
        # Get render order for each node
        node_orders = {}
        for node in write_nodes:
            node_name = node.fullName()
            node_orders[node_name] = self._get_render_order(node)
            
        # Group nodes by render order
        order_to_nodes = {}
        for node in write_nodes:
            node_name = node.fullName()
            order = node_orders[node_name]
            if order not in order_to_nodes:
                order_to_nodes[order] = []
            order_to_nodes[order].append(node_name)
            
        # Sort the render orders
        sorted_orders = sorted(order_to_nodes.keys())
        
        # Build dependencies based on render order
        dependencies = {}
        for i, order in enumerate(sorted_orders):
            # Nodes in this render order
            nodes = order_to_nodes[order]
            
            # Find which render order these nodes depend on (the highest previous order)
            dependents = []
            if i > 0:  # If not the first order, depend on nodes from the previous order
                prev_order = sorted_orders[i-1]
                dependents = order_to_nodes[prev_order]
            
            # Set dependencies for each node in this order
            for node_name in nodes:
                dependencies[node_name] = dependents.copy()
                
        self._dependencies = dependencies
        return dependencies
        
    def get_nodes_in_render_order(self, write_nodes: Optional[List[Any]] = None) -> List[Any]:
        """
        Get write nodes sorted by their render order.
        
        Args:
            write_nodes: Optional list of write nodes to sort. If None,
                         will use all write nodes in the script.
        
        Returns:
            List of write nodes sorted by render order
        """
        if write_nodes is None:
            write_nodes = self._write_nodes
            
        if not write_nodes:
            return []
            
        # Sort nodes by render order
        return sorted(write_nodes, key=self._get_render_order)
    
    def get_dependency_job_ids(self, node_to_job_id: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Convert node dependencies to job ID dependencies.
        
        Args:
            node_to_job_id: Dictionary mapping node names to job IDs
            
        Returns:
            Dictionary mapping job IDs to their dependency job IDs
        """
        job_dependencies = {}
        
        for node_name, upstream_nodes in self._dependencies.items():
            if node_name in node_to_job_id:
                job_id = node_to_job_id[node_name]
                job_dependencies[job_id] = [
                    node_to_job_id[dep_node] 
                    for dep_node in upstream_nodes 
                    if dep_node in node_to_job_id
                ]
                
        return job_dependencies
    
    def _find_all_write_nodes(self) -> List[Any]:
        """
        Find all Write nodes in the script, including those in groups.
        
        Returns:
            List of all Write nodes in the script
        """
        # Find all nodes of class Write
        all_nodes = nuke.allNodes(recurseGroups=True)
        write_nodes = [n for n in all_nodes if n.Class() == "Write"]
        return write_nodes
    
    def _is_node_or_parent_selected(self, node: Any) -> bool:
        """
        Check if a node or any of its parent nodes is selected.
        
        Args:
            node: The node to check
            
        Returns:
            True if the node or any parent is selected, False otherwise
        """
        if node.isSelected():
            return True
            
        # Check if the node is inside a group and if that group is selected
        parent_path = '.'.join(node.fullName().split('.')[:-1])
        if parent_path:
            parent_node = nuke.toNode(parent_path)
            if parent_node:
                return self._is_node_or_parent_selected(parent_node)
                
        return False
    
    def _get_render_order(self, node: Any) -> int:
        """
        Get the render order value of a node.
        
        Args:
            node: The node to get the render order for
            
        Returns:
            Render order value (lower numbers render first)
        """
        try:
            # Get the render_order knob value if it exists
            value = node['render_order'].value()
        except (KeyError, NameError):
            # If the knob doesn't exist, use 0 (default render order)
            value = 0
            
        return value 