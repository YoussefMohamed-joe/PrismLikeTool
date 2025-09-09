"""
Prism-like UI components for Vogue Manager

Complete Prism interface clone with all standard Prism functionalities.
"""

import os
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
    QInputDialog, QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QRect
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction, QPalette, QColor, QPainter, QPen

from .colors import COLORS
from .qss import build_qss


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
                        shot = Shot(sequence=sequence if sequence and sequence != "Shot" else "Main", name=shot_name)
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
        self.setStyleSheet(build_qss())


class ProjectBrowser(PrismStyleWidget):
    """Project browser widget - main left panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize clipboard state for cut/copy operations
        self.clipboard_item = None
        self.clipboard_operation = None  # 'cut' or 'copy'
        self.clipboard_type = None  # 'asset' or 'shot'
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create horizontal splitter for tabs + tasks
        self.horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Asset/Shot tabs
        self.setup_tabs_section()
        self.horizontal_splitter.addWidget(self.tabs_widget)

        # Right side: Tasks section
        self.setup_tasks_section()
        self.horizontal_splitter.addWidget(self.tasks_widget)

        # Set splitter proportions (50% tabs, 50% tasks+departments)
        self.horizontal_splitter.setSizes([400, 400])

        layout.addWidget(self.horizontal_splitter)

        # Set up thumbnail delegates
        self.asset_delegate = ThumbnailDelegate(self.asset_tree)
        self.shot_delegate = ThumbnailDelegate(self.shot_tree)
        self.asset_tree.setItemDelegate(self.asset_delegate)
        self.shot_tree.setItemDelegate(self.shot_delegate)

        # Don't populate with sample data initially - let project loading handle it
        # self.populate_asset_tree()
        # self.populate_shot_tree()

        # Setup context menus
        self.setup_context_menus()

    def setup_tabs_section(self):
        """Setup the tabs section (Assets/Shots)"""
        self.tabs_widget = QWidget()
        tabs_layout = QVBoxLayout(self.tabs_widget)
        tabs_layout.setContentsMargins(5, 5, 5, 5)

        # Main content area with tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setDocumentMode(True)  # Modern tab style

        # Assets tab
        assets_tab = QWidget()
        assets_layout = QVBoxLayout(assets_tab)
        assets_layout.setContentsMargins(5, 5, 5, 5)
        
        # Asset filter (removed type filter since we removed types)
        filter_layout = QHBoxLayout()
        filter_layout.addStretch()
        assets_layout.addLayout(filter_layout)
        
        # Asset tree view (Prism-style hierarchical with thumbnails)
        self.asset_tree = AssetTreeWidget()
        self.asset_tree.setHeaderHidden(True)
        self.asset_tree.setRootIsDecorated(True)
        self.asset_tree.setAlternatingRowColors(True)
        self.asset_tree.setMinimumHeight(300)

        # Enable drag and drop
        self.asset_tree.setDragEnabled(True)
        self.asset_tree.setAcceptDrops(True)
        self.asset_tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.asset_tree.setDropIndicatorShown(True)
        self.asset_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1A2332;
                border: 1px solid #2A3441;
                border-radius: 5px;
                alternate-background-color: #1E2533;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #2A3441;
            }
            QTreeWidget::item:hover {
                background-color: #212A37;
            }
            QTreeWidget::item:selected {
                background-color: #73C2FB;
                color: #12181F;
            }
            QTreeWidget::branch {
                background: transparent;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: none;
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: none;
            }
        """)
        assets_layout.addWidget(self.asset_tree)
        
        # Asset buttons
        asset_btn_layout = QHBoxLayout()
        self.add_asset_btn = QPushButton("Add Asset")
        self.add_asset_btn.setProperty("class", "primary")
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
        
        # Shot tree view (Prism-style hierarchical with thumbnails)
        self.shot_tree = ShotTreeWidget()
        self.shot_tree.setHeaderHidden(True)
        self.shot_tree.setRootIsDecorated(True)
        self.shot_tree.setAlternatingRowColors(True)
        self.shot_tree.setMinimumHeight(300)

        # Enable drag and drop
        self.shot_tree.setDragEnabled(True)
        self.shot_tree.setAcceptDrops(True)
        self.shot_tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.shot_tree.setDropIndicatorShown(True)
        self.shot_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1A2332;
                border: 1px solid #2A3441;
                border-radius: 5px;
                alternate-background-color: #1E2533;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #2A3441;
            }
            QTreeWidget::item:hover {
                background-color: #212A37;
            }
            QTreeWidget::item:selected {
                background-color: #73C2FB;
                color: #12181F;
            }
            QTreeWidget::branch {
                background: transparent;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: none;
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: none;
            }
        """)
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
        """Setup the Tasks section with project info, tasks, and departments underneath"""
        self.tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(self.tasks_widget)
        tasks_layout.setContentsMargins(5, 5, 5, 5)

        # Project Info Section
        self.setup_project_info_section()
        tasks_layout.addWidget(self.project_info_widget)

        # Tasks Section
        tasks_group = QGroupBox("Tasks")
        tasks_section_layout = QVBoxLayout(tasks_group)

        # Task Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.task_filter_combo = QComboBox()
        self.task_filter_combo.addItems(["All Tasks", "My Tasks", "Active", "Completed", "Pending"])
        filter_layout.addWidget(self.task_filter_combo)
        filter_layout.addStretch()
        tasks_section_layout.addLayout(filter_layout)

        # Tasks List
        self.tasks_list = QListWidget()
        self.tasks_list.setAlternatingRowColors(True)
        # Removed maximum height restriction to allow full vertical expansion

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

        tasks_section_layout.addWidget(self.tasks_list)

        # Task Actions
        task_actions_layout = QHBoxLayout()
        self.new_task_btn = QPushButton("New Task")
        self.new_task_btn.setProperty("class", "primary")
        self.assign_task_btn = QPushButton("Assign")
        self.complete_task_btn = QPushButton("Complete")

        task_actions_layout.addWidget(self.new_task_btn)
        task_actions_layout.addWidget(self.assign_task_btn)
        task_actions_layout.addWidget(self.complete_task_btn)
        task_actions_layout.addStretch()

        tasks_section_layout.addLayout(task_actions_layout)
        tasks_layout.addWidget(tasks_group)

        # Departments Section (underneath tasks)
        dept_group = QGroupBox("Departments")
        dept_layout = QVBoxLayout(dept_group)

        self.departments_list = QListWidget()
        self.departments_list.setAlternatingRowColors(True)
        # Removed maximum height restriction to allow full vertical expansion

        # Add default departments
        departments = [
            "Modeling - Active",
            "Texturing - Active",
            "Rigging - Active",
            "Animation - Active",
            "Lighting - Standby",
            "Rendering - Standby"
        ]

        for dept in departments:
            item = QListWidgetItem(dept)
            self.departments_list.addItem(item)

        dept_layout.addWidget(self.departments_list)

        # Add stretch to allow departments list to expand
        dept_layout.addStretch()

        # Department Actions
        dept_actions_layout = QHBoxLayout()
        self.add_dept_btn = QPushButton("Add Dept")
        self.add_dept_btn.setProperty("class", "primary")
        self.edit_dept_btn = QPushButton("Edit")
        self.remove_dept_btn = QPushButton("Remove")

        dept_actions_layout.addWidget(self.add_dept_btn)
        dept_actions_layout.addWidget(self.edit_dept_btn)
        dept_actions_layout.addWidget(self.remove_dept_btn)
        dept_actions_layout.addStretch()

        dept_layout.addLayout(dept_actions_layout)
        tasks_layout.addWidget(dept_group)

        tasks_layout.addStretch()

    def setup_project_info_section(self):
        """Setup the Project Info section above tasks"""
        self.project_info_widget = QWidget()
        info_layout = QVBoxLayout(self.project_info_widget)
        info_layout.setContentsMargins(5, 5, 5, 5)

        # Project info group
        project_group = QGroupBox("Project Info")
        project_layout = QVBoxLayout(project_group)

        # Project name and path display
        self.project_name_label = QLabel("Project: No Project Loaded")
        self.project_name_label.setStyleSheet("font-weight: bold; color: #73C2FB;")
        project_layout.addWidget(self.project_name_label)

        self.project_path_label = QLabel("Path: Not Available")
        self.project_path_label.setStyleSheet("font-size: 10px; color: #788490;")
        self.project_path_label.setWordWrap(True)
        project_layout.addWidget(self.project_path_label)

        info_layout.addWidget(project_group)

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
        # Asset tree context menu
        self.asset_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.asset_tree.customContextMenuRequested.connect(self.show_asset_context_menu)

        # Shot tree context menu
        self.shot_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.shot_tree.customContextMenuRequested.connect(self.show_shot_context_menu)

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
            # Check if folder with this name already exists
            folder_exists = False
            tree_widget = self.asset_tree if list_type == "asset" else self.shot_tree
            for i in range(tree_widget.topLevelItemCount()):
                item = tree_widget.topLevelItem(i)
                if item.text(0) == folder_name and item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
                    folder_exists = True
                    break

            if not folder_exists:
                # Create new folder item
                if list_type == "asset":
                    folder_item = QTreeWidgetItem(self.asset_tree)
                    folder_item.setText(0, folder_name)
                    folder_item.setData(0, Qt.ItemDataRole.UserRole, "Folder")
                else:
                    folder_item = QTreeWidgetItem(self.shot_tree)
                    folder_item.setText(0, folder_name)
                    folder_item.setData(0, Qt.ItemDataRole.UserRole, "Folder")

                self.add_log_message(f"Folder '{folder_name}' created in {list_type}s")

                # Auto-save the project
                if auto_save_project(self):
                    self.add_log_message("Project auto-saved")
                    # Force refresh the tree to show changes
                    self.asset_tree.update()
                    self.shot_tree.update()
                else:
                    self.add_log_message("Auto-save skipped: no project loaded")
            else:
                self.add_log_message(f"Folder '{folder_name}' already exists")

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

        # Check if we're dropping on a folder
        if target_item and target_item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
            # Allow drop on folders
            super().dropEvent(event)
            # Log the move
            dragged_item = self.currentItem()
            if dragged_item:
                item_name = dragged_item.text(0)
                folder_name = target_item.text(0)
                print(f"[LOG] Asset '{item_name}' moved to folder '{folder_name}'")

                # Auto-save the project after drag and drop
                if auto_save_project(self.parent()):
                    print("[LOG] Project auto-saved after drag and drop")
                else:
                    print("[LOG] Auto-save skipped after drag and drop: no project loaded")
        elif not target_item:
            # Allow drop on empty space (root level)
            super().dropEvent(event)
        else:
            # Reject drop on non-folder items
            event.ignore()

class ShotTreeWidget(QTreeWidget):
    """Custom tree widget with enhanced drag and drop support for shots"""

    def dropEvent(self, event):
        """Handle drop events to ensure items are only dropped on folders"""
        # Get the drop position
        pos = event.position().toPoint()
        target_item = self.itemAt(pos)

        # Check if we're dropping on a folder
        if target_item and target_item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
            # Allow drop on folders
            super().dropEvent(event)
            # Log the move
            dragged_item = self.currentItem()
            if dragged_item:
                item_name = dragged_item.text(0)
                folder_name = target_item.text(0)
                print(f"[LOG] Shot '{item_name}' moved to folder '{folder_name}'")

                # Auto-save the project after drag and drop
                if auto_save_project(self.parent()):
                    print("[LOG] Project auto-saved after drag and drop")
                else:
                    print("[LOG] Auto-save skipped after drag and drop: no project loaded")
        elif not target_item:
            # Allow drop on empty space (root level)
            super().dropEvent(event)
        else:
            # Reject drop on non-folder items
            event.ignore()

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
            painter.setPen(QColor("#E0E0E0"))
        else:
            painter.fillRect(option.rect, QColor("transparent"))
            painter.setPen(QColor("#E0E0E0"))

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
        """Setup the Asset Info widget like Prism VFX"""
        self.asset_info_widget = QWidget()
        info_layout = QVBoxLayout(self.asset_info_widget)
        info_layout.setContentsMargins(5, 5, 5, 5)

        # Current Asset Info
        asset_group = QGroupBox("Current Asset")
        asset_info_layout = QFormLayout(asset_group)

        self.asset_name_label = QLabel("No Selection")
        self.asset_name_label.setProperty("class", "title")
        self.asset_type_label = QLabel("-")
        self.asset_path_label = QLabel("-")
        self.asset_status_label = QLabel("-")
        self.asset_artist_label = QLabel("-")
        self.asset_date_label = QLabel("-")

        asset_info_layout.addRow("Name:", self.asset_name_label)
        asset_info_layout.addRow("Type:", self.asset_type_label)
        asset_info_layout.addRow("Path:", self.asset_path_label)
        asset_info_layout.addRow("Status:", self.asset_status_label)
        asset_info_layout.addRow("Artist:", self.asset_artist_label)
        asset_info_layout.addRow("Modified:", self.asset_date_label)

        info_layout.addWidget(asset_group)

        # Asset Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.asset_preview_label = QLabel("No Preview Available")
        self.asset_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.asset_preview_label.setMinimumHeight(120)
        self.asset_preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['panel']};
                border: 2px dashed {COLORS['border']};
                border-radius: 4px;
                color: {COLORS['muted']};
            }}
        """)

        preview_layout.addWidget(self.asset_preview_label)
        info_layout.addWidget(preview_group)

        # Asset Metadata
        metadata_group = QGroupBox("Metadata")
        metadata_layout = QVBoxLayout(metadata_group)

        self.asset_metadata_text = QTextEdit()
        self.asset_metadata_text.setPlainText("No metadata available")
        self.asset_metadata_text.setMaximumHeight(80)
        self.asset_metadata_text.setReadOnly(True)

        metadata_layout.addWidget(self.asset_metadata_text)
        info_layout.addWidget(metadata_group)

        # Asset Actions
        actions_group = QGroupBox("Asset Actions")
        actions_layout = QVBoxLayout(actions_group)

        self.open_asset_btn = QPushButton("Open Asset")
        self.open_asset_btn.setProperty("class", "primary")
        self.copy_path_btn = QPushButton("Copy Path")
        self.show_in_explorer_btn = QPushButton("Show in Explorer")
        self.asset_properties_btn = QPushButton("Properties")

        actions_layout.addWidget(self.open_asset_btn)
        actions_layout.addWidget(self.copy_path_btn)
        actions_layout.addWidget(self.show_in_explorer_btn)
        actions_layout.addWidget(self.asset_properties_btn)

        info_layout.addWidget(actions_group)
        info_layout.addStretch()


