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
        self.clipboard_operation = None  # 'cut' or 'copy'
        self.clipboard_type = None  # 'asset' or 'shot'
        
        # Connect signals after UI is set up
        self.setup_connections()
        
        # Setup asset tree context menu
        self.setup_asset_tree_context_menu()
        
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
    
    def show_asset_context_menu(self, position):
        """Show context menu for asset tree"""
        tree = self.project_browser.asset_tree
        item = tree.itemAt(position)
        if not item:
            return
        
        menu = QMenu(tree)
        
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
        """Delete item"""
        reply = QMessageBox.question(self, "Delete Item", 
                                   f"Delete '{item.text(0)}'?", 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                tree = self.project_browser.asset_tree
                tree.takeTopLevelItem(tree.indexOfTopLevelItem(item))
    
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
            if recent_projects:
                # Load the most recent project
                last_project = recent_projects[0]
                project_path = last_project['path']
                if os.path.exists(project_path):
                    self.logger.info(f"Auto-loading last project: {last_project['name']} from {project_path}")
                    self.manager.load_project(project_path)
                    self.update_assets_tree()
                    self.setWindowTitle(f"Vogue Manager - {self.manager.current_project.name}")
                    self.logger.info("Project loaded successfully")
                else:
                    self.logger.info("Last project path no longer exists")
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
        """Copy selected item"""
        tree = self.project_browser.asset_tree
        current_item = tree.currentItem()
        if current_item:
            self.copy_item(current_item)
    
    def cut_selected_item(self):
        """Cut selected item"""
        tree = self.project_browser.asset_tree
        current_item = tree.currentItem()
        if current_item:
            self.cut_item(current_item)
    
    def paste_to_selected_item(self):
        """Paste to selected item"""
        tree = self.project_browser.asset_tree
        current_item = tree.currentItem()
        if current_item:
            self.paste_item(current_item)
    
    def delete_selected_item(self):
        """Delete selected item"""
        tree = self.project_browser.asset_tree
        current_item = tree.currentItem()
        if current_item:
            self.delete_item(current_item)
    
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
