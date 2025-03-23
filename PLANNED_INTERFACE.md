# Nuke Submitter for Thinkbox Deadline - Interface Design Plan

## Overview
This document outlines the design approach for both the Command Line Interface (CLI) and Nuke User Interface for the Deadline submission tool. The goal is to create intuitive, efficient interfaces that cater to both power users (CLI) and artists (Nuke UI).

## Command Line Interface (CLI) Design

### Core Commands
```bash
# Basic submission
nk2dl submit <script_path> [options]

# Preview submission without actually submitting
nk2dl preview <script_path> [options]

# Configure default settings
nk2dl config [get|set] <key> [value]
```

### Key Features
1. **Script Analysis**
   - Auto-detection of write nodes
   - Frame range analysis
   - Dependency detection
   - Render settings extraction

2. **Job Configuration**
   - Frame range specification
   - Chunk size control
   - Priority settings
   - Machine requirements
   - Pool/group selection

3. **Output Options**
   - JSON/YAML output for automation
   - Verbose logging options
   - Progress indicators
   - Error reporting

### Example Usage
```bash
# Basic submission
nk2dl submit comp_v001.nk --priority 75 --chunk 10

# Preview with custom settings
nk2dl preview comp_v001.nk --frames 1-100 --pool render

# Get submission details in JSON
nk2dl submit comp_v001.nk --output json
```

## Nuke User Interface Design

### Main Window Layout
TBD

### Key Features
1. **Write Node Management**
   - Auto-detection of write nodes
   - Batch selection/deselection
   - Format validation
   - Path verification

2. **Frame Range Controls**
   - Script frame range detection
   - Custom range input
   - Frame step control
   - Preview frame selection

3. **Submission Settings**
   - Priority slider
   - Chunk size input
   - Pool/group dropdowns
   - Machine requirements
   - Dependencies

4. **Preview Functionality**
   - Job cost estimation
   - Timeline visualization
   - Resource requirements
   - Validation results

### Integration Points
1. **Nuke Menu Integration**
   - Add to Nuke's main menu

2. **Script Integration**
   - Save submission settings with script
   - Save submission settings for individual write nodes
   - Load previous settings

## Shared Features

### Configuration Management
- User-specific settings
- Project defaults
- Template support

### Validation
- Script validation
- Path verification
- Frame range checks
- Resource availability

### Error Handling
- Clear error messages
- Recovery suggestions
- Logging system
- Debug mode

## Implementation Priorities
1. Core CLI functionality
2. Basic Nuke UI
3. Write node integration
4. Preview system
5. Advanced features
6. Polish and optimization

## Success Metrics
1. Submission time < 2 seconds
2. Zero crashes
3. Intuitive workflow
4. Clear error messages
5. Efficient resource usage

## Next Steps
1. Create CLI prototype
2. Design UI mockups
3. Implement core functionality
4. Add Nuke integration
5. Test with real scripts
6. Gather user feedback 