class VersionManager(PrismStyleWidget):
    """Version manager widget - main right panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header with entity info
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.Box)
        header_frame.setStyleSheet(f"QFrame {{ background-color: {COLORS['hover']}; border: 1px solid {COLORS['border']}; }}")
        header_layout = QVBoxLayout(header_frame)
        
        self.entity_name_label = QLabel("No Selection")
        self.entity_name_label.setProperty("class", "title")
        self.entity_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.entity_name_label)
        
        self.entity_type_label = QLabel("")
        self.entity_type_label.setProperty("class", "muted")
        self.entity_type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.entity_type_label)
        
        layout.addWidget(header_frame)
        
        # Version controls
        controls_layout = QHBoxLayout()
        
        self.publish_btn = QPushButton("Publish")
        self.publish_btn.setProperty("class", "primary")
        self.publish_btn.setEnabled(False)
        
        self.import_btn = QPushButton("Import")
        self.import_btn.setEnabled(False)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setEnabled(False)
        
        controls_layout.addWidget(self.publish_btn)
        controls_layout.addWidget(self.import_btn)
        controls_layout.addWidget(self.export_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Version table
        self.version_table = QTableWidget()
        self.version_table.setColumnCount(6)
        self.version_table.setHorizontalHeaderLabels([
            "Version", "User", "Date", "Comment", "Status", "Path"
        ])
        self.version_table.horizontalHeader().setStretchLastSection(True)
        self.version_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.version_table.setAlternatingRowColors(True)
        self.version_table.setSortingEnabled(True)
        
        # Set column widths
        header = self.version_table.horizontalHeader()
        header.resizeSection(0, 80)   # Version
        header.resizeSection(1, 100)  # User
        header.resizeSection(2, 120)  # Date
        header.resizeSection(3, 200)  # Comment
        header.resizeSection(4, 80)   # Status
        
        layout.addWidget(self.version_table)
        
        # Version info panel
        info_group = QGroupBox("Version Info")
        info_layout = QVBoxLayout(info_group)
        
        # Version details
        details_layout = QGridLayout()
        
        details_layout.addWidget(QLabel("Version:"), 0, 0)
        self.version_label = QLabel("-")
        details_layout.addWidget(self.version_label, 0, 1)
        
        details_layout.addWidget(QLabel("User:"), 1, 0)
        self.user_label = QLabel("-")
        details_layout.addWidget(self.user_label, 1, 1)
        
        details_layout.addWidget(QLabel("Date:"), 2, 0)
        self.date_label = QLabel("-")
        details_layout.addWidget(self.date_label, 2, 1)
        
        details_layout.addWidget(QLabel("Comment:"), 3, 0)
        self.comment_label = QLabel("-")
        self.comment_label.setWordWrap(True)
        details_layout.addWidget(self.comment_label, 3, 1)
        
        info_layout.addLayout(details_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.open_btn = QPushButton("Open")
        self.open_btn.setEnabled(False)
        
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.setProperty("class", "danger")
        
        action_layout.addWidget(self.open_btn)
        action_layout.addWidget(self.copy_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addStretch()
        
        info_layout.addLayout(action_layout)
        
        layout.addWidget(info_group)


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
        
        # Apply Prism-like styling with enhanced design
        self.setStyleSheet(build_qss())

        # Set window properties for better appearance
        self.setWindowIconText("Vogue Manager")
        
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_docks()
    
    def setup_ui(self):
        """Set up the main UI layout"""
        # Create central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Project Browser
        self.project_browser = ProjectBrowser()
        main_splitter.addWidget(self.project_browser)
        
        # Center panel - Version Manager
        self.version_manager = VersionManager()
        main_splitter.addWidget(self.version_manager)
        
        # Right panel - Prism-style Tasks/Departments/Asset Info
        self.right_panel = PrismRightPanel()
        main_splitter.addWidget(self.right_panel)
        
        # Set splitter proportions (40% left, 50% center, 10% right)
        # Optimized for left panel with tabs+tasks+departments, center version manager, right asset info only
        main_splitter.setSizes([560, 700, 140])
        layout.addWidget(main_splitter)
    
    def setup_menu(self):
        """Set up the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Project submenu
        project_menu = file_menu.addMenu("&Project")
        
        browse_action = QAction("&Browse Project...", self)
        browse_action.setShortcut("Ctrl+O")
        project_menu.addAction(browse_action)
        
        new_action = QAction("&New Project...", self)
        new_action.setShortcut("Ctrl+N")
        project_menu.addAction(new_action)
        
        open_action = QAction("&Open Project...", self)
        open_action.setShortcut("Ctrl+Shift+O")
        project_menu.addAction(open_action)
        
        project_menu.addSeparator()

        # Recent Projects menu item
        self.recent_projects_action = QAction("&Recent Projects...", self)
        self.recent_projects_action.setShortcut("Ctrl+R")
        project_menu.addAction(self.recent_projects_action)
        
        project_menu.addSeparator()
        
        # Prism-specific project actions
        import_project_action = QAction("&Import Project...", self)
        project_menu.addAction(import_project_action)
        
        export_project_action = QAction("&Export Project...", self)
        project_menu.addAction(export_project_action)
        
        project_menu.addSeparator()
        
        project_settings_action = QAction("&Project Settings...", self)
        project_settings_action.setShortcut("Ctrl+Shift+P")
        project_menu.addAction(project_settings_action)
        
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