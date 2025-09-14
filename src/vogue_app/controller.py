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
from vogue_app.ayon_hybrid_ui import AyonHybridMainWindow
from vogue_app.dialogs import AssetDialog

class VogueController(AyonHybridMainWindow):
    """Clean controller for Vogue Manager desktop application"""
    
    def __init__(self):
        # Initialize logger first before calling super()
        self.logger = get_logger("Controller")
        super().__init__()
        self.manager = ProjectManager()
        
        # Initialize clipboard state for cut/copy operations
        self.clipboard_item = None
        self.clipboard_items = None  # For multi-select operations
        self.clipboard_operation = None  # 'cut' or 'copy'
        self.clipboard_type = None  # 'asset', 'shot', or 'multiple'
        
        # Override the modern UI connections with our specific implementations
        self.setup_vogue_connections()
        
        # Setup context menus for Ayon UI
        self.setup_ayon_context_menus()
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()

        # Setup tree widgets FIRST (before loading project)
        # QTimer.singleShot(100, self._setup_tree_widgets)  # Temporarily disabled for Ayon UI

        # Auto-load last opened project AFTER tree setup
        # QTimer.singleShot(200, self._auto_load_last_project)  # Temporarily disabled for Ayon UI
    
    def setup_vogue_connections(self):
        """Setup Vogue-specific signal connections for Ayon hybrid UI"""
        # Connect hierarchy tree
        if hasattr(self, 'hierarchy_tree'):
            self.hierarchy_tree.itemSelectionChanged.connect(self.on_hierarchy_selection_changed)
            self.hierarchy_tree.itemDoubleClicked.connect(self.on_hierarchy_double_clicked)
        
        # Connect task list
        if hasattr(self, 'task_list'):
            self.task_list.itemSelectionChanged.connect(self.on_task_selection_changed)
        
        # Connect table selections
        if hasattr(self, 'assets_table'):
            self.assets_table.itemSelectionChanged.connect(self.on_asset_selection_changed)
        
        if hasattr(self, 'shots_table'):
            self.shots_table.itemSelectionChanged.connect(self.on_shot_selection_changed)
        
        if hasattr(self, 'versions_table'):
            self.versions_table.itemSelectionChanged.connect(self.on_version_selection_changed)
        
        # Connect search
        if hasattr(self, 'hierarchy_search'):
            self.hierarchy_search.textChanged.connect(self.on_hierarchy_search_changed)
        
        # Connect task filter
        if hasattr(self, 'task_filter'):
            self.task_filter.currentTextChanged.connect(self.on_task_filter_changed)
    
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
        # For Ayon UI, update the assets table instead
        if hasattr(self, 'assets_table'):
            self.update_assets_table()
        return
        
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
                if folder.folder_type == "Asset":
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
                if folder.folder_type == "Asset" and hasattr(folder, 'assets') and folder.assets:
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
        if hasattr(self, 'logger'):
            self.logger.info(f"Updated assets tree with {tree.topLevelItemCount()} items")
    
    def update_shots_tree(self):
        """Update shots tree with icons"""
        tree = self.shot_tree
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
                if folder.folder_type == "Shot":
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
        if hasattr(self, 'logger'):
            self.logger.info(f"Updated shots tree with {tree.topLevelItemCount()} items")
    
    def setup_asset_tree_context_menu(self):
        """Setup context menu for asset tree"""
        # For Ayon UI, this is handled in setup_ayon_context_menus
        pass
    
    def setup_shot_tree_context_menu(self):
        """Setup context menu for shot tree"""
        # For Ayon UI, this is handled in setup_ayon_context_menus
        pass
    
    def show_asset_context_menu(self, position):
        """Show context menu for asset tree"""
        # For Ayon UI, this is handled by show_assets_context_menu
        pass
    
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
                    if hasattr(self, 'logger'):
                        self.logger.info(f"Updated asset properties: {asset_name}")
                except Exception as e:
                    QMessageBox.warning(self, "Save Error", f"Failed to save asset properties: {e}")
    
    def show_shot_context_menu(self, position):
        """Show context menu for shot tree"""
        tree = self.shot_tree
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
                    if hasattr(self, 'logger'):
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
            new_folder = Folder(name=name.strip(), folder_type="Asset", assets=[])
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
                if hasattr(self, 'asset_tree'):
                    for i in range(self.asset_tree.topLevelItemCount()):
                        if self.asset_tree.topLevelItem(i) == item:
                            self.asset_tree.takeTopLevelItem(i)
            return
        if hasattr(self, 'shot_tree'):
            for i in range(self.shot_tree.topLevelItemCount()):
                if self.shot_tree.topLevelItem(i) == item:
                    self.shot_tree.takeTopLevelItem(i)
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
                tree = self.asset_tree
                tree.takeTopLevelItem(tree.indexOfTopLevelItem(self.clipboard_item))
        
        # Clear clipboard
        self.clipboard_item = None
        self.clipboard_operation = None
        self.clipboard_type = None
    
    def setup_connections(self):
        """Setup signal connections"""
        # Connect button signals
        # These connections are already handled in setup_vogue_connections()
        pass
        
        # Connect menu actions
        self.connect_menu_actions()
    
    def _setup_tree_widgets(self):
        """Setup tree widgets"""
        self.logger.info("Setting up tree widgets")
        # Update Ayon UI components with current project data
        self.update_assets_table()
        self.update_shots_table()
        self.logger.info("Tree widgets setup completed successfully")
    
    def update_tasks_table(self):
        """Update the tasks table with current project data"""
        if not self.manager.current_project:
            return
        
        # Clear existing data
        self.task_table.setRowCount(0)
        
        # Add tasks from project
        for i, task in enumerate(self.manager.current_project.tasks):
            self.task_table.insertRow(i)
            self.task_table.setItem(i, 0, QTableWidgetItem(task.name))
            self.task_table.setItem(i, 1, QTableWidgetItem(getattr(task, 'task_type', 'General')))
            self.task_table.setItem(i, 2, QTableWidgetItem(getattr(task, 'assignee', 'Unassigned')))
            self.task_table.setItem(i, 3, QTableWidgetItem(getattr(task, 'status', 'Not Started')))
            self.task_table.setItem(i, 4, QTableWidgetItem(str(getattr(task, 'priority', 3))))
            self.task_table.setItem(i, 5, QTableWidgetItem(str(getattr(task, 'due_date', ''))))
    
    def update_versions_table(self):
        """Update the versions table with current project data"""
        if not self.manager.current_project:
            return
        
        # Clear existing data
        self.version_table.setRowCount(0)
        
        # Add versions from project
        row = 0
        for entity_key, versions in self.manager.current_project.versions.items():
            for version in versions:
                self.version_table.insertRow(row)
                self.version_table.setItem(row, 0, QTableWidgetItem(entity_key))
                self.version_table.setItem(row, 1, QTableWidgetItem(version.version))
                self.version_table.setItem(row, 2, QTableWidgetItem(version.user))
                self.version_table.setItem(row, 3, QTableWidgetItem(version.date))
                self.version_table.setItem(row, 4, QTableWidgetItem(version.comment))
                row += 1
    
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
                    if f.folder_type == "Asset" and f.name == folder_name:
                        folder = f
                        break
                if folder is None:
                    from vogue_core.models import Folder
                    folder = Folder(name=folder_name, folder_type="Asset", assets=[])
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
                folder = Folder(name=name, folder_type="Asset", assets=[])
                if not hasattr(self.manager.current_project, 'folders'):
                    self.manager.current_project.folders = []
                self.manager.current_project.folders.append(folder)
                self.manager.save_project()  # Save to JSON
                self.update_assets_tree()
                self.logger.info(f"Added folder: {name}")
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for asset tree"""
        from PyQt6.QtGui import QShortcut, QKeySequence
        
        tree = self.asset_tree
        
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
        tree = self.asset_tree
        selected_items = tree.selectedItems()
        
        if not selected_items:
            return
        
        if len(selected_items) == 1:
            self.copy_item(selected_items[0])
        else:
            self.copy_selected_items()
    
    def cut_selected_item(self):
        """Cut selected item(s)"""
        tree = self.asset_tree
        selected_items = tree.selectedItems()
        
        if not selected_items:
            return
        
        if len(selected_items) == 1:
            self.cut_item(selected_items[0])
        else:
            self.cut_selected_items()
    
    def paste_to_selected_item(self):
        """Paste to selected item"""
        tree = self.asset_tree
        current_item = tree.currentItem()
        if current_item:
            self.paste_item(current_item)
    
    def delete_selected_item(self):
        """Delete selected item(s)"""
        tree = self.asset_tree
        selected_items = tree.selectedItems()
        
        if not selected_items:
            return
        
        if len(selected_items) == 1:
            self.delete_item(selected_items[0])
        else:
            self.delete_selected_items()
    
    def connect_menu_actions(self):
        """Connect menu actions to their handlers"""
        # Menu actions are handled by the modern UI base class
        # We only need to override specific methods
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
            # Update window title with project info
            self.setWindowTitle(f"Vogue Manager - {self.manager.current_project.name}")
            
            # Update status menu
            if hasattr(self, 'project_status_action'):
                self.project_status_action.setText(f"Project: {self.manager.current_project.name}")
                self.project_status_action.setEnabled(True)
            
            self.logger.info(f"Updated project info display: {self.manager.current_project.name}")
        else:
            # No project loaded
            # Update window title
            self.setWindowTitle("Vogue Manager - No Project Loaded")
            
            if hasattr(self, 'project_status_action'):
                self.project_status_action.setText("Project: No project loaded")
                self.project_status_action.setEnabled(False)
    
    def show(self):
        """Show the main window"""
        super().show()
    
    def delete_selected_items(self):
        """Delete all selected items from both UI and project data"""
        tree = self.asset_tree
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
        tree = self.asset_tree
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
        tree = self.asset_tree
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
        dialog = ShotDialog(self, preselected_folder=preselected_folder)
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
                    folder = Folder(name=sequence_name, folder_type="Shot", assets=[])
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
                new_folder = Folder(name=name.strip(), folder_type="Shot", assets=[])
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
        tree = self.shot_tree
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
        tree = self.shot_tree
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
        tree = self.shot_tree
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

        dialog = CreateTaskDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_task_data()
            if data:
                # Add task to the tasks list
                task_text = f"{data['name']} - {data['status']}"
                if data['description']:
                    task_text += f" ({data['description']})"
                
                # Tasks are now handled in the task table
                pass
                
                # Save to project data
                if self.manager.current_project:
                    if not hasattr(self.manager.current_project, 'tasks'):
                        self.manager.current_project.tasks = []
                    
                    # Add task object to project
                    from vogue_core.models import Task
                    task = Task(
                        name=data['name'],
                        status=data['status'],
                        description=data['description']
                    )
                    self.manager.current_project.tasks.append(task)
                    self.manager.save_project()
                
                self.logger.info(f"Created new task: {data['name']}")

    def assign_task(self):
        """Assign selected task"""
        # Task selection is now handled in the task table
        pass
        if current_item:
            task_name = current_item.text().split(" - ")[0]
            QMessageBox.information(self, "Task Assignment", f"Task '{task_name}' assigned successfully!")
            self.logger.info(f"Assigned task: {task_name}")
        else:
            QMessageBox.warning(self, "No Selection", "Please select a task to assign.")

    def complete_task(self):
        """Mark selected task as complete"""
        # Task selection is now handled in the task table
        pass
        if current_item:
            task_text = current_item.text()
            if " - Complete" not in task_text:
                # Update task status to complete
                if " - " in task_text:
                    task_name = task_text.split(" - ")[0]
                    new_text = f"{task_name} - Complete"
                else:
                    new_text = f"{task_text} - Complete"
                
                current_item.setText(new_text)
                self.logger.info(f"Completed task: {task_name}")
            else:
                QMessageBox.information(self, "Already Complete", "This task is already marked as complete.")
        else:
            QMessageBox.warning(self, "No Selection", "Please select a task to complete.")
    
    def delete_task(self):
        """Delete selected task(s)"""
        # Task selection is now handled in the task table
        pass
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
                    # Task deletion is now handled in the task table
                    pass
            
            # Remove from project data if available
            if self.manager.current_project and hasattr(self.manager.current_project, 'tasks'):
                for task_name in deleted_tasks:
                    self.manager.current_project.tasks = [
                        task for task in self.manager.current_project.tasks 
                        if (hasattr(task, 'name') and task.name != task_name) or
                           (isinstance(task, dict) and task.get('name', '') != task_name)
                    ]
                self.manager.save_project()
            
            self.logger.info(f"Deleted {len(deleted_tasks)} task(s): {', '.join(deleted_tasks)}")
    
    # Department Management Methods
    def add_department(self):
        """Add a new department"""
        from PyQt6.QtWidgets import QInputDialog, QColorDialog
        
        name, ok = QInputDialog.getText(self, "New Department", "Department name:")
        if ok and name:
            # Get color for the department
            color = QColorDialog.getColor()
            if color.isValid():
                color_hex = color.name()
                
                # Add to departments list
                dept_text = f"{name} - Active"
                # Departments are now handled in the modern UI
                pass
                
                # Store department data in project if available
                if self.manager.current_project:
                    from vogue_core.models import Department
                    dept = Department(name=name, color=color_hex)
                    if not hasattr(self.manager.current_project, 'departments'):
                        self.manager.current_project.departments = []
                    self.manager.current_project.departments.append(dept)
                    self.manager.save_project()
                
                self.logger.info(f"Added department: {name}")
            else:
                QMessageBox.warning(self, "Invalid Color", "Please select a valid color for the department.")

    def edit_department(self):
        """Edit selected department"""
        # Department selection is now handled in the modern UI
        pass
        if current_item:
            current_text = current_item.text()
            current_name = current_text.split(" - ")[0]
            
            from PyQt6.QtWidgets import QInputDialog, QColorDialog
            
            name, ok = QInputDialog.getText(self, "Edit Department", "Department name:", text=current_name)
            if ok and name:
                # Get new color
                color = QColorDialog.getColor()
                if color.isValid():
                    # Update the item
                    status = current_text.split(" - ")[1] if " - " in current_text else "Active"
                    new_text = f"{name} - {status}"
                    current_item.setText(new_text)
                    
                    # Update in project data if available
                    if self.manager.current_project and hasattr(self.manager.current_project, 'departments'):
                        for dept in self.manager.current_project.departments:
                            if dept.name == current_name:
                                dept.name = name
                                dept.color = color.name()
                                break
                        self.manager.save_project()
                    
                    self.logger.info(f"Edited department: {current_name} -> {name}")
                else:
                    QMessageBox.warning(self, "Invalid Color", "Please select a valid color for the department.")
            else:
                QMessageBox.warning(self, "No Selection", "Please select a department to edit.")

    def remove_department(self):
        """Remove selected department(s)"""
        # Department selection is now handled in the modern UI
        pass
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select department(s) to remove.")
            return

        if len(selected_items) == 1:
            dept_name = selected_items[0].text().split(" - ")[0]
            message = f"Are you sure you want to remove the department '{dept_name}'?"
        else:
            dept_names = [item.text().split(" - ")[0] for item in selected_items]
            message = f"Are you sure you want to remove {len(selected_items)} departments?\n\nDepartments: {', '.join(dept_names)}"
        
            reply = QMessageBox.question(
            self, 
            "Remove Department(s)", 
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Store department names for logging
                removed_departments = []
                
                # Remove from UI (in reverse order to maintain indices)
                for item in reversed(selected_items):
                    dept_name = item.text().split(" - ")[0]
                    removed_departments.append(dept_name)
                    # Department deletion is now handled in the modern UI
                    pass
            
            # Remove from project data if available
            if self.manager.current_project and hasattr(self.manager.current_project, 'departments'):
                for dept_name in removed_departments:
                    self.manager.current_project.departments = [
                        dept for dept in self.manager.current_project.departments 
                        if (hasattr(dept, 'name') and dept.name != dept_name) or 
                           (isinstance(dept, str) and dept.split(" - ")[0] != dept_name)
                    ]
                self.manager.save_project()
            
            self.logger.info(f"Removed {len(removed_departments)} department(s): {', '.join(removed_departments)}")
    
    def load_tasks_from_project(self):
        """Load tasks from project data into UI"""
        if not self.manager.current_project:
            return
        
        # Clear existing tasks
        # Task list is now handled in the task table
        pass
        
        # Load tasks from project data if they exist
        if hasattr(self.manager.current_project, 'tasks') and self.manager.current_project.tasks:
            for task in self.manager.current_project.tasks:
                if hasattr(task, 'name'):
                    # Task object
                    task_text = f"{task.name} - {task.status}"
                    if task.description:
                        task_text += f" ({task.description})"
                elif isinstance(task, dict):
                    # Legacy dict format
                    task_text = f"{task.get('name', 'Unknown')} - {task.get('status', 'Pending')}"
                    if task.get('description'):
                        task_text += f" ({task['description']})"
                else:
                    continue
                
                # Tasks are now handled in the task table
                pass
            
            self.logger.info(f"Loaded {len(self.manager.current_project.tasks)} tasks from project")
        else:
            self.logger.info("No tasks found in project")
    
    def load_departments_from_project(self):
        """Load departments from project data into UI"""
        if not self.manager.current_project:
            return
        
        # Clear existing departments
        # Department list is now handled in the modern UI
        pass
        
        # Load departments from project data if they exist
        if hasattr(self.manager.current_project, 'departments') and self.manager.current_project.departments:
            for dept in self.manager.current_project.departments:
                if hasattr(dept, 'name'):
                    # Department object
                    dept_text = f"{dept.name} - Active"
                elif isinstance(dept, str):
                    # Department string
                    dept_text = dept
                else:
                    continue
                
                # Departments are now handled in the modern UI
                pass
            
            self.logger.info(f"Loaded {len(self.manager.current_project.departments)} departments from project")
        else:
            self.logger.info("No departments found in project")
    
    # Ayon Hybrid UI Event Handlers
    def on_hierarchy_selection_changed(self):
        """Handle hierarchy selection change"""
        # Implement hierarchy selection logic
        pass
    
    def on_hierarchy_double_clicked(self, item, column):
        """Handle hierarchy double click"""
        # Implement double click logic
        pass
    
    def on_task_selection_changed(self):
        """Handle task selection change"""
        # Implement task selection logic
        pass
    
    def on_hierarchy_search_changed(self, text):
        """Handle hierarchy search change"""
        # Implement hierarchy search logic
        pass
    
    def on_task_filter_changed(self, text):
        """Handle task filter change"""
        # Implement task filtering logic
        pass
    
    def on_version_selection_changed(self):
        """Handle version selection change"""
        # Implement version selection logic
        pass
    
    def on_asset_selection_changed(self):
        """Handle asset selection change"""
        # Implement asset selection logic
        pass
    
    def on_shot_selection_changed(self):
        """Handle shot selection change"""
        # Implement shot selection logic
        pass
    
    def setup_ayon_context_menus(self):
        """Setup context menus for Ayon UI components"""
        # Setup context menus for tables and trees
        if hasattr(self, 'assets_table'):
            self.assets_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.assets_table.customContextMenuRequested.connect(self.show_assets_context_menu)
        
        if hasattr(self, 'shots_table'):
            self.shots_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.shots_table.customContextMenuRequested.connect(self.show_shots_context_menu)
        
        if hasattr(self, 'hierarchy_tree'):
            self.hierarchy_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.hierarchy_tree.customContextMenuRequested.connect(self.show_hierarchy_context_menu)
    
    def show_assets_context_menu(self, position):
        """Show context menu for assets table"""
        # Implement assets context menu
        pass
    
    def show_shots_context_menu(self, position):
        """Show context menu for shots table"""
        # Implement shots context menu
        pass
    
    def show_hierarchy_context_menu(self, position):
        """Show context menu for hierarchy tree"""
        # Implement hierarchy context menu
        pass
    
    def update_assets_table(self):
        """Update the assets table with current project data"""
        if not self.manager.current_project:
            return
        
        # Clear existing data
        self.assets_table.setRowCount(0)
        
        # Add assets from project
        for i, asset in enumerate(self.manager.current_project.assets):
            self.assets_table.insertRow(i)
            self.assets_table.setItem(i, 0, QTableWidgetItem(asset.name))
            self.assets_table.setItem(i, 1, QTableWidgetItem(asset.type))
            self.assets_table.setItem(i, 2, QTableWidgetItem("Active"))
            self.assets_table.setItem(i, 3, QTableWidgetItem(str(len(asset.versions))))
            self.assets_table.setItem(i, 4, QTableWidgetItem("Unknown"))
    
    def update_shots_table(self):
        """Update the shots table with current project data"""
        if not self.manager.current_project:
            return
        
        # Clear existing data
        self.shots_table.setRowCount(0)
        
        # Add shots from project
        for i, shot in enumerate(self.manager.current_project.shots):
            self.shots_table.insertRow(i)
            self.shots_table.setItem(i, 0, QTableWidgetItem(shot.name))
            self.shots_table.setItem(i, 1, QTableWidgetItem(shot.sequence))
            self.shots_table.setItem(i, 2, QTableWidgetItem("Active"))
            self.shots_table.setItem(i, 3, QTableWidgetItem(str(len(shot.versions))))
            self.shots_table.setItem(i, 4, QTableWidgetItem("120 frames"))
