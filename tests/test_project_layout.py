"""
Test project layout creation and structure

Tests the project folder layout creation and pipeline.json generation.
"""

import pytest
import tempfile
import json
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vogue_core.fs import ensure_layout
from vogue_core.schema import create_default_pipeline, validate_pipeline
from vogue_core.manager import ProjectManager


class TestProjectLayout:
    """Test project layout creation"""
    
    def test_ensure_layout_creates_structure(self):
        """Test that ensure_layout creates the correct folder structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_name = "TestProject"
            ensure_layout(temp_dir, project_name)
            
            project_path = Path(temp_dir) / project_name
            
            # Check main project directory exists
            assert project_path.exists()
            assert project_path.is_dir()
            
            # Check required folders exist
            required_folders = [
                "00_Pipeline",
                "00_Pipeline/templates",
                "01_Assets/Characters",
                "01_Assets/Props",
                "01_Assets/Environments",
                "02_Shots",
                "03_Textures",
                "04_Designs",
                "05_Publish",
                "06_Scenes/Assets/Characters",
                "06_Scenes/Assets/Props",
                "06_Scenes/Assets/Environments",
                "06_Scenes/Shots",
                "07_Renders"
            ]
            
            for folder in required_folders:
                folder_path = project_path / folder
                assert folder_path.exists(), f"Folder {folder} should exist"
                assert folder_path.is_dir(), f"Folder {folder} should be a directory"
    
    def test_ensure_layout_creates_gitkeep_files(self):
        """Test that ensure_layout creates .gitkeep files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_name = "TestProject"
            ensure_layout(temp_dir, project_name)
            
            project_path = Path(temp_dir) / project_name
            
            # Check .gitkeep files exist in empty directories
            gitkeep_folders = [
                "00_Pipeline/templates",
                "01_Assets/Characters",
                "01_Assets/Props",
                "01_Assets/Environments",
                "02_Shots",
                "03_Textures",
                "04_Designs",
                "05_Publish",
                "06_Scenes/Assets/Characters",
                "06_Scenes/Assets/Props",
                "06_Scenes/Assets/Environments",
                "06_Scenes/Shots",
                "07_Renders"
            ]
            
            for folder in gitkeep_folders:
                gitkeep_path = project_path / folder / ".gitkeep"
                assert gitkeep_path.exists(), f".gitkeep file should exist in {folder}"
    
    def test_create_default_pipeline(self):
        """Test default pipeline creation"""
        pipeline_data = create_default_pipeline("TestProject", "/path/to/project")
        
        # Check required fields
        assert pipeline_data["name"] == "TestProject"
        assert pipeline_data["path"] == "/path/to/project"
        assert pipeline_data["fps"] == 24
        assert pipeline_data["resolution"] == [1920, 1080]
        assert "departments" in pipeline_data
        assert "tasks" in pipeline_data
        assert "assets" in pipeline_data
        assert "shots" in pipeline_data
        assert "versions" in pipeline_data
        
        # Check default values
        assert len(pipeline_data["departments"]) > 0
        assert len(pipeline_data["tasks"]) > 0
        assert pipeline_data["assets"] == []
        assert pipeline_data["shots"] == []
        assert pipeline_data["versions"] == {}
    
    def test_validate_pipeline_valid_data(self):
        """Test pipeline validation with valid data"""
        valid_data = {
            "name": "TestProject",
            "path": "/path/to/project",
            "fps": 24,
            "resolution": [1920, 1080],
            "departments": ["Model", "Rig", "Anim"],
            "tasks": ["WIP", "Review", "Final"],
            "assets": [],
            "shots": [],
            "versions": {}
        }
        
        # Should not raise an exception
        validate_pipeline(valid_data)
    
    def test_validate_pipeline_invalid_data(self):
        """Test pipeline validation with invalid data"""
        from vogue_core.schema import ValidationError
        
        # Missing required field
        invalid_data = {
            "name": "TestProject",
            # Missing path
            "fps": 24,
            "resolution": [1920, 1080],
            "departments": ["Model", "Rig", "Anim"],
            "tasks": ["WIP", "Review", "Final"]
        }
        
        with pytest.raises(ValidationError):
            validate_pipeline(invalid_data)
        
        # Invalid fps
        invalid_data = {
            "name": "TestProject",
            "path": "/path/to/project",
            "fps": -1,  # Invalid
            "resolution": [1920, 1080],
            "departments": ["Model", "Rig", "Anim"],
            "tasks": ["WIP", "Review", "Final"]
        }
        
        with pytest.raises(ValidationError):
            validate_pipeline(invalid_data)
        
        # Invalid resolution
        invalid_data = {
            "name": "TestProject",
            "path": "/path/to/project",
            "fps": 24,
            "resolution": [1920],  # Invalid - should be [width, height]
            "departments": ["Model", "Rig", "Anim"],
            "tasks": ["WIP", "Review", "Final"]
        }
        
        with pytest.raises(ValidationError):
            validate_pipeline(invalid_data)
    
    def test_project_manager_create_project(self):
        """Test ProjectManager.create_project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            
            project = manager.create_project("TestProject", temp_dir)
            
            # Check project object
            assert project.name == "TestProject"
            assert project.path == str(Path(temp_dir) / "TestProject")
            assert project.fps == 24
            assert project.resolution == [1920, 1080]
            
            # Check pipeline.json was created
            pipeline_path = Path(project.path) / "00_Pipeline" / "pipeline.json"
            assert pipeline_path.exists()
            
            # Check pipeline.json content
            with open(pipeline_path, 'r') as f:
                pipeline_data = json.load(f)
            
            assert pipeline_data["name"] == "TestProject"
            assert pipeline_data["fps"] == 24
            assert pipeline_data["resolution"] == [1920, 1080]
    
    def test_project_manager_load_project(self):
        """Test ProjectManager.load_project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            
            # Create a project first
            project = manager.create_project("TestProject", temp_dir)
            project_path = project.path
            
            # Create a new manager and load the project
            manager2 = ProjectManager()
            loaded_project = manager2.load_project(project_path)
            
            # Check loaded project
            assert loaded_project.name == "TestProject"
            assert loaded_project.path == project_path
            assert loaded_project.fps == 24
            assert loaded_project.resolution == [1920, 1080]
    
    def test_project_manager_save_project(self):
        """Test ProjectManager.save_project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ProjectManager()
            
            # Create a project
            project = manager.create_project("TestProject", temp_dir)
            
            # Modify project
            project.fps = 30
            project.resolution = [3840, 2160]
            
            # Save project
            manager.save_project()
            
            # Load project again to verify changes were saved
            manager2 = ProjectManager()
            loaded_project = manager2.load_project(project.path)
            
            assert loaded_project.fps == 30
            assert loaded_project.resolution == [3840, 2160]
