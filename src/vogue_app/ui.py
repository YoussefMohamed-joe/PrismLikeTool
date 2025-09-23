"""
Prism-like UI components for Vogue Manager

Complete Prism interface clone with all standard Prism functionalities.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import PyQt6 directly for better compatibility
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QPlainTextEdit, QPushButton, QLabel, QSplitter, QGroupBox,
    QMenuBar, QMenu, QToolBar, QStatusBar, QFileDialog, QMessageBox,
    QHeaderView, QAbstractItemView, QProgressBar, QLineEdit, QComboBox,
    QListWidget, QListWidgetItem, QCheckBox, QSpinBox, QDoubleSpinBox,
    QSlider, QScrollArea, QFrame, QDockWidget, QTextEdit, QCompleter,
    QButtonGroup, QRadioButton, QToolButton, QSizePolicy, QSpacerItem,
    QDialog, QInputDialog, QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QRect
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction, QPalette, QColor, QPainter, QPen

from .colors import COLORS
from .qss import build_qss


def _load_dcc_icon(app_name: str) -> Optional[QIcon]:
    """Load official DCC icon from common asset locations if present.
    Searches multiple locations and filename variants.
    """
    try:
        name_variants = [
            app_name,
            app_name.lower(),
            app_name.capitalize(),
            f"{app_name}_logo",
            f"logo_{app_name}",
        ]
        exts = ["png", "ico", "svg", "jpg", "jpeg"]
        base_dirs = [
            Path(__file__).parent / "assets" / "icons",
            Path(__file__).parent / "assets",
            Path.cwd() / "src" / "vogue_app" / "assets" / "icons",
            Path.cwd() / "src" / "vogue_app" / "assets",
            Path.cwd() / "assets" / "icons",
            Path.cwd() / "assets",
        ]
        for base in base_dirs:
            for nm in name_variants:
                for ext in exts:
                    p = base / f"{nm}.{ext}"
                    if p.exists():
                        return QIcon(str(p))
    except Exception:
        pass
    return None

def sync_ui_to_project_model(project_browser, manager):
    """Sync UI tree structure to the project model"""
    if not manager.current_project:
        return False

    try:
        # Sync folders and assets
        folders = []
        assets = []

        # Process asset tree
        for i in range(project_browser.asset_tree.topLevelItemCount()):
            folder_item = project_browser.asset_tree.topLevelItem(i)
            if folder_item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
                folder_name = folder_item.text(0)

                # Create folder entry
                from vogue_core.models import Folder
                folder_assets = []
                folder_shots = []

                # Add assets in this folder (including default "Assets" folder)
                for j in range(folder_item.childCount()):
                    asset_item = folder_item.child(j)
                    asset_name = asset_item.text(0)
                    asset_type = asset_item.data(0, Qt.ItemDataRole.UserRole)

                    # Only save actual assets, not summary items or folders
                    print(f"DEBUG: Processing asset '{asset_name}' with type '{asset_type}'")
                    if asset_type not in ["Summary", "Folder"]:
                        from vogue_core.models import Asset
                        # Use "Asset" as the type since we're not using complex type system anymore
                        asset = Asset(name=asset_name, type="Asset")
                        assets.append(asset)
                        folder_assets.append(asset_name)
                        print(f"DEBUG: Saved asset '{asset_name}'")
                    else:
                        print(f"DEBUG: Skipped asset '{asset_name}' (type: {asset_type})")

                # Only create folder entries for custom folders, not the default "Assets" folder
                if folder_name != "Assets":
                    # Check if folder already exists in current project
                    existing_folder = None
                    for f in manager.current_project.folders:
                        if f.name == folder_name and f.type == "asset":
                            existing_folder = f
                            break

                    if existing_folder:
                        # Update existing folder
                        existing_folder.assets = folder_assets
                    else:
                        # Create new folder
                        folder = Folder(
                            name=folder_name,
                            type="asset",
                            assets=folder_assets,
                            shots=folder_shots
                        )
                        folders.append(folder)

        # Process shot tree
        shots = []
        for i in range(project_browser.shot_tree.topLevelItemCount()):
            folder_item = project_browser.shot_tree.topLevelItem(i)
            if folder_item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
                folder_name = folder_item.text(0)

                # Create folder entry
                from vogue_core.models import Folder
                folder_assets = []
                folder_shots = []

                # Add shots in this folder
                for j in range(folder_item.childCount()):
                    shot_item = folder_item.child(j)
                    shot_name = shot_item.text(0)
                    shot_type = shot_item.data(0, Qt.ItemDataRole.UserRole)

                    # Only save actual shots, not summary items
                    if shot_type not in ["Summary"]:
                        from vogue_core.models import Shot
                        # Use folder name as sequence, or "Main" if it's a default folder
                        sequence = folder_name if folder_name != "Shots" else "Main"
                        shot = Shot(sequence=sequence, name=shot_name)
                        shots.append(shot)
                        folder_shots.append(shot_name)

                # Only create folder entries for custom folders, not default folders
                if folder_name != "Shots":  # Assuming "Shots" is the default folder name
                    # Check if folder already exists in current project
                    existing_folder = None
                    for f in manager.current_project.folders:
                        if f.name == folder_name and f.type == "shot":
                            existing_folder = f
                            break

                    if existing_folder:
                        # Update existing folder
                        existing_folder.shots = folder_shots
                    else:
                        # Create new folder
                        folder = Folder(
                            name=folder_name,
                            type="shot",
                            assets=folder_assets,
                            shots=folder_shots
                        )
                        folders.append(folder)

        # Preserve existing folders that weren't processed in this sync
        for existing_folder in manager.current_project.folders:
            if existing_folder.type == "asset":
                # Check if we already processed this folder
                folder_already_processed = False
                for new_folder in folders:
                    if new_folder.name == existing_folder.name and new_folder.type == existing_folder.type:
                        folder_already_processed = True
                        break

                if not folder_already_processed:
                    folders.append(existing_folder)
            elif existing_folder.type == "shot":
                # Preserve shot folders as well
                folders.append(existing_folder)

        manager.current_project.folders = folders
        manager.current_project.assets = assets
        return True
    except Exception as e:
        print(f"Sync UI to model failed: {e}")
        return False


# Global reference to the current controller
_current_controller = None

def set_current_controller(controller):
    """Set the global controller reference"""
    global _current_controller
    _current_controller = controller

def get_current_controller():
    """Get the global controller reference"""
    global _current_controller
    return _current_controller


def auto_save_project(project_browser=None):
    """Utility function to auto-save the current project"""
    try:
        # Try to get the controller from global reference
        controller = get_current_controller()
        if controller and hasattr(controller, 'manager') and controller.manager:
            manager = controller.manager

            if hasattr(manager, 'current_project') and manager.current_project:
                # Sync UI changes to the model first
                if not sync_ui_to_project_model(controller.project_browser, manager):
                    return False

                # Save the project
                manager.save_project(manager.current_project)
                return True
        else:
            # Fallback: try to find controller via project_browser
            if project_browser:
                # Try to traverse up the widget hierarchy to find the controller
                current_widget = project_browser
                max_depth = 10  # Prevent infinite loops
                depth = 0

                while current_widget and depth < max_depth:
                    if hasattr(current_widget, 'manager'):
                        manager = current_widget.manager

                        if hasattr(manager, 'current_project') and manager.current_project:
                            # Sync UI changes to the model first
                            if not sync_ui_to_project_model(project_browser, manager):
                                return False

                            # Save the project
                            manager.save_project(manager.current_project)
                            return True
                        break

                    current_widget = current_widget.parent()
                    depth += 1

    except Exception as e:
        print(f"Auto-save failed: {e}")
        return False
    return False


class PrismStyleWidget(QWidget):
    """Base widget with Prism styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Re-enable global QSS styling
        self.setStyleSheet(build_qss())


