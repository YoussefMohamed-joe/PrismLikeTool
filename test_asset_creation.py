#!/usr/bin/env python3
"""Test asset creation functionality"""

import sys
import os
sys.path.insert(0, 'src')

from vogue_core.manager import ProjectManager
from vogue_core.models import Asset, Project
from pathlib import Path

def test_asset_creation():
    """Test basic asset creation"""
    print("Testing asset creation...")
    
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
        print(f"Project path: {project.path}")
        print(f"Project assets: {project.assets}")
        
        # Try to create an asset
        asset = Asset(
            name="TestAsset",
            type="Props",
            path=str(Path(project.path) / "01_Assets" / "Props" / "TestAsset"),
            meta={"description": "Test asset"}
        )
        
        print(f"Created asset: {asset.name}")
        print(f"Asset type: {asset.type}")
        print(f"Asset meta: {asset.meta}")
        
        # Add asset to project
        project.assets.append(asset)
        print(f"Added asset to project. Total assets: {len(project.assets)}")
        
        # Save project
        manager.save_project()
        print("Project saved successfully")
        
        # Load project back
        loaded_project = manager.load_project(str(Path(project.path) / "00_Pipeline" / "pipeline.json"))
        print(f"Loaded project: {loaded_project.name}")
        print(f"Loaded assets: {len(loaded_project.assets)}")
        
        if loaded_project.assets:
            print(f"First asset: {loaded_project.assets[0].name}")
        
        return True
        
    except Exception as e:
        print(f"Error during asset creation test: {e}")
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
    success = test_asset_creation()
    if success:
        print("Asset creation test PASSED")
    else:
        print("Asset creation test FAILED")
