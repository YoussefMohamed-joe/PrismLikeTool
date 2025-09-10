#!/usr/bin/env python3
"""Test asset dialog creation"""

import sys
import os
sys.path.insert(0, 'src')

from PyQt6.QtWidgets import QApplication
from vogue_core.manager import ProjectManager
from vogue_app.dialogs import AssetDialog
from pathlib import Path

def test_dialog_asset_creation():
    """Test asset dialog creation"""
    print("Testing asset dialog creation...")
    
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
            
            # Create the dialog with None as parent (it should work)
            dialog = AssetDialog(None)
            print("Created AssetDialog successfully")
            
            # Test getting data from dialog (with default values)
            dialog.name_edit.setText("TestAsset")
            dialog.description_edit.setPlainText("Test description")
            dialog.tags_edit.setText("test, asset")
            dialog.artist_edit.setText("TestArtist")
            
            data = dialog.get_asset_data()
            print(f"Dialog data: {data}")
            
            if data:
                print("Asset dialog data retrieval SUCCESS")
                return True
            else:
                print("Asset dialog data retrieval FAILED")
                return False
                
        finally:
            # Cleanup
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)
                print("Cleaned up test directory")
                
    except Exception as e:
        print(f"Error during dialog test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dialog_asset_creation()
    if success:
        print("Dialog asset creation test PASSED")
    else:
        print("Dialog asset creation test FAILED")
