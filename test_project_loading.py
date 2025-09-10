#!/usr/bin/env python3
"""
Test script for project loading functionality
"""
import sys
import os
sys.path.append('src')

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from vogue_app.controller import VogueController

def test_project_loading():
    """Test project loading functionality"""
    app = QApplication(sys.argv)
    
    # Create controller
    controller = VogueController()
    
    print("Testing project loading functionality...")
    
    # Test 1: Check if methods exist
    print(f"✅ Load project method exists: {hasattr(controller, 'load_project')}")
    print(f"✅ Auto-load method exists: {hasattr(controller, '_auto_load_last_project')}")
    print(f"✅ Recent projects method exists: {hasattr(controller, 'show_recent_projects')}")
    
    # Test 2: Test with existing project
    test_project_path = "examples/sample_project"
    if os.path.exists(test_project_path):
        print(f"✅ Test project found: {test_project_path}")
        
        # Test loading the project
        try:
            controller.load_project(test_project_path)
            print("✅ Project loaded successfully")
            print(f"✅ Current project: {controller.manager.current_project.name if controller.manager.current_project else 'None'}")
        except Exception as e:
            print(f"❌ Project loading failed: {e}")
    else:
        print("⚠️ Test project not found, skipping load test")
    
    # Test 3: Test recent projects
    try:
        from vogue_core.settings import settings
        recent_projects = settings.get_recent_projects()
        print(f"✅ Recent projects count: {len(recent_projects)}")
        if recent_projects:
            print(f"✅ Most recent project: {recent_projects[0]['name']}")
    except Exception as e:
        print(f"❌ Recent projects test failed: {e}")
    
    print("\n🎉 Project loading tests completed!")
    
    # Show the application briefly
    controller.show()
    QTimer.singleShot(3000, app.quit)
    
    return app.exec()

if __name__ == "__main__":
    test_project_loading()
