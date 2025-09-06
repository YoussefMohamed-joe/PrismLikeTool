"""
Test shot management functionality

Tests shot creation, listing, and version management.
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
from vogue_core.models import Shot, Version


class TestShotManagement:
    """Test shot management functionality"""
    
    def test_add_shot(self):
        """Test adding a shot to a project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add a shot
            shot = manager.add_shot("sq01", "sh010", {"notes": "Opening shot"})
            
            # Check shot object
            assert shot.sequence == "sq01"
            assert shot.name == "sh010"
            assert shot.meta["notes"] == "Opening shot"
            assert shot.key == "sq01/sh010"
            
            # Check shot directory was created
            shot_dir = Path(project.path) / "02_Shots" / "sq01" / "sh010"
            assert shot_dir.exists()
            assert shot_dir.is_dir()
            
            # Check shot is in project
            assert len(project.shots) == 1
            assert project.shots[0].sequence == "sq01"
            assert project.shots[0].name == "sh010"
    
    def test_add_duplicate_shot(self):
        """Test adding a duplicate shot fails"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add first shot
            manager.add_shot("sq01", "sh010")
            
            # Try to add duplicate shot
            with pytest.raises(ValueError, match="already exists"):
                manager.add_shot("sq01", "sh010")
    
    def test_list_shots(self):
        """Test listing shots"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add multiple shots
            manager.add_shot("sq01", "sh010")
            manager.add_shot("sq01", "sh020")
            manager.add_shot("sq02", "sh010")
            manager.add_shot("sq02", "sh020")
            
            # List shots
            shots = manager.list_shots()
            assert len(shots) == 4
            
            # Check shot keys
            shot_keys = [shot.key for shot in shots]
            assert "sq01/sh010" in shot_keys
            assert "sq01/sh020" in shot_keys
            assert "sq02/sh010" in shot_keys
            assert "sq02/sh020" in shot_keys
    
    def test_get_shot(self):
        """Test getting a shot by sequence and name"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add a shot
            manager.add_shot("sq01", "sh010")
            
            # Get shot
            shot = manager.get_shot("sq01", "sh010")
            assert shot is not None
            assert shot.sequence == "sq01"
            assert shot.name == "sh010"
            assert shot.key == "sq01/sh010"
            
            # Get non-existent shot
            shot = manager.get_shot("sq01", "sh999")
            assert shot is None
    
    def test_shot_validation(self):
        """Test shot validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Test empty sequence
            with pytest.raises(ValueError, match="sequence cannot be empty"):
                manager.add_shot("", "sh010")
            
            # Test empty name
            with pytest.raises(ValueError, match="name cannot be empty"):
                manager.add_shot("sq01", "")
    
    def test_shot_serialization(self):
        """Test shot serialization to/from JSON"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add shot with metadata
            manager.add_shot("sq01", "sh010", {"notes": "Opening shot", "duration": 120})
            
            # Save project
            manager.save_project()
            
            # Load project in new manager
            manager2 = ProjectManager()
            loaded_project = manager2.load_project(project.path)
            
            # Check shot was loaded correctly
            assert len(loaded_project.shots) == 1
            shot = loaded_project.shots[0]
            assert shot.sequence == "sq01"
            assert shot.name == "sh010"
            assert shot.meta["notes"] == "Opening shot"
            assert shot.meta["duration"] == 120
    
    def test_shot_versions(self):
        """Test shot version management"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add a shot
            manager.add_shot("sq01", "sh010")
            
            # Create a dummy source file
            source_file = Path(temp_dir) / "source.ma"
            source_file.write_text("# Maya ASCII file")
            
            # Add version
            version = manager.add_version("sq01/sh010", str(source_file), "test_user", "Initial version")
            
            # Check version object
            assert version.version == "v001"
            assert version.user == "test_user"
            assert version.comment == "Initial version"
            assert version.path.endswith("sh010_v001.ma")
            
            # Check version file was copied
            assert Path(version.path).exists()
            
            # Check version is in project
            versions = manager.list_versions("sq01/sh010")
            assert len(versions) == 1
            assert versions[0].version == "v001"
    
    def test_shot_version_auto_increment(self):
        """Test shot version auto-increment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add a shot
            manager.add_shot("sq01", "sh010")
            
            # Create dummy source files
            source_file1 = Path(temp_dir) / "source1.ma"
            source_file1.write_text("# Maya ASCII file 1")
            
            source_file2 = Path(temp_dir) / "source2.ma"
            source_file2.write_text("# Maya ASCII file 2")
            
            # Add first version
            version1 = manager.add_version("sq01/sh010", str(source_file1), "user1", "Version 1")
            assert version1.version == "v001"
            
            # Add second version
            version2 = manager.add_version("sq01/sh010", str(source_file2), "user2", "Version 2")
            assert version2.version == "v002"
            
            # Check both versions exist
            versions = manager.list_versions("sq01/sh010")
            assert len(versions) == 2
            
            version_numbers = [v.version for v in versions]
            assert "v001" in version_numbers
            assert "v002" in version_numbers
    
    def test_shot_version_manual_version(self):
        """Test shot version with manual version number"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add a shot
            manager.add_shot("sq01", "sh010")
            
            # Create dummy source file
            source_file = Path(temp_dir) / "source.ma"
            source_file.write_text("# Maya ASCII file")
            
            # Add version with manual version number
            version = manager.add_version("sq01/sh010", str(source_file), "test_user", "Manual version", "v005")
            assert version.version == "v005"
            
            # Check version is in project
            versions = manager.list_versions("sq01/sh010")
            assert len(versions) == 1
            assert versions[0].version == "v005"
    
    def test_shot_version_validation(self):
        """Test shot version validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add a shot
            manager.add_shot("sq01", "sh010")
            
            # Create dummy source file
            source_file = Path(temp_dir) / "source.ma"
            source_file.write_text("# Maya ASCII file")
            
            # Test invalid version format
            with pytest.raises(ValueError, match="must start with 'v'"):
                manager.add_version("sq01/sh010", str(source_file), "test_user", "Invalid version", "001")
            
            # Test invalid version number
            with pytest.raises(ValueError, match="Version number must be >= 1"):
                manager.add_version("sq01/sh010", str(source_file), "test_user", "Invalid version", "v000")
    
    def test_shot_key_generation(self):
        """Test shot key generation"""
        shot = Shot(sequence="sq01", name="sh010")
        assert shot.key == "sq01/sh010"
        
        shot = Shot(sequence="sq02", name="sh020")
        assert shot.key == "sq02/sh020"
    
    def test_mixed_asset_shot_versions(self):
        """Test that asset and shot versions don't interfere with each other"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add asset and shot
            manager.add_asset("Characters", "char_A")
            manager.add_shot("sq01", "sh010")
            
            # Create dummy source files
            asset_source = Path(temp_dir) / "asset_source.ma"
            asset_source.write_text("# Asset Maya file")
            
            shot_source = Path(temp_dir) / "shot_source.ma"
            shot_source.write_text("# Shot Maya file")
            
            # Add versions for both
            asset_version = manager.add_version("char_A", str(asset_source), "user1", "Asset version")
            shot_version = manager.add_version("sq01/sh010", str(shot_source), "user2", "Shot version")
            
            # Check versions are separate
            assert asset_version.version == "v001"
            assert shot_version.version == "v001"
            
            # Check versions are stored separately
            asset_versions = manager.list_versions("char_A")
            shot_versions = manager.list_versions("sq01/sh010")
            
            assert len(asset_versions) == 1
            assert len(shot_versions) == 1
            assert asset_versions[0].version == "v001"
            assert shot_versions[0].version == "v001"
