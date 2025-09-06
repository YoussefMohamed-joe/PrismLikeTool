"""
Simplified UI components for Vogue Manager

Defines the main window and UI widgets for the desktop application.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import PyQt6 directly
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QPlainTextEdit, QPushButton, QLabel, QSplitter, QGroupBox,
    QMenuBar, QMenu, QToolBar, QStatusBar, QFileDialog, QMessageBox,
    QHeaderView, QAbstractItemView, QProgressBar, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction

from .colors import COLORS
from .qss import build_qss


class OverviewWidget(QWidget):
    """Overview tab widget showing project summary"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Project info section
        info_group = QGroupBox("Project Information")
        info_layout = QGridLayout(info_group)
        
        self.name_label = QLabel("No project loaded")
        self.name_label.setProperty("class", "title")
        info_layout.addWidget(QLabel("Name:"), 0, 0)
        info_layout.addWidget(self.name_label, 0, 1)
        
        self.path_label = QLabel("")
        self.path_label.setProperty("class", "muted")
        info_layout.addWidget(QLabel("Path:"), 1, 0)
        info_layout.addWidget(self.path_label, 1, 1)
        
        self.fps_label = QLabel("")
        info_layout.addWidget(QLabel("FPS:"), 2, 0)
        info_layout.addWidget(self.fps_label, 2, 1)
        
        self.resolution_label = QLabel("")
        info_layout.addWidget(QLabel("Resolution:"), 3, 0)
        info_layout.addWidget(self.resolution_label, 3, 1)
        
        layout.addWidget(info_group)
        
        # Statistics section
        stats_group = QGroupBox("Statistics")
        stats_layout = QGridLayout(stats_group)
        
        self.asset_count_label = QLabel("0")
        self.asset_count_label.setProperty("class", "subtitle")
        stats_layout.addWidget(QLabel("Assets:"), 0, 0)
        stats_layout.addWidget(self.asset_count_label, 0, 1)
        
        self.shot_count_label = QLabel("0")
        self.shot_count_label.setProperty("class", "subtitle")
        stats_layout.addWidget(QLabel("Shots:"), 1, 0)
        stats_layout.addWidget(self.shot_count_label, 1, 1)
        
        self.version_count_label = QLabel("0")
        self.version_count_label.setProperty("class", "subtitle")
        stats_layout.addWidget(QLabel("Versions:"), 2, 0)
        stats_layout.addWidget(self.version_count_label, 2, 1)
        
        layout.addWidget(stats_group)
        
        # Raw pipeline.json section
        pipeline_group = QGroupBox("Pipeline Data")
        pipeline_layout = QVBoxLayout(pipeline_group)
        
        self.pipeline_text = QPlainTextEdit()
        self.pipeline_text.setReadOnly(True)
        self.pipeline_text.setMaximumHeight(200)
        pipeline_layout.addWidget(self.pipeline_text)
        
        layout.addWidget(pipeline_group)
    
    def update_project_info(self, project_info: Dict[str, Any]):
        """Update the overview with project information"""
        self.name_label.setText(project_info.get("name", "Unknown"))
        self.path_label.setText(project_info.get("path", ""))
        self.fps_label.setText(str(project_info.get("fps", 0)))
        self.resolution_label.setText(f"{project_info.get('resolution', [0, 0])[0]}x{project_info.get('resolution', [0, 0])[1]}")
        
        self.asset_count_label.setText(str(project_info.get("asset_count", 0)))
        self.shot_count_label.setText(str(project_info.get("shot_count", 0)))
        self.version_count_label.setText(str(project_info.get("total_versions", 0)))
    
    def update_pipeline_data(self, pipeline_data: Dict[str, Any]):
        """Update the raw pipeline data display"""
        import json
        formatted_json = json.dumps(pipeline_data, indent=2, ensure_ascii=False)
        self.pipeline_text.setPlainText(formatted_json)


