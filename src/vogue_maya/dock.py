"""
Dockable widget for Maya integration

Creates a dockable Vogue Manager widget inside Maya.
"""

import os
from pathlib import Path
from typing import Optional

try:
    from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
    from PySide2.QtCore import Qt, Signal
    PYSIDE2_AVAILABLE = True
except ImportError:
    try:
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
        from PyQt5.QtCore import Qt, pyqtSignal as Signal
        PYSIDE2_AVAILABLE = True
    except ImportError:
        PYSIDE2_AVAILABLE = False

from ..vogue_core.logging_utils import get_logger
from .maya_bridge import maya_main_window, create_dock_widget, delete_dock_widget


class VogueMayaWidget(QWidget):
    """Dockable widget for Maya that hosts Vogue Manager functionality"""
    
    # Signals
    project_loaded = Signal(str)  # Emitted when a project is loaded
    version_opened = Signal(str)  # Emitted when a version is opened
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("VogueMayaWidget")
        self.dock_control = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the widget UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Vogue Manager")
        title_label.setProperty("class", "title")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Project info
        self.project_label = QLabel("No project loaded")
        self.project_label.setProperty("class", "muted")
        self.project_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.project_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.browse_button = QPushButton("Browse Project")
        self.browse_button.clicked.connect(self.browse_project)
        button_layout.addWidget(self.browse_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_project)
        button_layout.addWidget(self.refresh_button)
        
        layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setProperty("class", "muted")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Add stretch to push everything to top
        layout.addStretch()
    
    def browse_project(self):
        """Browse for a project to load"""
        from PySide2.QtWidgets import QFileDialog, QMessageBox
        
        project_dir = QFileDialog.getExistingDirectory(
            self, "Select Project Directory"
        )
        
        if project_dir:
            self.load_project(project_dir)
    
    def load_project(self, project_path: str):
        """Load a project"""
        try:
            # Import here to avoid circular imports
            from ..vogue_core.manager import ProjectManager
            from ..vogue_core.settings import settings
            
            manager = ProjectManager()
            project = manager.load_project(project_path)
            
            # Add to recent projects
            settings.add_recent_project(project.name, project.path)
            
            # Update UI
            self.project_label.setText(f"Project: {project.name}")
            self.status_label.setText("Project loaded")
            
            # Emit signal
            self.project_loaded.emit(project_path)
            
            self.logger.info(f"Loaded project in Maya: {project.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to load project: {e}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def refresh_project(self):
        """Refresh the current project"""
        self.status_label.setText("Refreshing...")
        # TODO: Implement refresh functionality
        self.status_label.setText("Refreshed")
    
    def open_version(self, file_path: str):
        """Open a version file in Maya"""
        try:
            from .maya_bridge import open_scene
            
            if open_scene(file_path):
                self.version_opened.emit(file_path)
                self.status_label.setText(f"Opened: {os.path.basename(file_path)}")
                self.logger.info(f"Opened version in Maya: {file_path}")
            else:
                self.status_label.setText("Failed to open file")
                
        except Exception as e:
            self.logger.error(f"Failed to open version: {e}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def dock_in_maya(self, title: str = "Vogue Manager") -> bool:
        """Dock this widget in Maya"""
        try:
            self.dock_control = create_dock_widget(self.__class__, title)
            if self.dock_control:
                self.logger.info(f"Docked widget in Maya: {title}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to dock widget in Maya: {e}")
            return False
    
    def undock_from_maya(self) -> bool:
        """Undock this widget from Maya"""
        if self.dock_control:
            try:
                success = delete_dock_widget(self.dock_control)
                if success:
                    self.dock_control = None
                    self.logger.info("Undocked widget from Maya")
                return success
            except Exception as e:
                self.logger.error(f"Failed to undock widget from Maya: {e}")
                return False
        return True


class VogueMayaController:
    """Controller for Maya integration that extends the desktop controller"""
    
    def __init__(self):
        self.logger = get_logger("VogueMayaController")
        self.widget = None
        self.manager = None
        
    def create_widget(self) -> VogueMayaWidget:
        """Create the Maya widget"""
        self.widget = VogueMayaWidget()
        return self.widget
    
    def show_in_maya(self, title: str = "Vogue Manager") -> bool:
        """Show the widget docked in Maya"""
        try:
            if not self.widget:
                self.widget = self.create_widget()
            
            return self.widget.dock_in_maya(title)
            
        except Exception as e:
            self.logger.error(f"Failed to show widget in Maya: {e}")
            return False
    
    def hide_from_maya(self) -> bool:
        """Hide the widget from Maya"""
        if self.widget:
            return self.widget.undock_from_maya()
        return True
