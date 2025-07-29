# -*- coding: utf-8 -*-
"""GSVView component for the nk2dl panel.

This module contains the GSVView class which handles the UI for the GSV tree, including primary/secondary GSV
input fields, tree widget, and control buttons.
"""

try:
    import nuke
    NUKE_AVAILABLE = True
    
    # Detect Nuke version and import appropriate PySide
    nuke_version = nuke.NUKE_VERSION_MAJOR
    if nuke_version >= 16:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    else:
        from PySide2 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide2"
        
except ImportError:
    NUKE_AVAILABLE = False
    PYSIDE_VERSION = "Unknown"
    # Fallback imports for testing without Nuke
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    except ImportError:
        try:
            from PySide2 import QtWidgets, QtCore, QtGui
            PYSIDE_VERSION = "PySide2"
        except ImportError:
            raise ImportError("Neither PySide6 nor PySide2 is available")

from ..widgets import ColoredGroupBox
from ..constants import Settings, Sizes, GSVDefaults


class GSVView(QtWidgets.QWidget):
    """View for the GSV hierarchy tree with controls.
    
    This view handles the UI for the GSV tree, including primary/secondary GSV
    input fields, tree widget, and control buttons.
    """
    
    def __init__(self, gsv_model, parent=None):
        super().__init__(parent)
        self.gsv_model = gsv_model
        
        # Create the main layout and UI components
        self._create_ui()
        self._connect_signals()
        self._load_data_from_model()
    
    def _create_ui(self):
        """Create the GSV UI components."""
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        self.setLayout(layout)
        
        # GSV input fields
        self._create_input_fields()
        layout.addLayout(self.input_layout)
        
        # Tree widget
        self._create_tree_widget()
        layout.addWidget(self.gsvs_tree)
        
        # Control buttons
        self._create_control_buttons()
        layout.addLayout(self.controls_layout)
    
    def _create_input_fields(self):
        """Create the GSV input fields."""
        self.input_layout = QtWidgets.QHBoxLayout()
        
        # Primary GSVs (tree hierarchy)
        self.input_layout.addWidget(QtWidgets.QLabel("Primary GSVs:"))
        self.primary_gsvs_field = QtWidgets.QLineEdit()
        self.primary_gsvs_field.setPlaceholderText("Sequence, Shotcode...")
        self.primary_gsvs_field.textChanged.connect(self._on_primary_gsv_text_changed)
        self.input_layout.addWidget(self.primary_gsvs_field)
        
        # Secondary GSVs (columns)
        self.input_layout.addWidget(QtWidgets.QLabel("Secondary GSVs:"))
        self.secondary_gsvs_field = QtWidgets.QLineEdit()
        self.secondary_gsvs_field.setPlaceholderText("Resolution, Format...")
        self.secondary_gsvs_field.textChanged.connect(self._on_secondary_gsv_text_changed)
        self.input_layout.addWidget(self.secondary_gsvs_field)
        
        # Refresh button
        refresh_hierarchy_btn = QtWidgets.QPushButton("Refresh Hierarchy")
        refresh_hierarchy_btn.clicked.connect(self._refresh_hierarchy)
        self.input_layout.addWidget(refresh_hierarchy_btn)
    
    def _create_tree_widget(self):
        """Create the GSV tree widget."""
        self.gsvs_tree = QtWidgets.QTreeWidget()
        self.gsvs_tree.setRootIsDecorated(True)
        self.gsvs_tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.gsvs_tree.setAlternatingRowColors(True)
        self.gsvs_tree.itemChanged.connect(self._on_tree_item_changed)
        
        # Apply centered checkbox delegate
        from ..delegates import CenteredCheckboxDelegate
        self.centered_delegate = CenteredCheckboxDelegate(self.gsvs_tree)
        self.gsvs_tree.setItemDelegate(self.centered_delegate)
        
        # Set up tree styling
        checkbox_style = """
            QTreeWidget::item {
                padding-top: 2px;
                padding-bottom: 2px;
            }
            QTreeWidget::item:hover {
                background-color: rgba(255, 255, 255, 20);
            }
            QTreeWidget::item:selected {
                background-color: transparent;
                border: none;
            }
            QTreeWidget::item:selected:active {
                background-color: transparent;
            }
            QTreeWidget::item:selected:!active {
                background-color: transparent;
            }
        """
        self.gsvs_tree.setStyleSheet(checkbox_style)
    
    def _create_control_buttons(self):
        """Create the control buttons."""
        self.controls_layout = QtWidgets.QHBoxLayout()
        
        expand_all_btn = QtWidgets.QPushButton("Expand All")
        expand_all_btn.clicked.connect(self.gsvs_tree.expandAll)
        self.controls_layout.addWidget(expand_all_btn)
        
        collapse_all_btn = QtWidgets.QPushButton("Collapse All")
        collapse_all_btn.clicked.connect(self.gsvs_tree.collapseAll)
        self.controls_layout.addWidget(collapse_all_btn)
        
        self.controls_layout.addStretch()
        
        check_all_btn = QtWidgets.QPushButton("Check All")
        check_all_btn.clicked.connect(self._check_all_items)
        self.controls_layout.addWidget(check_all_btn)
        
        uncheck_all_btn = QtWidgets.QPushButton("Uncheck All")
        uncheck_all_btn.clicked.connect(self._uncheck_all_items)
        self.controls_layout.addWidget(uncheck_all_btn)
    
    def _connect_signals(self):
        """Connect model signals to view updates."""
        self.gsv_model.hierarchyChanged.connect(self._on_hierarchy_changed)
        self.gsv_model.selectionChanged.connect(self._on_selection_changed)
    
    def _load_data_from_model(self):
        """Load data from the model into the UI."""
        # Load text fields
        self.primary_gsvs_field.setText(self.gsv_model.get_primary_gsv_text())
        self.secondary_gsvs_field.setText(self.gsv_model.get_secondary_gsv_text())
        
        # Refresh the hierarchy
        self._refresh_hierarchy()
    
    def _refresh_hierarchy(self):
        """Refresh the GSV hierarchy tree."""
        # Store current header view to preserve it
        current_header = self.gsvs_tree.header() if hasattr(self.gsvs_tree, 'header') else None
        from ..widgets import GroupedHeaderView
        is_grouped_header = isinstance(current_header, GroupedHeaderView)
        
        # Clear existing tree
        self.gsvs_tree.clear()
        
        # Get headers and groups from model
        headers = self.gsv_model.get_tree_headers()
        groups = self.gsv_model.get_tree_groups()
        
        if not headers:
            return
        
        # Set up tree headers
        self.gsvs_tree.setHeaderLabels(headers)
        self.gsvs_tree.setColumnCount(len(headers))
        
        # Apply grouped header view if we have secondary columns
        if len(headers) > 1:
            # Only create new header if we don't have one or it's not grouped
            if not is_grouped_header:
                grouped_header = GroupedHeaderView(QtCore.Qt.Horizontal, self.gsvs_tree)
                self.gsvs_tree.setHeader(grouped_header)
            else:
                grouped_header = current_header
            
            grouped_header.setGroups(groups)
        
        # Build the tree structure
        self._build_tree_from_model()
        
        # Expand first level by default
        self.gsvs_tree.expandToDepth(0)
        
        # Set up column properties
        self._setup_column_properties()
        
        # Force a repaint to ensure everything displays correctly
        self.gsvs_tree.update()
    
    def _build_tree_from_model(self):
        """Build the tree structure from the model data."""
        tree_items = self.gsv_model.build_tree_structure()
        self._add_tree_items(tree_items, None)
    
    def _add_tree_items(self, items, parent_widget_item):
        """Recursively add tree items to the widget.
        
        Args:
            items (list): List of item data dictionaries
            parent_widget_item (QTreeWidgetItem): Parent widget item (None for root)
        """
        for item_data in items:
            # Create tree item
            tree_item = QtWidgets.QTreeWidgetItem()
            tree_item.setText(0, item_data['text'])
            
            # Add checkbox to primary column (column 0)
            tree_item.setFlags(tree_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            tree_item.setCheckState(0, QtCore.Qt.Unchecked)
            
            # Store metadata for primary column
            tree_item.setData(0, QtCore.Qt.UserRole, {
                'level': item_data['level'],
                'value': item_data['value'],
                'level_index': item_data['level_index'],
                'is_primary': True,
                'path': item_data['path']
            })
            
            # Add checkboxes for secondary GSVs
            headers = self.gsv_model.get_tree_headers()
            secondary_gsv_data = self.gsv_model.get_secondary_gsv_data()
            secondary_gsv_levels = self.gsv_model.get_secondary_gsv_levels()
            
            column_index = 1
            for secondary_gsv in secondary_gsv_levels:
                if secondary_gsv in secondary_gsv_data:
                    for value in secondary_gsv_data[secondary_gsv]:
                        if column_index < len(headers):
                            tree_item.setFlags(tree_item.flags() | QtCore.Qt.ItemIsUserCheckable)
                            tree_item.setCheckState(column_index, QtCore.Qt.Unchecked)
                            
                            # Store metadata for secondary columns
                            tree_item.setData(column_index, QtCore.Qt.UserRole, {
                                'secondary_gsv': secondary_gsv,
                                'secondary_value': value,
                                'is_primary': False,
                                'path': item_data['path']
                            })
                            column_index += 1
            
            # Add to parent or root
            if parent_widget_item:
                parent_widget_item.addChild(tree_item)
            else:
                self.gsvs_tree.addTopLevelItem(tree_item)
            
            # Recursively add children
            if item_data['children']:
                self._add_tree_items(item_data['children'], tree_item)
    
    def _setup_column_properties(self):
        """Set up column properties including width and alignment."""
        header = self.gsvs_tree.header()
        
        # Set a reasonable minimum section size for GSV columns
        # This is separate from the node settings table minimum
        header.setMinimumSectionSize(GSVDefaults.GSV_HEADER_MIN_SECTION_SIZE)
        
        # Set up each column
        for i in range(self.gsvs_tree.columnCount()):
            if i == 0:
                # Primary GSVs column
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.Interactive)
                primary_width = self._calculate_primary_column_width()
                header.resizeSection(i, primary_width)
            else:
                # Secondary GSV columns
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.Fixed)
                secondary_width = self._calculate_secondary_column_width()
                header.resizeSection(i, secondary_width)
    
    def _calculate_primary_column_width(self):
        """Calculate the optimal width for the primary GSVs column."""
        font = self.gsvs_tree.font()
        font_metrics = QtGui.QFontMetrics(font)
        max_width = 0
        
        # Check the header text width
        header_text = "Primary GSVs"
        try:
            header_width = font_metrics.horizontalAdvance(header_text)
        except AttributeError:
            header_width = font_metrics.width(header_text)
        max_width = max(max_width, header_width)
        
        # Check all possible GSV values from the model data
        gsv_data = self.gsv_model.get_gsv_data()
        primary_levels = self.gsv_model.get_primary_gsv_levels()
        
        def check_data_width(data, level_index=0):
            nonlocal max_width
            if level_index >= len(primary_levels):
                return
            
            level_name = primary_levels[level_index]
            if level_name in data:
                level_data = data[level_name]
                if isinstance(level_data, dict):
                    for key in level_data.keys():
                        try:
                            text_width = font_metrics.horizontalAdvance(str(key))
                        except AttributeError:
                            text_width = font_metrics.width(str(key))
                        
                        # Add indentation using constant
                        indented_width = text_width + (level_index * GSVDefaults.PRIMARY_COLUMN_INDENTATION)
                        max_width = max(max_width, indented_width)
                        
                        # Recursively check children
                        check_data_width(level_data[key], level_index + 1)
        
        check_data_width(gsv_data)
        
        # Add padding using constant
        final_width = max_width + GSVDefaults.PRIMARY_COLUMN_PADDING
        
        # Ensure reasonable bounds using constants
        return max(GSVDefaults.PRIMARY_COLUMN_MIN_WIDTH, min(final_width, GSVDefaults.PRIMARY_COLUMN_MAX_WIDTH))
    
    def _calculate_secondary_column_width(self):
        """Calculate the optimal width for secondary GSV columns.
        
        This method finds the widest GSV value (not the grouped header names)
        across all secondary columns, adds minimal padding for the checkbox,
        and returns a uniform width that all secondary columns will use.
        """
        font = self.gsvs_tree.font()
        font_metrics = QtGui.QFontMetrics(font)
        max_width = 0
        longest_value = ""
        
        # Only check the actual GSV values (second row headers), not the grouped headers
        secondary_gsv_data = self.gsv_model.get_secondary_gsv_data()
        all_values = []
        for values in secondary_gsv_data.values():
            all_values.extend(values)
        
        # Find the longest GSV value (e.g., "Full", "Proxy", "EXR", "MOV", "DWAA")
        for value in all_values:
            value_str = str(value)
            try:
                value_width = font_metrics.horizontalAdvance(value_str)
            except AttributeError:
                value_width = font_metrics.width(value_str)
            
            if value_width > max_width:
                max_width = value_width
                longest_value = value_str
        
        # Calculate width based on content with padding from constants
        if max_width > 0:
            content_based_width = max_width + GSVDefaults.SECONDARY_COLUMN_PADDING
        else:
            # Fallback: use minimum width from constants
            content_based_width = GSVDefaults.SECONDARY_COLUMN_MIN_WIDTH
        
        # Ensure bounds using constants
        final_width = max(GSVDefaults.SECONDARY_COLUMN_MIN_WIDTH, min(content_based_width, GSVDefaults.SECONDARY_COLUMN_MAX_WIDTH))
        
        return final_width
    
    def _on_primary_gsv_text_changed(self, text):
        """Handle primary GSV text changes."""
        self.gsv_model.set_primary_gsv_text(text)
    
    def _on_secondary_gsv_text_changed(self, text):
        """Handle secondary GSV text changes."""
        self.gsv_model.set_secondary_gsv_text(text)
    
    def _on_hierarchy_changed(self):
        """Handle hierarchy changes from the model."""
        # Use event-based debouncing to avoid updating on every keystroke
        # This queues the update to happen after current input processing
        self._schedule_hierarchy_update()
    
    def _schedule_hierarchy_update(self):
        """Schedule hierarchy update via event queue with debouncing."""
        # Cancel any pending update
        if hasattr(self, '_hierarchy_update_scheduled') and self._hierarchy_update_scheduled:
            return
        
        # Mark as scheduled and queue the update
        self._hierarchy_update_scheduled = True
        QtCore.QTimer.singleShot(0, self._on_hierarchy_update_ready)

    def _on_hierarchy_update_ready(self):
        """Handle hierarchy update ready event."""
        try:
            # Reset scheduling flag
            self._hierarchy_update_scheduled = False
            
            # Perform the actual hierarchy refresh
            self._refresh_hierarchy()
            
        except Exception as e:
            # Reset flag even on error
            self._hierarchy_update_scheduled = False
            logger.error(f"Error in hierarchy update: {e}", exc_info=True)
    
    def _on_selection_changed(self):
        """Handle selection changes from the model."""
        # Update tree widget selection states
        self._update_tree_selection_from_model()
    
    def _on_tree_item_changed(self, item, column):
        """Handle tree item checkbox state changes."""
        if not item:
            return
        
        # Get item metadata
        item_data = item.data(column, QtCore.Qt.UserRole)
        if not item_data:
            return
        
        # Get the item path
        item_path = item_data.get('path', [])
        
        # Get the new check state
        check_state = item.checkState(column)
        checked = check_state == QtCore.Qt.Checked
        
        # Update the model
        self.gsv_model.set_item_selection(item_path, column, checked)
        
        # Handle parent/child updates
        self._update_parent_child_states(item, column, check_state)
    
    def _update_parent_child_states(self, item, column, check_state):
        """Update parent and child states based on item change."""
        # Block signals to prevent recursion
        self.gsvs_tree.blockSignals(True)
        
        try:
            # Update all children
            self._update_children_state(item, column, check_state)
            
            # Update parent state
            self._update_parent_state(item, column)
        finally:
            # Re-enable signals
            self.gsvs_tree.blockSignals(False)
    
    def _update_children_state(self, parent_item, column, check_state):
        """Update all children of an item."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            child.setCheckState(column, check_state)
            # Recursively update grandchildren
            self._update_children_state(child, column, check_state)
    
    def _update_parent_state(self, child_item, column):
        """Update parent state based on children."""
        parent = child_item.parent()
        if not parent:
            return
        
        # Count checked and unchecked children
        total_children = parent.childCount()
        checked_children = 0
        
        for i in range(total_children):
            child = parent.child(i)
            if child.checkState(column) == QtCore.Qt.Checked:
                checked_children += 1
        
        # Set parent state based on children
        if checked_children == 0:
            parent.setCheckState(column, QtCore.Qt.Unchecked)
        elif checked_children == total_children:
            parent.setCheckState(column, QtCore.Qt.Checked)
        else:
            parent.setCheckState(column, QtCore.Qt.PartiallyChecked)
        
        # Recursively update grandparent
        self._update_parent_state(parent, column)
    
    def _update_tree_selection_from_model(self):
        """Update tree widget selection states from the model."""
        # This would be implemented to sync model selection state to UI
        # For now, it's a placeholder
        pass
    
    def _check_all_items(self):
        """Check all items in all columns."""
        self.gsv_model.set_all_selections(True)
        self._set_all_tree_items_check_state(QtCore.Qt.Checked)
    
    def _uncheck_all_items(self):
        """Uncheck all items in all columns."""
        self.gsv_model.set_all_selections(False)
        self._set_all_tree_items_check_state(QtCore.Qt.Unchecked)
    
    def _set_all_tree_items_check_state(self, check_state):
        """Set check state for all items in all columns."""
        self.gsvs_tree.blockSignals(True)
        try:
            # Iterate through all top-level items
            for i in range(self.gsvs_tree.topLevelItemCount()):
                item = self.gsvs_tree.topLevelItem(i)
                self._set_item_and_children_check_state(item, check_state)
        finally:
            self.gsvs_tree.blockSignals(False)
    
    def _set_item_and_children_check_state(self, item, check_state):
        """Recursively set check state for an item and all its children."""
        # Set check state for all columns
        for column in range(self.gsvs_tree.columnCount()):
            item.setCheckState(column, check_state)
        
        # Recursively update children
        for i in range(item.childCount()):
            child = item.child(i)
            self._set_item_and_children_check_state(child, check_state)
    
    def get_gsv_model(self):
        """Get the GSV model.
        
        Returns:
            GSVHierarchyModel: The GSV model instance
        """
        return self.gsv_model
    
    def get_selected_gsvs(self):
        """Get the currently selected GSV values.
        
        Returns:
            dict: Dictionary with selected GSV data
        """
        return self.gsv_model.get_selected_gsvs()