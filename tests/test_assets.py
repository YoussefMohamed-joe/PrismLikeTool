"""
Test asset management functionality

Tests asset creation, listing, and version management.
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
from vogue_core.models import Asset, Version
from vogue_core.schema import ValidationError


class TestAssetManagement:
    """Test asset management functionality"""
    
    def test_add_asset(self):
        """Test adding an asset to a project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add an asset
            asset = manager.add_asset("Characters", "char_A", {"notes": "Main character"})
            
            # Check asset object
            assert asset.name == "char_A"
            assert asset.type == "Characters"
            assert asset.meta["notes"] == "Main character"
            
            # Check asset directory was created
            asset_dir = Path(project.path) / "01_Assets" / "Characters" / "char_A"
            assert asset_dir.exists()
            assert asset_dir.is_dir()
            
            # Check asset is in project
            assert len(project.assets) == 1
            assert project.assets[0].name == "char_A"
    
    def test_add_duplicate_asset(self):
        """Test adding a duplicate asset fails"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add first asset
            manager.add_asset("Characters", "char_A")
            
            # Try to add duplicate asset
            with pytest.raises(ValueError, match="already exists"):
                manager.add_asset("Characters", "char_A")
    
    def test_list_assets(self):
        """Test listing assets"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add multiple assets
            manager.add_asset("Characters", "char_A")
            manager.add_asset("Characters", "char_B")
            manager.add_asset("Props", "prop_1")
            manager.add_asset("Environments", "env_1")
            
            # List assets
            assets = manager.list_assets()
            assert len(assets) == 4
            
            # Check asset names
            asset_names = [asset.name for asset in assets]
            assert "char_A" in asset_names
            assert "char_B" in asset_names
            assert "prop_1" in asset_names
            assert "env_1" in asset_names
    
    def test_get_asset(self):
        """Test getting an asset by name"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add an asset
            manager.add_asset("Characters", "char_A")
            
            # Get asset
            asset = manager.get_asset("char_A")
            assert asset is not None
            assert asset.name == "char_A"
            assert asset.type == "Characters"
            
            # Get non-existent asset
            asset = manager.get_asset("non_existent")
            assert asset is None
    
    def test_asset_validation(self):
        """Test asset validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Test empty name
            with pytest.raises(ValueError, match="name cannot be empty"):
                manager.add_asset("Characters", "")
            
            # Test empty type
            with pytest.raises(ValueError, match="type cannot be empty"):
                manager.add_asset("", "char_A")
    
    def test_asset_serialization(self):
        """Test asset serialization to/from JSON"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add asset with metadata
            manager.add_asset("Characters", "char_A", {"notes": "Main character", "priority": "high"})
            
            # Save project
            manager.save_project()
            
            # Load project in new manager
            manager2 = ProjectManager()
            loaded_project = manager2.load_project(project.path)
            
            # Check asset was loaded correctly
            assert len(loaded_project.assets) == 1
            asset = loaded_project.assets[0]
            assert asset.name == "char_A"
            assert asset.type == "Characters"
            assert asset.meta["notes"] == "Main character"
            assert asset.meta["priority"] == "high"
    
    def test_asset_versions(self):
        """Test asset version management"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add an asset
            manager.add_asset("Characters", "char_A")
            
            # Create a dummy source file
            source_file = Path(temp_dir) / "source.ma"
            source_file.write_text("# Maya ASCII file")
            
            # Add version
            version = manager.add_version("char_A", str(source_file), "test_user", "Initial version")
            
            # Check version object
            assert version.version == "v001"
            assert version.user == "test_user"
            assert version.comment == "Initial version"
            assert version.path.endswith("char_A_v001.ma")
            
            # Check version file was copied
            assert Path(version.path).exists()
            
            # Check version is in project
            versions = manager.list_versions("char_A")
            assert len(versions) == 1
            assert versions[0].version == "v001"
    
    def test_asset_version_auto_increment(self):
        """Test asset version auto-increment"""
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
            version1 = manager.add_version("char_A", str(source_file1), "user1", "Version 1")
            assert version1.version == "v001"
            
            # Add second version
            version2 = manager.add_version("char_A", str(source_file2), "user2", "Version 2")
            assert version2.version == "v002"
            
            # Check both versions exist
            versions = manager.list_versions("char_A")
            assert len(versions) == 2
            
            version_numbers = [v.version for v in versions]
            assert "v001" in version_numbers
            assert "v002" in version_numbers
    
    def test_asset_version_manual_version(self):
        """Test asset version with manual version number"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add an asset
            manager.add_asset("Characters", "char_A")
            
            # Create dummy source file
            source_file = Path(temp_dir) / "source.ma"
            source_file.write_text("# Maya ASCII file")
            
            # Add version with manual version number
            version = manager.add_version("char_A", str(source_file), "test_user", "Manual version", "v005")
            assert version.version == "v005"
            
            # Check version is in project
            versions = manager.list_versions("char_A")
            assert len(versions) == 1
            assert versions[0].version == "v005"
    
    def test_asset_version_validation(self):
        """Test asset version validation"""
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
