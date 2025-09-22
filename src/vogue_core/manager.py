"""
Core ProjectManager for Vogue Manager

Provides the main interface for project management, asset/shot operations, and version control.
"""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import Project, Asset, Shot, Version
from .schema import validate_pipeline, create_default_pipeline, pipeline_to_project, project_to_pipeline
from .fs import (
    ensure_layout, atomic_write_json, scan_assets, scan_shots, 
    next_version, get_canonical_version_path, copy_version_file,
    scan_filesystem_for_versions
)
from .logging_utils import get_logger
from .dcc_integration import dcc_manager


class ProjectManager:
    """Main project management class for Vogue Manager"""
    
    def __init__(self):
        self.current_project: Optional[Project] = None
        self.logger = get_logger("ProjectManager")
    
    def create_project(self, name: str, parent_dir: str, fps: int = 24, resolution: List[int] = None) -> Project:
        """
        Create a new Vogue project
        
        Args:
            name: Project name
            parent_dir: Parent directory for the project
            fps: Frames per second
            resolution: [width, height] resolution
            
        Returns:
            Created Project object
        """
        if resolution is None:
            resolution = [1920, 1080]
        
        project_path = Path(parent_dir) / name
        
        # Create project layout
        ensure_layout(parent_dir, name)
        
        # Create pipeline.json
        pipeline_data = create_default_pipeline(name, str(project_path), fps, resolution)
        pipeline_path = project_path / "00_Pipeline" / "pipeline.json"
        atomic_write_json(str(pipeline_path), pipeline_data)
        
        # Create project object
        project = pipeline_to_project(pipeline_data)
        self.current_project = project
        
        self.logger.info(f"Created new project: {name} at {project_path}")
        return project
    
    def load_project(self, proj_path: str) -> Project:
        """
        Load an existing project from pipeline.json
        
        Args:
            proj_path: Path to project directory or pipeline.json file
            
        Returns:
            Loaded Project object
        """
        proj_path = Path(proj_path)
        
        # If directory provided, look for pipeline.json
        if proj_path.is_dir():
            pipeline_path = proj_path / "00_Pipeline" / "pipeline.json"
        else:
            pipeline_path = proj_path
        
        if not pipeline_path.exists():
            raise FileNotFoundError(f"Pipeline file not found: {pipeline_path}")
        
        # Load and validate pipeline data
        try:
            with open(pipeline_path, 'r', encoding='utf-8') as f:
                pipeline_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise ValueError(f"Failed to load pipeline file: {e}")
        
        validate_pipeline(pipeline_data)
        
        # Create project object
        project = pipeline_to_project(pipeline_data)
        self.current_project = project
        
        self.logger.info(f"Loaded project: {project.name} from {pipeline_path}")
        return project
    
    def save_project(self, project: Optional[Project] = None) -> None:
        """
        Save project to pipeline.json
        
        Args:
            project: Project to save (uses current project if None)
        """
        if project is None:
            project = self.current_project
        
        if project is None:
            raise ValueError("No project to save")
        
        # Convert to pipeline data
        pipeline_data = project_to_pipeline(project)
        
        # Write to file
        pipeline_path = Path(project.path) / "00_Pipeline" / "pipeline.json"
        atomic_write_json(str(pipeline_path), pipeline_data)
        
        self.logger.info(f"Saved project: {project.name}")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get project summary information
        
        Returns:
            Dictionary with project summary
        """
        if self.current_project is None:
            return {"error": "No project loaded"}
        
        return self.current_project.get_info()
    
    # Asset operations
    def list_assets(self) -> List[Asset]:
        """Get list of all assets"""
        if self.current_project is None:
            return []
        return self.current_project.assets
    
    def add_asset(self, type: str, name: str, meta: Dict[str, Any] = None) -> Asset:
        """
        Add a new asset to the project
        
        Args:
            type: Asset type (Characters, Props, Environments, etc.)
            name: Asset name
            meta: Optional metadata
            
        Returns:
            Created Asset object
        """
        if self.current_project is None:
            raise ValueError("No project loaded")
        
        if meta is None:
            meta = {}
        
        # Create asset directory
        asset_dir = Path(self.current_project.path) / "01_Assets" / type / name
        asset_dir.mkdir(parents=True, exist_ok=True)
        
        # Create asset object
        asset = Asset(
            name=name,
            type=type,
            path=str(asset_dir),
            meta=meta
        )
        
        # Add to project
        self.current_project.add_asset(asset)
        
        # Save project
        self.save_project()
        
        self.logger.info(f"Added asset: {name} ({type})")
        return asset
    
    def get_asset(self, name: str) -> Optional[Asset]:
        """Get asset by name"""
        if self.current_project is None:
            return None
        return self.current_project.get_asset(name)
    
    # Shot operations
    def list_shots(self) -> List[Shot]:
        """Get list of all shots"""
        if self.current_project is None:
            return []
        return self.current_project.shots
    
    def add_shot(self, sequence: str, name: str, meta: Dict[str, Any] = None) -> Shot:
        """
        Add a new shot to the project
        
        Args:
            sequence: Sequence name
            name: Shot name
            meta: Optional metadata
            
        Returns:
            Created Shot object
        """
        if self.current_project is None:
            raise ValueError("No project loaded")
        
        if meta is None:
            meta = {}
        
        # Create shot directory
        shot_dir = Path(self.current_project.path) / "02_Shots" / sequence / name
        shot_dir.mkdir(parents=True, exist_ok=True)
        
        # Create shot object
        shot = Shot(
            sequence=sequence,
            name=name,
            path=str(shot_dir),
            meta=meta
        )
        
        # Add to project
        self.current_project.add_shot(shot)
        
        # Save project
        self.save_project()
        
        self.logger.info(f"Added shot: {sequence}/{name}")
        return shot
    
    def get_shot(self, sequence: str, name: str) -> Optional[Shot]:
        """Get shot by sequence and name"""
        if self.current_project is None:
            return None
        return self.current_project.get_shot(sequence, name)
    
    # Department and Task operations
    def get_departments(self) -> List[str]:
        """Get list of departments"""
        if self.current_project is None:
            return []
        return self.current_project.departments
    
    def get_tasks(self) -> List[str]:
        """Get list of tasks"""
        if self.current_project is None:
            return []
        return self.current_project.tasks
    
    # Version operations
    def list_versions(self, entity_key: str) -> List[Version]:
        """Get list of versions for an entity"""
        if self.current_project is None:
            return []
        return self.current_project.get_versions(entity_key)
    
    def add_version(self, entity_key: str, source_file: str, user: str, comment: str = "", version: str = None) -> Version:
        """
        Add a new version for an entity
        
        Args:
            entity_key: Asset name or "sequence/shot" for shots
            source_file: Source file path
            user: User name
            comment: Version comment
            version: Version string (auto-generated if None)
            
        Returns:
            Created Version object
        """
        if self.current_project is None:
            raise ValueError("No project loaded")
        
        # Get existing versions to determine next version
        existing_versions = [v.version for v in self.current_project.get_versions(entity_key)]
        
        if version is None:
            version = next_version(existing_versions)
        
        # Get canonical path
        canonical_path = get_canonical_version_path(self.current_project.path, entity_key, version)
        
        # Copy file to canonical location
        copy_version_file(source_file, canonical_path)
        
        # Create version object
        version_obj = Version(
            version=version,
            user=user,
            date=datetime.now().isoformat(),
            comment=comment,
            path=canonical_path
        )
        
        # Add to project
        self.current_project.add_version(entity_key, version_obj)
        
        # Save project
        self.save_project()
        
        self.logger.info(f"Added version {version} for {entity_key} by {user}")
        return version_obj
    
    def create_dcc_version(self, entity_key: str, dcc_app: str, task_name: str, 
                          user: str, comment: str = "", workfile_path: str = None) -> Version:
        """
        Create a new version using a DCC application
        
        Args:
            entity_key: Asset name or "sequence/shot" for shots
            dcc_app: DCC application name (maya, blender, etc.)
            task_name: Task name for this version
            user: User name
            comment: Version comment
            workfile_path: Optional workfile path to use
            
        Returns:
            Created Version object
        """
        if self.current_project is None:
            raise ValueError("No project loaded")
        
        # Get DCC app info
        app = dcc_manager.get_app(dcc_app)
        if not app:
            raise ValueError(f"DCC app '{dcc_app}' not found")
        
        # Get existing versions to determine next version
        existing_versions = [v.version for v in self.current_project.get_versions(entity_key)]
        version_str = next_version(existing_versions)
        version_num = int(version_str[1:])  # Extract number from v001
        
        # Create workfile path if not provided
        if not workfile_path:
            workfile_path = dcc_manager.create_workfile_path(
                dcc_app, entity_key, task_name, version_num, self.current_project.path
            )
        
        # Get canonical version path
        canonical_path = get_canonical_version_path(self.current_project.path, entity_key, version_str)
        
        # Copy workfile to canonical location
        copy_version_file(workfile_path, canonical_path)
        
        # Generate thumbnail
        thumbnail_path = ""
        if os.path.exists(workfile_path):
            thumbnail_path = os.path.join(
                self.current_project.path, 
                "thumbnails", 
                "versions", 
                f"{os.path.splitext(os.path.basename(canonical_path))[0]}_thumb.png"
            )
            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
            dcc_manager.generate_thumbnail(workfile_path, thumbnail_path)
        
        # Create version object
        version_obj = Version(
            version=version_str,
            user=user,
            date=datetime.now().isoformat(),
            comment=comment,
            path=canonical_path,
            dcc_app=dcc_app,
            task_name=task_name,
            workfile_path=workfile_path,
            thumbnail=thumbnail_path,
            status="WIP"
        )
        
        # Add to project
        self.current_project.add_version(entity_key, version_obj)
        
        # Save project
        self.save_project()
        
        self.logger.info(f"Created DCC version {version_str} for {entity_key} using {app.display_name}")
        return version_obj

    def create_placeholder_version(
        self,
        entity_key: str,
        user: str,
        comment: str = "",
        dcc_app: str | None = None,
        task_name: str | None = None,
        status: str = "WIP",
    ) -> Version:
        """Create a version entry without requiring a source workfile.

        Touches an empty file at the canonical version path so the UI has a real path
        to show/open later. Useful for quickly registering versions from the UI.
        """
        if self.current_project is None:
            raise ValueError("No project loaded")

        # Determine next version string
        existing_versions = [v.version for v in self.current_project.get_versions(entity_key)]
        version_str = next_version(existing_versions)

        # Canonical path and create an empty file
        canonical_path = get_canonical_version_path(self.current_project.path, entity_key, version_str)
        os.makedirs(os.path.dirname(canonical_path), exist_ok=True)
        try:
            with open(canonical_path, 'wb') as f:
                f.write(b'')
        except OSError:
            # If path is not writable, fallback to no file but still register version
            canonical_path = ""

        # Build version object
        version_obj = Version(
            version=version_str,
            user=user,
            date=datetime.now().isoformat(),
            comment=comment,
            path=canonical_path,
        )
        # Optional fields if present on Version
        if hasattr(version_obj, 'dcc_app'):
            version_obj.dcc_app = dcc_app  # type: ignore
        if hasattr(version_obj, 'task_name') and task_name:
            version_obj.task_name = task_name  # type: ignore
        if hasattr(version_obj, 'status'):
            version_obj.status = status  # type: ignore

        # Persist in project
        self.current_project.add_version(entity_key, version_obj)
        self.save_project()
        self.logger.info(f"Created placeholder version {version_str} for {entity_key}")
        return version_obj
    
    def launch_dcc_app(self, dcc_app: str, entity_key: str = None, 
                      task_name: str = None, version: str = None) -> bool:
        """
        Launch DCC application with optional workfile
        
        Args:
            dcc_app: DCC application name
            entity_key: Optional entity to open
            task_name: Optional task name
            version: Optional version to open
            
        Returns:
            True if launched successfully
        """
        if self.current_project is None:
            self.logger.error("No project loaded")
            return False
        
        workfile_path = None
        
        # If entity and version specified, find the workfile
        if entity_key and version:
            versions = self.current_project.get_versions(entity_key)
            for v in versions:
                if v.version == version and v.dcc_app == dcc_app:
                    workfile_path = v.workfile_path or v.path
                    break
        
        # Launch the DCC app
        return dcc_manager.launch_app(
            dcc_app, 
            workfile_path, 
            self.current_project.path
        )
    
    def get_dcc_apps(self) -> List[Dict[str, Any]]:
        """Get list of available DCC applications"""
        apps = dcc_manager.list_apps()
        return [
            {
                "name": app.name,
                "display_name": app.display_name,
                "executable_path": app.executable_path,
                "file_extensions": app.file_extensions,
                "icon": app.get_dcc_app_icon()
            }
            for app in apps
        ]
    
    def scan_filesystem(self, update_missing: bool = True) -> None:
        """
        Scan filesystem and update project data
        
        Args:
            update_missing: Whether to add missing assets/shots found on disk
        """
        if self.current_project is None:
            raise ValueError("No project loaded")
        
        project_path = self.current_project.path
        
        # Scan for assets
        found_assets = scan_assets(project_path)
        for asset_data in found_assets:
            existing_asset = self.current_project.get_asset(asset_data["name"])
            if existing_asset is None and update_missing:
                # Add missing asset
                asset = Asset(
                    name=asset_data["name"],
                    type=asset_data["type"],
                    path=asset_data["path"],
                    meta=asset_data["meta"]
                )
                self.current_project.add_asset(asset)
                self.logger.info(f"Found and added asset: {asset_data['name']}")
        
        # Scan for shots
        found_shots = scan_shots(project_path)
        for shot_data in found_shots:
            existing_shot = self.current_project.get_shot(shot_data["sequence"], shot_data["name"])
            if existing_shot is None and update_missing:
                # Add missing shot
                shot = Shot(
                    sequence=shot_data["sequence"],
                    name=shot_data["name"],
                    path=shot_data["path"],
                    meta=shot_data["meta"]
                )
                self.current_project.add_shot(shot)
                self.logger.info(f"Found and added shot: {shot_data['sequence']}/{shot_data['name']}")
        
        # Scan for versions
        found_versions = scan_filesystem_for_versions(project_path)
        for entity_key, version_list in found_versions.items():
            existing_versions = [v.version for v in self.current_project.get_versions(entity_key)]
            
            for version_data in version_list:
                if version_data["version"] not in existing_versions and update_missing:
                    # Add missing version
                    version = Version(
                        version=version_data["version"],
                        user=version_data["user"],
                        date=version_data["date"],
                        comment=version_data["comment"],
                        path=version_data["path"]
                    )
                    self.current_project.add_version(entity_key, version)
                    self.logger.info(f"Found and added version {version_data['version']} for {entity_key}")
        
        # Save updated project
        if update_missing:
            self.save_project()
        
        self.logger.info("Filesystem scan completed")
    
    def get_entity_key(self, asset_or_shot) -> str:
        """
        Get entity key for an asset or shot
        
        Args:
            asset_or_shot: Asset or Shot object
            
        Returns:
            Entity key string
        """
        if isinstance(asset_or_shot, Asset):
            return asset_or_shot.name
        elif isinstance(asset_or_shot, Shot):
            return asset_or_shot.key
        else:
            raise ValueError("Expected Asset or Shot object")
