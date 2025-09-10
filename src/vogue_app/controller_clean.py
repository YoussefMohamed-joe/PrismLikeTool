# Clean controller implementation for asset tree
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
