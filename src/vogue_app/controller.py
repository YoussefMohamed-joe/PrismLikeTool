# Clean controller implementation for asset tree
import os
from pathlib import Path
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
from PyQt6.QtGui import QFont, QBrush, QColor, QIcon, QPixmap, QPainter, QPen

from vogue_core.manager import ProjectManager
from vogue_core.logging_utils import get_logger
from vogue_core.settings import settings
from vogue_app.ui import PrismMainWindow
from vogue_app.dialogs import AssetDialog

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
        
        # Setup thumbnail preview integration
        self.setup_thumbnail_integration()
        
        # Setup asset tree context menu
        self.setup_asset_tree_context_menu()
        
        # Setup shot tree context menu
        self.setup_shot_tree_context_menu()
        
        # Setup task and department context menus
        self.setup_task_context_menu()
        self.setup_department_context_menu()
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()

        # Setup tree widgets FIRST (before loading project)
        QTimer.singleShot(100, self._setup_tree_widgets)

        # Auto-load last opened project AFTER tree setup
        QTimer.singleShot(200, self._auto_load_last_project)
    
    def create_default_asset_icon(self, width, height):
        """Create a default asset placeholder icon with dark stripes and dashed border"""
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(40, 40, 40))  # Dark background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw diagonal stripes
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        stripe_spacing = 8
        for i in range(-height, width + height, stripe_spacing):
            painter.drawLine(i, 0, i + height, height)
        
        # Draw dashed border
        pen = QPen(QColor(100, 100, 100), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawRect(2, 2, width - 4, height - 4)
        
        # Draw "ASSET" text in center
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "ASSET")
        
        painter.end()
        return pixmap
    
    def get_asset_icon(self, asset, size=120):
        """Get asset icon - custom image if available, otherwise default placeholder"""
        # Check if asset has a custom image path
        if hasattr(asset, 'meta') and asset.meta.get('image_path'):
            image_path = asset.meta['image_path']
            if os.path.exists(image_path):
                try:
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        # Scale to desired size
                        return pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                except Exception as e:
                    self.logger.warning(f"Failed to load asset image {image_path}: {e}")
        
        # Return default placeholder
        return self.create_default_asset_icon(size, size)

    def update_assets_tree(self):
        """Simple asset tree update with icons"""
        tree = self.project_browser.asset_tree
        tree.clear()
        
        if not self.manager.current_project:
            placeholder_item = QTreeWidgetItem(tree)
            placeholder_item.setText(0, "No project loaded")
            return

        # Create icons with different sizes
        folder_icon = self.style().standardIcon(self.style().StandardPixmap.SP_DirOpenIcon)
        
        # Scale folder icon to be smaller
        folder_icon = folder_icon.pixmap(24, 24)
        
        # Create default asset placeholder image (dark striped with dashed border) - much bigger for picture preview
        default_asset_icon = self.create_default_asset_icon(120, 120)
        
        # Add folders
        if hasattr(self.manager.current_project, 'folders') and self.manager.current_project.folders:
            for folder in self.manager.current_project.folders:
                if folder.type == "asset":
                    folder_item = QTreeWidgetItem(tree)
                    folder_item.setText(0, folder.name)
                    folder_item.setIcon(0, QIcon(folder_icon))
                    folder_item.setData(0, Qt.ItemDataRole.UserRole, "Folder")
                    
                    # Add assets to folder
                    if hasattr(folder, 'assets') and folder.assets:
                        for asset_name in folder.assets:
                            # Find the actual asset object to get custom icon
                            asset_obj = next((a for a in self.manager.current_project.assets if a.name == asset_name), None)
                            asset_icon = self.get_asset_icon(asset_obj) if asset_obj else default_asset_icon
                            
                            asset_item = QTreeWidgetItem(folder_item)
                            asset_item.setText(0, asset_name)
                            asset_item.setIcon(0, QIcon(asset_icon))
                            asset_item.setData(0, Qt.ItemDataRole.UserRole, "Asset")
        
        # Add unassigned assets
        assigned_assets = set()
        if hasattr(self.manager.current_project, 'folders') and self.manager.current_project.folders:
            for folder in self.manager.current_project.folders:
                if folder.type == "asset" and hasattr(folder, 'assets') and folder.assets:
                    assigned_assets.update(folder.assets)
        
        for asset in self.manager.current_project.assets:
            if asset.name not in assigned_assets:
                # Get custom icon for this asset
                asset_icon = self.get_asset_icon(asset)
                
                asset_item = QTreeWidgetItem(tree)
                asset_item.setText(0, asset.name)
                asset_item.setIcon(0, QIcon(asset_icon))
                asset_item.setData(0, Qt.ItemDataRole.UserRole, "Asset")
        
        # Set much larger row height to accommodate bigger icons for picture preview
        tree.setIconSize(QSize(120, 120))
        tree.setIndentation(20)  # More indentation for better visual hierarchy
        
        # Set larger font for better readability with bigger images (like Prism)
        font = tree.font()
        font.setPointSize(14)  # Even larger font size for bigger images
        tree.setFont(font)
        
        tree.expandAll()
        self.logger.info(f"Updated assets tree with {tree.topLevelItemCount()} items")
    
    def update_shots_tree(self):
        """Update shots tree with icons"""
        tree = self.project_browser.shot_tree
        tree.clear()
        
        if not self.manager.current_project:
            placeholder_item = QTreeWidgetItem(tree)
            placeholder_item.setText(0, "No project loaded")
            return

        # Create icons with different sizes - much bigger for shots like assets
        folder_icon = self.style().standardIcon(self.style().StandardPixmap.SP_DirOpenIcon)
        shot_icon = self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay)
        
        # Scale folder icon to be smaller, shot icon much bigger like assets
        folder_icon = folder_icon.pixmap(24, 24)
        shot_icon = shot_icon.pixmap(120, 120)  # Much bigger like assets
        
        # Add shot folders
        if hasattr(self.manager.current_project, 'folders') and self.manager.current_project.folders:
            for folder in self.manager.current_project.folders:
                if folder.type == "shot":
                    folder_item = QTreeWidgetItem(tree)
                    folder_item.setText(0, folder.name)
                    folder_item.setIcon(0, QIcon(folder_icon))
                    folder_item.setData(0, Qt.ItemDataRole.UserRole, "Folder")
                    
                    # Add shots to folder
                    if hasattr(folder, 'assets') and folder.assets:
                        for shot_name in folder.assets:
                            shot_item = QTreeWidgetItem(folder_item)
                            shot_item.setText(0, shot_name)  # Just the shot name, not sequence/shot
                            shot_item.setIcon(0, QIcon(shot_icon))
                            shot_item.setData(0, Qt.ItemDataRole.UserRole, "Shot")
        
        # Add unassigned shots (shots not in any folder)
        assigned_shots = set()
        if hasattr(self.manager.current_project, 'folders') and self.manager.current_project.folders:
            for folder in self.manager.current_project.folders:
                if folder.type == "shot" and hasattr(folder, 'assets') and folder.assets:
                    assigned_shots.update(folder.assets)
        
        # Display all shots - either in folders or as unassigned
        if hasattr(self.manager.current_project, 'shots') and self.manager.current_project.shots:
            for shot in self.manager.current_project.shots:
                # Check if this shot is already in a folder
                if shot.name not in assigned_shots:
                    # Display as unassigned shot
                    shot_item = QTreeWidgetItem(tree)
                    shot_item.setText(0, shot.name)  # Just the shot name, not sequence/shot
                    shot_item.setIcon(0, QIcon(shot_icon))
                    shot_item.setData(0, Qt.ItemDataRole.UserRole, "Shot")
        
        # Set much larger row height to accommodate bigger icons like assets
        tree.setIconSize(QSize(120, 120))
        tree.setIndentation(20)  # More indentation for better visual hierarchy
        
        # Set larger font for better readability with bigger images (like Prism)
        font = tree.font()
        font.setPointSize(14)  # Even larger font size for bigger images
        tree.setFont(font)
        
        tree.expandAll()
        self.logger.info(f"Updated shots tree with {tree.topLevelItemCount()} items")
    
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
    
    def setup_task_context_menu(self):
        """Setup context menu for task list"""
        task_list = self.project_browser.tasks_list
        task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        task_list.customContextMenuRequested.connect(self.show_task_context_menu)
    
    def setup_department_context_menu(self):
        """Setup context menu for department list"""
        dept_list = self.project_browser.departments_list
        dept_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        dept_list.customContextMenuRequested.connect(self.show_department_context_menu)
    
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
                menu.addAction("Properties...", lambda: self.show_asset_properties(item))
                menu.addSeparator()
                # Department management
                dept_menu = menu.addMenu("Manage Departments")
                dept_menu.addAction("Add Department...", lambda: self.add_department_to_entity(item))
                dept_menu.addAction("Remove Department...", lambda: self.remove_department_from_entity(item))
                menu.addSeparator()
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
    
    def show_asset_properties(self, item):
        """Show asset properties dialog"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Load or create a project first.")
            return
            
        # Find the asset object
        asset_name = item.text(0)
        asset = next((a for a in self.manager.current_project.assets if a.name == asset_name), None)
        
        if not asset:
            QMessageBox.warning(self, "Asset Not Found", f"Could not find asset: {asset_name}")
            return

        # Create and show properties dialog
        from vogue_app.dialogs import AssetPropertiesDialog
        dialog = AssetPropertiesDialog(self, asset)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update the asset with new properties
            data = dialog.get_asset_data()
            if data:
                # Update asset properties
                if data.get('description'):
                    asset.meta['description'] = data['description']
                if data.get('image_path'):
                    asset.meta['image_path'] = data['image_path']
                if data.get('meta'):
                    asset.meta.update(data['meta'])
                
                # Save project
                try:
                    self.manager.save_project()
                    self.update_assets_tree()  # Refresh the tree
                    self.logger.info(f"Updated asset properties: {asset_name}")
                except Exception as e:
                    QMessageBox.warning(self, "Save Error", f"Failed to save asset properties: {e}")
    
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
                menu.addAction("Properties...", lambda: self.show_shot_properties(item))
                menu.addSeparator()
                # Department management
                dept_menu = menu.addMenu("Manage Departments")
                dept_menu.addAction("Add Department...", lambda: self.add_department_to_entity(item))
                dept_menu.addAction("Remove Department...", lambda: self.remove_department_from_entity(item))
                menu.addSeparator()
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
    
    def show_task_context_menu(self, position):
        """Show context menu for task list"""
        task_list = self.project_browser.tasks_list
        item = task_list.itemAt(position)
        
        menu = QMenu(task_list)
        
        # Always show New Task option
        menu.addAction("New Task", self.new_task)
        menu.addSeparator()
        
        if item:
            # Task is selected
            menu.addAction("Assign Task", self.assign_task)
            menu.addAction("Complete Task", self.complete_task)
            menu.addSeparator()
            menu.addAction("Delete Task", self.delete_task)
        else:
            # No task selected
            menu.addAction("Assign Task", self.assign_task).setEnabled(False)
            menu.addAction("Complete Task", self.complete_task).setEnabled(False)
            menu.addAction("Delete Task", self.delete_task).setEnabled(False)
        
        menu.exec(task_list.mapToGlobal(position))
    
    def show_department_context_menu(self, position):
        """Show context menu for department list"""
        dept_list = self.project_browser.departments_list
        item = dept_list.itemAt(position)
        
        menu = QMenu(dept_list)
        
        # Check if we have a selected entity
        if self.project_browser.current_entity and self.project_browser.current_entity_type:
            # We have an entity selected, show department management options
            menu.addAction("Add Department...", self.add_department_to_current_entity)
            menu.addSeparator()
            
            if item:
                # Department is selected
                menu.addAction("Edit Department...", lambda: self.edit_department_from_current_entity(item))
                menu.addAction("Remove Department", lambda: self.remove_department_from_current_entity(item))
                
                # Multi-select options
                selected_items = dept_list.selectedItems()
                if len(selected_items) > 1:
                    menu.addSeparator()
                    menu.addAction(f"Remove Selected ({len(selected_items)})", 
                                 lambda: self.remove_selected_departments_from_current_entity())
            else:
                # No department selected
                menu.addAction("Edit Department...", self.edit_department_from_current_entity).setEnabled(False)
                menu.addAction("Remove Department", self.remove_department_from_current_entity).setEnabled(False)
        else:
            # No entity selected
            menu.addAction("No asset or shot selected")
            menu.addAction("Select an asset or shot to manage departments").setEnabled(False)
        
        menu.exec(dept_list.mapToGlobal(position))
    
    def show_shot_properties(self, item):
        """Show shot properties dialog"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Load or create a project first.")
            return

        # Find the shot object
        shot_name = item.text(0)
        shot = next((s for s in self.manager.current_project.shots if s.name == shot_name), None)
        
        if not shot:
            QMessageBox.warning(self, "Shot Not Found", f"Could not find shot: {shot_name}")
            return
        
        # Create and show properties dialog
        from vogue_app.dialogs import ShotPropertiesDialog
        dialog = ShotPropertiesDialog(self, shot)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update the shot with new properties
            data = dialog.get_shot_data()
            if data:
                # Update shot properties
                if data.get('description'):
                    shot.meta['description'] = data['description']
                if data.get('image_path'):
                    shot.meta['image_path'] = data['image_path']
                if data.get('meta'):
                    shot.meta.update(data['meta'])
                
                # Save project
                try:
                    self.manager.save_project()
                    self.update_shots_tree()  # Refresh the tree
                    self.logger.info(f"Updated shot properties: {shot_name}")
                except Exception as e:
                    QMessageBox.warning(self, "Save Error", f"Failed to save shot properties: {e}")
    
    def add_asset_to_folder(self, folder_item):
        """Open AssetDialog with preselected folder and add asset"""
        folder_name = folder_item.text(0)
        self.add_asset(preselected_folder=folder_name)
    
    def add_subfolder(self, parent_item):
        """Add new subfolder"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Load or create a project first.")
            return

        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            # Ensure folders container
            project = self.manager.current_project
            if not hasattr(project, 'folders') or project.folders is None:
                project.folders = []

            # Check if folder already exists
            existing = next((f for f in project.folders if f.name == name and f.type == "asset"), None)
            if existing:
                QMessageBox.warning(self, "Folder Exists", f"Folder '{name}' already exists.")
                return

            from vogue_core.models import Folder
            new_folder = Folder(name=name.strip(), type="asset", assets=[])
            project.folders.append(new_folder)
            
            # Save project immediately
            try:
                self.manager.save_project()
                self.logger.info(f"Added folder: {name.strip()} and saved project")
            except Exception as e:
                self.logger.error(f"Failed saving project after folder add: {e}")
                QMessageBox.warning(self, "Save Error", f"Folder added but failed to save project: {e}")
                return

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
                            if folder.type == "shot" and hasattr(folder, 'assets'):
                                folder.assets = [s for s in folder.assets if s != item_name]
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
        
        # Connect shot button signals
        self.project_browser.add_shot_btn.clicked.connect(self.add_shot)
        self.project_browser.new_shot_folder_btn.clicked.connect(self.add_shot_folder)
        self.project_browser.refresh_shots_btn.clicked.connect(self.update_shots_tree)
        
        # Connect department selection change
        self.project_browser.departments_list.itemSelectionChanged.connect(self.on_department_selection_changed)
        
        # Connect task selection change
        self.project_browser.tasks_list.itemSelectionChanged.connect(self.on_task_selection_changed)
        
        # Connect focus events to maintain selection
        self.project_browser.departments_list.focusOutEvent = self.department_list_focus_out
        self.project_browser.departments_list.focusInEvent = self.department_list_focus_in
        
        # Override mouse press event to maintain selection
        self.project_browser.departments_list.mousePressEvent = self.department_list_mouse_press
        
        # Setup timer to periodically check and maintain selection
        self.selection_timer = QTimer()
        self.selection_timer.timeout.connect(self.maintain_selection)
        self.selection_timer.start(1000)  # Check every second
        
        # Ensure department selection persists (don't deselect when clicking elsewhere)
        self.project_browser.departments_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.project_browser.departments_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
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
                    self.update_shots_tree()
                    self.setWindowTitle(f"Vogue Manager - {self.manager.current_project.name}")
                    self.update_project_info()
                    self.load_tasks_from_project()
                    self.load_departments_from_project()
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
                            self.update_project_info()
                            self.load_tasks_from_project()
                            self.load_departments_from_project()
                            self.logger.info("Project loaded successfully")
                            break
            else:
                self.logger.info("No recent projects to load")
        except Exception as e:
            self.logger.error(f"Failed to auto-load last project: {e}")
    
    def add_asset(self, preselected_folder: str | None = None):
        """Open AssetDialog and add asset to project and JSON"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Load or create a project first.")
            return
            
        dialog = AssetDialog(self)
        if preselected_folder:
            idx = dialog.folder_combo.findText(preselected_folder)
            if idx >= 0:
                dialog.folder_combo.setCurrentIndex(idx)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_asset_data()
            if not data:
                QMessageBox.warning(self, "Invalid Data", "Please enter a valid asset name.")
                return
            
            from vogue_core.models import Asset
            project = self.manager.current_project

            # Ensure folders container
            if not hasattr(project, 'folders') or project.folders is None:
                project.folders = []

            # Handle folder selection - "Main" means root level, not a folder
            folder_name = data["folder"].strip() if data.get("folder") else "Main"
            folder = None
            if folder_name and folder_name != "Main":
                # Find existing folder or create new one
                for f in project.folders:
                    if f.type == "asset" and f.name == folder_name:
                        folder = f
                        break
                if folder is None:
                    from vogue_core.models import Folder
                    folder = Folder(name=folder_name, type="asset", assets=[])
                    project.folders.append(folder)

            # Create asset and append to project assets list if not exists
            existing = next((a for a in getattr(project, 'assets', []) if a.name == data['name']), None)
            if existing is None:
                if not hasattr(project, 'assets') or project.assets is None:
                    project.assets = []
                # Asset model requires 'type' parameter, use folder name as type or default
                asset_type = folder_name if folder_name != "Main" else "Props"
                asset = Asset(name=data['name'], type=asset_type)
                # Store description in meta
                if data.get('description'):
                    asset.meta['description'] = data['description']
                # Store image path in meta
                if data.get('image_path'):
                    asset.meta['image_path'] = data['image_path']
                # Attach other meta data
                if hasattr(asset, 'meta') and isinstance(asset.meta, dict):
                    asset.meta.update(data.get('meta', {}))
                project.assets.append(asset)

            # Add to folder list (string names)
            if folder_name != "Main" and folder is not None:
                if not hasattr(folder, 'assets') or folder.assets is None:
                    folder.assets = []
                if data['name'] not in folder.assets:
                    folder.assets.append(data['name'])

            # Persist to JSON
            try:
                self.manager.save_project()
            except Exception as e:
                self.logger.error(f"Failed saving project after asset add: {e}")
                QMessageBox.warning(self, "Save Error", f"Asset added but failed to save project: {e}")

            # Refresh UI
            self.update_assets_tree()
            if folder_name == "Main":
                self.logger.info(f"Added asset: {data['name']} to root level")
            else:
                self.logger.info(f"Added asset: {data['name']} to folder: {folder_name}")
    
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
                self.manager.save_project()  # Save to JSON
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
        
        # Task and department actions now handled via right-click context menus
        
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
        from .dialogs import NewProjectDialog
        from PyQt6.QtWidgets import QDialog
        
        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            project_data = dialog.get_project_data()
            if project_data:
                self.create_new_project(project_data)
    
    def create_new_project(self, project_data):
        """Create a new project from dialog data"""
        try:
            self.logger.info(f"Creating new project: {project_data['name']}")
            
            # Create project using manager
            self.manager.create_project(
                project_data['name'],
                str(project_data['path']),
                fps=project_data['fps'],
                resolution=project_data['resolution']
            )
            
            # Load the new project
            project_path = project_data['path'] / project_data['name']
            self.load_project(str(project_path))
            
            self.logger.info(f"Created new project: {project_data['name']}")
            
        except Exception as e:
            self.logger.error(f"Failed to create project: {e}")
            from PyQt6.QtWidgets import QMessageBox
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
            self.update_shots_tree()
            self.setWindowTitle(f"Vogue Manager - {self.manager.current_project.name}")
            
            # Update project info display
            self.update_project_info()
            
            # Clear current entity selection and departments
            self.project_browser.current_entity = None
            self.project_browser.current_entity_type = None
            self.project_browser.departments_list.clear()
            
            # Load tasks and departments from project data
            self.load_tasks_from_project()
            self.load_departments_from_project()
            
            # Add to recent projects
            settings.add_recent_project(self.manager.current_project.name, project_path)
            
            self.logger.info(f"Loaded project: {self.manager.current_project.name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project: {e}")
    
    def update_project_info(self):
        """Update the project info display"""
        if self.manager.current_project:
            # Update project name and path labels (they're direct attributes of project_browser)
            if hasattr(self.project_browser, 'project_name_label'):
                self.project_browser.project_name_label.setText(f"Project: {self.manager.current_project.name}")
            
            if hasattr(self.project_browser, 'project_path_label'):
                self.project_browser.project_path_label.setText(f"Path: {self.manager.current_project.path}")
            
            # Update status menu
            if hasattr(self, 'project_status_action'):
                self.project_status_action.setText(f"Project: {self.manager.current_project.name}")
                self.project_status_action.setEnabled(True)
            
            self.logger.info(f"Updated project info display: {self.manager.current_project.name}")
        else:
            # No project loaded
            if hasattr(self.project_browser, 'project_name_label'):
                self.project_browser.project_name_label.setText("Project: No Project Loaded")
            
            if hasattr(self.project_browser, 'project_path_label'):
                self.project_browser.project_path_label.setText("Path: Not Available")
            
            if hasattr(self, 'project_status_action'):
                self.project_status_action.setText("Project: No project loaded")
                self.project_status_action.setEnabled(False)
    
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
        """Add new shot to folder with preselected folder"""
        folder_name = folder_item.text(0)
        self.add_shot(preselected_folder=folder_name)
    
    def add_shot(self, preselected_folder=None):
        """Add a new shot with folder selection"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Load or create a project first.")
            return
        
        from vogue_app.dialogs import ShotDialog
        dialog = ShotDialog(self, preselected_folder=preselected_folder, manager=self.manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_shot_data()
            if data:
                self.create_shot(data)
    
    def create_shot(self, data):
        """Create a new shot"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Load or create a project first.")
            return
        
        try:
            project = self.manager.current_project
            
            # Handle folder/sequence relationship
            sequence_name = data["sequence"].strip()
            folder_name = data["folder"].strip() if data.get("folder") else "Main"
            
            folder = None
            
            # If user typed a new sequence name, create a new folder for it
            if sequence_name and sequence_name != "Main":
                # Check if this sequence already exists as a folder
                for f in project.folders:
                    if f.type == "shot" and f.name == sequence_name:
                        folder = f
                        break
                
                if not folder:
                    # Create new folder for this sequence
                    from vogue_core.models import Folder
                    folder = Folder(name=sequence_name, type="shot", assets=[])
                    project.folders.append(folder)
            else:
                # Use selected folder or Main (no folder)
                if folder_name and folder_name != "Main":
                    for f in project.folders:
                        if f.type == "shot" and f.name == folder_name:
                            folder = f
                            break
            
            # Create shot object
            from vogue_core.models import Shot
            shot = Shot(
                name=data['name'],
                sequence=data['sequence'],
                path=str(Path(project.path) / "02_Shots" / data['sequence'] / data['name']),
                meta=data['meta'].copy()
            )
            
            # Add description to meta if provided
            if data.get('description'):
                shot.meta['description'] = data['description']
            
            # Add image path to meta if provided
            if data.get('image_path'):
                shot.meta['image_path'] = data['image_path']
            
            # Add to project shots list
            if not hasattr(project, 'shots') or project.shots is None:
                project.shots = []
            project.shots.append(shot)
            
            # Add to folder if not "Main"
            if folder:
                if not hasattr(folder, 'assets') or folder.assets is None:
                    folder.assets = []
                if data['name'] not in folder.assets:
                    folder.assets.append(data['name'])
            
            # Persist to JSON
            try:
                self.manager.save_project()
            except Exception as e:
                self.logger.error(f"Failed saving project after shot add: {e}")
                QMessageBox.warning(self, "Save Error", f"Shot added but failed to save project: {e}")

            # Refresh UI
            self.update_shots_tree()
            if folder:
                self.logger.info(f"Added shot: {data['name']} to folder: {folder.name}")
            else:
                self.logger.info(f"Added shot: {data['name']} to root level")
            
            # Update sequence dropdown in any open dialogs
            self.refresh_shot_dialogs()
            
        except Exception as e:
            self.logger.error(f"Failed to create shot: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create shot: {e}")
    
    def refresh_shot_dialogs(self):
        """Refresh sequence dropdowns in any open shot dialogs"""
        # Find any open ShotDialog instances and refresh their sequence dropdowns
        for widget in self.findChildren(QWidget):
            if hasattr(widget, 'populate_sequences') and hasattr(widget, 'sequence_combo'):
                widget.populate_sequences()
    
    def add_shot_folder(self):
        """Add new shot folder"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Load or create a project first.")
            return

        name, ok = QInputDialog.getText(self, "New Shot Folder", "Folder name:")
        if ok and name:
            try:
                project = self.manager.current_project
                
                # Check if folder already exists
                existing_folder = next((f for f in project.folders if f.name == name.strip() and f.type == "shot"), None)
                if existing_folder:
                    QMessageBox.warning(self, "Folder Exists", f"Shot folder '{name.strip()}' already exists.")
                    return

                # Create new shot folder
                from vogue_core.models import Folder
                new_folder = Folder(name=name.strip(), type="shot", assets=[])
                project.folders.append(new_folder)
                
                # Save project immediately
                try:
                    self.manager.save_project()
                    self.logger.info(f"Added shot folder: {name.strip()} and saved project")
                except Exception as e:
                    self.logger.error(f"Failed saving project after shot folder add: {e}")
                    QMessageBox.warning(self, "Save Error", f"Shot folder added but failed to save project: {e}")
                
                # Refresh UI
                self.update_shots_tree()
                self.logger.info(f"Added shot folder: {name.strip()}")
                
            except Exception as e:
                self.logger.error(f"Failed to create shot folder: {e}")
                QMessageBox.critical(self, "Error", f"Failed to create shot folder: {e}")
    
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
                                if folder.type == "shot" and hasattr(folder, 'assets'):
                                    folder.assets = [s for s in folder.assets if s != item_name]
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
    
    # Task Management Methods
    def new_task(self):
        """Create a new task"""
        from vogue_app.dialogs import CreateTaskDialog
        
        # Check if an entity is selected
        if not self.project_browser.current_entity or not self.project_browser.current_entity_type:
            QMessageBox.warning(self, "No Entity Selected", 
                              "Please select an asset or shot first before creating tasks.\nTasks are specific to the selected entity.")
            return
        
        # Check if there are departments available for the selected entity
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Load or create a project first.")
            return
        
        # Get departments for the current entity
        entity_departments = []
        if self.project_browser.current_entity_type == "Asset":
            asset = self.manager.current_project.get_asset(self.project_browser.current_entity)
            if asset:
                entity_departments = asset.departments
        elif self.project_browser.current_entity_type == "Shot":
            if "/" in self.project_browser.current_entity:
                sequence, name = self.project_browser.current_entity.split("/", 1)
                shot = self.manager.current_project.get_shot(sequence, name)
                if shot:
                    entity_departments = shot.departments
        
        if not entity_departments:
            QMessageBox.warning(self, "No Departments", 
                              f"The selected {self.project_browser.current_entity_type.lower()} '{self.project_browser.current_entity}' has no departments.\nPlease add departments first before creating tasks.")
            return

        dialog = CreateTaskDialog(self, entity_departments=entity_departments)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_task_data()
            if data:
                # Add task to the tasks list
                task_text = f"{data['name']} - {data['status']}"
                if data['description']:
                    task_text += f" ({data['description']})"
                
                self.project_browser.tasks_list.addItem(task_text)
                
                # Save to project data
                if self.manager.current_project:
                    if not hasattr(self.manager.current_project, 'tasks'):
                        self.manager.current_project.tasks = []
                    
                    # Add task object to project with entity association
                    from vogue_core.models import Task
                    task = Task(
                        name=data['name'],
                        department=data['department'],
                        status=data['status'],
                        description=data['description'],
                        entity=self.project_browser.current_entity,
                        entity_type=self.project_browser.current_entity_type
                    )
                    self.manager.current_project.tasks.append(task)
                    self.manager.save_project()
                
                # Ensure department selection is maintained after task creation
                self.ensure_department_selection_visible()
                self.filter_tasks_by_department()
                
                self.logger.info(f"Created new task: {data['name']} in department: {data['department']} for {self.project_browser.current_entity_type.lower()}: {self.project_browser.current_entity}")

    def assign_task(self):
        """Assign selected task"""
        current_item = self.project_browser.tasks_list.currentItem()
        if current_item:
            task_name = current_item.text().split(" - ")[0]
            QMessageBox.information(self, "Task Assignment", f"Task '{task_name}' assigned successfully!")
            self.logger.info(f"Assigned task: {task_name}")
            # Ensure department selection is maintained
            self.ensure_department_selection_visible()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a task to assign.")

    def complete_task(self):
        """Mark selected task as complete"""
        current_item = self.project_browser.tasks_list.currentItem()
        if current_item:
            task_text = current_item.text()
            # Extract task name consistently
            task_name = task_text.split(" - ")[0] if " - " in task_text else task_text
            if " - Complete" not in task_text:
                # Update task status to complete (UI label)
                new_text = f"{task_name} - Complete"
                
                current_item.setText(new_text)
                self.logger.info(f"Completed task: {task_name}")
                # Ensure department selection is maintained
                self.ensure_department_selection_visible()

                # Persist task status change to project and update related versions
                try:
                    if self.manager.current_project:
                        # Update task object in project if present
                        if hasattr(self.manager.current_project, 'tasks') and self.manager.current_project.tasks:
                            updated_any = False
                            for idx, t in enumerate(self.manager.current_project.tasks):
                                # Support both object and dict storage
                                if hasattr(t, 'name'):
                                    match = (
                                        t.name == task_name and
                                        getattr(t, 'entity', None) == self.project_browser.current_entity and
                                        getattr(t, 'entity_type', None) == self.project_browser.current_entity_type
                                    )
                                    if match:
                                        t.status = 'Complete'
                                        updated_any = True
                                elif isinstance(t, dict):
                                    match = (
                                        t.get('name') == task_name and
                                        t.get('entity') == self.project_browser.current_entity and
                                        t.get('entity_type') == self.project_browser.current_entity_type
                                    )
                                    if match:
                                        t['status'] = 'Complete'
                                        self.manager.current_project.tasks[idx] = t
                                        updated_any = True
                        # Update versions that belong to this task
                        entity_key = self.project_browser.current_entity
                        versions = self.manager.current_project.get_versions(entity_key)
                        for v in versions:
                            if getattr(v, 'task_name', '') == task_name:
                                setattr(v, 'status', 'Complete')
                        # Save
                        self.manager.save_project()
                        # Refresh versions UI if available
                        if hasattr(self, 'version_manager') and self.version_manager:
                            try:
                                self.version_manager.update_entity(entity_key, self.project_browser.current_entity_type, task_name)
                            except Exception:
                                # Fallback to reload
                                self.version_manager.load_versions()
                        self.logger.info(f"Marked related versions as Complete for task: {task_name}")
                except Exception as e:
                    self.logger.warning(f"Failed to persist completion state: {e}")
            else:
                QMessageBox.information(self, "Already Complete", "This task is already marked as complete.")
        else:
            QMessageBox.warning(self, "No Selection", "Please select a task to complete.")
    
    def delete_task(self):
        """Delete selected task(s)"""
        selected_items = self.project_browser.tasks_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select task(s) to delete.")
            return

        if len(selected_items) == 1:
            task_name = selected_items[0].text().split(" - ")[0]
            message = f"Are you sure you want to delete the task '{task_name}'?"
        else:
            task_names = [item.text().split(" - ")[0] for item in selected_items]
            message = f"Are you sure you want to delete {len(selected_items)} tasks?\n\nTasks: {', '.join(task_names)}"
        
            reply = QMessageBox.question(
            self, 
            "Delete Task(s)", 
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Store task names for logging
                deleted_tasks = []
                
                # Remove from UI (in reverse order to maintain indices)
                for item in reversed(selected_items):
                    task_name = item.text().split(" - ")[0]
                    deleted_tasks.append(task_name)
                    row = self.project_browser.tasks_list.row(item)
                    self.project_browser.tasks_list.takeItem(row)
            
                # Remove from project data if available
                if self.manager.current_project and hasattr(self.manager.current_project, 'tasks'):
                    for task_name in deleted_tasks:
                        self.manager.current_project.tasks = [
                            task for task in self.manager.current_project.tasks 
                            if not (hasattr(task, 'name') and task.name == task_name and
                                   hasattr(task, 'entity') and task.entity == self.project_browser.current_entity and
                                   hasattr(task, 'entity_type') and task.entity_type == self.project_browser.current_entity_type) and
                               not (isinstance(task, dict) and task.get('name', '') == task_name and
                                   task.get('entity') == self.project_browser.current_entity and
                                   task.get('entity_type') == self.project_browser.current_entity_type)
                        ]
                    self.manager.save_project()
                
                # Ensure department selection is maintained after deletion
                self.ensure_department_selection_visible()
                self.filter_tasks_by_department()
                
                self.logger.info(f"Deleted {len(deleted_tasks)} task(s): {', '.join(deleted_tasks)}")
    
    # Department Management Methods - now handled per-entity only


    
    def load_tasks_from_project(self):
        """Load tasks from project data into UI - now only clears the list"""
        if not self.manager.current_project:
            return
        
        # Clear existing tasks - no project-level tasks are shown initially
        self.project_browser.tasks_list.clear()
        
        # No project-level tasks are loaded - only entity-specific tasks when an entity is selected
        self.logger.info("Tasks list cleared - will show entity-specific tasks when an asset or shot is selected")
    
    def load_departments_from_project(self):
        """Load departments from project data into UI - now only clears the list"""
        if not self.manager.current_project:
            return
        
        # Clear existing departments - no project-level departments are shown
        self.project_browser.departments_list.clear()
        
        # No project-level departments are loaded - only entity-specific departments
        self.logger.info("Departments list cleared - will show entity-specific departments when selected")
    
    def filter_tasks_by_department(self):
        """Filter tasks by selected department for the current entity"""
        if not self.manager.current_project or not hasattr(self.manager.current_project, 'tasks'):
            return
        
        # Check if we have a current entity selected
        if not self.project_browser.current_entity or not self.project_browser.current_entity_type:
            return
        
        # Get selected department
        current_item = self.project_browser.departments_list.currentItem()
        if not current_item:
            return
        
        selected_dept = current_item.text().split(" - ")[0]
        
        # Clear and repopulate tasks list with filtered tasks for current entity
        self.project_browser.tasks_list.clear()
        
        for task in self.manager.current_project.tasks:
            # Check if task belongs to current entity and selected department
            task_entity = getattr(task, 'entity', None) if hasattr(task, 'entity') else None
            task_entity_type = getattr(task, 'entity_type', None) if hasattr(task, 'entity_type') else None
            
            # Filter by entity and department
            if (task_entity == self.project_browser.current_entity and 
                task_entity_type == self.project_browser.current_entity_type and
                hasattr(task, 'department') and task.department == selected_dept):
                # Task object
                task_text = f"{task.name} - {task.status}"
                if task.description:
                    task_text += f" ({task.description})"
                self.project_browser.tasks_list.addItem(task_text)
            elif (isinstance(task, dict) and 
                  task.get('entity') == self.project_browser.current_entity and
                  task.get('entity_type') == self.project_browser.current_entity_type and
                  task.get('department') == selected_dept):
                # Legacy dict format
                task_text = f"{task.get('name', 'Unknown')} - {task.get('status', 'Pending')}"
                if task.get('description'):
                    task_text += f" ({task['description']})"
                self.project_browser.tasks_list.addItem(task_text)
        
        # Auto-select first task if any exist
        if self.project_browser.tasks_list.count() > 0:
            self.project_browser.tasks_list.setCurrentRow(0)
        
        self.logger.info(f"Filtered tasks for department: {selected_dept} in {self.project_browser.current_entity_type.lower()}: {self.project_browser.current_entity}")
    
    def on_department_selection_changed(self):
        """Handle department selection change"""
        self.filter_tasks_by_department()
    
    def on_task_selection_changed(self):
        """Handle task selection change"""
        # Task selection is handled in the UI, just ensure it's maintained
        self.project_browser.ensure_task_selection_visible()
    
    def ensure_department_selection_visible(self):
        """Ensure the department selection is visually highlighted"""
        if self.project_browser.departments_list.count() > 0:
            # Get current selection
            current_row = self.project_browser.departments_list.currentRow()
            if current_row < 0:
                # If no selection, select the first item
                current_row = 0
                self.project_browser.departments_list.setCurrentRow(current_row)
            
            # Ensure the item is visible and selected
            self.project_browser.departments_list.scrollToItem(
                self.project_browser.departments_list.item(current_row)
            )
            self.project_browser.departments_list.setFocus()
            self.project_browser.departments_list.repaint()
    
    def setup_department_list_persistence(self):
        """Setup department list to maintain selection"""
        # Set selection mode to single selection (prevents deselection)
        self.project_browser.departments_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Set focus policy to strong focus (maintains selection when clicking elsewhere)
        self.project_browser.departments_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Ensure at least one item is always selected
        if self.project_browser.departments_list.count() > 0:
            if self.project_browser.departments_list.currentRow() < 0:
                self.project_browser.departments_list.setCurrentRow(0)
    
    def department_list_focus_out(self, event):
        """Handle focus out event for department list - maintain selection"""
        # Don't clear selection when losing focus, especially for popup menus
        event.ignore()
        # Ensure selection is maintained even when focus is lost
        QTimer.singleShot(10, self.ensure_department_selection_visible)
    
    def department_list_focus_in(self, event):
        """Handle focus in event for department list - ensure selection is visible"""
        # Ensure selection is visible when regaining focus
        self.ensure_department_selection_visible()
        event.accept()
    
    def maintain_selection_after_action(self):
        """Ensure department selection is maintained after any action"""
        # Ensure at least one department is selected
        if self.project_browser.departments_list.count() > 0:
            if self.project_browser.departments_list.currentRow() < 0:
                self.project_browser.departments_list.setCurrentRow(0)
            self.ensure_department_selection_visible()
            self.filter_tasks_by_department()
    
    def department_list_mouse_press(self, event):
        """Handle mouse press event for department list - maintain selection"""
        # Call the original mouse press event
        from PyQt6.QtWidgets import QListWidget
        QListWidget.mousePressEvent(self.project_browser.departments_list, event)
        
        # Ensure selection is maintained
        self.ensure_department_selection_visible()
    
    def maintain_selection(self):
        """Periodically check and maintain department and task selection"""
        # Maintain department selection
        if (self.project_browser.departments_list.count() > 0 and 
            self.project_browser.departments_list.currentRow() < 0):
            # If no selection but items exist, select the first one
            self.project_browser.departments_list.setCurrentRow(0)
            self.filter_tasks_by_department()
        
        # Maintain task selection
        if (self.project_browser.tasks_list.count() > 0 and
            self.project_browser.tasks_list.currentRow() < 0):
            self.project_browser.tasks_list.setCurrentRow(0)
            self.project_browser.ensure_task_selection_visible()
    
    def add_department_to_entity(self, item):
        """Add a department to the selected entity (asset or shot)"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Load or create a project first.")
            return
        
        # Get entity info from the item
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        entity_name = item.text(0)
        
        if item_type == "Asset":
            # Find the asset
            asset = self.manager.current_project.get_asset(entity_name)
            if not asset:
                QMessageBox.warning(self, "Asset Not Found", f"Could not find asset: {entity_name}")
                return
            
            # Get department name from user
            department, ok = QInputDialog.getText(self, "Add Department", "Enter department name:")
            if not ok or not department.strip():
                return
            
            department = department.strip()
            
            # Add department to asset
            asset.add_department(department)
            self.manager.save_project()
            
            # Update UI
            self.project_browser.load_entity_departments(entity_name, "Asset")
            self.logger.info(f"Added department '{department}' to asset '{entity_name}'")
            
        elif item_type == "Shot":
            # Get parent folder for sequence
            parent_item = item.parent()
            sequence = parent_item.text(0) if parent_item else "Main"
            shot_key = f"{sequence}/{entity_name}"
            
            # Find the shot
            shot = self.manager.current_project.get_shot(sequence, entity_name)
            if not shot:
                QMessageBox.warning(self, "Shot Not Found", f"Could not find shot: {shot_key}")
                return
            
            # Get department name from user
            department, ok = QInputDialog.getText(self, "Add Department", "Enter department name:")
            if not ok or not department.strip():
                return
            
            department = department.strip()
            
            # Add department to shot
            shot.add_department(department)
            self.manager.save_project()
            
            # Update UI
            self.project_browser.load_entity_departments(shot_key, "Shot")
            self.logger.info(f"Added department '{department}' to shot '{shot_key}'")
    
    def remove_department_from_entity(self, item):
        """Remove a department from the selected entity (asset or shot)"""
        if not self.manager.current_project:
            QMessageBox.warning(self, "No Project", "Load or create a project first.")
            return
        
        # Get entity info from the item
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        entity_name = item.text(0)
        
        if item_type == "Asset":
            # Find the asset
            asset = self.manager.current_project.get_asset(entity_name)
            if not asset:
                QMessageBox.warning(self, "Asset Not Found", f"Could not find asset: {entity_name}")
                return
            
            if not asset.departments:
                QMessageBox.information(self, "No Departments", f"Asset '{entity_name}' has no departments to remove.")
                return
            
            # Show department selection dialog
            department, ok = QInputDialog.getItem(
                self, "Remove Department", "Select department to remove:",
                asset.departments, 0, False
            )
            if not ok or not department:
                return
            
            # Remove department from asset
            asset.remove_department(department)
            self.manager.save_project()
            
            # Update UI
            self.project_browser.load_entity_departments(entity_name, "Asset")
            self.logger.info(f"Removed department '{department}' from asset '{entity_name}'")
            
        elif item_type == "Shot":
            # Get parent folder for sequence
            parent_item = item.parent()
            sequence = parent_item.text(0) if parent_item else "Main"
            shot_key = f"{sequence}/{entity_name}"
            
            # Find the shot
            shot = self.manager.current_project.get_shot(sequence, entity_name)
            if not shot:
                QMessageBox.warning(self, "Shot Not Found", f"Could not find shot: {shot_key}")
                return
            
            if not shot.departments:
                QMessageBox.information(self, "No Departments", f"Shot '{shot_key}' has no departments to remove.")
                return
            
            # Show department selection dialog
            department, ok = QInputDialog.getItem(
                self, "Remove Department", "Select department to remove:",
                shot.departments, 0, False
            )
            if not ok or not department:
                return
            
            # Remove department from shot
            shot.remove_department(department)
            self.manager.save_project()
            
            # Update UI
            self.project_browser.load_entity_departments(shot_key, "Shot")
            self.logger.info(f"Removed department '{department}' from shot '{shot_key}'")
    
    def add_department_to_current_entity(self):
        """Add a department to the currently selected entity"""
        if not self.project_browser.current_entity or not self.project_browser.current_entity_type:
            QMessageBox.warning(self, "No Selection", "Please select an asset or shot first.")
            return
        
        # Get department name from user
        department, ok = QInputDialog.getText(self, "Add Department", "Enter department name:")
        if not ok or not department.strip():
            return
        
        department = department.strip()
        
        # Add department to entity
        if self.project_browser.current_entity_type == "Asset":
            asset = self.manager.current_project.get_asset(self.project_browser.current_entity)
            if asset:
                asset.add_department(department)
                self.manager.save_project()
                # Reload departments display
                self.project_browser.load_entity_departments(self.project_browser.current_entity, "Asset")
                self.logger.info(f"Added department '{department}' to asset '{self.project_browser.current_entity}'")
        elif self.project_browser.current_entity_type == "Shot":
            if "/" in self.project_browser.current_entity:
                sequence, name = self.project_browser.current_entity.split("/", 1)
                shot = self.manager.current_project.get_shot(sequence, name)
                if shot:
                    shot.add_department(department)
                    self.manager.save_project()
                    # Reload departments display
                    self.project_browser.load_entity_departments(self.project_browser.current_entity, "Shot")
                    self.logger.info(f"Added department '{department}' to shot '{self.project_browser.current_entity}'")
    
    def edit_department_from_current_entity(self, item=None):
        """Edit a department from the currently selected entity"""
        if not self.project_browser.current_entity or not self.project_browser.current_entity_type:
            QMessageBox.warning(self, "No Selection", "Please select an asset or shot first.")
            return
        
        # Get the department to edit
        if not item:
            item = self.project_browser.departments_list.currentItem()
            if not item:
                QMessageBox.warning(self, "No Selection", "Please select a department to edit.")
                return
        
        current_text = item.text()
        current_name = current_text.split(" - ")[0]
        
        # Get new department name from user
        new_name, ok = QInputDialog.getText(self, "Edit Department", "Enter new department name:", text=current_name)
        if not ok or not new_name.strip():
            return
        
        new_name = new_name.strip()
        
        # Update department in entity
        if self.project_browser.current_entity_type == "Asset":
            asset = self.manager.current_project.get_asset(self.project_browser.current_entity)
            if asset and current_name in asset.departments:
                asset.remove_department(current_name)
                asset.add_department(new_name)
                self.manager.save_project()
                # Reload departments display
                self.project_browser.load_entity_departments(self.project_browser.current_entity, "Asset")
                self.logger.info(f"Edited department '{current_name}' to '{new_name}' in asset '{self.project_browser.current_entity}'")
        elif self.project_browser.current_entity_type == "Shot":
            if "/" in self.project_browser.current_entity:
                sequence, name = self.project_browser.current_entity.split("/", 1)
                shot = self.manager.current_project.get_shot(sequence, name)
                if shot and current_name in shot.departments:
                    shot.remove_department(current_name)
                    shot.add_department(new_name)
                    self.manager.save_project()
                    # Reload departments display
                    self.project_browser.load_entity_departments(self.project_browser.current_entity, "Shot")
                    self.logger.info(f"Edited department '{current_name}' to '{new_name}' in shot '{self.project_browser.current_entity}'")
    
    def remove_department_from_current_entity(self, item=None):
        """Remove a department from the currently selected entity"""
        if not self.project_browser.current_entity or not self.project_browser.current_entity_type:
            QMessageBox.warning(self, "No Selection", "Please select an asset or shot first.")
            return
        
        # Get the department to remove
        if not item:
            item = self.project_browser.departments_list.currentItem()
            if not item:
                QMessageBox.warning(self, "No Selection", "Please select a department to remove.")
                return
        
        department_text = item.text()
        department = department_text.split(" - ")[0]
        
        # Remove department from entity
        if self.project_browser.current_entity_type == "Asset":
            asset = self.manager.current_project.get_asset(self.project_browser.current_entity)
            if asset:
                asset.remove_department(department)
                self.manager.save_project()
                # Reload departments display
                self.project_browser.load_entity_departments(self.project_browser.current_entity, "Asset")
                self.logger.info(f"Removed department '{department}' from asset '{self.project_browser.current_entity}'")
        elif self.project_browser.current_entity_type == "Shot":
            if "/" in self.project_browser.current_entity:
                sequence, name = self.project_browser.current_entity.split("/", 1)
                shot = self.manager.current_project.get_shot(sequence, name)
                if shot:
                    shot.remove_department(department)
                    self.manager.save_project()
                    # Reload departments display
                    self.project_browser.load_entity_departments(self.project_browser.current_entity, "Shot")
                    self.logger.info(f"Removed department '{department}' from shot '{self.project_browser.current_entity}'")
    
    def remove_selected_departments_from_current_entity(self):
        """Remove selected departments from the currently selected entity"""
        if not self.project_browser.current_entity or not self.project_browser.current_entity_type:
            QMessageBox.warning(self, "No Selection", "Please select an asset or shot first.")
            return
        
        selected_items = self.project_browser.departments_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select departments to remove.")
            return
        
        # Get department names
        departments_to_remove = [item.text().split(" - ")[0] for item in selected_items]
        
        # Confirm removal
        if len(departments_to_remove) == 1:
            message = f"Are you sure you want to remove the department '{departments_to_remove[0]}'?"
        else:
            message = f"Are you sure you want to remove {len(departments_to_remove)} departments?\n\nDepartments: {', '.join(departments_to_remove)}"
        
        reply = QMessageBox.question(
            self, 
            "Remove Departments", 
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove departments from entity
            if self.project_browser.current_entity_type == "Asset":
                asset = self.manager.current_project.get_asset(self.project_browser.current_entity)
                if asset:
                    for department in departments_to_remove:
                        asset.remove_department(department)
                    self.manager.save_project()
                    # Reload departments display
                    self.project_browser.load_entity_departments(self.project_browser.current_entity, "Asset")
                    self.logger.info(f"Removed {len(departments_to_remove)} departments from asset '{self.project_browser.current_entity}': {', '.join(departments_to_remove)}")
            elif self.project_browser.current_entity_type == "Shot":
                if "/" in self.project_browser.current_entity:
                    sequence, name = self.project_browser.current_entity.split("/", 1)
                    shot = self.manager.current_project.get_shot(sequence, name)
                    if shot:
                        for department in departments_to_remove:
                            shot.remove_department(department)
                        self.manager.save_project()
                        # Reload departments display
                        self.project_browser.load_entity_departments(self.project_browser.current_entity, "Shot")
                        self.logger.info(f"Removed {len(departments_to_remove)} departments from shot '{self.project_browser.current_entity}': {', '.join(departments_to_remove)}")
    
    def setup_thumbnail_integration(self):
        """Setup thumbnail preview integration"""
        try:
            # Connect right panel thumbnail preview signals
            if hasattr(self.right_panel, 'thumbnail_preview_widget'):
                self.right_panel.thumbnail_preview_widget.thumbnail_clicked.connect(self.on_thumbnail_clicked)
                self.right_panel.thumbnail_preview_widget.thumbnail_double_clicked.connect(self.on_thumbnail_double_clicked)
                self.right_panel.thumbnail_preview_widget.generate_thumbnail_requested.connect(self.on_generate_thumbnail_requested)
                
                # Set project path for Prism-style previews
                if self.manager.current_project:
                    self.right_panel.thumbnail_preview_widget.set_project_path(self.manager.current_project.path)
                
                self.logger.info("Thumbnail preview integration setup complete")
        except Exception as e:
            self.logger.warning(f"Failed to setup thumbnail integration: {e}")
    
    def on_thumbnail_clicked(self, file_path: str):
        """Handle thumbnail click - select in tree"""
        try:
            # Find and select the file in the appropriate tree
            if hasattr(self, 'version_manager') and hasattr(self.version_manager, 'select_file'):
                self.version_manager.select_file(file_path)
        except Exception as e:
            self.logger.warning(f"Failed to select file in tree: {e}")
    
    def on_thumbnail_double_clicked(self, file_path: str):
        """Handle thumbnail double-click - open file or launch DCC app"""
        try:
            # Try to launch DCC app with the file
            if self.manager.current_project:
                # Determine DCC app from file extension
                from vogue_core.dcc_integration import dcc_manager
                file_info = dcc_manager.get_file_info(file_path)
                dcc_app = file_info.get('dcc_app', 'unknown')
                
                if dcc_app != 'unknown':
                    success = self.manager.launch_dcc_app(dcc_app, workfile_path=file_path)
                    if success:
                        self.logger.info(f"Launched {dcc_app} with file: {file_path}")
                    else:
                        self.logger.warning(f"Failed to launch {dcc_app} with file: {file_path}")
                else:
                    # Try to open with default application
                    import subprocess
                    import platform
                    
                    if platform.system() == "Windows":
                        os.startfile(file_path)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", file_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", file_path])
        except Exception as e:
            self.logger.error(f"Failed to handle thumbnail double-click: {e}")
    
    def on_generate_thumbnail_requested(self, file_path: str, entity_type: str, entity_name: str):
        """Handle thumbnail generation request"""
        try:
            if self.manager.current_project:
                # Generate enhanced thumbnail
                thumbnail_path = self.manager.generate_enhanced_thumbnail(
                    file_path, entity_type, entity_name
                )
                
                if thumbnail_path and os.path.exists(thumbnail_path):
                    self.logger.info(f"Generated thumbnail: {thumbnail_path}")
                    
                    # Update thumbnail preview if available
                    if hasattr(self.right_panel, 'thumbnail_preview_widget'):
                        self.right_panel.thumbnail_preview_widget.update_thumbnail(file_path, thumbnail_path)
                else:
                    self.logger.warning(f"Failed to generate thumbnail for: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to generate thumbnail: {e}")
    
    def load_project_thumbnails(self):
        """Load all project thumbnails into the preview widget"""
        try:
            if not self.manager.current_project:
                return
            
            thumbnails = []
            project_path = self.manager.current_project.path
            
            # Scan for thumbnails in various locations
            thumbnail_dirs = [
                Path(project_path) / "thumbnails" / "versions",
                Path(project_path) / "thumbnails" / "assets", 
                Path(project_path) / "thumbnails" / "shots",
                Path(project_path) / "00_Pipeline" / "Assetinfo",
                Path(project_path) / "00_Pipeline" / "Shotinfo",
            ]
            
            for thumb_dir in thumbnail_dirs:
                if thumb_dir.exists():
                    for thumb_file in thumb_dir.glob("*.png"):
                        # Try to find corresponding source file
                        source_file = self.find_source_file_for_thumbnail(thumb_file)
                        if source_file:
                            thumbnails.append({
                                'file_path': source_file,
                                'entity_type': 'asset' if 'Assetinfo' in str(thumb_dir) else 'shot',
                                'entity_name': thumb_file.stem.replace('_preview', '').replace('_thumb', ''),
                                'task_name': '',
                                'thumbnail_path': str(thumb_file)
                            })
            
            # Load thumbnails into preview widget
            if hasattr(self.right_panel, 'load_thumbnails'):
                self.right_panel.load_thumbnails(thumbnails)
                
        except Exception as e:
            self.logger.error(f"Failed to load project thumbnails: {e}")
    
    def find_source_file_for_thumbnail(self, thumbnail_path: Path) -> str | None:
        """Find the source file for a thumbnail"""
        try:
            # Look for corresponding source files in common locations
            project_path = Path(self.manager.current_project.path)
            thumb_name = thumbnail_path.stem.replace('_preview', '').replace('_thumb', '')
            
            # Search in workfiles and scenes directories
            search_dirs = [
                project_path / "workfiles",
                project_path / "06_Scenes",
                project_path / "01_Assets",
                project_path / "02_Shots"
            ]
            
            for search_dir in search_dirs:
                if search_dir.exists():
                    for source_file in search_dir.rglob("*"):
                        if source_file.is_file() and source_file.stem == thumb_name:
                            return str(source_file)
            
            return None
        except Exception as e:
            self.logger.warning(f"Failed to find source file for thumbnail {thumbnail_path}: {e}")
            return None
