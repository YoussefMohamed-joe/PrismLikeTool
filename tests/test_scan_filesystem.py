"""
Test filesystem scanning functionality

Tests filesystem scanning and project data reconciliation.
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
from vogue_core.fs import scan_assets, scan_shots, scan_filesystem_for_versions


class TestFilesystemScanning:
    """Test filesystem scanning functionality"""
    
    def test_scan_assets_empty_directory(self):
        """Test scanning empty assets directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty assets directory
            assets_dir = Path(temp_dir) / "01_Assets"
            assets_dir.mkdir(parents=True)
            
            # Scan assets
            assets = scan_assets(temp_dir)
            assert len(assets) == 0
    
    def test_scan_assets_with_folders(self):
        """Test scanning assets directory with folders"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create assets directory structure
            assets_dir = Path(temp_dir) / "01_Assets"
            characters_dir = assets_dir / "Characters"
            props_dir = assets_dir / "Props"
            environments_dir = assets_dir / "Environments"
            
            # Create asset folders
            (characters_dir / "char_A").mkdir(parents=True)
            (characters_dir / "char_B").mkdir(parents=True)
            (props_dir / "prop_1").mkdir(parents=True)
            (environments_dir / "env_1").mkdir(parents=True)
            
            # Scan assets
            assets = scan_assets(temp_dir)
            assert len(assets) == 4
            
            # Check asset data
            asset_names = [asset["name"] for asset in assets]
            asset_types = [asset["type"] for asset in assets]
            
            assert "char_A" in asset_names
            assert "char_B" in asset_names
            assert "prop_1" in asset_names
            assert "env_1" in asset_names
            
            assert "Characters" in asset_types
            assert "Props" in asset_types
            assert "Environments" in asset_types
    
    def test_scan_assets_with_meta_files(self):
        """Test scanning assets with meta.json files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create assets directory structure
            assets_dir = Path(temp_dir) / "01_Assets"
            characters_dir = assets_dir / "Characters"
            char_a_dir = characters_dir / "char_A"
            char_a_dir.mkdir(parents=True)
            
            # Create meta.json file
            meta_file = char_a_dir / "meta.json"
            meta_data = {"notes": "Main character", "priority": "high"}
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f)
            
            # Scan assets
            assets = scan_assets(temp_dir)
            assert len(assets) == 1
            
            asset = assets[0]
            assert asset["name"] == "char_A"
            assert asset["type"] == "Characters"
            assert asset["meta"] == meta_data
    
    def test_scan_assets_ignores_dot_files(self):
        """Test that scan_assets ignores dot files and directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create assets directory structure
            assets_dir = Path(temp_dir) / "01_Assets"
            characters_dir = assets_dir / "Characters"
            characters_dir.mkdir(parents=True)
            
            # Create asset folder
            (characters_dir / "char_A").mkdir(parents=True)
            
            # Create dot files and directories
            (characters_dir / ".hidden").mkdir(parents=True)
            (characters_dir / ".gitkeep").touch()
            
            # Scan assets
            assets = scan_assets(temp_dir)
            assert len(assets) == 1
            assert assets[0]["name"] == "char_A"
    
    def test_scan_shots_empty_directory(self):
        """Test scanning empty shots directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty shots directory
            shots_dir = Path(temp_dir) / "02_Shots"
            shots_dir.mkdir(parents=True)
            
            # Scan shots
            shots = scan_shots(temp_dir)
            assert len(shots) == 0
    
    def test_scan_shots_with_folders(self):
        """Test scanning shots directory with folders"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create shots directory structure
            shots_dir = Path(temp_dir) / "02_Shots"
            sq01_dir = shots_dir / "sq01"
            sq02_dir = shots_dir / "sq02"
            
            # Create shot folders
            (sq01_dir / "sh010").mkdir(parents=True)
            (sq01_dir / "sh020").mkdir(parents=True)
            (sq02_dir / "sh010").mkdir(parents=True)
            (sq02_dir / "sh020").mkdir(parents=True)
            
            # Scan shots
            shots = scan_shots(temp_dir)
            assert len(shots) == 4
            
            # Check shot data
            shot_keys = [f"{shot['sequence']}/{shot['name']}" for shot in shots]
            
            assert "sq01/sh010" in shot_keys
            assert "sq01/sh020" in shot_keys
            assert "sq02/sh010" in shot_keys
            assert "sq02/sh020" in shot_keys
    
    def test_scan_shots_with_meta_files(self):
        """Test scanning shots with meta.json files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create shots directory structure
            shots_dir = Path(temp_dir) / "02_Shots"
            sq01_dir = shots_dir / "sq01"
            sh010_dir = sq01_dir / "sh010"
            sh010_dir.mkdir(parents=True)
            
            # Create meta.json file
            meta_file = sh010_dir / "meta.json"
            meta_data = {"notes": "Opening shot", "duration": 120}
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f)
            
            # Scan shots
            shots = scan_shots(temp_dir)
            assert len(shots) == 1
            
            shot = shots[0]
            assert shot["sequence"] == "sq01"
            assert shot["name"] == "sh010"
            assert shot["meta"] == meta_data
    
    def test_scan_filesystem_for_versions_assets(self):
        """Test scanning filesystem for asset versions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create project structure
            project_path = Path(temp_dir) / "TestProject"
            scenes_dir = project_path / "06_Scenes" / "Assets" / "Characters"
            char_a_dir = scenes_dir / "char_A"
            char_a_dir.mkdir(parents=True)
            
            # Create version files
            version_files = [
                "char_A_v001.ma",
                "char_A_v002.ma",
                "char_A_v003.ma"
            ]
            
            for version_file in version_files:
                file_path = char_a_dir / version_file
                file_path.write_text(f"# Maya ASCII file {version_file}")
            
            # Scan versions
            versions = scan_filesystem_for_versions(str(project_path))
            
            # Check versions
            assert "char_A" in versions
            char_versions = versions["char_A"]
            assert len(char_versions) == 3
            
            version_numbers = [v["version"] for v in char_versions]
            assert "v001" in version_numbers
            assert "v002" in version_numbers
            assert "v003" in version_numbers
    
    def test_scan_filesystem_for_versions_shots(self):
        """Test scanning filesystem for shot versions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create project structure
            project_path = Path(temp_dir) / "TestProject"
            scenes_dir = project_path / "06_Scenes" / "Shots" / "sq01"
            sh010_dir = scenes_dir / "sh010"
            sh010_dir.mkdir(parents=True)
            
            # Create version files
            version_files = [
                "sh010_v001.ma",
                "sh010_v002.ma"
            ]
            
            for version_file in version_files:
                file_path = sh010_dir / version_file
                file_path.write_text(f"# Maya ASCII file {version_file}")
            
            # Scan versions
            versions = scan_filesystem_for_versions(str(project_path))
            
            # Check versions
            assert "sq01/sh010" in versions
            shot_versions = versions["sq01/sh010"]
            assert len(shot_versions) == 2
            
            version_numbers = [v["version"] for v in shot_versions]
            assert "v001" in version_numbers
            assert "v002" in version_numbers
    
    def test_scan_filesystem_for_versions_ignores_invalid_files(self):
        """Test that scan_filesystem_for_versions ignores invalid files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create project structure
            project_path = Path(temp_dir) / "TestProject"
            scenes_dir = project_path / "06_Scenes" / "Assets" / "Characters"
            char_a_dir = scenes_dir / "char_A"
            char_a_dir.mkdir(parents=True)
            
            # Create valid and invalid files
            valid_file = char_a_dir / "char_A_v001.ma"
            valid_file.write_text("# Maya ASCII file")
            
            invalid_file = char_a_dir / "char_A_base.ma"  # No version number
            invalid_file.write_text("# Maya ASCII file")
            
            other_file = char_a_dir / "other_file.txt"  # Wrong extension
            other_file.write_text("Text file")
            
            # Scan versions
            versions = scan_filesystem_for_versions(str(project_path))
            
            # Check only valid version was found
            assert "char_A" in versions
            char_versions = versions["char_A"]
            assert len(char_versions) == 1
            assert char_versions[0]["version"] == "v001"
    
    def test_manager_scan_filesystem(self):
        """Test ProjectManager.scan_filesystem method"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Create filesystem structure manually
            assets_dir = Path(project.path) / "01_Assets" / "Characters"
            char_a_dir = assets_dir / "char_A"
            char_a_dir.mkdir(parents=True)
            
            shots_dir = Path(project.path) / "02_Shots" / "sq01"
            sh010_dir = shots_dir / "sh010"
            sh010_dir.mkdir(parents=True)
            
            # Create version files
            char_version_file = char_a_dir / "char_A_v001.ma"
            char_version_file.write_text("# Maya ASCII file")
            
            shot_version_file = sh010_dir / "sh010_v001.ma"
            shot_version_file.write_text("# Maya ASCII file")
            
            # Scan filesystem
            manager.scan_filesystem(update_missing=True)
            
            # Check assets were added
            assets = manager.list_assets()
            assert len(assets) == 1
            assert assets[0].name == "char_A"
            assert assets[0].type == "Characters"
            
            # Check shots were added
            shots = manager.list_shots()
            assert len(shots) == 1
            assert shots[0].sequence == "sq01"
            assert shots[0].name == "sh010"
            
            # Check versions were added
            char_versions = manager.list_versions("char_A")
            assert len(char_versions) == 1
            assert char_versions[0].version == "v001"
            
            shot_versions = manager.list_versions("sq01/sh010")
            assert len(shot_versions) == 1
            assert shot_versions[0].version == "v001"
    
    def test_manager_scan_filesystem_no_update(self):
        """Test ProjectManager.scan_filesystem with update_missing=False"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Create filesystem structure manually
            assets_dir = Path(project.path) / "01_Assets" / "Characters"
            char_a_dir = assets_dir / "char_A"
            char_a_dir.mkdir(parents=True)
            
            # Create version file
            char_version_file = char_a_dir / "char_A_v001.ma"
            char_version_file.write_text("# Maya ASCII file")
            
            # Scan filesystem without updating
            manager.scan_filesystem(update_missing=False)
            
            # Check assets were NOT added
            assets = manager.list_assets()
            assert len(assets) == 0
            
            # Check versions were NOT added
            char_versions = manager.list_versions("char_A")
            assert len(char_versions) == 0
    
    def test_scan_filesystem_with_existing_data(self):
        """Test scanning filesystem with existing project data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add existing asset
            manager.add_asset("Characters", "char_A")
            
            # Create additional filesystem structure
            assets_dir = Path(project.path) / "01_Assets" / "Props"
            prop_1_dir = assets_dir / "prop_1"
            prop_1_dir.mkdir(parents=True)
            
            # Create version file for existing asset
            char_a_dir = Path(project.path) / "01_Assets" / "Characters" / "char_A"
            char_version_file = char_a_dir / "char_A_v001.ma"
            char_version_file.write_text("# Maya ASCII file")
            
            # Scan filesystem
            manager.scan_filesystem(update_missing=True)
            
            # Check existing asset is still there
            assets = manager.list_assets()
            assert len(assets) == 2  # Original + new
            
            asset_names = [asset.name for asset in assets]
            assert "char_A" in asset_names
            assert "prop_1" in asset_names
            
            # Check version was added for existing asset
            char_versions = manager.list_versions("char_A")
            assert len(char_versions) == 1
            assert char_versions[0].version == "v001"
    
    def test_scan_filesystem_error_handling(self):
        """Test filesystem scanning error handling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Create invalid meta.json file
            assets_dir = Path(project.path) / "01_Assets" / "Characters"
            char_a_dir = assets_dir / "char_A"
            char_a_dir.mkdir(parents=True)
            
            meta_file = char_a_dir / "meta.json"
            meta_file.write_text("invalid json content")
            
            # Scan filesystem (should handle invalid JSON gracefully)
            manager.scan_filesystem(update_missing=True)
            
            # Check asset was still added with empty meta
            assets = manager.list_assets()
            assert len(assets) == 1
            assert assets[0].name == "char_A"
            assert assets[0].meta == {}  # Should be empty due to invalid JSON