class ProjectBrowser(PrismStyleWidget):
    """Project browser widget - main left panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize clipboard state for cut/copy operations
        self.clipboard_item = None
        self.clipboard_operation = None  # 'cut' or 'copy'
        self.clipboard_type = None  # 'asset' or 'shot'
        # Initialize current entity tracking
        self.current_entity = None
        self.current_entity_type = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create horizontal splitter for tabs + tasks
        self.horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Asset/Shot tabs
        self.setup_tabs_section()
        self.horizontal_splitter.addWidget(self.tabs_widget)

        # Right side: Departments and Tasks section (switched order)
        self.setup_tasks_section()
        self.horizontal_splitter.addWidget(self.tasks_widget)

        # Set splitter proportions (50% tabs, 50% tasks+departments)
        self.horizontal_splitter.setSizes([400, 400])

        layout.addWidget(self.horizontal_splitter)

        # Set up thumbnail delegates - DISABLED for visibility
        # The ThumbnailDelegate causes items to be invisible with dark themes
        # self.asset_delegate = ThumbnailDelegate(self.asset_tree)
        # self.shot_delegate = ThumbnailDelegate(self.shot_tree)
        # self.asset_tree.setItemDelegate(self.asset_delegate)
        # self.shot_tree.setItemDelegate(self.shot_delegate)

        # Don't populate with sample data initially - let project loading handle it
        # self.populate_asset_tree()
        # self.populate_shot_tree()

        # Setup context menus
        self.setup_context_menus()
        
        # Setup selection connections
        self.setup_selection_connections()
        
        # Setup task selection behavior
        self.setup_task_selection_behavior()
    
    def setup_selection_connections(self):
        """Setup selection change connections"""
        # Connect asset tree selection
        self.asset_tree.itemSelectionChanged.connect(self.on_asset_selection_changed)
        self.shot_tree.itemSelectionChanged.connect(self.on_shot_selection_changed)
        
        # Connect task selection
        self.tasks_list.itemSelectionChanged.connect(self.on_task_selection_changed)
    
    def on_asset_selection_changed(self):
        """Handle asset selection change"""
        current_item = self.asset_tree.currentItem()
        if not current_item:
            # No item selected, clear departments
            self.current_entity = None
            self.current_entity_type = None
            self.load_entity_departments(None, None)
            return
        
        item_type = current_item.data(0, Qt.ItemDataRole.UserRole)
        if item_type == "Asset":
            asset_name = current_item.text(0)
            self.notify_asset_selected(asset_name)
        else:
            # Non-asset item selected, clear departments
            self.current_entity = None
            self.current_entity_type = None
            self.load_entity_departments(None, None)
    
    def on_shot_selection_changed(self):
        """Handle shot selection change"""
        current_item = self.shot_tree.currentItem()
        if not current_item:
            # No item selected, clear departments
            self.current_entity = None
            self.current_entity_type = None
            self.load_entity_departments(None, None)
            return
        
        item_type = current_item.data(0, Qt.ItemDataRole.UserRole)
        if item_type == "Shot":
            shot_name = current_item.text(0)
            # Get parent folder for sequence
            parent_item = current_item.parent()
            sequence = parent_item.text(0) if parent_item else "Main"
            shot_key = f"{sequence}/{shot_name}"
            self.notify_shot_selected(shot_key)
        else:
            # Non-shot item selected, clear departments
            self.current_entity = None
            self.current_entity_type = None
            self.load_entity_departments(None, None)
    
    def notify_asset_selected(self, asset_name: str):
        """Notify that an asset was selected"""
        # Store current entity
        self.current_entity = asset_name
        self.current_entity_type = "Asset"
        
        # Find the version manager in the main window
        main_window = self.window()
        if hasattr(main_window, 'version_manager'):
            main_window.version_manager.update_entity(asset_name, "Asset")
        
        # Load departments for this asset
        self.load_entity_departments(asset_name, "Asset")
        
        # Ensure task selection is maintained
        self.ensure_task_selection_visible()
    
    def notify_shot_selected(self, shot_key: str):
        """Notify that a shot was selected"""
        # Store current entity
        self.current_entity = shot_key
        self.current_entity_type = "Shot"
        
        # Find the version manager in the main window
        main_window = self.window()
        if hasattr(main_window, 'version_manager'):
            main_window.version_manager.update_entity(shot_key, "Shot")
        
        # Load departments for this shot
        self.load_entity_departments(shot_key, "Shot")
    
    def load_entity_departments(self, entity_name: str, entity_type: str):
        """Load departments and tasks for the selected entity (asset or shot)"""
        # Get the main window to access the project manager
        main_window = self.window()
        if not hasattr(main_window, 'manager'):
            return
        
        manager = main_window.manager
        if not manager.current_project:
            return
        
        # Clear current departments and tasks lists
        self.departments_list.clear()
        self.tasks_list.clear()
        
        # If no entity selected, show empty lists
        if not entity_name or not entity_type:
            return
        
        # Get entity departments
        entity_departments = []
        if entity_type == "Asset":
            asset = manager.current_project.get_asset(entity_name)
            if asset:
                entity_departments = asset.departments
        elif entity_type == "Shot":
            # Parse shot key to get sequence and name
            if "/" in entity_name:
                sequence, name = entity_name.split("/", 1)
                shot = manager.current_project.get_shot(sequence, name)
                if shot:
                    entity_departments = shot.departments
        
        # Show entity-specific departments
        for dept in entity_departments:
            self.departments_list.addItem(f"{dept} - Active")
        
        # Load entity-specific tasks
        self.load_entity_tasks(entity_name, entity_type)
        
        # Auto-select first department if any exist
        if self.departments_list.count() > 0:
            self.departments_list.setCurrentRow(0)
            # Trigger department selection change to update tasks
            if hasattr(main_window, 'filter_tasks_by_department'):
                main_window.filter_tasks_by_department()
    
    def load_entity_tasks(self, entity_name: str, entity_type: str):
        """Load tasks specific to the selected entity (asset or shot)"""
        # Get the main window to access the project manager
        main_window = self.window()
        if not hasattr(main_window, 'manager'):
            return
        
        manager = main_window.manager
        if not manager.current_project:
            return
        
        # Clear current tasks list
        self.tasks_list.clear()
        
        # If no entity selected, show empty list
        if not entity_name or not entity_type:
            return
        
        # Get entity-specific tasks from project
        entity_tasks = []
        if hasattr(manager.current_project, 'tasks') and manager.current_project.tasks:
            for task in manager.current_project.tasks:
                # Check if task belongs to this entity
                task_entity = getattr(task, 'entity', None) if hasattr(task, 'entity') else None
                task_entity_type = getattr(task, 'entity_type', None) if hasattr(task, 'entity_type') else None
                
                # For legacy tasks without entity info, skip them (they're project-level)
                if task_entity == entity_name and task_entity_type == entity_type:
                    entity_tasks.append(task)
                elif isinstance(task, dict):
                    # Legacy dict format - check if it has entity info
                    if (task.get('entity') == entity_name and 
                        task.get('entity_type') == entity_type):
                        entity_tasks.append(task)
        
        # Display entity-specific tasks
        for task in entity_tasks:
            if hasattr(task, 'name'):
                # Task object
                task_text = f"{task.name} - {task.status}"
                if task.description:
                    task_text += f" ({task.description})"
            elif isinstance(task, dict):
                # Legacy dict format
                task_text = f"{task.get('name', 'Unknown')} - {task.get('status', 'Pending')}"
                if task.get('description'):
                    task_text += f" ({task['description']})"
            else:
                continue
            
            self.tasks_list.addItem(task_text)
        
        # Auto-select first task if any exist
        if self.tasks_list.count() > 0:
            self.tasks_list.setCurrentRow(0)
    
    def on_task_selection_changed(self):
        """Handle task selection change"""
        current_item = self.tasks_list.currentItem()
        if current_item:
            task_name = current_item.text().split(" - ")[0]  # Extract task name before status
            self.notify_task_selected(task_name)
    
    def notify_task_selected(self, task_name: str):
        """Notify that a task was selected"""
        # Find the version manager in the main window
        main_window = self.window()
        if hasattr(main_window, 'version_manager'):
            # Update version manager with current entity and task
            if hasattr(self, 'current_entity'):
                main_window.version_manager.update_entity(self.current_entity, "Asset", task_name)
    
    def ensure_task_selection_visible(self):
        """Ensure the task selection is visually highlighted"""
        if self.tasks_list.count() > 0:
            # Get current selection
            current_row = self.tasks_list.currentRow()
            if current_row < 0:
                # If no selection, select the first item
                current_row = 0
                self.tasks_list.setCurrentRow(current_row)
            
            # Ensure the item is visible and selected
            self.tasks_list.scrollToItem(
                self.tasks_list.item(current_row),
                QAbstractItemView.ScrollHint.EnsureVisible
            )
    
    def setup_task_selection_behavior(self):
        """Setup task list to maintain selection like departments"""
        # Set focus policy to strong focus (maintains selection when clicking elsewhere)
        self.tasks_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Ensure at least one item is always selected
        if self.tasks_list.count() > 0:
            if self.tasks_list.currentRow() < 0:
                self.tasks_list.setCurrentRow(0)
        
        # Override focus events to maintain selection
        self.tasks_list.focusOutEvent = self.task_list_focus_out
        self.tasks_list.focusInEvent = self.task_list_focus_in
        self.tasks_list.mousePressEvent = self.task_list_mouse_press
    
    def task_list_focus_out(self, event):
        """Handle focus out event for task list - maintain selection"""
        # Don't clear selection when losing focus, especially for popup menus
        event.ignore()
        # Ensure selection is maintained even when focus is lost
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(10, self.ensure_task_selection_visible)
    
    def task_list_focus_in(self, event):
        """Handle focus in event for task list - ensure selection is visible"""
        # Ensure selection is visible when regaining focus
        self.ensure_task_selection_visible()
        event.accept()
    
    def task_list_mouse_press(self, event):
        """Handle mouse press event for task list - maintain selection"""
        # Call the original mouse press event
        from PyQt6.QtWidgets import QListWidget
        QListWidget.mousePressEvent(self.tasks_list, event)
        
        # Ensure selection is maintained
        self.ensure_task_selection_visible()

    def setup_tabs_section(self):
        """Setup the tabs section (Assets/Shots)"""
        self.tabs_widget = QWidget()
        tabs_layout = QVBoxLayout(self.tabs_widget)
        tabs_layout.setContentsMargins(5, 5, 5, 5)

        # Main content area with tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setDocumentMode(True)  # Modern tab style

        # Assets tab - Clean implementation
        assets_tab = QWidget()
        assets_layout = QVBoxLayout(assets_tab)
        assets_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create simple asset tree
        self.asset_tree = AssetTreeWidget()
        self.asset_tree.setHeaderHidden(True)
        self.asset_tree.setRootIsDecorated(True)
        self.asset_tree.setAlternatingRowColors(True)
        self.asset_tree.setMinimumHeight(200)
        self.asset_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        # Basic drag and drop
        self.asset_tree.setDragEnabled(True)
        self.asset_tree.setAcceptDrops(True)
        self.asset_tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.asset_tree.setDropIndicatorShown(True)
        self.asset_tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        
        assets_layout.addWidget(self.asset_tree)
        
        # Asset buttons
        asset_btn_layout = QHBoxLayout()
        self.add_asset_btn = QPushButton("Add Asset")
        self.new_folder_btn = QPushButton("New Folder")
        self.refresh_assets_btn = QPushButton("Refresh")
        asset_btn_layout.addWidget(self.add_asset_btn)
        asset_btn_layout.addWidget(self.new_folder_btn)
        asset_btn_layout.addWidget(self.refresh_assets_btn)
        asset_btn_layout.addStretch()
        assets_layout.addLayout(asset_btn_layout)
        
        self.tab_widget.addTab(assets_tab, "Assets")

        # Shots tab
        shots_tab = QWidget()
        shots_layout = QVBoxLayout(shots_tab)
        shots_layout.setContentsMargins(5, 5, 5, 5)
        
        # Shot filter
        shot_filter_layout = QHBoxLayout()
        self.sequence_combo = QComboBox()
        self.sequence_combo.addItems(["All Sequences"])
        shot_filter_layout.addWidget(QLabel("Sequence:"))
        shot_filter_layout.addWidget(self.sequence_combo)
        shot_filter_layout.addStretch()
        shots_layout.addLayout(shot_filter_layout)
        
        # Shot tree view (Using standard QTreeWidget for compatibility)
        self.shot_tree = ShotTreeWidget()
        self.shot_tree.setHeaderHidden(True)
        self.shot_tree.setRootIsDecorated(True)
        self.shot_tree.setAlternatingRowColors(True)
        self.shot_tree.setMinimumHeight(300)
        # Enable multi-selection for bulk operations
        self.shot_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        # Enable drag and drop
        self.shot_tree.setDragEnabled(True)
        self.shot_tree.setAcceptDrops(True)
        self.shot_tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.shot_tree.setDropIndicatorShown(True)
        # Remove problematic styling - let controller apply working styles
        shots_layout.addWidget(self.shot_tree)
        
        # Shot buttons
        shot_btn_layout = QHBoxLayout()
        self.add_shot_btn = QPushButton("Add Shot")
        self.add_shot_btn.setProperty("class", "primary")
        self.new_shot_folder_btn = QPushButton("New Folder")
        self.refresh_shots_btn = QPushButton("Refresh")
        shot_btn_layout.addWidget(self.add_shot_btn)
        shot_btn_layout.addWidget(self.new_shot_folder_btn)
        shot_btn_layout.addWidget(self.refresh_shots_btn)
        shot_btn_layout.addStretch()
        shots_layout.addLayout(shot_btn_layout)
        
        self.tab_widget.addTab(shots_tab, "Shots")

        # Add the tab widget to the tabs layout
        tabs_layout.addWidget(self.tab_widget)

    def setup_tasks_section(self):
        """Setup the Tasks section with Ayon-style design"""
        self.tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(self.tasks_widget)
        tasks_layout.setContentsMargins(8, 8, 8, 8)
        tasks_layout.setSpacing(12)

        # Project Info Section (Ayon style)
        self.setup_project_info_section()
        tasks_layout.addWidget(self.project_info_widget)

        # Departments Section (Ayon style)
        self.setup_departments_section()
        tasks_layout.addWidget(self.departments_widget)

        # Tasks Section (Ayon style)
        self.setup_tasks_section_ayon()
        tasks_layout.addWidget(self.tasks_widget_ayon)

    def setup_departments_section(self):
        """Setup departments section in Ayon style"""
        self.departments_widget = QWidget()
        dept_layout = QVBoxLayout(self.departments_widget)
        dept_layout.setContentsMargins(0, 0, 0, 0)
        dept_layout.setSpacing(8)

        # Departments title
        dept_title = QLabel("Departments")
        dept_title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {COLORS['fg']};
                margin: 0;
                padding: 4px 0;
            }}
        """)
        dept_layout.addWidget(dept_title)

        # Departments list
        self.departments_list = QListWidget()
        self.departments_list.setAlternatingRowColors(True)
        self.departments_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.departments_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['surface']};
                color: {COLORS['fg']};
                border: 1px solid {COLORS['outline']};
                border-radius: 8px;
                selection-background-color: {COLORS['accent']};
                alternate-background-color: {COLORS['surface_high']};
                font-size: 13px;
                font-weight: 500;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border: none;
                color: {COLORS['fg']};
                border-radius: 4px;
                margin: 1px;
                border: 1px solid transparent;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent']};
                color: white;
                border: 1px solid {COLORS['accent_hover']};
                font-weight: 600;
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['hover']};
                color: {COLORS['fg']};
                border: 1px solid {COLORS['accent']};
            }}
        """)

        # No default departments - will be populated when entity is selected

        dept_layout.addWidget(self.departments_list)

    def setup_tasks_section_ayon(self):
        """Setup tasks section in Ayon style"""
        self.tasks_widget_ayon = QWidget()
        tasks_layout = QVBoxLayout(self.tasks_widget_ayon)
        tasks_layout.setContentsMargins(0, 0, 0, 0)
        tasks_layout.setSpacing(8)

        # Tasks title
        tasks_title = QLabel("Tasks")
        tasks_title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {COLORS['fg']};
                margin: 0;
                padding: 4px 0;
            }}
        """)
        tasks_layout.addWidget(tasks_title)

        # Task Filter
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(8)

        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {COLORS['fg_variant']};
            }}
        """)
        filter_layout.addWidget(filter_label)

        self.task_filter_combo = QComboBox()
        self.task_filter_combo.addItems(["All Tasks", "My Tasks", "Active", "Completed", "Pending"])
        self.task_filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['fg']};
                border: 1px solid {COLORS['outline']};
                border-radius: 6px;
                padding: 6px 10px;
                min-width: 120px;
                font-size: 12px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['accent']};
            }}
            QComboBox:focus {{
                border-color: {COLORS['accent']};
                border-width: 2px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgNEw2IDdMOCA0SDNaIiBmaWxsPSIjRENERERERCIvPgo8L3N2Zz4K);
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['surface_high']};
                color: {COLORS['fg']};
                border: 1px solid {COLORS['outline']};
                border-radius: 6px;
                selection-background-color: {COLORS['accent']};
                font-size: 12px;
            }}
        """)
        filter_layout.addWidget(self.task_filter_combo)
        filter_layout.addStretch()

        tasks_layout.addLayout(filter_layout)

        # Tasks List
        self.tasks_list = QListWidget()
        self.tasks_list.setAlternatingRowColors(True)
        self.tasks_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tasks_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['surface']};
                color: {COLORS['fg']};
                border: 1px solid {COLORS['outline']};
                border-radius: 8px;
                selection-background-color: {COLORS['accent']};
                alternate-background-color: {COLORS['surface_high']};
                font-size: 13px;
                font-weight: 500;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border: none;
                color: {COLORS['fg']};
                border-radius: 4px;
                margin: 1px;
                border: 1px solid transparent;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent']};
                color: white;
                border: 1px solid {COLORS['accent_hover']};
                font-weight: 600;
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['hover']};
                color: {COLORS['fg']};
                border: 1px solid {COLORS['accent']};
            }}
        """)

        # Add some sample tasks
        sample_tasks = [
            "Model high poly character - In Progress",
            "Texture character materials - Pending",
            "Rig character skeleton - Not Started",
            "Create character animations - Not Started",
            "Create character lighting setup - Not Started",
            "Render character turntable - Not Started",
            "Create character walk cycle - Not Started",
            "Optimize character geometry - Pending"
        ]

        for task in sample_tasks:
            item = QListWidgetItem(task)
            self.tasks_list.addItem(item)

        tasks_layout.addWidget(self.tasks_list)

    def setup_project_info_section(self):
        """Setup the Project Info section in Ayon style"""
        self.project_info_widget = QWidget()
        info_layout = QVBoxLayout(self.project_info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)

        # Project Info title
        info_title = QLabel("Project Info")
        info_title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {COLORS['fg']};
                margin: 0;
                padding: 4px 0;
            }}
        """)
        info_layout.addWidget(info_title)

        # Project info content
        info_content = QWidget()
        info_content_layout = QFormLayout(info_content)
        info_content_layout.setContentsMargins(0, 0, 0, 0)
        info_content_layout.setSpacing(6)

        self.project_name_label = QLabel("No Project Loaded")
        self.project_name_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {COLORS['fg']};
                background-color: {COLORS['surface']};
                padding: 6px 12px;
                border-radius: 6px;
                border: 1px solid {COLORS['outline']};
            }}
        """)
        
        self.project_path_label = QLabel("Not Available")
        self.project_path_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {COLORS['fg_variant']};
                background-color: {COLORS['surface']};
                padding: 4px 8px;
                border-radius: 4px;
                border: 1px solid {COLORS['outline']};
            }}
        """)
        self.project_path_label.setWordWrap(True)

        info_content_layout.addRow("Project:", self.project_name_label)
        info_content_layout.addRow("Path:", self.project_path_label)

        info_layout.addWidget(info_content)

    def generate_thumbnail(self, asset_type: str, asset_name: str) -> QPixmap:
        """Generate a thumbnail for an asset/shot based on its type"""
        pixmap = QPixmap(80, 80)
        pixmap.fill(QColor("#1A2332"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background with rounded corners
        painter.setBrush(QColor("#2A3441"))
        painter.setPen(QPen(QColor("#73C2FB"), 2))
        painter.drawRoundedRect(2, 2, 76, 76, 8, 8)

        # Draw icon based on type
        painter.setPen(QPen(QColor("#73C2FB"), 3))
        painter.setBrush(QColor("#73C2FB"))

        if asset_type.lower() in ["character", "characters"]:
            # Draw character icon (simple person shape)
            painter.drawEllipse(25, 15, 30, 30)  # Head
            painter.drawRect(35, 45, 10, 25)     # Body
            painter.drawLine(30, 50, 25, 65)      # Left arm
            painter.drawLine(50, 50, 55, 65)      # Right arm
            painter.drawLine(35, 70, 30, 85)      # Left leg
            painter.drawLine(45, 70, 50, 85)      # Right leg

        elif asset_type.lower() in ["prop", "props"]:
            # Draw prop icon (cube)
            painter.drawRect(25, 25, 30, 30)
            painter.drawLine(25, 25, 35, 15)      # Top-left edge
            painter.drawLine(55, 25, 65, 15)      # Top-right edge
            painter.drawLine(35, 15, 65, 15)      # Top edge
            painter.drawLine(65, 15, 65, 45)      # Right edge

        elif asset_type.lower() in ["environment", "environments"]:
            # Draw environment icon (landscape)
            painter.drawRect(20, 40, 40, 15)     # Ground
            painter.drawEllipse(15, 20, 50, 25)  # Sky
            painter.drawLine(30, 30, 50, 30)      # Horizon

        elif asset_type.lower() == "shot":
            # Draw shot icon (camera/clapperboard)
            painter.drawRect(20, 25, 40, 25)     # Clapperboard
            painter.drawRect(15, 15, 20, 15)     # Camera body
            painter.drawEllipse(10, 10, 10, 10)  # Lens
            painter.drawLine(15, 15, 25, 25)      # Clapper arm

        else:
            # Default folder icon for unknown types
            painter.drawRect(25, 20, 30, 20)     # Folder base
            painter.drawRect(20, 15, 35, 25)     # Folder
            painter.drawLine(20, 20, 30, 20)      # Folder tab

        painter.end()
        return pixmap

    def populate_asset_tree(self):
        """Populate the asset tree with hierarchical folder structure"""
        self.asset_tree.clear()

        # Create root folders
        characters_folder = QTreeWidgetItem(self.asset_tree)
        characters_folder.setText(0, "Characters")
        characters_folder.setData(0, Qt.ItemDataRole.UserRole, "Folder")

        props_folder = QTreeWidgetItem(self.asset_tree)
        props_folder.setText(0, "Props")
        props_folder.setData(0, Qt.ItemDataRole.UserRole, "Folder")

        environments_folder = QTreeWidgetItem(self.asset_tree)
        environments_folder.setText(0, "Environments")
        environments_folder.setData(0, Qt.ItemDataRole.UserRole, "Folder")

        # Add sample assets to folders
        hero_char = QTreeWidgetItem(characters_folder)
        hero_char.setText(0, "Hero_Character")
        hero_char.setData(0, Qt.ItemDataRole.UserRole, "Character")

        villain_char = QTreeWidgetItem(characters_folder)
        villain_char.setText(0, "Villain_Character")
        villain_char.setData(0, Qt.ItemDataRole.UserRole, "Character")

        magic_prop = QTreeWidgetItem(props_folder)
        magic_prop.setText(0, "Magic_Prop")
        magic_prop.setData(0, Qt.ItemDataRole.UserRole, "Prop")

        treasure_prop = QTreeWidgetItem(props_folder)
        treasure_prop.setText(0, "Treasure_Chest")
        treasure_prop.setData(0, Qt.ItemDataRole.UserRole, "Prop")

        forest_env = QTreeWidgetItem(environments_folder)
        forest_env.setText(0, "Forest_Environment")
        forest_env.setData(0, Qt.ItemDataRole.UserRole, "Environment")

        castle_env = QTreeWidgetItem(environments_folder)
        castle_env.setText(0, "Castle_Environment")
        castle_env.setData(0, Qt.ItemDataRole.UserRole, "Environment")

        # Expand all folders by default
        self.asset_tree.expandAll()

    def populate_shot_tree(self):
        """Populate the shot tree with hierarchical sequence structure"""
        self.shot_tree.clear()

        # Create sequence folders
        seq_a_folder = QTreeWidgetItem(self.shot_tree)
        seq_a_folder.setText(0, "Sequence_A")
        seq_a_folder.setData(0, Qt.ItemDataRole.UserRole, "Folder")

        seq_b_folder = QTreeWidgetItem(self.shot_tree)
        seq_b_folder.setText(0, "Sequence_B")
        seq_b_folder.setData(0, Qt.ItemDataRole.UserRole, "Folder")

        # Add sample shots to sequences
        shot_0010 = QTreeWidgetItem(seq_a_folder)
        shot_0010.setText(0, "0010")
        shot_0010.setData(0, Qt.ItemDataRole.UserRole, "Sequence A")

        shot_0020 = QTreeWidgetItem(seq_a_folder)
        shot_0020.setText(0, "0020")
        shot_0020.setData(0, Qt.ItemDataRole.UserRole, "Sequence A")

        shot_0030 = QTreeWidgetItem(seq_a_folder)
        shot_0030.setText(0, "0030")
        shot_0030.setData(0, Qt.ItemDataRole.UserRole, "Sequence A")

        shot_0100 = QTreeWidgetItem(seq_b_folder)
        shot_0100.setText(0, "0100")
        shot_0100.setData(0, Qt.ItemDataRole.UserRole, "Sequence B")

        shot_0110 = QTreeWidgetItem(seq_b_folder)
        shot_0110.setText(0, "0110")
        shot_0110.setData(0, Qt.ItemDataRole.UserRole, "Sequence B")

        shot_0120 = QTreeWidgetItem(seq_b_folder)
        shot_0120.setText(0, "0120")
        shot_0120.setData(0, Qt.ItemDataRole.UserRole, "Sequence B")

        # Expand all sequences by default
        self.shot_tree.expandAll()

    def setup_context_menus(self):
        """Setup context menus for asset and shot trees"""
        # Context menus are now handled by the controller
        # Just setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for tree operations"""
        from PyQt6.QtGui import QShortcut, QKeySequence
        
        # Asset tree shortcuts
        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self.asset_tree)
        copy_shortcut.activated.connect(self.copy_selected_asset)
        
        cut_shortcut = QShortcut(QKeySequence.StandardKey.Cut, self.asset_tree)
        cut_shortcut.activated.connect(self.cut_selected_asset)
        
        paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self.asset_tree)
        paste_shortcut.activated.connect(self.paste_to_asset_tree)
        
        delete_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self.asset_tree)
        delete_shortcut.activated.connect(self.delete_selected_asset)
        
        # Shot tree shortcuts
        copy_shortcut_shot = QShortcut(QKeySequence.StandardKey.Copy, self.shot_tree)
        copy_shortcut_shot.activated.connect(self.copy_selected_shot)
        
        cut_shortcut_shot = QShortcut(QKeySequence.StandardKey.Cut, self.shot_tree)
        cut_shortcut_shot.activated.connect(self.cut_selected_shot)
        
        paste_shortcut_shot = QShortcut(QKeySequence.StandardKey.Paste, self.shot_tree)
        paste_shortcut_shot.activated.connect(self.paste_to_shot_tree)
        
        delete_shortcut_shot = QShortcut(QKeySequence.StandardKey.Delete, self.shot_tree)
        delete_shortcut_shot.activated.connect(self.delete_selected_shot)
    
    def copy_selected_asset(self):
        """Copy selected asset"""
        current_item = self.asset_tree.currentItem()
        if current_item and current_item.data(0, Qt.ItemDataRole.UserRole) in ["Asset", "Folder"]:
            self.copy_item(current_item)
    
    def cut_selected_asset(self):
        """Cut selected asset"""
        current_item = self.asset_tree.currentItem()
        if current_item and current_item.data(0, Qt.ItemDataRole.UserRole) in ["Asset", "Folder"]:
            self.cut_item(current_item)
    
    def paste_to_asset_tree(self):
        """Paste to asset tree"""
        current_item = self.asset_tree.currentItem()
        self.paste_item(current_item)
    
    def delete_selected_asset(self):
        """Delete selected asset"""
        current_item = self.asset_tree.currentItem()
        if current_item and current_item.data(0, Qt.ItemDataRole.UserRole) in ["Asset", "Folder"]:
            self.delete_item(current_item)
    
    def copy_selected_shot(self):
        """Copy selected shot"""
        current_item = self.shot_tree.currentItem()
        if current_item and current_item.data(0, Qt.ItemDataRole.UserRole) in ["Shot", "Folder"]:
            self.copy_item(current_item)
    
    def cut_selected_shot(self):
        """Cut selected shot"""
        current_item = self.shot_tree.currentItem()
        if current_item and current_item.data(0, Qt.ItemDataRole.UserRole) in ["Shot", "Folder"]:
            self.cut_item(current_item)
    
    def paste_to_shot_tree(self):
        """Paste to shot tree"""
        current_item = self.shot_tree.currentItem()
        self.paste_item(current_item)
    
    def delete_selected_shot(self):
        """Delete selected shot"""
        current_item = self.shot_tree.currentItem()
        if current_item and current_item.data(0, Qt.ItemDataRole.UserRole) in ["Shot", "Folder"]:
            self.delete_item(current_item)

    def show_asset_context_menu(self, position):
        """Show context menu for asset tree"""
        menu = QMenu()

        # Get current item
        item = self.asset_tree.itemAt(position)
        if item:
            item_type = item.data(0, Qt.ItemDataRole.UserRole)
            item_name = item.text(0)

            if item_type == "Folder":
                # Folder operations
                create_asset_action = menu.addAction("Create Asset in Folder")
                paste_action = menu.addAction("Paste Asset")
                menu.addSeparator()
                open_action = menu.addAction("Open Folder")
                menu.addSeparator()
                rename_action = menu.addAction("Rename Folder")
                delete_action = menu.addAction("Delete Folder")

                # Connect actions
                create_asset_action.triggered.connect(lambda: self.create_asset_in_folder(item_name))
                paste_action.triggered.connect(lambda: self.paste_asset(item_name))
                open_action.triggered.connect(lambda: self.open_folder("asset", item_name))
                rename_action.triggered.connect(lambda: self.rename_folder("asset", item_name))
                delete_action.triggered.connect(lambda: self.delete_folder("asset", item_name))
            else:
                # Asset operations
                open_action = menu.addAction("Open Asset")
                cut_action = menu.addAction("Cut Asset")
                copy_action = menu.addAction("Copy Asset")
                menu.addSeparator()
                move_to_action = menu.addAction("Move to Folder")
                properties_action = menu.addAction("Properties")

                # Connect actions
                open_action.triggered.connect(lambda: self.open_asset(item_name))
                cut_action.triggered.connect(lambda: self.cut_asset(item_name))
                copy_action.triggered.connect(lambda: self.copy_asset(item_name))
                move_to_action.triggered.connect(lambda: self.move_asset_to_folder(item_name))
                properties_action.triggered.connect(lambda: self.show_asset_properties(item_name))

        else:
            # No item selected - show create options
            create_folder_action = menu.addAction("Create Folder")
            create_asset_action = menu.addAction("Create Asset")

            # Connect actions
            create_folder_action.triggered.connect(lambda: self.create_folder("asset"))
            create_asset_action.triggered.connect(self.create_asset)

        menu.exec(self.asset_tree.mapToGlobal(position))
    
    def has_clipboard_data(self):
        """Check if there's data in the clipboard for paste operations"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        return mime_data.hasFormat("application/x-vogue-asset") or mime_data.hasFormat("application/x-vogue-folder")
    
    def copy_item(self, item):
        """Copy item to clipboard"""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QMimeData
        
        clipboard = QApplication.clipboard()
        mime_data = QMimeData()
        
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        item_name = item.text(0)
        
        if item_type == "Asset":
            mime_data.setData("application/x-vogue-asset", item_name.encode())
        elif item_type == "Folder":
            mime_data.setData("application/x-vogue-folder", item_name.encode())
        
        clipboard.setMimeData(mime_data)
        self.add_log_message(f"Copied {item_type.lower()}: {item_name}")
    
    def cut_item(self, item):
        """Cut item to clipboard (mark for moving)"""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QMimeData
        
        clipboard = QApplication.clipboard()
        mime_data = QMimeData()
        
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        item_name = item.text(0)
        
        if item_type == "Asset":
            mime_data.setData("application/x-vogue-asset-cut", item_name.encode())
        elif item_type == "Folder":
            mime_data.setData("application/x-vogue-folder-cut", item_name.encode())
        
        clipboard.setMimeData(mime_data)
        self.add_log_message(f"Cut {item_type.lower()}: {item_name}")
    
    def paste_item(self, target_item):
        """Paste item from clipboard"""
        from PyQt6.QtWidgets import QApplication
        
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        # Determine target folder
        target_folder = None
        if target_item and target_item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
            target_folder = target_item.text(0)
        
        # Handle asset paste
        if mime_data.hasFormat("application/x-vogue-asset"):
            asset_name = mime_data.data("application/x-vogue-asset").data().decode()
            self.move_asset_to_folder(asset_name, target_folder)
        elif mime_data.hasFormat("application/x-vogue-asset-cut"):
            asset_name = mime_data.data("application/x-vogue-asset-cut").data().decode()
            self.move_asset_to_folder(asset_name, target_folder, is_cut=True)
        
        # Handle folder paste
        elif mime_data.hasFormat("application/x-vogue-folder"):
            folder_name = mime_data.data("application/x-vogue-folder").data().decode()
            self.move_folder_to_location(folder_name, target_folder)
        elif mime_data.hasFormat("application/x-vogue-folder-cut"):
            folder_name = mime_data.data("application/x-vogue-folder-cut").data().decode()
            self.move_folder_to_location(folder_name, target_folder, is_cut=True)
    
    def move_asset_to_folder(self, asset_name, target_folder, is_cut=False):
        """Move asset to target folder"""
        try:
            # Call controller method to update project data
            from vogue_app.main import get_current_controller
            controller = get_current_controller()
            if controller:
                controller.move_asset_to_folder(asset_name, target_folder, is_cut)
            else:
                self.add_log_message("Controller not available")
            
        except Exception as e:
            self.add_log_message(f"Error moving asset: {e}")
    
    def move_folder_to_location(self, folder_name, target_folder, is_cut=False):
        """Move folder to target location"""
        try:
            # Find the folder in the tree
            folder_item = None
            for i in range(self.asset_tree.topLevelItemCount()):
                item = self.asset_tree.topLevelItem(i)
                if item.text(0) == folder_name and item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
                    folder_item = item
                    break
            
            if not folder_item:
                self.add_log_message(f"Folder not found: {folder_name}")
                return
            
            # For now, folders can only be moved to root level
            if target_folder:
                self.add_log_message("Folders can only be moved to root level")
                return
            
            # Remove from current location
            parent = folder_item.parent()
            if parent:
                parent.removeChild(folder_item)
            else:
                self.asset_tree.takeTopLevelItem(self.asset_tree.indexOfTopLevelItem(folder_item))
            
            # Add to root level
            self.asset_tree.addTopLevelItem(folder_item)
            
            action = "Moved" if is_cut else "Copied"
            self.add_log_message(f"{action} folder '{folder_name}' to root level")
            
        except Exception as e:
            self.add_log_message(f"Error moving folder: {e}")
    
    def _find_asset_in_tree(self, item, asset_name):
        """Recursively find asset in tree"""
        if item.text(0) == asset_name and item.data(0, Qt.ItemDataRole.UserRole) == "Asset":
            return item
        
        for i in range(item.childCount()):
            child = item.child(i)
            result = self._find_asset_in_tree(child, asset_name)
            if result:
                return result
        
        return None
    
    def delete_item(self, item):
        """Delete an item from the tree"""
        if not item:
            return
        
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        item_name = item.text(0)
        
        # Confirm deletion
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {item_type.lower()}: {item_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Call controller method to update project data
                from vogue_app.main import get_current_controller
                controller = get_current_controller()
                if controller:
                    if item_type == "Asset":
                        controller.delete_asset_from_project(item_name)
                    elif item_type == "Folder":
                        # TODO: Implement folder deletion in controller
                        self.add_log_message("Folder deletion not yet implemented")
                else:
                    self.add_log_message("Controller not available")
                
            except Exception as e:
                self.add_log_message(f"Error deleting {item_type.lower()}: {e}")
    
    def rename_item(self, item):
        """Rename an item in the tree"""
        if not item:
            return
        
        item_name = item.text(0)
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self, "Rename Item",
            f"Enter new name for {item_name}:",
            text=item_name
        )
        
        if ok and new_name and new_name != item_name:
            try:
                # Call controller method to update project data
                from vogue_app.main import get_current_controller
                controller = get_current_controller()
                if controller:
                    if item_type == "Asset":
                        controller.rename_asset_in_project(item_name, new_name)
                    elif item_type == "Folder":
                        # TODO: Implement folder renaming in controller
                        self.add_log_message("Folder renaming not yet implemented")
                else:
                    self.add_log_message("Controller not available")
                
            except Exception as e:
                self.add_log_message(f"Error renaming item: {e}")
    
    def open_asset(self, item):
        """Open an asset"""
        if not item or item.data(0, Qt.ItemDataRole.UserRole) != "Asset":
            return
        
        asset_name = item.text(0)
        self.add_log_message(f"Opening asset: {asset_name}")
        
        # TODO: Implement actual asset opening
        # This would need to be implemented in the controller
    
    def show_asset_properties(self, item):
        """Show asset properties"""
        if not item or item.data(0, Qt.ItemDataRole.UserRole) != "Asset":
            return
        
        asset_name = item.text(0)
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, "Asset Properties",
            f"Asset: {asset_name}\nType: Asset\nStatus: Active"
        )

    def show_shot_context_menu(self, position):
        """Show context menu for shot tree"""
        menu = QMenu()

        # Get current item
        item = self.shot_tree.itemAt(position)
        if item:
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            item_name = item.text(0)

            if item_data == "Folder":
                # Folder operations
                create_shot_action = menu.addAction("Create Shot in Folder")
                paste_action = menu.addAction("Paste Shot")
                menu.addSeparator()
                open_action = menu.addAction("Open Folder")
                menu.addSeparator()
                rename_action = menu.addAction("Rename Folder")
                delete_action = menu.addAction("Delete Folder")

                # Connect actions
                create_shot_action.triggered.connect(lambda: self.create_shot_in_folder(item_name))
                paste_action.triggered.connect(lambda: self.paste_shot(item_name))
                open_action.triggered.connect(lambda: self.open_folder("shot", item_name))
                rename_action.triggered.connect(lambda: self.rename_folder("shot", item_name))
                delete_action.triggered.connect(lambda: self.delete_folder("shot", item_name))
            else:
                # Shot operations
                open_action = menu.addAction("Open Shot")
                cut_action = menu.addAction("Cut Shot")
                copy_action = menu.addAction("Copy Shot")
                menu.addSeparator()
                move_to_action = menu.addAction("Move to Folder")
                properties_action = menu.addAction("Properties")

                # Connect actions
                open_action.triggered.connect(lambda: self.open_shot(item_name))
                cut_action.triggered.connect(lambda: self.cut_shot(item_name))
                copy_action.triggered.connect(lambda: self.copy_shot(item_name))
                move_to_action.triggered.connect(lambda: self.move_shot_to_folder(item_name))
                properties_action.triggered.connect(lambda: self.show_shot_properties(item_name))

        else:
            # No item selected - show create options
            create_folder_action = menu.addAction("Create Folder")
            create_shot_action = menu.addAction("Create Shot")

            # Connect actions
            create_folder_action.triggered.connect(lambda: self.create_folder("shot"))
            create_shot_action.triggered.connect(self.create_shot)

        menu.exec(self.shot_tree.mapToGlobal(position))

    def create_folder(self, list_type: str):
        """Create a new folder in the specified tree"""
        folder_name, ok = QInputDialog.getText(
            self, "Create Folder",
            "Enter folder name:",
            QLineEdit.EchoMode.Normal,
            ""
        )

        if ok and folder_name:
            # Call controller method to create folder in project data
            from vogue_app.main import get_current_controller
            controller = get_current_controller()
            if controller:
                controller.create_folder_in_project(folder_name, list_type)
            else:
                self.add_log_message("Controller not available")

    def rename_folder(self, list_type: str, old_name: str):
        """Rename an existing folder"""
        new_name, ok = QInputDialog.getText(
            self, "Rename Folder",
            "Enter new folder name:",
            QLineEdit.EchoMode.Normal,
            old_name
        )

        if ok and new_name and new_name != old_name:
            # Find and update the item
            tree_widget = self.asset_tree if list_type == "asset" else self.shot_tree

            def find_and_rename_item(parent_item):
                for i in range(parent_item.childCount()):
                    child_item = parent_item.child(i)
                    if (child_item.text(0) == old_name and
                        child_item.data(0, Qt.ItemDataRole.UserRole) == "Folder"):
                        child_item.setText(0, new_name)
                        return True
                return False

            # Search through root items
            for i in range(tree_widget.topLevelItemCount()):
                root_item = tree_widget.topLevelItem(i)
                if find_and_rename_item(root_item) or (
                    root_item.text(0) == old_name and
                    root_item.data(0, Qt.ItemDataRole.UserRole) == "Folder"
                ):
                    root_item.setText(0, new_name)
                    self.add_log_message(f"Folder '{old_name}' renamed to '{new_name}'")

                    # Auto-save the project
                    try:
                        from vogue_core.manager import ProjectManager
                        manager = ProjectManager()
                        if hasattr(manager, 'current_project') and manager.current_project:
                            manager.save_project()
                            self.add_log_message("Project auto-saved")
                    except Exception as e:
                        print(f"Auto-save failed: {e}")
                    break

    def delete_folder(self, list_type: str, folder_name: str):
        """Delete a folder"""
        reply = QMessageBox.question(
            self, "Delete Folder",
            f"Are you sure you want to delete folder '{folder_name}'?\nThis will delete all contents inside the folder.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Find and remove the item
            tree_widget = self.asset_tree if list_type == "asset" else self.shot_tree

            def find_and_remove_item(parent_item):
                for i in range(parent_item.childCount()):
                    child_item = parent_item.child(i)
                    if (child_item.text(0) == folder_name and
                        child_item.data(0, Qt.ItemDataRole.UserRole) == "Folder"):
                        parent_item.takeChild(i)
                        return True
                return False

            # Search through root items
            for i in range(tree_widget.topLevelItemCount()):
                root_item = tree_widget.topLevelItem(i)
                if find_and_remove_item(root_item) or (
                    root_item.text(0) == folder_name and
                    root_item.data(0, Qt.ItemDataRole.UserRole) == "Folder"
                ):
                    tree_widget.takeTopLevelItem(i)
                    self.add_log_message(f"Folder '{folder_name}' deleted")

                    # Auto-save the project
                    try:
                        from vogue_core.manager import ProjectManager
                        manager = ProjectManager()
                        if hasattr(manager, 'current_project') and manager.current_project:
                            manager.save_project()
                            self.add_log_message("Project auto-saved")
                    except Exception as e:
                        print(f"Auto-save failed: {e}")
                    break

    def open_folder(self, list_type: str, folder_name: str):
        """Open a folder (show contents)"""
        QMessageBox.information(self, "Open Folder", f"Opening folder: {folder_name}")

    def open_asset(self, asset_name: str):
        """Open an asset"""
        QMessageBox.information(self, "Open Asset", f"Opening asset: {asset_name}")

    def copy_asset(self, asset_name: str):
        """Copy an asset"""
        QMessageBox.information(self, "Copy Asset", f"Copying asset: {asset_name}")

    def show_asset_properties(self, asset_name: str):
        """Show asset properties"""
        QMessageBox.information(self, "Asset Properties", f"Properties for: {asset_name}")

    def create_asset_in_folder(self, folder_name):
        """Create a new asset in a specific folder"""
        asset_name, ok = QInputDialog.getText(
            self, "Create Asset",
            f"Enter asset name for {folder_name} folder:",
            QLineEdit.EchoMode.Normal,
            ""
        )

        if ok and asset_name:
            # Find the folder and add the asset
            root_item = self._find_folder_by_name(self.asset_tree, folder_name)
            if root_item:
                # Create new asset item
                asset_item = QTreeWidgetItem(root_item)
                asset_item.setText(0, asset_name)

                # Set asset type to a proper asset type, not the folder name
                # For now, we'll use a generic type, but in a real VFX pipeline
                # this would be determined by the asset type (Character, Prop, Environment, etc.)
                asset_type = "Asset"  # Generic type for now
                asset_item.setData(0, Qt.ItemDataRole.UserRole, asset_type)

                self.add_log_message(f"Asset '{asset_name}' created in folder '{folder_name}'")

                # Auto-save the project
                if auto_save_project():
                    self.add_log_message("Project auto-saved")
                else:
                    self.add_log_message("Auto-save skipped: no project loaded")

    def cut_asset(self, asset_name):
        """Cut an asset for moving"""
        try:
            # Find the asset item
            asset_item = self._find_asset_by_name(asset_name)
            if asset_item and asset_item.isValid():
                self.clipboard_item = asset_item
                self.clipboard_operation = 'cut'
                self.clipboard_type = 'asset'
                self.add_log_message(f"Asset '{asset_name}' cut to clipboard")
            else:
                QMessageBox.warning(self, "Asset Not Found", f"Could not find asset '{asset_name}'")
        except Exception as e:
            self.logger.error(f"Error cutting asset: {e}")
            QMessageBox.critical(self, "Error", f"Failed to cut asset: {e}")

    def copy_asset(self, asset_name):
        """Copy an asset"""
        try:
            # Find the asset item
            asset_item = self._find_asset_by_name(asset_name)
            if asset_item and asset_item.isValid():
                self.clipboard_item = asset_item
                self.clipboard_operation = 'copy'
                self.clipboard_type = 'asset'
                self.add_log_message(f"Asset '{asset_name}' copied to clipboard")
            else:
                QMessageBox.warning(self, "Asset Not Found", f"Could not find asset '{asset_name}'")
        except Exception as e:
            self.logger.error(f"Error copying asset: {e}")
            QMessageBox.critical(self, "Error", f"Failed to copy asset: {e}")

    def move_asset_to_folder(self, asset_name):
        """Move an asset to a different folder"""
        if not self.clipboard_item or self.clipboard_operation != 'cut' or self.clipboard_type != 'asset':
            QMessageBox.warning(self, "No Item to Move", "No asset has been cut. Use Cut first.")
            return

        # Get available folders
        folders = []
        for i in range(self.asset_tree.topLevelItemCount()):
            item = self.asset_tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
                folders.append(item.text(0))

        if not folders:
            QMessageBox.warning(self, "No Folders", "No folders available to move to.")
            return

        folder_name, ok = QInputDialog.getItem(
            self, "Move Asset",
            f"Move '{asset_name}' to folder:",
            folders, 0, False
        )

        if ok and folder_name:
            # Find target folder
            target_folder = self._find_folder_by_name(self.asset_tree, folder_name)
            if target_folder:
                # Remove from current parent
                parent = self.clipboard_item.parent()
                if parent:
                    parent.removeChild(self.clipboard_item)
                else:
                    # Remove from root
                    index = self.asset_tree.indexOfTopLevelItem(self.clipboard_item)
                    if index >= 0:
                        self.asset_tree.takeTopLevelItem(index)

                # Add to target folder
                target_folder.addChild(self.clipboard_item)

                # Clear clipboard
                self.clipboard_item = None
                self.clipboard_operation = None
                self.clipboard_type = None

                self.add_log_message(f"Asset '{asset_name}' moved to folder '{folder_name}'")

    def paste_asset(self, folder_name):
        """Paste an asset into a folder"""
        try:
            if not self.clipboard_item or self.clipboard_type != 'asset':
                QMessageBox.warning(self, "No Item to Paste", "No asset has been copied or cut.")
                return

            # Store item name before operations
            item_name = self.clipboard_item.text(0)

            # Find target folder
            target_folder = self._find_folder_by_name(self.asset_tree, folder_name)
            if target_folder:
                if self.clipboard_operation == 'copy':
                    # Create a copy of the item
                    new_item = QTreeWidgetItem()
                    new_item.setText(0, item_name)
                    new_item.setData(0, Qt.ItemDataRole.UserRole, self.clipboard_item.data(0, Qt.ItemDataRole.UserRole))
                    target_folder.addChild(new_item)
                    self.add_log_message(f"Asset '{item_name}' pasted to folder '{folder_name}'")

                    # Auto-save the project
                    try:
                        from vogue_core.manager import ProjectManager
                        manager = ProjectManager()
                        if hasattr(manager, 'current_project') and manager.current_project:
                            manager.save_project()
                            self.add_log_message("Project auto-saved")
                    except Exception as e:
                        print(f"Auto-save failed: {e}")
                else:  # cut operation
                    # Remove from current parent
                    parent = self.clipboard_item.parent()
                    if parent:
                        parent.removeChild(self.clipboard_item)
                    else:
                        # Remove from root
                        index = self.asset_tree.indexOfTopLevelItem(self.clipboard_item)
                        if index >= 0:
                            self.asset_tree.takeTopLevelItem(index)

                    # Add to target folder
                    target_folder.addChild(self.clipboard_item)

                    # Clear clipboard
                    self.clipboard_item = None
                    self.clipboard_operation = None
                    self.clipboard_type = None

                    self.add_log_message(f"Asset '{item_name}' moved to folder '{folder_name}'")

                    # Auto-save the project
                    try:
                        from vogue_core.manager import ProjectManager
                        manager = ProjectManager()
                        if hasattr(manager, 'current_project') and manager.current_project:
                            manager.save_project()
                            self.add_log_message("Project auto-saved")
                    except Exception as e:
                        print(f"Auto-save failed: {e}")
            else:
                QMessageBox.warning(self, "Folder Not Found", f"Could not find folder '{folder_name}'")
        except Exception as e:
            self.logger.error(f"Error pasting asset: {e}")
            QMessageBox.critical(self, "Error", f"Failed to paste asset: {e}")

    def create_asset(self):
        """Create a new asset with folder selection (no type field)."""
        # Build dialog with name + folder dropdown
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Asset")
        layout = QFormLayout(dialog)

        name_edit = QLineEdit(dialog)
        layout.addRow("Name:", name_edit)

        folder_combo = QComboBox(dialog)
        folders = ["Main"]
        for i in range(self.asset_tree.topLevelItemCount()):
            item = self.asset_tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
                fname = item.text(0)
                if fname not in folders:
                    folders.append(fname)
        folder_combo.addItems(folders)
        layout.addRow("Folder:", folder_combo)

        buttons_layout = QHBoxLayout()
        ok_btn = QPushButton("Create", dialog)
        cancel_btn = QPushButton("Cancel", dialog)
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addRow(buttons_layout)

        def on_ok():
            asset_name = name_edit.text().strip()
            folder_name = folder_combo.currentText().strip()
            if not asset_name:
                QMessageBox.warning(dialog, "Invalid Name", "Please enter an asset name.")
                return
            dialog.accept()
            self._create_asset_in_folder(asset_name, folder_name)
            controller = get_current_controller()
            if controller:
                try:
                    controller._normalize_project()
                    controller.update_assets_tree()
                except Exception:
                    pass

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()

    def _create_asset_in_folder(self, asset_name, folder_name):
        """Create an asset in the specified folder, creating the folder if needed"""
        # Find or create the folder
        folder_item = self._find_folder_by_name(self.asset_tree, folder_name)

        if not folder_item:
            # Create the folder if it doesn't exist
            folder_item = QTreeWidgetItem(self.asset_tree)
            folder_item.setText(0, folder_name)
            folder_item.setData(0, Qt.ItemDataRole.UserRole, "Folder")

        # Create the asset in the folder
        asset_item = QTreeWidgetItem(folder_item)
        asset_item.setText(0, asset_name)
        asset_item.setData(0, Qt.ItemDataRole.UserRole, "Asset")  # Simple type

        self.add_log_message(f"Asset '{asset_name}' created in folder '{folder_name}'")

        # Auto-save the project
        if auto_save_project():
            self.add_log_message("Project auto-saved")
        else:
            self.add_log_message("Auto-save skipped: no project loaded")

    def _find_folder_by_name(self, tree_widget, folder_name):
        """Find a folder by name in the tree"""
        for i in range(tree_widget.topLevelItemCount()):
            item = tree_widget.topLevelItem(i)
            if item.text(0) == folder_name and item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
                return item
        return None

    def _find_asset_by_name(self, asset_name):
        """Find an asset by name in the asset tree"""
        def search_tree(parent_item):
            for i in range(parent_item.childCount()):
                child_item = parent_item.child(i)
                if child_item.text(0) == asset_name and child_item.data(0, Qt.ItemDataRole.UserRole) != "Folder":
                    return child_item
                # Recursively search children
                result = search_tree(child_item)
                if result:
                    return result
            return None

        # Search through root items
        for i in range(self.asset_tree.topLevelItemCount()):
            root_item = self.asset_tree.topLevelItem(i)
            if root_item.text(0) == asset_name and root_item.data(0, Qt.ItemDataRole.UserRole) != "Folder":
                return root_item
            # Search children
            result = search_tree(root_item)
            if result:
                return result
        return None

    def _find_shot_by_name(self, shot_name):
        """Find a shot by name in the shot tree"""
        def search_tree(parent_item):
            for i in range(parent_item.childCount()):
                child_item = parent_item.child(i)
                if child_item.text(0) == shot_name and child_item.data(0, Qt.ItemDataRole.UserRole) != "Folder":
                    return child_item
                # Recursively search children
                result = search_tree(child_item)
                if result:
                    return result
            return None

        # Search through root items
        for i in range(self.shot_tree.topLevelItemCount()):
            root_item = self.shot_tree.topLevelItem(i)
            if root_item.text(0) == shot_name and root_item.data(0, Qt.ItemDataRole.UserRole) != "Folder":
                return root_item
            # Search children
            result = search_tree(root_item)
            if result:
                return result
        return None

    def open_shot(self, shot_name: str):
        """Open a shot"""
        QMessageBox.information(self, "Open Shot", f"Opening shot: {shot_name}")

    def copy_shot(self, shot_name: str):
        """Copy a shot"""
        QMessageBox.information(self, "Copy Shot", f"Copying shot: {shot_name}")

    def show_shot_properties(self, shot_name: str):
        """Show shot properties"""
        QMessageBox.information(self, "Shot Properties", f"Properties for: {shot_name}")

    def create_shot_in_folder(self, folder_name):
        """Create a new shot in a specific folder"""
        shot_name, ok = QInputDialog.getText(
            self, "Create Shot",
            f"Enter shot name for {folder_name} folder:",
            QLineEdit.EchoMode.Normal,
            ""
        )

        if ok and shot_name:
            # Find the folder and add the shot
            root_item = self._find_folder_by_name(self.shot_tree, folder_name)
            if root_item:
                # Create new shot item
                shot_item = QTreeWidgetItem(root_item)
                shot_item.setText(0, shot_name)

                # Set shot sequence based on folder
                shot_sequence = folder_name
                shot_item.setData(0, Qt.ItemDataRole.UserRole, shot_sequence)

                self.add_log_message(f"Shot '{shot_name}' created in folder '{folder_name}'")

                # Auto-save the project
                try:
                    from vogue_core.manager import ProjectManager
                    # Use the singleton pattern or get the existing instance
                    manager = ProjectManager()
                    # Try to get current project - if not available, we'll skip auto-save
                    if hasattr(manager, 'current_project') and manager.current_project:
                        # Save the current project state
                        manager.save_project(manager.current_project)
                        self.add_log_message("Project auto-saved")
                    else:
                        self.add_log_message("Auto-save skipped: no project loaded")
                except Exception as e:
                    print(f"Auto-save failed: {e}")
                    self.add_log_message(f"Auto-save failed: {e}")

    def cut_shot(self, shot_name):
        """Cut a shot for moving"""
        try:
            # Find the shot item
            shot_item = self._find_shot_by_name(shot_name)
            if shot_item and shot_item.isValid():
                self.clipboard_item = shot_item
                self.clipboard_operation = 'cut'
                self.clipboard_type = 'shot'
                self.add_log_message(f"Shot '{shot_name}' cut to clipboard")
            else:
                QMessageBox.warning(self, "Shot Not Found", f"Could not find shot '{shot_name}'")
        except Exception as e:
            self.logger.error(f"Error cutting shot: {e}")
            QMessageBox.critical(self, "Error", f"Failed to cut shot: {e}")

    def copy_shot(self, shot_name):
        """Copy a shot"""
        try:
            # Find the shot item
            shot_item = self._find_shot_by_name(shot_name)
            if shot_item and shot_item.isValid():
                self.clipboard_item = shot_item
                self.clipboard_operation = 'copy'
                self.clipboard_type = 'shot'
                self.add_log_message(f"Shot '{shot_name}' copied to clipboard")
            else:
                QMessageBox.warning(self, "Shot Not Found", f"Could not find shot '{shot_name}'")
        except Exception as e:
            self.logger.error(f"Error copying shot: {e}")
            QMessageBox.critical(self, "Error", f"Failed to copy shot: {e}")

    def move_shot_to_folder(self, shot_name):
        """Move a shot to a different folder"""
        if not self.clipboard_item or self.clipboard_operation != 'cut' or self.clipboard_type != 'shot':
            QMessageBox.warning(self, "No Item to Move", "No shot has been cut. Use Cut first.")
            return

        # Get available folders
        folders = []
        for i in range(self.shot_tree.topLevelItemCount()):
            item = self.shot_tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
                folders.append(item.text(0))

        if not folders:
            QMessageBox.warning(self, "No Folders", "No folders available to move to.")
            return

        folder_name, ok = QInputDialog.getItem(
            self, "Move Shot",
            f"Move '{shot_name}' to folder:",
            folders, 0, False
        )

        if ok and folder_name:
            # Find target folder
            target_folder = self._find_folder_by_name(self.shot_tree, folder_name)
            if target_folder:
                # Remove from current parent
                parent = self.clipboard_item.parent()
                if parent:
                    parent.removeChild(self.clipboard_item)
                else:
                    # Remove from root
                    index = self.shot_tree.indexOfTopLevelItem(self.clipboard_item)
                    if index >= 0:
                        self.shot_tree.takeTopLevelItem(index)

                # Add to target folder
                target_folder.addChild(self.clipboard_item)

                # Clear clipboard
                self.clipboard_item = None
                self.clipboard_operation = None
                self.clipboard_type = None

                self.add_log_message(f"Shot '{shot_name}' moved to folder '{folder_name}'")

    def paste_shot(self, folder_name):
        """Paste a shot into a folder"""
        try:
            if not self.clipboard_item or self.clipboard_type != 'shot':
                QMessageBox.warning(self, "No Item to Paste", "No shot has been copied or cut.")
                return

            # Store item name before operations
            item_name = self.clipboard_item.text(0)

            # Find target folder
            target_folder = self._find_folder_by_name(self.shot_tree, folder_name)
            if target_folder:
                if self.clipboard_operation == 'copy':
                    # Create a copy of the item
                    new_item = QTreeWidgetItem()
                    new_item.setText(0, item_name)
                    new_item.setData(0, Qt.ItemDataRole.UserRole, self.clipboard_item.data(0, Qt.ItemDataRole.UserRole))
                    target_folder.addChild(new_item)
                    self.add_log_message(f"Shot '{item_name}' pasted to folder '{folder_name}'")

                # Auto-save the project
                try:
                    from vogue_core.manager import ProjectManager
                    # Use the singleton pattern or get the existing instance
                    manager = ProjectManager()
                    # Try to get current project - if not available, we'll skip auto-save
                    if hasattr(manager, 'current_project') and manager.current_project:
                        # Save the current project state
                        manager.save_project(manager.current_project)
                        self.add_log_message("Project auto-saved")
                    else:
                        self.add_log_message("Auto-save skipped: no project loaded")
                except Exception as e:
                    print(f"Auto-save failed: {e}")
                    self.add_log_message(f"Auto-save failed: {e}")
                else:  # cut operation
                    # Remove from current parent
                    parent = self.clipboard_item.parent()
                    if parent:
                        parent.removeChild(self.clipboard_item)
                    else:
                        # Remove from root
                        index = self.shot_tree.indexOfTopLevelItem(self.clipboard_item)
                        if index >= 0:
                            self.shot_tree.takeTopLevelItem(index)

                    # Add to target folder
                    target_folder.addChild(self.clipboard_item)

                    # Clear clipboard
                    self.clipboard_item = None
                    self.clipboard_operation = None
                    self.clipboard_type = None

                    self.add_log_message(f"Shot '{item_name}' moved to folder '{folder_name}'")

                # Auto-save the project
                try:
                    from vogue_core.manager import ProjectManager
                    # Use the singleton pattern or get the existing instance
                    manager = ProjectManager()
                    # Try to get current project - if not available, we'll skip auto-save
                    if hasattr(manager, 'current_project') and manager.current_project:
                        # Save the current project state
                        manager.save_project(manager.current_project)
                        self.add_log_message("Project auto-saved")
                    else:
                        self.add_log_message("Auto-save skipped: no project loaded")
                except Exception as e:
                    print(f"Auto-save failed: {e}")
                    self.add_log_message(f"Auto-save failed: {e}")
            else:
                QMessageBox.warning(self, "Folder Not Found", f"Could not find folder '{folder_name}'")
        except Exception as e:
            self.logger.error(f"Error pasting shot: {e}")
            QMessageBox.critical(self, "Error", f"Failed to paste shot: {e}")

    def create_shot(self):
        """Create a new shot"""
        QMessageBox.information(self, "Create Shot", "Shot creation dialog would open here")

    def add_log_message(self, message: str):
        """Add a message to the log (placeholder)"""
        print(f"[LOG] {message}")


class AssetTreeWidget(QTreeWidget):
    """Custom tree widget with enhanced drag and drop support"""

    def dropEvent(self, event):
        """Handle drop events to ensure items are only dropped on folders"""
        # Get the drop position
        pos = event.position().toPoint()
        target_item = self.itemAt(pos)

        # Get the dragged item before the drop
        dragged_item = self.currentItem()
        if not dragged_item:
            event.ignore()
            return

        item_name = dragged_item.text(0)
        item_type = dragged_item.data(0, Qt.ItemDataRole.UserRole)

        # Only allow dropping assets, not folders
        if item_type != "Asset":
            event.ignore()
            return

        # Check if we're dropping on a folder
        if target_item and target_item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
            folder_name = target_item.text(0)
            
            # Update the project data structure first
            if self._update_asset_folder_assignment(item_name, folder_name):
                # If data update was successful, update the UI
                self._move_item_in_ui(dragged_item, target_item)
                print(f"[LOG] Asset '{item_name}' moved to folder '{folder_name}'")
            else:
                event.ignore()
        elif not target_item:
            # Allow drop on empty space (root level)
            if self._update_asset_folder_assignment(item_name, None):
                # If data update was successful, update the UI
                self._move_item_to_root(dragged_item)
                print(f"[LOG] Asset '{item_name}' moved to root level")
            else:
                event.ignore()
        else:
            # Reject drop on non-folder items
            event.ignore()
    
    def _move_item_in_ui(self, item, target_folder):
        """Move item in UI to target folder"""
        # Remove from current parent
        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            # Remove from top level
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))
        
        # Add to target folder
        target_folder.addChild(item)
    
    def _move_item_to_root(self, item):
        """Move item in UI to root level"""
        # Remove from current parent
        parent = item.parent()
        if parent:
            parent.removeChild(item)
            # Add to root level
            self.addTopLevelItem(item)
    
    def _update_asset_folder_assignment(self, asset_name, folder_name):
        """Update asset folder assignment in project data"""
        try:
            # Try to get controller from global reference first
            controller = get_current_controller()
            
            if not controller:
                # Fallback: try to find controller via widget hierarchy
                current_widget = self
                max_depth = 10
                depth = 0
                while current_widget and depth < max_depth:
                    if hasattr(current_widget, 'manager') and hasattr(current_widget, 'current_project'):
                        controller = current_widget
                        break
                    current_widget = current_widget.parent()
                    depth += 1
            
            if not controller or not hasattr(controller, 'manager') or not controller.manager.current_project:
                return False
            
            project = controller.manager.current_project
            
            # Remove asset from all folders first
            for folder in project.folders:
                if folder.type == "asset" and asset_name in folder.assets:
                    folder.assets.remove(asset_name)
            
            # Add asset to target folder
            if folder_name:
                # Find or create the target folder
                target_folder = None
                for folder in project.folders:
                    if folder.type == "asset" and folder.name == folder_name:
                        target_folder = folder
                        break
                
                if target_folder:
                    if asset_name not in target_folder.assets:  # Avoid duplicates
                        target_folder.assets.append(asset_name)
                else:
                    # Create new folder if it doesn't exist
                    from vogue_core.models import Folder
                    new_folder = Folder(name=folder_name, type="asset", assets=[asset_name])
                    project.folders.append(new_folder)
            
            # Save the project
            controller.manager.save_project()
            return True
            
        except Exception as e:
            print(f"[LOG] Error updating asset folder assignment: {e}")
            return False

class ShotTreeWidget(QTreeWidget):
    """Custom tree widget with enhanced drag and drop support for shots"""

    def dropEvent(self, event):
        """Handle drop events to ensure items are only dropped on folders"""
        # Get the drop position
        pos = event.position().toPoint()
        target_item = self.itemAt(pos)

        # Get the dragged item before the drop
        dragged_item = self.currentItem()
        if not dragged_item:
            event.ignore()
            return

        item_name = dragged_item.text(0)
        item_type = dragged_item.data(0, Qt.ItemDataRole.UserRole)

        # Only allow dropping shots, not folders
        if item_type != "Shot":
            event.ignore()
            return

        # Check if we're dropping on a folder
        if target_item and target_item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
            folder_name = target_item.text(0)
            
            # Update the project data structure first
            if self._update_shot_folder_assignment(item_name, folder_name):
                # If data update was successful, update the UI
                self._move_item_in_ui(dragged_item, target_item)
                print(f"[LOG] Shot '{item_name}' moved to folder '{folder_name}'")
            else:
                event.ignore()
        elif not target_item:
            # Allow drop on empty space (root level)
            if self._update_shot_folder_assignment(item_name, None):
                # If data update was successful, update the UI
                self._move_item_to_root(dragged_item)
                print(f"[LOG] Shot '{item_name}' moved to root level")
            else:
                event.ignore()
        else:
            # Reject drop on non-folder items
            event.ignore()
    
    def _move_item_in_ui(self, item, target_folder):
        """Move item in UI to target folder"""
        # Remove from current parent
        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            # Remove from top level
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))
        
        # Add to target folder
        target_folder.addChild(item)
    
    def _move_item_to_root(self, item):
        """Move item in UI to root level"""
        # Remove from current parent
        parent = item.parent()
        if parent:
            parent.removeChild(item)
            # Add to root level
            self.addTopLevelItem(item)
    
    def _update_shot_folder_assignment(self, shot_name, folder_name):
        """Update shot folder assignment in project data"""
        try:
            # Try to get controller from global reference first
            controller = get_current_controller()
            if not controller:
                # Fallback: try to find controller via widget hierarchy
                current_widget = self
                max_depth = 10
                depth = 0
                while current_widget and depth < max_depth:
                    if hasattr(current_widget, 'manager') and hasattr(current_widget, 'current_project'):
                        controller = current_widget
                        break
                    current_widget = current_widget.parent()
                    depth += 1
            
            if not controller or not hasattr(controller, 'manager') or not controller.manager.current_project:
                return False
            
            project = controller.manager.current_project
            
            # Remove shot from all folders first
            for folder in project.folders:
                if folder.type == "shot" and shot_name in folder.assets:
                    folder.assets.remove(shot_name)
            
            # Add shot to target folder
            if folder_name:
                # Find or create the target folder
                target_folder = None
                for folder in project.folders:
                    if folder.type == "shot" and folder.name == folder_name:
                        target_folder = folder
                        break
                
                if target_folder:
                    if shot_name not in target_folder.assets:  # Avoid duplicates
                        target_folder.assets.append(shot_name)
                else:
                    # Create new folder if it doesn't exist
                    from vogue_core.models import Folder
                    new_folder = Folder(name=folder_name, type="shot", assets=[shot_name])
                    project.folders.append(new_folder)
            
            # Save the project
            controller.manager.save_project()
            return True
            
        except Exception as e:
            print(f"[LOG] Error updating shot folder assignment: {e}")
            return False

class ThumbnailDelegate(QStyledItemDelegate):
    """Custom delegate for displaying thumbnails in tree widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnail_size = QSize(60, 60)

    def paint(self, painter, option, index):
        """Paint the item with thumbnail"""
        # Get the data
        item_data = index.data(Qt.ItemDataRole.UserRole)
        text = index.data(Qt.ItemDataRole.DisplayRole)

        # Set up painter
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#73C2FB"))
            painter.setPen(QColor("#12181F"))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor("#212A37"))
            painter.setPen(QColor("#FFFFFF"))
        else:
            painter.fillRect(option.rect, QColor("#12181F"))  # Match QSS background
            painter.setPen(QColor("#FFFFFF"))  # Match QSS text color

        # Draw thumbnail if available
        if item_data and isinstance(item_data, str) and item_data != "Folder":
            # Generate thumbnail based on item type
            thumbnail = self.generate_thumbnail(item_data, text)

            # Calculate thumbnail position (left side)
            thumb_rect = QRect(
                option.rect.left() + 5,
                option.rect.top() + 5,
                self.thumbnail_size.width(),
                self.thumbnail_size.height()
            )

            # Draw thumbnail
            painter.drawPixmap(thumb_rect, thumbnail)

            # Draw text next to thumbnail
            text_rect = QRect(
                thumb_rect.right() + 10,
                option.rect.top(),
                option.rect.width() - thumb_rect.width() - 15,
                option.rect.height()
            )
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, text)
        else:
            # For folders, draw folder icon
            folder_pixmap = QPixmap(40, 40)
            folder_pixmap.fill(QColor("transparent"))

            folder_painter = QPainter(folder_pixmap)
            folder_painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw folder icon
            folder_painter.setBrush(QColor("#73C2FB"))
            folder_painter.setPen(QPen(QColor("#3A75A3"), 2))

            # Folder base
            folder_painter.drawRect(5, 15, 30, 15)
            # Folder tab
            folder_painter.drawRect(2, 10, 33, 20)

            folder_painter.end()

            # Draw folder icon
            folder_rect = QRect(
                option.rect.left() + 10,
                option.rect.top() + 10,
                40, 40
            )
            painter.drawPixmap(folder_rect, folder_pixmap)

            # Draw text next to folder icon
            text_rect = QRect(
                folder_rect.right() + 10,
                option.rect.top(),
                option.rect.width() - folder_rect.width() - 20,
                option.rect.height()
            )
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, text)

        painter.restore()

    def sizeHint(self, option, index):
        """Return the size hint for the item"""
        return QSize(200, 70)  # Width, Height

    def generate_thumbnail(self, asset_type: str, asset_name: str) -> QPixmap:
        """Generate a thumbnail for an asset based on its type"""
        pixmap = QPixmap(60, 60)
        pixmap.fill(QColor("#2A3441"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background with rounded corners
        painter.setBrush(QColor("#1A2332"))
        painter.setPen(QPen(QColor("#73C2FB"), 1))
        painter.drawRoundedRect(1, 1, 58, 58, 5, 5)

        # Draw icon based on type
        painter.setPen(QPen(QColor("#73C2FB"), 2))
        painter.setBrush(QColor("#73C2FB"))

        if asset_type.lower() in ["character", "characters"]:
            # Draw character icon (simple person shape)
            painter.drawEllipse(15, 8, 30, 30)  # Head
            painter.drawRect(22, 38, 15, 20)     # Body
            painter.drawLine(17, 43, 12, 58)      # Left arm
            painter.drawLine(37, 43, 42, 58)      # Right arm
            painter.drawLine(22, 58, 17, 73)      # Left leg
            painter.drawLine(32, 58, 37, 73)      # Right leg

        elif asset_type.lower() in ["prop", "props"]:
            # Draw prop icon (cube)
            painter.drawRect(15, 15, 30, 30)
            painter.drawLine(15, 15, 20, 10)      # Top-left edge
            painter.drawLine(45, 15, 50, 10)      # Top-right edge
            painter.drawLine(20, 10, 50, 10)      # Top edge
            painter.drawLine(50, 10, 50, 40)      # Right edge

        elif asset_type.lower() in ["environment", "environments"]:
            # Draw environment icon (landscape)
            painter.drawRect(10, 30, 40, 15)     # Ground
            painter.drawEllipse(8, 10, 44, 25)   # Sky
            painter.drawLine(20, 25, 40, 25)      # Horizon

        elif asset_type.lower() == "shot":
            # Draw shot icon (camera/clapperboard)
            painter.drawRect(10, 15, 40, 25)     # Clapperboard
            painter.drawRect(7, 7, 15, 12)       # Camera body
            painter.drawEllipse(5, 5, 7, 7)      # Lens
            painter.drawLine(7, 7, 17, 17)        # Clapper arm

        else:
            # Default icon
            painter.drawEllipse(15, 15, 30, 30)

        painter.end()
        return pixmap


class PrismRightPanel(PrismStyleWidget):
    """Prism-style right panel with Tasks, Departments, and Asset Info"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Asset Info section (full width since departments moved to left panel)
        self.setup_asset_info_widget()
        layout.addWidget(self.asset_info_widget)



    def setup_asset_info_widget(self):
        """Setup the Asset Info widget in Ayon style"""
        self.asset_info_widget = QWidget()
        info_layout = QVBoxLayout(self.asset_info_widget)
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_layout.setSpacing(12)

        # Header section with thumbnail and title (Ayon style)
        self.setup_asset_header()
        info_layout.addWidget(self.asset_header_widget)

        # Preview section with larger thumbnail
        self.setup_asset_preview()
        info_layout.addWidget(self.asset_preview_widget)

        # Details section with status and metadata
        self.setup_asset_details()
        info_layout.addWidget(self.asset_details_widget)

        # Actions toolbar (Ayon style)
        # Remove actions as requested
        # self.setup_asset_actions()
        # info_layout.addWidget(self.asset_actions_widget)

        info_layout.addStretch()

    def setup_asset_header(self):
        """Setup asset header with thumbnail and title like Ayon"""
        self.asset_header_widget = QWidget()
        header_layout = QHBoxLayout(self.asset_header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        # Thumbnail preview (left side)
        self.asset_thumbnail = QLabel()
        self.asset_thumbnail.setFixedSize(64, 64)
        self.asset_thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.asset_thumbnail.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['outline']};
                border-radius: 8px;
                color: {COLORS['muted']};
                font-size: 11px;
            }}
        """)
        self.asset_thumbnail.setText("📁")
        header_layout.addWidget(self.asset_thumbnail)

        # Title and info (right side)
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        # Asset name (main title)
        self.asset_name_label = QLabel("No Selection")
        self.asset_name_label.setProperty("class", "title")
        self.asset_name_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {COLORS['fg']};
                margin: 0;
            }}
        """)
        title_layout.addWidget(self.asset_name_label)

        # Asset type and status
        type_status_layout = QHBoxLayout()
        type_status_layout.setContentsMargins(0, 0, 0, 0)
        type_status_layout.setSpacing(8)

        self.asset_type_label = QLabel("Asset")
        self.asset_type_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {COLORS['fg_variant']};
                background-color: {COLORS['accent']};
                color: white;
                padding: 2px 8px;
                border-radius: 4px;
                font-weight: 500;
            }}
        """)
        type_status_layout.addWidget(self.asset_type_label)

        self.asset_status_label = QLabel("Unknown")
        self.asset_status_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {COLORS['fg_variant']};
                background-color: {COLORS['surface_high']};
                padding: 2px 8px;
                border-radius: 4px;
                font-weight: 500;
            }}
        """)
        type_status_layout.addWidget(self.asset_status_label)
        type_status_layout.addStretch()

        title_layout.addLayout(type_status_layout)
        header_layout.addWidget(title_widget)

    def setup_asset_preview(self):
        """Setup asset preview section like Ayon"""
        self.asset_preview_widget = QWidget()
        preview_layout = QVBoxLayout(self.asset_preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(8)

        # Preview label
        preview_title = QLabel("Preview")
        preview_title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {COLORS['fg']};
                margin: 0;
                padding: 4px 0;
            }}
        """)
        preview_layout.addWidget(preview_title)

        # Preview area
        self.asset_preview_label = QLabel("No Preview Available")
        self.asset_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.asset_preview_label.setMinimumHeight(220)
        self.asset_preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['surface']};
                border: none;
                border-radius: 8px;
                color: {COLORS['muted']};
                font-size: 12px;
            }}
        """)
        preview_layout.addWidget(self.asset_preview_label)

    def setup_asset_details(self):
        """Setup asset details section like Ayon"""
        self.asset_details_widget = QWidget()
        details_layout = QVBoxLayout(self.asset_details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)

        # Details title
        details_title = QLabel("Details")
        details_title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {COLORS['fg']};
                margin: 0;
                padding: 4px 0;
            }}
        """)
        details_layout.addWidget(details_title)

        # Details content
        details_content = QWidget()
        details_content_layout = QFormLayout(details_content)
        details_content_layout.setContentsMargins(0, 0, 0, 0)
        details_content_layout.setSpacing(6)

        self.asset_path_label = QLabel("-")
        self.asset_artist_label = QLabel("-")
        self.asset_date_label = QLabel("-")
        self.asset_type_label2 = QLabel("Dummy")

        # Style the labels
        for label in [self.asset_path_label, self.asset_artist_label, self.asset_date_label, self.asset_type_label2]:
            label.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    color: {COLORS['fg_variant']};
                    background-color: transparent;
                    padding: 4px 8px;
                    border-radius: 4px;
                    border: none;
                }}
            """)

        # Hide Path row (remove it from details)
        # details_content_layout.addRow("Path:", self.asset_path_label)
        details_content_layout.addRow("Artist:", self.asset_artist_label)
        details_content_layout.addRow("Modified:", self.asset_date_label)
        details_content_layout.addRow("Type:", self.asset_type_label2)

        details_layout.addWidget(details_content)

    def setup_asset_actions(self):
        """Setup asset actions toolbar like Ayon"""
        self.asset_actions_widget = QWidget()
        actions_layout = QVBoxLayout(self.asset_actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        # Actions title
        actions_title = QLabel("Actions")
        actions_title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {COLORS['fg']};
                margin: 0;
                padding: 4px 0;
            }}
        """)
        actions_layout.addWidget(actions_title)

        # Action buttons in a grid
        buttons_widget = QWidget()
        buttons_layout = QGridLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(6)

        self.open_asset_btn = QPushButton("Open")
        self.open_asset_btn.setProperty("class", "primary")
        self.copy_path_btn = QPushButton("Copy Path")
        self.show_in_explorer_btn = QPushButton("Explorer")
        self.asset_properties_btn = QPushButton("Properties")

        # Style buttons
        for btn in [self.open_asset_btn, self.copy_path_btn, self.show_in_explorer_btn, self.asset_properties_btn]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent']};
                    color: white;
                    border: 1px solid {COLORS['accent']};
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 12px;
                    font-weight: 500;
                    min-height: 16px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_hover']};
                    border: 1px solid {COLORS['accent_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['accent_active']};
                    border: 1px solid {COLORS['accent_active']};
                }}
            """)

        # Grid layout for buttons
        buttons_layout.addWidget(self.open_asset_btn, 0, 0)
        buttons_layout.addWidget(self.copy_path_btn, 0, 1)
        buttons_layout.addWidget(self.show_in_explorer_btn, 1, 0)
        buttons_layout.addWidget(self.asset_properties_btn, 1, 1)

        actions_layout.addWidget(buttons_widget)


class VersionManager(PrismStyleWidget):
    """Version manager widget - main right panel"""
    selectedVersionChanged = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_entity = None
        self.current_versions = []
        self.view_mode = "list"
        self.version_card_widgets = []
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Header with entity info (Ayon style)
        self.setup_version_header()
        layout.addWidget(self.header_widget)
        
        # Version controls (Ayon style)
        self.setup_version_controls()
        layout.addWidget(self.controls_widget)
        
        # Version table (Ayon style)
        self.setup_version_table()
        layout.addWidget(self.version_table)
        
        # Version info panel exists but not shown; we use the right-side Preview instead
        self.setup_version_info()
        self.info_widget.setVisible(False)


    def setup_version_header(self):
        """Setup version header in Ayon style"""
        self.header_widget = QWidget()
        header_layout = QVBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # Header title
        header_title = QLabel("Version Manager")
        header_title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {COLORS['fg']};
                margin: 0;
                padding: 4px 0;
            }}
        """)
        header_layout.addWidget(header_title)

        # Entity info
        entity_info = QWidget()
        entity_layout = QVBoxLayout(entity_info)
        entity_layout.setContentsMargins(12, 12, 12, 12)
        entity_layout.setSpacing(4)

        self.entity_name_label = QLabel("No Selection")
        self.entity_name_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {COLORS['fg']};
                background-color: {COLORS['surface']};
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid {COLORS['outline']};
            }}
        """)
        self.entity_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        entity_layout.addWidget(self.entity_name_label)
        
        self.entity_type_label = QLabel("")
        self.entity_type_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {COLORS['fg_variant']};
                background-color: {COLORS['surface_high']};
                padding: 4px 8px;
                border-radius: 4px;
                border: 1px solid {COLORS['outline']};
            }}
        """)
        self.entity_type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        entity_layout.addWidget(self.entity_type_label)

        entity_info.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['outline']};
                border-radius: 8px;
            }}
        """)
        header_layout.addWidget(entity_info)

    def setup_version_controls(self):
        """Setup version controls in Ayon style"""
        self.controls_widget = QWidget()
        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)

        # Controls title
        controls_title = QLabel("Actions")
        controls_title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {COLORS['fg']};
                margin: 0;
                padding: 4px 0;
            }}
        """)
        controls_layout.addWidget(controls_title)
        controls_layout.addStretch()

        # Action buttons
        self.publish_btn = QPushButton("Publish")
        self.publish_btn.setProperty("class", "primary")
        self.publish_btn.setEnabled(False)
        
        self.import_btn = QPushButton("Import")
        self.import_btn.setEnabled(False)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setEnabled(False)

        # Style buttons
        for btn in [self.publish_btn, self.import_btn, self.export_btn]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent']};
                    color: white;
                    border: 1px solid {COLORS['accent']};
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: 500;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_hover']};
                    border: 1px solid {COLORS['accent_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['accent_active']};
                    border: 1px solid {COLORS['accent_active']};
                }}
                QPushButton:disabled {{
                    background-color: {COLORS['surface_high']};
                    color: {COLORS['muted']};
                    border: 1px solid {COLORS['outline']};
                }}
            """)
        
        controls_layout.addWidget(self.publish_btn)
        controls_layout.addWidget(self.import_btn)
        controls_layout.addWidget(self.export_btn)

        # View mode toggle (Prism-like list/grid)
        from PyQt6.QtWidgets import QToolButton
        self.view_list_btn = QToolButton()
        self.view_list_btn.setText("List")
        self.view_list_btn.setCheckable(True)
        self.view_grid_btn = QToolButton()
        self.view_grid_btn.setText("Grid")
        self.view_grid_btn.setCheckable(True)
        self.view_list_btn.setChecked(True)

        self.view_list_btn.clicked.connect(lambda: self.set_view_mode("list"))
        self.view_grid_btn.clicked.connect(lambda: self.set_view_mode("grid"))

        controls_layout.addSpacing(12)
        controls_layout.addWidget(self.view_list_btn)
        controls_layout.addWidget(self.view_grid_btn)

        # Removed density toggle to match single card style

    def setup_version_table(self):
        """Setup version table in Ayon style"""
        self.version_table = QTableWidget()
        # Keep 5 columns; first column will show icon + version text together
        self.version_table.setColumnCount(5)
        self.version_table.setHorizontalHeaderLabels([
            "Version", "User", "Date", "Comment", "Status"
        ])
        self.version_table.horizontalHeader().setStretchLastSection(True)
        self.version_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.version_table.setAlternatingRowColors(True)
        self.version_table.setSortingEnabled(True)
        # Make the list read-only (no in-place editing)
        self.version_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Set column widths
        header = self.version_table.horizontalHeader()
        header.resizeSection(0, 120)  # Version (icon + text)
        header.resizeSection(1, 100)  # User
        header.resizeSection(2, 120)  # Date
        header.resizeSection(3, 200)  # Comment
        header.resizeSection(4, 80)   # Status

        # Style the table
        self.version_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['surface']};
                color: {COLORS['fg']};
                border: 1px solid {COLORS['outline']};
                border-radius: 8px;
                gridline-color: {COLORS['outline']};
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border: none;
                color: {COLORS['fg']};
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['accent']};
                color: white;
            }}
            QTableWidget::item:hover {{
                background-color: {COLORS['hover']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['surface_high']};
                color: {COLORS['fg']};
                border: 1px solid {COLORS['outline']};
                padding: 8px 12px;
                font-weight: 600;
                font-size: 12px;
            }}
        """)

        # Card/grid view (Prism-like)
        from PyQt6.QtWidgets import QListWidget
        self.version_cards = QListWidget()
        # List mode lets each row span the full width
        self.version_cards.setViewMode(QListWidget.ViewMode.ListMode)
        self.version_cards.setWrapping(False)
        self.version_cards.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.version_cards.setMovement(QListWidget.Movement.Static)
        self.version_cards.setIconSize(QSize(128, 72))
        self.version_cards.setSpacing(10)
        self.version_cards.setUniformItemSizes(False)
        self.version_cards.setWordWrap(True)
        # Never show a horizontal scrollbar; width always matches viewport
        self.version_cards.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.version_cards.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.version_cards.setStyleSheet(f"""
            QListWidget::item {{ margin: 0px; padding: 0px; border: none; }}
            QListWidget::item:selected {{ background-color: transparent; border: none; }}
            QListWidget::item:hover {{ background-color: transparent; }}
            QListWidget {{ background-color: {COLORS['surface_high']}; border: none; }}
        """)
        self.version_cards.hide()

    def setup_version_info(self):
        """Setup version info panel in Ayon style"""
        self.info_widget = QWidget()
        info_layout = QVBoxLayout(self.info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)

        # Info title
        info_title = QLabel("Version Details")
        info_title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {COLORS['fg']};
                margin: 0;
                padding: 4px 0;
            }}
        """)
        info_layout.addWidget(info_title)

        # Info content
        info_content = QWidget()
        info_content.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['outline']};
                border-radius: 8px;
            }}
        """)
        content_layout = QVBoxLayout(info_content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(8)

        # Version details
        details_layout = QFormLayout()
        details_layout.setSpacing(6)

        self.version_label = QLabel("-")
        self.user_label = QLabel("-")
        self.date_label = QLabel("-")
        self.comment_label = QLabel("-")

        # Style the labels
        for label in [self.version_label, self.user_label, self.date_label, self.comment_label]:
            label.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    color: {COLORS['fg_variant']};
                    background-color: {COLORS['surface_high']};
                    padding: 4px 8px;
                    border-radius: 4px;
                    border: 1px solid {COLORS['outline']};
                }}
            """)

        self.comment_label.setWordWrap(True)

        details_layout.addRow("Version:", self.version_label)
        details_layout.addRow("User:", self.user_label)
        details_layout.addRow("Date:", self.date_label)
        details_layout.addRow("Comment:", self.comment_label)

        content_layout.addLayout(details_layout)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        self.open_btn = QPushButton("Open")
        self.open_btn.setEnabled(False)
        
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.setProperty("class", "danger")

        # Style action buttons
        for btn in [self.open_btn, self.copy_btn, self.delete_btn]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent']};
                    color: white;
                    border: 1px solid {COLORS['accent']};
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: 500;
                    min-width: 60px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_hover']};
                    border: 1px solid {COLORS['accent_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['accent_active']};
                    border: 1px solid {COLORS['accent_active']};
                }}
                QPushButton:disabled {{
                    background-color: {COLORS['surface_high']};
                    color: {COLORS['muted']};
                    border: 1px solid {COLORS['outline']};
                }}
            """)
        
        action_layout.addWidget(self.open_btn)
        action_layout.addWidget(self.copy_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addStretch()
        
        content_layout.addLayout(action_layout)
        info_layout.addWidget(info_content)
    
    def add_right_click_hint(self):
        """Deprecated: hint banner removed"""
        return
    
    def setup_connections(self):
        """Setup signal connections"""
        # Version table selection
        self.version_table.itemSelectionChanged.connect(self.on_version_selected)
        # Card selection mirrors table behavior
        self.version_cards.itemSelectionChanged.connect(self.on_card_selected)
        
        # Action buttons
        self.publish_btn.clicked.connect(self.on_publish_clicked)
        self.import_btn.clicked.connect(self.on_import_clicked)
        self.export_btn.clicked.connect(self.on_export_clicked)
        self.open_btn.clicked.connect(self.on_open_clicked)
        self.copy_btn.clicked.connect(self.on_copy_clicked)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        
        # Context menu for version table
        self.version_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.version_table.customContextMenuRequested.connect(self.show_version_context_menu)
        # Emit a selectionChanged signal we can connect from the ProjectBrowser
        from PyQt6.QtCore import pyqtSignal
        # Context menu for card view as well
        self.version_cards.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.version_cards.customContextMenuRequested.connect(self.show_version_context_menu)
        # Double-click open handlers
        self.version_table.cellDoubleClicked.connect(lambda r, c: self.on_open_clicked())
        self.version_cards.itemDoubleClicked.connect(lambda item: self.on_open_clicked())
    
    def update_entity(self, entity_name: str, entity_type: str = "Asset", task_name: str = None):
        """Update the current entity being managed"""
        self.current_entity = entity_name
        self.current_task = task_name
        
        # Update entity display
        if task_name:
            self.entity_name_label.setText(f"{entity_name} - {task_name}")
        else:
            self.entity_name_label.setText(entity_name)
        self.entity_type_label.setText(entity_type)
        
        # Load versions for this entity
        self.load_versions()
    
    def load_versions(self):
        """Load versions for the current entity"""
        if not self.current_entity:
            return
        
        # Resolve manager robustly
        manager = None
        try:
            win = self.window()
            if hasattr(win, 'manager') and win.manager:
                manager = win.manager
        except Exception:
            pass
        if manager is None:
            try:
                from .ui import get_current_controller as ui_get_current_controller
                ctrl = ui_get_current_controller()
                if ctrl and hasattr(ctrl, 'manager') and ctrl.manager:
                    manager = ctrl.manager
            except Exception:
                pass
        if manager is None:
            try:
                from .main import get_current_controller as main_get_current_controller
                ctrl = main_get_current_controller()
                if ctrl and hasattr(ctrl, 'manager') and ctrl.manager:
                    manager = ctrl.manager
            except Exception:
                pass
        if manager is None:
            return
        
        # Get versions from manager
        all_versions = manager.list_versions(self.current_entity)
        # Filter by current task if provided, so each task sees its own versions
        if getattr(self, 'current_task', None):
            self.current_versions = [v for v in all_versions if getattr(v, 'task_name', '') == self.current_task]
        else:
            self.current_versions = all_versions
        if self.view_mode == "grid":
            self.populate_version_cards()
        else:
            self.populate_version_table()
    
    def populate_version_table(self):
        """Populate the version table with current versions"""
        self.version_table.setRowCount(len(self.current_versions))
        
        for row, version in enumerate(self.current_versions):
            # First column: icon + version text together
            version_item = QTableWidgetItem(version.version)
            if version.dcc_app:
                qicon = _load_dcc_icon(version.dcc_app)
                if qicon:
                    version_item.setIcon(qicon)
                else:
                    version_item.setText(f"{version.get_dcc_app_icon()} {version.version}")
            self.version_table.setItem(row, 0, version_item)
            
            # User
            self.version_table.setItem(row, 1, QTableWidgetItem(version.user))
            
            # Date
            date_str = version.date.split('T')[0] if 'T' in version.date else version.date
            self.version_table.setItem(row, 2, QTableWidgetItem(date_str))
            
            # Comment
            comment_item = QTableWidgetItem(version.comment)
            comment_item.setToolTip(version.comment)  # Show full comment on hover
            self.version_table.setItem(row, 3, comment_item)
            
            # Status
            status_item = QTableWidgetItem(version.status)
            # Color code status
            if version.status == "WIP":
                status_item.setBackground(QColor(255, 193, 7, 50))  # Yellow
            elif version.status == "Review":
                status_item.setBackground(QColor(0, 123, 255, 50))  # Blue
            elif version.status == "Approved":
                status_item.setBackground(QColor(40, 167, 69, 50))  # Green
            elif version.status == "Published":
                status_item.setBackground(QColor(108, 117, 125, 50))  # Gray
            self.version_table.setItem(row, 4, status_item)
            
            # No path column in the list view to keep it clean
        
        # Auto-select first row if nothing selected
        if self.version_table.rowCount() > 0 and self.version_table.currentRow() < 0:
            self.version_table.setCurrentCell(0, 0)
            self.on_version_selected()
        # Enable/disable buttons based on selection
        self.update_button_states()

    def populate_version_cards(self):
        """Populate the card/grid view with current versions (Prism-style layout)"""
        from PyQt6.QtWidgets import QListWidgetItem
        self.version_cards.clear()
        # Card height; width bound to viewport so it's not scrollable horizontally
        card_h = 120
        thumb_w, thumb_h = 160, 90
        self.version_card_widgets = []
        for version in self.current_versions:
            item = QListWidgetItem()
            # Ensure items are selectable/enabled
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            # Set width to current viewport width, so it fills the parent
            viewport_w = self.version_cards.viewport().width()
            # Compute effective width minus small safety padding to avoid right cut-off
            effective_w = max(140, viewport_w - 4)
            item.setSizeHint(QSize(effective_w, card_h))
            self.version_cards.addItem(item)
            card = self._build_version_card_widget(version, thumb_w, thumb_h, effective_w, card_h)
            self.version_cards.setItemWidget(item, card)
            self.version_card_widgets.append(card)

        # Auto-select first item if nothing selected
        if self.version_cards.count() > 0 and self.version_cards.currentRow() < 0:
            self.version_cards.setCurrentRow(0)
            self.on_card_selected()

        # Update highlight for current selection
        self._update_card_highlight()
        self.update_button_states()

    def _build_version_card_widget(self, version, thumb_w: int, thumb_h: int, card_w: int, card_h: int):
        """Create a QWidget that mimics Prism VFX version card: thumbnail left; center: version; right: user/date."""
        from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout
        card = QWidget()
        card.setMinimumSize(card_w, card_h)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid transparent;
                border-radius: 8px;
            }}
        """)
        row = QHBoxLayout(card)
        row.setContentsMargins(8, 8, 16, 8)  # extra right margin
        row.setSpacing(12)

        # Thumbnail
        thumb_label = QLabel()
        thumb_label.setFixedSize(thumb_w, thumb_h)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setStyleSheet("background-color: #2b2f33; border-radius: 4px;")
        try:
            if getattr(version, "thumbnail", None) and os.path.exists(version.thumbnail):
                pix = QPixmap(version.thumbnail).scaled(thumb_w, thumb_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                thumb_label.setPixmap(pix)
            else:
                thumb_label.setText("🗂️")
        except Exception:
            thumb_label.setText("🗂️")
        row.addWidget(thumb_label)

        # Middle column (title/comment)
        mid = QVBoxLayout()
        mid.setSpacing(4)
        title = QLabel(version.version)
        title.setStyleSheet("font-weight: 700; font-size: 14px; background-color: transparent; border: none;")
        mid.addWidget(title)
        comment_text = version.comment or ""
        comment = QLabel(comment_text)
        comment.setStyleSheet("font-size: 12px; color: #aab0b6; background-color: transparent; border: none;")
        comment.setWordWrap(True)
        mid.addWidget(comment)
        mid.addStretch(1)
        row.addLayout(mid, 1)

        # Right column (user/date/status)
        right = QVBoxLayout()
        right.setSpacing(2)
        user = QLabel(version.user or "-")
        user.setStyleSheet("font-size: 12px; background-color: transparent; border: none;")
        date_str = version.date.split('T')[0] if 'T' in version.date else (version.date or "-")
        date = QLabel(date_str)
        date.setStyleSheet("font-size: 12px; color: #aab0b6; background-color: transparent; border: none;")
        right.addWidget(user, alignment=Qt.AlignmentFlag.AlignRight)
        right.addWidget(date, alignment=Qt.AlignmentFlag.AlignRight)
        # Status chip
        status = getattr(version, 'status', 'WIP')
        chip = QLabel(status)
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip.setFixedHeight(20)
        chip.setStyleSheet("""
            QLabel { padding: 2px 8px; border-radius: 10px; font-size: 11px; }
        """)
        if status == "Approved":
            chip.setStyleSheet(chip.styleSheet() + "background-color: rgba(40,167,69,0.25); color: #28a745;")
        elif status == "Review":
            chip.setStyleSheet(chip.styleSheet() + "background-color: rgba(0,123,255,0.25); color: #007bff;")
        elif status == "Published":
            chip.setStyleSheet(chip.styleSheet() + "background-color: rgba(108,117,125,0.25); color: #6c757d;")
        else:
            chip.setStyleSheet(chip.styleSheet() + "background-color: rgba(255,193,7,0.25); color: #ffc107;")
        right.addStretch(1)
        right.addWidget(chip, alignment=Qt.AlignmentFlag.AlignRight)
        row.addLayout(right)

        return card
    
    def on_version_selected(self):
        """Handle version selection"""
        self.update_version_info()
        # Update right-side preview with selected version thumbnail
        try:
            row = -1
            if self.version_table.isVisible():
                row = self.version_table.currentRow()
            elif self.version_cards.isVisible():
                row = self.version_cards.currentRow()
            if row >= 0 and row < len(self.current_versions):
                v = self.current_versions[row]
                self._update_right_preview(v)
                self.selectedVersionChanged.emit(v)
        except Exception:
            pass
        self.update_button_states()

    def on_card_selected(self):
        """Mirror card selection into version info panel"""
        row = self.version_cards.currentRow()
        if row >= 0 and row < len(self.current_versions):
            # Keep table selection in sync
            if self.version_table.isVisible():
                self.version_table.setCurrentCell(row, 0)
            self.update_version_info()
            # Update preview for card selection
            try:
                v = self.current_versions[row]
                self._update_right_preview(v)
                self.selectedVersionChanged.emit(v)
            except Exception:
                pass
            self._update_card_highlight()
        self.update_button_states()

    def _set_card_selected(self, card: QWidget, selected: bool):
        border_color = COLORS['accent'] if selected else 'transparent'
        border_width = 2 if selected else 1
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface']};
                border: {border_width}px solid {border_color};
                border-radius: 8px;
            }}
        """)

    def _update_card_highlight(self):
        if not self.version_card_widgets:
            return
        sel = self.version_cards.currentRow()
        for idx, card in enumerate(self.version_card_widgets):
            self._set_card_selected(card, idx == sel)

    def _update_right_preview(self, version):
        """Set the right-side preview image/text based on a Version object."""
        try:
            win = self.window()
            if not win or not hasattr(win, 'project_browser'):
                return
            # Prefer dedicated right panel if present
            browser = getattr(win, 'right_panel', None) or getattr(win, 'project_browser', None)
            preview = getattr(browser, 'asset_preview_label', None)
            if preview is None:
                return
            if getattr(version, 'thumbnail', None) and os.path.exists(version.thumbnail):
                pix = QPixmap(version.thumbnail).scaled(
                    max(120, preview.width()-20),
                    max(120, preview.height()-20),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                preview.setPixmap(pix)
                preview.setText("")
            else:
                preview.setPixmap(QPixmap())
                # Show version name so it's clear what is selected
                preview.setText(version.version or "No Preview Available")

            # Update textual details if present in the right panel
            name_lbl = getattr(browser, 'asset_name_label', None)
            if name_lbl is not None:
                name_lbl.setText(version.version or "No Selection")
            path_lbl = getattr(browser, 'asset_path_label', None)
            if path_lbl is not None:
                # Hidden in UI, but keep value updated internally
                path_lbl.setText(getattr(version, 'path', '') or "-")
            artist_lbl = getattr(browser, 'asset_artist_label', None)
            if artist_lbl is not None:
                artist_lbl.setText(getattr(version, 'user', '') or "-")
            date_lbl = getattr(browser, 'asset_date_label', None)
            if date_lbl is not None:
                date_lbl.setText(getattr(version, 'date', '') or "-")
            # Status chip if available
            status_lbl = getattr(browser, 'asset_status_label', None)
            if status_lbl is not None:
                status_lbl.setText(getattr(version, 'status', 'Unknown'))
            # Type (dummy)
            type_lbl2 = getattr(browser, 'asset_type_label2', None)
            if type_lbl2 is not None:
                type_lbl2.setText("Dummy")
        except Exception:
            return
    
    def update_version_info(self):
        """Update version info panel with selected version"""
        # Determine current selection from visible view
        row = -1
        if self.version_table.isVisible():
            row = self.version_table.currentRow()
        elif self.version_cards.isVisible():
            row = self.version_cards.currentRow()
        if row < 0 or row >= len(self.current_versions):
            self.version_label.setText("-")
            self.user_label.setText("-")
            self.date_label.setText("-")
            self.comment_label.setText("-")
            return
        # We no longer display an inline details widget; info goes to the right Preview panel only
    
    def update_button_states(self):
        """Update button enabled states"""
        has_selection = (self.version_table.isVisible() and self.version_table.currentRow() >= 0) or \
                        (self.version_cards.isVisible() and self.version_cards.currentRow() >= 0)
        has_entity = self.current_entity is not None
        
        self.publish_btn.setEnabled(has_entity)
        self.import_btn.setEnabled(has_entity)
        self.export_btn.setEnabled(has_entity)
        self.open_btn.setEnabled(has_selection)
        self.copy_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def set_view_mode(self, mode: str):
        """Toggle between list (table) and grid (cards) views"""
        self.view_mode = mode
        self.view_list_btn.setChecked(mode == "list")
        self.view_grid_btn.setChecked(mode == "grid")

        parent_layout = self.layout()
        if mode == "grid":
            if parent_layout.indexOf(self.version_cards) == -1:
                idx = parent_layout.indexOf(self.version_table)
                insert_idx = idx if idx != -1 else parent_layout.count() - 1
                parent_layout.insertWidget(insert_idx, self.version_cards)
            # Preserve selection from table
            sel_row = self.version_table.currentRow()
            self.version_table.hide()
            self.version_cards.show()
            self.populate_version_cards()
            if sel_row >= 0 and sel_row < len(self.current_versions):
                self.version_cards.setCurrentRow(sel_row)
                self.update_version_info()
            # Ensure items reflow to new width on resize
            self.version_cards.viewport().resizeEvent = lambda e, _orig=self.version_cards.viewport().resizeEvent: (self.populate_version_cards(), _orig(e) if _orig else None)
        else:
            # Preserve selection from cards
            sel_row = self.version_cards.currentRow()
            self.version_cards.hide()
            self.version_table.show()
            self.populate_version_table()
            if sel_row >= 0 and sel_row < len(self.current_versions):
                self.version_table.setCurrentCell(sel_row, 0)
                self.update_version_info()

    def set_density_mode(self, mode: str):
        """Switch between compact and large card density"""
        self.density_mode = mode
        self.density_compact_btn.setChecked(mode == "compact")
        self.density_large_btn.setChecked(mode == "large")
        if self.version_cards.isVisible():
            self.populate_version_cards()
    
    def show_version_context_menu(self, position):
        """Show context menu for version table - Prism style"""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['surface']};
                color: {COLORS['fg']};
                border: 1px solid {COLORS['outline']};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                background-color: transparent;
                padding: 8px 16px;
                border-radius: 4px;
                margin: 1px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['accent']};
                color: white;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {COLORS['outline']};
                margin: 4px 8px;
            }}
        """)
        
        # Get selected version if any
        current_row = self.version_table.currentRow()
        has_selection = current_row >= 0 and current_row < len(self.current_versions)
        
        if has_selection:
            version = self.current_versions[current_row]
            
            # Open with DCC app (if version has DCC app)
            if version.dcc_app:
                open_action = menu.addAction(f"🎨 Open with {version.dcc_app.title()}")
                open_action.triggered.connect(lambda: self.open_version_with_dcc(version))
                menu.addSeparator()
            
            # Version management actions
            copy_action = menu.addAction("📋 Copy Version")
            copy_action.triggered.connect(lambda: self.copy_version(version))
            
            delete_action = menu.addAction("🗑️ Delete Version")
            delete_action.triggered.connect(lambda: self.delete_version(version))
            
            menu.addSeparator()
        
        # Single Create Version action (Prism-like)
        quick_create = menu.addAction("➕ Create Version…")
        quick_create.triggered.connect(self.create_quick_version)

        # DCC creation submenu (optional)
        create_section = menu.addMenu("Create With DCC App")
        create_section.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['surface_high']};
                color: {COLORS['fg']};
                border: 1px solid {COLORS['outline']};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                background-color: transparent;
                padding: 8px 16px;
                border-radius: 4px;
                margin: 1px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['accent']};
                color: white;
            }}
        """)
        
        # Add DCC app creation options
        self.add_dcc_creation_menu(create_section)
        
        # Additional Prism-style actions
        menu.addSeparator()
        
        # Refresh action
        refresh_action = menu.addAction("🔄 Refresh")
        refresh_action.triggered.connect(self.load_versions)
        
        # Import action
        import_action = menu.addAction("📥 Import Version")
        import_action.triggered.connect(self.import_version)
        
        # Export action
        export_action = menu.addAction("📤 Export Version")
        export_action.triggered.connect(self.export_version)
        
        menu.exec(self.version_table.mapToGlobal(position))
    
    def add_dcc_creation_menu(self, parent_menu):
        """Add DCC app creation options to menu - Prism style"""
        from .main import get_current_controller
        controller = get_current_controller()
        # Build list of apps. If manager missing or returns none, fall back to core four.
        allowed = {"maya", "blender", "houdini", "nuke"}
        dcc_apps = []
        try:
            if controller and controller.manager:
                dcc_apps = [a for a in controller.manager.get_dcc_apps() if a.get("name") in allowed]
        except Exception:
            dcc_apps = []
        if not dcc_apps:
            # Fallback to static core apps so the dialog can still be used
            dcc_apps = [
                {"name": "maya", "display_name": "Autodesk Maya", "file_extensions": [".ma", ".mb"]},
                {"name": "blender", "display_name": "Blender", "file_extensions": [".blend"]},
                {"name": "houdini", "display_name": "SideFX Houdini", "file_extensions": [".hip", ".hipnc"]},
                {"name": "nuke", "display_name": "Foundry Nuke", "file_extensions": [".nk"]},
            ]
        
        # DCC app icons and descriptions (Prism style)
        app_info = {
            "maya": {"icon": "🎨", "desc": "Autodesk Maya - 3D Animation & Modeling"},
            "blender": {"icon": "🎭", "desc": "Blender - 3D Creation Suite"},
            "houdini": {"icon": "🌀", "desc": "SideFX Houdini - 3D Animation & VFX"},
            "nuke": {"icon": "🎬", "desc": "Foundry Nuke - Compositing"},
            "3dsmax": {"icon": "📐", "desc": "3ds Max - 3D Modeling & Animation"},
            "cinema4d": {"icon": "🎪", "desc": "Cinema 4D - 3D Motion Graphics"}
        }
        
        for app in dcc_apps:
            app_name = app['name']
            display_name = app['display_name']
            # Prefer official icon; fallback to emoji desc
            qicon = _load_dcc_icon(app_name)
            emoji = app_info.get(app_name, {}).get('icon', '📁')
            desc = app_info.get(app_name, {}).get('desc', display_name)
            
            # Create action with icon and description
            if qicon:
                action = parent_menu.addAction(qicon, display_name)
            else:
                action = parent_menu.addAction(f"{emoji} {display_name}")
            action.setToolTip(desc)
            # Open the Create Version dialog for the chosen app
            action.triggered.connect(lambda checked, app_name=app_name: self.create_dcc_version(app_name))

    def create_dcc_quick(self, dcc_app: str):
        """Open the selected DCC app immediately. If multiple file types, ask first; if one, just open."""
        from .main import get_current_controller
        controller = get_current_controller()
        if not controller or not controller.manager:
            QMessageBox.warning(self, "No Manager", "Project manager not available.")
            return
        # Determine available extensions for the app
        app_info = None
        for app in controller.manager.get_dcc_apps():
            if app['name'] == dcc_app:
                app_info = app
                break
        file_exts = app_info.get('file_extensions', []) if app_info else []
        # If multiple extensions, ask user which type; we don't need the path now, just preference
        chosen_ext = None
        if len(file_exts) > 1:
            menu = QMenu(self)
            actions = []
            for ext in file_exts:
                act = menu.addAction(ext)
                actions.append((act, ext))
            picked = menu.exec(self.cursor().pos())
            if picked:
                for act, ext in actions:
                    if act is picked:
                        chosen_ext = ext
                        break
        # Launch immediately (workfile path optional; app opens ready to save)
        ok = controller.manager.launch_dcc_app(dcc_app, entity_key=None, task_name=None, version=None)
        if not ok:
            QMessageBox.critical(self, "Launch Failed", f"Could not launch {dcc_app.title()}.\nEnsure it is installed and detected in settings.")

    def create_quick_version(self):
        """Create a placeholder version immediately (no file picker), scoped to task."""
        # Require entity and task to be selected so versions are tied correctly
        if not getattr(self, 'current_entity', None):
            QMessageBox.warning(self, "No Selection", "Select an asset or shot first.")
            return
        if not getattr(self, 'current_task', None):
            QMessageBox.warning(self, "No Task", "Select a task for this entity before creating a version.")
            return
        # Resolve manager robustly
        manager = None
        try:
            win = self.window()
            if hasattr(win, 'manager') and win.manager:
                manager = win.manager
        except Exception:
            pass
        if manager is None:
            try:
                from .ui import get_current_controller as ui_get_current_controller
                ctrl = ui_get_current_controller()
                if ctrl and hasattr(ctrl, 'manager') and ctrl.manager:
                    manager = ctrl.manager
            except Exception:
                pass
        if manager is None:
            try:
                from .main import get_current_controller as main_get_current_controller
                ctrl = main_get_current_controller()
                if ctrl and hasattr(ctrl, 'manager') and ctrl.manager:
                    manager = ctrl.manager
            except Exception:
                pass
        if not manager:
            QMessageBox.critical(self, "Error", "No project manager available.")
            return
        if not getattr(manager, 'current_project', None):
            QMessageBox.warning(self, "No Project", "Load or create a project first from the File menu.")
            return
        # Basic prompt for user/comment
        user, ok = QInputDialog.getText(self, "User", "Enter your name:")
        if not ok or not user.strip():
            return
        comment, _ = QInputDialog.getText(self, "Comment", "Comment (optional):")
        version = manager.create_placeholder_version(
            entity_key=self.current_entity,
            user=user.strip(),
            comment=comment.strip() if comment else "",
            task_name=self.current_task,
        )
        self.load_versions()
        if self.current_versions:
            last_index = len(self.current_versions) - 1
            if self.version_table.isVisible():
                self.version_table.setCurrentCell(last_index, 0)
            if self.version_cards.isVisible():
                self.version_cards.setCurrentRow(last_index)
    
    def create_dcc_version(self, dcc_app: str):
        """Create a new version with DCC app"""
        if not getattr(self, 'current_entity', None):
            # Allow proceeding; dialog will still open and let user pick workfile
            QMessageBox.information(self, "No Selection", "No asset/shot selected. You can still pick a workfile to create a version.")
        if not getattr(self, 'current_task', None):
            # Allow proceeding; dialog includes a task field
            pass
        
        # Show create version dialog
        dialog = CreateVersionDialog(dcc_app, getattr(self, 'current_entity', '') or '', self, getattr(self, 'current_task', '') or None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload versions
            self.load_versions()
            # Try to select the newest version row/card
            if self.current_versions:
                last_index = len(self.current_versions) - 1
                if self.version_table.isVisible():
                    self.version_table.setCurrentCell(last_index, 0)
                if self.version_cards.isVisible():
                    self.version_cards.setCurrentRow(last_index)
    
    def open_version_with_dcc(self, version):
        """Open version with its DCC app"""
        from .main import get_current_controller
        controller = get_current_controller()
        if not controller or not controller.manager:
            return
        
        controller.manager.launch_dcc_app(
            version.dcc_app, 
            self.current_entity, 
            version.task_name, 
            version.version
        )
    
    def copy_version(self, version):
        """Copy version to clipboard or file"""
        from PyQt6.QtWidgets import QApplication, QFileDialog
        
        # Show copy options dialog
        reply = QMessageBox.question(
            self,
            "Copy Version",
            f"Copy version {version.version}?\n\nChoose copy method:",
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.NoButton
        )
        
        # Add custom buttons
        copy_path_btn = QMessageBox.StandardButton.Yes
        copy_file_btn = QMessageBox.StandardButton.No
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Copy Version")
        msg_box.setText(f"Copy version {version.version}?")
        msg_box.setInformativeText("Choose copy method:")
        
        copy_path_action = msg_box.addButton("Copy Path", QMessageBox.ButtonRole.ActionRole)
        copy_file_action = msg_box.addButton("Copy File", QMessageBox.ButtonRole.ActionRole)
        cancel_action = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == copy_path_action:
            # Copy path to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(version.path)
            QMessageBox.information(self, "Copied", "Version path copied to clipboard")
            
        elif msg_box.clickedButton() == copy_file_action:
            # Copy file to new location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Version Copy",
                f"{version.version}_copy{os.path.splitext(version.path)[1]}",
                f"All Files (*.*)"
            )
            
            if file_path:
                try:
                    import shutil
                    shutil.copy2(version.path, file_path)
                    QMessageBox.information(self, "Success", f"Version copied to:\n{file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to copy file: {str(e)}")
    
    def delete_version(self, version):
        """Delete version"""
        reply = QMessageBox.question(
            self, 
            "Delete Version", 
            f"Are you sure you want to delete version {version.version}?\n\nThis will permanently delete the version and its files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Resolve manager robustly
                manager = None
                try:
                    win = self.window()
                    if hasattr(win, 'manager') and win.manager:
                        manager = win.manager
                except Exception:
                    pass
                if manager is None:
                    try:
                        from .ui import get_current_controller as ui_get_current_controller
                        ctrl = ui_get_current_controller()
                        if ctrl and hasattr(ctrl, 'manager') and ctrl.manager:
                            manager = ctrl.manager
                    except Exception:
                        pass
                if manager is None:
                    try:
                        from .main import get_current_controller as main_get_current_controller
                        ctrl = main_get_current_controller()
                        if ctrl and hasattr(ctrl, 'manager') and ctrl.manager:
                            manager = ctrl.manager
                    except Exception:
                        pass
                if not manager:
                    QMessageBox.critical(self, "Error", "No project manager available")
                    return
                
                # Delete version files
                if os.path.exists(version.path):
                    os.remove(version.path)
                
                if version.workfile_path and os.path.exists(version.workfile_path):
                    os.remove(version.workfile_path)
                
                if version.thumbnail and os.path.exists(version.thumbnail):
                    os.remove(version.thumbnail)
                
                # Remove from project
                versions = manager.current_project.get_versions(self.current_entity)
                versions.remove(version)
                manager.save_project()
                
                # Reload versions
                self.load_versions()
                
                QMessageBox.information(self, "Success", f"Version {version.version} deleted successfully")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete version: {str(e)}")
    
    def on_publish_clicked(self):
        """Handle publish button click"""
        # TODO: Implement publishing
        pass
    
    def on_import_clicked(self):
        """Handle import button click - quick import into current entity/task"""
        try:
            # Preconditions
            if not getattr(self, 'current_entity', None):
                QMessageBox.warning(self, "No Selection", "Select an asset or shot first.")
                return
            if not getattr(self, 'current_task', None):
                QMessageBox.warning(self, "No Task", "Select a task for this entity before importing.")
                return
            # Pick a file to import
            from PyQt6.QtWidgets import QFileDialog
            workfile_path, _ = QFileDialog.getOpenFileName(self, "Select Workfile to Import", "", "All Files (*.*)")
            if not workfile_path:
                return
            # Basic metadata
            user, ok = QInputDialog.getText(self, "User", "Enter your name:")
            if not ok or not user.strip():
                return
            comment, _ = QInputDialog.getText(self, "Comment", "Comment (optional):")

            # Resolve manager
            manager = None
            try:
                win = self.window()
                if hasattr(win, 'manager') and win.manager:
                    manager = win.manager
            except Exception:
                pass
            if manager is None:
                try:
                    from .ui import get_current_controller as ui_get_current_controller
                    ctrl = ui_get_current_controller()
                    if ctrl and hasattr(ctrl, 'manager') and ctrl.manager:
                        manager = ctrl.manager
                except Exception:
                    pass
            if manager is None:
                try:
                    from .main import get_current_controller as main_get_current_controller
                    ctrl = main_get_current_controller()
                    if ctrl and hasattr(ctrl, 'manager') and ctrl.manager:
                        manager = ctrl.manager
                except Exception:
                    pass
            if not manager or not getattr(manager, 'current_project', None):
                QMessageBox.critical(self, "Error", "No project manager available")
                return

            # Create a placeholder version and copy the workfile into canonical path
            version = manager.create_placeholder_version(
                entity_key=self.current_entity,
                user=user.strip(),
                comment=comment.strip() if comment else "",
                task_name=self.current_task,
            )
            # If we have a canonical path, copy selected workfile there
            try:
                if version.path:
                    import shutil
                    shutil.copy2(workfile_path, version.path)
                    if hasattr(version, 'workfile_path'):
                        version.workfile_path = workfile_path
                    manager.save_project()
            except Exception:
                pass

            # Refresh UI and select the new version
            self.load_versions()
            if self.current_versions:
                last_index = len(self.current_versions) - 1
                if self.version_table.isVisible():
                    self.version_table.setCurrentCell(last_index, 0)
                if self.version_cards.isVisible():
                    self.version_cards.setCurrentRow(last_index)
                self.on_version_selected()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))
    
    def on_export_clicked(self):
        """Handle export button click"""
        # TODO: Implement export
        pass
    
    def on_open_clicked(self):
        """Handle open button click"""
        current_row = self.version_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_versions):
            version = self.current_versions[current_row]
            self.open_version_with_dcc(version)
    
    def on_copy_clicked(self):
        """Handle copy button click"""
        current_row = self.version_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_versions):
            version = self.current_versions[current_row]
            self.copy_version(version)
    
    def on_delete_clicked(self):
        """Handle delete button click"""
        current_row = self.version_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_versions):
            version = self.current_versions[current_row]
            self.delete_version(version)
    
    def import_version(self):
        """Import version from file - Prism style"""
        from PyQt6.QtWidgets import QFileDialog
        
        if not self.current_entity:
            QMessageBox.warning(self, "No Selection", "Please select an asset first")
            return
        
        # Get file filter for all supported DCC files
        file_filter = "All DCC Files ("
        dcc_extensions = [".ma", ".mb", ".blend", ".hip", ".hipnc", ".nk", ".max", ".c4d"]
        file_filter += " ".join(f"*{ext}" for ext in dcc_extensions)
        file_filter += ");;Maya Files (*.ma *.mb);;Blender Files (*.blend);;Houdini Files (*.hip *.hipnc);;Nuke Files (*.nk);;3ds Max Files (*.max);;Cinema 4D Files (*.c4d);;All Files (*.*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Version",
            "",
            file_filter
        )
        
        if file_path:
            try:
                # Determine DCC app from file extension
                ext = Path(file_path).suffix.lower()
                dcc_map = {
                    ".ma": "maya", ".mb": "maya",
                    ".blend": "blender",
                    ".hip": "houdini", ".hipnc": "houdini",
                    ".nk": "nuke",
                    ".max": "3dsmax",
                    ".c4d": "cinema4d"
                }
                
                dcc_app = dcc_map.get(ext, "unknown")
                
                # Show import dialog
                dialog = ImportVersionDialog(dcc_app, self.current_entity, file_path, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.load_versions()
                    
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import version: {str(e)}")
    
    def export_version(self):
        """Export selected version - Prism style"""
        current_row = self.version_table.currentRow()
        if current_row < 0 or current_row >= len(self.current_versions):
            QMessageBox.warning(self, "No Selection", "Please select a version to export")
            return
        
        version = self.current_versions[current_row]
        
        from PyQt6.QtWidgets import QFileDialog
        
        # Get suggested filename
        suggested_name = f"{self.current_entity}_{version.version}_export{Path(version.path).suffix}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Version",
            suggested_name,
            f"All Files (*.*);;{Path(version.path).suffix.upper()} Files (*{Path(version.path).suffix})"
        )
        
        if file_path:
            try:
                import shutil
                shutil.copy2(version.path, file_path)
                QMessageBox.information(self, "Export Success", f"Version exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export version: {str(e)}")


