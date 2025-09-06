"""
Test JSON integrity and atomic operations

Tests JSON file operations, atomic writes, and data integrity.
"""

import pytest
import tempfile
import json
import os
import shutil
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vogue_core.fs import atomic_write_json
from vogue_core.manager import ProjectManager
from vogue_core.schema import project_to_pipeline, pipeline_to_project


class TestJSONIntegrity:
    """Test JSON file integrity and atomic operations"""
    
    def test_atomic_write_json_basic(self):
        """Test basic atomic JSON write operation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}
            
            # Write JSON atomically
            atomic_write_json(str(test_file), test_data)
            
            # Check file exists
            assert test_file.exists()
            
            # Check content
            with open(test_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data
    
    def test_atomic_write_json_backup(self):
        """Test atomic JSON write with backup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            backup_file = test_file.with_suffix('.json.bak')
            
            # Write initial data
            initial_data = {"key": "initial"}
            atomic_write_json(str(test_file), initial_data)
            
            # Write new data with backup
            new_data = {"key": "updated", "new": "value"}
            atomic_write_json(str(test_file), new_data, backup=True)
            
            # Check backup exists
            assert backup_file.exists()
            
            # Check backup content
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            assert backup_data == initial_data
            
            # Check new content
            with open(test_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            assert loaded_data == new_data
    
    def test_atomic_write_json_utf8(self):
        """Test atomic JSON write with UTF-8 content"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_data = {
                "unicode": "Hello 世界",
                "emoji": "🚀",
                "special": "Special chars: àáâãäåæçèéêë"
            }
            
            # Write JSON atomically
            atomic_write_json(str(test_file), test_data)
            
            # Check content
            with open(test_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data
    
    def test_atomic_write_json_large_data(self):
        """Test atomic JSON write with large data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            
            # Create large data
            large_data = {
                "items": [{"id": i, "data": f"Item {i}"} for i in range(1000)],
                "metadata": {"count": 1000, "description": "Large dataset"}
            }
            
            # Write JSON atomically
            atomic_write_json(str(test_file), large_data)
            
            # Check content
            with open(test_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            assert loaded_data == large_data
    
    def test_atomic_write_json_error_handling(self):
        """Test atomic JSON write error handling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test write to non-existent directory
            test_file = Path(temp_dir) / "nonexistent" / "test.json"
            
            with pytest.raises(FileNotFoundError):
                atomic_write_json(str(test_file), {"key": "value"})
    
    def test_project_save_load_roundtrip(self):
        """Test project save/load roundtrip"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            
            # Create project
            project = manager.create_project("TestProject", temp_dir)
            
            # Add some data
            manager.add_asset("Characters", "char_A", {"notes": "Main character"})
            manager.add_asset("Props", "prop_1", {"notes": "Important prop"})
            manager.add_shot("sq01", "sh010", {"notes": "Opening shot"})
            manager.add_shot("sq01", "sh020", {"notes": "Action shot"})
            
            # Create dummy source files for versions
            source_file1 = Path(temp_dir) / "source1.ma"
            source_file1.write_text("# Maya ASCII file 1")
            
            source_file2 = Path(temp_dir) / "source2.ma"
            source_file2.write_text("# Maya ASCII file 2")
            
            # Add versions
            manager.add_version("char_A", str(source_file1), "user1", "Version 1")
            manager.add_version("sq01/sh010", str(source_file2), "user2", "Version 1")
            
            # Save project
            manager.save_project()
            
            # Create new manager and load project
            manager2 = ProjectManager()
            loaded_project = manager2.load_project(project.path)
            
            # Check project data
            assert loaded_project.name == "TestProject"
            assert loaded_project.fps == 24
            assert loaded_project.resolution == [1920, 1080]
            
            # Check assets
            assert len(loaded_project.assets) == 2
            asset_names = [asset.name for asset in loaded_project.assets]
            assert "char_A" in asset_names
            assert "prop_1" in asset_names
            
            # Check shots
            assert len(loaded_project.shots) == 2
            shot_keys = [shot.key for shot in loaded_project.shots]
            assert "sq01/sh010" in shot_keys
            assert "sq01/sh020" in shot_keys
            
            # Check versions
            char_versions = loaded_project.get_versions("char_A")
            assert len(char_versions) == 1
            assert char_versions[0].version == "v001"
            assert char_versions[0].user == "user1"
            
            shot_versions = loaded_project.get_versions("sq01/sh010")
            assert len(shot_versions) == 1
            assert shot_versions[0].version == "v001"
            assert shot_versions[0].user == "user2"
    
    def test_pipeline_json_consistency(self):
        """Test pipeline.json consistency after operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add some data
            manager.add_asset("Characters", "char_A")
            manager.add_shot("sq01", "sh010")
            
            # Save project
            manager.save_project()
            
            # Load pipeline.json directly
            pipeline_path = Path(project.path) / "00_Pipeline" / "pipeline.json"
            with open(pipeline_path, 'r', encoding='utf-8') as f:
                pipeline_data = json.load(f)
            
            # Check consistency
            assert pipeline_data["name"] == "TestProject"
            assert len(pipeline_data["assets"]) == 1
            assert len(pipeline_data["shots"]) == 1
            assert pipeline_data["assets"][0]["name"] == "char_A"
            assert pipeline_data["shots"][0]["sequence"] == "sq01"
            assert pipeline_data["shots"][0]["name"] == "sh010"
    
    def test_project_to_pipeline_conversion(self):
        """Test project to pipeline conversion"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            project = manager.create_project("TestProject", temp_dir)
            
            # Add some data
            manager.add_asset("Characters", "char_A", {"notes": "Main character"})
            manager.add_shot("sq01", "sh010", {"notes": "Opening shot"})
            
            # Convert to pipeline data
            pipeline_data = project_to_pipeline(project)
            
            # Check conversion
            assert pipeline_data["name"] == "TestProject"
            assert pipeline_data["fps"] == 24
            assert pipeline_data["resolution"] == [1920, 1080]
            assert len(pipeline_data["assets"]) == 1
            assert len(pipeline_data["shots"]) == 1
            assert pipeline_data["assets"][0]["name"] == "char_A"
            assert pipeline_data["assets"][0]["type"] == "Characters"
            assert pipeline_data["assets"][0]["meta"]["notes"] == "Main character"
            assert pipeline_data["shots"][0]["sequence"] == "sq01"
            assert pipeline_data["shots"][0]["name"] == "sh010"
            assert pipeline_data["shots"][0]["meta"]["notes"] == "Opening shot"
    
    def test_pipeline_to_project_conversion(self):
        """Test pipeline to project conversion"""
        pipeline_data = {
            "name": "TestProject",
            "path": "/path/to/project",
            "fps": 30,
            "resolution": [3840, 2160],
            "departments": ["Model", "Rig", "Anim"],
            "tasks": ["WIP", "Review", "Final"],
            "assets": [
                {"name": "char_A", "type": "Characters", "path": "/path/to/char_A", "meta": {"notes": "Main character"}}
            ],
            "shots": [
                {"sequence": "sq01", "name": "sh010", "path": "/path/to/sh010", "meta": {"notes": "Opening shot"}}
            ],
            "versions": {
                "char_A": [
                    {"version": "v001", "user": "user1", "date": "2025-01-01T00:00:00", "comment": "Initial", "path": "/path/to/char_A_v001.ma"}
                ],
                "sq01/sh010": [
                    {"version": "v001", "user": "user2", "date": "2025-01-01T00:00:00", "comment": "Initial", "path": "/path/to/sh010_v001.ma"}
                ]
            }
        }
        
        # Convert to project
        project = pipeline_to_project(pipeline_data)
        
        # Check conversion
        assert project.name == "TestProject"
        assert project.path == "/path/to/project"
        assert project.fps == 30
        assert project.resolution == [3840, 2160]
        assert project.departments == ["Model", "Rig", "Anim"]
        assert project.tasks == ["WIP", "Review", "Final"]
        
        # Check assets
        assert len(project.assets) == 1
        asset = project.assets[0]
        assert asset.name == "char_A"
        assert asset.type == "Characters"
        assert asset.path == "/path/to/char_A"
        assert asset.meta["notes"] == "Main character"
        
        # Check shots
        assert len(project.shots) == 1
        shot = project.shots[0]
        assert shot.sequence == "sq01"
        assert shot.name == "sh010"
        assert shot.path == "/path/to/sh010"
        assert shot.meta["notes"] == "Opening shot"
        
        # Check versions
        char_versions = project.get_versions("char_A")
        assert len(char_versions) == 1
        assert char_versions[0].version == "v001"
        assert char_versions[0].user == "user1"
        
        shot_versions = project.get_versions("sq01/sh010")
        assert len(shot_versions) == 1
        assert shot_versions[0].version == "v001"
        assert shot_versions[0].user == "user2"
    
    def test_json_indentation_and_formatting(self):
        """Test JSON indentation and formatting"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_data = {
                "nested": {
                    "level1": {
                        "level2": "value"
                    }
                },
                "array": [1, 2, 3, {"nested": "object"}]
            }
            
            # Write JSON atomically
            atomic_write_json(str(test_file), test_data)
            
            # Check file content
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should be properly indented
            lines = content.split('\n')
            assert len(lines) > 1  # Should have multiple lines due to indentation
            
            # Should be valid JSON
            loaded_data = json.loads(content)
            assert loaded_data == test_data
    
    def test_concurrent_write_safety(self):
        """Test that atomic writes are safe from interruption"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            
            # Write initial data
            initial_data = {"key": "initial"}
            atomic_write_json(str(test_file), initial_data)
            
            # Simulate interruption by creating a temp file
            temp_file = test_file.with_suffix('.json.tmp')
            temp_file.write_text('{"interrupted": true}')
            
            # Write new data (should handle temp file cleanup)
            new_data = {"key": "updated"}
            atomic_write_json(str(test_file), new_data)
            
            # Check final result
            with open(test_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            assert loaded_data == new_data
            
            # Check temp file was cleaned up
            assert not temp_file.exists()
