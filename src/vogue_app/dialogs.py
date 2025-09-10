"""
Dialog windows for Vogue Manager

Contains all dialog windows for project creation, asset management, etc.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QSpinBox,
    QFileDialog, QMessageBox, QGroupBox, QCheckBox, QListWidget,
    QListWidgetItem, QTabWidget, QWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSplitter, QFrame, QScrollArea,
    QButtonGroup, QRadioButton, QSlider, QProgressBar, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QPixmap, QFont, QIcon, QPalette, QColor

from vogue_core.manager import ProjectManager
from vogue_core.models import Project, Asset, Shot, Version, Department, Task
from vogue_core.settings import settings
from vogue_core.fs import ensure_layout, atomic_write_json
from vogue_core.schema import project_to_pipeline, pipeline_to_project
from .colors import COLORS


class NewProjectDialog(QDialog):
    """Dialog for creating a new project"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Project info group
        info_group = QGroupBox("Project Information")
        info_layout = QFormLayout(info_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter project name...")
        info_layout.addRow("Project Name:", self.name_edit)
        
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select project directory...")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_path)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        info_layout.addRow("Project Path:", path_layout)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Project description (optional)...")
        info_layout.addRow("Description:", self.description_edit)
        
        layout.addWidget(info_group)
        
        # Project settings group
        settings_group = QGroupBox("Project Settings")
        settings_layout = QFormLayout(settings_group)
        
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(12, 120)
        self.fps_spin.setValue(24)
        settings_layout.addRow("Frame Rate:", self.fps_spin)
        
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1920x1080 (HD)",
            "3840x2160 (4K)",
            "1280x720 (HD 720p)",
            "2560x1440 (2K)",
            "Custom"
        ])
        settings_layout.addRow("Resolution:", self.resolution_combo)
        
        self.custom_res_widget = QWidget()
        custom_res_layout = QHBoxLayout(self.custom_res_widget)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 8000)
        self.width_spin.setValue(1920)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 8000)
        self.height_spin.setValue(1080)
        custom_res_layout.addWidget(QLabel("Width:"))
        custom_res_layout.addWidget(self.width_spin)
        custom_res_layout.addWidget(QLabel("Height:"))
        custom_res_layout.addWidget(self.height_spin)
        custom_res_layout.addStretch()
        self.custom_res_widget.setVisible(False)
        settings_layout.addRow("Custom Resolution:", self.custom_res_widget)
        
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        
        layout.addWidget(settings_group)
        
        # Departments and tasks
        dept_group = QGroupBox("Departments & Tasks")
        dept_layout = QVBoxLayout(dept_group)
        
        # Default departments
        self.departments = [
            {"name": "Modeling", "color": "#FF7F7F", "tasks": ["High", "Mid", "Low"]},
            {"name": "Texturing", "color": "#5FD4C7", "tasks": ["Diffuse", "Normal", "Roughness"]},
            {"name": "Rigging", "color": "#73C2FB", "tasks": ["Rig", "Controls", "Skinning"]},
            {"name": "Animation", "color": "#7FB97F", "tasks": ["Blocking", "Spline", "Polish"]},
            {"name": "Lighting", "color": "#FFD700", "tasks": ["Key", "Fill", "Rim"]},
            {"name": "Rendering", "color": "#E6A3E6", "tasks": ["Beauty", "AOVs", "Comp"]}
        ]
        
        self.dept_table = QTableWidget()
        self.dept_table.setColumnCount(3)
        self.dept_table.setHorizontalHeaderLabels(["Department", "Color", "Tasks"])
        self.dept_table.horizontalHeader().setStretchLastSection(True)
        self.dept_table.setMaximumHeight(150)
        
        # Populate departments
        self.populate_departments()
        
        dept_layout.addWidget(self.dept_table)
        
        # Department buttons
        dept_btn_layout = QHBoxLayout()
        add_dept_btn = QPushButton("Add Department")
        remove_dept_btn = QPushButton("Remove Department")
        add_dept_btn.clicked.connect(self.add_department)
        remove_dept_btn.clicked.connect(self.remove_department)
        dept_btn_layout.addWidget(add_dept_btn)
        dept_btn_layout.addWidget(remove_dept_btn)
        dept_btn_layout.addStretch()
        dept_layout.addLayout(dept_btn_layout)
        
        layout.addWidget(dept_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def browse_path(self):
        """Browse for project directory"""
        path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if path:
            self.path_edit.setText(path)
            
    def on_resolution_changed(self, text):
        """Handle resolution combo change"""
        self.custom_res_widget.setVisible(text == "Custom")
        
    def populate_departments(self):
        """Populate departments table"""
        self.dept_table.setRowCount(len(self.departments))
        
        for row, dept in enumerate(self.departments):
            # Department name
            name_item = QTableWidgetItem(dept["name"])
            self.dept_table.setItem(row, 0, name_item)
            
            # Color
            color_item = QTableWidgetItem(dept["color"])
            self.dept_table.setItem(row, 1, color_item)
            
            # Tasks
            tasks_item = QTableWidgetItem(", ".join(dept["tasks"]))
            self.dept_table.setItem(row, 2, tasks_item)
    
    def add_department(self):
        """Add a new department"""
        # Add new department to the list
        new_dept = {
            "name": "New Department",
            "color": "#73C2FB",
            "tasks": ["WIP", "Review", "Final"]
        }
        self.departments.append(new_dept)
        self.populate_departments()
        
        # Select the new row for editing
        new_row = len(self.departments) - 1
        self.dept_table.selectRow(new_row)
        self.dept_table.edit(self.dept_table.item(new_row, 0))
    
    def remove_department(self):
        """Remove selected department"""
        current_row = self.dept_table.currentRow()
        if current_row >= 0 and current_row < len(self.departments):
            # Remove from departments list
            del self.departments[current_row]
            self.populate_departments()
            
            # Select the next available row
            if current_row < len(self.departments):
                self.dept_table.selectRow(current_row)
            elif len(self.departments) > 0:
                self.dept_table.selectRow(len(self.departments) - 1)
            
    def get_project_data(self):
        """Get project data from dialog"""
        name = self.name_edit.text().strip()
        path = self.path_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        
        if not name or not path:
            return None
            
        # Get resolution
        resolution_text = self.resolution_combo.currentText()
        if resolution_text == "Custom":
            width = self.width_spin.value()
            height = self.height_spin.value()
        else:
            # Parse resolution from text
            res_part = resolution_text.split(" ")[0]
            width, height = map(int, res_part.split("x"))
            
        # Get departments
        departments = []
        for row in range(self.dept_table.rowCount()):
            name_item = self.dept_table.item(row, 0)
            color_item = self.dept_table.item(row, 1)
            tasks_item = self.dept_table.item(row, 2)
            
            if name_item and color_item and tasks_item:
                dept_name = name_item.text().strip()
                dept_color = color_item.text().strip()
                dept_tasks = [t.strip() for t in tasks_item.text().split(",") if t.strip()]
                
                if dept_name:
                    departments.append({
                        "name": dept_name,
                        "color": dept_color,
                        "tasks": dept_tasks
                    })
        
        return {
            "name": name,
            "path": Path(path),
            "description": description,
            "fps": self.fps_spin.value(),
            "width": width,
            "height": height,
            "departments": departments
        }


class RecentProjectsDialog(QDialog):
    """Dialog for selecting from recent projects"""
    
    project_selected = pyqtSignal(str)  # Emits project path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recent Projects")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
        self.load_recent_projects()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Select a Recent Project")
        header_label.setProperty("class", "title")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)
        
        # Projects list
        self.projects_list = QListWidget()
        self.projects_list.setAlternatingRowColors(True)
        self.projects_list.itemDoubleClicked.connect(self.on_project_double_clicked)
        layout.addWidget(self.projects_list)
        
        # Project info
        info_group = QGroupBox("Project Information")
        info_layout = QFormLayout(info_group)
        
        self.name_label = QLabel("-")
        self.path_label = QLabel("-")
        self.date_label = QLabel("-")
        self.description_label = QLabel("-")
        
        info_layout.addRow("Name:", self.name_label)
        info_layout.addRow("Path:", self.path_label)
        info_layout.addRow("Last Opened:", self.date_label)
        info_layout.addRow("Description:", self.description_label)
        
        layout.addWidget(info_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.open_btn = QPushButton("Open Project")
        self.open_btn.setProperty("class", "primary")
        self.open_btn.clicked.connect(self.open_selected_project)
        self.open_btn.setEnabled(False)
        
        self.browse_btn = QPushButton("Browse for Project...")
        self.browse_btn.clicked.connect(self.browse_project)
        
        self.remove_btn = QPushButton("Remove from Recent")
        self.remove_btn.clicked.connect(self.remove_selected_project)
        self.remove_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.open_btn)
        button_layout.addWidget(self.browse_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.remove_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Connect selection change
        self.projects_list.itemSelectionChanged.connect(self.on_selection_changed)
        
    def load_recent_projects(self):
        """Load recent projects from settings"""
        self.projects_list.clear()
        recent_projects = settings.get_recent_projects()
        
        for project_data in recent_projects:
            item = QListWidgetItem()
            item.setText(f"{project_data['name']} ({project_data['path']})")
            item.setData(Qt.ItemDataRole.UserRole, project_data)
            self.projects_list.addItem(item)
            
    def on_selection_changed(self):
        """Handle project selection change"""
        current_item = self.projects_list.currentItem()
        
        if current_item:
            project_data = current_item.data(Qt.ItemDataRole.UserRole)
            
            self.name_label.setText(project_data.get('name', '-'))
            self.path_label.setText(str(project_data.get('path', '-')))
            self.date_label.setText(project_data.get('last_opened', '-'))
            self.description_label.setText(project_data.get('description', '-'))
            
            self.open_btn.setEnabled(True)
            self.remove_btn.setEnabled(True)
        else:
            self.name_label.setText("-")
            self.path_label.setText("-")
            self.date_label.setText("-")
            self.description_label.setText("-")
            
            self.open_btn.setEnabled(False)
            self.remove_btn.setEnabled(False)
            
    def on_project_double_clicked(self, item):
        """Handle project double-click"""
        self.open_selected_project()
        
    def open_selected_project(self):
        """Open the selected project"""
        current_item = self.projects_list.currentItem()
        if current_item:
            project_data = current_item.data(Qt.ItemDataRole.UserRole)
            project_path = str(project_data.get('path', ''))
            if project_path and Path(project_path).exists():
                self.project_selected.emit(project_path)
                self.accept()
            else:
                QMessageBox.warning(self, "Project Not Found", 
                                  f"Project path does not exist: {project_path}")
                
    def browse_project(self):
        """Browse for a project"""
        project_path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if project_path:
            # Check if it's a valid project
            pipeline_file = Path(project_path) / "00_Pipeline" / "pipeline.json"
            if pipeline_file.exists():
                self.project_selected.emit(project_path)
                self.accept()
            else:
                QMessageBox.warning(self, "Invalid Project", 
                                  "Selected directory is not a valid Vogue project.")
                
    def remove_selected_project(self):
        """Remove selected project from recent list"""
        current_item = self.projects_list.currentItem()
        if current_item:
            project_data = current_item.data(Qt.ItemDataRole.UserRole)
            settings.remove_recent_project(project_data['name'], project_data['path'])
            self.load_recent_projects()


class AssetDialog(QDialog):
    """Dialog for creating/editing assets"""
    
    def __init__(self, parent=None, asset=None):
        super().__init__(parent)
        self.asset = asset
        self.setWindowTitle("Edit Asset" if asset else "Create New Asset")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
        
        if asset:
            self.populate_from_asset()
            
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Asset info
        info_group = QGroupBox("Asset Information")
        info_layout = QFormLayout(info_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter asset name...")
        info_layout.addRow("Name:", self.name_edit)
        
        # Folder selection
        self.folder_combo = QComboBox()
        self.folder_combo.setEditable(False)
        self.populate_folders()
        info_layout.addRow("Folder:", self.folder_combo)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Asset description (optional)...")
        info_layout.addRow("Description:", self.description_edit)
        
        layout.addWidget(info_group)
        
        # Asset settings
        settings_group = QGroupBox("Asset Settings")
        settings_layout = QFormLayout(settings_group)
        
        self.lod_combo = QComboBox()
        self.lod_combo.addItems(["High", "Medium", "Low", "All"])
        settings_layout.addRow("LOD Level:", self.lod_combo)
        
        self.rigged_check = QCheckBox("Rigged")
        settings_layout.addRow("", self.rigged_check)
        
        self.animated_check = QCheckBox("Animated")
        settings_layout.addRow("", self.animated_check)
        
        layout.addWidget(settings_group)
        
        # Meta data
        meta_group = QGroupBox("Meta Data")
        meta_layout = QFormLayout(meta_group)
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Enter tags separated by commas...")
        meta_layout.addRow("Tags:", self.tags_edit)
        
        self.artist_edit = QLineEdit()
        self.artist_edit.setPlaceholderText("Asset artist...")
        meta_layout.addRow("Artist:", self.artist_edit)
        
        layout.addWidget(meta_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def populate_folders(self):
        """Populate the folder dropdown with available folders"""
        # Get the current project from the parent controller
        if hasattr(self.parent(), 'manager') and self.parent().manager.current_project:
            project = self.parent().manager.current_project
            
            # Get asset folders
            asset_folders = [f for f in project.folders if f.type == "asset"]
            
            # Add folders to combo box
            self.folder_combo.clear()
            
            # Always add "Main" as the first option
            self.folder_combo.addItem("Main")
            
            # Add other folders
            for folder in asset_folders:
                self.folder_combo.addItem(folder.name)
            
            # Set "Main" as default selection (index 0)
            self.folder_combo.setCurrentIndex(0)
        else:
            # No project loaded, just add Main
            self.folder_combo.clear()
            self.folder_combo.addItem("Main")
            self.folder_combo.setCurrentIndex(0)
    
    def populate_from_asset(self):
        """Populate dialog from existing asset"""
        if not self.asset:
            return
            
        self.name_edit.setText(self.asset.name)
        self.description_edit.setPlainText(self.asset.description or "")
        self.tags_edit.setText(", ".join(self.asset.meta.get("tags", [])))
        self.artist_edit.setText(self.asset.meta.get("artist", ""))
        
        # Set folder if asset is in a folder
        if hasattr(self.parent(), 'manager') and self.parent().manager.current_project:
            project = self.parent().manager.current_project
            for folder in project.folders:
                if folder.type == "asset" and self.asset.name in folder.assets:
                    folder_index = self.folder_combo.findText(folder.name)
                    if folder_index >= 0:
                        self.folder_combo.setCurrentIndex(folder_index)
                    break
        
    def get_asset_data(self):
        """Get asset data from dialog"""
        name = self.name_edit.text().strip()
        folder_name = self.folder_combo.currentText().strip()
        description = self.description_edit.toPlainText().strip()
        tags = [t.strip() for t in self.tags_edit.text().split(",") if t.strip()]
        artist = self.artist_edit.text().strip()
        
        if not name:
            return None
            
        meta = {
            "tags": tags,
            "artist": artist,
            "lod": self.lod_combo.currentText(),
            "rigged": self.rigged_check.isChecked(),
            "animated": self.animated_check.isChecked()
        }
        
        return {
            "name": name,
            "folder": folder_name,
            "description": description,
            "meta": meta
        }


class ShotDialog(QDialog):
    """Dialog for creating/editing shots"""
    
    def __init__(self, parent=None, shot=None):
        super().__init__(parent)
        self.shot = shot
        self.setWindowTitle("Edit Shot" if shot else "Create New Shot")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
        
        if shot:
            self.populate_from_shot()
            
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Shot info
        info_group = QGroupBox("Shot Information")
        info_layout = QFormLayout(info_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter shot name (e.g., 0010)...")
        info_layout.addRow("Shot Name:", self.name_edit)
        
        self.sequence_edit = QLineEdit()
        self.sequence_edit.setPlaceholderText("Enter sequence name (e.g., SEQ001)...")
        info_layout.addRow("Sequence:", self.sequence_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Shot description (optional)...")
        info_layout.addRow("Description:", self.description_edit)
        
        layout.addWidget(info_group)
        
        # Shot settings
        settings_group = QGroupBox("Shot Settings")
        settings_layout = QFormLayout(settings_group)
        
        self.start_frame_spin = QSpinBox()
        self.start_frame_spin.setRange(1, 999999)
        self.start_frame_spin.setValue(1001)
        settings_layout.addRow("Start Frame:", self.start_frame_spin)
        
        self.end_frame_spin = QSpinBox()
        self.end_frame_spin.setRange(1, 999999)
        self.end_frame_spin.setValue(1100)
        settings_layout.addRow("End Frame:", self.end_frame_spin)
        
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(12, 120)
        self.fps_spin.setValue(24)
        settings_layout.addRow("Frame Rate:", self.fps_spin)
        
        layout.addWidget(settings_group)
        
        # Meta data
        meta_group = QGroupBox("Meta Data")
        meta_layout = QFormLayout(meta_group)
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Enter tags separated by commas...")
        meta_layout.addRow("Tags:", self.tags_edit)
        
        self.director_edit = QLineEdit()
        self.director_edit.setPlaceholderText("Shot director...")
        meta_layout.addRow("Director:", self.director_edit)
        
        layout.addWidget(meta_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def populate_from_shot(self):
        """Populate dialog from existing shot"""
        if not self.shot:
            return
            
        self.name_edit.setText(self.shot.name)
        self.sequence_edit.setText(self.shot.sequence)
        self.description_edit.setPlainText(self.shot.description or "")
        self.tags_edit.setText(", ".join(self.shot.meta.get("tags", [])))
        self.director_edit.setText(self.shot.meta.get("director", ""))
        
    def get_shot_data(self):
        """Get shot data from dialog"""
        name = self.name_edit.text().strip()
        sequence = self.sequence_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        tags = [t.strip() for t in self.tags_edit.text().split(",") if t.strip()]
        director = self.director_edit.text().strip()
        
        if not name or not sequence:
            return None
            
        meta = {
            "tags": tags,
            "director": director,
            "start_frame": self.start_frame_spin.value(),
            "end_frame": self.end_frame_spin.value(),
            "fps": self.fps_spin.value()
        }
        
        return {
            "name": name,
            "sequence": sequence,
            "description": description,
            "meta": meta
        }


class PublishDialog(QDialog):
    """Dialog for publishing versions"""
    
    def __init__(self, parent=None, entity=None, entity_type=None):
        super().__init__(parent)
        self.entity = entity
        self.entity_type = entity_type
        self.setWindowTitle(f"Publish {entity_type}")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Entity info
        info_group = QGroupBox("Entity Information")
        info_layout = QFormLayout(info_group)
        
        self.entity_name_label = QLabel(self.entity.name if self.entity else "-")
        self.entity_type_label = QLabel(self.entity_type or "-")
        
        info_layout.addRow("Entity:", self.entity_name_label)
        info_layout.addRow("Type:", self.entity_type_label)
        
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
        self.comment_text.setPlaceholderText("Describe what was changed in this version...")
        comment_layout.addWidget(self.comment_text)
        options_layout.addLayout(comment_layout)
        
        # Options
        self.create_thumbnail_cb = QCheckBox("Create Thumbnail")
        self.create_thumbnail_cb.setChecked(True)
        options_layout.addWidget(self.create_thumbnail_cb)
        
        self.open_after_publish_cb = QCheckBox("Open after Publish")
        self.open_after_publish_cb.setChecked(False)
        options_layout.addWidget(self.open_after_publish_cb)
        
        self.auto_increment_cb = QCheckBox("Auto-increment version number")
        self.auto_increment_cb.setChecked(True)
        options_layout.addWidget(self.auto_increment_cb)
        
        layout.addWidget(options_group)
        
        # File selection
        file_group = QGroupBox("Files to Publish")
        file_layout = QVBoxLayout(file_group)
        
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(150)
        file_layout.addWidget(self.file_list)
        
        file_btn_layout = QHBoxLayout()
        self.add_file_btn = QPushButton("Add File...")
        self.add_file_btn.clicked.connect(self.add_file)
        self.remove_file_btn = QPushButton("Remove File")
        self.remove_file_btn.clicked.connect(self.remove_file)
        file_btn_layout.addWidget(self.add_file_btn)
        file_btn_layout.addWidget(self.remove_file_btn)
        file_btn_layout.addStretch()
        file_layout.addLayout(file_btn_layout)
        
        layout.addWidget(file_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def add_file(self):
        """Add file to publish list"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Publish", "", "All Files (*)"
        )
        if file_path:
            item = QListWidgetItem(file_path)
            self.file_list.addItem(item)
            
    def remove_file(self):
        """Remove selected file from list"""
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            self.file_list.takeItem(current_row)
            
    def get_publish_data(self):
        """Get publish data from dialog"""
        return {
            "version": self.version_spin.value(),
            "comment": self.comment_text.toPlainText().strip(),
            "create_thumbnail": self.create_thumbnail_cb.isChecked(),
            "open_after_publish": self.open_after_publish_cb.isChecked(),
            "auto_increment": self.auto_increment_cb.isChecked(),
            "files": [self.file_list.item(i).text() for i in range(self.file_list.count())]
        }


class ImagePreviewDialog(QDialog):
    """Dialog for previewing images and thumbnails"""
    
    def __init__(self, parent=None, image_path=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setWindowTitle("Image Preview")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
        
        if image_path:
            self.load_image(image_path)
            
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(f"QLabel {{ border: 1px solid {COLORS['border']}; background-color: {COLORS['bg']}; }}")
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Image info
        info_group = QGroupBox("Image Information")
        info_layout = QFormLayout(info_group)
        
        self.path_label = QLabel("-")
        self.size_label = QLabel("-")
        self.format_label = QLabel("-")
        
        info_layout.addRow("Path:", self.path_label)
        info_layout.addRow("Size:", self.size_label)
        info_layout.addRow("Format:", self.format_label)
        
        layout.addWidget(info_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.open_btn = QPushButton("Open in External Viewer")
        self.open_btn.clicked.connect(self.open_external)
        
        self.copy_btn = QPushButton("Copy Path")
        self.copy_btn.clicked.connect(self.copy_path)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.open_btn)
        button_layout.addWidget(self.copy_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
    def load_image(self, image_path):
        """Load and display image"""
        if not Path(image_path).exists():
            return
            
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return
            
        # Scale image to fit dialog
        scaled_pixmap = pixmap.scaled(
            self.size() * 0.8, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        
        # Update info
        self.path_label.setText(str(image_path))
        self.size_label.setText(f"{pixmap.width()} x {pixmap.height()}")
        self.format_label.setText(Path(image_path).suffix.upper())
        
    def open_external(self):
        """Open image in external viewer"""
        if self.image_path and Path(self.image_path).exists():
            os.startfile(str(self.image_path))
            
    def copy_path(self):
        """Copy image path to clipboard"""
        if self.image_path:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(str(self.image_path))


class SettingsDialog(QDialog):
    """Dialog for application settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        self.auto_save_cb = QCheckBox("Enable auto-save")
        general_layout.addRow("Auto-save:", self.auto_save_cb)
        
        self.auto_save_interval_spin = QSpinBox()
        self.auto_save_interval_spin.setRange(1, 60)
        self.auto_save_interval_spin.setValue(5)
        self.auto_save_interval_spin.setSuffix(" minutes")
        general_layout.addRow("Auto-save interval:", self.auto_save_interval_spin)
        
        self.startup_project_cb = QCheckBox("Load last project on startup")
        general_layout.addRow("Startup:", self.startup_project_cb)
        
        tab_widget.addTab(general_tab, "General")
        
        # Projects tab
        projects_tab = QWidget()
        projects_layout = QVBoxLayout(projects_tab)
        
        # Recent projects
        recent_group = QGroupBox("Recent Projects")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_projects_list = QListWidget()
        self.recent_projects_list.setMaximumHeight(150)
        recent_layout.addWidget(self.recent_projects_list)
        
        recent_btn_layout = QHBoxLayout()
        self.clear_recent_btn = QPushButton("Clear Recent Projects")
        self.clear_recent_btn.clicked.connect(self.clear_recent_projects)
        recent_btn_layout.addWidget(self.clear_recent_btn)
        recent_btn_layout.addStretch()
        recent_layout.addLayout(recent_btn_layout)
        
        projects_layout.addWidget(recent_group)
        
        tab_widget.addTab(projects_tab, "Projects")
        
        # Appearance tab
        appearance_tab = QWidget()
        appearance_layout = QFormLayout(appearance_tab)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Auto"])
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        appearance_layout.addRow("Font Size:", self.font_size_spin)
        
        tab_widget.addTab(appearance_tab, "Appearance")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_settings(self):
        """Load current settings"""
        # Load recent projects
        recent_projects = settings.get_recent_projects()
        self.recent_projects_list.clear()
        for project in recent_projects:
            item = QListWidgetItem(f"{project['name']} ({project['path']})")
            self.recent_projects_list.addItem(item)
            
    def clear_recent_projects(self):
        """Clear all recent projects"""
        settings.clear_recent_projects()
        self.load_settings()
        
    def get_settings(self):
        """Get settings from dialog"""
        return {
            "auto_save": self.auto_save_cb.isChecked(),
            "auto_save_interval": self.auto_save_interval_spin.value(),
            "startup_project": self.startup_project_cb.isChecked(),
            "theme": self.theme_combo.currentText(),
            "font_size": self.font_size_spin.value()
        }


class CreateTaskDialog(QDialog):
    """Dialog for creating tasks"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Task")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Task info
        info_group = QGroupBox("Task Information")
        info_layout = QFormLayout(info_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter task name...")
        info_layout.addRow("Task Name:", self.name_edit)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["WIP", "Review", "Final", "Blocked", "Complete"])
        info_layout.addRow("Status:", self.status_combo)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Task description (optional)...")
        info_layout.addRow("Description:", self.description_edit)
        
        layout.addWidget(info_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_task_data(self):
        """Get task data from dialog"""
        name = self.name_edit.text().strip()
        status = self.status_combo.currentText()
        description = self.description_edit.toPlainText().strip()
        
        if not name:
            return None
            
        return {
            "name": name,
            "status": status,
            "description": description
        }


class CreateShotDialog(QDialog):
    """Dialog for creating shots"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Shot")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Shot info
        info_group = QGroupBox("Shot Information")
        info_layout = QFormLayout(info_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter shot name (e.g., 0010)...")
        info_layout.addRow("Shot Name:", self.name_edit)
        
        self.sequence_edit = QLineEdit()
        self.sequence_edit.setPlaceholderText("Enter sequence name (e.g., SEQ001)...")
        info_layout.addRow("Sequence:", self.sequence_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Shot description (optional)...")
        info_layout.addRow("Description:", self.description_edit)
        
        layout.addWidget(info_group)
        
        # Shot settings
        settings_group = QGroupBox("Shot Settings")
        settings_layout = QFormLayout(settings_group)
        
        self.start_frame_spin = QSpinBox()
        self.start_frame_spin.setRange(1, 999999)
        self.start_frame_spin.setValue(1001)
        settings_layout.addRow("Start Frame:", self.start_frame_spin)
        
        self.end_frame_spin = QSpinBox()
        self.end_frame_spin.setRange(1, 999999)
        self.end_frame_spin.setValue(1100)
        settings_layout.addRow("End Frame:", self.end_frame_spin)
        
        layout.addWidget(settings_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_shot_data(self):
        """Get shot data from dialog"""
        name = self.name_edit.text().strip()
        sequence = self.sequence_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        
        if not name or not sequence:
            return None
            
        meta = {
            "start_frame": self.start_frame_spin.value(),
            "end_frame": self.end_frame_spin.value()
        }
        
        return {
            "name": name,
            "sequence": sequence,
            "description": description,
            "meta": meta
        }
