#!/usr/bin/env python3
"""
Test script for Vogue Manager backend functionality
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

def test_recent_projects():
    """Test recent projects functionality"""
    print("Testing recent projects functionality...")

    try:
        from vogue_core.settings import settings

        # Test adding a recent project
        test_project_path = os.path.join(os.getcwd(), '..', 'test_projects', 'TestProject')
        settings.add_recent_project('TestProject', test_project_path)

        # Test getting recent projects
        recent_projects = settings.get_recent_projects()
        print(f'✓ Recent projects loaded: {len(recent_projects)} projects')

        for project in recent_projects:
            print(f'  - {project["name"]}: {project["path"]}')

        # Test clearing recent projects
        settings.clear_recent_projects()
        recent_projects_after_clear = settings.get_recent_projects()
        print(f'✓ Recent projects cleared: {len(recent_projects_after_clear)} projects remaining')

        return True

    except Exception as e:
        print(f'✗ Error in recent projects functionality: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_project_loading():
    """Test project loading functionality"""
    print("\nTesting project loading functionality...")

    try:
        from vogue_core.manager import ProjectManager

        manager = ProjectManager()

        # Try to load the test project
        project_path = os.path.join(os.getcwd(), '..', 'test_projects', 'TestProject')
        project = manager.load_project(project_path)

        print(f'✓ Project loaded successfully: {project.name}')
        print(f'✓ Project path: {project.path}')
        print(f'✓ Assets count: {len(project.assets)}')
        print(f'✓ Shots count: {len(project.shots)}')
        print(f'✓ FPS: {project.fps}')
        print(f'✓ Resolution: {project.resolution}')

        return True

    except Exception as e:
        print(f'✗ Error in project loading: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_asset_creation():
    """Test asset creation functionality"""
    print("\nTesting asset creation functionality...")

    try:
        from vogue_core.models import Asset, Version

        # Create a test asset
        asset = Asset(
            name="TestCharacter",
            type="Character",
            path="/test/path/TestCharacter",
            meta={"artist": "TestArtist", "description": "Test character"}
        )

        print(f'✓ Asset created: {asset.name}')
        print(f'✓ Asset type: {asset.type}')
        print(f'✓ Asset path: {asset.path}')

        # Test version creation
        from datetime import datetime
        version = Version(
            version="v001",
            user="TestUser",
            date=datetime.now().isoformat(),
            comment="Initial version"
        )

        print(f'✓ Version created: {version.version}')
        print(f'✓ Version user: {version.user}')

        return True

    except Exception as e:
        print(f'✗ Error in asset creation: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Starting Vogue Manager Backend Tests")
    print("=" * 50)

    tests = [
        test_recent_projects,
        test_project_loading,
        test_asset_creation,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