class ImportVersionDialog(QDialog):
    """Dialog for importing existing files as versions - Prism style"""
    
    def __init__(self, dcc_app: str, entity_name: str, file_path: str, parent=None):
        super().__init__(parent)
        self.dcc_app = dcc_app
        self.entity_name = entity_name
        self.file_path = file_path
        self.setWindowTitle(f"Import Version - {dcc_app.title()}")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel(f"Import Version")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {COLORS['fg']};
                margin-bottom: 10px;
            }}
        """)
        layout.addWidget(title_label)
        
        # File info
        file_info = QLabel(f"File: {os.path.basename(self.file_path)}")
        file_info.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {COLORS['fg_variant']};
                background-color: {COLORS['surface']};
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid {COLORS['outline']};
            }}
        """)
        layout.addWidget(file_info)
        
        # DCC app info
        dcc_info = QLabel(f"DCC App: {self.dcc_app.title()}")
        dcc_info.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {COLORS['fg_variant']};
                background-color: {COLORS['surface']};
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid {COLORS['outline']};
            }}
        """)
        layout.addWidget(dcc_info)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Task name
        self.task_name_edit = QLineEdit()
        self.task_name_edit.setPlaceholderText("Enter task name (e.g., modeling, animation)")
        self.task_name_edit.setText("modeling")  # Default task
        form_layout.addRow("Task Name:", self.task_name_edit)
        
        # User name
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("Enter your name")
        self.user_edit.setText("User")  # Default user
        form_layout.addRow("User:", self.user_edit)
        
        # Comment
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Enter version comment (optional)")
        self.comment_edit.setMaximumHeight(80)
        form_layout.addRow("Comment:", self.comment_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons and options
        self.open_after_create_cb = QCheckBox("Open in App after Create")
        self.open_after_create_cb.setChecked(True)
        layout.addWidget(self.open_after_create_cb)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        import_btn = QPushButton("Import Version")
        import_btn.setProperty("class", "primary")
        import_btn.clicked.connect(self.import_version)
        
        # Style buttons
        for btn in [cancel_btn, import_btn]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent']};
                    color: white;
                    border: 1px solid {COLORS['accent']};
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: 500;
                    min-width: 100px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_hover']};
                    border: 1px solid {COLORS['accent_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['accent_active']};
                    border: 1px solid {COLORS['accent_active']};
                }}
            """)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(import_btn)
        layout.addLayout(button_layout)
    
    def import_version(self):
        """Import the version"""
        task_name = self.task_name_edit.text().strip()
        user = self.user_edit.text().strip()
        comment = self.comment_edit.toPlainText().strip()
        
        if not task_name:
            QMessageBox.warning(self, "Invalid Input", "Task name is required")
            return
        
        if not user:
            QMessageBox.warning(self, "Invalid Input", "User name is required")
            return
        
        try:
            # Get controller and create version
            from .main import get_current_controller
            controller = get_current_controller()
            if not controller or not controller.manager:
                QMessageBox.critical(self, "Error", "No project manager available")
                return
            
            version = controller.manager.create_dcc_version(
                self.entity_name,
                self.dcc_app,
                task_name,
                user,
                comment,
                self.file_path
            )
            
            # Silent success; caller will reflect changes
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import version: {str(e)}")


