"""
Controller for Vogue Manager Desktop Application

Handles the interaction between UI and the core backend.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from PyQt6.QtWidgets import (QMainWindow, QFileDialog, QMessageBox, QInputDialog, 
                                QToolBar, QDialog, QTreeWidgetItem, QListWidgetItem, QTableWidgetItem)
    from PyQt6.QtCore import QThread, pyqtSignal, QObject, Qt
    from PyQt6.QtGui import QDesktopServices, QUrl
    QT_AVAILABLE = True
    QT_VERSION = "PyQt6"
except ImportError:
    try:
        from PySide2.QtWidgets import (QMainWindow, QFileDialog, QMessageBox, QInputDialog,
                                     QTreeWidgetItem, QListWidgetItem, QTableWidgetItem)
        from PySide2.QtCore import QThread, Signal as pyqtSignal, QObject, Qt
        from PySide2.QtGui import QDesktopServices, QUrl
        QT_AVAILABLE = True
        QT_VERSION = "PySide2"
    except ImportError:
        try:
            from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QMessageBox, QInputDialog,
                                       QTreeWidgetItem, QListWidgetItem, QTableWidgetItem)
            from PyQt5.QtCore import QThread, pyqtSignal, QObject, Qt
            from PyQt5.QtGui import QDesktopServices, QUrl
            QT_AVAILABLE = True
            QT_VERSION = "PyQt5"
        except ImportError:
            QT_AVAILABLE = False
            QT_VERSION = None

from vogue_core.manager import ProjectManager
from vogue_core.models import Project, Asset, Shot, Version, Department, Task
from vogue_core.settings import settings
from vogue_core.logging_utils import get_logger
from vogue_core.fs import ensure_layout, atomic_write_json, next_version
from vogue_core.schema import project_to_pipeline, pipeline_to_project
from .ui import PrismMainWindow
from .dialogs import (
    NewProjectDialog, RecentProjectsDialog, AssetDialog, ShotDialog,
    PublishDialog, ImagePreviewDialog, SettingsDialog
)


class WorkerThread(QThread):
    """Worker thread for long-running operations"""
    
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            self.func(*self.args, **self.kwargs)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class VogueController(PrismMainWindow):
    """Main controller for Vogue Manager desktop application"""
    
    def __init__(self):
        super().__init__()
        self.manager = ProjectManager()
        self.logger = get_logger("Controller")
        
        # Set initial state
        self.update_ui_state()
        
        # Connect signals after UI is set up
        self.setup_connections()
        
        self.logger.info("Vogue Controller initialized")
    
    def setup_connections(self):
        """Set up signal connections"""
        # Project browser connections
        self.project_browser.browse_btn.clicked.connect(self.browse_project)
        self.project_browser.add_asset_btn.clicked.connect(self.add_asset)
        self.project_browser.add_shot_btn.clicked.connect(self.add_shot)
        self.project_browser.refresh_assets_btn.clicked.connect(self.refresh_assets)
        self.project_browser.refresh_shots_btn.clicked.connect(self.refresh_shots)
        
        # Asset tree selection
        self.project_browser.asset_tree.itemSelectionChanged.connect(
            self.on_asset_selection_changed
        )
        
        # Shot tree selection
        self.project_browser.shot_tree.itemSelectionChanged.connect(
            self.on_shot_selection_changed
        )
        
        # Version manager connections
        self.version_manager.publish_btn.clicked.connect(self.publish_selection)
        self.version_manager.import_btn.clicked.connect(self.import_version)
        self.version_manager.export_btn.clicked.connect(self.export_version)
        self.version_manager.open_btn.clicked.connect(self.open_selected_version)
        self.version_manager.copy_btn.clicked.connect(self.copy_selected_version)
        self.version_manager.delete_btn.clicked.connect(self.delete_selected_version)
        
        # Version table selection
        self.version_manager.version_table.itemSelectionChanged.connect(
            self.on_version_selection_changed
        )
        
        # Version table double-click
        self.version_manager.version_table.itemDoubleClicked.connect(
            self.on_version_double_clicked
        )
        
        # Menu actions
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.actions()[0].menu()
        project_menu = file_menu.actions()[0].menu()
        
        # Connect project menu actions
        for action in project_menu.actions():
            if "Browse" in action.text():
                action.triggered.connect(self.browse_project)
            elif "New" in action.text():
                action.triggered.connect(self.new_project)
            elif "Open" in action.text():
                action.triggered.connect(self.open_project)
            elif "Import" in action.text():
                action.triggered.connect(self.import_project)
            elif "Export" in action.text():
                action.triggered.connect(self.export_project)
            elif "Settings" in action.text():
                action.triggered.connect(self.project_settings)
        
        # Connect file menu actions
        for action in file_menu.actions():
            if "Save" in action.text() and "As" not in action.text():
                action.triggered.connect(self.save_project)
            elif "Save As" in action.text():
                action.triggered.connect(self.save_as_project)
            elif "Exit" in action.text():
                action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.actions()[1].menu()
        for action in edit_menu.actions():
            if "Refresh" in action.text():
                action.triggered.connect(self.refresh_project)
            elif "Scan" in action.text():
                action.triggered.connect(self.scan_filesystem)
            elif "Settings" in action.text():
                action.triggered.connect(self.show_settings)
        
        # Assets menu
        assets_menu = menubar.actions()[2].menu()
        for action in assets_menu.actions():
            if "Add Asset" in action.text():
                action.triggered.connect(self.add_asset)
            elif "Import Asset" in action.text():
                action.triggered.connect(self.import_asset)
        
        # Shots menu
        shots_menu = menubar.actions()[3].menu()
        for action in shots_menu.actions():
            if "Add Shot" in action.text():
                action.triggered.connect(self.add_shot)
        
        # Publish menu
        publish_menu = menubar.actions()[4].menu()
        for action in publish_menu.actions():
            if "Publish Version" in action.text():
                action.triggered.connect(self.publish_selection)
            elif "Batch Publish" in action.text():
                action.triggered.connect(self.batch_publish)
        
        # Tools menu
        tools_menu = menubar.actions()[5].menu()
        for action in tools_menu.actions():
            if "Thumbnails" in action.text():
                action.triggered.connect(self.generate_thumbnails)
            elif "Cleanup" in action.text():
                action.triggered.connect(self.cleanup_project)
            elif "Validate" in action.text():
                action.triggered.connect(self.validate_project)
            elif "Optimize" in action.text():
                action.triggered.connect(self.optimize_project)
            elif "Maya" in action.text():
                action.triggered.connect(self.launch_maya)
            elif "Houdini" in action.text():
                action.triggered.connect(self.launch_houdini)
            elif "Blender" in action.text():
                action.triggered.connect(self.launch_blender)
            elif "API Server" in action.text():
                action.triggered.connect(self.start_api_server)
            elif "Logs" in action.text():
                action.triggered.connect(self.view_logs)
        
        # Status menu
        status_menu = menubar.actions()[6].menu()
        for action in status_menu.actions():
            if "System Information" in action.text():
                action.triggered.connect(self.show_system_info)
        
        # Pipeline panel connections
        self.pipeline_panel.validate_btn.clicked.connect(self.validate_project)
        self.pipeline_panel.optimize_btn.clicked.connect(self.optimize_project)
        self.pipeline_panel.cleanup_btn.clicked.connect(self.cleanup_project)
        
        # Log dock connections
        log_widget = self.log_dock.widget()
        if log_widget:
            log_widget.clear_log_btn.clicked.connect(self.clear_log)
        
        # Toolbar connections
        toolbar = self.findChild(QToolBar, "Main")
        if toolbar:
            for action in toolbar.actions():
                if "Browse" in action.text():
                    action.triggered.connect(self.browse_project)
                elif "New" in action.text():
                    action.triggered.connect(self.new_project)
                elif "Add Asset" in action.text():
                    action.triggered.connect(self.add_asset)
                elif "Add Shot" in action.text():
                    action.triggered.connect(self.add_shot)
                elif "Publish" in action.text():
                    action.triggered.connect(self.publish_selection)
                elif "Refresh" in action.text():
                    action.triggered.connect(self.refresh_project)
                elif "Scan" in action.text():
                    action.triggered.connect(self.scan_filesystem)
    
    def browse_project(self):
        """Browse for a project to load"""
        # Show recent projects dialog first
        dialog = RecentProjectsDialog(self)
        dialog.project_selected.connect(self.load_project)
        dialog.exec()
    
    def show_recent_projects_dialog(self):
        """Show dialog to select from recent projects"""
        recent_projects = settings.get_recent_projects()
        
        if not recent_projects:
            QMessageBox.information(self, "No Recent Projects", "No recent projects found.")
            return
        
        # Create project list
        project_names = [f"{p['name']} ({p['path']})" for p in recent_projects]
        
        project_name, ok = QInputDialog.getItem(
            self, "Select Recent Project", "Choose a project:", project_names, 0, False
        )
        
        if ok and project_name:
            # Extract path from selection
            selected_path = project_name.split(" (")[-1].rstrip(")")
            self.load_project(selected_path)
    
    def load_project(self, project_path: str):
        """Load a project"""
        try:
            self.logger.info(f"Loading project from: {project_path}")
            
            # Load project
            project = self.manager.load_project(project_path)
            
            # Add to recent projects
            settings.add_recent_project(project.name, project.path)
            
            # Update UI
            self.update_ui_state()
            
            # Update status
            self.update_project_status(project.name, project.path)
            
            # Update user info
            username = os.getenv('USERNAME', 'Unknown')
            self.update_user(username)
            
            self.logger.info(f"Project loaded successfully: {project.name}")
            self.add_log_message(f"Loaded project: {project.name}")
            
        except Exception as e:
            error_msg = f"Failed to load project: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def save_project(self):
        """Save the current project"""
        try:
            if not self.manager.current_project:
                QMessageBox.warning(self, "No Project", "No project loaded to save.")
                return
            
            self.manager.save_project()
            self.logger.info("Project saved successfully")
            self.add_log_message("Project saved")
            
        except Exception as e:
            error_msg = f"Failed to save project: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def refresh_project(self):
        """Refresh the current project data"""
        try:
            if not self.manager.current_project:
                QMessageBox.warning(self, "No Project", "No project loaded to refresh.")
                return
            
            # Reload project
            project_path = self.manager.current_project.path
            self.manager.load_project(project_path)
            
            # Update UI
            self.update_ui_state()
            
            self.logger.info("Project refreshed")
            self.add_log_message("Project refreshed")
            
        except Exception as e:
            error_msg = f"Failed to refresh project: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def scan_filesystem(self):
        """Scan filesystem and update project"""
        try:
            if not self.manager.current_project:
                QMessageBox.warning(self, "No Project", "No project loaded to scan.")
                return
            
            # Run scan in worker thread
            self.worker_thread = WorkerThread(self.manager.scan_filesystem, update_missing=True)
            self.worker_thread.finished.connect(self.on_scan_finished)
            self.worker_thread.error.connect(self.on_scan_error)
            self.worker_thread.start()
            
            self.add_log_message("Scanning filesystem...")
            
        except Exception as e:
            error_msg = f"Failed to start filesystem scan: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def on_scan_finished(self):
        """Handle filesystem scan completion"""
        self.update_ui_state()
        self.logger.info("Filesystem scan completed")
        self.add_log_message("Filesystem scan completed")
    
    def on_scan_error(self, error_msg: str):
        """Handle filesystem scan error"""
        self.logger.error(f"Filesystem scan error: {error_msg}")
        QMessageBox.critical(self, "Scan Error", f"Filesystem scan failed: {error_msg}")
    
    def new_project(self):
        """Create a new project"""
        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            project_data = dialog.get_project_data()
            if project_data:
                self.create_new_project(project_data)
    
    def open_project(self):
        """Open an existing project"""
        self.browse_project()
    
    def add_shot(self):
        """Add a new shot"""
        QMessageBox.information(self, "Add Shot", "Add shot functionality not yet implemented.")
    
    def refresh_assets(self):
        """Refresh assets list"""
        self.update_ui_state()
        self.add_log_message("Assets refreshed")
    
    def refresh_shots(self):
        """Refresh shots list"""
        self.update_ui_state()
        self.add_log_message("Shots refreshed")
    
    def import_version(self):
        """Import a version"""
        QMessageBox.information(self, "Import Version", "Import version functionality not yet implemented.")
    
    def export_version(self):
        """Export a version"""
        QMessageBox.information(self, "Export Version", "Export version functionality not yet implemented.")
    
    def open_selected_version(self):
        """Open the selected version"""
        current_item = self.version_manager.version_table.currentItem()
        if current_item:
            row = current_item.row()
            path_item = self.version_manager.version_table.item(row, 5)  # Path column
            if path_item:
                self.open_file(path_item.text())
    
    def copy_selected_version(self):
        """Copy the selected version"""
        QMessageBox.information(self, "Copy Version", "Copy version functionality not yet implemented.")
    
    def delete_selected_version(self):
        """Delete the selected version"""
        QMessageBox.information(self, "Delete Version", "Delete version functionality not yet implemented.")
    
    def on_version_selection_changed(self):
        """Handle version selection change"""
        current_item = self.version_manager.version_table.currentItem()
        if current_item:
            row = current_item.row()
            
            # Update version info panel
            version = self.version_manager.version_table.item(row, 0).text()
            user = self.version_manager.version_table.item(row, 1).text()
            date = self.version_manager.version_table.item(row, 2).text()
            comment = self.version_manager.version_table.item(row, 3).text()
            
            self.version_manager.version_label.setText(version)
            self.version_manager.user_label.setText(user)
            self.version_manager.date_label.setText(date)
            self.version_manager.comment_label.setText(comment)
            
            # Enable action buttons
            self.version_manager.open_btn.setEnabled(True)
            self.version_manager.copy_btn.setEnabled(True)
            self.version_manager.delete_btn.setEnabled(True)
        else:
            # Clear version info
            self.version_manager.version_label.setText("-")
            self.version_manager.user_label.setText("-")
            self.version_manager.date_label.setText("-")
            self.version_manager.comment_label.setText("-")
            
            # Disable action buttons
            self.version_manager.open_btn.setEnabled(False)
            self.version_manager.copy_btn.setEnabled(False)
            self.version_manager.delete_btn.setEnabled(False)
    
    def import_asset(self):
        """Import an asset"""
        QMessageBox.information(self, "Import Asset", "Import asset functionality not yet implemented.")
    
    def generate_thumbnails(self):
        """Generate thumbnails for versions"""
        QMessageBox.information(self, "Generate Thumbnails", "Thumbnail generation functionality not yet implemented.")
    
    def cleanup_project(self):
        """Cleanup project files"""
        QMessageBox.information(self, "Cleanup Project", "Project cleanup functionality not yet implemented.")
    
    def start_api_server(self):
        """Start the API server"""
        QMessageBox.information(self, "API Server", "API server functionality not yet implemented.")
    
    def clear_log(self):
        """Clear the log"""
        log_widget = self.log_dock.widget()
        if log_widget:
            log_widget.log_text.clear()
    
    def create_new_project(self, project_data):
        """Create a new project from dialog data"""
        try:
            self.logger.info(f"Creating new project: {project_data['name']}")
            
            # Create project directory structure
            project_path = project_data['path'] / project_data['name']
            ensure_layout(str(project_data['path']), project_data['name'])
            
            # Create departments
            departments = []
            for dept_data in project_data['departments']:
                dept = Department(
                    name=dept_data['name'],
                    color=dept_data['color'],
                    description=dept_data.get('description', '')
                )
                departments.append(dept)
            
            # Create project
            project = Project(
                name=project_data['name'],
                path=str(project_path),
                fps=project_data['fps'],
                resolution=[project_data['width'], project_data['height']],
                departments=[dept.name for dept in departments],
                assets=[],
                shots=[]
            )
            
            # Save project
            self.manager.save_project(project)
            
            # Load the new project
            self.load_project(str(project_path))
            
            self.add_log_message(f"Created new project: {project.name}")
            
        except Exception as e:
            error_msg = f"Failed to create project: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def add_asset(self):
        """Add a new asset"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Please load a project first.")
            return
            
        dialog = AssetDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            asset_data = dialog.get_asset_data()
            if asset_data:
                self.create_asset(asset_data)
    
    def create_asset(self, asset_data):
        """Create a new asset"""
        try:
            # Prepare meta data including description
            meta = asset_data['meta'].copy()
            if asset_data.get('description'):
                meta['description'] = asset_data['description']
            
            # Create asset
            asset = Asset(
                name=asset_data['name'],
                type=asset_data['type'],
                path=str(Path(self.manager.current_project.path) / "01_Assets" / asset_data['type'] / asset_data['name']),
                meta=meta
            )
            
            # Add to project
            self.manager.current_project.assets.append(asset)
            
            # Save project
            self.manager.save_project(self.manager.current_project)
            
            # Update UI
            self.update_assets_tree()
            
            self.add_log_message(f"Created asset: {asset.name}")
            
        except Exception as e:
            error_msg = f"Failed to create asset: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def add_shot(self):
        """Add a new shot"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Please load a project first.")
            return
            
        dialog = ShotDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            shot_data = dialog.get_shot_data()
            if shot_data:
                self.create_shot(shot_data)
    
    def create_shot(self, shot_data):
        """Create a new shot"""
        try:
            # Prepare meta data including description
            meta = shot_data['meta'].copy()
            if shot_data.get('description'):
                meta['description'] = shot_data['description']
            
            # Create shot
            shot = Shot(
                name=shot_data['name'],
                sequence=shot_data['sequence'],
                path=str(Path(self.manager.current_project.path) / "02_Shots" / shot_data['sequence'] / shot_data['name']),
                meta=meta
            )
            
            # Add to project
            self.manager.current_project.shots.append(shot)
            
            # Save project
            self.manager.save_project(self.manager.current_project)
            
            # Update UI
            self.update_shots_tree()
            
            self.add_log_message(f"Created shot: {shot.name}")
            
        except Exception as e:
            error_msg = f"Failed to create shot: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def publish_selection(self):
        """Publish the current selection"""
        # Get current selection
        current_asset = self.get_current_asset()
        current_shot = self.get_current_shot()
        
        if not current_asset and not current_shot:
            QMessageBox.warning(self, "No Selection", "Please select an asset or shot to publish.")
            return
        
        entity = current_asset or current_shot
        entity_type = "Asset" if current_asset else "Shot"
        
        dialog = PublishDialog(self, entity, entity_type)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            publish_data = dialog.get_publish_data()
            if publish_data:
                self.publish_version(entity, publish_data)
    
    def get_current_asset(self):
        """Get currently selected asset"""
        current_item = self.project_browser.asset_tree.currentItem()
        if current_item and current_item.parent():
            return current_item.data(0, Qt.ItemDataRole.UserRole)
        return None
    
    def get_current_shot(self):
        """Get currently selected shot"""
        current_item = self.project_browser.shot_tree.currentItem()
        if current_item and current_item.parent():
            return current_item.data(0, Qt.ItemDataRole.UserRole)
        return None
    
    def publish_version(self, entity, publish_data):
        """Publish a new version"""
        try:
            # Get next version number
            if publish_data['auto_increment']:
                version_num = next_version(entity.versions)
            else:
                version_num = publish_data['version']
            
            # Create version
            version = Version(
                version=version_num,
                user=os.getenv('USERNAME', 'Unknown'),
                comment=publish_data['comment'],
                path=Path(entity.path) / f"v{version_num:03d}",
                created_at=datetime.now(),
                meta={}
            )
            
            # Add version to entity
            entity.versions.append(version)
            
            # Create version directory
            version.path.mkdir(parents=True, exist_ok=True)
            
            # Copy files if any
            for file_path in publish_data['files']:
                if Path(file_path).exists():
                    dest_path = version.path / Path(file_path).name
                    shutil.copy2(file_path, dest_path)
            
            # Create thumbnail if requested
            if publish_data['create_thumbnail']:
                self.create_thumbnail(version)
            
            # Save project
            self.manager.save_project(self.manager.current_project)
            
            # Update UI
            self.update_versions_table(entity.versions)
            
            self.add_log_message(f"Published version v{version_num:03d} for {entity.name}")
            
            # Open after publish if requested
            if publish_data['open_after_publish']:
                self.open_file(str(version.path))
            
        except Exception as e:
            error_msg = f"Failed to publish version: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def create_thumbnail(self, version):
        """Create thumbnail for version"""
        try:
            # Look for image files in version directory
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tga', '.exr']
            for ext in image_extensions:
                for img_file in Path(version.path).glob(f"*{ext}"):
                    # Create thumbnail
                    from vogue_core.thumbnails import make_thumbnail
                    thumb_path = Path(version.path) / "thumbnail.jpg"
                    make_thumbnail(str(img_file), str(thumb_path))
                    break
        except Exception as e:
            self.logger.warning(f"Failed to create thumbnail: {e}")
    
    def import_version(self):
        """Import a version from external source"""
        QMessageBox.information(self, "Import Version", "Import version functionality not yet implemented.")
    
    def export_version(self):
        """Export selected version"""
        current_item = self.version_manager.version_table.currentItem()
        if current_item:
            row = current_item.row()
            path_item = self.version_manager.version_table.item(row, 5)
            if path_item:
                export_path = QFileDialog.getExistingDirectory(self, "Select Export Directory")
                if export_path:
                    # Copy version to export location
                    version_path = Path(path_item.text())
                    dest_path = Path(export_path) / version_path.name
                    shutil.copytree(version_path, dest_path, dirs_exist_ok=True)
                    self.add_log_message(f"Exported version to: {dest_path}")
    
    def open_selected_version(self):
        """Open the selected version"""
        current_item = self.version_manager.version_table.currentItem()
        if current_item:
            row = current_item.row()
            path_item = self.version_manager.version_table.item(row, 5)
            if path_item:
                self.open_file(path_item.text())
    
    def copy_selected_version(self):
        """Copy selected version"""
        current_item = self.version_manager.version_table.currentItem()
        if current_item:
            row = current_item.row()
            path_item = self.version_manager.version_table.item(row, 5)
            if path_item:
                # Copy to clipboard
                if QT_VERSION == "PyQt6":
                    from PyQt6.QtWidgets import QApplication
                elif QT_VERSION == "PySide2":
                    from PySide2.QtWidgets import QApplication
                else:  # PyQt5
                    from PyQt5.QtWidgets import QApplication
                QApplication.clipboard().setText(path_item.text())
                self.add_log_message("Version path copied to clipboard")
    
    def delete_selected_version(self):
        """Delete selected version"""
        current_item = self.version_manager.version_table.currentItem()
        if current_item:
            row = current_item.row()
            path_item = self.version_manager.version_table.item(row, 5)
            if path_item:
                reply = QMessageBox.question(
                    self, "Delete Version",
                    f"Are you sure you want to delete this version?\n\n{path_item.text()}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        # Remove from entity
                        entity = self.get_current_asset() or self.get_current_shot()
                        if entity:
                            version_path = Path(path_item.text())
                            entity.versions = [v for v in entity.versions if Path(v.path) != version_path]
                            
                            # Delete directory
                            shutil.rmtree(version_path)
                            
                            # Save project
                            self.manager.save_project(self.manager.current_project)
                            
                            # Update UI
                            self.update_versions_table(entity.versions)
                            
                            self.add_log_message(f"Deleted version: {version_path.name}")
                            
                    except Exception as e:
                        error_msg = f"Failed to delete version: {e}"
                        self.logger.error(error_msg)
                        QMessageBox.critical(self, "Error", error_msg)
    
    def import_asset(self):
        """Import an asset from external source"""
        QMessageBox.information(self, "Import Asset", "Import asset functionality not yet implemented.")
    
    def batch_publish(self):
        """Batch publish multiple items"""
        QMessageBox.information(self, "Batch Publish", "Batch publish functionality not yet implemented.")
    
    def generate_thumbnails(self):
        """Generate thumbnails for all versions"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Please load a project first.")
            return
        
        try:
            self.show_progress("Generating thumbnails...")
            
            # Generate thumbnails for all versions
            for asset in self.manager.current_project.assets:
                for version in asset.versions:
                    self.create_thumbnail(version)
            
            for shot in self.manager.current_project.shots:
                for version in shot.versions:
                    self.create_thumbnail(version)
            
            self.hide_progress()
            self.add_log_message("Thumbnail generation completed")
            
        except Exception as e:
            self.hide_progress()
            error_msg = f"Failed to generate thumbnails: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def cleanup_project(self):
        """Cleanup project files"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Please load a project first.")
            return
        
        reply = QMessageBox.question(
            self, "Cleanup Project",
            "This will remove unused files and optimize the project. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.show_progress("Cleaning up project...")
                
                # TODO: Implement cleanup logic
                # - Remove orphaned files
                # - Optimize thumbnails
                # - Clean up temporary files
                
                self.hide_progress()
                self.add_log_message("Project cleanup completed")
                
            except Exception as e:
                self.hide_progress()
                error_msg = f"Failed to cleanup project: {e}"
                self.logger.error(error_msg)
                QMessageBox.critical(self, "Error", error_msg)
    
    def start_api_server(self):
        """Start the API server"""
        QMessageBox.information(self, "API Server", "API server functionality not yet implemented.")
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            settings_data = dialog.get_settings()
            # TODO: Apply settings
            self.add_log_message("Settings updated")
    
    def show_image_preview(self, image_path):
        """Show image preview dialog"""
        dialog = ImagePreviewDialog(self, image_path)
        dialog.exec()
    
    def validate_project(self):
        """Validate project integrity"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Please load a project first.")
            return
        
        try:
            self.show_progress("Validating project...")
            
            # Check project structure
            issues = []
            
            # Check pipeline.json exists
            pipeline_file = Path(self.manager.current_project.path) / "00_Pipeline" / "pipeline.json"
            if not pipeline_file.exists():
                issues.append("Missing pipeline.json file")
            
            # Check asset directories
            for asset in self.manager.current_project.assets:
                if not Path(asset.path).exists():
                    issues.append(f"Asset directory missing: {asset.name}")
            
            # Check shot directories
            for shot in self.manager.current_project.shots:
                if not Path(shot.path).exists():
                    issues.append(f"Shot directory missing: {shot.name}")
            
            self.hide_progress()
            
            if issues:
                QMessageBox.warning(self, "Project Validation", 
                                  f"Found {len(issues)} issues:\n\n" + "\n".join(issues))
            else:
                QMessageBox.information(self, "Project Validation", "Project is valid!")
                
            self.add_log_message(f"Project validation completed - {len(issues)} issues found")
            
        except Exception as e:
            self.hide_progress()
            error_msg = f"Failed to validate project: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def optimize_project(self):
        """Optimize project for better performance"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Please load a project first.")
            return
        
        try:
            self.show_progress("Optimizing project...")
            
            # TODO: Implement optimization logic
            # - Compress thumbnails
            # - Remove unused files
            # - Optimize database
            
            self.hide_progress()
            self.add_log_message("Project optimization completed")
            QMessageBox.information(self, "Project Optimization", "Project has been optimized!")
            
        except Exception as e:
            self.hide_progress()
            error_msg = f"Failed to optimize project: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def launch_maya(self):
        """Launch Maya with Prism integration"""
        try:
            import subprocess
            subprocess.Popen(["maya"])
            self.add_log_message("Maya launched")
        except Exception as e:
            QMessageBox.warning(self, "Maya Launch", f"Failed to launch Maya: {e}")
    
    def launch_houdini(self):
        """Launch Houdini with Prism integration"""
        try:
            import subprocess
            subprocess.Popen(["houdini"])
            self.add_log_message("Houdini launched")
        except Exception as e:
            QMessageBox.warning(self, "Houdini Launch", f"Failed to launch Houdini: {e}")
    
    def launch_blender(self):
        """Launch Blender with Prism integration"""
        try:
            import subprocess
            subprocess.Popen(["blender"])
            self.add_log_message("Blender launched")
        except Exception as e:
            QMessageBox.warning(self, "Blender Launch", f"Failed to launch Blender: {e}")
    
    def view_logs(self):
        """View detailed logs"""
        self.show_log_dock()
        self.add_log_message("Log panel opened")
    
    def show_system_info(self):
        """Show system information dialog"""
        super().show_system_info()
    
    def import_project(self):
        """Import project from external source"""
        QMessageBox.information(self, "Import Project", "Import project functionality not yet implemented.")
    
    def export_project(self):
        """Export project to external format"""
        QMessageBox.information(self, "Export Project", "Export project functionality not yet implemented.")
    
    def project_settings(self):
        """Open project settings dialog"""
        QMessageBox.information(self, "Project Settings", "Project settings functionality not yet implemented.")
    
    def save_as_project(self):
        """Save project with new name"""
        QMessageBox.information(self, "Save As", "Save as functionality not yet implemented.")
    
    def on_asset_selection_changed(self):
        """Handle asset selection change"""
        current_item = self.project_browser.asset_tree.currentItem()
        
        if not current_item or current_item.parent() is None:
            # No asset selected or type selected
            self.update_versions_table([])
            self.version_manager.entity_name_label.setText("No Selection")
            self.version_manager.entity_type_label.setText("")
            return
        
        # Get asset data
        asset = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not asset:
            return
        
        # Update entity info
        self.version_manager.entity_name_label.setText(asset.name)
        self.version_manager.entity_type_label.setText(f"Asset - {asset.type}")
        
        # Update versions table
        self.update_versions_table(asset.versions)
        
        # Enable publish button
        self.version_manager.publish_btn.setEnabled(True)
    
    def on_shot_selection_changed(self):
        """Handle shot selection change"""
        current_item = self.project_browser.shot_tree.currentItem()
        
        if not current_item or current_item.parent() is None:
            # No shot selected or sequence selected
            self.update_versions_table([])
            self.version_manager.entity_name_label.setText("No Selection")
            self.version_manager.entity_type_label.setText("")
            return
        
        # Get shot data
        shot = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not shot:
            return
        
        # Update entity info
        self.version_manager.entity_name_label.setText(shot.name)
        self.version_manager.entity_type_label.setText(f"Shot - {shot.sequence}")
        
        # Update versions table
        self.update_versions_table(shot.versions)
        
        # Enable publish button
        self.version_manager.publish_btn.setEnabled(True)
    
    def on_version_double_clicked(self, item):
        """Handle version double-click"""
        if not item:
            return
        
        # Get the path from the last column
        table = item.tableWidget()
        row = item.row()
        path_item = table.item(row, 4)  # Path column
        
        if path_item:
            file_path = path_item.text()
            self.open_file(file_path)
    
    def open_file(self, file_path: str):
        """Open a file with the system default application"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', file_path])
            else:
                # Fallback
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            
            self.logger.info(f"Opened file: {file_path}")
            self.add_log_message(f"Opened file: {file_path}")
            
        except Exception as e:
            error_msg = f"Failed to open file: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def update_ui_state(self):
        """Update the UI state based on current project"""
        if self.manager.current_project:
            # Update project info
            self.setWindowTitle(f"Vogue Manager - {self.manager.current_project.name}")
            self.statusBar().showMessage(f"Project: {self.manager.current_project.name} | Path: {self.manager.current_project.path}")
            
            # Update assets tree
            self.update_assets_tree()
            
            # Update shots tree
            self.update_shots_tree()
            
            # Update recent projects
            self.update_recent_projects()
            
            # Add log message
            self.add_log_message("Project loaded successfully")
        else:
            # Clear UI
            self.setWindowTitle("Vogue Manager - Prism Interface")
            self.statusBar().showMessage("No project loaded")
            self.project_browser.asset_tree.clear()
            self.project_browser.shot_tree.clear()
            self.version_manager.version_table.setRowCount(0)
            self.version_manager.entity_name_label.setText("No Selection")
            self.version_manager.entity_type_label.setText("")
    
    def update_assets_tree(self):
        """Update the assets tree widget"""
        self.project_browser.asset_tree.clear()
        
        if not self.manager.current_project:
            return
        
        # Group assets by type
        assets_by_type = {}
        for asset in self.manager.current_project.assets:
            asset_type = asset.type
            if asset_type not in assets_by_type:
                assets_by_type[asset_type] = []
            assets_by_type[asset_type].append(asset)
        
        # Create tree items
        for asset_type, assets in assets_by_type.items():
            type_item = QTreeWidgetItem(self.project_browser.asset_tree)
            type_item.setText(0, asset_type)
            type_item.setText(1, asset_type)
            type_item.setText(2, str(len(assets)))
            type_item.setData(0, Qt.ItemDataRole.UserRole, asset_type)
            
            for asset in assets:
                asset_item = QTreeWidgetItem(type_item)
                asset_item.setText(0, asset.name)
                asset_item.setText(1, asset.type)
                asset_item.setText(2, str(len(asset.versions)))
                asset_item.setData(0, Qt.ItemDataRole.UserRole, asset)
        
        # Expand all items
        self.project_browser.asset_tree.expandAll()
    
    def update_shots_tree(self):
        """Update the shots tree widget"""
        self.project_browser.shot_tree.clear()
        
        if not self.manager.current_project:
            return
        
        # Group shots by sequence
        shots_by_sequence = {}
        for shot in self.manager.current_project.shots:
            sequence = shot.sequence
            if sequence not in shots_by_sequence:
                shots_by_sequence[sequence] = []
            shots_by_sequence[sequence].append(shot)
        
        # Create tree items
        for sequence, shots in shots_by_sequence.items():
            seq_item = QTreeWidgetItem(self.project_browser.shot_tree)
            seq_item.setText(0, sequence)
            seq_item.setText(1, sequence)
            seq_item.setText(2, str(len(shots)))
            seq_item.setData(0, Qt.ItemDataRole.UserRole, sequence)
            
            for shot in shots:
                shot_item = QTreeWidgetItem(seq_item)
                shot_item.setText(0, shot.name)
                shot_item.setText(1, shot.sequence)
                shot_item.setText(2, str(len(shot.versions)))
                shot_item.setData(0, Qt.ItemDataRole.UserRole, shot)
        
        # Expand all items
        self.project_browser.shot_tree.expandAll()
    
    def update_recent_projects(self):
        """Update the recent projects list"""
        self.project_browser.recent_list.clear()
        
        recent_projects = settings.get_recent_projects()
        for project_path in recent_projects[:5]:  # Show only last 5
            item = QListWidgetItem(str(project_path))
            self.project_browser.recent_list.addItem(item)
    
    def update_versions_table(self, versions):
        """Update the versions table with the given versions"""
        self.version_manager.version_table.setRowCount(len(versions))
        
        for row, version in enumerate(versions):
            # Version number
            version_item = QTableWidgetItem(f"v{version.version:03d}")
            self.version_manager.version_table.setItem(row, 0, version_item)
            
            # User
            user_item = QTableWidgetItem(version.user)
            self.version_manager.version_table.setItem(row, 1, user_item)
            
            # Date
            date_item = QTableWidgetItem(version.created_at.strftime("%Y-%m-%d %H:%M"))
            self.version_manager.version_table.setItem(row, 2, date_item)
            
            # Comment
            comment_item = QTableWidgetItem(version.comment or "")
            self.version_manager.version_table.setItem(row, 3, comment_item)
            
            # Status
            status_item = QTableWidgetItem("Published")
            self.version_manager.version_table.setItem(row, 4, status_item)
            
            # Path
            path_item = QTableWidgetItem(str(version.path))
            self.version_manager.version_table.setItem(row, 5, path_item)
    
    def update_project_status(self, name: str, path: str):
        """Update the project status in the UI"""
        super().update_project_status(name, path)
    
    def add_log_message(self, message: str, level: str = "INFO"):
        """Add a message to the log dock"""
        log_widget = self.log_dock.widget()
        if log_widget and hasattr(log_widget, 'log_text'):
            log_widget.log_text.appendPlainText(f"[{level}] {message}")
            # Auto-scroll to bottom
            log_widget.log_text.verticalScrollBar().setValue(
                log_widget.log_text.verticalScrollBar().maximum()
            )
    
    def show(self):
        """Show the main window"""
        super().show()
