"""
Dockable widget for Maya integration

Creates a dockable Vogue Manager widget inside Maya.
"""

import os
from pathlib import Path
from typing import Optional

try:
    from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QInputDialog, QMessageBox
    from PySide2.QtCore import Qt, Signal
    PYSIDE2_AVAILABLE = True
except ImportError:
    try:
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QInputDialog, QMessageBox
        from PyQt5.QtCore import Qt, pyqtSignal as Signal
        PYSIDE2_AVAILABLE = True
    except ImportError:
        PYSIDE2_AVAILABLE = False

from vogue_core.logging_utils import get_logger
from vogue_maya.maya_bridge import maya_main_window, create_dock_widget, delete_dock_widget


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
        title_label = QLabel("Vogue Launcher")
        title_label.setProperty("class", "title")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Project info
        self.project_label = QLabel("No project loaded")
        self.project_label.setProperty("class", "muted")
        self.project_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.project_label)
        
        # Project selection
        project_layout = QHBoxLayout()
        self.project_combo = QComboBox()
        self.project_combo.setPlaceholderText("Select Project")
        self.project_combo.currentTextChanged.connect(self.on_project_selected)
        project_layout.addWidget(self.project_combo)
        
        self.refresh_projects_button = QPushButton("↻")
        self.refresh_projects_button.setToolTip("Refresh Projects")
        self.refresh_projects_button.clicked.connect(self.refresh_projects)
        project_layout.addWidget(self.refresh_projects_button)
        
        layout.addLayout(project_layout)
        
        # Asset/Folder creation
        create_layout = QHBoxLayout()
        
        self.create_asset_button = QPushButton("New Asset")
        self.create_asset_button.clicked.connect(self.create_asset)
        create_layout.addWidget(self.create_asset_button)
        
        self.create_shot_button = QPushButton("New Shot")
        self.create_shot_button.clicked.connect(self.create_shot)
        create_layout.addWidget(self.create_shot_button)
        
        layout.addLayout(create_layout)
        
        # Product creation
        product_layout = QHBoxLayout()
        
        self.create_product_button = QPushButton("New Product")
        self.create_product_button.clicked.connect(self.create_product)
        product_layout.addWidget(self.create_product_button)
        
        self.product_type_combo = QComboBox()
        self.product_type_combo.addItems(["Model", "Rig", "Animation", "Render", "Compositing"])
        product_layout.addWidget(self.product_type_combo)
        
        layout.addLayout(product_layout)
        
        # Maya scene info
        self.scene_label = QLabel("No scene loaded")
        self.scene_label.setProperty("class", "muted")
        self.scene_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.scene_label)
        
        # Maya actions
        maya_layout = QHBoxLayout()
        
        self.save_scene_button = QPushButton("Save Scene")
        self.save_scene_button.clicked.connect(self.save_scene)
        maya_layout.addWidget(self.save_scene_button)
        
        self.playblast_button = QPushButton("Playblast")
        self.playblast_button.clicked.connect(self.create_playblast)
        maya_layout.addWidget(self.playblast_button)
        
        layout.addLayout(maya_layout)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setProperty("class", "muted")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        # Load available projects
        self.refresh_projects()
    
    def browse_project(self):
        """Browse for a project to load"""
        from PySide2.QtWidgets import QFileDialog, QMessageBox
        
        project_dir = QFileDialog.getExistingDirectory(
            self, "Select Project Directory"
        )
        
        if project_dir:
            self.load_project(project_dir)
    
    def load_project(self, project_path: str):
        """Load a project using the new Vogue backend"""
        try:
            # Import here to avoid circular imports
            from vogue_core.real_ayon_backend import get_real_ayon_backend
            
            backend = get_real_ayon_backend()
            project_name = Path(project_path).name
            
            # Load project using the new backend
            project = backend.load_project(project_name)
            
            if project:
                # Update UI
                self.project_label.setText(f"Project: {project.name}")
                self.status_label.setText("Project loaded")
                
                # Emit signal
                self.project_loaded.emit(project_path)
                
                self.logger.info(f"Loaded Vogue project in Maya: {project.name}")
            else:
                self.status_label.setText("Failed to load project")
                self.logger.error(f"Project not found: {project_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to load project: {e}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def refresh_projects(self):
        """Refresh the list of available projects"""
        try:
            from vogue_core.real_ayon_backend import get_real_ayon_backend
            
            backend = get_real_ayon_backend()
            projects = backend.get_projects()
            
            self.project_combo.clear()
            for project in projects:
                self.project_combo.addItem(project.name)
            
            self.status_label.setText(f"Found {len(projects)} projects")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh projects: {e}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def on_project_selected(self, project_name: str):
        """Handle project selection"""
        if project_name:
            self.load_project_by_name(project_name)
    
    def load_project_by_name(self, project_name: str):
        """Load a project by name"""
        try:
            from vogue_core.real_ayon_backend import get_real_ayon_backend
            
            backend = get_real_ayon_backend()
            project = backend.load_project(project_name)
            
            if project:
                self.project_label.setText(f"Project: {project.name}")
                self.status_label.setText("Project loaded")
                self.project_loaded.emit(project.name)
                self.logger.info(f"Loaded Vogue project in Maya: {project.name}")
            else:
                self.status_label.setText("Failed to load project")
                
        except Exception as e:
            self.logger.error(f"Failed to load project: {e}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def create_asset(self):
        """Create a new asset folder"""
        try:
            from vogue_core.real_ayon_backend import get_real_ayon_backend
            
            backend = get_real_ayon_backend()
            if not backend.current_project:
                QMessageBox.warning(self, "No Project", "Please select a project first")
                return
            
            name, ok = QInputDialog.getText(self, "New Asset", "Asset name:")
            if ok and name:
                folder = backend.create_folder(name, "Asset")
                self.status_label.setText(f"Created asset: {name}")
                self.logger.info(f"Created asset in Maya: {name}")
                
        except Exception as e:
            self.logger.error(f"Failed to create asset: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create asset: {str(e)}")
    
    def create_shot(self):
        """Create a new shot folder"""
        try:
            from vogue_core.real_ayon_backend import get_real_ayon_backend
            
            backend = get_real_ayon_backend()
            if not backend.current_project:
                QMessageBox.warning(self, "No Project", "Please select a project first")
                return
            
            name, ok = QInputDialog.getText(self, "New Shot", "Shot name:")
            if ok and name:
                folder = backend.create_folder(name, "Shot")
                self.status_label.setText(f"Created shot: {name}")
                self.logger.info(f"Created shot in Maya: {name}")
                
        except Exception as e:
            self.logger.error(f"Failed to create shot: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create shot: {str(e)}")
    
    def create_product(self):
        """Create a new product"""
        try:
            from vogue_core.real_ayon_backend import get_real_ayon_backend
            
            backend = get_real_ayon_backend()
            if not backend.current_project:
                QMessageBox.warning(self, "No Project", "Please select a project first")
                return
            
            name, ok = QInputDialog.getText(self, "New Product", "Product name:")
            if ok and name:
                product_type = self.product_type_combo.currentText()
                # For now, create in a default folder - in practice you'd select a folder
                folder = backend.create_folder("Default", "Asset")
                product = backend.create_product(name, product_type, folder.id)
                self.status_label.setText(f"Created product: {name} ({product_type})")
                self.logger.info(f"Created product in Maya: {name} ({product_type})")
                
        except Exception as e:
            self.logger.error(f"Failed to create product: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create product: {str(e)}")
    
    def save_scene(self):
        """Save the current Maya scene"""
        try:
            from vogue_maya.maya_bridge import save_scene, get_current_scene_path
            
            scene_path = get_current_scene_path()
            if scene_path:
                if save_scene():
                    self.scene_label.setText(f"Saved: {os.path.basename(scene_path)}")
                    self.status_label.setText("Scene saved")
                else:
                    self.status_label.setText("Failed to save scene")
            else:
                self.status_label.setText("No scene to save")
                
        except Exception as e:
            self.logger.error(f"Failed to save scene: {e}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def create_playblast(self):
        """Create a playblast of the current scene"""
        try:
            from vogue_maya.maya_bridge import create_playblast, get_current_scene_path
            from PySide2.QtWidgets import QFileDialog
            
            scene_path = get_current_scene_path()
            if not scene_path:
                QMessageBox.warning(self, "No Scene", "No scene loaded to playblast")
                return
            
            # Get output path
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Save Playblast", 
                f"{os.path.splitext(scene_path)[0]}_playblast.mov",
                "Movie files (*.mov *.mp4 *.avi)"
            )
            
            if output_path:
                if create_playblast(output_path):
                    self.status_label.setText("Playblast created")
                else:
                    self.status_label.setText("Failed to create playblast")
                
        except Exception as e:
            self.logger.error(f"Failed to create playblast: {e}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def refresh_project(self):
        """Refresh the current project"""
        self.status_label.setText("Refreshing...")
        # TODO: Implement refresh functionality
        self.status_label.setText("Refreshed")
    
    def open_version(self, file_path: str):
        """Open a version file in Maya"""
        try:
            from vogue_maya.maya_bridge import open_scene
            
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