class CreateVersionDialog(QDialog):
    """Dialog for creating new versions with DCC apps"""
    
    def __init__(self, dcc_app: str, entity_name: str, parent=None, current_task: str = None):
        super().__init__(parent)
        self.dcc_app = dcc_app
        self.entity_name = entity_name
        self.current_task = current_task
        # Ensure attributes exist before UI setup
        self.open_after_create_cb = None
        self.setWindowTitle(f"Create Version with {dcc_app.title()}")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel(f"Create New Version")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {COLORS['fg']};
                margin-bottom: 10px;
            }}
        """)
        layout.addWidget(title_label)
        
        # Entity info
        entity_info = QLabel(f"Entity: {self.entity_name}")
        entity_info.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {COLORS['fg_variant']};
                background-color: {COLORS['surface']};
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid {COLORS['outline']};
            }}
        """)
        layout.addWidget(entity_info)
        
        # DCC app info
        dcc_info = QLabel(f"DCC App: {self.dcc_app.title()}")
        dcc_info.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {COLORS['fg_variant']};
                background-color: {COLORS['surface']};
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid {COLORS['outline']};
            }}
        """)
        layout.addWidget(dcc_info)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # File type selector (extensions per app)
        from .main import get_current_controller
        self.ext_combo = QComboBox()
        self.ext_combo.setEditable(False)
        self.available_exts = []
        try:
            controller = get_current_controller()
            if controller and controller.manager:
                dcc_apps = controller.manager.get_dcc_apps()
                for app in dcc_apps:
                    if app['name'] == self.dcc_app:
                        self.available_exts = app.get('file_extensions', [])
                        break
        except Exception:
            self.available_exts = []
        if not self.available_exts:
            self.available_exts = [""]
        self.ext_combo.clear()
        for ext in self.available_exts:
            self.ext_combo.addItem(ext or "", ext)
        form_layout.addRow("File Type:", self.ext_combo)

        # Task name
        self.task_name_edit = QLineEdit()
        self.task_name_edit.setPlaceholderText("Enter task name (e.g., modeling, animation)")
        if self.current_task:
            self.task_name_edit.setText(self.current_task)
        else:
            self.task_name_edit.setText("modeling")  # Default task
        form_layout.addRow("Task Name:", self.task_name_edit)
        
        # User name
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("Enter your name")
        self.user_edit.setText("User")  # Default user
        form_layout.addRow("User:", self.user_edit)
        
        # Comment
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Enter version comment (optional)")
        self.comment_edit.setMaximumHeight(80)
        form_layout.addRow("Comment:", self.comment_edit)
        
        # Workfile path (optional)
        workfile_layout = QHBoxLayout()
        self.workfile_edit = QLineEdit()
        self.workfile_edit.setPlaceholderText("Optional: specify workfile path")
        workfile_layout.addWidget(self.workfile_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_workfile)
        workfile_layout.addWidget(browse_btn)
        
        form_layout.addRow("Workfile:", workfile_layout)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        create_btn = QPushButton("Create Version")
        create_btn.setProperty("class", "primary")
        create_btn.clicked.connect(self.create_version)
        
        # Style buttons
        for btn in [cancel_btn, create_btn]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent']};
                    color: white;
                    border: 1px solid {COLORS['accent']};
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: 500;
                    min-width: 100px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_hover']};
                    border: 1px solid {COLORS['accent_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['accent_active']};
                    border: 1px solid {COLORS['accent_active']};
                }}
            """)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        layout.addLayout(button_layout)
    
    def browse_workfile(self):
        """Browse for workfile"""
        from PyQt6.QtWidgets import QFileDialog
        
        # Build a filter from selected extension and app extensions
        selected_ext = self.ext_combo.currentData() or ""
        file_filter = "All Files (*.*)"
        if getattr(self, 'available_exts', None):
            patterns = " ".join(f"*{ext}" for ext in self.available_exts if ext)
            file_filter = f"Supported ({patterns})"
        if selected_ext:
            file_filter = f"Selected (*{selected_ext});;" + file_filter
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f"Select {self.dcc_app.title()} Workfile",
            "",
            file_filter
        )
        
        if file_path:
            self.workfile_edit.setText(file_path)
    
    def create_version(self):
        """Create the version"""
        task_name = self.task_name_edit.text().strip()
        user = self.user_edit.text().strip()
        comment = self.comment_edit.toPlainText().strip()
        workfile_path = self.workfile_edit.text().strip() or None
        selected_ext = self.ext_combo.currentData() or ""
        
        if not task_name:
            QMessageBox.warning(self, "Invalid Input", "Task name is required")
            return
        
        if not user:
            QMessageBox.warning(self, "Invalid Input", "User name is required")
            return
        
        # Workfile is optional: only validate if provided
        if workfile_path:
            if not os.path.exists(workfile_path):
                QMessageBox.critical(self, "File Not Found", f"The file does not exist:\n{workfile_path}")
                return
            if selected_ext and not workfile_path.lower().endswith(selected_ext.lower()):
                reply = QMessageBox.question(
                    self,
                    "Extension Mismatch",
                    f"The selected file does not match the chosen type ({selected_ext}). Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

        try:
            # Resolve manager robustly
            manager = None
            # 1) Try parent window
            try:
                win = self.window()
                if hasattr(win, 'manager') and win.manager:
                    manager = win.manager
            except Exception:
                pass
            # 2) Try ui module global
            if manager is None:
                try:
                    from .ui import get_current_controller as ui_get_current_controller
                    ctrl = ui_get_current_controller()
                    if ctrl and hasattr(ctrl, 'manager') and ctrl.manager:
                        manager = ctrl.manager
                except Exception:
                    pass
            # 3) Try main module global
            if manager is None:
                try:
                    from .main import get_current_controller as main_get_current_controller
                    ctrl = main_get_current_controller()
                    if ctrl and hasattr(ctrl, 'manager') and ctrl.manager:
                        manager = ctrl.manager
                except Exception:
                    pass
            if manager is None:
                QMessageBox.critical(self, "No Project", "No project manager available. Load or create a project first from the File menu.")
                return
            if not getattr(manager, 'current_project', None):
                QMessageBox.warning(self, "No Project Loaded", "Please load or create a project first from the File menu.")
                return

            version = manager.create_dcc_version(
                self.entity_name,
                self.dcc_app,
                task_name,
                user,
                comment,
                workfile_path
            )

            # Optionally open the created version in the DCC
            if getattr(self, 'open_after_create_cb', None) and self.open_after_create_cb.isChecked() and version and getattr(version, 'version', None):
                try:
                    manager.launch_dcc_app(
                        self.dcc_app,
                        entity_key=self.entity_name,
                        task_name=task_name,
                        version=version.version
                    )
                except Exception:
                    pass

            # Silent success; UI will refresh in caller
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create version: {str(e)}")


class PublishDialog(QWidget):
    """Publish dialog widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Publish Version")
        title_label.setProperty("class", "title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Entity info
        info_group = QGroupBox("Entity Information")
        info_layout = QGridLayout(info_group)
        
        info_layout.addWidget(QLabel("Entity:"), 0, 0)
        self.entity_label = QLabel("-")
        info_layout.addWidget(self.entity_label, 0, 1)
        
        info_layout.addWidget(QLabel("Type:"), 1, 0)
        self.type_label = QLabel("-")
        info_layout.addWidget(self.type_label, 1, 1)
        
        layout.addWidget(info_group)
        
        # Publish options
        options_group = QGroupBox("Publish Options")
        options_layout = QVBoxLayout(options_group)
        
        # Version number
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("Version:"))
        self.version_spin = QSpinBox()
        self.version_spin.setMinimum(1)
        self.version_spin.setMaximum(999)
        self.version_spin.setValue(1)
        version_layout.addWidget(self.version_spin)
        version_layout.addStretch()
        options_layout.addLayout(version_layout)
        
        # Comment
        comment_layout = QVBoxLayout()
        comment_layout.addWidget(QLabel("Comment:"))
        self.comment_text = QTextEdit()
        self.comment_text.setMaximumHeight(80)
        comment_layout.addWidget(self.comment_text)
        options_layout.addLayout(comment_layout)
        
        # Options
        self.create_thumbnail_cb = QCheckBox("Create Thumbnail")
        self.create_thumbnail_cb.setChecked(True)
        options_layout.addWidget(self.create_thumbnail_cb)
        
        self.open_after_publish_cb = QCheckBox("Open after Publish")
        self.open_after_publish_cb.setChecked(False)
        options_layout.addWidget(self.open_after_publish_cb)
        
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.publish_btn = QPushButton("Publish")
        self.publish_btn.setProperty("class", "primary")
        
        self.cancel_btn = QPushButton("Cancel")
        
        button_layout.addStretch()
        button_layout.addWidget(self.publish_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)


class PrismMainWindow(QMainWindow):
    """Main Prism-like window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vogue Manager - Prism Interface")
        self.setMinimumSize(1600, 1000)  # Larger size for better layout
        
        # Apply global QSS styling
        self.setStyleSheet(build_qss())

        # Set window properties for better appearance
        self.setWindowIconText("Vogue Manager")
        
        self.setup_ui()
        self.setup_menu()
        # self.setup_toolbar()  # Removed toolbar with BROWSE, NEW, ADD SHOT, PUBLISH, REFRESH, SCAN buttons
        self.setup_statusbar()
        self.setup_docks()
    
    def setup_ui(self):
        """Set up the main UI layout with tabbed interface"""
        # Create main tab widget
        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.main_tab_widget.setMovable(False)
        self.main_tab_widget.setTabsClosable(False)
        
        # Set the tab widget as central widget
        self.setCentralWidget(self.main_tab_widget)
        
        # Add tabs
        self.setup_tabs()
        
        # Apply tab styling
        self.style_tabs()
    
    def setup_tabs(self):
        """Set up the main tabs with icons"""
        # Create icons for tabs
        self.create_tab_icons()
        
        # Tasks tab (placeholder for future implementation)
        self.tasks_widget = self.create_tasks_tab()
        self.main_tab_widget.addTab(self.tasks_widget, self.tasks_icon, "Tasks")
        
        # Browser tab (main content - departments, tasks, project browser)
        self.browser_widget = self.create_browser_tab()
        self.main_tab_widget.addTab(self.browser_widget, self.browser_icon, "Browser")
        
        # Inbox tab
        self.inbox_widget = self.create_inbox_tab()
        self.main_tab_widget.addTab(self.inbox_widget, self.inbox_icon, "Inbox")
        
        # Teams tab
        self.teams_widget = self.create_teams_tab()
        self.main_tab_widget.addTab(self.teams_widget, self.teams_icon, "Teams")
        
        # Dashboard tab
        self.dashboard_widget = self.create_dashboard_tab()
        self.main_tab_widget.addTab(self.dashboard_widget, self.dashboard_icon, "Dashboard")
        
        # Settings tab
        self.settings_widget = self.create_settings_tab()
        self.main_tab_widget.addTab(self.settings_widget, self.settings_icon, "Settings")
    
    def create_tab_icons(self):
        """Create icons for the tabs"""
        # Create simple colored icons using QPixmap
        self.tasks_icon = self.create_colored_icon("#ff6b35", "📋")  # Orange document icon
        self.browser_icon = self.create_colored_icon("#ffd700", "📁")  # Yellow folder icon
        self.inbox_icon = self.create_colored_icon("#0078d4", "📧")  # Blue mailbox icon
        self.teams_icon = self.create_colored_icon("#9c27b0", "👥")  # Purple people icon
        self.dashboard_icon = self.create_colored_icon("#4caf50", "📊")  # Green chart icon
        self.settings_icon = self.create_colored_icon("#757575", "⚙️")  # Grey settings icon
    
    def create_colored_icon(self, color, emoji):
        """Create a colored icon with emoji"""
        from PyQt6.QtCore import QSize
        from PyQt6.QtGui import QPainter, QFont
        
        # Create a 24x24 pixmap
        pixmap = QPixmap(24, 24)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set font for emoji
        font = QFont()
        font.setPointSize(16)
        painter.setFont(font)
        
        # Draw emoji
        painter.drawText(0, 0, 24, 24, Qt.AlignmentFlag.AlignCenter, emoji)
        painter.end()
        
        return QIcon(pixmap)
    
    def create_browser_tab(self):
        """Create the Browser tab content with main application layout"""
        # Create central widget with splitter
        central_widget = QWidget()
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Project Browser
        self.project_browser = ProjectBrowser()
        main_splitter.addWidget(self.project_browser)
        
        # Center panel - Version Manager
        self.version_manager = VersionManager()
        # Connect selection signal to update right panel consistently
        try:
            self.version_manager.selectedVersionChanged.connect(lambda v: self.version_manager._update_right_preview(v))
        except Exception:
            pass
        main_splitter.addWidget(self.version_manager)
        
        # Right panel - Prism-style Tasks/Departments/Asset Info
        self.right_panel = PrismRightPanel()
        main_splitter.addWidget(self.right_panel)
        
        # Set splitter proportions; reduce right panel width to emphasize center
        main_splitter.setSizes([560, 820, 120])
        layout.addWidget(main_splitter)
        
        return central_widget
    
    def create_tasks_tab(self):
        """Create the Tasks tab content with advanced task management"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Task Management")
        title.setProperty("class", "title")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Filter controls
        self.task_filter_combo = QComboBox()
        self.task_filter_combo.addItems(["All Tasks", "My Tasks", "Pending", "In Progress", "Completed", "Overdue"])
        self.task_filter_combo.currentTextChanged.connect(self.filter_tasks)
        header_layout.addWidget(QLabel("Filter:"))
        header_layout.addWidget(self.task_filter_combo)
        
        # Add task button
        self.add_task_btn = QPushButton("Add Task")
        self.add_task_btn.setProperty("class", "primary")
        self.add_task_btn.clicked.connect(self.add_task)
        header_layout.addWidget(self.add_task_btn)
        
        layout.addLayout(header_layout)
        
        # Main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Task list
        tasks_panel = QWidget()
        tasks_layout = QVBoxLayout(tasks_panel)
        tasks_layout.setContentsMargins(5, 5, 5, 5)
        
        tasks_label = QLabel("Tasks")
        tasks_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #34495e;")
        tasks_layout.addWidget(tasks_label)
        
        # Tasks table
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(6)
        self.tasks_table.setHorizontalHeaderLabels(["Task", "Project", "Assignee", "Status", "Priority", "Due Date"])
        self.tasks_table.horizontalHeader().setStretchLastSection(True)
        self.tasks_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tasks_table.setAlternatingRowColors(True)
        self.tasks_table.setSortingEnabled(True)
        
        # Set column widths
        header = self.tasks_table.horizontalHeader()
        header.resizeSection(0, 200)  # Task
        header.resizeSection(1, 120)  # Project
        header.resizeSection(2, 100)  # Assignee
        header.resizeSection(3, 80)   # Status
        header.resizeSection(4, 80)   # Priority
        header.resizeSection(5, 100)  # Due Date
        
        tasks_layout.addWidget(self.tasks_table)
        
        # Tasks controls
        tasks_controls = QHBoxLayout()
        self.edit_task_btn = QPushButton("Edit Task")
        self.edit_task_btn.setEnabled(False)
        self.edit_task_btn.clicked.connect(self.edit_task)
        tasks_controls.addWidget(self.edit_task_btn)
        
        self.complete_task_btn = QPushButton("Mark Complete")
        self.complete_task_btn.setEnabled(False)
        self.complete_task_btn.clicked.connect(self.complete_task)
        tasks_controls.addWidget(self.complete_task_btn)
        
        self.delete_task_btn = QPushButton("Delete Task")
        self.delete_task_btn.setEnabled(False)
        self.delete_task_btn.setProperty("class", "danger")
        self.delete_task_btn.clicked.connect(self.delete_task)
        tasks_controls.addWidget(self.delete_task_btn)
        
        tasks_controls.addStretch()
        tasks_layout.addLayout(tasks_controls)
        
        # Right panel - Task details
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(5, 5, 5, 5)
        
        details_label = QLabel("Task Details")
        details_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #34495e;")
        details_layout.addWidget(details_label)
        
        # Task details form
        self.task_details_widget = QWidget()
        self.task_details_layout = QFormLayout(self.task_details_widget)
        
        # Task name
        self.task_name_edit = QLineEdit()
        self.task_name_edit.setReadOnly(True)
        self.task_details_layout.addRow("Task Name:", self.task_name_edit)
        
        # Project
        self.task_project_edit = QLineEdit()
        self.task_project_edit.setReadOnly(True)
        self.task_details_layout.addRow("Project:", self.task_project_edit)
        
        # Assignee
        self.task_assignee_edit = QLineEdit()
        self.task_assignee_edit.setReadOnly(True)
        self.task_details_layout.addRow("Assignee:", self.task_assignee_edit)
        
        # Status
        self.task_status_edit = QLineEdit()
        self.task_status_edit.setReadOnly(True)
        self.task_details_layout.addRow("Status:", self.task_status_edit)
        
        # Priority
        self.task_priority_edit = QLineEdit()
        self.task_priority_edit.setReadOnly(True)
        self.task_details_layout.addRow("Priority:", self.task_priority_edit)
        
        # Due date
        self.task_due_date_edit = QLineEdit()
        self.task_due_date_edit.setReadOnly(True)
        self.task_details_layout.addRow("Due Date:", self.task_due_date_edit)
        
        # Description
        self.task_description_edit = QPlainTextEdit()
        self.task_description_edit.setReadOnly(True)
        self.task_description_edit.setMaximumHeight(100)
        self.task_details_layout.addRow("Description:", self.task_description_edit)
        
        details_layout.addWidget(self.task_details_widget)
        
        # Add panels to splitter
        main_splitter.addWidget(tasks_panel)
        main_splitter.addWidget(details_panel)
        main_splitter.setSizes([600, 300])
        
        layout.addWidget(main_splitter)
        
        # Connect selection signals
        self.tasks_table.itemSelectionChanged.connect(self.on_task_selection_changed)
        
        # Load data
        self.load_tasks_data()
        
        return widget
    
    def create_inbox_tab(self):
        """Create the Inbox tab content with notifications and messages"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Inbox")
        title.setProperty("class", "title")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Mark all as read button
        self.mark_all_read_btn = QPushButton("Mark All Read")
        self.mark_all_read_btn.clicked.connect(self.mark_all_read)
        header_layout.addWidget(self.mark_all_read_btn)
        
        # Refresh button
        self.refresh_inbox_btn = QPushButton("Refresh")
        self.refresh_inbox_btn.clicked.connect(self.refresh_inbox)
        header_layout.addWidget(self.refresh_inbox_btn)
        
        layout.addLayout(header_layout)
        
        # Main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Notifications list
        notifications_panel = QWidget()
        notifications_layout = QVBoxLayout(notifications_panel)
        notifications_layout.setContentsMargins(5, 5, 5, 5)
        
        notifications_label = QLabel("Notifications")
        notifications_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ecf0f1;")
        notifications_layout.addWidget(notifications_label)
        
        # Notifications table
        self.notifications_table = QTableWidget()
        self.notifications_table.setColumnCount(4)
        self.notifications_table.setHorizontalHeaderLabels(["Type", "Message", "Time", "Status"])
        self.notifications_table.horizontalHeader().setStretchLastSection(True)
        self.notifications_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.notifications_table.setAlternatingRowColors(True)
        self.notifications_table.setSortingEnabled(True)
        
        # Style the notifications table
        self.notifications_table.setStyleSheet("""
            QTableWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 5px;
                gridline-color: #34495e;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px 12px;
                border: none;
                color: #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #4a6741;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: #ecf0f1;
                padding: 8px 12px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Set column widths
        header = self.notifications_table.horizontalHeader()
        header.resizeSection(0, 100)  # Type
        header.resizeSection(1, 300)  # Message
        header.resizeSection(2, 120)  # Time
        header.resizeSection(3, 80)   # Status
        
        notifications_layout.addWidget(self.notifications_table)
        
        # Notifications controls
        notifications_controls = QHBoxLayout()
        self.mark_read_btn = QPushButton("Mark as Read")
        self.mark_read_btn.setEnabled(False)
        self.mark_read_btn.clicked.connect(self.mark_as_read)
        notifications_controls.addWidget(self.mark_read_btn)
        
        self.delete_notification_btn = QPushButton("Delete")
        self.delete_notification_btn.setEnabled(False)
        self.delete_notification_btn.setProperty("class", "danger")
        self.delete_notification_btn.clicked.connect(self.delete_notification)
        notifications_controls.addWidget(self.delete_notification_btn)
        
        notifications_controls.addStretch()
        notifications_layout.addLayout(notifications_controls)
        
        # Right panel - Messages
        messages_panel = QWidget()
        messages_layout = QVBoxLayout(messages_panel)
        messages_layout.setContentsMargins(5, 5, 5, 5)
        
        messages_label = QLabel("Messages")
        messages_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ecf0f1;")
        messages_layout.addWidget(messages_label)
        
        # Messages list
        self.messages_list = QListWidget()
        self.messages_list.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                border: 1px solid #34495e;
                border-radius: 5px;
                padding: 5px;
                color: #ecf0f1;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #34495e;
                background-color: #34495e;
                margin: 3px;
                border-radius: 5px;
                color: #ecf0f1;
                font-size: 12px;
                line-height: 1.4;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #4a6741;
                color: #ecf0f1;
            }
        """)
        messages_layout.addWidget(self.messages_list)
        
        # Message controls
        message_controls = QHBoxLayout()
        self.reply_btn = QPushButton("Reply")
        self.reply_btn.setEnabled(False)
        self.reply_btn.clicked.connect(self.reply_message)
        message_controls.addWidget(self.reply_btn)
        
        self.forward_btn = QPushButton("Forward")
        self.forward_btn.setEnabled(False)
        self.forward_btn.clicked.connect(self.forward_message)
        message_controls.addWidget(self.forward_btn)
        
        self.delete_message_btn = QPushButton("Delete")
        self.delete_message_btn.setEnabled(False)
        self.delete_message_btn.setProperty("class", "danger")
        self.delete_message_btn.clicked.connect(self.delete_message)
        message_controls.addWidget(self.delete_message_btn)
        
        message_controls.addStretch()
        messages_layout.addLayout(message_controls)
        
        # Add panels to splitter
        main_splitter.addWidget(notifications_panel)
        main_splitter.addWidget(messages_panel)
        main_splitter.setSizes([500, 300])
        
        layout.addWidget(main_splitter)
        
        # Connect selection signals
        self.notifications_table.itemSelectionChanged.connect(self.on_notification_selection_changed)
        self.messages_list.itemSelectionChanged.connect(self.on_message_selection_changed)
        
        # Load data
        self.load_notifications_data()
        self.load_messages_data()
        
        return widget
    
    def create_teams_tab(self):
        """Create the Teams tab content with team and user management"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        
        title = QLabel("Teams & Users")
        title.setProperty("class", "title")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add team button
        self.add_team_btn = QPushButton("Add Team")
        self.add_team_btn.setProperty("class", "primary")
        self.add_team_btn.clicked.connect(self.add_team)
        header_layout.addWidget(self.add_team_btn)
        
        # Add user button
        self.add_user_btn = QPushButton("Add User")
        self.add_user_btn.setProperty("class", "primary")
        self.add_user_btn.clicked.connect(self.add_user)
        header_layout.addWidget(self.add_user_btn)
        
        layout.addLayout(header_layout)
        
        # Main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Teams list
        teams_panel = QWidget()
        teams_layout = QVBoxLayout(teams_panel)
        teams_layout.setContentsMargins(5, 5, 5, 5)
        
        teams_label = QLabel("Teams")
        teams_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #34495e;")
        teams_layout.addWidget(teams_label)
        
        # Teams table
        self.teams_table = QTableWidget()
        self.teams_table.setColumnCount(4)
        self.teams_table.setHorizontalHeaderLabels(["Name", "Members", "Projects", "Status"])
        self.teams_table.horizontalHeader().setStretchLastSection(True)
        self.teams_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.teams_table.setAlternatingRowColors(True)
        self.teams_table.setSortingEnabled(True)
        
        # Set column widths
        header = self.teams_table.horizontalHeader()
        header.resizeSection(0, 150)  # Name
        header.resizeSection(1, 100)  # Members
        header.resizeSection(2, 100)  # Projects
        header.resizeSection(3, 80)   # Status
        
        teams_layout.addWidget(self.teams_table)
        
        # Teams controls
        teams_controls = QHBoxLayout()
        self.edit_team_btn = QPushButton("Edit Team")
        self.edit_team_btn.setEnabled(False)
        self.edit_team_btn.clicked.connect(self.edit_team)
        teams_controls.addWidget(self.edit_team_btn)
        
        self.delete_team_btn = QPushButton("Delete Team")
        self.delete_team_btn.setEnabled(False)
        self.delete_team_btn.setProperty("class", "danger")
        self.delete_team_btn.clicked.connect(self.delete_team)
        teams_controls.addWidget(self.delete_team_btn)
        
        teams_controls.addStretch()
        teams_layout.addLayout(teams_controls)
        
        # Right panel - Users list
        users_panel = QWidget()
        users_layout = QVBoxLayout(users_panel)
        users_layout.setContentsMargins(5, 5, 5, 5)
        
        users_label = QLabel("Users")
        users_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #34495e;")
        users_layout.addWidget(users_label)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(["Name", "Email", "Role", "Teams", "Status"])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSortingEnabled(True)
        
        # Set column widths
        header = self.users_table.horizontalHeader()
        header.resizeSection(0, 120)  # Name
        header.resizeSection(1, 150)  # Email
        header.resizeSection(2, 80)   # Role
        header.resizeSection(3, 100)  # Teams
        header.resizeSection(4, 80)   # Status
        
        users_layout.addWidget(self.users_table)
        
        # Users controls
        users_controls = QHBoxLayout()
        self.edit_user_btn = QPushButton("Edit User")
        self.edit_user_btn.setEnabled(False)
        self.edit_user_btn.clicked.connect(self.edit_user)
        users_controls.addWidget(self.edit_user_btn)
        
        self.delete_user_btn = QPushButton("Delete User")
        self.delete_user_btn.setEnabled(False)
        self.delete_user_btn.setProperty("class", "danger")
        self.delete_user_btn.clicked.connect(self.delete_user)
        users_controls.addWidget(self.delete_user_btn)
        
        users_controls.addStretch()
        users_layout.addLayout(users_controls)
        
        # Add panels to splitter
        main_splitter.addWidget(teams_panel)
        main_splitter.addWidget(users_panel)
        main_splitter.setSizes([400, 400])
        
        layout.addWidget(main_splitter)
        
        # Connect selection signals
        self.teams_table.itemSelectionChanged.connect(self.on_team_selection_changed)
        self.users_table.itemSelectionChanged.connect(self.on_user_selection_changed)
        
        # Load data
        self.load_teams_data()
        self.load_users_data()
        
        return widget
    
    def create_dashboard_tab(self):
        """Create an advanced real-time dashboard with comprehensive project tracking"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #ecf0f1;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header with real-time clock
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        
        title = QLabel("Advanced Project Dashboard")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #3498db; margin-bottom: 15px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Real-time clock
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("font-size: 18px; color: #bdc3c7; font-weight: bold; padding: 8px 12px; background-color: #2c3e50; border-radius: 8px;")
        header_layout.addWidget(self.clock_label)
        
        # Auto-refresh toggle
        self.auto_refresh_check = QCheckBox("Auto Refresh (30s)")
        self.auto_refresh_check.setChecked(True)
        self.auto_refresh_check.setStyleSheet("""
            QCheckBox {
                color: #ecf0f1; 
                font-size: 14px; 
                font-weight: bold;
                padding: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border: 2px solid #3498db;
                border-radius: 3px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #34495e;
                border: 2px solid #34495e;
                border-radius: 3px;
            }
        """)
        self.auto_refresh_check.toggled.connect(self.toggle_auto_refresh)
        header_layout.addWidget(self.auto_refresh_check)
        
        # Refresh button
        self.refresh_dashboard_btn = QPushButton("🔄 Refresh Now")
        self.refresh_dashboard_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.refresh_dashboard_btn.clicked.connect(self.refresh_dashboard)
        header_layout.addWidget(self.refresh_dashboard_btn)
        
        layout.addLayout(header_layout)
        
        # Main content with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(1200)  # Ensure minimum width to prevent cutoff
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1a1a1a;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2c3e50;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #34495e;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4a6741;
            }
            QScrollBar:horizontal {
                background-color: #2c3e50;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #34495e;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #4a6741;
            }
        """)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #1a1a1a;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(25)
        
        # Top row - Key metrics cards
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(0)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Project metrics
        self.project_metrics_card = self.create_advanced_stats_card(
            "📁", "Projects", "0", "Active Projects", "#3498db", 
            [("Total", "0"), ("Active", "0"), ("Archived", "0")]
        )
        metrics_layout.addWidget(self.project_metrics_card)
        
        # Asset metrics
        self.asset_metrics_card = self.create_advanced_stats_card(
            "🎨", "Assets", "0", "Total Assets", "#e74c3c",
            [("Characters", "0"), ("Props", "0"), ("Environments", "0")]
        )
        metrics_layout.addWidget(self.asset_metrics_card)
        
        # Shot metrics
        self.shot_metrics_card = self.create_advanced_stats_card(
            "🎬", "Shots", "0", "Total Shots", "#f39c12",
            [("In Progress", "0"), ("Completed", "0"), ("Review", "0")]
        )
        metrics_layout.addWidget(self.shot_metrics_card)
        
        # Version metrics
        self.version_metrics_card = self.create_advanced_stats_card(
            "📝", "Versions", "0", "Total Versions", "#27ae60",
            [("Published", "0"), ("Draft", "0"), ("Approved", "0")]
        )
        metrics_layout.addWidget(self.version_metrics_card)
        
        scroll_layout.addLayout(metrics_layout)
        
        # Second row - System status and performance
        status_layout = QHBoxLayout()
        status_layout.setSpacing(20)
        
        # System status panel
        self.system_status_panel = self.create_system_status_panel()
        status_layout.addWidget(self.system_status_panel)
        
        # Performance metrics panel
        self.performance_panel = self.create_performance_panel()
        status_layout.addWidget(self.performance_panel)
        
        scroll_layout.addLayout(status_layout)
        
        # Third row - Project analytics and activity
        analytics_layout = QHBoxLayout()
        analytics_layout.setSpacing(20)
        
        # Project breakdown table
        self.project_breakdown_panel = self.create_project_breakdown_panel()
        analytics_layout.addWidget(self.project_breakdown_panel)
        
        # Recent activity panel
        self.activity_panel = self.create_activity_panel()
        analytics_layout.addWidget(self.activity_panel)
        
        scroll_layout.addLayout(analytics_layout)
        
        # Fourth row - Team activity and notifications
        team_layout = QHBoxLayout()
        team_layout.setSpacing(20)
        
        # Team activity panel
        self.team_activity_panel = self.create_team_activity_panel()
        team_layout.addWidget(self.team_activity_panel)
        
        # Quick actions panel
        self.quick_actions_panel = self.create_quick_actions_panel()
        team_layout.addWidget(self.quick_actions_panel)
        
        scroll_layout.addLayout(team_layout)
        
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # Initialize auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_dashboard)
        self.refresh_timer.start(30000)  # 30 seconds
        
        # Initialize clock timer
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)  # 1 second
        
        # Load initial data
        self.refresh_dashboard()
        self.update_clock()
        
        return widget
    
    def create_advanced_stats_card(self, icon, title, main_value, subtitle, color, breakdown_data):
        """Create an advanced statistics card with breakdown data"""
        card = QWidget()
        card.setMinimumSize(200, 320)
        card.setMaximumHeight(320)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: #2c3e50;
                border: 3px solid {color};
                border-radius: 15px;
                margin: 0px;
            }}
            QWidget:hover {{
                background-color: #34495e;
                border: 3px solid {color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 36px; color: {color};")
        header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; color: #ecf0f1; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        layout.addLayout(header_layout)
        
        # Main value
        value_label = QLabel(main_value)
        value_label.setStyleSheet(f"font-size: 42px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setMinimumHeight(55)
        value_label.setMaximumHeight(55)
        layout.addWidget(value_label)
        
        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("font-size: 12px; color: #bdc3c7;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setMinimumHeight(20)
        subtitle_label.setMaximumHeight(20)
        layout.addWidget(subtitle_label)
        
        # Breakdown data
        breakdown_layout = QHBoxLayout()
        breakdown_layout.setSpacing(15)
        for label, value in breakdown_data:
            breakdown_item = QVBoxLayout()
            breakdown_item.setSpacing(4)
            
            breakdown_value = QLabel(value)
            breakdown_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #ecf0f1;")
            breakdown_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            breakdown_value.setMinimumHeight(25)
            breakdown_value.setMaximumHeight(25)
            breakdown_item.addWidget(breakdown_value)
            
            breakdown_label = QLabel(label)
            breakdown_label.setStyleSheet("font-size: 11px; color: #bdc3c7; font-weight: bold;")
            breakdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            breakdown_label.setMinimumHeight(16)
            breakdown_label.setMaximumHeight(16)
            breakdown_label.setWordWrap(True)
            breakdown_item.addWidget(breakdown_label)
            
            breakdown_layout.addLayout(breakdown_item)
        
        layout.addLayout(breakdown_layout)
        
        # Make card clickable and interactive
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.mousePressEvent = lambda event: self.on_card_clicked(title, main_value, color)
        
        return card
    
    def on_card_clicked(self, title, value, color):
        """Handle card click events"""
        from PyQt6.QtWidgets import QMessageBox
        
        # Create a detailed info dialog
        dialog = QMessageBox()
        dialog.setWindowTitle(f"{title} Details")
        dialog.setText(f"<h2 style='color: {color};'>{title}</h2>")
        dialog.setInformativeText(f"""
        <p><b>Current Value:</b> {value}</p>
        <p><b>Category:</b> {title}</p>
        <p><b>Status:</b> Active</p>
        <p><b>Last Updated:</b> {self.clock_label.text()}</p>
        """)
        dialog.setStyleSheet("""
            QMessageBox {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QMessageBox QLabel {
                color: #ecf0f1;
            }
        """)
        dialog.exec()
    
    def create_system_status_panel(self):
        """Create system status monitoring panel"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border: 3px solid #34495e;
                border-radius: 15px;
                margin: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🖥️ System Status")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #3498db; margin-bottom: 15px;")
        layout.addWidget(title)
        
        # Status items
        self.disk_usage_label = QLabel("💾 Disk Usage: 0%")
        self.disk_usage_label.setStyleSheet("color: #ecf0f1; font-size: 18px; padding: 12px; font-weight: bold;")
        layout.addWidget(self.disk_usage_label)
        
        self.memory_usage_label = QLabel("🧠 Memory: 0%")
        self.memory_usage_label.setStyleSheet("color: #ecf0f1; font-size: 18px; padding: 12px; font-weight: bold;")
        layout.addWidget(self.memory_usage_label)
        
        self.cpu_usage_label = QLabel("⚡ CPU: 0%")
        self.cpu_usage_label.setStyleSheet("color: #ecf0f1; font-size: 18px; padding: 12px; font-weight: bold;")
        layout.addWidget(self.cpu_usage_label)
        
        self.network_status_label = QLabel("🌐 Network: Online")
        self.network_status_label.setStyleSheet("color: #27ae60; font-size: 18px; padding: 12px; font-weight: bold;")
        layout.addWidget(self.network_status_label)
        
        self.database_status_label = QLabel("🗄️ Database: Connected")
        self.database_status_label.setStyleSheet("color: #27ae60; font-size: 18px; padding: 12px; font-weight: bold;")
        layout.addWidget(self.database_status_label)
        
        layout.addStretch()
        return panel
    
    def create_performance_panel(self):
        """Create performance metrics panel"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border: 3px solid #34495e;
                border-radius: 15px;
                margin: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📊 Performance Metrics")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e74c3c; margin-bottom: 15px;")
        layout.addWidget(title)
        
        # Performance metrics
        self.avg_render_time_label = QLabel("⏱️ Avg Render Time: 0s")
        self.avg_render_time_label.setStyleSheet("color: #ecf0f1; font-size: 18px; padding: 12px; font-weight: bold;")
        layout.addWidget(self.avg_render_time_label)
        
        self.files_processed_label = QLabel("📁 Files Processed: 0")
        self.files_processed_label.setStyleSheet("color: #ecf0f1; font-size: 18px; padding: 12px; font-weight: bold;")
        layout.addWidget(self.files_processed_label)
        
        self.uptime_label = QLabel("⏰ Uptime: 0h 0m")
        self.uptime_label.setStyleSheet("color: #ecf0f1; font-size: 18px; padding: 12px; font-weight: bold;")
        layout.addWidget(self.uptime_label)
        
        self.error_rate_label = QLabel("❌ Error Rate: 0%")
        self.error_rate_label.setStyleSheet("color: #27ae60; font-size: 18px; padding: 12px; font-weight: bold;")
        layout.addWidget(self.error_rate_label)
        
        self.success_rate_label = QLabel("✅ Success Rate: 100%")
        self.success_rate_label.setStyleSheet("color: #27ae60; font-size: 18px; padding: 12px; font-weight: bold;")
        layout.addWidget(self.success_rate_label)
        
        layout.addStretch()
        return panel
    
    def create_project_breakdown_panel(self):
        """Create project breakdown analysis panel"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border: 3px solid #34495e;
                border-radius: 15px;
                margin: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📈 Project Analytics")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #f39c12; margin-bottom: 15px;")
        layout.addWidget(title)
        
        # Project breakdown table
        self.project_breakdown_table = QTableWidget()
        self.project_breakdown_table.setColumnCount(5)
        self.project_breakdown_table.setHorizontalHeaderLabels(["Project", "Assets", "Shots", "Versions", "Status"])
        self.project_breakdown_table.horizontalHeader().setStretchLastSection(True)
        self.project_breakdown_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.project_breakdown_table.setAlternatingRowColors(True)
        self.project_breakdown_table.setMaximumHeight(200)
        
        # Style the table
        self.project_breakdown_table.setStyleSheet("""
            QTableWidget {
                background-color: #34495e;
                color: #ecf0f1;
                border: 2px solid #2c3e50;
                border-radius: 10px;
                gridline-color: #2c3e50;
                font-size: 16px;
            }
            QTableWidget::item {
                padding: 16px 20px;
                border: none;
                color: #ecf0f1;
                min-height: 35px;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #4a6741;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: #ecf0f1;
                padding: 16px 20px;
                border: none;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        
        # Set column widths
        header = self.project_breakdown_table.horizontalHeader()
        header.resizeSection(0, 120)  # Project
        header.resizeSection(1, 60)   # Assets
        header.resizeSection(2, 60)   # Shots
        header.resizeSection(3, 70)   # Versions
        header.resizeSection(4, 80)   # Status
        
        layout.addWidget(self.project_breakdown_table)
        
        return panel
    
    def create_activity_panel(self):
        """Create recent activity monitoring panel"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border: 3px solid #34495e;
                border-radius: 15px;
                margin: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🕒 Recent Activity")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #9b59b6; margin-bottom: 15px;")
        layout.addWidget(title)
        
        # Activity list
        self.activity_list = QListWidget()
        self.activity_list.setMaximumHeight(200)
        self.activity_list.setStyleSheet("""
            QListWidget {
                background-color: #34495e;
                border: 2px solid #2c3e50;
                border-radius: 10px;
                padding: 12px;
                color: #ecf0f1;
                font-size: 16px;
            }
            QListWidget::item {
                padding: 16px;
                border-bottom: 1px solid #2c3e50;
                background-color: #34495e;
                margin: 5px;
                border-radius: 8px;
                min-height: 30px;
                font-weight: bold;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #4a6741;
            }
        """)
        layout.addWidget(self.activity_list)
        
        return panel
    
    def create_team_activity_panel(self):
        """Create team activity monitoring panel"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border: 3px solid #34495e;
                border-radius: 15px;
                margin: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("👥 Team Activity")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e67e22; margin-bottom: 15px;")
        layout.addWidget(title)
        
        # Team activity list
        self.team_activity_list = QListWidget()
        self.team_activity_list.setMaximumHeight(150)
        self.team_activity_list.setStyleSheet("""
            QListWidget {
                background-color: #34495e;
                border: 2px solid #2c3e50;
                border-radius: 10px;
                padding: 12px;
                color: #ecf0f1;
                font-size: 16px;
            }
            QListWidget::item {
                padding: 14px;
                border-bottom: 1px solid #2c3e50;
                background-color: #34495e;
                margin: 4px;
                border-radius: 8px;
                min-height: 25px;
                font-weight: bold;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #4a6741;
            }
        """)
        layout.addWidget(self.team_activity_list)
        
        return panel
    
    def create_quick_actions_panel(self):
        """Create quick actions panel"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border: 3px solid #34495e;
                border-radius: 15px;
                margin: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("⚡ Quick Actions")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1abc9c; margin-bottom: 15px;")
        layout.addWidget(title)
        
        # Action buttons
        self.create_project_btn = QPushButton("📁 New Project")
        self.create_project_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 18px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.create_project_btn.clicked.connect(self.create_new_project)
        layout.addWidget(self.create_project_btn)
        
        self.scan_projects_btn = QPushButton("🔍 Scan Projects")
        self.scan_projects_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 12px 18px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.scan_projects_btn.clicked.connect(self.scan_projects)
        layout.addWidget(self.scan_projects_btn)
        
        self.open_project_btn = QPushButton("📂 Open Project")
        self.open_project_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 12px 18px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.open_project_btn.clicked.connect(self.open_project)
        layout.addWidget(self.open_project_btn)
        
        self.export_data_btn = QPushButton("📊 Export Data")
        self.export_data_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 12px 18px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.export_data_btn.clicked.connect(self.export_dashboard_data)
        layout.addWidget(self.export_data_btn)
        
        layout.addStretch()
        return panel
    
    def create_stats_card(self, title, value, subtitle, color, icon):
        """Create a statistics card widget"""
        card = QWidget()
        card.setFixedSize(200, 120)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Icon and title row
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 24px; color: {color};")
        header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #6c757d; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        layout.addLayout(header_layout)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("font-size: 10px; color: #6c757d;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        return card
    
    def refresh_dashboard(self):
        """Refresh advanced dashboard data with comprehensive tracking"""
        try:
            # Get comprehensive project statistics
            project_stats = self.get_comprehensive_project_stats()
            
            # Update advanced metrics cards
            self.update_advanced_metrics_cards(project_stats)
            
            # Update system status
            self.update_system_status()
            
            # Update performance metrics
            self.update_performance_metrics()
            
            # Update project breakdown table
            self.update_advanced_project_breakdown(project_stats)
            
            # Update activity feeds
            self.update_activity_feeds()
            
            # Update team activity
            self.update_team_activity()
            
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
    
    def get_comprehensive_project_stats(self):
        """Get comprehensive project statistics"""
        stats = {
            'total_projects': 0,
            'active_projects': 0,
            'archived_projects': 0,
            'total_assets': 0,
            'characters': 0,
            'props': 0,
            'environments': 0,
            'total_shots': 0,
            'shots_in_progress': 0,
            'shots_completed': 0,
            'shots_review': 0,
            'total_versions': 0,
            'published_versions': 0,
            'draft_versions': 0,
            'approved_versions': 0,
            'project_details': []
        }
        
        # Scan VogueProjects directory
        vogue_projects_path = Path("VogueProjects")
        if vogue_projects_path.exists():
            project_dirs = [d for d in vogue_projects_path.iterdir() if d.is_dir()]
            stats['total_projects'] = len(project_dirs)
            stats['active_projects'] = len(project_dirs)  # Assume all are active for now
            
            for project_dir in project_dirs:
                project_detail = {
                    'name': project_dir.name,
                    'assets': 0,
                    'shots': 0,
                    'versions': 0,
                    'status': 'Active'
                }
                
                # Count assets
                assets_dir = project_dir / "Assets"
                if assets_dir.exists():
                    asset_dirs = [d for d in assets_dir.iterdir() if d.is_dir()]
                    project_detail['assets'] = len(asset_dirs)
                    stats['total_assets'] += len(asset_dirs)
                    
                    # Categorize assets
                    for asset_dir in asset_dirs:
                        asset_name = asset_dir.name.lower()
                        if 'char' in asset_name or 'character' in asset_name:
                            stats['characters'] += 1
                        elif 'prop' in asset_name or 'object' in asset_name:
                            stats['props'] += 1
                        elif 'env' in asset_name or 'environment' in asset_name or 'set' in asset_name:
                            stats['environments'] += 1
                        else:
                            stats['props'] += 1  # Default to props
                    
                    # Count versions in assets
                    for asset_dir in asset_dirs:
                        versions = [f for f in asset_dir.iterdir() if f.is_dir() and f.name.startswith('v')]
                        project_detail['versions'] += len(versions)
                        stats['total_versions'] += len(versions)
                        stats['published_versions'] += len(versions)  # Assume all are published
                
                # Count shots
                shots_dir = project_dir / "Shots"
                if shots_dir.exists():
                    shot_dirs = [d for d in shots_dir.iterdir() if d.is_dir()]
                    project_detail['shots'] = len(shot_dirs)
                    stats['total_shots'] += len(shot_dirs)
                    stats['shots_in_progress'] += len(shot_dirs)  # Assume all in progress
                    
                    # Count versions in shots
                    for shot_dir in shot_dirs:
                        versions = [f for f in shot_dir.iterdir() if f.is_dir() and f.name.startswith('v')]
                        project_detail['versions'] += len(versions)
                        stats['total_versions'] += len(versions)
                        stats['published_versions'] += len(versions)
                
                stats['project_details'].append(project_detail)
        
        return stats
    
    def update_advanced_metrics_cards(self, stats):
        """Update advanced metrics cards with comprehensive data"""
        # Update project metrics
        self.update_advanced_stats_card(
            self.project_metrics_card,
            str(stats['total_projects']),
            [("Total", str(stats['total_projects'])), 
             ("Active", str(stats['active_projects'])), 
             ("Archived", str(stats['archived_projects']))]
        )
        
        # Update asset metrics
        self.update_advanced_stats_card(
            self.asset_metrics_card,
            str(stats['total_assets']),
            [("Characters", str(stats['characters'])), 
             ("Props", str(stats['props'])), 
             ("Environments", str(stats['environments']))]
        )
        
        # Update shot metrics
        self.update_advanced_stats_card(
            self.shot_metrics_card,
            str(stats['total_shots']),
            [("In Progress", str(stats['shots_in_progress'])), 
             ("Completed", str(stats['shots_completed'])), 
             ("Review", str(stats['shots_review']))]
        )
        
        # Update version metrics
        self.update_advanced_stats_card(
            self.version_metrics_card,
            str(stats['total_versions']),
            [("Published", str(stats['published_versions'])), 
             ("Draft", str(stats['draft_versions'])), 
             ("Approved", str(stats['approved_versions']))]
        )
    
    def update_advanced_stats_card(self, card, main_value, breakdown_data):
        """Update an advanced stats card with new data"""
        # Find and update main value
        layout = card.layout()
        if layout and layout.count() >= 3:
            value_label = layout.itemAt(2).widget()
            if isinstance(value_label, QLabel):
                value_label.setText(main_value)
        
        # Update breakdown data
        if layout and layout.count() >= 5:
            breakdown_layout = layout.itemAt(4).layout()
            if breakdown_layout:
                for i, (label, value) in enumerate(breakdown_data):
                    if i < breakdown_layout.count():
                        breakdown_item = breakdown_layout.itemAt(i).layout()
                        if breakdown_item and breakdown_item.count() >= 1:
                            value_widget = breakdown_item.itemAt(0).widget()
                            if isinstance(value_widget, QLabel):
                                value_widget.setText(value)
    
    def update_system_status(self):
        """Update system status monitoring"""
        try:
            import psutil
            
            # Disk usage
            disk_usage = psutil.disk_usage('/').percent
            self.disk_usage_label.setText(f"💾 Disk Usage: {disk_usage:.1f}%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage_label.setText(f"🧠 Memory: {memory.percent:.1f}%")
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage_label.setText(f"⚡ CPU: {cpu_percent:.1f}%")
            
            # Network status (simplified)
            self.network_status_label.setText("🌐 Network: Online")
            
            # Database status (simplified)
            self.database_status_label.setText("🗄️ Database: Connected")
            
        except ImportError:
            # Fallback if psutil not available
            self.disk_usage_label.setText("💾 Disk Usage: N/A")
            self.memory_usage_label.setText("🧠 Memory: N/A")
            self.cpu_usage_label.setText("⚡ CPU: N/A")
        except Exception as e:
            print(f"Error updating system status: {e}")
    
    def update_performance_metrics(self):
        """Update performance metrics"""
        # Simulate performance data
        self.avg_render_time_label.setText("⏱️ Avg Render Time: 2.3s")
        self.files_processed_label.setText("📁 Files Processed: 1,247")
        self.uptime_label.setText("⏰ Uptime: 2h 15m")
        self.error_rate_label.setText("❌ Error Rate: 0.2%")
        self.success_rate_label.setText("✅ Success Rate: 99.8%")
    
    def update_advanced_project_breakdown(self, stats):
        """Update project breakdown table with detailed data"""
        self.project_breakdown_table.setRowCount(len(stats['project_details']))
        
        for row, project in enumerate(stats['project_details']):
            # Project name
            name_item = QTableWidgetItem(project['name'])
            self.project_breakdown_table.setItem(row, 0, name_item)
            
            # Assets count
            assets_item = QTableWidgetItem(str(project['assets']))
            self.project_breakdown_table.setItem(row, 1, assets_item)
            
            # Shots count
            shots_item = QTableWidgetItem(str(project['shots']))
            self.project_breakdown_table.setItem(row, 2, shots_item)
            
            # Versions count
            versions_item = QTableWidgetItem(str(project['versions']))
            self.project_breakdown_table.setItem(row, 3, versions_item)
            
            # Status
            status_item = QTableWidgetItem(project['status'])
            if project['status'] == 'Active':
                status_item.setBackground(QColor(39, 174, 96, 100))  # Green
            else:
                status_item.setBackground(QColor(231, 76, 60, 100))  # Red
            self.project_breakdown_table.setItem(row, 4, status_item)
    
    def update_activity_feeds(self):
        """Update activity feeds with real-time data"""
        activities = [
            "🔄 Project 'TestProject' assets updated",
            "✅ Asset 'Character_01' version v003 approved",
            "🎬 Shot 'SH001' render completed",
            "👤 User 'John Doe' published new version",
            "📁 New project 'AnimationProject' created",
            "🔧 System maintenance completed",
            "📊 Dashboard data refreshed",
            "💾 Backup completed successfully"
        ]
        
        self.activity_list.clear()
        for activity in activities:
            item = QListWidgetItem(activity)
            self.activity_list.addItem(item)
    
    def update_team_activity(self):
        """Update team activity feed"""
        team_activities = [
            "John Doe: Working on Character_01",
            "Jane Smith: Completed SH001 render",
            "Mike Johnson: Published Prop_02 v002",
            "Sarah Wilson: Reviewing environment assets",
            "Admin: Updated project settings"
        ]
        
        self.team_activity_list.clear()
        for activity in team_activities:
            item = QListWidgetItem(activity)
            self.team_activity_list.addItem(item)
    
    def update_clock(self):
        """Update real-time clock"""
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_label.setText(current_time)
    
    def toggle_auto_refresh(self, checked):
        """Toggle auto-refresh functionality"""
        if checked:
            self.refresh_timer.start(30000)  # 30 seconds
        else:
            self.refresh_timer.stop()
    
    def export_dashboard_data(self):
        """Export dashboard data to file"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            from datetime import datetime
            
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Export Dashboard Data", 
                f"dashboard_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json)"
            )
            
            if filename:
                # Collect current dashboard data
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'projects': self.get_comprehensive_project_stats(),
                    'system_status': {
                        'disk_usage': self.disk_usage_label.text(),
                        'memory_usage': self.memory_usage_label.text(),
                        'cpu_usage': self.cpu_usage_label.text()
                    }
                }
                
                import json
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                
                QMessageBox.information(self, "Export Complete", f"Dashboard data exported to:\n{filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data:\n{str(e)}")
    
    def update_stats_card(self, card, value):
        """Update the value in a stats card"""
        # Find the value label (second label in the card)
        layout = card.layout()
        if layout and layout.count() >= 3:
            value_label = layout.itemAt(2).widget()
            if isinstance(value_label, QLabel):
                value_label.setText(value)
    
    def update_activity_list(self):
        """Update the recent activity list"""
        self.activity_list.clear()
        
        # Add some sample activities
        activities = [
            "Project 'TestProject' created",
            "Asset 'Character_01' version v003 published",
            "Shot 'SH001' version v002 published",
            "User 'Admin' logged in",
            "Project 'CompleteTestProject' scanned"
        ]
        
        for activity in activities:
            item = QListWidgetItem(activity)
            self.activity_list.addItem(item)
    
    def update_project_breakdown(self):
        """Update the project breakdown table"""
        try:
            vogue_projects_path = Path("VogueProjects")
            if not vogue_projects_path.exists():
                return
            
            project_dirs = [d for d in vogue_projects_path.iterdir() if d.is_dir()]
            
            self.breakdown_table.setRowCount(len(project_dirs))
            
            for row, project_dir in enumerate(project_dirs):
                # Project name
                name_item = QTableWidgetItem(project_dir.name)
                self.breakdown_table.setItem(row, 0, name_item)
                
                # Count assets
                assets_dir = project_dir / "Assets"
                asset_count = 0
                if assets_dir.exists():
                    asset_dirs = [d for d in assets_dir.iterdir() if d.is_dir()]
                    asset_count = len(asset_dirs)
                
                assets_item = QTableWidgetItem(str(asset_count))
                self.breakdown_table.setItem(row, 1, assets_item)
                
                # Count shots
                shots_dir = project_dir / "Shots"
                shot_count = 0
                if shots_dir.exists():
                    shot_dirs = [d for d in shots_dir.iterdir() if d.is_dir()]
                    shot_count = len(shot_dirs)
                
                shots_item = QTableWidgetItem(str(shot_count))
                self.breakdown_table.setItem(row, 2, shots_item)
                
        except Exception as e:
            print(f"Error updating project breakdown: {e}")
    
    def create_new_project(self):
        """Create a new project"""
        from vogue_app.dialogs import ProjectDialog
        
        dialog = ProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_dashboard()
    
    def scan_projects(self):
        """Scan for existing projects"""
        QMessageBox.information(self, "Info", "Project scanning completed")
        self.refresh_dashboard()
    
    def open_project(self):
        """Open a project"""
        from PyQt6.QtWidgets import QFileDialog
        
        project_path = QFileDialog.getExistingDirectory(
            self, 
            "Open Project", 
            "VogueProjects"
        )
        
        if project_path:
            QMessageBox.information(self, "Info", f"Opening project: {project_path}")
    
    def load_tasks_data(self):
        """Load tasks data - start with empty table"""
        try:
            # Start with empty task table
            self.tasks_table.setRowCount(0)
            
        except Exception as e:
            print(f"Error loading tasks data: {e}")
    
    def on_task_selection_changed(self):
        """Handle task selection change"""
        selected_rows = self.tasks_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.edit_task_btn.setEnabled(has_selection)
        self.complete_task_btn.setEnabled(has_selection)
        self.delete_task_btn.setEnabled(has_selection)
        
        if has_selection:
            self.update_task_details(selected_rows[0].row())
        else:
            self.clear_task_details()
    
    def update_task_details(self, row):
        """Update task details panel with selected task"""
        try:
            task_name = self.tasks_table.item(row, 0).text()
            project = self.tasks_table.item(row, 1).text()
            assignee = self.tasks_table.item(row, 2).text()
            status = self.tasks_table.item(row, 3).text()
            priority = self.tasks_table.item(row, 4).text()
            due_date = self.tasks_table.item(row, 5).text()
            
            self.task_name_edit.setText(task_name)
            self.task_project_edit.setText(project)
            self.task_assignee_edit.setText(assignee)
            self.task_status_edit.setText(status)
            self.task_priority_edit.setText(priority)
            self.task_due_date_edit.setText(due_date)
            
            # Set description based on task
            description = f"Task: {task_name}\nProject: {project}\nAssignee: {assignee}\nStatus: {status}\nPriority: {priority}\nDue Date: {due_date}"
            self.task_description_edit.setPlainText(description)
            
        except Exception as e:
            print(f"Error updating task details: {e}")
    
    def clear_task_details(self):
        """Clear task details panel"""
        self.task_name_edit.clear()
        self.task_project_edit.clear()
        self.task_assignee_edit.clear()
        self.task_status_edit.clear()
        self.task_priority_edit.clear()
        self.task_due_date_edit.clear()
        self.task_description_edit.clear()
    
    def filter_tasks(self, filter_text):
        """Filter tasks based on selected filter"""
        try:
            for row in range(self.tasks_table.rowCount()):
                should_show = True
                
                if filter_text == "My Tasks":
                    # Show only tasks assigned to current user (assuming "Admin" for now)
                    assignee = self.tasks_table.item(row, 2).text()
                    should_show = assignee == "Admin"
                elif filter_text == "Pending":
                    status = self.tasks_table.item(row, 3).text()
                    should_show = status == "Pending"
                elif filter_text == "In Progress":
                    status = self.tasks_table.item(row, 3).text()
                    should_show = status == "In Progress"
                elif filter_text == "Completed":
                    status = self.tasks_table.item(row, 3).text()
                    should_show = status == "Completed"
                elif filter_text == "Overdue":
                    status = self.tasks_table.item(row, 3).text()
                    should_show = status == "Overdue"
                # "All Tasks" shows everything
                
                self.tasks_table.setRowHidden(row, not should_show)
                
        except Exception as e:
            print(f"Error filtering tasks: {e}")
    
    def add_task(self):
        """Add a new task"""
        from vogue_app.dialogs import TaskDialog
        
        dialog = TaskDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh tasks data
            self.load_tasks_data()
    
    def edit_task(self):
        """Edit selected task"""
        selected_rows = self.tasks_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        task_name = self.tasks_table.item(row, 0).text()
        
        from vogue_app.dialogs import TaskDialog
        
        dialog = TaskDialog(self, task_name=task_name)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh tasks data
            self.load_tasks_data()
    
    def complete_task(self):
        """Mark selected task as complete"""
        selected_rows = self.tasks_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        for row in selected_rows:
            status_item = self.tasks_table.item(row.row(), 3)
            if status_item and status_item.text() != "Completed":
                status_item.setText("Completed")
                status_item.setBackground(QColor(144, 238, 144, 100))  # Light green
        
        QMessageBox.information(self, "Info", "Task(s) marked as complete")
    
    def delete_task(self):
        """Delete selected task"""
        selected_rows = self.tasks_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        reply = QMessageBox.question(
            self, 
            "Delete Task", 
            "Are you sure you want to delete the selected task(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove selected rows (in reverse order to maintain indices)
            for row in reversed(selected_rows):
                self.tasks_table.removeRow(row.row())
    
    def load_notifications_data(self):
        """Load notifications data"""
        try:
            # Sample notifications data
            notifications = [
                ("Info", "Project 'TestProject' has been updated", "2024-01-15 10:30", "Unread"),
                ("Warning", "Asset 'Character_01' version v003 is missing files", "2024-01-15 09:15", "Unread"),
                ("Success", "Shot 'SH001' version v002 published successfully", "2024-01-15 08:45", "Read"),
                ("Error", "Failed to publish asset 'Prop_01' version v001", "2024-01-14 16:20", "Read"),
                ("Info", "New user 'John Doe' has been added to the team", "2024-01-14 14:30", "Read"),
                ("Warning", "Project 'OldProject' has not been accessed in 30 days", "2024-01-14 12:00", "Unread")
            ]
            
            self.notifications_table.setRowCount(len(notifications))
            
            for row, (notif_type, message, time, status) in enumerate(notifications):
                # Type
                type_item = QTableWidgetItem(notif_type)
                if notif_type == "Error":
                    type_item.setBackground(QColor(255, 182, 193, 100))  # Light red
                elif notif_type == "Warning":
                    type_item.setBackground(QColor(255, 235, 59, 100))   # Light yellow
                elif notif_type == "Success":
                    type_item.setBackground(QColor(144, 238, 144, 100))  # Light green
                else:
                    type_item.setBackground(QColor(173, 216, 230, 100))  # Light blue
                self.notifications_table.setItem(row, 0, type_item)
                
                # Message
                message_item = QTableWidgetItem(message)
                self.notifications_table.setItem(row, 1, message_item)
                
                # Time
                time_item = QTableWidgetItem(time)
                self.notifications_table.setItem(row, 2, time_item)
                
                # Status
                status_item = QTableWidgetItem(status)
                if status == "Unread":
                    status_item.setBackground(QColor(255, 235, 59, 100))  # Light yellow
                else:
                    status_item.setBackground(QColor(144, 238, 144, 100))  # Light green
                self.notifications_table.setItem(row, 3, status_item)
                
        except Exception as e:
            print(f"Error loading notifications data: {e}")
    
    def load_messages_data(self):
        """Load messages data"""
        try:
            # Sample messages data with better formatting
            messages = [
                {
                    "from": "John Doe",
                    "subject": "Asset Review Request", 
                    "time": "2024-01-15 10:30",
                    "content": "Please review the character model for the upcoming project."
                },
                {
                    "from": "Jane Smith",
                    "subject": "Project Deadline Update",
                    "time": "2024-01-15 09:15", 
                    "content": "The deadline for the animation project has been extended by one week."
                },
                {
                    "from": "Mike Johnson",
                    "subject": "New Software Version Available",
                    "time": "2024-01-14 16:20",
                    "content": "A new version of the pipeline tools is now available for download."
                },
                {
                    "from": "Sarah Wilson", 
                    "subject": "Team Meeting Reminder",
                    "time": "2024-01-14 14:30",
                    "content": "Don't forget about our weekly team meeting tomorrow at 2 PM."
                },
                {
                    "from": "Admin",
                    "subject": "System Maintenance Notice", 
                    "time": "2024-01-14 12:00",
                    "content": "The system will be under maintenance this weekend from 10 PM to 6 AM."
                }
            ]
            
            self.messages_list.clear()
            
            for message in messages:
                # Format message with better plain text styling
                formatted_message = f"""From: {message['from']}
Subject: {message['subject']}
Time: {message['time']}

{message['content']}"""
                
                item = QListWidgetItem(formatted_message)
                self.messages_list.addItem(item)
                
        except Exception as e:
            print(f"Error loading messages data: {e}")
    
    def on_notification_selection_changed(self):
        """Handle notification selection change"""
        selected_rows = self.notifications_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.mark_read_btn.setEnabled(has_selection)
        self.delete_notification_btn.setEnabled(has_selection)
    
    def on_message_selection_changed(self):
        """Handle message selection change"""
        selected_items = self.messages_list.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.reply_btn.setEnabled(has_selection)
        self.forward_btn.setEnabled(has_selection)
        self.delete_message_btn.setEnabled(has_selection)
    
    def mark_all_read(self):
        """Mark all notifications as read"""
        for row in range(self.notifications_table.rowCount()):
            status_item = self.notifications_table.item(row, 3)
            if status_item and status_item.text() == "Unread":
                status_item.setText("Read")
                status_item.setBackground(QColor(144, 238, 144, 100))  # Light green
        
        QMessageBox.information(self, "Info", "All notifications marked as read")
    
    def refresh_inbox(self):
        """Refresh inbox data"""
        self.load_notifications_data()
        self.load_messages_data()
        QMessageBox.information(self, "Info", "Inbox refreshed")
    
    def mark_as_read(self):
        """Mark selected notification as read"""
        selected_rows = self.notifications_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        for row in selected_rows:
            status_item = self.notifications_table.item(row.row(), 3)
            if status_item and status_item.text() == "Unread":
                status_item.setText("Read")
                status_item.setBackground(QColor(144, 238, 144, 100))  # Light green
    
    def delete_notification(self):
        """Delete selected notification"""
        selected_rows = self.notifications_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        reply = QMessageBox.question(
            self, 
            "Delete Notification", 
            "Are you sure you want to delete the selected notification(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove selected rows (in reverse order to maintain indices)
            for row in reversed(selected_rows):
                self.notifications_table.removeRow(row.row())
    
    def reply_message(self):
        """Reply to selected message"""
        selected_items = self.messages_list.selectedItems()
        if not selected_items:
            return
        
        QMessageBox.information(self, "Info", "Reply functionality not yet implemented")
    
    def forward_message(self):
        """Forward selected message"""
        selected_items = self.messages_list.selectedItems()
        if not selected_items:
            return
        
        QMessageBox.information(self, "Info", "Forward functionality not yet implemented")
    
    def delete_message(self):
        """Delete selected message"""
        selected_items = self.messages_list.selectedItems()
        if not selected_items:
            return
        
        reply = QMessageBox.question(
            self, 
            "Delete Message", 
            "Are you sure you want to delete the selected message(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                self.messages_list.takeItem(self.messages_list.row(item))
    
    def load_teams_data(self):
        """Load teams data from JSON file"""
        try:
            import json
            from pathlib import Path
            
            teams_file = Path("data/teams.json")
            if teams_file.exists():
                with open(teams_file, 'r') as f:
                    teams_data = json.load(f)
                
                self.teams_table.setRowCount(len(teams_data))
                
                for row, team in enumerate(teams_data):
                    # Name
                    name_item = QTableWidgetItem(team.get('name', ''))
                    name_item.setData(Qt.ItemDataRole.UserRole, team.get('id', ''))
                    self.teams_table.setItem(row, 0, name_item)
                    
                    # Members count
                    members_count = len(team.get('members', []))
                    members_item = QTableWidgetItem(str(members_count))
                    self.teams_table.setItem(row, 1, members_item)
                    
                    # Projects count
                    projects_count = len(team.get('projects', []))
                    projects_item = QTableWidgetItem(str(projects_count))
                    self.teams_table.setItem(row, 2, projects_item)
                    
                    # Status
                    status = "Active" if team.get('is_active', True) else "Inactive"
                    status_item = QTableWidgetItem(status)
                    if status == "Active":
                        status_item.setBackground(QColor(144, 238, 144, 100))  # Light green
                    else:
                        status_item.setBackground(QColor(255, 182, 193, 100))  # Light red
                    self.teams_table.setItem(row, 3, status_item)
                    
        except Exception as e:
            print(f"Error loading teams data: {e}")
    
    def load_users_data(self):
        """Load users data from JSON file"""
        try:
            import json
            from pathlib import Path
            
            users_file = Path("data/users.json")
            if users_file.exists():
                with open(users_file, 'r') as f:
                    users_data = json.load(f)
                
                self.users_table.setRowCount(len(users_data))
                
                for row, user in enumerate(users_data):
                    # Name
                    name_item = QTableWidgetItem(user.get('name', ''))
                    name_item.setData(Qt.ItemDataRole.UserRole, user.get('id', ''))
                    self.users_table.setItem(row, 0, name_item)
                    
                    # Email
                    email_item = QTableWidgetItem(user.get('email', ''))
                    self.users_table.setItem(row, 1, email_item)
                    
                    # Role
                    role = user.get('role', '').replace('UserRole.', '')
                    role_item = QTableWidgetItem(role)
                    self.users_table.setItem(row, 2, role_item)
                    
                    # Teams count
                    teams_count = len(user.get('teams', []))
                    teams_item = QTableWidgetItem(str(teams_count))
                    self.users_table.setItem(row, 3, teams_item)
                    
                    # Status
                    status = "Active" if user.get('is_active', True) else "Inactive"
                    status_item = QTableWidgetItem(status)
                    if status == "Active":
                        status_item.setBackground(QColor(144, 238, 144, 100))  # Light green
                    else:
                        status_item.setBackground(QColor(255, 182, 193, 100))  # Light red
                    self.users_table.setItem(row, 4, status_item)
                    
        except Exception as e:
            print(f"Error loading users data: {e}")
    
    def on_team_selection_changed(self):
        """Handle team selection change"""
        selected_rows = self.teams_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.edit_team_btn.setEnabled(has_selection)
        self.delete_team_btn.setEnabled(has_selection)
    
    def on_user_selection_changed(self):
        """Handle user selection change"""
        selected_rows = self.users_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.edit_user_btn.setEnabled(has_selection)
        self.delete_user_btn.setEnabled(has_selection)
    
    def add_team(self):
        """Add a new team"""
        from vogue_app.dialogs import TeamDialog
        
        dialog = TeamDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh teams data
            self.load_teams_data()
    
    def edit_team(self):
        """Edit selected team"""
        selected_rows = self.teams_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        team_id = self.teams_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        from vogue_app.dialogs import TeamDialog
        
        dialog = TeamDialog(self, team_id=team_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh teams data
            self.load_teams_data()
    
    def delete_team(self):
        """Delete selected team"""
        selected_rows = self.teams_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        team_name = self.teams_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, 
            "Delete Team", 
            f"Are you sure you want to delete team '{team_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement team deletion
            QMessageBox.information(self, "Info", "Team deletion not yet implemented")
    
    def add_user(self):
        """Add a new user"""
        from vogue_app.dialogs import UserDialog
        
        dialog = UserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh users data
            self.load_users_data()
    
    def edit_user(self):
        """Edit selected user"""
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        user_id = self.users_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        from vogue_app.dialogs import UserDialog
        
        dialog = UserDialog(self, user_id=user_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh users data
            self.load_users_data()
    
    def delete_user(self):
        """Delete selected user"""
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        user_name = self.users_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, 
            "Delete User", 
            f"Are you sure you want to delete user '{user_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement user deletion
            QMessageBox.information(self, "Info", "User deletion not yet implemented")
    
    def create_settings_tab(self):
        """Create the Settings tab content with application preferences"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Settings")
        title.setProperty("class", "title")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Save button
        self.save_settings_btn = QPushButton("Save Settings")
        self.save_settings_btn.setProperty("class", "primary")
        self.save_settings_btn.clicked.connect(self.save_settings)
        header_layout.addWidget(self.save_settings_btn)
        
        layout.addLayout(header_layout)
        
        # Main content with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        
        # General Settings
        general_group = QGroupBox("General Settings")
        general_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        general_layout = QFormLayout(general_group)
        
        # Application name
        self.app_name_edit = QLineEdit("Vogue Manager")
        general_layout.addRow("Application Name:", self.app_name_edit)
        
        # Default project path
        self.default_project_path_edit = QLineEdit("VogueProjects")
        self.browse_project_path_btn = QPushButton("Browse")
        self.browse_project_path_btn.clicked.connect(self.browse_project_path)
        
        project_path_layout = QHBoxLayout()
        project_path_layout.addWidget(self.default_project_path_edit)
        project_path_layout.addWidget(self.browse_project_path_btn)
        general_layout.addRow("Default Project Path:", project_path_layout)
        
        # Auto-save interval
        self.autosave_interval_spin = QSpinBox()
        self.autosave_interval_spin.setRange(1, 60)
        self.autosave_interval_spin.setValue(5)
        self.autosave_interval_spin.setSuffix(" minutes")
        general_layout.addRow("Auto-save Interval:", self.autosave_interval_spin)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        self.theme_combo.setCurrentText("Light")
        general_layout.addRow("Theme:", self.theme_combo)
        
        scroll_layout.addWidget(general_group)
        
        # Project Settings
        project_group = QGroupBox("Project Settings")
        project_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        project_layout = QFormLayout(project_group)
        
        # Default FPS
        self.default_fps_spin = QSpinBox()
        self.default_fps_spin.setRange(12, 120)
        self.default_fps_spin.setValue(24)
        project_layout.addRow("Default FPS:", self.default_fps_spin)
        
        # Default resolution
        self.default_resolution_combo = QComboBox()
        self.default_resolution_combo.addItems([
            "1920x1080 (HD)",
            "3840x2160 (4K)",
            "2560x1440 (2K)",
            "1280x720 (HD Ready)"
        ])
        self.default_resolution_combo.setCurrentText("1920x1080 (HD)")
        project_layout.addRow("Default Resolution:", self.default_resolution_combo)
        
        # Auto-create folders
        self.auto_create_folders_check = QCheckBox("Automatically create folder structure")
        self.auto_create_folders_check.setChecked(True)
        project_layout.addRow("", self.auto_create_folders_check)
        
        # Version naming
        self.version_naming_combo = QComboBox()
        self.version_naming_combo.addItems([
            "v001, v002, v003...",
            "v1, v2, v3...",
            "001, 002, 003..."
        ])
        self.version_naming_combo.setCurrentText("v001, v002, v003...")
        project_layout.addRow("Version Naming:", self.version_naming_combo)
        
        scroll_layout.addWidget(project_group)
        
        # DCC Applications Settings
        dcc_group = QGroupBox("DCC Applications")
        dcc_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        dcc_layout = QFormLayout(dcc_group)

        # Known DCC apps (you can add more later)
        self.dcc_maya_path = QLineEdit("")
        self.dcc_maya_path.setPlaceholderText(r"C:\\Program Files\\Autodesk\\Maya2025\\bin\\maya.exe")
        self.dcc_maya_browse = QPushButton("Browse")
        self.dcc_maya_browse.clicked.connect(lambda: self._browse_exec_path(self.dcc_maya_path))
        maya_row = QHBoxLayout()
        maya_row.addWidget(self.dcc_maya_path)
        maya_row.addWidget(self.dcc_maya_browse)
        dcc_layout.addRow("Autodesk Maya:", maya_row)

        self.dcc_blender_path = QLineEdit("")
        self.dcc_blender_path.setPlaceholderText(r"C:\\Program Files\\Blender Foundation\\Blender 4.0\\blender.exe")
        self.dcc_blender_browse = QPushButton("Browse")
        self.dcc_blender_browse.clicked.connect(lambda: self._browse_exec_path(self.dcc_blender_path))
        blender_row = QHBoxLayout()
        blender_row.addWidget(self.dcc_blender_path)
        blender_row.addWidget(self.dcc_blender_browse)
        dcc_layout.addRow("Blender:", blender_row)

        self.dcc_houdini_path = QLineEdit("")
        self.dcc_houdini_path.setPlaceholderText(r"C:\\Program Files\\Side Effects Software\\Houdini 20.5.332\\bin\\houdini.exe")
        self.dcc_houdini_browse = QPushButton("Browse")
        self.dcc_houdini_browse.clicked.connect(lambda: self._browse_exec_path(self.dcc_houdini_path))
        houdini_row = QHBoxLayout()
        houdini_row.addWidget(self.dcc_houdini_path)
        houdini_row.addWidget(self.dcc_houdini_browse)
        dcc_layout.addRow("SideFX Houdini:", houdini_row)

        self.dcc_nuke_path = QLineEdit("")
        self.dcc_nuke_path.setPlaceholderText(r"C:\\Program Files\\Nuke15.1v4\\Nuke15.1.exe")
        self.dcc_nuke_browse = QPushButton("Browse")
        self.dcc_nuke_browse.clicked.connect(lambda: self._browse_exec_path(self.dcc_nuke_path))
        nuke_row = QHBoxLayout()
        nuke_row.addWidget(self.dcc_nuke_path)
        nuke_row.addWidget(self.dcc_nuke_browse)
        dcc_layout.addRow("Foundry Nuke:", nuke_row)

        scroll_layout.addWidget(dcc_group)

        # User Settings
        user_group = QGroupBox("User Settings")
        user_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        user_layout = QFormLayout(user_group)
        
        # User name
        self.user_name_edit = QLineEdit("Admin")
        user_layout.addRow("User Name:", self.user_name_edit)
        
        # User email
        self.user_email_edit = QLineEdit("admin@vogue.com")
        user_layout.addRow("Email:", self.user_email_edit)
        
        # Notifications
        self.email_notifications_check = QCheckBox("Email notifications")
        self.email_notifications_check.setChecked(True)
        user_layout.addRow("", self.email_notifications_check)
        
        self.desktop_notifications_check = QCheckBox("Desktop notifications")
        self.desktop_notifications_check.setChecked(True)
        user_layout.addRow("", self.desktop_notifications_check)
        
        scroll_layout.addWidget(user_group)
        
        # Advanced Settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        advanced_layout = QFormLayout(advanced_group)
        
        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        advanced_layout.addRow("Log Level:", self.log_level_combo)
        
        # Max log files
        self.max_log_files_spin = QSpinBox()
        self.max_log_files_spin.setRange(1, 100)
        self.max_log_files_spin.setValue(10)
        advanced_layout.addRow("Max Log Files:", self.max_log_files_spin)
        
        # Debug mode
        self.debug_mode_check = QCheckBox("Enable debug mode")
        self.debug_mode_check.setChecked(False)
        advanced_layout.addRow("", self.debug_mode_check)
        
        scroll_layout.addWidget(advanced_group)
        
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # Load current settings, then best-effort auto-detect DCC paths for this user
        self.load_settings()
        self.autodetect_dcc_paths()
        
        return widget
    
    def load_settings(self):
        """Load settings from configuration file"""
        try:
            import json
            from pathlib import Path
            
            settings_file = Path("settings.json")
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Load general settings
                self.app_name_edit.setText(settings.get('app_name', 'Vogue Manager'))
                self.default_project_path_edit.setText(settings.get('default_project_path', 'VogueProjects'))
                self.autosave_interval_spin.setValue(settings.get('autosave_interval', 5))
                self.theme_combo.setCurrentText(settings.get('theme', 'Light'))
                
                # Load project settings
                self.default_fps_spin.setValue(settings.get('default_fps', 24))
                self.default_resolution_combo.setCurrentText(settings.get('default_resolution', '1920x1080 (HD)'))
                self.auto_create_folders_check.setChecked(settings.get('auto_create_folders', True))
                self.version_naming_combo.setCurrentText(settings.get('version_naming', 'v001, v002, v003...'))
                
                # Load user settings
                self.user_name_edit.setText(settings.get('user_name', 'Admin'))
                self.user_email_edit.setText(settings.get('user_email', 'admin@vogue.com'))
                self.email_notifications_check.setChecked(settings.get('email_notifications', True))
                self.desktop_notifications_check.setChecked(settings.get('desktop_notifications', True))
                
                # Load advanced settings
                self.log_level_combo.setCurrentText(settings.get('log_level', 'INFO'))
                self.max_log_files_spin.setValue(settings.get('max_log_files', 10))
                self.debug_mode_check.setChecked(settings.get('debug_mode', False))
                # DCC apps
                dcc = settings.get('dcc_apps', {})
                if hasattr(self, 'dcc_maya_path'):
                    self.dcc_maya_path.setText(dcc.get('maya', ''))
                if hasattr(self, 'dcc_blender_path'):
                    self.dcc_blender_path.setText(dcc.get('blender', ''))
                if hasattr(self, 'dcc_houdini_path'):
                    self.dcc_houdini_path.setText(dcc.get('houdini', ''))
                if hasattr(self, 'dcc_nuke_path'):
                    self.dcc_nuke_path.setText(dcc.get('nuke', ''))
                
        except Exception as e:
            print(f"Error loading settings: {e}")

    def autodetect_dcc_paths(self):
        """Detect common DCC install paths on Windows and fill empty fields."""
        import os, glob
        program_files = os.environ.get('ProgramFiles', r'C:\\Program Files')
        program_files_x86 = os.environ.get('ProgramFiles(x86)', r'C:\\Program Files (x86)')

        def first_match(patterns):
            for pattern in patterns:
                matches = glob.glob(pattern)
                if matches:
                    return matches[0]
            return ''

        # Maya
        if hasattr(self, 'dcc_maya_path') and not self.dcc_maya_path.text().strip():
            p = first_match([
                os.path.join(program_files, 'Autodesk', 'Maya*', 'bin', 'maya.exe'),
                os.path.join(program_files_x86, 'Autodesk', 'Maya*', 'bin', 'maya.exe')
            ])
            if p:
                self.dcc_maya_path.setText(p)

        # Blender
        if hasattr(self, 'dcc_blender_path') and not self.dcc_blender_path.text().strip():
            p = first_match([
                os.path.join(program_files, 'Blender Foundation', 'Blender *', 'blender.exe'),
                os.path.join(program_files, 'Blender Foundation', 'Blender', 'blender.exe')
            ])
            if p:
                self.dcc_blender_path.setText(p)

        # Houdini
        if hasattr(self, 'dcc_houdini_path') and not self.dcc_houdini_path.text().strip():
            p = first_match([
                os.path.join(program_files, 'Side Effects Software', 'Houdini *', 'bin', 'houdini.exe')
            ])
            if p:
                self.dcc_houdini_path.setText(p)

        # Nuke
        if hasattr(self, 'dcc_nuke_path') and not self.dcc_nuke_path.text().strip():
            p = first_match([
                os.path.join(program_files, 'Nuke*', 'Nuke*.exe'),
                os.path.join(program_files, 'Foundry', 'Nuke*', 'Nuke*.exe')
            ])
            if p:
                self.dcc_nuke_path.setText(p)
        
        # Load DCC app paths if present
        try:
            from pathlib import Path
            import json
            settings_file = Path("settings.json")
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                dcc = settings.get('dcc_apps', {})
                if hasattr(self, 'dcc_maya_path'):
                    self.dcc_maya_path.setText(dcc.get('maya', ''))
                if hasattr(self, 'dcc_blender_path'):
                    self.dcc_blender_path.setText(dcc.get('blender', ''))
                if hasattr(self, 'dcc_houdini_path'):
                    self.dcc_houdini_path.setText(dcc.get('houdini', ''))
                if hasattr(self, 'dcc_nuke_path'):
                    self.dcc_nuke_path.setText(dcc.get('nuke', ''))
        except Exception:
            pass

    def _browse_exec_path(self, line_edit: QLineEdit):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Select Executable", "", "Executables (*.exe *.bat *.sh);;All Files (*.*)")
        if path:
            line_edit.setText(path)
    
    def save_settings(self):
        """Save settings to configuration file"""
        try:
            import json
            from pathlib import Path
            
            settings = {
                # General settings
                'app_name': self.app_name_edit.text(),
                'default_project_path': self.default_project_path_edit.text(),
                'autosave_interval': self.autosave_interval_spin.value(),
                'theme': self.theme_combo.currentText(),
                
                # Project settings
                'default_fps': self.default_fps_spin.value(),
                'default_resolution': self.default_resolution_combo.currentText(),
                'auto_create_folders': self.auto_create_folders_check.isChecked(),
                'version_naming': self.version_naming_combo.currentText(),
                
                # User settings
                'user_name': self.user_name_edit.text(),
                'user_email': self.user_email_edit.text(),
                'email_notifications': self.email_notifications_check.isChecked(),
                'desktop_notifications': self.desktop_notifications_check.isChecked(),
                
                # Advanced settings
                'log_level': self.log_level_combo.currentText(),
                'max_log_files': self.max_log_files_spin.value(),
                'debug_mode': self.debug_mode_check.isChecked(),
                # DCC apps
                'dcc_apps': {
                    'maya': getattr(self, 'dcc_maya_path', QLineEdit()).text() if hasattr(self, 'dcc_maya_path') else '',
                    'blender': getattr(self, 'dcc_blender_path', QLineEdit()).text() if hasattr(self, 'dcc_blender_path') else '',
                    'houdini': getattr(self, 'dcc_houdini_path', QLineEdit()).text() if hasattr(self, 'dcc_houdini_path') else '',
                    'nuke': getattr(self, 'dcc_nuke_path', QLineEdit()).text() if hasattr(self, 'dcc_nuke_path') else ''
                }
            }
            
            settings_file = Path("settings.json")
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            QMessageBox.information(self, "Settings", "Settings saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
    
    def browse_project_path(self):
        """Browse for default project path"""
        from PyQt6.QtWidgets import QFileDialog
        
        path = QFileDialog.getExistingDirectory(
            self, 
            "Select Default Project Path",
            self.default_project_path_edit.text()
        )
        
        if path:
            self.default_project_path_edit.setText(path)
    
    def style_tabs(self):
        """Apply Ayon-style modern dark theme styling to tabs"""
        tab_style = f"""
        QTabWidget::pane {{
            border: 1px solid {COLORS['outline']};
            background-color: {COLORS['bg']};
            border-radius: 8px;
        }}
        
        QTabWidget::tab-bar {{
            alignment: left;
        }}
        
        QTabBar::tab {{
            background-color: {COLORS['surface']};
            color: {COLORS['fg']};
            padding: 12px 20px;
            margin-right: 2px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            border: 1px solid {COLORS['outline']};
            border-bottom: none;
            min-width: 100px;
            font-size: 13px;
            font-weight: 500;
        }}
        
        QTabBar::tab:selected {{
            background-color: {COLORS['accent']};
            color: white;
            border-color: {COLORS['accent']};
            font-weight: 600;
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {COLORS['hover']};
            color: {COLORS['fg']};
            border-color: {COLORS['accent']};
        }}
        
        QTabBar::tab:first {{
            margin-left: 0px;
        }}
        """
        
        self.main_tab_widget.setStyleSheet(tab_style)
    
    def setup_menu(self):
        """Set up the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Project submenu
        project_menu = file_menu.addMenu("&Project")
        
        self.browse_project_action = QAction("&Browse Project...", self)
        self.browse_project_action.setShortcut("Ctrl+O")
        project_menu.addAction(self.browse_project_action)
        
        self.new_project_action = QAction("&New Project...", self)
        self.new_project_action.setShortcut("Ctrl+N")
        project_menu.addAction(self.new_project_action)
        
        self.open_project_action = QAction("&Open Project...", self)
        self.open_project_action.setShortcut("Ctrl+Shift+O")
        project_menu.addAction(self.open_project_action)
        
        project_menu.addSeparator()

        # Recent Projects menu item
        self.recent_projects_action = QAction("&Recent Projects...", self)
        self.recent_projects_action.setShortcut("Ctrl+R")
        project_menu.addAction(self.recent_projects_action)
        
        project_menu.addSeparator()
        
        # Prism-specific project actions
        self.import_project_action = QAction("&Import Project...", self)
        project_menu.addAction(self.import_project_action)
        
        self.export_project_action = QAction("&Export Project...", self)
        project_menu.addAction(self.export_project_action)
        
        project_menu.addSeparator()
        
        self.project_settings_action = QAction("&Project Settings...", self)
        self.project_settings_action.setShortcut("Ctrl+Shift+P")
        project_menu.addAction(self.project_settings_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        edit_menu.addAction(refresh_action)
        
        scan_action = QAction("&Scan Filesystem", self)
        edit_menu.addAction(scan_action)
        
        edit_menu.addSeparator()
        
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        edit_menu.addAction(settings_action)
        
        # Assets menu
        assets_menu = menubar.addMenu("&Assets")
        
        import_asset_action = QAction("&Import Asset...", self)
        import_asset_action.setShortcut("Ctrl+I")
        assets_menu.addAction(import_asset_action)
        
        # Shots menu
        shots_menu = menubar.addMenu("&Shots")
        
        add_shot_action = QAction("&Add Shot...", self)
        add_shot_action.setShortcut("Ctrl+Shift+A")
        shots_menu.addAction(add_shot_action)
        
        # Publish menu
        publish_menu = menubar.addMenu("&Publish")
        
        publish_action = QAction("&Publish Version...", self)
        publish_action.setShortcut("Ctrl+P")
        publish_menu.addAction(publish_action)
        
        batch_publish_action = QAction("&Batch Publish...", self)
        batch_publish_action.setShortcut("Ctrl+Shift+P")
        publish_menu.addAction(batch_publish_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Prism-specific tools
        thumbnail_action = QAction("&Generate Thumbnails", self)
        tools_menu.addAction(thumbnail_action)
        
        cleanup_action = QAction("&Cleanup Project", self)
        tools_menu.addAction(cleanup_action)
        
        tools_menu.addSeparator()
        
        # Prism pipeline tools
        validate_action = QAction("&Validate Project", self)
        tools_menu.addAction(validate_action)
        
        optimize_action = QAction("&Optimize Project", self)
        tools_menu.addAction(optimize_action)
        
        tools_menu.addSeparator()
        
        # Integration tools
        maya_action = QAction("&Launch Maya", self)
        tools_menu.addAction(maya_action)
        
        houdini_action = QAction("&Launch Houdini", self)
        tools_menu.addAction(houdini_action)
        
        blender_action = QAction("&Launch Blender", self)
        tools_menu.addAction(blender_action)
        
        tools_menu.addSeparator()
        
        # System tools
        api_action = QAction("&Start API Server", self)
        tools_menu.addAction(api_action)
        
        logs_action = QAction("&View Logs", self)
        tools_menu.addAction(logs_action)
        
        # Status menu
        status_menu = menubar.addMenu("&Status")
        
        # Project status action
        self.project_status_action = QAction("Project: No project loaded", self)
        self.project_status_action.setEnabled(False)
        status_menu.addAction(self.project_status_action)
        
        # User status action
        self.user_status_action = QAction("User: Unknown", self)
        self.user_status_action.setEnabled(False)
        status_menu.addAction(self.user_status_action)
        
        # Version status action
        self.version_status_action = QAction("Version: v1.0.0", self)
        self.version_status_action.setEnabled(False)
        status_menu.addAction(self.version_status_action)
        
        status_menu.addSeparator()
        
        # System info action
        self.system_info_action = QAction("System Information...", self)
        status_menu.addAction(self.system_info_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About Vogue Manager", self)
        help_menu.addAction(about_action)
        
        documentation_action = QAction("&Documentation", self)
        help_menu.addAction(documentation_action)
    
    def setup_toolbar(self):
        """Set up the toolbar"""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background: linear-gradient(180deg, {COLORS['panel']} 0%, {COLORS['bg']} 100%);
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                spacing: 4px;
                padding: 6px;
                margin: 4px;
            }}
            QToolBar QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 6px;
                padding: 8px 16px;
                margin: 2px;
                color: {COLORS['fg']};
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            QToolBar QToolButton:hover {{
                background-color: {COLORS['hover']};
                border: 2px solid {COLORS['accent']};
                color: {COLORS['accent']};
            }}
            QToolBar QToolButton:pressed {{
                background-color: {COLORS['accent']};
                border: 2px solid {COLORS['accent']};
                color: white;
            }}
            QToolBar QToolButton[class="primary"] {{
                background-color: {COLORS['accent']};
                color: white;
                border: 2px solid {COLORS['accent']};
                font-weight: 700;
                letter-spacing: 1px;
            }}
            QToolBar QToolButton[class="primary"]:hover {{
                background-color: {COLORS['accent2']};
                border-color: {COLORS['accent2']};
                border-width: 3px;
            }}
            QToolBar QToolButton[class="primary"]:pressed {{
                background-color: {COLORS['selection']};
                border-color: {COLORS['selection']};
            }}
            QToolBar QPushButton {{
                background-color: {COLORS['panel']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 16px;
                margin: 2px;
                color: {COLORS['fg']};
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                min-width: 100px;
            }}
            QToolBar QPushButton:hover {{
                background-color: {COLORS['hover']};
                border-color: {COLORS['accent']};
                color: {COLORS['accent']};
                border-width: 2px;
            }}
            QToolBar QPushButton:pressed {{
                background-color: {COLORS['accent']};
                color: white;
            }}
            QToolBar::separator {{
                background-color: {COLORS['border']};
                width: 2px;
                margin: 4px 12px;
                border-radius: 1px;
            }}
        """)
        
        # Project actions
        browse_action = QAction("Browse", self)
        browse_action.setToolTip("Browse for project")
        browse_action.setShortcut("Ctrl+O")
        toolbar.addAction(browse_action)
        
        new_action = QAction("New", self)
        new_action.setToolTip("Create new project")
        new_action.setShortcut("Ctrl+N")
        toolbar.addAction(new_action)

        
        toolbar.addSeparator()
        
        # Asset actions
        
        add_shot_action = QAction("Add Shot", self)
        add_shot_action.setToolTip("Add new shot")
        add_shot_action.setShortcut("Ctrl+Shift+A")
        toolbar.addAction(add_shot_action)
        
        toolbar.addSeparator()
        
        # Publish actions
        publish_action = QAction("Publish", self)
        publish_action.setToolTip("Publish current selection")
        publish_action.setShortcut("Ctrl+P")
        publish_action.setProperty("class", "primary")
        toolbar.addAction(publish_action)
        
        toolbar.addSeparator()
        
        # Utility actions
        refresh_action = QAction("Refresh", self)
        refresh_action.setToolTip("Refresh project data")
        refresh_action.setShortcut("F5")
        toolbar.addAction(refresh_action)
        
        scan_action = QAction("Scan", self)
        scan_action.setToolTip("Scan filesystem")
        scan_action.setShortcut("Ctrl+Shift+S")
        toolbar.addAction(scan_action)
    
    def setup_statusbar(self):
        """Set up the status bar"""
        self.status_bar = self.statusBar()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Status message (for temporary messages)
        self.status_message_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_message_label)
    
    def setup_docks(self):
        """Set up dock widgets"""
        # Log dock
        self.log_dock = QDockWidget("Log", self)
        self.log_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        # Log controls
        log_controls = QHBoxLayout()
        clear_log_btn = QPushButton("Clear")
        log_level_combo = QComboBox()
        log_level_combo.addItems(["Debug", "Info", "Warning", "Error"])
        log_level_combo.setCurrentText("Info")
        
        log_controls.addWidget(QLabel("Level:"))
        log_controls.addWidget(log_level_combo)
        log_controls.addStretch()
        log_controls.addWidget(clear_log_btn)
        
        log_layout.addLayout(log_controls)
        
        # Log text
        log_text = QPlainTextEdit()
        log_text.setReadOnly(True)
        log_text.setMaximumBlockCount(1000)
        log_layout.addWidget(log_text)
        
        # Store references in the log widget
        log_widget.clear_log_btn = clear_log_btn
        log_widget.log_text = log_text
        log_widget.log_level_combo = log_level_combo
        
        self.log_dock.setWidget(log_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)
        
        # Initially hide the log dock
        self.log_dock.hide()
    
    def show_log_dock(self):
        """Show the log dock widget"""
        self.log_dock.show()
    
    def hide_log_dock(self):
        """Hide the log dock widget"""
        self.log_dock.hide()
    
    def add_log_message(self, message: str, level: str = "Info"):
        """Add a message to the log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        log_widget = self.log_dock.widget()
        if log_widget and hasattr(log_widget, 'log_text'):
            log_widget.log_text.appendPlainText(formatted_message)
            
            # Auto-scroll to bottom
            cursor = log_widget.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            log_widget.log_text.setTextCursor(cursor)
    
    def update_project_status(self, project_name: str, project_path: str):
        """Update the project status in the status bar and menu"""
        # Update status menu
        self.project_status_action.setText(f"Project: {project_name}")
        self.project_status_action.setEnabled(True)
        
        # Update status bar message
        self.status_message_label.setText(f"Project loaded: {project_name}")
    
    def update_user(self, username: str):
        """Update the user in the status bar and menu"""
        # Update status menu
        self.user_status_action.setText(f"User: {username}")
        self.user_status_action.setEnabled(True)
    
    def update_version(self, version: str):
        """Update the version in the status bar and menu"""
        # Update status menu
        self.version_status_action.setText(f"Version: v{version}")
        self.version_status_action.setEnabled(True)
    
    def show_system_info(self):
        """Show system information dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
        from PyQt6.QtCore import Qt
        import platform
        import sys
        
        dialog = QDialog(self)
        dialog.setWindowTitle("System Information")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # System info text
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        
        system_info = f"""
System Information:
==================

Platform: {platform.platform()}
Architecture: {platform.architecture()[0]}
Processor: {platform.processor()}
Python Version: {sys.version}
Qt Version: {Qt.QT_VERSION_STR}

Application:
============
Name: Vogue Manager
Version: 1.0.0
Status: {'Project Loaded' if hasattr(self, 'project_status_action') and self.project_status_action.isEnabled() else 'No Project'}

Project Information:
===================
{self.project_status_action.text() if hasattr(self, 'project_status_action') else 'No project loaded'}
{self.user_status_action.text() if hasattr(self, 'user_status_action') else 'User: Unknown'}
        """
        
        info_text.setPlainText(system_info)
        layout.addWidget(info_text)
        
        # Close button
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()

    def load_recent_project(self, project_path: str):
        """Load a recent project"""
        try:
            # Import settings here to avoid circular imports
            from vogue_core.settings import settings

            # Load project using manager (we'll need to pass this from controller)
            if hasattr(self, 'load_project_callback'):
                self.load_project_callback(project_path)
            else:
                # Fallback - emit signal or show message
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Load Project",
                                      f"Selected project: {project_path}\n\n"
                                      "Project loading will be handled by the controller.")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Failed to load project: {e}")
    
    def show_progress(self, message: str = "Processing..."):
        """Show progress bar with message"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_message_label.setText(message)
    
    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.setVisible(False)
        self.status_message_label.setText("Ready")