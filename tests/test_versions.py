"""
Test version management functionality

Tests version creation, auto-increment, and file operations.
"""

import pytest
import tempfile
import json
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vogue_core.manager import ProjectManager
from vogue_core.models import Version
from vogue_core.fs import next_version


class TestVersionManagement:
    """Test version management functionality"""
    
    def test_next_version_generation(self):
        """Test next version generation"""
        # Test empty list
        assert next_version([]) == "v001"
        
        # Test single version
        assert next_version(["v001"]) == "v002"
        
        # Test multiple versions
        assert next_version(["v001", "v002", "v003"]) == "v004"
        
        # Test non-sequential versions
        assert next_version(["v001", "v003", "v005"]) == "v006"
        
        # Test with invalid versions (should be ignored)
        assert next_version(["v001", "invalid", "v002"]) == "v003"
        
        # Test with versions not starting with 'v'
        assert next_version(["v001", "001", "v002"]) == "v003"
    
    def test_add_version_auto_increment(self):
        """Test adding versions with auto-increment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add an asset
            manager.add_asset("Characters", "char_A")
            
            # Create dummy source files
            source_files = []
            for i in range(5):
                source_file = Path(temp_dir) / f"source{i}.ma"
                source_file.write_text(f"# Maya ASCII file {i}")
                source_files.append(str(source_file))
            
            # Add multiple versions
            versions = []
            for i, source_file in enumerate(source_files):
                version = manager.add_version("char_A", source_file, f"user{i}", f"Version {i+1}")
                versions.append(version)
            
            # Check version numbers
            expected_versions = ["v001", "v002", "v003", "v004", "v005"]
            actual_versions = [v.version for v in versions]
            assert actual_versions == expected_versions
            
            # Check all versions are in project
            project_versions = manager.list_versions("char_A")
            assert len(project_versions) == 5
            
            # Check version files exist
            for version in versions:
                assert Path(version.path).exists()
                assert version.path.endswith(f"char_A_{version.version}.ma")
    
    def test_add_version_manual_version(self):
        """Test adding versions with manual version numbers"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add an asset
            manager.add_asset("Characters", "char_A")
            
            # Create dummy source file
            source_file = Path(temp_dir) / "source.ma"
            source_file.write_text("# Maya ASCII file")
            
            # Add version with manual version number
            version = manager.add_version("char_A", str(source_file), "test_user", "Manual version", "v010")
            assert version.version == "v010"
            
            # Check version is in project
            versions = manager.list_versions("char_A")
            assert len(versions) == 1
            assert versions[0].version == "v010"
    
    def test_add_version_duplicate_version(self):
        """Test adding duplicate version numbers fails"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add an asset
            manager.add_asset("Characters", "char_A")
            
            # Create dummy source files
            source_file1 = Path(temp_dir) / "source1.ma"
            source_file1.write_text("# Maya ASCII file 1")
            
            source_file2 = Path(temp_dir) / "source2.ma"
            source_file2.write_text("# Maya ASCII file 2")
            
            # Add first version
            manager.add_version("char_A", str(source_file1), "user1", "Version 1", "v001")
            
            # Try to add duplicate version
            with pytest.raises(ValueError, match="already exists"):
                manager.add_version("char_A", str(source_file2), "user2", "Version 2", "v001")
    
    def test_add_version_file_operations(self):
        """Test version file operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add an asset
            manager.add_asset("Characters", "char_A")
            
            # Create source file with content
            source_file = Path(temp_dir) / "source.ma"
            source_content = "# Maya ASCII file\n# Test content\n"
            source_file.write_text(source_content)
            
            # Add version
            version = manager.add_version("char_A", str(source_file), "test_user", "Test version")
            
            # Check version file was copied
            version_path = Path(version.path)
            assert version_path.exists()
            
            # Check content was preserved
            with open(version_path, 'r') as f:
                copied_content = f.read()
            assert copied_content == source_content
            
            # Check file is in correct location
            expected_path = Path(project.path) / "06_Scenes" / "Assets" / "Characters" / "char_A" / "char_A_v001.ma"
            assert version_path == expected_path
    
    def test_add_version_shot_file_operations(self):
        """Test version file operations for shots"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add a shot
            manager.add_shot("sq01", "sh010")
            
            # Create source file with content
            source_file = Path(temp_dir) / "source.ma"
            source_content = "# Maya ASCII file\n# Shot content\n"
            source_file.write_text(source_content)
            
            # Add version
            version = manager.add_version("sq01/sh010", str(source_file), "test_user", "Test version")
            
            # Check version file was copied
            version_path = Path(version.path)
            assert version_path.exists()
            
            # Check content was preserved
            with open(version_path, 'r') as f:
                copied_content = f.read()
            assert copied_content == source_content
            
            # Check file is in correct location
            expected_path = Path(project.path) / "06_Scenes" / "Shots" / "sq01" / "sh010" / "sh010_v001.ma"
            assert version_path == expected_path
    
    def test_version_validation(self):
        """Test version validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add an asset
            manager.add_asset("Characters", "char_A")
            
            # Create dummy source file
            source_file = Path(temp_dir) / "source.ma"
            source_file.write_text("# Maya ASCII file")
            
            # Test invalid version format
            with pytest.raises(ValueError, match="must start with 'v'"):
                manager.add_version("char_A", str(source_file), "test_user", "Invalid version", "001")
            
            # Test invalid version number
            with pytest.raises(ValueError, match="Version number must be >= 1"):
                manager.add_version("char_A", str(source_file), "test_user", "Invalid version", "v000")
            
            # Test negative version number
            with pytest.raises(ValueError, match="Version number must be >= 1"):
                manager.add_version("char_A", str(source_file), "test_user", "Invalid version", "v-001")
    
    def test_version_metadata(self):
        """Test version metadata storage"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add an asset
            manager.add_asset("Characters", "char_A")
            
            # Create dummy source file
            source_file = Path(temp_dir) / "source.ma"
            source_file.write_text("# Maya ASCII file")
            
            # Add version with metadata
            version = manager.add_version("char_A", str(source_file), "test_user", "Test version with metadata")
            
            # Check version metadata
            assert version.user == "test_user"
            assert version.comment == "Test version with metadata"
            assert version.date is not None
            assert version.path is not None
            
            # Check version is stored in project
            versions = manager.list_versions("char_A")
            assert len(versions) == 1
            stored_version = versions[0]
            assert stored_version.user == "test_user"
            assert stored_version.comment == "Test version with metadata"
            assert stored_version.date == version.date
            assert stored_version.path == version.path
    
    def test_version_serialization(self):
        """Test version serialization to/from JSON"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add an asset
            manager.add_asset("Characters", "char_A")
            
            # Create dummy source file
            source_file = Path(temp_dir) / "source.ma"
            source_file.write_text("# Maya ASCII file")
            
            # Add version
            version = manager.add_version("char_A", str(source_file), "test_user", "Test version")
            
            # Save project
            manager.save_project()
            
            # Load project in new manager
            manager2 = ProjectManager()
            loaded_project = manager2.load_project(project.path)
            
            # Check version was loaded correctly
            versions = loaded_project.get_versions("char_A")
            assert len(versions) == 1
            loaded_version = versions[0]
            assert loaded_version.version == "v001"
            assert loaded_version.user == "test_user"
            assert loaded_version.comment == "Test version"
            assert loaded_version.path.endswith("char_A_v001.ma")
    
    def test_version_listing(self):
        """Test version listing functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add an asset
            manager.add_asset("Characters", "char_A")
            
            # Create dummy source files
            source_files = []
            for i in range(3):
                source_file = Path(temp_dir) / f"source{i}.ma"
                source_file.write_text(f"# Maya ASCII file {i}")
                source_files.append(str(source_file))
            
            # Add versions
            for i, source_file in enumerate(source_files):
                manager.add_version("char_A", source_file, f"user{i}", f"Version {i+1}")
            
            # List versions
            versions = manager.list_versions("char_A")
            assert len(versions) == 3
            
            # Check version order (should be in creation order)
            version_numbers = [v.version for v in versions]
            assert version_numbers == ["v001", "v002", "v003"]
            
            # Check non-existent entity
            versions = manager.list_versions("non_existent")
            assert len(versions) == 0
    
    def test_version_file_cleanup(self):
        """Test that source files are not modified during version creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add an asset
            manager.add_asset("Characters", "char_A")
            
            # Create source file
            source_file = Path(temp_dir) / "source.ma"
            source_content = "# Maya ASCII file\n# Original content\n"
            source_file.write_text(source_content)
            
            # Add version
            manager.add_version("char_A", str(source_file), "test_user", "Test version")
            
            # Check source file is unchanged
            with open(source_file, 'r') as f:
                original_content = f.read()
            assert original_content == source_content
            
            # Check version file has the same content
            versions = manager.list_versions("char_A")
            version_path = Path(versions[0].path)
            with open(version_path, 'r') as f:
                version_content = f.read()
            assert version_content == source_content