class AssetsWidget(QWidget):
    """Assets tab widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Left side - Asset tree
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(QLabel("Assets"))
        self.asset_tree = QTreeWidget()
        self.asset_tree.setHeaderLabels(["Name", "Type"])
        self.asset_tree.setRootIsDecorated(True)
        left_layout.addWidget(self.asset_tree)
        
        # Right side - Versions table
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        right_layout.addWidget(QLabel("Versions"))
        self.versions_table = QTableWidget()
        self.versions_table.setColumnCount(5)
        self.versions_table.setHorizontalHeaderLabels(["Version", "User", "Date", "Comment", "Path"])
        self.versions_table.horizontalHeader().setStretchLastSection(True)
        self.versions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        right_layout.addWidget(self.versions_table)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])
        layout.addWidget(splitter)
    
    def update_assets(self, assets: List[Dict[str, Any]]):
        """Update the assets tree"""
        self.asset_tree.clear()
        
        # Group assets by type
        asset_types = {}
        for asset in assets:
            asset_type = asset.get("type", "Unknown")
            if asset_type not in asset_types:
                asset_types[asset_type] = []
            asset_types[asset_type].append(asset)
        
        # Create tree structure
        for asset_type, type_assets in asset_types.items():
            type_item = QTreeWidgetItem([asset_type, ""])
            type_item.setExpanded(True)
            self.asset_tree.addTopLevelItem(type_item)
            
            for asset in type_assets:
                asset_item = QTreeWidgetItem([asset["name"], asset_type])
                type_item.addChild(asset_item)
    
    def update_versions(self, versions: List[Dict[str, Any]]):
        """Update the versions table"""
        self.versions_table.setRowCount(len(versions))
        
        for row, version in enumerate(versions):
            self.versions_table.setItem(row, 0, QTableWidgetItem(version.get("version", "")))
            self.versions_table.setItem(row, 1, QTableWidgetItem(version.get("user", "")))
            self.versions_table.setItem(row, 2, QTableWidgetItem(version.get("date", "")))
            self.versions_table.setItem(row, 3, QTableWidgetItem(version.get("comment", "")))
            self.versions_table.setItem(row, 4, QTableWidgetItem(version.get("path", "")))
        
        self.versions_table.resizeColumnsToContents()


class ShotsWidget(QWidget):
    """Shots tab widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Left side - Shot tree
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(QLabel("Shots"))
        self.shot_tree = QTreeWidget()
        self.shot_tree.setHeaderLabels(["Sequence", "Shot"])
        self.shot_tree.setRootIsDecorated(True)
        left_layout.addWidget(self.shot_tree)
        
        # Right side - Versions table
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        right_layout.addWidget(QLabel("Versions"))
        self.versions_table = QTableWidget()
        self.versions_table.setColumnCount(5)
        self.versions_table.setHorizontalHeaderLabels(["Version", "User", "Date", "Comment", "Path"])
        self.versions_table.horizontalHeader().setStretchLastSection(True)
        self.versions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        right_layout.addWidget(self.versions_table)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])
        layout.addWidget(splitter)
    
    def update_shots(self, shots: List[Dict[str, Any]]):
        """Update the shots tree"""
        self.shot_tree.clear()
        
        # Group shots by sequence
        sequences = {}
        for shot in shots:
            sequence = shot.get("sequence", "Unknown")
            if sequence not in sequences:
                sequences[sequence] = []
            sequences[sequence].append(shot)
        
        # Create tree structure
        for sequence, sequence_shots in sequences.items():
            seq_item = QTreeWidgetItem([sequence, ""])
            seq_item.setExpanded(True)
            self.shot_tree.addTopLevelItem(seq_item)
            
            for shot in sequence_shots:
                shot_item = QTreeWidgetItem([shot["name"], sequence])
                seq_item.addChild(shot_item)
    
    def update_versions(self, versions: List[Dict[str, Any]]):
        """Update the versions table"""
        self.versions_table.setRowCount(len(versions))
        
        for row, version in enumerate(versions):
            self.versions_table.setItem(row, 0, QTableWidgetItem(version.get("version", "")))
            self.versions_table.setItem(row, 1, QTableWidgetItem(version.get("user", "")))
            self.versions_table.setItem(row, 2, QTableWidgetItem(version.get("date", "")))
            self.versions_table.setItem(row, 3, QTableWidgetItem(version.get("comment", "")))
            self.versions_table.setItem(row, 4, QTableWidgetItem(version.get("path", "")))
        
        self.versions_table.resizeColumnsToContents()


class LogWidget(QWidget):
    """Log tab widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Log controls
        controls_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear Log")
        self.clear_button.clicked.connect(self.clear_log)
        controls_layout.addWidget(self.clear_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Log text
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)  # Limit log size
        layout.addWidget(self.log_text)
    
    def add_log_message(self, message: str):
        """Add a message to the log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.appendPlainText(formatted_message)
        
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.clear()


class VogueMainWindow(QMainWindow):
    """Main window for Vogue Manager"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vogue Manager")
        self.setMinimumSize(1200, 800)
        
        # Apply styling
        self.setStyleSheet(build_qss())
        
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
    
    def setup_ui(self):
        """Set up the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.overview_widget = OverviewWidget()
        self.assets_widget = AssetsWidget()
        self.shots_widget = ShotsWidget()
        self.log_widget = LogWidget()
        
        self.tab_widget.addTab(self.overview_widget, "Overview")
        self.tab_widget.addTab(self.assets_widget, "Assets")
        self.tab_widget.addTab(self.shots_widget, "Shots")
        self.tab_widget.addTab(self.log_widget, "Log")
    
    def setup_menu(self):
        """Set up the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        browse_action = QAction("&Browse Project...", self)
        browse_action.setShortcut("Ctrl+O")
        file_menu.addAction(browse_action)
        
        save_action = QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        tools_menu.addAction(refresh_action)
        
        scan_action = QAction("&Scan Filesystem", self)
        tools_menu.addAction(scan_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Set up the toolbar"""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        
        # Browse project button
        browse_action = QAction("Browse", self)
        browse_action.setToolTip("Browse for project")
        toolbar.addAction(browse_action)
        
        # Save project button
        save_action = QAction("Save", self)
        save_action.setToolTip("Save project")
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Publish button
        publish_action = QAction("Publish", self)
        publish_action.setToolTip("Publish current selection")
        toolbar.addAction(publish_action)
        
        toolbar.addSeparator()
        
        # Refresh button
        refresh_action = QAction("Refresh", self)
        refresh_action.setToolTip("Refresh project data")
        toolbar.addAction(refresh_action)
    
    def setup_statusbar(self):
        """Set up the status bar"""
        self.status_bar = self.statusBar()
        
        # Project status
        self.project_status_label = QLabel("No project loaded")
        self.status_bar.addWidget(self.project_status_label)
        
        # User label
        self.user_label = QLabel("User: Unknown")
        self.status_bar.addPermanentWidget(self.user_label)
    
    def update_project_status(self, project_name: str, project_path: str):
        """Update the project status in the status bar"""
        self.project_status_label.setText(f"Project: {project_name} ({project_path})")
    
    def update_user(self, username: str):
        """Update the user in the status bar"""
        self.user_label.setText(f"User: {username}")
    
    def add_log_message(self, message: str):
        """Add a message to the log tab"""
        self.log_widget.add_log_message(message)
