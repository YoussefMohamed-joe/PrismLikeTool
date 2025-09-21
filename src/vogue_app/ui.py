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
    QDialog, QInputDialog, QStyledItemDelegate, QStyle
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
        self.tasks_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
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
        self.setup_asset_actions()
        info_layout.addWidget(self.asset_actions_widget)

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
        self.asset_preview_label.setMinimumHeight(120)
        self.asset_preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['outline']};
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

        # Style the labels
        for label in [self.asset_path_label, self.asset_artist_label, self.asset_date_label]:
            label.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    color: {COLORS['fg_variant']};
                    background-color: {COLORS['surface']};
                    padding: 4px 8px;
                    border-radius: 4px;
                    border: 1px solid {COLORS['outline']};
                }}
            """)

        details_content_layout.addRow("Path:", self.asset_path_label)
        details_content_layout.addRow("Artist:", self.asset_artist_label)
        details_content_layout.addRow("Modified:", self.asset_date_label)

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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
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
        
        # Version info panel (Ayon style)
        self.setup_version_info()
        layout.addWidget(self.info_widget)

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

    def setup_version_table(self):
        """Setup version table in Ayon style"""
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
        main_splitter.addWidget(self.version_manager)
        
        # Right panel - Prism-style Tasks/Departments/Asset Info
        self.right_panel = PrismRightPanel()
        main_splitter.addWidget(self.right_panel)
        
        # Set splitter proportions (40% left, 50% center, 10% right)
        # Optimized for left panel with tabs+tasks+departments, center version manager, right asset info only
        main_splitter.setSizes([560, 700, 140])
        layout.addWidget(main_splitter)
        
        return central_widget
    
    def create_tasks_tab(self):
        """Create the Tasks tab content (placeholder for future implementation)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Tasks")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Content placeholder
        content = QLabel("Advanced task management features will be implemented here")
        content.setProperty("class", "muted")
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(content)
        
        layout.addStretch()
        return widget
    
    def create_inbox_tab(self):
        """Create the Inbox tab content"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Inbox")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Content placeholder
        content = QLabel("Notifications and messages will be here")
        content.setProperty("class", "muted")
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(content)
        
        layout.addStretch()
        return widget
    
    def create_teams_tab(self):
        """Create the Teams tab content"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Teams")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Content placeholder
        content = QLabel("Team collaboration and user management will be here")
        content.setProperty("class", "muted")
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(content)
        
        layout.addStretch()
        return widget
    
    def create_dashboard_tab(self):
        """Create the Dashboard tab content"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Dashboard")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Content placeholder
        content = QLabel("Project statistics and analytics will be here")
        content.setProperty("class", "muted")
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(content)
        
        layout.addStretch()
        return widget
    
    def create_settings_tab(self):
        """Create the Settings tab content"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Settings")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Content placeholder
        content = QLabel("Application settings and preferences will be here")
        content.setProperty("class", "muted")
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(content)
        
        layout.addStretch()
        return widget
    
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