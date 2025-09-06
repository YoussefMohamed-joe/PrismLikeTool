# Vogue Manager - Complete Prism Pipeline Clone

A complete clone of the [Prism Pipeline](https://github.com/PrismPipeline/Prism) production management system with a shared backend, PyQt6 desktop application, and Maya integration. Built from scratch without using Prism or external databases, but with all the features and functionality of the real Prism Pipeline.

## 🎯 Features

### Complete Prism Pipeline Interface
- **Project Browser**: Left panel with assets and shots organized by type/sequence
- **Version Manager**: Center panel with version table, publish controls, and entity info
- **Pipeline Panel**: Right panel with pipeline status, tools, and software integration
- **Recent Projects**: Dedicated dialog for project selection and management
- **Log Dock**: Collapsible log panel with filtering and clearing
- **Status Bar**: Project status, progress indicator, user info, and version

### Project Management
- **New Project Creation**: Full project setup with departments, tasks, and settings
- **Project Browsing**: Recent projects dialog with project information
- **Project Settings**: FPS, resolution, departments, and custom configurations
- **Project Import/Export**: Import and export projects to/from external formats
- **Project Validation**: Validate project integrity and structure
- **Project Optimization**: Optimize project for better performance
- **Auto-save**: Configurable auto-save functionality

### Asset Management
- **Asset Creation**: Add assets with type, description, and metadata
- **Asset Organization**: Group by type (Characters, Props, Environments, etc.)
- **Asset Metadata**: Tags, artist, LOD level, rigged/animated flags
- **Asset Import**: Import assets from external sources

### Shot Management
- **Shot Creation**: Add shots with sequence, frame range, and metadata
- **Shot Organization**: Group by sequence with version tracking
- **Shot Metadata**: Director, tags, frame range, FPS settings
- **Shot Import**: Import shots from external sources

### Version Control
- **Publish System**: Complete version publishing with comments and options
- **Version Management**: View, open, copy, export, and delete versions
- **Auto-increment**: Automatic version numbering
- **Thumbnail Generation**: Automatic thumbnail creation for versions
- **File Management**: Copy files during publish, export versions

### Image & Thumbnail Support
- **Image Preview**: Dedicated dialog for viewing images and thumbnails
- **Thumbnail Generation**: Automatic thumbnail creation from image files
- **Multiple Formats**: Support for JPG, PNG, BMP, TGA, EXR formats
- **External Viewer**: Open images in system default viewer

### Prism Pipeline Features
- **Pipeline Validation**: Validate project structure and integrity
- **Project Optimization**: Optimize projects for better performance
- **Software Integration**: Launch Maya, Houdini, Blender with Prism integration
- **Pipeline Status**: Real-time pipeline status and active tools monitoring
- **Quick Actions**: One-click access to common pipeline operations

### Settings & Preferences
- **General Settings**: Auto-save, startup behavior, user preferences
- **Project Settings**: Recent projects management, cleanup options
- **Appearance**: Theme selection, font size customization
- **Recent Projects**: Full recent projects management with removal

### Backend Features
- **JSON Database**: Atomic writes with backup files
- **Project Layout**: Standard production folder structure
- **Schema Validation**: JSON schema validation for data integrity
- **Filesystem Scanning**: Automatic asset and shot discovery
- **Settings Management**: Global and user-specific settings
- **Logging System**: Structured logging with file and UI output

## 🏗️ Architecture

### Monorepo Structure
```
vogue_manager/
├── src/
│   ├── vogue_core/          # Shared backend
│   │   ├── models.py        # Data models (Project, Asset, Shot, Version)
│   │   ├── manager.py       # Core ProjectManager
│   │   ├── schema.py        # JSON schema validation
│   │   ├── fs.py           # Filesystem utilities
│   │   ├── settings.py     # Settings management
│   │   ├── logging_utils.py # Logging system
│   │   ├── publish.py      # Publishing hooks
│   │   ├── thumbnails.py   # Thumbnail generation
│   │   └── api_local.py    # Optional HTTP API
│   ├── vogue_app/          # Desktop application
│   │   ├── ui.py           # Main Prism-like UI
│   │   ├── dialogs.py      # All dialog windows
│   │   ├── controller.py   # Application controller
│   │   ├── colors.py       # Color palette
│   │   ├── qss.py          # QSS styling
│   │   └── main.py         # Application entry point
│   └── vogue_maya/         # Maya integration
│       ├── tool.py         # Maya tool entry point
│       ├── dock.py         # Dockable widget
│       └── maya_bridge.py  # Maya command wrappers
├── tests/                  # Unit tests
├── examples/               # Example projects
└── scripts/               # Helper scripts
```

### Project Layout
```
ProjectName/
├── 00_Pipeline/
│   └── pipeline.json       # Project data (single source of truth)
├── Assets/
│   ├── Characters/
│   ├── Props/
│   └── Environments/
├── Shots/
│   ├── SEQ001/
│   └── SEQ002/
├── Renders/
├── Cache/
└── Exports/
```

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd vogue_manager

# Install dependencies
pip install -r requirements.txt

# Run the desktop application
python -m vogue_app.main
```

### Creating Your First Project
1. Launch Vogue Manager
2. Click "Browse Project..." or use File > Project > New Project
3. Fill in project details (name, path, description)
4. Configure project settings (FPS, resolution, departments)
5. Click "OK" to create the project

### Adding Assets
1. Select the project in the left panel
2. Click "Add Asset" button
3. Fill in asset details (name, type, description)
4. Configure metadata (tags, artist, LOD level)
5. Click "OK" to create the asset

### Publishing Versions
1. Select an asset or shot in the left panel
2. Click "Publish" button
3. Add files to publish, set version comment
4. Configure publish options (thumbnail, auto-increment)
5. Click "Publish" to create the version

## 🎨 UI Features

### Prism-like Interface
- **Dark Theme**: Professional dark color scheme
- **Split Panels**: Project browser (left) and version manager (right)
- **Tree Views**: Hierarchical display of assets and shots
- **Version Table**: Detailed version information with actions
- **Context Menus**: Right-click actions for all items
- **Keyboard Shortcuts**: Full keyboard navigation support

### Dialogs
- **New Project**: Complete project creation wizard
- **Recent Projects**: Project selection with information
- **Asset/Shot Creation**: Detailed creation dialogs
- **Publish Dialog**: Version publishing with options
- **Image Preview**: Full-featured image viewer
- **Settings**: Comprehensive settings management

### Status & Logging
- **Status Bar**: Project status, user info, version
- **Progress Bar**: Long-running operation feedback
- **Log Panel**: Collapsible log with filtering
- **Message System**: Toast notifications for actions

## 🔧 Configuration

### Project Settings
- **Frame Rate**: 12-120 FPS
- **Resolution**: HD, 2K, 4K, or custom
- **Departments**: Customizable with colors and tasks
- **Metadata**: Flexible metadata system

### Application Settings
- **Auto-save**: Configurable interval
- **Startup**: Load last project option
- **Theme**: Dark/Light/Auto
- **Font Size**: 8-24pt range

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_project_layout.py
pytest tests/test_assets.py
pytest tests/test_shots.py
pytest tests/test_versions.py
```

## 📚 API Reference

### Core Models
- `Project`: Main project container
- `Asset`: 3D asset with versions
- `Shot`: Animation shot with versions
- `Version`: Published version with metadata
- `Department`: Project department with tasks
- `Task`: Individual department task

### Key Classes
- `ProjectManager`: Core project management
- `VogueController`: Desktop application controller
- `PrismMainWindow`: Main UI window
- `RecentProjectsDialog`: Project selection dialog
- `PublishDialog`: Version publishing dialog

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by Prism pipeline management
- Built with PyQt6 for modern UI
- Uses JSON for lightweight data storage
- Designed for production pipeline workflows

---

**Vogue Manager** - Your complete production pipeline solution! 🎬✨