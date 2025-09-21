# Vogue Manager - Version Management Features

## Overview

Vogue Manager now includes a comprehensive version management system with DCC (Digital Content Creation) application integration, similar to professional VFX pipeline tools like Prism. This system allows you to create, manage, and work with versions of assets and shots using various DCC applications.

## Key Features

### 🎨 DCC Application Integration
- **Auto-detection** of installed DCC applications (Maya, Blender, Houdini, Nuke, etc.)
- **Maya Bridge** with advanced workfile management and scene operations
- **Thumbnail generation** for DCC files with app-specific rendering
- **Workfile templates** for consistent naming conventions

### 📋 Professional Version Manager UI
- **Entity-based version management** (Assets and Shots)
- **Context menus** for right-click version creation
- **Status tracking** (WIP, Review, Approved, Published)
- **Version comparison** and history viewing
- **Professional table interface** with sorting and filtering

### 🔧 Version Actions
- **Open with DCC app** - Launch the appropriate DCC application with the version
- **Copy version** - Copy path to clipboard or duplicate the file
- **Delete version** - Remove version and associated files
- **Thumbnail preview** - Visual representation of each version

### 🎯 Task-Based Workflow
- **Task assignment** for each version (modeling, animation, lighting, etc.)
- **Department organization** with color-coded status
- **User tracking** and comment system
- **Date and time stamps** for all operations

## Supported DCC Applications

| Application | File Extensions | Status | Features |
|-------------|----------------|--------|----------|
| **Maya** | .ma, .mb | ✅ Full Support | Workfile creation, thumbnail generation, scene info |
| **Blender** | .blend | ✅ Basic Support | File detection, thumbnail generation |
| **Houdini** | .hip, .hipnc | ✅ Basic Support | File detection, thumbnail generation |
| **Nuke** | .nk | ✅ Basic Support | File detection, thumbnail generation |
| **3ds Max** | .max | ✅ Basic Support | File detection, thumbnail generation |
| **Cinema 4D** | .c4d | ✅ Basic Support | File detection, thumbnail generation |

## Usage Guide

### 1. Creating Versions

#### Method 1: Context Menu
1. Select an asset or shot in the left panel
2. Right-click in the version table
3. Choose "Create Version with..." → Select DCC app
4. Fill in the version details dialog
5. Click "Create Version"

#### Method 2: Action Buttons
1. Select an asset or shot
2. Click "Publish" button in the Actions section
3. Choose DCC app and fill details
4. Create version

### 2. Managing Versions

#### Viewing Versions
- Select any asset or shot to view its versions
- Versions are displayed in a professional table format
- Each version shows: Version number, User, Date, Comment, Status, Path
- DCC app icons are displayed for easy identification

#### Version Actions
- **Open**: Double-click or use "Open" button to launch with DCC app
- **Copy**: Right-click → "Copy Version" for path or file duplication
- **Delete**: Right-click → "Delete Version" to remove permanently

#### Status Management
- **WIP** (Work In Progress) - Yellow background
- **Review** - Blue background  
- **Approved** - Green background
- **Published** - Gray background

### 3. DCC App Integration

#### Maya Integration
The Maya bridge provides advanced features:
- **Workfile creation** with proper project setup
- **Scene metadata** storage for pipeline integration
- **Thumbnail generation** using Maya's playblast system
- **Scene validation** and info extraction

#### Other DCC Apps
Basic integration includes:
- **File detection** and validation
- **Thumbnail generation** (placeholder or app-specific)
- **Launch capabilities** with proper project context

## File Structure

```
Project/
├── workfiles/           # DCC workfiles
│   ├── AssetName/
│   │   └── task_name/
│   │       ├── AssetName_task_name_v001.ma
│   │       ├── AssetName_task_name_v002.ma
│   │       └── ...
├── versions/            # Published versions
│   ├── AssetName/
│   │   ├── v001/
│   │   ├── v002/
│   │   └── ...
└── thumbnails/          # Version thumbnails
    └── versions/
        ├── AssetName_task_name_v001_thumb.png
        ├── AssetName_task_name_v002_thumb.png
        └── ...
```

## Technical Implementation

### Core Components

1. **DCCManager** (`src/vogue_core/dcc_integration.py`)
   - Manages DCC application detection and integration
   - Handles workfile creation and thumbnail generation
   - Provides unified interface for all DCC apps

2. **MayaBridge** (`src/vogue_maya/maya_bridge.py`)
   - Specialized Maya integration
   - Advanced workfile management
   - Scene metadata and validation

3. **VersionManager UI** (`src/vogue_app/ui.py`)
   - Professional version management interface
   - Context menus and action handling
   - Real-time updates and synchronization

4. **Enhanced Version Model** (`src/vogue_core/models.py`)
   - Extended Version class with DCC support
   - Status tracking and metadata
   - Thumbnail and workfile path management

### Key Features Implementation

#### Auto-Detection
```python
# Automatically detects installed DCC applications
dcc_manager = DCCManager()
apps = dcc_manager.list_apps()
```

#### Version Creation
```python
# Create version with DCC app
version = manager.create_dcc_version(
    entity_key="Character_Hero",
    dcc_app="maya",
    task_name="modeling",
    user="Artist",
    comment="Initial model"
)
```

#### Thumbnail Generation
```python
# Generate thumbnail for DCC file
success = dcc_manager.generate_thumbnail(
    file_path="workfile.ma",
    output_path="thumbnail.png",
    size=(256, 256)
)
```

## Testing

Run the test script to verify functionality:

```bash
python test_version_management.py
```

This will:
1. Test DCC application detection
2. Create a test project with assets
3. Generate versions using DCC apps
4. Test version management features
5. Verify DCC app launching

## Future Enhancements

### Planned Features
- **Advanced Maya integration** with MEL/Python scripting
- **Blender bridge** with Python API integration
- **Houdini bridge** with HScript/Python support
- **Version comparison** tools
- **Batch operations** for multiple versions
- **Render management** integration
- **Pipeline validation** rules

### Extensibility
The system is designed to be easily extensible:
- Add new DCC apps by extending the DCCApp class
- Create custom bridges for specialized workflows
- Implement custom thumbnail generation
- Add validation rules and pipeline checks

## Troubleshooting

### Common Issues

1. **DCC apps not detected**
   - Ensure DCC applications are properly installed
   - Check executable paths in DCCManager
   - Verify file permissions

2. **Thumbnail generation fails**
   - Check DCC app availability
   - Verify file paths and permissions
   - Check Maya Python installation for Maya files

3. **Version creation errors**
   - Ensure project is loaded
   - Check file system permissions
   - Verify DCC app integration

### Debug Mode
Enable debug logging to troubleshoot issues:

```python
from vogue_core.logging_utils import setup_logging
setup_logging(level="DEBUG")
```

## Conclusion

The Vogue Manager version management system provides a professional-grade solution for managing digital content across multiple DCC applications. With its intuitive interface, powerful DCC integration, and extensible architecture, it brings enterprise-level pipeline management to your creative workflow.

The system is designed to grow with your needs, supporting everything from small indie projects to large-scale VFX productions. Whether you're working with Maya, Blender, or other DCC applications, Vogue Manager provides the tools you need to maintain version control and streamline your creative pipeline.
