#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test to verify display name usage in column width calculations.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from nk2dl.gui.panel.constants import TableColumns

def test_display_names():
    """Test that display names are correctly mapped."""
    print("Testing TableColumns display name mapping:")
    print("=" * 50)
    
    # Test key headers that should have different display names
    test_headers = ["ChunkSize", "TaskTimeout", "NodesFrames", "AutoTimeout", "UseGPU", "GPUId"]
    
    for header in test_headers:
        display_name = TableColumns.HEADER_DISPLAY_NAMES.get(header, header)
        print(f"'{header}' -> '{display_name}'")
        
        # Check if they're different (which they should be for most)
        if header != display_name:
            print(f"  ✓ Display name is different from internal name")
        else:
            print(f"  → Display name same as internal name")
    
    print("\n" + "=" * 50)
    print("All headers and their display names:")
    print("=" * 50)
    
    for header in TableColumns.HEADERS[:10]:  # Show first 10
        display_name = TableColumns.HEADER_DISPLAY_NAMES.get(header, header)
        print(f"{header:15} -> {display_name}")

if __name__ == "__main__":
    test_display_names() 