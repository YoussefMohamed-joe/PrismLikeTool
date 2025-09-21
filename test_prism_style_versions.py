#!/usr/bin/env python3
"""
Test script for Prism-style Version Management

This script demonstrates the new Prism-style right-click functionality for version creation.
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
    print("=== Creating Prism-Style Test Project ===")
    
    manager = ProjectManager()
    
    # Create test project
    project_path = "test_projects/PrismStyleTest"
    project = manager.create_project(
        name="PrismStyleTest",
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


def demonstrate_prism_features():
    """Demonstrate the Prism-style features"""
    print("\n=== Prism-Style Version Management Features ===")
    print()
    print("🎯 RIGHT-CLICK FUNCTIONALITY (Like Prism VFX):")
    print("1. Right-click anywhere in the version table")
    print("2. See professional context menu with:")
    print("   - ➕ Create Version (submenu with DCC apps)")
    print("   - 🎨 Open with [DCC App] (if version selected)")
    print("   - 📋 Copy Version (if version selected)")
    print("   - 🗑️ Delete Version (if version selected)")
    print("   - 🔄 Refresh")
    print("   - 📥 Import Version")
    print("   - 📤 Export Version")
    print()
    print("🎨 DCC APP INTEGRATION:")
    print("- 🎨 Maya - 3D Animation & Modeling")
    print("- 🎭 Blender - 3D Creation Suite")
    print("- 🌀 Houdini - 3D Animation & VFX")
    print("- 🎬 Nuke - Compositing")
    print("- 📐 3ds Max - 3D Modeling & Animation")
    print("- 🎪 Cinema 4D - 3D Motion Graphics")
    print()
    print("📋 VERSION CREATION WORKFLOW:")
    print("1. Select an asset in the left panel")
    print("2. Select a task (automatically selected)")
    print("3. Right-click in version table")
    print("4. Choose 'Create Version' → Select DCC app")
    print("5. Task name is pre-filled")
    print("6. Add comment and create version")
    print()
    print("📥 IMPORT/EXPORT FEATURES:")
    print("- Import existing DCC files as versions")
    print("- Export versions to new locations")
    print("- Automatic DCC app detection from file extension")
    print("- Professional file dialogs with proper filters")
    print()
    print("🎯 PROFESSIONAL INTERFACE:")
    print("- Dark theme with Prism-style colors")
    print("- Icons and tooltips for all actions")
    print("- Context-aware menus and dialogs")
    print("- Visual feedback and status indicators")
    print("- Right-click hint at bottom of version table")


def main_test():
    """Run the test"""
    print("Vogue Manager - Prism-Style Version Management Test")
    print("=" * 60)
    
    # Create test project
    manager = create_test_project()
    
    # Demonstrate features
    demonstrate_prism_features()
    
    print("\n" + "=" * 60)
    print("Test project created successfully!")
    print()
    print("🚀 TO TEST THE PRISM-STYLE FEATURES:")
    print("1. Run: python src/vogue_app/main.py")
    print("2. Load the 'PrismStyleTest' project")
    print("3. Select an asset in the left panel")
    print("4. Select a task (first one auto-selected)")
    print("5. RIGHT-CLICK in the version table")
    print("6. Explore the professional context menu")
    print("7. Create versions with different DCC apps")
    print("8. Try import/export functionality")
    print()
    print("✨ EXPECTED BEHAVIOR:")
    print("- Right-click anywhere in version table shows context menu")
    print("- Professional menu with icons and descriptions")
    print("- DCC app submenu with all available applications")
    print("- Task name pre-filled in creation dialogs")
    print("- Import/export with proper file filters")
    print("- Visual feedback and status messages")
    print("- Prism-like professional appearance")


if __name__ == "__main__":
    main_test()
