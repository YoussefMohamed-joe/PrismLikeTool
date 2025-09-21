#!/usr/bin/env python3
"""
Test script for Task Selection and Version Management Features

This script demonstrates the new task selection behavior and right-click version creation.
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from vogue_core.manager import ProjectManager
from vogue_core.models import Project, Asset, Department, Task
from vogue_app.main import main


def create_test_project():
    """Create a test project with departments and tasks"""
    print("=== Creating Test Project ===")
    
    manager = ProjectManager()
    
    # Create test project
    project_path = "test_projects/TaskSelectionTest"
    project = manager.create_project(
        name="TaskSelectionTest",
        parent_dir="test_projects",
        fps=24,
        resolution=[1920, 1080]
    )
    
    print(f"Created project: {project.name}")
    
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
    
    # Add tasks for each department
    tasks = [
        # Modeling tasks
        Task("modeling", "Modeling", "WIP"),
        Task("texturing", "Modeling", "Pending"),
        Task("rigging", "Modeling", "Pending"),
        
        # Animation tasks
        Task("animation", "Animation", "Pending"),
        Task("fx_animation", "Animation", "Pending"),
        
        # Lighting tasks
        Task("lighting", "Lighting", "Pending"),
        Task("rendering", "Lighting", "Pending"),
        
        # Compositing tasks
        Task("compositing", "Compositing", "Pending"),
        Task("color_grading", "Compositing", "Pending")
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


def test_task_selection_behavior():
    """Test the task selection behavior"""
    print("\n=== Task Selection Behavior ===")
    print("The following behavior should be observed:")
    print("1. When you select an asset, the first task should be automatically selected")
    print("2. Task selection should persist when clicking elsewhere (like departments)")
    print("3. When you select a different task, it should remain selected")
    print("4. The version manager should show the selected asset and task")
    print("5. Right-clicking in the version table should show DCC app creation options")
    print("6. The task name should be pre-filled in the version creation dialog")


def main_test():
    """Run the test"""
    print("Vogue Manager Task Selection and Version Management Test")
    print("=" * 60)
    
    # Create test project
    manager = create_test_project()
    
    # Test task selection behavior
    test_task_selection_behavior()
    
    print("\n" + "=" * 60)
    print("Test project created successfully!")
    print()
    print("To test the UI:")
    print("1. Run: python src/vogue_app/main.py")
    print("2. Load the 'TaskSelectionTest' project")
    print("3. Select an asset in the left panel")
    print("4. Observe that the first task is automatically selected")
    print("5. Select different tasks and notice they stay selected")
    print("6. Right-click in the version table to create versions")
    print("7. Notice the task name is pre-filled in the dialog")
    print()
    print("Expected behavior:")
    print("- Tasks behave like departments with persistent selection")
    print("- Version manager shows 'AssetName - TaskName' format")
    print("- Right-click context menu always shows DCC app creation options")
    print("- Version creation dialog pre-fills the current task name")


if __name__ == "__main__":
    main_test()
