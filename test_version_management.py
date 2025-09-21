#!/usr/bin/env python3
"""
Test script for Vogue Manager Version Management with DCC Integration

This script demonstrates the new version management features including:
- DCC application integration (Maya, Blender, etc.)
- Version creation with context menus
- Thumbnail generation
- Professional version manager UI
- Version actions (open, copy, delete)
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from vogue_core.manager import ProjectManager
from vogue_core.dcc_integration import dcc_manager
from vogue_core.models import Project, Asset, Department, Task
from vogue_app.main import main


def test_dcc_integration():
    """Test DCC application integration"""
    print("=== Testing DCC Integration ===")
    
    # List available DCC apps
    apps = dcc_manager.list_apps()
    print(f"Available DCC applications: {len(apps)}")
    
    for app in apps:
        print(f"  - {app.display_name} ({app.name})")
        print(f"    Executable: {app.executable_path}")
        print(f"    Extensions: {app.file_extensions}")
        print(f"    Icon: {app.get_dcc_app_icon()}")
        print()
    
    return len(apps) > 0


def test_project_creation():
    """Test project creation with DCC support"""
    print("=== Testing Project Creation ===")
    
    manager = ProjectManager()
    
    # Create test project
    project_path = "test_projects/VersionTestProject"
    project = manager.create_project(
        name="VersionTestProject",
        parent_dir="test_projects",
        fps=24,
        resolution=[1920, 1080]
    )
    
    print(f"Created project: {project.name}")
    print(f"Project path: {project.path}")
    
    # Add departments
    departments = [
        Department("Modeling", "3D modeling and sculpting", "#3498db"),
        Department("Animation", "Character and object animation", "#e74c3c"),
        Department("Lighting", "Scene lighting and rendering", "#f39c12"),
        Department("Compositing", "Final compositing and effects", "#9b59b6")
    ]
    
    for dept in departments:
        project.departments.append(dept)
    
    print(f"Added {len(departments)} departments")
    
    # Add tasks
    tasks = [
        Task("modeling", "Modeling", "WIP"),
        Task("texturing", "Modeling", "Pending"),
        Task("rigging", "Modeling", "Pending"),
        Task("animation", "Animation", "Pending"),
        Task("lighting", "Lighting", "Pending"),
        Task("rendering", "Lighting", "Pending"),
        Task("compositing", "Compositing", "Pending")
    ]
    
    for task in tasks:
        project.tasks.append(task)
    
    print(f"Added {len(tasks)} tasks")
    
    # Add test assets
    assets = [
        Asset("Character_Hero", "Character"),
        Asset("Environment_City", "Environment"),
        Asset("Prop_Weapon", "Prop"),
        Asset("Vehicle_Car", "Vehicle")
    ]
    
    for asset in assets:
        project.add_asset(asset)
    
    print(f"Added {len(assets)} assets")
    
    # Save project
    manager.save_project()
    print("Project saved successfully")
    
    return manager


def test_version_creation():
    """Test DCC version creation"""
    print("=== Testing Version Creation ===")
    
    manager = ProjectManager()
    manager.load_project("test_projects/VersionTestProject")
    
    if not manager.current_project:
        print("No project loaded")
        return False
    
    # Get available DCC apps
    dcc_apps = manager.get_dcc_apps()
    if not dcc_apps:
        print("No DCC applications available")
        return False
    
    # Test version creation with first available DCC app
    dcc_app = dcc_apps[0]
    print(f"Using DCC app: {dcc_app['display_name']}")
    
    # Create versions for each asset
    for asset in manager.current_project.assets:
        try:
            version = manager.create_dcc_version(
                entity_key=asset.name,
                dcc_app=dcc_app['name'],
                task_name="modeling",
                user="TestUser",
                comment=f"Test version for {asset.name}"
            )
            
            print(f"Created version {version.version} for {asset.name}")
            print(f"  DCC App: {version.dcc_app}")
            print(f"  Task: {version.task_name}")
            print(f"  Status: {version.status}")
            print(f"  Path: {version.path}")
            print(f"  Thumbnail: {version.thumbnail}")
            print()
            
        except Exception as e:
            print(f"Failed to create version for {asset.name}: {e}")
    
    return True


def test_version_management():
    """Test version management features"""
    print("=== Testing Version Management ===")
    
    manager = ProjectManager()
    manager.load_project("test_projects/VersionTestProject")
    
    if not manager.current_project:
        print("No project loaded")
        return False
    
    # Test version listing
    for asset in manager.current_project.assets:
        versions = manager.list_versions(asset.name)
        print(f"Asset '{asset.name}' has {len(versions)} versions:")
        
        for version in versions:
            print(f"  - {version.version} ({version.dcc_app}) - {version.status}")
            print(f"    User: {version.user}")
            print(f"    Date: {version.date}")
            print(f"    Comment: {version.comment}")
            print(f"    Icon: {version.get_dcc_app_icon()}")
            print()
    
    return True


def test_launch_dcc_apps():
    """Test launching DCC applications"""
    print("=== Testing DCC App Launch ===")
    
    manager = ProjectManager()
    manager.load_project("test_projects/VersionTestProject")
    
    if not manager.current_project:
        print("No project loaded")
        return False
    
    # Get available DCC apps
    dcc_apps = manager.get_dcc_apps()
    if not dcc_apps:
        print("No DCC applications available")
        return False
    
    # Test launching each DCC app
    for app in dcc_apps:
        print(f"Testing launch of {app['display_name']}...")
        
        success = manager.launch_dcc_app(app['name'])
        if success:
            print(f"  ✓ Successfully launched {app['display_name']}")
        else:
            print(f"  ✗ Failed to launch {app['display_name']}")
    
    return True


def main_test():
    """Run all tests"""
    print("Vogue Manager Version Management Test")
    print("=" * 50)
    
    # Test DCC integration
    dcc_available = test_dcc_integration()
    
    if not dcc_available:
        print("Warning: No DCC applications detected")
        print("Make sure Maya, Blender, or other DCC apps are installed")
        print()
    
    # Test project creation
    manager = test_project_creation()
    
    # Test version creation
    if manager:
        test_version_creation()
        test_version_management()
        test_launch_dcc_apps()
    
    print("=" * 50)
    print("Test completed!")
    print()
    print("To test the UI:")
    print("1. Run: python src/vogue_app/main.py")
    print("2. Load the 'VersionTestProject' project")
    print("3. Select an asset in the left panel")
    print("4. Right-click in the version table to create versions")
    print("5. Use the context menu to open versions with DCC apps")


if __name__ == "__main__":
    main_test()
