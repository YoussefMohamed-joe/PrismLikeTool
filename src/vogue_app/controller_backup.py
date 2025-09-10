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

# Import PyQt6 only
from PyQt6.QtWidgets import (QMainWindow, QFileDialog, QMessageBox, QInputDialog,
                            QToolBar, QDialog, QTreeWidget, QTreeWidgetItem, QListWidgetItem, QTableWidgetItem, QLineEdit, QAbstractItemView, QSizePolicy)
from PyQt6.QtCore import QThread, pyqtSignal, QObject, Qt, QUrl, QTimer
from PyQt6.QtGui import QDesktopServices, QColor, QIcon

QT_AVAILABLE = True
QT_VERSION = "PyQt6"

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
        
        # Set global controller reference for auto-save
        from vogue_app.ui import set_current_controller
        set_current_controller(self)
        
        # Connect signals after UI is set up
        self.setup_connections()
        
        # Setup asset tree context menu
        self.setup_asset_tree_context_menu()

        # Setup tree widgets FIRST (before loading project)
        QTimer.singleShot(100, self._setup_tree_widgets)

        # Auto-load last opened project AFTER tree setup
        QTimer.singleShot(200, self.auto_load_last_project)

        self.logger.info("Vogue Controller initialized")

    def _setup_tree_widgets(self):
        """Ensure tree widgets are properly configured and visible"""
        try:
            if hasattr(self, 'project_browser'):
                # Ensure no delegates are set (they're now disabled in UI setup)
                self.project_browser.asset_tree.setItemDelegate(None)
                self.project_browser.shot_tree.setItemDelegate(None)

                # Don't populate trees here - let auto_load_last_project handle it
                # This prevents conflicts between placeholder and project data
                self.logger.info("Tree widgets setup completed successfully")
        except Exception as e:
            self.logger.error(f"Failed to setup tree widgets: {e}")

    def auto_load_last_project(self):
        """Automatically load the last opened project on startup"""
        try:
            from vogue_core.settings import settings

            # Get the most recent project from settings
            recent_projects = settings.recent_projects
            if recent_projects and len(recent_projects) > 0:
                # Load the most recent project (first in the list)
                last_project = recent_projects[0]
                project_path = last_project.get('path')

                if project_path and os.path.exists(project_path):
                    self.logger.info(f"Auto-loading last project: {last_project.get('name')} from {project_path}")
                    self.load_project(project_path)
                else:
                    self.logger.info("Last project path not found or doesn't exist")
            else:
                self.logger.info("No recent projects found, starting with empty state")
        except Exception as e:
            self.logger.error(f"Failed to auto-load last project: {e}")
    
    def setup_connections(self):
        """Set up signal connections"""
        # Project browser connections
        self.project_browser.add_asset_btn.clicked.connect(self.add_asset)
        self.project_browser.add_shot_btn.clicked.connect(self.add_shot)
        self.project_browser.new_folder_btn.clicked.connect(lambda: self.project_browser.create_folder("asset"))
        self.project_browser.new_shot_folder_btn.clicked.connect(lambda: self.project_browser.create_folder("shot"))
        self.project_browser.refresh_assets_btn.clicked.connect(self.refresh_assets)
        self.project_browser.refresh_shots_btn.clicked.connect(self.refresh_shots)
        
        # Asset tree selection
        self.project_browser.asset_tree.itemSelectionChanged.connect(
            lambda: self.on_asset_selection_changed(self.project_browser.asset_tree.currentItem())
        )
        
        # Shot tree selection
        self.project_browser.shot_tree.itemSelectionChanged.connect(
            lambda: self.on_shot_selection_changed(self.project_browser.shot_tree.currentItem())
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
        
        # Connect menu actions using object names (more robust than indexing)
        self._connect_menu_actions()

        # Left panel task connections (moved from right panel)
        # Task buttons
        self.project_browser.new_task_btn.clicked.connect(self.new_task)
        self.project_browser.assign_task_btn.clicked.connect(self.assign_task)
        self.project_browser.complete_task_btn.clicked.connect(self.complete_task)

        # Department buttons (moved to left panel)
        self.project_browser.add_dept_btn.clicked.connect(self.add_department)
        self.project_browser.edit_dept_btn.clicked.connect(self.edit_department)
        self.project_browser.remove_dept_btn.clicked.connect(self.remove_department)

        # Asset info buttons
        self.right_panel.open_asset_btn.clicked.connect(self.open_selected_version)
        self.right_panel.copy_path_btn.clicked.connect(self.copy_asset_path)
        self.right_panel.show_in_explorer_btn.clicked.connect(self.show_in_explorer)
        self.right_panel.asset_properties_btn.clicked.connect(self.show_asset_properties)
        
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

        # Recent projects menu connection
        if hasattr(self, 'recent_projects_action'):
            self.recent_projects_action.triggered.connect(self.show_recent_projects_dialog)

        # Set load project callback for recent projects dialog
        self.load_project_callback = self.load_project
    
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
        
        # Create a simple list dialog
        from PyQt6.QtWidgets import QListWidget, QVBoxLayout, QDialog, QPushButton, QHBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Recent Project")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        # Create list widget
        list_widget = QListWidget()
        for project in recent_projects:
            list_widget.addItem(f"{project['name']}\n{project['path']}")

        layout.addWidget(list_widget)

        # Buttons
        button_layout = QHBoxLayout()
        open_btn = QPushButton("Open")
        open_btn.setDefault(True)
        cancel_btn = QPushButton("Cancel")

        button_layout.addStretch()
        button_layout.addWidget(open_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        # Connect buttons
        def on_open():
            current_item = list_widget.currentItem()
            if current_item:
                # Find the corresponding project
                item_text = current_item.text()
                for project in recent_projects:
                    if project['name'] in item_text and project['path'] in item_text:
                        # Always close dialog first, then load project
                        dialog.accept()  # Close dialog immediately
                        try:
                            self.load_project(project['path'])
                        except Exception as e:
                            QMessageBox.warning(None, "Load Error", f"Failed to load project: {e}")
                        return
            QMessageBox.warning(dialog, "No Selection", "Please select a project to open.")

        def on_cancel():
            dialog.reject()

        open_btn.clicked.connect(on_open)
        cancel_btn.clicked.connect(on_cancel)

        # Handle double-click on items
        def on_double_click(item):
            # Find the corresponding project
            item_text = item.text()
            for project in recent_projects:
                if project['name'] in item_text and project['path'] in item_text:
                    # Always close dialog first, then load project
                    dialog.accept()  # Close dialog immediately
                    try:
                        self.load_project(project['path'])
                    except Exception as e:
                        QMessageBox.warning(None, "Load Error", f"Failed to load project: {e}")
                    return

        list_widget.itemDoubleClicked.connect(on_double_click)

        dialog.exec()
    
    def load_project(self, project_path: str):
        """Load a project"""
        try:
            self.logger.info(f"Loading project from: {project_path}")
            
            # Load project
            project = self.manager.load_project(project_path)
            
            # Normalize project data: ensure 'Main' folder exists and assign unassigned assets
            try:
                self._normalize_project()
            except Exception as norm_err:
                self.logger.error(f"Normalization failed: {norm_err}")

            # Add to recent projects
            settings.add_recent_project(project.name, project.path)
            
            # Don't call _setup_tree_widgets here as it interferes with update_ui_state

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

    def _normalize_project(self):
        """Ensure a 'Main' asset folder exists and all assets are assigned to a folder.

        - Creates a 'Main' folder (type='asset') if missing
        - Assigns any unassigned assets to 'Main'
        - Deduplicates asset references inside folders
        """
        project = self.manager.current_project
        if not project:
            return

        # Ensure folders list exists
        if not hasattr(project, 'folders') or project.folders is None:
            project.folders = []

        # Find or create 'Main' folder (asset type)
        main_folder = None
        for f in project.folders:
            if getattr(f, 'type', None) == 'asset' and getattr(f, 'name', '') == 'Main':
                main_folder = f
                break
        if main_folder is None:
            from vogue_core.models import Folder
            main_folder = Folder(name='Main', type='asset', assets=[], shots=[])
            project.folders.append(main_folder)

        # Build set of assets referenced by folders
        assets_in_folders = set()
        for f in project.folders:
            if getattr(f, 'type', None) == 'asset':
                # Deduplicate in-place
                if hasattr(f, 'assets') and f.assets:
                    seen = set()
                    deduped = []
                    for a_name in f.assets:
                        if a_name not in seen:
                            seen.add(a_name)
                            deduped.append(a_name)
                    f.assets = deduped
                    assets_in_folders.update(deduped)

        # Ensure project.assets contains entries for any names referenced by folders
        from vogue_core.models import Asset as _VMAsset
        existing_asset_names = set(a.name for a in (project.assets or []))
        for name in list(assets_in_folders):
            if name not in existing_asset_names:
                project.assets.append(_VMAsset(name=name, type="Asset"))
                existing_asset_names.add(name)

        # Assign any unassigned assets to 'Main'
        for a in project.assets or []:
            if a.name not in assets_in_folders:
                main_folder.assets.append(a.name)
                assets_in_folders.add(a.name)

        # Final dedupe of Main
        if hasattr(main_folder, 'assets') and main_folder.assets:
            main_folder.assets = list(dict.fromkeys(main_folder.assets))

        # Rebuild project.assets strictly from folder listings; treat all as generic 'Asset'
        from vogue_core.models import Asset as _VMAsset
        rebuilt_assets = []
        seen_assets = set()
        for f in project.folders:
            if getattr(f, 'type', None) == 'asset':
                for a_name in getattr(f, 'assets', []) or []:
                    if a_name and a_name not in seen_assets:
                        seen_assets.add(a_name)
                        rebuilt_assets.append(_VMAsset(name=a_name, type="Asset"))

        project.assets = rebuilt_assets
    
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
    
        # Clean up the worker thread to prevent memory leaks
        self._cleanup_worker_thread()
    
    def on_scan_error(self, error_msg: str):
        """Handle filesystem scan error"""
        self.logger.error(f"Filesystem scan error: {error_msg}")
        QMessageBox.critical(self, "Scan Error", f"Filesystem scan failed: {error_msg}")

        # Clean up the worker thread to prevent memory leaks
        self._cleanup_worker_thread()

    def _cleanup_worker_thread(self):
        """Clean up worker thread and disconnect signals"""
        if hasattr(self, 'worker_thread') and self.worker_thread:
            try:
                # Disconnect all signals
                self.worker_thread.finished.disconnect()
                self.worker_thread.error.disconnect()

                # Wait for thread to finish if it's still running
                if self.worker_thread.isRunning():
                    self.worker_thread.wait(3000)  # Wait up to 3 seconds

                # Mark for deletion
                self.worker_thread.deleteLater()
                self.worker_thread = None

            except Exception as e:
                self.logger.warning(f"Error cleaning up worker thread: {e}")

    def _connect_menu_actions(self):
        """Connect menu actions using object names (robust method)"""
        try:
            menubar = self.menuBar()
            if not menubar:
                return

            # Find menus by traversing all actions
            for action in menubar.actions():
                menu = action.menu()
                if not menu:
                    continue

                menu_name = menu.objectName() or menu.title()

                # Connect file menu actions
                if "File" in menu_name or "&File" in menu_name:
                    self._connect_file_menu_actions(menu)
                # Connect edit menu actions
                elif "Edit" in menu_name or "&Edit" in menu_name:
                    self._connect_edit_menu_actions(menu)
                # Connect assets menu actions
                elif "Assets" in menu_name or "&Assets" in menu_name:
                    self._connect_assets_menu_actions(menu)
                # Connect shots menu actions
                elif "Shots" in menu_name or "&Shots" in menu_name:
                    self._connect_shots_menu_actions(menu)
                # Connect publish menu actions
                elif "Publish" in menu_name or "&Publish" in menu_name:
                    self._connect_publish_menu_actions(menu)
                # Connect tools menu actions
                elif "Tools" in menu_name or "&Tools" in menu_name:
                    self._connect_tools_menu_actions(menu)
                # Connect status menu actions
                elif "Status" in menu_name or "&Status" in menu_name:
                    self._connect_status_menu_actions(menu)

        except Exception as e:
            self.logger.error(f"Error connecting menu actions: {e}")

    def _connect_file_menu_actions(self, file_menu):
        """Connect file menu actions"""
        for action in file_menu.actions():
            text = action.text()
            if "Save" in text and "As" not in text:
                action.triggered.connect(self.save_project)
            elif "Save As" in text:
                action.triggered.connect(self.save_as_project)
            elif "Exit" in text:
                action.triggered.connect(self.close)

            # Handle submenus
            submenu = action.menu()
            if submenu:
                submenu_name = submenu.objectName() or submenu.title()
                if "Project" in submenu_name:
                    self._connect_project_menu_actions(submenu)

    def _connect_project_menu_actions(self, project_menu):
        """Connect project submenu actions"""
        for action in project_menu.actions():
            text = action.text()
            if "Browse" in text:
                action.triggered.connect(self.browse_project)
            elif "New" in text:
                action.triggered.connect(self.new_project)
            elif "Open" in text:
                action.triggered.connect(self.open_project)
            elif "Import" in text:
                action.triggered.connect(self.import_project)
            elif "Export" in text:
                action.triggered.connect(self.export_project)
            elif "Settings" in text:
                action.triggered.connect(self.project_settings)
            # Note: Recent Projects is handled by specific connection above

    def _connect_edit_menu_actions(self, edit_menu):
        """Connect edit menu actions"""
        for action in edit_menu.actions():
            text = action.text()
            if "Refresh" in text:
                action.triggered.connect(self.refresh_project)
            elif "Scan" in text:
                action.triggered.connect(self.scan_filesystem)
            elif "Settings" in text:
                action.triggered.connect(self.show_settings)

    def _connect_assets_menu_actions(self, assets_menu):
        """Connect assets menu actions"""
        for action in assets_menu.actions():
            text = action.text()
            if "Add Asset" in text:
                action.triggered.connect(self.add_asset)
            elif "Import Asset" in text:
                action.triggered.connect(self.import_asset)

    def _connect_shots_menu_actions(self, shots_menu):
        """Connect shots menu actions"""
        for action in shots_menu.actions():
            text = action.text()
            if "Add Shot" in text:
                action.triggered.connect(self.add_shot)

    def _connect_publish_menu_actions(self, publish_menu):
        """Connect publish menu actions"""
        for action in publish_menu.actions():
            text = action.text()
            if "Publish Version" in text:
                action.triggered.connect(self.publish_selection)
            elif "Batch Publish" in text:
                action.triggered.connect(self.batch_publish)

    def _connect_tools_menu_actions(self, tools_menu):
        """Connect tools menu actions"""
        for action in tools_menu.actions():
            text = action.text()
            if "Thumbnails" in text:
                action.triggered.connect(self.generate_thumbnails)
            elif "Cleanup" in text:
                action.triggered.connect(self.cleanup_project)
            elif "Validate" in text:
                action.triggered.connect(self.validate_project)
            elif "Optimize" in text:
                action.triggered.connect(self.optimize_project)
            elif "Maya" in text:
                action.triggered.connect(self.launch_maya)
            elif "Houdini" in text:
                action.triggered.connect(self.launch_houdini)
            elif "Blender" in text:
                action.triggered.connect(self.launch_blender)
            elif "API Server" in text:
                action.triggered.connect(self.start_api_server)
            elif "Logs" in text:
                action.triggered.connect(self.view_logs)

    def _connect_status_menu_actions(self, status_menu):
        """Connect status menu actions"""
        for action in status_menu.actions():
            text = action.text()
            if "System Information" in text:
                action.triggered.connect(self.show_system_info)
    
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
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Please load a project first.")
            return

        try:
            # Create shot creation dialog
            from vogue_app.dialogs import CreateShotDialog
            dialog = CreateShotDialog(self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                shot_data = dialog.get_shot_data()
                self.create_shot(shot_data)
                self.refresh_shots()
                self.add_log_message(f"Shot '{shot_data['name']}' added successfully")

        except Exception as e:
            self.logger.error(f"Error adding shot: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add shot: {e}")
    
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
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Please load a project first.")
            return

        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Import Version", "", "All Files (*.*)"
            )

            if file_path:
                # Get current selection
                current_item = self.version_manager.version_table.currentItem()
                if not current_item:
                    QMessageBox.warning(self, "No Selection", "Please select an asset or shot first.")
                    return

                # Import the file as a new version
                import shutil
                import os
                from pathlib import Path

                # Create version directory
                asset_name = self.get_current_asset_name()
                version_dir = Path(self.manager.current_project.path) / "01_Assets" / asset_name / "versions"
                version_dir.mkdir(parents=True, exist_ok=True)

                # Copy file
                file_name = Path(file_path).name
                dest_path = version_dir / file_name
                shutil.copy2(file_path, dest_path)

                # Create version entry
                version_data = {
                    'version': f"v{len(os.listdir(version_dir)):03d}",
                    'user': os.getenv('USERNAME', 'Unknown'),
                    'comment': f"Imported from {file_path}"
                }

                self.add_log_message(f"Version imported: {dest_path}")
                self.update_ui_state()

        except Exception as e:
            self.logger.error(f"Error importing version: {e}")
            QMessageBox.critical(self, "Error", f"Failed to import version: {e}")
    
    def export_version(self):
        """Export a version"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Please load a project first.")
            return

        try:
            # Get selected version
            current_row = self.version_manager.version_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "No Selection", "Please select a version to export.")
                return

            # Get version data
            path_item = self.version_manager.version_table.item(current_row, 5)
            if not path_item:
                QMessageBox.warning(self, "No Path", "Selected version has no file path.")
                return

            source_path = path_item.text()
            if not Path(source_path).exists():
                QMessageBox.warning(self, "File Not Found", f"File does not exist: {source_path}")
                return

            # Choose export location
            file_name = Path(source_path).name
            export_path, _ = QFileDialog.getSaveFileName(
                self, "Export Version", file_name, "All Files (*.*)"
            )

            if export_path:
                import shutil
                shutil.copy2(source_path, export_path)
                self.add_log_message(f"Version exported to: {export_path}")
                QMessageBox.information(self, "Export Complete", f"Version exported to: {export_path}")

        except Exception as e:
            self.logger.error(f"Error exporting version: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export version: {e}")
    
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
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Please load a project first.")
            return

        try:
            current_row = self.version_manager.version_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "No Selection", "Please select a version to copy.")
                return

            # Get version data
            path_item = self.version_manager.version_table.item(current_row, 5)
            if not path_item:
                QMessageBox.warning(self, "No Path", "Selected version has no file path.")
                return

            source_path = path_item.text()
            if not Path(source_path).exists():
                QMessageBox.warning(self, "File Not Found", f"File does not exist: {source_path}")
                return

            # Choose copy destination
            file_name = Path(source_path).name
            copy_path, _ = QFileDialog.getSaveFileName(
                self, "Copy Version", f"copy_{file_name}", "All Files (*.*)"
            )

            if copy_path:
                import shutil
                shutil.copy2(source_path, copy_path)
                self.add_log_message(f"Version copied to: {copy_path}")
                QMessageBox.information(self, "Copy Complete", f"Version copied to: {copy_path}")

        except Exception as e:
            self.logger.error(f"Error copying version: {e}")
            QMessageBox.critical(self, "Error", f"Failed to copy version: {e}")
    
    def delete_selected_version(self):
        """Delete the selected version"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Please load a project first.")
            return

        try:
            current_row = self.version_manager.version_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "No Selection", "Please select a version to delete.")
                return

            # Confirm deletion
            reply = QMessageBox.question(
                self, "Confirm Delete",
                "Are you sure you want to delete this version?\nThis action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # Get version data
            path_item = self.version_manager.version_table.item(current_row, 5)
            if not path_item:
                QMessageBox.warning(self, "No Path", "Selected version has no file path.")
                return

            source_path = path_item.text()
            if not Path(source_path).exists():
                QMessageBox.warning(self, "File Not Found", f"File does not exist: {source_path}")
                return

            # Delete the file
            Path(source_path).unlink()

            # Remove from table
            self.version_manager.version_table.removeRow(current_row)

            self.add_log_message(f"Version deleted: {source_path}")
            QMessageBox.information(self, "Delete Complete", "Version deleted successfully.")

        except Exception as e:
            self.logger.error(f"Error deleting version: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete version: {e}")
    
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
        # Asset creation working correctly
        try:
            # Prepare meta data including description
            meta = asset_data['meta'].copy()
            if asset_data.get('description'):
                meta['description'] = asset_data['description']
            
            # Create asset (no type field)
            asset = Asset(
                name=asset_data['name'],
                type="Asset",  # Default type
                path=str(Path(self.manager.current_project.path) / "01_Assets" / "Assets" / asset_data['name']),
                meta=meta
            )
            
            # Add to project
            self.manager.current_project.assets.append(asset)
            
            # Handle folder assignment
            folder_name = asset_data.get('folder', 'Main')
            self._assign_asset_to_folder(asset.name, folder_name)
            
            # Save project
            self.manager.save_project(self.manager.current_project)
            
            # Update UI
            self.update_assets_tree()
            
            self.add_log_message(f"Created asset: {asset.name} in folder: {folder_name}")
            
        except Exception as e:
            error_msg = f"Failed to create asset: {e}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def _assign_asset_to_folder(self, asset_name: str, folder_name: str):
        """Assign an asset to a folder, creating the folder if it doesn't exist"""
        if not self.manager.current_project:
            return
        
        # Ensure folders list exists
        if not hasattr(self.manager.current_project, 'folders') or self.manager.current_project.folders is None:
            self.manager.current_project.folders = []
        
        # If folder_name is "Main", don't create a folder - assets go at root
        if folder_name == "Main":
            # Find or create Main folder for tracking, but don't display it
            folder = None
            for f in self.manager.current_project.folders:
                if f.type == "asset" and f.name == "Main":
                    folder = f
                    break
            
            if folder is None:
                # Create Main folder for tracking
                from vogue_core.models import Folder
                folder = Folder(name="Main", type="asset", assets=[], shots=[])
                self.manager.current_project.folders.append(folder)
            
            # Add asset to Main folder for tracking
            if asset_name not in folder.assets:
                folder.assets.append(asset_name)
        else:
            # Find or create the folder
            folder = None
            for f in self.manager.current_project.folders:
                if f.type == "asset" and f.name == folder_name:
                    folder = f
                    break
            
            if folder is None:
                # Create new folder
                from vogue_core.models import Folder
                folder = Folder(name=folder_name, type="asset", assets=[], shots=[])
                self.manager.current_project.folders.append(folder)
            
            # Add asset to folder if not already there
            if asset_name not in folder.assets:
                folder.assets.append(asset_name)
    
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
        if current_item and current_item.data(0, Qt.ItemDataRole.UserRole) != "Folder":
            return current_item.text(0)
        return None
    
    def get_current_shot(self):
        """Get currently selected shot"""
        current_item = self.project_browser.shot_tree.currentItem()
        if current_item and current_item.data(0, Qt.ItemDataRole.UserRole) != "Folder":
            return current_item.text(0)
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
                from PyQt6.QtWidgets import QApplication
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
    
    def on_asset_selection_changed(self, current_item):
        """Handle asset selection change"""
        if not current_item:
            # No asset selected
            self.update_versions_table([])
            self.version_manager.entity_name_label.setText("No Selection")
            self.version_manager.entity_type_label.setText("")
            return
        
        # Get asset name
        asset_name = current_item.text(0)
        item_type = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        # Only handle actual assets, not folders
        if item_type == "Asset":
            # Update entity info
            self.version_manager.entity_name_label.setText(asset_name)
            self.version_manager.entity_type_label.setText("Asset")

            # For now, show empty versions table (can be enhanced later)
            self.update_versions_table([])

            # Update asset info panel with basic info
            self.update_asset_info_for_list(asset_name)
            
            # Enable publish button
            self.version_manager.publish_btn.setEnabled(True)
        else:
            # Folder selected, clear selection
            self.update_versions_table([])
            self.version_manager.entity_name_label.setText("No Selection")
            self.version_manager.entity_type_label.setText("")
            self.version_manager.publish_btn.setEnabled(False)
    
    def on_shot_selection_changed(self, current_item):
        """Handle shot selection change"""
        if not current_item:
            # No shot selected
            self.update_versions_table([])
            self.version_manager.entity_name_label.setText("No Selection")
            self.version_manager.entity_type_label.setText("")
            return
        
        # Get shot name and sequence
        shot_name = current_item.text(0)
        shot_sequence = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        # Update entity info
        self.version_manager.entity_name_label.setText(shot_name)
        self.version_manager.entity_type_label.setText(f"Shot - {shot_sequence}")

        # For now, show empty versions table (can be enhanced later)
        self.update_versions_table([])

        # Update asset info panel with basic shot info
        self.update_shot_info_for_list(shot_name, shot_sequence)
        
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

            # Sync project data to ensure UI consistency
            self.sync_project_to_ui()
            
            # Update recent projects
            self.update_recent_projects()

    def sync_project_to_ui(self):
        """Sync project model data to UI to ensure consistency"""
        if not self.manager.current_project:
            return


        try:
            # The update_assets_tree and update_shots_tree methods already handle
            # syncing from project to UI, so we just need to make sure they're called
            # This method serves as a central point for any additional sync operations

            # Ensure trees are properly expanded and updated
            self.project_browser.asset_tree.expandAll()
            self.project_browser.shot_tree.expandAll()
        except Exception as e:
            self.logger.error(f"Failed to sync project to UI: {e}")
            
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
        """Simple asset tree update"""
        tree = self.project_browser.asset_tree
        tree.clear()
        
        if not self.manager.current_project:
            placeholder_item = QTreeWidgetItem(tree)
            placeholder_item.setText(0, "No project loaded")
            return
        
        # Add folders
        if hasattr(self.manager.current_project, 'folders') and self.manager.current_project.folders:
            for folder in self.manager.current_project.folders:
                if folder.type == "asset":
                    folder_item = QTreeWidgetItem(tree)
                    folder_item.setText(0, folder.name)
                    folder_item.setData(0, Qt.ItemDataRole.UserRole, "Folder")
                    
                    # Add assets to folder
                    if hasattr(folder, 'assets') and folder.assets:
                        for asset_name in folder.assets:
                            asset_item = QTreeWidgetItem(folder_item)
                            asset_item.setText(0, asset_name)
                            asset_item.setData(0, Qt.ItemDataRole.UserRole, "Asset")
        
        # Add unassigned assets
        assigned_assets = set()
        if hasattr(self.manager.current_project, 'folders') and self.manager.current_project.folders:
            for folder in self.manager.current_project.folders:
                if folder.type == "asset" and hasattr(folder, 'assets') and folder.assets:
                    assigned_assets.update(folder.assets)
        
        for asset in self.manager.current_project.assets:
            if asset.name not in assigned_assets:
                asset_item = QTreeWidgetItem(tree)
                asset_item.setText(0, asset.name)
                asset_item.setData(0, Qt.ItemDataRole.UserRole, "Asset")
        
        tree.expandAll()
        self.logger.info(f"Updated assets tree with {tree.topLevelItemCount()} items")
    
    def setup_asset_tree_context_menu(self):
        """Setup context menu for asset tree"""
        self.asset_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.asset_tree.customContextMenuRequested.connect(self.show_asset_context_menu)
    
    def show_asset_context_menu(self, position):
        """Show context menu for asset tree"""
        item = self.asset_tree.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self.asset_tree)
        
        # Add actions based on item type
        if item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
            menu.addAction("New Asset", lambda: self.add_asset_to_folder(item))
            menu.addAction("New Subfolder", lambda: self.add_subfolder(item))
            menu.addSeparator()
            menu.addAction("Rename", lambda: self.rename_item(item))
            menu.addAction("Delete", lambda: self.delete_item(item))
        else:  # Asset
            menu.addAction("Rename", lambda: self.rename_item(item))
            menu.addAction("Delete", lambda: self.delete_item(item))
            menu.addSeparator()
            menu.addAction("Copy", lambda: self.copy_item(item))
            menu.addAction("Cut", lambda: self.cut_item(item))
            if self.clipboard_item:
                menu.addAction("Paste", lambda: self.paste_item(item))
        
        menu.exec(self.asset_tree.mapToGlobal(position))
    
    def add_asset_to_folder(self, folder_item):
        """Add new asset to folder"""
        name, ok = QInputDialog.getText(self, "New Asset", "Asset name:")
        if ok and name:
            asset_item = QTreeWidgetItem(folder_item)
            asset_item.setText(0, name)
            asset_item.setData(0, Qt.ItemDataRole.UserRole, "Asset")
            self.update_assets_tree()
    
    def add_subfolder(self, parent_item):
        """Add new subfolder"""
        name, ok = QInputDialog.getText(self, "New Subfolder", "Folder name:")
        if ok and name:
            folder_item = QTreeWidgetItem(parent_item)
            folder_item.setText(0, name)
            folder_item.setData(0, Qt.ItemDataRole.UserRole, "Folder")
            self.update_assets_tree()
    
    def rename_item(self, item):
        """Rename item"""
        old_name = item.text(0)
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=old_name)
        if ok and new_name and new_name != old_name:
            item.setText(0, new_name)
    
    def delete_item(self, item):
        """Delete item"""
        reply = QMessageBox.question(self, "Delete Item", 
                                   f"Delete '{item.text(0)}'?", 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                self.asset_tree.takeTopLevelItem(self.asset_tree.indexOfTopLevelItem(item))
    
    def copy_item(self, item):
        """Copy item to clipboard"""
        self.clipboard_item = item
        self.clipboard_operation = "copy"
        self.clipboard_type = item.data(0, Qt.ItemDataRole.UserRole)
    
    def cut_item(self, item):
        """Cut item to clipboard"""
        self.clipboard_item = item
        self.clipboard_operation = "cut"
        self.clipboard_type = item.data(0, Qt.ItemDataRole.UserRole)
    
    def paste_item(self, target_item):
        """Paste item from clipboard"""
        if not self.clipboard_item:
            return
        
        # Create new item
        new_item = QTreeWidgetItem(target_item)
        new_item.setText(0, self.clipboard_item.text(0))
        new_item.setData(0, Qt.ItemDataRole.UserRole, self.clipboard_type)
        
        # If cut operation, remove original
        if self.clipboard_operation == "cut":
            parent = self.clipboard_item.parent()
            if parent:
                parent.removeChild(self.clipboard_item)
            else:
                self.asset_tree.takeTopLevelItem(self.asset_tree.indexOfTopLevelItem(self.clipboard_item))
        
        # Clear clipboard
        self.clipboard_item = None
        self.clipboard_operation = None
        self.clipboard_type = None
            placeholder_item.setText(0, "No project loaded")
            placeholder_item.setData(0, Qt.ItemDataRole.UserRole, "Placeholder")
            placeholder_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            
            # Apply basic styling
            tree.setStyleSheet("""
                QTreeWidget {
                    background-color: white;
                    color: black;
                    border: 2px solid red;
                    font-size: 16px;
                    font-weight: bold;
                }
                QTreeWidget::item {
                    color: black;
                    background-color: yellow;
                    padding: 10px;
                    height: 30px;
                    border: 1px solid black;
                }
            """)
            
            self.logger.info("No project loaded - showing placeholder in assets tree")
            return

        # Use the existing tree widget instead of creating a new one
        tree = self.project_browser.asset_tree
        self.logger.info(f"Tree widget ID before clear: {id(tree)}")
        tree.clear()
        tree.setEnabled(True)
        tree.setColumnCount(1)
        tree.setHeaderHidden(True)
        self.logger.info(f"Tree widget ID after clear: {id(tree)}")
        
        # Ensure proper tree configuration
        tree.setRootIsDecorated(True)
        tree.setAlternatingRowColors(True)
        tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        tree.setDragEnabled(True)
        tree.setAcceptDrops(True)
        tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        tree.setDropIndicatorShown(True)
        tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        tree.setSortingEnabled(True)
        tree.setDragDropOverwriteMode(False)
        
        # Force the tree to be visible and properly sized
        tree.setVisible(True)
        tree.setMinimumHeight(200)
        tree.setMinimumWidth(200)
        
        self.logger.info(f"Updating assets tree for project: {self.manager.current_project.name}")
        self.logger.info(f"Project has {len(self.manager.current_project.assets)} assets")
        self.logger.info(f"Project has {len(getattr(self.manager.current_project, 'folders', []))} folders")
        
        # No test items - only show actual project data
        
        # Apply clean, professional styling
        tree.setStyleSheet("""
            QTreeWidget {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #CCCCCC;
                font-size: 12px;
                font-weight: normal;
                selection-background-color: #0078D4;
                alternate-background-color: #F8F8F8;
            }
            QTreeWidget::item {
                color: #000000;
                background-color: transparent;
                padding: 4px;
                height: 20px;
                border: none;
                margin: 0px;
            }
            QTreeWidget::item:selected {
                background-color: #0078D4;
                color: #FFFFFF;
            }
            QTreeWidget::item:hover {
                background-color: #E0E0E0;
                color: #000000;
            }
            QTreeWidget::branch {
                background-color: transparent;
            }
        """)
        
        # No test items - only show actual project data
        
        # Expand all items to make them visible
        tree.expandAll()
        
        # Debug: Check if items are actually visible
        self.logger.info(f"Tree has {tree.topLevelItemCount()} top-level items after population")
        self.logger.info(f"Tree root item count: {tree.invisibleRootItem().childCount()}")
        
        # Check if items are in the tree
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            if item:
                self.logger.info(f"Item {i}: '{item.text(0)}' - visible: {not item.isHidden()}, expanded: {item.isExpanded()}")
                if item.childCount() > 0:
                    for j in range(item.childCount()):
                        child = item.child(j)
                        if child:
                            self.logger.info(f"  Child {j}: '{child.text(0)}' - visible: {not child.isHidden()}")
            else:
                self.logger.warning(f"Item {i} is None!")
        
        # Ensure proper sizing and visibility
        tree.setMinimumSize(300, 400)
        tree.resize(300, 400)
        tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Force the tree to refresh and be visible
        tree.show()
        tree.raise_()
        tree.activateWindow()
        tree.repaint()
        tree.update()
        tree.viewport().update()
        tree.viewport().repaint()
        
        # Force the parent widget to refresh
        if tree.parent():
            tree.parent().update()
            tree.parent().repaint()
        
        # Ensure the tree is visible in the main window
        self.project_browser.show()
        self.project_browser.raise_()
        self.show()
        self.raise_()
        
        # Ensure the tree is focused and visible
        tree.setFocus()
        # Scroll to top of tree
        if tree.topLevelItemCount() > 0:
            tree.scrollToItem(tree.topLevelItem(0))
        
        # Make sure the tree is visible and properly sized
        tree.setVisible(True)
        tree.setEnabled(True)
        tree.setMinimumSize(400, 300)
        tree.resize(400, 300)
        
        # Force the tree to be visible
        tree.show()
        tree.raise_()
        tree.activateWindow()
        tree.repaint()
        tree.update()
        
        # Debug tree visibility
        self.logger.info(f"Tree final state - visible: {tree.isVisible()}, enabled: {tree.isEnabled()}")
        self.logger.info(f"Tree final size: {tree.size()}, geometry: {tree.geometry()}")
        self.logger.info(f"Tree parent: {tree.parent()}")
        self.logger.info(f"Tree parent visible: {tree.parent().isVisible() if tree.parent() else 'No parent'}")
        self.logger.info(f"Tree parent size: {tree.parent().size() if tree.parent() else 'No parent'}")
        
        # Force the tree to be visible
        tree.setVisible(True)
        tree.show()
        tree.raise_()
        tree.activateWindow()
        tree.repaint()
        tree.update()
        
        # Force the main window to refresh
        if hasattr(self, 'project_browser') and self.project_browser:
            self.project_browser.update()
            self.project_browser.repaint()
        
        self.logger.info(f"Applied styling to tree - visible: {tree.isVisible()}, enabled: {tree.isEnabled()}")
        self.logger.info(f"Tree size: {tree.size()}, geometry: {tree.geometry()}")
        self.logger.info(f"Tree parent: {tree.parent()}")
        self.logger.info(f"Tree object name: {tree.objectName()}")
        self.logger.info(f"Tree style sheet applied: {len(tree.styleSheet())} characters")
        
        # Check window geometry
        if hasattr(self, 'geometry'):
            self.logger.info(f"Main window geometry: {self.geometry()}")
        if hasattr(self, 'project_browser') and self.project_browser:
            self.logger.info(f"Project browser geometry: {self.project_browser.geometry()}")
            if hasattr(self.project_browser, 'tab_widget'):
                self.logger.info(f"Tab widget geometry: {self.project_browser.tab_widget.geometry()}")
                if self.project_browser.tab_widget.count() > 0:
                    current_tab = self.project_browser.tab_widget.currentWidget()
                    self.logger.info(f"Current tab geometry: {current_tab.geometry()}")
        
        # Check if the tree is in the correct tab
        if hasattr(self.project_browser, 'tab_widget'):
            current_tab = self.project_browser.tab_widget.currentIndex()
            self.logger.info(f"Current tab index: {current_tab}")
            self.logger.info(f"Tab count: {self.project_browser.tab_widget.count()}")
            
            # Make sure we're on the assets tab (index 0)
            if current_tab != 0:
                self.logger.info("Switching to assets tab (index 0)")
                self.project_browser.tab_widget.setCurrentIndex(0)

        # Create proper folder hierarchy from project data
        folder_items = {}
        unassigned_assets = []
        
        # Process existing folders and create folder items
        if hasattr(self.manager.current_project, 'folders') and self.manager.current_project.folders:
            for folder in self.manager.current_project.folders:
                if folder.type == "asset":
                    # Create folder item
                    folder_item = QTreeWidgetItem(tree)
                    folder_item.setText(0, folder.name)
                    folder_item.setData(0, Qt.ItemDataRole.UserRole, "Folder")
                    folder_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    self._style_tree_item(folder_item, is_folder=True)
                    folder_items[folder.name] = folder_item
                    self.logger.info(f"Created folder '{folder.name}' - text: '{folder_item.text(0)}' - tree ID: {id(tree)} - tree count: {tree.topLevelItemCount()}")
                    
                    # Add assets to this folder immediately after creating it
                    if hasattr(folder, 'assets') and folder.assets:
                        for asset_name in folder.assets:
                            asset_item = QTreeWidgetItem(folder_item)
                            asset_item.setText(0, asset_name)
                            asset_item.setData(0, Qt.ItemDataRole.UserRole, "Asset")
                            asset_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                            self.logger.info(f"Added asset '{asset_name}' to folder '{folder.name}' - text: '{asset_item.text(0)}'")
                    
                    self.logger.info(f"Created folder item: '{folder.name}' with {folder_item.childCount()} children")
        
        # Find unassigned assets (assets not in any folder)
        assigned_assets = set()
        if hasattr(self.manager.current_project, 'folders') and self.manager.current_project.folders:
            for folder in self.manager.current_project.folders:
                if folder.type == "asset" and hasattr(folder, 'assets') and folder.assets:
                    assigned_assets.update(folder.assets)

        # Add unassigned assets directly to root
        for asset in self.manager.current_project.assets:
            if asset.name not in assigned_assets:
                asset_item = QTreeWidgetItem(tree)
                asset_item.setText(0, asset.name)
                asset_item.setData(0, Qt.ItemDataRole.UserRole, "Asset")
                asset_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                unassigned_assets.append(asset.name)
                self.logger.info(f"Added unassigned asset '{asset.name}' to root")
        
        # Add unassigned assets to root
        for asset_name in unassigned_assets:
            item = QTreeWidgetItem(tree)
            item.setText(0, asset_name)
            item.setData(0, Qt.ItemDataRole.UserRole, "Asset")
            self._style_tree_item(item)
        
        # If no assets or folders exist, show sample data for demonstration
        if tree.topLevelItemCount() == 0:
            self.logger.info("No assets found - adding sample data for demonstration")
            
            # Create sample folder
            sample_folder = QTreeWidgetItem(tree)
            sample_folder.setText(0, "Sample Assets")
            sample_folder.setData(0, Qt.ItemDataRole.UserRole, "Folder")
            self._style_tree_item(sample_folder, is_folder=True)
            
            # Add sample assets
            sample_assets = ["Character_01", "Prop_01", "Environment_01"]
            for asset_name in sample_assets:
                asset_item = QTreeWidgetItem(sample_folder)
                asset_item.setText(0, asset_name)
                asset_item.setData(0, Qt.ItemDataRole.UserRole, "Asset")
                self._style_tree_item(asset_item)
        
        # Expand all folders
        tree.expandAll()
        
        # Set first item as current if available
        if tree.topLevelItemCount() > 0:
            first_item = tree.topLevelItem(0)
            tree.setCurrentItem(first_item)
        
        # Ensure visibility
        tree.setVisible(True)
        tree.update()
        tree.repaint()
        
        # Debug information
        self.logger.info(f"Updated assets tree with {tree.topLevelItemCount()} top-level items")
        self.logger.info(f"Tree visible: {tree.isVisible()}")
        self.logger.info(f"Tree enabled: {tree.isEnabled()}")
        self.logger.info(f"Tree size: {tree.size()}")
        
        # No need to reapply styling - clean white theme is already applied
        
        # Debug: List all top-level items and their children
        self.logger.info(f"Total top-level items in tree: {tree.topLevelItemCount()}")
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            self.logger.info(f"Top-level item {i}: '{item.text(0)}' (type: {item.data(0, Qt.ItemDataRole.UserRole)}) with {item.childCount()} children")
            for j in range(item.childCount()):
                child = item.child(j)
                self.logger.info(f"  Child {j}: '{child.text(0)}' (type: {child.data(0, Qt.ItemDataRole.UserRole)})")
        
        # Debug: Check tree widget properties
        self.logger.info(f"Tree widget properties:")
        self.logger.info(f"  - Visible: {tree.isVisible()}")
        self.logger.info(f"  - Enabled: {tree.isEnabled()}")
        self.logger.info(f"  - Size: {tree.size()}")
        self.logger.info(f"  - Geometry: {tree.geometry()}")
        self.logger.info(f"  - Parent: {tree.parent()}")
        self.logger.info(f"  - Parent visible: {tree.parent().isVisible() if tree.parent() else 'No parent'}")
        self.logger.info(f"  - Parent size: {tree.parent().size() if tree.parent() else 'No parent'}")
        
        # Check if tree is actually in the layout
        if tree.parent():
            parent_layout = tree.parent().layout()
            if parent_layout:
                self.logger.info(f"  - Parent layout: {parent_layout}")
                self.logger.info(f"  - Layout item count: {parent_layout.count()}")
                for i in range(parent_layout.count()):
                    item = parent_layout.itemAt(i)
                    if item and item.widget() == tree:
                        self.logger.info(f"  - Tree found in layout at position {i}")
                        break
                else:
                    self.logger.info(f"  - Tree NOT found in parent layout!")
            else:
                self.logger.info(f"  - Parent has no layout!")
        
        # Force the tree to be visible and properly sized
        tree.setVisible(True)
        tree.setEnabled(True)
        tree.setMinimumSize(300, 200)
        tree.setMaximumSize(500, 400)
        tree.resize(300, 200)
        tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Force the tree to be on top and visible - this is critical!
        tree.raise_()
        tree.activateWindow()
        tree.setFocus()
        tree.show()
        
        # Force the parent to refresh and ensure tree stays visible
        if tree.parent():
            tree.parent().raise_()
            tree.parent().activateWindow()
            tree.parent().update()
            tree.parent().repaint()
        
        # Force a final refresh to ensure tree stays visible
        tree.update()
        tree.repaint()
        tree.viewport().update()
        tree.viewport().repaint()
        
        # No need for periodic refresh timer - tree should stay visible now
        
        # Try to force the tree to refresh its display
        tree.viewport().update()
        tree.viewport().repaint()
    
    def _style_tree_item(self, item, is_folder=False):
        """Style a tree item"""
        from PyQt6.QtGui import QFont, QBrush, QColor
        
        font = QFont()
        font.setPointSize(14)
        item.setFont(0, font)
        
        if is_folder:
            item.setForeground(0, QBrush(QColor("#FFD700")))  # Gold for folders
            item.setIcon(0, self._get_folder_icon())
        else:
            item.setForeground(0, QBrush(QColor("#FFFFFF")))  # White for assets
            item.setIcon(0, self._get_asset_icon())
    
    def _get_folder_icon(self):
        """Get folder icon"""
        from PyQt6.QtGui import QIcon, QPixmap
        from PyQt6.QtCore import QSize
        
        # Create a simple folder icon
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor("#FFD700"))
        return QIcon(pixmap)
    
    def _get_asset_icon(self):
        """Get asset icon"""
        from PyQt6.QtGui import QIcon, QPixmap
        from PyQt6.QtCore import QSize
        
        # Create a simple asset icon
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor("#73C2FB"))
        return QIcon(pixmap)
    
    def move_asset_to_folder(self, asset_name, target_folder_name, is_cut=False):
        """Move an asset to a different folder in the project data"""
        if not self.manager.current_project:
            return
        
        try:
            # Ensure folders list exists
            if not hasattr(self.manager.current_project, 'folders') or self.manager.current_project.folders is None:
                self.manager.current_project.folders = []
            
            # Find the asset in project data
            asset = None
            for a in self.manager.current_project.assets:
                if a.name == asset_name:
                    asset = a
                    break
            
            if not asset:
                self.logger.warning(f"Asset not found in project data: {asset_name}")
                return
            
            # Remove asset from current folder
            for folder in self.manager.current_project.folders:
                if folder.type == "asset" and asset_name in folder.assets:
                    folder.assets.remove(asset_name)
                    break
            
            # Add asset to target folder
            if target_folder_name:
                # Find or create target folder
                target_folder = None
                for folder in self.manager.current_project.folders:
                    if folder.type == "asset" and folder.name == target_folder_name:
                        target_folder = folder
                        break
                
                if not target_folder:
                    # Create new folder
                    from vogue_core.models import Folder
                    target_folder = Folder(name=target_folder_name, type="asset", assets=[], shots=[])
                    self.manager.current_project.folders.append(target_folder)
                
                if asset_name not in target_folder.assets:
                    target_folder.assets.append(asset_name)
            else:
                # Add to Main folder (root level)
                main_folder = None
                for folder in self.manager.current_project.folders:
                    if folder.type == "asset" and folder.name == "Main":
                        main_folder = folder
                        break
                
                if not main_folder:
                    from vogue_core.models import Folder
                    main_folder = Folder(name="Main", type="asset", assets=[], shots=[])
                    self.manager.current_project.folders.append(main_folder)
                
                if asset_name not in main_folder.assets:
                    main_folder.assets.append(asset_name)
            
            # Save project
            self.manager.save_project(self.manager.current_project)
            
            # Update UI
            self.update_assets_tree()
            
            action = "Moved" if is_cut else "Copied"
            self.add_log_message(f"{action} asset '{asset_name}' to folder '{target_folder_name or 'Main'}'")
            
        except Exception as e:
            self.logger.error(f"Error moving asset to folder: {e}")
            self.add_log_message(f"Error moving asset: {e}")
    
    def delete_asset_from_project(self, asset_name):
        """Delete an asset from the project data"""
        if not self.manager.current_project:
            return
        
        try:
            # Remove from assets list
            self.manager.current_project.assets = [a for a in self.manager.current_project.assets if a.name != asset_name]
            
            # Remove from all folders
            for folder in self.manager.current_project.folders:
                if folder.type == "asset" and asset_name in folder.assets:
                    folder.assets.remove(asset_name)
            
            # Save project
            self.manager.save_project(self.manager.current_project)
            
            # Update UI
            self.update_assets_tree()
            
            self.add_log_message(f"Deleted asset: {asset_name}")
            
        except Exception as e:
            self.logger.error(f"Error deleting asset: {e}")
            self.add_log_message(f"Error deleting asset: {e}")
    
    def rename_asset_in_project(self, old_name, new_name):
        """Rename an asset in the project data"""
        if not self.manager.current_project:
            return
        
        try:
            # Update asset name
            for asset in self.manager.current_project.assets:
                if asset.name == old_name:
                    asset.name = new_name
                    break
            
            # Update in all folders
            for folder in self.manager.current_project.folders:
                if folder.type == "asset" and old_name in folder.assets:
                    index = folder.assets.index(old_name)
                    folder.assets[index] = new_name
            
            # Save project
            self.manager.save_project(self.manager.current_project)
            
            # Update UI
            self.update_assets_tree()
            
            self.add_log_message(f"Renamed asset from '{old_name}' to '{new_name}'")
            
        except Exception as e:
            self.logger.error(f"Error renaming asset: {e}")
            self.add_log_message(f"Error renaming asset: {e}")
    
    def create_folder_in_project(self, folder_name, folder_type="asset"):
        """Create a new folder in the project data"""
        if not self.manager.current_project:
            return
        
        try:
            # Ensure folders list exists
            if not hasattr(self.manager.current_project, 'folders') or self.manager.current_project.folders is None:
                self.manager.current_project.folders = []
            
            # Check if folder already exists
            for folder in self.manager.current_project.folders:
                if folder.type == folder_type and folder.name == folder_name:
                    self.add_log_message(f"Folder '{folder_name}' already exists")
                    return
            
            # Create new folder
            from vogue_core.models import Folder
            new_folder = Folder(name=folder_name, type=folder_type, assets=[], shots=[])
            self.manager.current_project.folders.append(new_folder)
            
            # Save project
            self.manager.save_project(self.manager.current_project)
            
            # Update UI
            if folder_type == "asset":
                self.update_assets_tree()
            else:
                self.update_shots_tree()
            
            self.add_log_message(f"Created {folder_type} folder: {folder_name}")
            
        except Exception as e:
            self.logger.error(f"Error creating folder: {e}")
            self.add_log_message(f"Error creating folder: {e}")
    
    def update_shots_tree(self):
        """Update the shots tree widget"""
        if not self.manager.current_project:
            return
        

        # Clear the tree first
        self.project_browser.shot_tree.clear()

        # Create shot folders from saved folder structure
        shot_folders = [f for f in self.manager.current_project.folders if f.type == "shot"]

        if shot_folders:
            # Recreate the custom folder structure
            for folder in shot_folders:
                # Create folder
                folder_item = QTreeWidgetItem(self.project_browser.shot_tree)
                folder_item.setText(0, folder.name)
                folder_item.setData(0, Qt.ItemDataRole.UserRole, "Folder")

                # Add shots to the folder
                for shot_name in folder.shots:
                    # Find the shot in the project
                    shot = None
                    for s in self.manager.current_project.shots:
                        if s.name == shot_name:
                            shot = s
                            break

                    if shot:
                        shot_item = QTreeWidgetItem(folder_item)
                        shot_item.setText(0, shot.name)
                        shot_item.setData(0, Qt.ItemDataRole.UserRole, "Shot")
        else:
            # Fallback: group shots by sequence if no custom folders exist
            if self.manager.current_project.shots:
                # Group shots by sequence
                shots_by_sequence = {}
                for shot in self.manager.current_project.shots:
                    sequence = shot.sequence
                    if sequence not in shots_by_sequence:
                        shots_by_sequence[sequence] = []
                    shots_by_sequence[sequence].append(shot)

                # Create sequence folders and add shots
                for sequence, shots in shots_by_sequence.items():
                    # Create sequence folder
                    seq_folder = QTreeWidgetItem(self.project_browser.shot_tree)
                    seq_folder.setText(0, sequence)
                    seq_folder.setData(0, Qt.ItemDataRole.UserRole, "Folder")

                    # Add shots to the sequence
                    for shot in shots:
                        shot_item = QTreeWidgetItem(seq_folder)
                        shot_item.setText(0, shot.name)
                        shot_item.setData(0, Qt.ItemDataRole.UserRole, "Shot")
        
        # Expand all folders so shots are immediately visible
        self.project_browser.shot_tree.expandAll()

        # Add a summary item at the top showing all shots
        if self.manager.current_project.shots:
            # Check if summary already exists
            summary_exists = False
            for i in range(self.project_browser.shot_tree.topLevelItemCount()):
                item = self.project_browser.shot_tree.topLevelItem(i)
                if item.data(0, Qt.ItemDataRole.UserRole) == "Summary":
                    summary_exists = True
                    break

            if not summary_exists:
                summary_item = QTreeWidgetItem(self.project_browser.shot_tree)
                summary_item.setText(0, f"🎬 All Shots ({len(self.manager.current_project.shots)} total)")
                summary_item.setData(0, Qt.ItemDataRole.UserRole, "Summary")

                # Add all shots in a flat list for easy access
                for shot in self.manager.current_project.shots:
                    shot_item = QTreeWidgetItem(summary_item)
                    shot_item.setText(0, shot.name)
                    shot_item.setData(0, Qt.ItemDataRole.UserRole, "Shot")

                summary_item.setExpanded(True)  # Expand summary by default
        

        # Force the tree to be visible and update
        self.project_browser.shot_tree.setVisible(True)
        self.project_browser.shot_tree.update()
        self.project_browser.shot_tree.repaint()

    def update_asset_info_for_list(self, asset_name: str, asset_type: str = None):
        """Update asset info panel for list-based assets"""
        if hasattr(self.right_panel, 'asset_name_label'):
            self.right_panel.asset_name_label.setText(asset_name)
            self.right_panel.asset_type_label.setText("Asset")  # Fixed type
            self.right_panel.asset_path_label.setText("Path: Not Available")
            self.right_panel.asset_status_label.setText("Status: Active")
            self.right_panel.asset_artist_label.setText("Artist: Unknown")
            self.right_panel.asset_date_label.setText("Modified: Today")

    def update_shot_info_for_list(self, shot_name: str, shot_sequence: str):
        """Update asset info panel for list-based shots"""
        if hasattr(self.right_panel, 'asset_name_label'):
            self.right_panel.asset_name_label.setText(shot_name)
            self.right_panel.asset_type_label.setText(f"Shot - {shot_sequence}")
            self.right_panel.asset_path_label.setText("Path: Not Available")
            self.right_panel.asset_status_label.setText("Status: Active")
            self.right_panel.asset_artist_label.setText("Artist: Unknown")
            self.right_panel.asset_date_label.setText("Modified: Today")
    
    def update_recent_projects(self):
        """Update the recent projects list"""
        # Recent projects are now handled through the menu system
        # No longer need to update a widget in the left panel
        pass
    
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
        # Update window title with project name
        if name and name != "No Project":
            self.setWindowTitle(f"Vogue Manager - {name}")
        else:
            self.setWindowTitle("Vogue Manager - Prism Interface")

        # Update status bar with project path
        if path:
            self.status_bar.showMessage(f"Project: {path}")
        else:
            self.status_bar.showMessage("No project loaded")

        # Update project info labels in the browser
        if hasattr(self, 'project_browser') and hasattr(self.project_browser, 'project_name_label'):
            if name and name != "No Project":
                self.project_browser.project_name_label.setText(f"Project: {name}")
            else:
                self.project_browser.project_name_label.setText("Project: No Project Loaded")

            if path:
                self.project_browser.project_path_label.setText(f"Path: {path}")
            else:
                self.project_browser.project_path_label.setText("Path: Not Available")

        # Call parent method for any additional updates
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
    
    # Task management methods
    def new_task(self):
        """Create a new task"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Please load a project first.")
            return

        try:
            # Create task creation dialog
            from vogue_app.dialogs import CreateTaskDialog
            dialog = CreateTaskDialog(self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                task_data = dialog.get_task_data()

                # Add to tasks list
                task_text = f"{task_data['name']} - {task_data['status']}"
                item = QListWidgetItem(task_text)
                self.project_browser.tasks_list.addItem(item)

                self.add_log_message(f"Task '{task_data['name']}' created successfully")

        except Exception as e:
            self.logger.error(f"Error creating task: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create task: {e}")

    def assign_task(self):
        """Assign a task to someone"""
        current_item = self.project_browser.tasks_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a task to assign.")
            return

        try:
            # Simple assignment dialog
            user, ok = QInputDialog.getText(
                self, "Assign Task",
                "Enter user name to assign this task to:",
                QLineEdit.EchoMode.Normal,
                ""
            )

            if ok and user:
                current_text = current_item.text()
                new_text = f"{current_text} [Assigned to: {user}]"
                current_item.setText(new_text)
                self.add_log_message(f"Task assigned to {user}")

        except Exception as e:
            self.logger.error(f"Error assigning task: {e}")
            QMessageBox.critical(self, "Error", f"Failed to assign task: {e}")

    def complete_task(self):
        """Mark a task as completed"""
        current_item = self.project_browser.tasks_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a task to complete.")
            return

        try:
            # Confirm completion
            reply = QMessageBox.question(
                self, "Complete Task",
                "Mark this task as completed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                current_text = current_item.text()
                new_text = f"{current_text} - COMPLETED"
                current_item.setText(new_text)

                # Change text color to indicate completion
                current_item.setForeground(QColor("#4CAF50"))  # Green color

                self.add_log_message("Task marked as completed")

        except Exception as e:
            self.logger.error(f"Error completing task: {e}")
            QMessageBox.critical(self, "Error", f"Failed to complete task: {e}")

    # Department management methods
    def add_department(self):
        """Add a new department"""
        try:
            # Simple department creation dialog
            dept_name, ok = QInputDialog.getText(
                self, "Add Department",
                "Enter department name:",
                QLineEdit.EchoMode.Normal,
                ""
            )

            if ok and dept_name:
                dept_text = f"{dept_name} - Active"
                item = QListWidgetItem(dept_text)
                self.project_browser.departments_list.addItem(item)
                self.add_log_message(f"Department '{dept_name}' added successfully")

        except Exception as e:
            self.logger.error(f"Error adding department: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add department: {e}")

    def edit_department(self):
        """Edit an existing department"""
        current_item = self.project_browser.departments_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a department to edit.")
            return

        try:
            current_text = current_item.text()
            dept_name = current_text.split(" - ")[0]  # Extract department name

            # Edit department name dialog
            new_name, ok = QInputDialog.getText(
                self, "Edit Department",
                "Enter new department name:",
                QLineEdit.EchoMode.Normal,
                dept_name
            )

            if ok and new_name:
                new_text = f"{new_name} - Active"
                current_item.setText(new_text)
                self.add_log_message(f"Department renamed to '{new_name}'")

        except Exception as e:
            self.logger.error(f"Error editing department: {e}")
            QMessageBox.critical(self, "Error", f"Failed to edit department: {e}")

    def remove_department(self):
        """Remove a department"""
        current_item = self.project_browser.departments_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a department to remove.")
            return

        try:
            # Confirm removal
            reply = QMessageBox.question(
                self, "Remove Department",
                "Are you sure you want to remove this department?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                dept_name = current_item.text().split(" - ")[0]
                row = self.project_browser.departments_list.row(current_item)
                self.project_browser.departments_list.takeItem(row)
                self.add_log_message(f"Department '{dept_name}' removed")

        except Exception as e:
            self.logger.error(f"Error removing department: {e}")
            QMessageBox.critical(self, "Error", f"Failed to remove department: {e}")

    # Department tools methods
    def open_farm_monitor(self):
        """Open the farm monitor"""
        QMessageBox.information(self, "Farm Monitor", "Farm monitor functionality will be implemented.")

    # Asset info methods
    def copy_asset_path(self):
        """Copy the current asset path to clipboard"""
        current_item = self.version_manager.version_table.currentItem()
        if current_item:
            row = current_item.row()
            path_item = self.version_manager.version_table.item(row, 5)  # Path column
            if path_item:
                from PyQt6.QtWidgets import QApplication
                QApplication.clipboard().setText(path_item.text())
                self.add_log_message("Asset path copied to clipboard")

    def show_in_explorer(self):
        """Show the current asset in file explorer"""
        current_item = self.version_manager.version_table.currentItem()
        if current_item:
            row = current_item.row()
            path_item = self.version_manager.version_table.item(row, 5)  # Path column
            if path_item:
                asset_path = path_item.text()
                try:
                    import os
                    if os.name == 'nt':  # Windows
                        os.startfile(os.path.dirname(asset_path))
                    else:  # macOS/Linux
                        import subprocess
                        subprocess.run(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', os.path.dirname(asset_path)])
                    self.add_log_message(f"Opened in explorer: {os.path.dirname(asset_path)}")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not open in explorer: {e}")

    def show_asset_properties(self):
        """Show properties of the current asset"""
        current_item = self.version_manager.version_table.currentItem()
        if current_item:
            row = current_item.row()
            path_item = self.version_manager.version_table.item(row, 5)  # Path column
            if path_item:
                asset_path = path_item.text()
                import os
                file_size = "Unknown"
                try:
                    if os.path.exists(asset_path):
                        size_bytes = os.path.getsize(asset_path)
                        # Convert to human readable format
                        for unit in ['B', 'KB', 'MB', 'GB']:
                            if size_bytes < 1024.0:
                                file_size = ".1f"
                                break
                            size_bytes /= 1024.0
                except:
                    pass

                QMessageBox.information(self, "Asset Properties",
                                      f"Path: {asset_path}\nSize: {file_size}")

    # Update asset info display methods
    def update_asset_info(self, asset=None):
        """Update the asset info panel with current selection"""
        if hasattr(self, 'right_panel'):
            if asset:
                self.right_panel.asset_name_label.setText(asset.name or "Unknown")
                self.right_panel.asset_type_label.setText(asset.type or "Unknown")
                self.right_panel.asset_path_label.setText(asset.path or "Unknown")
                self.right_panel.asset_status_label.setText("Published")
                self.right_panel.asset_artist_label.setText(asset.meta.get('artist', 'Unknown') if hasattr(asset, 'meta') else 'Unknown')
                self.right_panel.asset_date_label.setText("Recent")

                # Update metadata
                metadata = []
                if hasattr(asset, 'meta'):
                    for key, value in asset.meta.items():
                        metadata.append(f"{key}: {value}")
                self.right_panel.asset_metadata_text.setPlainText("\n".join(metadata) if metadata else "No metadata available")
            else:
                self.right_panel.asset_name_label.setText("No Selection")
                self.right_panel.asset_type_label.setText("-")
                self.right_panel.asset_path_label.setText("-")
                self.right_panel.asset_status_label.setText("-")
                self.right_panel.asset_artist_label.setText("-")
                self.right_panel.asset_date_label.setText("-")
                self.right_panel.asset_metadata_text.setPlainText("No metadata available")
    
    def show(self):
        """Show the main window"""
        super().show()
    
    # Removed _reapply_tree_styling method - no longer needed

