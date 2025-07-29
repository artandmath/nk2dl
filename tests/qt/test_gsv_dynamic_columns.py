#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for GSV functionality with dynamic column sizing.

This test demonstrates:
1. Dynamic column width calculation based on actual content
2. Proper checkbox behavior (built-in for primary, centered for secondary)
3. GSV hierarchy tree building
4. Column sizing optimization

Run this script in Nuke terminal mode using --tg flag.
"""

import sys
import os
import time

# Path setup for Nuke testing
nk2dl_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, nk2dl_path)

# Nuke-compatible PySide imports
try:
    import nuke
    if nuke.NUKE_VERSION_MAJOR >= 16:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    else:
        from PySide2 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide2"
    NUKE_AVAILABLE = True
except ImportError:
    NUKE_AVAILABLE = False
    # Fallback for testing without Nuke
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        PYSIDE_VERSION = "PySide6"
    except ImportError:
        try:
            from PySide2 import QtWidgets, QtCore, QtGui
            PYSIDE_VERSION = "PySide2"
        except ImportError:
            print("Neither PySide6 nor PySide2 is available")
            sys.exit(1)

from nk2dl.gui.panel.models import GSVHierarchyModel
from nk2dl.gui.panel.views import GSVView
from nk2dl.gui.panel.widgets import GroupedHeaderView
from nk2dl.gui.panel.delegates import CenteredCheckboxDelegate


class GSVTestWindow(QtWidgets.QMainWindow):
    """Test window for GSV functionality."""
    
    def __init__(self):
        super().__init__()
        nuke_info = f" - Nuke {nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}" if NUKE_AVAILABLE else ""
        self.setWindowTitle(f"GSV Dynamic Columns Test - {PYSIDE_VERSION}{nuke_info}")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Add title
        title = QtWidgets.QLabel("GSV Dynamic Column Sizing Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        
        # Add description
        description = QtWidgets.QLabel(
            "This test demonstrates dynamic column sizing where all secondary columns "
            "are sized to fit the widest header or value, making the interface compact "
            "while maintaining consistency."
        )
        description.setWordWrap(True)
        description.setStyleSheet("margin: 5px 10px; color: #666;")
        layout.addWidget(description)
        
        # Create test scenarios section
        self._create_test_scenarios(layout)
        
        # Create GSV model and view
        self.gsv_model = GSVHierarchyModel()
        self.gsv_view = GSVView(self.gsv_model)
        
        # Load test data
        self._load_test_data()
        
        # Add GSV view to layout
        layout.addWidget(self.gsv_view)
        
        # Add status bar
        self.statusBar().showMessage("Ready - Try different test scenarios to see dynamic column sizing")
    
    def _create_test_scenarios(self, layout):
        """Create test scenario buttons."""
        scenarios_group = QtWidgets.QGroupBox("Test Scenarios")
        scenarios_layout = QtWidgets.QHBoxLayout()
        scenarios_group.setLayout(scenarios_layout)
        
        # Scenario 1: Short headers
        short_btn = QtWidgets.QPushButton("Short Headers (EXR, MOV)")
        short_btn.clicked.connect(self._load_short_headers_scenario)
        scenarios_layout.addWidget(short_btn)
        
        # Scenario 2: Long headers
        long_btn = QtWidgets.QPushButton("Long Headers (Resolution, Format)")
        long_btn.clicked.connect(self._load_long_headers_scenario)
        scenarios_layout.addWidget(long_btn)
        
        # Scenario 3: Mixed length
        mixed_btn = QtWidgets.QPushButton("Mixed Length Headers")
        mixed_btn.clicked.connect(self._load_mixed_headers_scenario)
        scenarios_layout.addWidget(mixed_btn)
        
        # Scenario 4: Many columns
        many_btn = QtWidgets.QPushButton("Many Columns")
        many_btn.clicked.connect(self._load_many_columns_scenario)
        scenarios_layout.addWidget(many_btn)
        
        scenarios_layout.addStretch()
        
        # Force refresh button
        refresh_btn = QtWidgets.QPushButton("Force Column Refresh")
        refresh_btn.clicked.connect(self._force_column_refresh)
        scenarios_layout.addWidget(refresh_btn)
        
        # Info button
        info_btn = QtWidgets.QPushButton("Column Width Info")
        info_btn.clicked.connect(self._show_column_info)
        scenarios_layout.addWidget(info_btn)
        
        layout.addWidget(scenarios_group)
    
    def _load_test_data(self):
        """Load initial test data."""
        self._load_long_headers_scenario()
    
    def _load_short_headers_scenario(self):
        """Load scenario with short headers."""
        self.gsv_model.set_primary_gsv_text("Sequence, Shot")
        self.gsv_model.set_secondary_gsv_text("EXR, MOV")
        
        # Set test GSV data
        test_data = {
            "Sequence": {
                "seq010": {
                    "Shot": {
                        "sh001": {},
                        "sh002": {},
                        "sh003": {}
                    }
                },
                "seq020": {
                    "Shot": {
                        "sh010": {},
                        "sh011": {}
                    }
                }
            }
        }
        
        secondary_data = {
            "EXR": ["Full", "Proxy"],
            "MOV": ["Full", "Proxy"]
        }
        
        self.gsv_model.set_gsv_data(test_data)
        self.gsv_model.set_secondary_gsv_data(secondary_data)
        self.gsv_view._refresh_hierarchy()
        
        # Force column width recalculation
        self._force_column_refresh()
        
        self.statusBar().showMessage("Loaded: Short Headers - Columns should be compact")
    
    def _load_long_headers_scenario(self):
        """Load scenario with long headers."""
        self.gsv_model.set_primary_gsv_text("Sequence, Shotcode")
        self.gsv_model.set_secondary_gsv_text("Resolution, Format")
        
        # Set test GSV data
        test_data = {
            "Sequence": {
                "seq010": {
                    "Shotcode": {
                        "sh001": {},
                        "sh002": {},
                        "sh003": {}
                    }
                },
                "seq020": {
                    "Shotcode": {
                        "sh010": {},
                        "sh011": {},
                        "sh012": {}
                    }
                },
                "seq030": {
                    "Shotcode": {
                        "sh020": {},
                        "sh021": {}
                    }
                }
            }
        }
        
        secondary_data = {
            "Resolution": ["Full", "Proxy"],
            "Format": ["EXR", "MOV", "DWAA"]
        }
        
        self.gsv_model.set_gsv_data(test_data)
        self.gsv_model.set_secondary_gsv_data(secondary_data)
        self.gsv_view._refresh_hierarchy()
        
        # Force column width recalculation
        self._force_column_refresh()
        
        self.statusBar().showMessage("Loaded: Long Headers - Columns sized to fit 'Resolution'")
    
    def _load_mixed_headers_scenario(self):
        """Load scenario with mixed length headers."""
        self.gsv_model.set_primary_gsv_text("Sequence, Shot")
        self.gsv_model.set_secondary_gsv_text("Res, Format, Quality")
        
        # Set test GSV data
        test_data = {
            "Sequence": {
                "seq010": {
                    "Shot": {
                        "sh001": {},
                        "sh002": {}
                    }
                },
                "seq020": {
                    "Shot": {
                        "sh010": {},
                        "sh011": {}
                    }
                }
            }
        }
        
        secondary_data = {
            "Res": ["Full", "Proxy"],
            "Format": ["EXR", "MOV"],
            "Quality": ["High", "Medium", "Low"]
        }
        
        self.gsv_model.set_gsv_data(test_data)
        self.gsv_model.set_secondary_gsv_data(secondary_data)
        self.gsv_view._refresh_hierarchy()
        
        # Force column width recalculation
        self._force_column_refresh()
        
        self.statusBar().showMessage("Loaded: Mixed Headers - All columns sized to fit 'Quality'")
    
    def _load_many_columns_scenario(self):
        """Load scenario with many columns."""
        self.gsv_model.set_primary_gsv_text("Seq, Shot")
        self.gsv_model.set_secondary_gsv_text("Res, Fmt, Qual, Comp, AOV, Ver")
        
        # Set test GSV data
        test_data = {
            "Seq": {
                "s010": {
                    "Shot": {
                        "001": {},
                        "002": {}
                    }
                },
                "s020": {
                    "Shot": {
                        "010": {},
                        "011": {}
                    }
                }
            }
        }
        
        secondary_data = {
            "Res": ["F", "P"],
            "Fmt": ["EXR", "MOV"],
            "Qual": ["Hi", "Lo"],
            "Comp": ["Y", "N"],
            "AOV": ["Beauty", "Spec"],
            "Ver": ["v1", "v2"]
        }
        
        self.gsv_model.set_gsv_data(test_data)
        self.gsv_model.set_secondary_gsv_data(secondary_data)
        self.gsv_view._refresh_hierarchy()
        
        # Force column width recalculation
        self._force_column_refresh()
        
        self.statusBar().showMessage("Loaded: Many Columns - Compact layout with uniform sizing")
    
    def _force_column_refresh(self):
        """Force a refresh of column widths."""
        if hasattr(self.gsv_view, 'gsvs_tree') and hasattr(self.gsv_view, '_setup_column_properties'):
            # Force recalculation of column properties
            self.gsv_view._setup_column_properties()
            
            # Also force a repaint
            self.gsv_view.gsvs_tree.update()
            
            # Process events to ensure the update takes effect
            QtWidgets.QApplication.processEvents()
    
    def _show_column_info(self):
        """Show information about current column widths."""
        if not hasattr(self.gsv_view, 'gsvs_tree'):
            QtWidgets.QMessageBox.information(self, "Info", "No GSV tree loaded yet.")
            return
        
        tree = self.gsv_view.gsvs_tree
        header = tree.header()
        
        info_text = "Current Column Widths:\n\n"
        
        for i in range(tree.columnCount()):
            width = header.sectionSize(i)
            header_text = tree.headerItem().text(i) if tree.headerItem() else f"Column {i}"
            info_text += f"{header_text}: {width}px\n"
        
        # Calculate secondary column width
        if hasattr(self.gsv_view, '_calculate_secondary_column_width'):
            calculated_width = self.gsv_view._calculate_secondary_column_width()
            info_text += f"\nCalculated secondary width: {calculated_width}px"
        
        # Show font metrics info
        font = tree.font()
        font_metrics = QtGui.QFontMetrics(font)
        
        info_text += f"\n\nFont Metrics:"
        info_text += f"\nFont: {font.family()}, {font.pointSize()}pt"
        
        # Sample text widths
        sample_texts = ["Resolution", "Format", "EXR", "MOV", "Full", "Proxy"]
        info_text += f"\n\nSample Text Widths:"
        for text in sample_texts:
            try:
                width = font_metrics.horizontalAdvance(text)
            except AttributeError:
                width = font_metrics.width(text)
            info_text += f"\n'{text}': {width}px"
        
        QtWidgets.QMessageBox.information(self, "Column Width Information", info_text)


def main():
    """Run the GSV test application."""
    # Create or get existing QApplication
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("GSV Dynamic Columns Test")
    app.setApplicationVersion("1.0")
    
    # Create and show the test window
    window = GSVTestWindow()
    window.show()
    
    # Keep alive for Nuke terminal mode - prevent garbage collection
    globals()['_test_window'] = window
    
    if NUKE_AVAILABLE:
        # Keep responsive in Nuke terminal mode
        try:
            print("GSV Test Window opened. Close the window to exit.")
            while True:
                QtWidgets.QApplication.processEvents()
                time.sleep(0.1)
                if not window.isVisible():
                    break
        except KeyboardInterrupt:
            print("Test interrupted by user.")
    else:
        # Standard Qt application execution
        if hasattr(app, 'exec'):
            return app.exec()
        else:
            return app.exec_()
    
    return window


if __name__ == "__main__":
    main() 