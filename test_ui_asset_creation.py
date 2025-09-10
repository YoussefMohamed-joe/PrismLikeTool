#!/usr/bin/env python3
"""Test UI asset creation functionality"""

import sys
import os
sys.path.insert(0, 'src')

from vogue_core.manager import ProjectManager
from vogue_core.models import Asset, Project
from pathlib import Path

def test_ui_asset_creation():
    """Test asset creation as it would happen in the UI"""
    print("Testing UI asset creation flow...")
    
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
        print(f"Project folders before: {len(project.folders) if hasattr(project, 'folders') else 0}")
        
        # Simulate the asset creation flow from the controller
        asset_data = {
            "name": "TestAsset",
            "folder": "Main",  # This should create an unassigned asset
            "description": "Test asset description",
            "image_path": None,
            "meta": {
                "tags": ["test"],
                "artist": "TestArtist",
                "lod": "High",
                "rigged": False,
                "animated": False,
                "image_path": None
            }
        }
        
        print(f"Asset data: {asset_data}")
        
        # Simulate the controller logic
        from vogue_core.models import Asset
        
        # Ensure folders container
        if not hasattr(project, 'folders') or project.folders is None:
            project.folders = []
            print("Created folders container")

        # Handle folder selection - "Main" means root level, not a folder
        folder_name = asset_data["folder"].strip() if asset_data.get("folder") else "Main"
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
        existing = next((a for a in getattr(project, 'assets', []) if a.name == asset_data['name']), None)
        if existing is None:
            if not hasattr(project, 'assets') or project.assets is None:
                project.assets = []
            # Asset model requires 'type' parameter, use folder name as type or default
            asset_type = folder_name if folder_name != "Main" else "Props"
            asset = Asset(name=asset_data['name'], type=asset_type)
            # Store description in meta
            if asset_data.get('description'):
                asset.meta['description'] = asset_data['description']
            # Store image path in meta
            if asset_data.get('image_path'):
                asset.meta['image_path'] = asset_data['image_path']
            # Attach other meta data
            if hasattr(asset, 'meta') and isinstance(asset.meta, dict):
                asset.meta.update(asset_data.get('meta', {}))
            project.assets.append(asset)
            print(f"Created asset: {asset.name} with type: {asset.type}")
            print(f"Asset meta: {asset.meta}")

        # Add to folder list (string names)
        if folder_name != "Main" and folder is not None:
            if not hasattr(folder, 'assets') or folder.assets is None:
                folder.assets = []
            if asset_data['name'] not in folder.assets:
                folder.assets.append(asset_data['name'])
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
        
    except Exception as e:
        print(f"Error during UI asset creation test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("Cleaned up test directory")

if __name__ == "__main__":
    success = test_ui_asset_creation()
    if success:
        print("UI asset creation test PASSED")
    else:
        print("UI asset creation test FAILED")
