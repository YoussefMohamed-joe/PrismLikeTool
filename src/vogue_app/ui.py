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
    QButtonGroup, QRadioButton, QToolButton, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QRect
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction, QPalette, QColor, QPainter

from .colors import COLORS
from .qss import build_qss


class PrismStyleWidget(QWidget):
    """Base widget with Prism styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(build_qss())


class ProjectBrowser(PrismStyleWidget):
    """Project browser widget - main left panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
        
        # Asset type filter
        filter_layout = QHBoxLayout()
        self.asset_type_combo = QComboBox()
        self.asset_type_combo.addItems(["All", "Characters", "Props", "Environments"])
        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.asset_type_combo)
        filter_layout.addStretch()
        assets_layout.addLayout(filter_layout)
        
        # Asset tree
        self.asset_tree = QTreeWidget()
        self.asset_tree.setHeaderLabels(["Name", "Type", "Versions"])
        self.asset_tree.setRootIsDecorated(True)
        self.asset_tree.setAlternatingRowColors(True)
        self.asset_tree.setSortingEnabled(True)
        self.asset_tree.setMinimumHeight(300)
        assets_layout.addWidget(self.asset_tree)
        
        # Asset buttons
        asset_btn_layout = QHBoxLayout()
        self.add_asset_btn = QPushButton("Add Asset")
        self.add_asset_btn.setProperty("class", "primary")
        self.refresh_assets_btn = QPushButton("Refresh")
        asset_btn_layout.addWidget(self.add_asset_btn)
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
        
        # Shot tree
        self.shot_tree = QTreeWidget()
        self.shot_tree.setHeaderLabels(["Shot", "Sequence", "Versions"])
        self.shot_tree.setRootIsDecorated(True)
        self.shot_tree.setAlternatingRowColors(True)
        self.shot_tree.setSortingEnabled(True)
        self.shot_tree.setMinimumHeight(300)
        shots_layout.addWidget(self.shot_tree)
        
        # Shot buttons
        shot_btn_layout = QHBoxLayout()
        self.add_shot_btn = QPushButton("Add Shot")
        self.add_shot_btn.setProperty("class", "primary")
        self.refresh_shots_btn = QPushButton("Refresh")
        shot_btn_layout.addWidget(self.add_shot_btn)
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
        
        # Recent files submenu
        recent_menu = file_menu.addMenu("&Recent Projects")
        self.recent_menu = recent_menu
        
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
        
        add_asset_action = QAction("&Add Asset...", self)
        add_asset_action.setShortcut("Ctrl+A")
        assets_menu.addAction(add_asset_action)
        
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
        add_asset_action = QAction("Add Asset", self)
        add_asset_action.setToolTip("Add new asset")
        add_asset_action.setShortcut("Ctrl+A")
        toolbar.addAction(add_asset_action)
        
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
    
    def show_recent_projects_dialog(self):
        """Show recent projects dialog"""
        from .dialogs import RecentProjectsDialog

        # Create and show recent projects dialog
        dialog = RecentProjectsDialog(self)
        dialog.project_selected.connect(self.load_recent_project)
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