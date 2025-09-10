# Clean controller implementation for asset tree
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTreeWidget, 
                             QTreeWidgetItem, QTabWidget, QSplitter, QComboBox, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QAbstractItemView, QMessageBox, QInputDialog, 
                             QDialog, QFormLayout, QLineEdit, QTextEdit, 
                             QGroupBox, QProgressBar, QStatusBar, QMenuBar, 
                             QMenu, QToolBar, QDockWidget, QListWidget, 
                             QListWidgetItem, QCheckBox, QSpinBox, QSlider, 
                             QScrollArea, QFrame, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QBrush, QColor, QIcon

from vogue_core.manager import ProjectManager
from vogue_core.logging_utils import get_logger
from vogue_core.settings import settings
from vogue_app.ui import PrismMainWindow

class VogueController(PrismMainWindow):
    """Clean controller for Vogue Manager desktop application"""
    
    def __init__(self):
        super().__init__()
        self.manager = ProjectManager()
        self.logger = get_logger("Controller")
        
        # Initialize clipboard state for cut/copy operations
        self.clipboard_item = None
        self.clipboard_items = None  # For multi-select operations
        self.clipboard_operation = None  # 'cut' or 'copy'
        self.clipboard_type = None  # 'asset', 'shot', or 'multiple'
        
        # Connect signals after UI is set up
        self.setup_connections()
        
        # Setup asset tree context menu
        self.setup_asset_tree_context_menu()
        
        # Setup shot tree context menu
        self.setup_shot_tree_context_menu()
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()

        # Setup tree widgets FIRST (before loading project)
        QTimer.singleShot(100, self._setup_tree_widgets)

        # Auto-load last opened project AFTER tree setup
        QTimer.singleShot(200, self._auto_load_last_project)

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
        tree = self.project_browser.asset_tree
        tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(self.show_asset_context_menu)
    
    def setup_shot_tree_context_menu(self):
        """Setup context menu for shot tree"""
        tree = self.project_browser.shot_tree
        tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(self.show_shot_context_menu)
    
    def show_asset_context_menu(self, position):
        """Show context menu for asset tree"""
        tree = self.project_browser.asset_tree
        item = tree.itemAt(position)
        if not item:
            return
        
        # Get selected items
        selected_items = tree.selectedItems()
        
        menu = QMenu(tree)
        
        if len(selected_items) == 1:
            # Single item selected
            if item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
                menu.addAction("New Asset", lambda: self.add_asset_to_folder(item))
                menu.addAction("New Subfolder", lambda: self.add_subfolder(item))
                menu.addSeparator()
                menu.addAction("Rename", lambda: self.rename_item(item))
                menu.addAction("Delete", lambda: self.delete_item(item))
                menu.addSeparator()
                menu.addAction("Copy", lambda: self.copy_item(item))
                menu.addAction("Cut", lambda: self.cut_item(item))
                if self.clipboard_item:
                    menu.addAction("Paste", lambda: self.paste_item(item))
            else:  # Asset
                menu.addAction("Rename", lambda: self.rename_item(item))
                menu.addAction("Delete", lambda: self.delete_item(item))
                menu.addSeparator()
                menu.addAction("Copy", lambda: self.copy_item(item))
                menu.addAction("Cut", lambda: self.cut_item(item))
                if self.clipboard_item:
                    menu.addAction("Paste", lambda: self.paste_item(item))
        else:
            # Multiple items selected
            menu.addAction(f"Delete Selected ({len(selected_items)})", lambda: self.delete_selected_items())
            menu.addSeparator()
            menu.addAction(f"Copy Selected ({len(selected_items)})", lambda: self.copy_selected_items())
            menu.addAction(f"Cut Selected ({len(selected_items)})", lambda: self.cut_selected_items())
        
        menu.exec(tree.mapToGlobal(position))
    
    def show_shot_context_menu(self, position):
        """Show context menu for shot tree"""
        tree = self.project_browser.shot_tree
        item = tree.itemAt(position)
        if not item:
            return
        
        # Get selected items
        selected_items = tree.selectedItems()
        
        menu = QMenu(tree)
        
        if len(selected_items) == 1:
            # Single item selected
            if item.data(0, Qt.ItemDataRole.UserRole) == "Folder":
                menu.addAction("New Shot", lambda: self.add_shot_to_folder(item))
                menu.addAction("New Subfolder", lambda: self.add_shot_subfolder(item))
                menu.addSeparator()
                menu.addAction("Rename", lambda: self.rename_item(item))
                menu.addAction("Delete", lambda: self.delete_item(item))
                menu.addSeparator()
                menu.addAction("Copy", lambda: self.copy_item(item))
                menu.addAction("Cut", lambda: self.cut_item(item))
                if self.clipboard_item:
                    menu.addAction("Paste", lambda: self.paste_item(item))
            else:  # Shot
                menu.addAction("Rename", lambda: self.rename_item(item))
                menu.addAction("Delete", lambda: self.delete_item(item))
                menu.addSeparator()
                menu.addAction("Copy", lambda: self.copy_item(item))
                menu.addAction("Cut", lambda: self.cut_item(item))
                if self.clipboard_item:
                    menu.addAction("Paste", lambda: self.paste_item(item))
        else:
            # Multiple items selected
            menu.addAction(f"Delete Selected ({len(selected_items)})", lambda: self.delete_selected_shot_items())
            menu.addSeparator()
            menu.addAction(f"Copy Selected ({len(selected_items)})", lambda: self.copy_selected_shot_items())
            menu.addAction(f"Cut Selected ({len(selected_items)})", lambda: self.cut_selected_shot_items())
        
        menu.exec(tree.mapToGlobal(position))
    
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
        """Delete item from both UI and project data"""
        item_name = item.text(0)
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(self, "Delete Item", 
                                   f"Delete '{item_name}'?", 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from project data first
            if self.manager.current_project:
                if item_type == "Asset":
                    # Remove from assets list
                    self.manager.current_project.assets = [
                        asset for asset in self.manager.current_project.assets 
                        if asset.name != item_name
                    ]
                    # Remove from folders
                    if hasattr(self.manager.current_project, 'folders'):
                        for folder in self.manager.current_project.folders:
                            if folder.type == "asset" and hasattr(folder, 'assets'):
                                folder.assets = [a for a in folder.assets if a != item_name]
                elif item_type == "Shot":
                    # Remove from shots list
                    self.manager.current_project.shots = [
                        shot for shot in self.manager.current_project.shots 
                        if shot.name != item_name
                    ]
                    # Remove from folders
                    if hasattr(self.manager.current_project, 'folders'):
                        for folder in self.manager.current_project.folders:
                            if folder.type == "shot" and hasattr(folder, 'shots'):
                                folder.shots = [s for s in folder.shots if s != item_name]
                elif item_type == "Folder":
                    # Remove folder from project
                    if hasattr(self.manager.current_project, 'folders'):
                        self.manager.current_project.folders = [
                            folder for folder in self.manager.current_project.folders 
                            if folder.name != item_name
                        ]
                
                # Save project to file
                try:
                    self.manager.save_project()
                    self.logger.info(f"Deleted {item_type.lower()}: {item_name} and saved project")
                except Exception as e:
                    self.logger.error(f"Failed to save project after deletion: {e}")
                    QMessageBox.warning(self, "Save Error", f"Item deleted from UI but failed to save project: {e}")
            
            # Remove from UI
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                # Find which tree the item belongs to
                if hasattr(self.project_browser, 'asset_tree'):
                    for i in range(self.project_browser.asset_tree.topLevelItemCount()):
                        if self.project_browser.asset_tree.topLevelItem(i) == item:
                            self.project_browser.asset_tree.takeTopLevelItem(i)
                            return
                if hasattr(self.project_browser, 'shot_tree'):
                    for i in range(self.project_browser.shot_tree.topLevelItemCount()):
                        if self.project_browser.shot_tree.topLevelItem(i) == item:
                            self.project_browser.shot_tree.takeTopLevelItem(i)
                            return
    
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
                tree = self.project_browser.asset_tree
                tree.takeTopLevelItem(tree.indexOfTopLevelItem(self.clipboard_item))
        
        # Clear clipboard
        self.clipboard_item = None
        self.clipboard_operation = None
        self.clipboard_type = None
    
    def setup_connections(self):
        """Setup signal connections"""
        # Connect button signals
        self.project_browser.add_asset_btn.clicked.connect(self.add_asset)
        self.project_browser.new_folder_btn.clicked.connect(self.add_folder)
        self.project_browser.refresh_assets_btn.clicked.connect(self.update_assets_tree)
        
        # Connect menu actions
        self.connect_menu_actions()
    
    def _setup_tree_widgets(self):
        """Setup tree widgets"""
        self.logger.info("Setting up tree widgets")
        # Tree widgets are already created in UI, just update them
        self.update_assets_tree()
        self.logger.info("Tree widgets setup completed successfully")
    
    def _auto_load_last_project(self):
        """Auto-load the last opened project"""
        try:
            # Get recent projects from settings
            recent_projects = settings.get_recent_projects()
            self.logger.info(f"Found {len(recent_projects)} recent projects")
            
            if recent_projects:
                # Log all recent projects for debugging
                for i, project in enumerate(recent_projects):
                    self.logger.info(f"  {i+1}. {project['name']} - {project['path']}")
                
                # Load the most recent project
                last_project = recent_projects[0]
                project_path = last_project['path']
                self.logger.info(f"Attempting to load: {last_project['name']} from {project_path}")
                
                if os.path.exists(project_path):
                    self.logger.info(f"Auto-loading last project: {last_project['name']} from {project_path}")
                    self.manager.load_project(project_path)
                    self.update_assets_tree()
                    self.setWindowTitle(f"Vogue Manager - {self.manager.current_project.name}")
                    self.logger.info("Project loaded successfully")
                else:
                    self.logger.info(f"Last project path no longer exists: {project_path}")
                    # Try next project if first doesn't exist
                    for project in recent_projects[1:]:
                        if os.path.exists(project['path']):
                            self.logger.info(f"Trying next project: {project['name']} from {project['path']}")
                            self.manager.load_project(project['path'])
                            self.update_assets_tree()
                            self.setWindowTitle(f"Vogue Manager - {self.manager.current_project.name}")
                            self.logger.info("Project loaded successfully")
                            break
            else:
                self.logger.info("No recent projects to load")
        except Exception as e:
            self.logger.error(f"Failed to auto-load last project: {e}")
    
    def add_asset(self):
        """Add new asset"""
        name, ok = QInputDialog.getText(self, "New Asset", "Asset name:")
        if ok and name:
            # Add to current project
            if self.manager.current_project:
                from vogue_core.models import Asset
                asset = Asset(name=name)
                self.manager.current_project.assets.append(asset)
                self.update_assets_tree()
                self.logger.info(f"Added asset: {name}")
    
    def add_folder(self):
        """Add new folder"""
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            # Add to current project
            if self.manager.current_project:
                from vogue_core.models import Folder
                folder = Folder(name=name, type="asset", assets=[])
                if not hasattr(self.manager.current_project, 'folders'):
                    self.manager.current_project.folders = []
                self.manager.current_project.folders.append(folder)
                self.update_assets_tree()
                self.logger.info(f"Added folder: {name}")
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for asset tree"""
        from PyQt6.QtGui import QShortcut, QKeySequence
        
        tree = self.project_browser.asset_tree
        
        # Copy (Ctrl+C)
        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, tree)
        copy_shortcut.activated.connect(self.copy_selected_item)
        
        # Cut (Ctrl+X)
        cut_shortcut = QShortcut(QKeySequence.StandardKey.Cut, tree)
        cut_shortcut.activated.connect(self.cut_selected_item)
        
        # Paste (Ctrl+V)
        paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, tree)
        paste_shortcut.activated.connect(self.paste_to_selected_item)
        
        # Delete
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), tree)
        delete_shortcut.activated.connect(self.delete_selected_item)
    
    def copy_selected_item(self):
        """Copy selected item(s)"""
        tree = self.project_browser.asset_tree
        selected_items = tree.selectedItems()
        
        if not selected_items:
            return
        
        if len(selected_items) == 1:
            self.copy_item(selected_items[0])
        else:
            self.copy_selected_items()
    
    def cut_selected_item(self):
        """Cut selected item(s)"""
        tree = self.project_browser.asset_tree
        selected_items = tree.selectedItems()
        
        if not selected_items:
            return
        
        if len(selected_items) == 1:
            self.cut_item(selected_items[0])
        else:
            self.cut_selected_items()
    
    def paste_to_selected_item(self):
        """Paste to selected item"""
        tree = self.project_browser.asset_tree
        current_item = tree.currentItem()
        if current_item:
            self.paste_item(current_item)
    
    def delete_selected_item(self):
        """Delete selected item(s)"""
        tree = self.project_browser.asset_tree
        selected_items = tree.selectedItems()
        
        if not selected_items:
            return
        
        if len(selected_items) == 1:
            self.delete_item(selected_items[0])
        else:
            self.delete_selected_items()
    
    def connect_menu_actions(self):
        """Connect menu actions to their handlers"""
        # Connect directly to the stored action instances
        self.browse_project_action.triggered.connect(self.browse_project)
        self.new_project_action.triggered.connect(self.new_project)
        self.open_project_action.triggered.connect(self.open_project)
        self.recent_projects_action.triggered.connect(self.show_recent_projects)
        self.import_project_action.triggered.connect(self.import_project)
        self.export_project_action.triggered.connect(self.export_project)
        self.project_settings_action.triggered.connect(self.project_settings)
        
        self.logger.info("Menu actions connected successfully")
    
    def browse_project(self):
        """Browse for project directory"""
        from PyQt6.QtWidgets import QFileDialog
        
        project_path = QFileDialog.getExistingDirectory(
            self, 
            "Select Project Directory",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if project_path:
            self.load_project(project_path)
    
    def new_project(self):
        """Create new project"""
        from PyQt6.QtWidgets import QInputDialog
        
        project_name, ok = QInputDialog.getText(
            self, 
            "New Project", 
            "Enter project name:"
        )
        
        if ok and project_name:
            # Create project directory
            from pathlib import Path
            import os
            
            # Get projects directory from settings
            projects_dir = getattr(settings, 'projects_dir', os.path.expanduser("~/VogueProjects"))
            project_path = Path(projects_dir) / project_name
            
            try:
                # Create project structure
                self.manager.create_project(str(project_path), project_name)
                self.load_project(str(project_path))
                self.logger.info(f"Created new project: {project_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create project: {e}")
    
    def open_project(self):
        """Open existing project"""
        from PyQt6.QtWidgets import QFileDialog
        
        project_file = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "Project Files (*.json);;All Files (*)"
        )[0]
        
        if project_file:
            self.load_project(project_file)
    
    def show_recent_projects(self):
        """Show recent projects dialog"""
        from vogue_app.dialogs import RecentProjectsDialog
        
        dialog = RecentProjectsDialog(self)
        # Connect the signal to load the project
        dialog.project_selected.connect(self.load_project)
        dialog.exec()
    
    def import_project(self):
        """Import project from external source"""
        QMessageBox.information(self, "Import Project", "Import functionality coming soon!")
    
    def export_project(self):
        """Export project to external format"""
        QMessageBox.information(self, "Export Project", "Export functionality coming soon!")
    
    def project_settings(self):
        """Open project settings"""
        QMessageBox.information(self, "Project Settings", "Project settings coming soon!")
    
    def load_project(self, project_path):
        """Load project from path"""
        try:
            self.manager.load_project(project_path)
            self.update_assets_tree()
            self.setWindowTitle(f"Vogue Manager - {self.manager.current_project.name}")
            
            # Add to recent projects
            settings.add_recent_project(self.manager.current_project.name, project_path)
            
            self.logger.info(f"Loaded project: {self.manager.current_project.name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project: {e}")
    
    def show(self):
        """Show the main window"""
        super().show()
    
    def delete_selected_items(self):
        """Delete all selected items from both UI and project data"""
        tree = self.project_browser.asset_tree
        selected_items = tree.selectedItems()
        
        if not selected_items:
            return
        
        # Confirm deletion
        item_names = [item.text(0) for item in selected_items]
        item_list = "\n".join(f"• {name}" for name in item_names)
        
        reply = QMessageBox.question(
            self, 
            "Delete Selected Items", 
            f"Are you sure you want to delete the following {len(selected_items)} items?\n\n{item_list}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from project data first
            if self.manager.current_project:
                for item in selected_items:
                    item_name = item.text(0)
                    item_type = item.data(0, Qt.ItemDataRole.UserRole)
                    
                    if item_type == "Asset":
                        # Remove from assets list
                        self.manager.current_project.assets = [
                            asset for asset in self.manager.current_project.assets 
                            if asset.name != item_name
                        ]
                        # Remove from folders
                        if hasattr(self.manager.current_project, 'folders'):
                            for folder in self.manager.current_project.folders:
                                if folder.type == "asset" and hasattr(folder, 'assets'):
                                    folder.assets = [a for a in folder.assets if a != item_name]
                    elif item_type == "Folder":
                        # Remove folder from project
                        if hasattr(self.manager.current_project, 'folders'):
                            self.manager.current_project.folders = [
                                folder for folder in self.manager.current_project.folders 
                                if folder.name != item_name
                            ]
                
                # Save project to file
                try:
                    self.manager.save_project()
                    self.logger.info(f"Deleted {len(selected_items)} items and saved project")
                except Exception as e:
                    self.logger.error(f"Failed to save project after bulk deletion: {e}")
                    QMessageBox.warning(self, "Save Error", f"Items deleted from UI but failed to save project: {e}")
            
            # Delete items from UI (in reverse order to avoid index issues)
            for item in reversed(selected_items):
                parent = item.parent()
                if parent:
                    parent.removeChild(item)
                else:
                    tree.takeTopLevelItem(tree.indexOfTopLevelItem(item))
            
            self.logger.info(f"Deleted {len(selected_items)} selected items")
    
    def copy_selected_items(self):
        """Copy all selected items to clipboard"""
        tree = self.project_browser.asset_tree
        selected_items = tree.selectedItems()
        
        if not selected_items:
            return
        
        # Store multiple items in clipboard
        self.clipboard_items = selected_items
        self.clipboard_operation = "copy"
        self.clipboard_type = "multiple"
        
        self.logger.info(f"Copied {len(selected_items)} items to clipboard")
    
    def cut_selected_items(self):
        """Cut all selected items to clipboard"""
        tree = self.project_browser.asset_tree
        selected_items = tree.selectedItems()
        
        if not selected_items:
            return
        
        # Store multiple items in clipboard
        self.clipboard_items = selected_items
        self.clipboard_operation = "cut"
        self.clipboard_type = "multiple"
        
        self.logger.info(f"Cut {len(selected_items)} items to clipboard")
    
    def add_shot_to_folder(self, folder_item):
        """Add new shot to folder"""
        name, ok = QInputDialog.getText(self, "New Shot", "Shot name:")
        if ok and name:
            shot_item = QTreeWidgetItem(folder_item)
            shot_item.setText(0, name)
            shot_item.setData(0, Qt.ItemDataRole.UserRole, "Shot")
    
    def add_shot_subfolder(self, parent_item):
        """Add new shot subfolder"""
        name, ok = QInputDialog.getText(self, "New Subfolder", "Folder name:")
        if ok and name:
            folder_item = QTreeWidgetItem(parent_item)
            folder_item.setText(0, name)
            folder_item.setData(0, Qt.ItemDataRole.UserRole, "Folder")
    
    def delete_selected_shot_items(self):
        """Delete all selected shot items from both UI and project data"""
        tree = self.project_browser.shot_tree
        selected_items = tree.selectedItems()
        
        if not selected_items:
            return
        
        # Confirm deletion
        item_names = [item.text(0) for item in selected_items]
        item_list = "\n".join(f"• {name}" for name in item_names)
        
        reply = QMessageBox.question(
            self, 
            "Delete Selected Items", 
            f"Are you sure you want to delete the following {len(selected_items)} items?\n\n{item_list}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from project data first
            if self.manager.current_project:
                for item in selected_items:
                    item_name = item.text(0)
                    item_type = item.data(0, Qt.ItemDataRole.UserRole)
                    
                    if item_type == "Shot":
                        # Remove from shots list
                        self.manager.current_project.shots = [
                            shot for shot in self.manager.current_project.shots 
                            if shot.name != item_name
                        ]
                        # Remove from folders
                        if hasattr(self.manager.current_project, 'folders'):
                            for folder in self.manager.current_project.folders:
                                if folder.type == "shot" and hasattr(folder, 'shots'):
                                    folder.shots = [s for s in folder.shots if s != item_name]
                    elif item_type == "Folder":
                        # Remove folder from project
                        if hasattr(self.manager.current_project, 'folders'):
                            self.manager.current_project.folders = [
                                folder for folder in self.manager.current_project.folders 
                                if folder.name != item_name
                            ]
                
                # Save project to file
                try:
                    self.manager.save_project()
                    self.logger.info(f"Deleted {len(selected_items)} shot items and saved project")
                except Exception as e:
                    self.logger.error(f"Failed to save project after shot deletion: {e}")
                    QMessageBox.warning(self, "Save Error", f"Items deleted from UI but failed to save project: {e}")
            
            # Delete items from UI (in reverse order to avoid index issues)
            for item in reversed(selected_items):
                parent = item.parent()
                if parent:
                    parent.removeChild(item)
                else:
                    tree.takeTopLevelItem(tree.indexOfTopLevelItem(item))
            
            self.logger.info(f"Deleted {len(selected_items)} selected shot items")
    
    def copy_selected_shot_items(self):
        """Copy all selected shot items to clipboard"""
        tree = self.project_browser.shot_tree
        selected_items = tree.selectedItems()
        
        if not selected_items:
            return
        
        # Store multiple items in clipboard
        self.clipboard_items = selected_items
        self.clipboard_operation = "copy"
        self.clipboard_type = "multiple"
        
        self.logger.info(f"Copied {len(selected_items)} shot items to clipboard")
    
    def cut_selected_shot_items(self):
        """Cut all selected shot items to clipboard"""
        tree = self.project_browser.shot_tree
        selected_items = tree.selectedItems()
        
        if not selected_items:
            return
        
        # Store multiple items in clipboard
        self.clipboard_items = selected_items
        self.clipboard_operation = "cut"
        self.clipboard_type = "multiple"
        
        self.logger.info(f"Cut {len(selected_items)} shot items to clipboard")
