#!/usr/bin/env python3
"""Test UI tree update functionality"""

import sys
import os
sys.path.insert(0, 'src')

from PyQt6.QtWidgets import QApplication, QWidget
from vogue_core.manager import ProjectManager
from vogue_core.models import Asset
from pathlib import Path

def test_ui_tree_update():
    """Test UI tree update functionality"""
    print("Testing UI tree update...")
    
    app = QApplication(sys.argv)
    
    try:
        # Create a test project
        manager = ProjectManager()
        
        # Create a temporary project
        test_dir = Path("test_temp_project")
        test_dir.mkdir(exist_ok=True)
        
        try:
            # Create project
            project = manager.create_project(
                name="TestProject",
                parent_dir=str(test_dir),
                fps=24,
                resolution=[1920, 1080]
            )
            
            print(f"Created project: {project.name}")
            print(f"Project assets before: {len(project.assets)}")
            
            # Create a mock controller
            class MockController(QWidget):
                def __init__(self, manager):
                    super().__init__()
                    self.manager = manager
                    self.logger = type('Logger', (), {'info': lambda self, x: print(f"LOG: {x}"), 'error': lambda self, x: print(f"ERROR: {x}")})()
                
                def create_default_asset_icon(self, width, height):
                    from PyQt6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor
                    from PyQt6.QtCore import Qt
                    
                    pixmap = QPixmap(width, height)
                    pixmap.fill(QColor(60, 60, 60))  # Dark background
                    
                    painter = QPainter(pixmap)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    
                    # Draw striped pattern
                    pen = QPen(QColor(100, 100, 100), 2)
                    painter.setPen(pen)
                    
                    for i in range(0, width, 20):
                        painter.drawLine(i, 0, i, height)
                    for i in range(0, height, 20):
                        painter.drawLine(0, i, width, i)
                    
                    # Draw dashed border
                    pen = QPen(QColor(150, 150, 150), 3)
                    pen.setStyle(Qt.PenStyle.DashLine)
                    painter.setPen(pen)
                    painter.drawRect(2, 2, width-4, height-4)
                    
                    painter.end()
                    return pixmap
                
                def get_asset_icon(self, asset, size=120):
                    return self.create_default_asset_icon(size, size)
                
                def update_assets_tree(self):
                    """Simple asset tree update with icons"""
                    from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
                    from PyQt6.QtGui import QIcon
                    from PyQt6.QtCore import QSize, Qt
                    
                    # Create a mock tree widget
                    tree = QTreeWidget()
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
                    
                    return tree
            
            controller = MockController(manager)
            
            # Test tree update with no assets
            tree = controller.update_assets_tree()
            print(f"Tree items with no assets: {tree.topLevelItemCount()}")
            
            # Add an asset
            asset = Asset(name="TestAsset", type="Props", meta={"description": "Test asset"})
            project.assets.append(asset)
            print(f"Added asset: {asset.name}")
            print(f"Project assets after: {len(project.assets)}")
            
            # Test tree update with asset
            tree = controller.update_assets_tree()
            print(f"Tree items with asset: {tree.topLevelItemCount()}")
            
            # Check if asset appears in tree
            found_asset = False
            for i in range(tree.topLevelItemCount()):
                item = tree.topLevelItem(i)
                if item.text(0) == "TestAsset":
                    found_asset = True
                    print(f"Found asset in tree: {item.text(0)}")
                    break
            
            if found_asset:
                print("Asset appears in tree correctly")
                return True
            else:
                print("Asset does NOT appear in tree")
                return False
                
        finally:
            # Cleanup
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)
                print("Cleaned up test directory")
                
    except Exception as e:
        print(f"Error during UI tree update test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ui_tree_update()
    if success:
        print("UI tree update test PASSED")
    else:
        print("UI tree update test FAILED")
