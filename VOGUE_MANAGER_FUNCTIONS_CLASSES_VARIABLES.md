# Vogue Manager Upgrade: Complete Functions, Classes & Variables Reference

## Table of Contents
1. [Core Data Models](#core-data-models)
2. [Database Layer](#database-layer)
3. [Task Management](#task-management)
4. [Version Management](#version-management)
5. [UI Components](#ui-components)
6. [DCC Integration](#dcc-integration)
7. [Plugin System](#plugin-system)
8. [Utility Classes](#utility-classes)
9. [Configuration System](#configuration-system)
10. [Event System](#event-system)

## Core Data Models

### BaseEntity Class
**Purpose**: Base class for all entities in the system
**Location**: `src/vogue_core/models.py`

```python
@dataclass
class BaseEntity:
    # Core Properties
    id: str                    # UUID identifier
    name: str                  # Entity name
    label: str                 # Display label
    created_at: datetime       # Creation timestamp
    updated_at: datetime       # Last update timestamp
    created_by: str            # Creator user ID
    updated_by: str            # Last updater user ID
    status: str                # Entity status
    tags: List[str]            # Associated tags
    attributes: Dict[str, Any] # Custom attributes
    
    # Methods
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for serialization"""
        
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load entity from dictionary"""
        
    def validate(self) -> List[str]:
        """Validate entity data, return list of errors"""
        
    def update_attributes(self, attrs: Dict[str, Any]) -> None:
        """Update custom attributes"""
        
    def add_tag(self, tag: str) -> None:
        """Add tag to entity"""
        
    def remove_tag(self, tag: str) -> None:
        """Remove tag from entity"""
        
    def has_tag(self, tag: str) -> bool:
        """Check if entity has specific tag"""
        
    def get_attribute(self, key: str, default=None):
        """Get custom attribute value"""
        
    def set_attribute(self, key: str, value: Any) -> None:
        """Set custom attribute value"""
```

### Folder Class
**Purpose**: Represents folders in project hierarchy
**Location**: `src/vogue_core/models.py`

```python
@dataclass
class Folder(BaseEntity):
    # Properties
    folder_type: str           # "Asset", "Shot", "Sequence", "Episode"
    parent_id: Optional[str]   # Parent folder ID
    path: str                  # Folder path
    children: List[str]        # Child folder IDs
    tasks: List[str]           # Task IDs in this folder
    products: List[str]        # Product IDs in this folder
    
    # Methods
    def get_children(self) -> List['Folder']:
        """Get child folders"""
        
    def get_tasks(self) -> List['Task']:
        """Get tasks in this folder"""
        
    def get_products(self) -> List['Product']:
        """Get products in this folder"""
        
    def add_child(self, child: 'Folder') -> None:
        """Add child folder"""
        
    def remove_child(self, child_id: str) -> None:
        """Remove child folder"""
        
    def get_path_string(self) -> str:
        """Get full path as string"""
        
    def get_depth(self) -> int:
        """Get folder depth in hierarchy"""
        
    def is_ancestor_of(self, folder_id: str) -> bool:
        """Check if this folder is ancestor of another"""
        
    def get_all_descendants(self) -> List['Folder']:
        """Get all descendant folders"""
```

### Task Class
**Purpose**: Represents tasks in the pipeline
**Location**: `src/vogue_core/models.py`

```python
@dataclass
class Task(BaseEntity):
    # Properties
    task_type: str             # "Modeling", "Animation", "Lighting", etc.
    assignee: Optional[str]    # Assigned user ID
    status: str                # "Not Started", "In Progress", "Done", "Blocked"
    priority: int              # 1-5 priority level
    due_date: Optional[datetime] # Due date
    folder_id: str             # Parent folder ID
    dependencies: List[str]    # Task IDs this task depends on
    estimated_hours: Optional[float] # Estimated hours
    actual_hours: Optional[float]   # Actual hours worked
    
    # Methods
    def assign_to(self, user_id: str) -> None:
        """Assign task to user"""
        
    def unassign(self) -> None:
        """Unassign task from user"""
        
    def update_status(self, status: str) -> None:
        """Update task status"""
        
    def add_dependency(self, task_id: str) -> None:
        """Add task dependency"""
        
    def remove_dependency(self, task_id: str) -> None:
        """Remove task dependency"""
        
    def get_dependencies(self) -> List['Task']:
        """Get dependency tasks"""
        
    def get_dependents(self) -> List['Task']:
        """Get tasks that depend on this one"""
        
    def is_blocked(self) -> bool:
        """Check if task is blocked by dependencies"""
        
    def can_start(self) -> bool:
        """Check if task can start (dependencies met)"""
        
    def get_progress_percentage(self) -> float:
        """Get task progress percentage"""
        
    def add_time(self, hours: float) -> None:
        """Add actual hours worked"""
```

### Product Class
**Purpose**: Represents products (assets, shots, etc.)
**Location**: `src/vogue_core/models.py`

```python
@dataclass
class Product(BaseEntity):
    # Properties
    product_type: str          # "Model", "Rig", "Animation", "Render"
    folder_id: str             # Parent folder ID
    status: str                # Product status
    latest_version: Optional[int] # Latest version number
    versions: List[str]        # Version IDs
    
    # Methods
    def get_latest_version(self) -> Optional['Version']:
        """Get latest version"""
        
    def get_versions(self) -> List['Version']:
        """Get all versions"""
        
    def create_version(self, author: str, comment: str = "") -> 'Version':
        """Create new version"""
        
    def get_version(self, version_num: int) -> Optional['Version']:
        """Get specific version"""
        
    def get_version_count(self) -> int:
        """Get total version count"""
        
    def get_published_versions(self) -> List['Version']:
        """Get published versions only"""
        
    def get_draft_versions(self) -> List['Version']:
        """Get draft versions only"""
        
    def archive_old_versions(self, keep_count: int = 5) -> None:
        """Archive old versions, keep specified count"""
```

### Version Class
**Purpose**: Represents versions of products
**Location**: `src/vogue_core/models.py`

```python
@dataclass
class Version(BaseEntity):
    # Properties
    version: int                # Version number
    product_id: str             # Parent product ID
    author: str                 # Author user ID
    comment: str                # Version comment
    status: str                 # "Published", "Draft", "Archived"
    thumbnail_id: Optional[str] # Thumbnail file ID
    representations: List[str]  # Representation IDs
    
    # Methods
    def get_representations(self) -> List['Representation']:
        """Get all representations"""
        
    def add_representation(self, rep: 'Representation') -> None:
        """Add representation"""
        
    def remove_representation(self, rep_id: str) -> None:
        """Remove representation"""
        
    def get_representation(self, name: str) -> Optional['Representation']:
        """Get representation by name"""
        
    def publish(self) -> None:
        """Publish version"""
        
    def archive(self) -> None:
        """Archive version"""
        
    def unpublish(self) -> None:
        """Unpublish version"""
        
    def is_published(self) -> bool:
        """Check if version is published"""
        
    def get_file_count(self) -> int:
        """Get total file count across all representations"""
        
    def get_total_size(self) -> int:
        """Get total size of all files"""
```

### Representation Class
**Purpose**: Represents different formats of a version
**Location**: `src/vogue_core/models.py`

```python
@dataclass
class Representation(BaseEntity):
    # Properties
    name: str                   # Format name ("ma", "mb", "abc", "exr")
    version_id: str             # Parent version ID
    files: List[str]            # File IDs
    attributes: Dict[str, Any]  # Format-specific attributes
    active: bool                # Whether representation is active
    
    # Methods
    def get_files(self) -> List['FileInfo']:
        """Get all files"""
        
    def add_file(self, file_info: 'FileInfo') -> None:
        """Add file"""
        
    def remove_file(self, file_id: str) -> None:
        """Remove file"""
        
    def get_file(self, file_id: str) -> Optional['FileInfo']:
        """Get specific file"""
        
    def activate(self) -> None:
        """Activate representation"""
        
    def deactivate(self) -> None:
        """Deactivate representation"""
        
    def get_file_count(self) -> int:
        """Get file count"""
        
    def get_total_size(self) -> int:
        """Get total size of all files"""
        
    def get_primary_file(self) -> Optional['FileInfo']:
        """Get primary file (first file)"""
```

### FileInfo Class
**Purpose**: Represents individual files
**Location**: `src/vogue_core/models.py`

```python
@dataclass
class FileInfo(BaseEntity):
    # Properties
    name: str                   # File name
    path: str                   # File path
    size: int                   # File size in bytes
    hash: str                   # File hash
    hash_type: str              # Hash algorithm ("md5", "sha256")
    representation_id: str      # Parent representation ID
    mime_type: str              # MIME type
    created_at: datetime        # File creation time
    
    # Methods
    def get_absolute_path(self) -> str:
        """Get absolute file path"""
        
    def exists(self) -> bool:
        """Check if file exists on disk"""
        
    def get_hash(self) -> str:
        """Calculate file hash"""
        
    def verify_hash(self) -> bool:
        """Verify file hash integrity"""
        
    def get_size_formatted(self) -> str:
        """Get formatted file size string"""
        
    def get_extension(self) -> str:
        """Get file extension"""
        
    def is_image(self) -> bool:
        """Check if file is an image"""
        
    def is_video(self) -> bool:
        """Check if file is a video"""
        
    def is_3d_model(self) -> bool:
        """Check if file is a 3D model"""
```

## Database Layer

### DatabaseManager Class
**Purpose**: Manages database connections and operations
**Location**: `src/vogue_core/database.py`

```python
class DatabaseManager:
    # Properties
    db_path: str                # Database file path
    connection: sqlite3.Connection # Database connection
    cursor: sqlite3.Cursor      # Database cursor
    
    # Methods
    def __init__(self, db_path: str):
        """Initialize database manager"""
        
    def connect(self) -> None:
        """Connect to database"""
        
    def disconnect(self) -> None:
        """Disconnect from database"""
        
    def create_tables(self) -> None:
        """Create database tables"""
        
    def drop_tables(self) -> None:
        """Drop all tables"""
        
    def migrate(self, from_version: str, to_version: str) -> None:
        """Run database migration"""
        
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute SQL query"""
        
    def execute_transaction(self, queries: List[tuple]) -> None:
        """Execute multiple queries in transaction"""
        
    def get_table_info(self, table_name: str) -> List[Dict]:
        """Get table information"""
        
    def backup_database(self, backup_path: str) -> None:
        """Backup database"""
        
    def restore_database(self, backup_path: str) -> None:
        """Restore database from backup"""
        
    def optimize_database(self) -> None:
        """Optimize database performance"""
        
    def get_database_size(self) -> int:
        """Get database file size"""
        
    def vacuum_database(self) -> None:
        """Vacuum database to reclaim space"""
```

### EntityRepository Class
**Purpose**: Repository pattern for entity operations
**Location**: `src/vogue_core/repository.py`

```python
class EntityRepository:
    # Properties
    db_manager: DatabaseManager # Database manager instance
    
    # Methods
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository"""
        
    def create(self, entity: BaseEntity) -> str:
        """Create entity in database"""
        
    def read(self, entity_id: str) -> Optional[BaseEntity]:
        """Read entity from database"""
        
    def update(self, entity: BaseEntity) -> None:
        """Update entity in database"""
        
    def delete(self, entity_id: str) -> None:
        """Delete entity from database"""
        
    def find_by_name(self, name: str) -> List[BaseEntity]:
        """Find entities by name"""
        
    def find_by_type(self, entity_type: str) -> List[BaseEntity]:
        """Find entities by type"""
        
    def find_by_status(self, status: str) -> List[BaseEntity]:
        """Find entities by status"""
        
    def find_by_tag(self, tag: str) -> List[BaseEntity]:
        """Find entities by tag"""
        
    def search(self, query: str) -> List[BaseEntity]:
        """Search entities"""
        
    def count(self, entity_type: str = None) -> int:
        """Count entities"""
        
    def exists(self, entity_id: str) -> bool:
        """Check if entity exists"""
        
    def get_children(self, parent_id: str) -> List[BaseEntity]:
        """Get child entities"""
        
    def get_parent(self, entity_id: str) -> Optional[BaseEntity]:
        """Get parent entity"""
```

## Task Management

### TaskManager Class
**Purpose**: Manages task operations
**Location**: `src/vogue_core/task_manager.py`

```python
class TaskManager:
    # Properties
    db_manager: DatabaseManager # Database manager
    repository: EntityRepository # Entity repository
    
    # Methods
    def __init__(self, db_manager: DatabaseManager):
        """Initialize task manager"""
        
    def create_task(self, name: str, task_type: str, folder_id: str) -> Task:
        """Create new task"""
        
    def assign_task(self, task_id: str, user_id: str) -> None:
        """Assign task to user"""
        
    def unassign_task(self, task_id: str) -> None:
        """Unassign task from user"""
        
    def update_task_status(self, task_id: str, status: str) -> None:
        """Update task status"""
        
    def update_task_priority(self, task_id: str, priority: int) -> None:
        """Update task priority"""
        
    def set_task_due_date(self, task_id: str, due_date: datetime) -> None:
        """Set task due date"""
        
    def get_tasks_by_user(self, user_id: str) -> List[Task]:
        """Get tasks assigned to user"""
        
    def get_tasks_by_folder(self, folder_id: str) -> List[Task]:
        """Get tasks in folder"""
        
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """Get tasks by status"""
        
    def get_tasks_by_type(self, task_type: str) -> List[Task]:
        """Get tasks by type"""
        
    def get_overdue_tasks(self) -> List[Task]:
        """Get overdue tasks"""
        
    def get_task_dependencies(self, task_id: str) -> List[Task]:
        """Get task dependencies"""
        
    def add_task_dependency(self, task_id: str, dependency_id: str) -> None:
        """Add task dependency"""
        
    def remove_task_dependency(self, task_id: str, dependency_id: str) -> None:
        """Remove task dependency"""
        
    def get_task_progress(self, task_id: str) -> float:
        """Get task progress percentage"""
        
    def update_task_hours(self, task_id: str, hours: float) -> None:
        """Update task hours worked"""
        
    def get_task_statistics(self, folder_id: str = None) -> Dict[str, int]:
        """Get task statistics"""
```

### StatusTracker Class
**Purpose**: Tracks task status changes
**Location**: `src/vogue_core/status_tracker.py`

```python
class StatusTracker:
    # Properties
    task_manager: TaskManager   # Task manager instance
    
    # Methods
    def __init__(self, task_manager: TaskManager):
        """Initialize status tracker"""
        
    def track_status_change(self, task_id: str, old_status: str, new_status: str) -> None:
        """Track status change"""
        
    def get_status_history(self, task_id: str) -> List[Dict]:
        """Get status history"""
        
    def get_status_statistics(self, folder_id: str) -> Dict[str, int]:
        """Get status statistics"""
        
    def get_progress_percentage(self, folder_id: str) -> float:
        """Get progress percentage"""
        
    def get_completion_rate(self, folder_id: str) -> float:
        """Get completion rate"""
        
    def get_average_completion_time(self, task_type: str) -> float:
        """Get average completion time for task type"""
        
    def get_status_trends(self, days: int = 30) -> Dict[str, List]:
        """Get status trends over time"""
```

## Version Management

### VersionManager Class
**Purpose**: Manages version operations
**Location**: `src/vogue_core/version_manager.py`

```python
class VersionManager:
    # Properties
    db_manager: DatabaseManager # Database manager
    repository: EntityRepository # Entity repository
    
    # Methods
    def __init__(self, db_manager: DatabaseManager):
        """Initialize version manager"""
        
    def create_version(self, product_id: str, author: str, comment: str = "") -> Version:
        """Create new version"""
        
    def publish_version(self, version_id: str) -> None:
        """Publish version"""
        
    def archive_version(self, version_id: str) -> None:
        """Archive version"""
        
    def unpublish_version(self, version_id: str) -> None:
        """Unpublish version"""
        
    def get_version_history(self, product_id: str) -> List[Version]:
        """Get version history"""
        
    def get_published_versions(self, product_id: str) -> List[Version]:
        """Get published versions"""
        
    def get_draft_versions(self, product_id: str) -> List[Version]:
        """Get draft versions"""
        
    def compare_versions(self, version1_id: str, version2_id: str) -> Dict:
        """Compare two versions"""
        
    def rollback_to_version(self, product_id: str, version_id: str) -> None:
        """Rollback to specific version"""
        
    def get_latest_version(self, product_id: str) -> Optional[Version]:
        """Get latest version"""
        
    def get_version_by_number(self, product_id: str, version_num: int) -> Optional[Version]:
        """Get version by number"""
        
    def get_version_count(self, product_id: str) -> int:
        """Get version count"""
        
    def archive_old_versions(self, product_id: str, keep_count: int = 5) -> None:
        """Archive old versions"""
        
    def get_version_statistics(self, product_id: str) -> Dict[str, Any]:
        """Get version statistics"""
```

### PublishingPipeline Class
**Purpose**: Manages publishing pipeline
**Location**: `src/vogue_core/publishing.py`

```python
class PublishingPipeline:
    # Properties
    version_manager: VersionManager # Version manager
    validators: List[Validator]     # List of validators
    integrators: List[Integrator]   # List of integrators
    
    # Methods
    def __init__(self, version_manager: VersionManager):
        """Initialize publishing pipeline"""
        
    def add_validator(self, validator: 'Validator') -> None:
        """Add validator to pipeline"""
        
    def add_integrator(self, integrator: 'Integrator') -> None:
        """Add integrator to pipeline"""
        
    def publish(self, version_id: str) -> bool:
        """Publish version through pipeline"""
        
    def validate(self, version_id: str) -> List[str]:
        """Validate version"""
        
    def integrate(self, version_id: str) -> bool:
        """Integrate version"""
        
    def get_validation_errors(self, version_id: str) -> List[str]:
        """Get validation errors"""
        
    def get_integration_status(self, version_id: str) -> str:
        """Get integration status"""
        
    def retry_publish(self, version_id: str) -> bool:
        """Retry failed publish"""
        
    def cancel_publish(self, version_id: str) -> None:
        """Cancel ongoing publish"""
```

## UI Components

### MainWindow Class
**Purpose**: Main application window
**Location**: `src/vogue_app/main_window.py`

```python
class MainWindow(QMainWindow):
    # Properties
    project_manager: ProjectManager # Project manager
    ui_manager: UIManager           # UI manager
    event_manager: EventManager     # Event manager
    
    # Methods
    def __init__(self):
        """Initialize main window"""
        
    def setup_ui(self) -> None:
        """Setup main window UI"""
        
    def setup_connections(self) -> None:
        """Setup signal connections"""
        
    def create_menu_bar(self) -> None:
        """Create menu bar"""
        
    def create_tool_bar(self) -> None:
        """Create tool bar"""
        
    def create_status_bar(self) -> None:
        """Create status bar"""
        
    def create_central_widget(self) -> None:
        """Create central widget"""
        
    def show_project_dialog(self) -> None:
        """Show project selection dialog"""
        
    def show_settings_dialog(self) -> None:
        """Show settings dialog"""
        
    def show_about_dialog(self) -> None:
        """Show about dialog"""
        
    def closeEvent(self, event) -> None:
        """Handle close event"""
        
    def resizeEvent(self, event) -> None:
        """Handle resize event"""
```

### HierarchyPanel Class
**Purpose**: Project hierarchy display
**Location**: `src/vogue_app/hierarchy_panel.py`

```python
class HierarchyPanel(QWidget):
    # Properties
    tree_widget: QTreeWidget       # Tree widget
    project_manager: ProjectManager # Project manager
    
    # Methods
    def __init__(self, parent=None):
        """Initialize hierarchy panel"""
        
    def setup_ui(self) -> None:
        """Setup hierarchy panel UI"""
        
    def refresh_hierarchy(self) -> None:
        """Refresh hierarchy display"""
        
    def add_folder(self, folder: Folder) -> None:
        """Add folder to hierarchy"""
        
    def remove_folder(self, folder_id: str) -> None:
        """Remove folder from hierarchy"""
        
    def move_folder(self, folder_id: str, new_parent_id: str) -> None:
        """Move folder to new parent"""
        
    def expand_folder(self, folder_id: str) -> None:
        """Expand folder in tree"""
        
    def collapse_folder(self, folder_id: str) -> None:
        """Collapse folder in tree"""
        
    def select_folder(self, folder_id: str) -> None:
        """Select folder in tree"""
        
    def get_selected_folder(self) -> Optional[Folder]:
        """Get selected folder"""
        
    def filter_folders(self, filter_text: str) -> None:
        """Filter folders by text"""
        
    def sort_folders(self, column: int, order: Qt.SortOrder) -> None:
        """Sort folders by column"""
```

### DetailsPanel Class
**Purpose**: Entity details display
**Location**: `src/vogue_app/details_panel.py`

```python
class DetailsPanel(QWidget):
    # Properties
    scroll_area: QScrollArea       # Scroll area
    form_layout: QFormLayout       # Form layout
    current_entity: BaseEntity     # Current entity
    
    # Methods
    def __init__(self, parent=None):
        """Initialize details panel"""
        
    def setup_ui(self) -> None:
        """Setup details panel UI"""
        
    def show_entity(self, entity: BaseEntity) -> None:
        """Show entity details"""
        
    def update_entity(self, entity: BaseEntity) -> None:
        """Update entity details"""
        
    def clear_details(self) -> None:
        """Clear details display"""
        
    def create_entity_form(self, entity: BaseEntity) -> None:
        """Create form for entity"""
        
    def update_entity_form(self, entity: BaseEntity) -> None:
        """Update entity form"""
        
    def save_entity_changes(self) -> None:
        """Save entity changes"""
        
    def cancel_entity_changes(self) -> None:
        """Cancel entity changes"""
        
    def validate_entity_form(self) -> List[str]:
        """Validate entity form"""
```

### TaskPanel Class
**Purpose**: Task management display
**Location**: `src/vogue_app/task_panel.py`

```python
class TaskPanel(QWidget):
    # Properties
    task_table: QTableWidget       # Task table
    task_manager: TaskManager      # Task manager
    
    # Methods
    def __init__(self, parent=None):
        """Initialize task panel"""
        
    def setup_ui(self) -> None:
        """Setup task panel UI"""
        
    def refresh_tasks(self) -> None:
        """Refresh task display"""
        
    def create_task(self) -> None:
        """Create new task"""
        
    def edit_task(self, task_id: str) -> None:
        """Edit task"""
        
    def delete_task(self, task_id: str) -> None:
        """Delete task"""
        
    def assign_task(self, task_id: str, user_id: str) -> None:
        """Assign task to user"""
        
    def update_task_status(self, task_id: str, status: str) -> None:
        """Update task status"""
        
    def filter_tasks(self, filter_text: str) -> None:
        """Filter tasks by text"""
        
    def sort_tasks(self, column: int, order: Qt.SortOrder) -> None:
        """Sort tasks by column"""
        
    def get_selected_task(self) -> Optional[Task]:
        """Get selected task"""
        
    def show_task_details(self, task_id: str) -> None:
        """Show task details"""
```

## DCC Integration

### DCCBridge Class
**Purpose**: Base class for DCC integration
**Location**: `src/vogue_integration/dcc_bridge.py`

```python
class DCCBridge:
    # Properties
    dcc_name: str                  # DCC name
    is_connected: bool            # Connection status
    
    # Methods
    def __init__(self, dcc_name: str):
        """Initialize DCC bridge"""
        
    def connect(self) -> bool:
        """Connect to DCC"""
        
    def disconnect(self) -> None:
        """Disconnect from DCC"""
        
    def launch(self, project_path: str) -> bool:
        """Launch DCC with project"""
        
    def get_current_scene(self) -> str:
        """Get current scene path"""
        
    def set_current_scene(self, scene_path: str) -> bool:
        """Set current scene"""
        
    def save_scene(self) -> bool:
        """Save current scene"""
        
    def export_selection(self, export_path: str) -> bool:
        """Export selection"""
        
    def import_file(self, file_path: str) -> bool:
        """Import file"""
        
    def get_selection(self) -> List[str]:
        """Get selected objects"""
        
    def set_selection(self, objects: List[str]) -> None:
        """Set selection"""
        
    def is_dcc_running(self) -> bool:
        """Check if DCC is running"""
        
    def get_dcc_version(self) -> str:
        """Get DCC version"""
```

### MayaBridge Class
**Purpose**: Maya-specific integration
**Location**: `src/vogue_integration/maya_bridge.py`

```python
class MayaBridge(DCCBridge):
    # Methods
    def __init__(self):
        """Initialize Maya bridge"""
        
    def connect(self) -> bool:
        """Connect to Maya"""
        
    def create_reference(self, file_path: str, namespace: str = "") -> str:
        """Create file reference"""
        
    def remove_reference(self, reference_node: str) -> bool:
        """Remove file reference"""
        
    def get_references(self) -> List[Dict]:
        """Get all references"""
        
    def update_reference(self, reference_node: str, new_path: str) -> bool:
        """Update reference path"""
        
    def get_scene_info(self) -> Dict[str, Any]:
        """Get scene information"""
        
    def get_objects_by_type(self, object_type: str) -> List[str]:
        """Get objects by type"""
        
    def create_camera(self, name: str) -> str:
        """Create camera"""
        
    def create_light(self, name: str, light_type: str) -> str:
        """Create light"""
        
    def render_scene(self, output_path: str) -> bool:
        """Render scene"""
        
    def get_render_settings(self) -> Dict[str, Any]:
        """Get render settings"""
        
    def set_render_settings(self, settings: Dict[str, Any]) -> None:
        """Set render settings"""
```

## Plugin System

### PluginManager Class
**Purpose**: Manages plugins
**Location**: `src/vogue_core/plugin_manager.py`

```python
class PluginManager:
    # Properties
    plugins: Dict[str, Plugin]     # Loaded plugins
    plugin_dirs: List[str]         # Plugin directories
    
    # Methods
    def __init__(self):
        """Initialize plugin manager"""
        
    def add_plugin_dir(self, path: str) -> None:
        """Add plugin directory"""
        
    def load_plugin(self, plugin_path: str) -> bool:
        """Load plugin"""
        
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload plugin"""
        
    def get_plugin(self, plugin_name: str) -> Optional['Plugin']:
        """Get plugin by name"""
        
    def list_plugins(self) -> List[str]:
        """List loaded plugins"""
        
    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload plugin"""
        
    def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        """Get plugin information"""
        
    def check_plugin_dependencies(self, plugin_name: str) -> List[str]:
        """Check plugin dependencies"""
        
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable plugin"""
        
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable plugin"""
        
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get plugin configuration"""
        
    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """Set plugin configuration"""
```

### Plugin Class
**Purpose**: Base class for plugins
**Location**: `src/vogue_core/plugin.py`

```python
class Plugin:
    # Properties
    name: str                      # Plugin name
    version: str                   # Plugin version
    enabled: bool                  # Plugin enabled status
    
    # Methods
    def __init__(self, name: str, version: str):
        """Initialize plugin"""
        
    def initialize(self) -> bool:
        """Initialize plugin"""
        
    def cleanup(self) -> None:
        """Cleanup plugin"""
        
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        
    def get_dependencies(self) -> List[str]:
        """Get plugin dependencies"""
        
    def check_compatibility(self) -> bool:
        """Check compatibility"""
        
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema"""
        
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration"""
        
    def on_enable(self) -> None:
        """Called when plugin is enabled"""
        
    def on_disable(self) -> None:
        """Called when plugin is disabled"""
        
    def on_project_load(self, project_path: str) -> None:
        """Called when project is loaded"""
        
    def on_project_save(self, project_path: str) -> None:
        """Called when project is saved"""
```

## Utility Classes

### SettingsManager Class
**Purpose**: Manages application settings
**Location**: `src/vogue_core/settings.py`

```python
class SettingsManager:
    # Properties
    config_path: str               # Configuration file path
    config: Dict[str, Any]         # Configuration data
    
    # Methods
    def __init__(self, config_path: str):
        """Initialize settings manager"""
        
    def load_config(self) -> None:
        """Load configuration from file"""
        
    def save_config(self) -> None:
        """Save configuration to file"""
        
    def get(self, key: str, default=None):
        """Get configuration value"""
        
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        
    def get_section(self, section: str) -> Dict:
        """Get configuration section"""
        
    def set_section(self, section: str, values: Dict) -> None:
        """Set configuration section"""
        
    def has_key(self, key: str) -> bool:
        """Check if key exists"""
        
    def remove_key(self, key: str) -> None:
        """Remove key"""
        
    def reset_to_defaults(self) -> None:
        """Reset to default values"""
        
    def export_config(self, export_path: str) -> None:
        """Export configuration"""
        
    def import_config(self, import_path: str) -> None:
        """Import configuration"""
```

### EventManager Class
**Purpose**: Manages events
**Location**: `src/vogue_core/events.py`

```python
class EventManager:
    # Properties
    listeners: Dict[str, List[Callable]] # Event listeners
    
    # Methods
    def __init__(self):
        """Initialize event manager"""
        
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to event"""
        
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from event"""
        
    def emit(self, event_type: str, data: Any = None) -> None:
        """Emit event"""
        
    def emit_async(self, event_type: str, data: Any = None) -> None:
        """Emit event asynchronously"""
        
    def get_listeners(self, event_type: str) -> List[Callable]:
        """Get event listeners"""
        
    def clear_listeners(self, event_type: str = None) -> None:
        """Clear event listeners"""
        
    def get_event_types(self) -> List[str]:
        """Get all event types"""
        
    def get_listener_count(self, event_type: str) -> int:
        """Get listener count for event type"""
```

This comprehensive reference provides all the functions, classes, and variables you need to upgrade your Vogue Manager program. Each component is designed to work together to create a professional-grade VFX pipeline tool that combines the best features from both Ayon and Prism.
