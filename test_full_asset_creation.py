#!/usr/bin/env python3
"""Test full asset creation flow"""

import sys
import os
sys.path.insert(0, 'src')

from PyQt6.QtWidgets import QApplication, QWidget
from vogue_core.manager import ProjectManager
from vogue_app.dialogs import AssetDialog
from vogue_core.models import Asset
from pathlib import Path

def test_full_asset_creation():
    """Test the complete asset creation flow"""
    print("Testing full asset creation flow...")
    
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
                    self.logger = type('Logger', (), {'info': lambda x: print(f"LOG: {x}"), 'error': lambda x: print(f"ERROR: {x}")})()
            
            controller = MockController(manager)
            
            # Create the dialog
            dialog = AssetDialog(controller)
            print("Created AssetDialog successfully")
            
            # Set up the dialog with test data
            dialog.name_edit.setText("TestAsset")
            dialog.description_edit.setPlainText("Test description")
            dialog.tags_edit.setText("test, asset")
            dialog.artist_edit.setText("TestArtist")
            
            # Get data from dialog
            data = dialog.get_asset_data()
            print(f"Dialog data: {data}")
            
            if not data:
                print("No data from dialog")
                return False
            
            # Simulate the controller's add_asset method
            from PyQt6.QtWidgets import QMessageBox
            
            # Ensure folders container
            if not hasattr(project, 'folders') or project.folders is None:
                project.folders = []
                print("Created folders container")

            # Handle folder selection - "Main" means root level, not a folder
            folder_name = data["folder"].strip() if data.get("folder") else "Main"
            folder = None
            if folder_name and folder_name != "Main":
                # Find existing folder or create new one
                for f in project.folders:
                    if f.type == "asset" and f.name == folder_name:
                        folder = f
                        break
            if folder is None and folder_name != "Main":
                from vogue_core.models import Folder
                folder = Folder(name=folder_name, type="asset", assets=[])
                project.folders.append(folder)
                print(f"Created folder: {folder_name}")

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
                print(f"Created asset: {asset.name} with type: {asset.type}")
                print(f"Asset meta: {asset.meta}")

            # Add to folder list (string names)
            if folder_name != "Main" and folder is not None:
                if not hasattr(folder, 'assets') or folder.assets is None:
                    folder.assets = []
                if data['name'] not in folder.assets:
                    folder.assets.append(data['name'])
                    print(f"Added asset to folder: {folder_name}")

            # Save project
            manager.save_project()
            print("Project saved successfully")
            
            print(f"Project assets after: {len(project.assets)}")
            print(f"Project folders after: {len(project.folders) if hasattr(project, 'folders') else 0}")
            
            # Load project back to verify
            loaded_project = manager.load_project(str(Path(project.path) / "00_Pipeline" / "pipeline.json"))
            print(f"Loaded project: {loaded_project.name}")
            print(f"Loaded assets: {len(loaded_project.assets)}")
            
            if loaded_project.assets:
                for asset in loaded_project.assets:
                    print(f"  - Asset: {asset.name} (type: {asset.type})")
                    print(f"    Meta: {asset.meta}")
            
            return True
                
        finally:
            # Cleanup
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)
                print("Cleaned up test directory")
                
    except Exception as e:
        print(f"Error during full asset creation test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_asset_creation()
    if success:
        print("Full asset creation test PASSED")
    else:
        print("Full asset creation test FAILED")
