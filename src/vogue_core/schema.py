"""
JSON schema validation for Vogue Manager pipeline files

Provides validation and default factory functions for pipeline.json files.
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from .models import Project, Asset, Shot, Version


def validate_pipeline(data: Dict[str, Any]) -> None:
    """
    Validate pipeline.json data structure
    
    Args:
        data: Dictionary containing pipeline data
        
    Raises:
        ValidationError: If data structure is invalid
    """
    required_fields = ["name", "path", "fps", "resolution", "departments", "tasks"]
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate name
    if not isinstance(data["name"], str) or not data["name"].strip():
        raise ValidationError("Project name must be a non-empty string")
    
    # Validate path
    if not isinstance(data["path"], str) or not data["path"].strip():
        raise ValidationError("Project path must be a non-empty string")
    
    # Validate fps
    if not isinstance(data["fps"], int) or data["fps"] <= 0:
        raise ValidationError("FPS must be a positive integer")
    
    # Validate resolution
    if not isinstance(data["resolution"], list) or len(data["resolution"]) != 2:
        raise ValidationError("Resolution must be a list of two integers [width, height]")
    
    if not all(isinstance(r, int) and r > 0 for r in data["resolution"]):
        raise ValidationError("Resolution values must be positive integers")
    
    # Validate departments
    if not isinstance(data["departments"], list) or not data["departments"]:
        raise ValidationError("Departments must be a non-empty list of strings")
    
    if not all(isinstance(d, str) and d.strip() for d in data["departments"]):
        raise ValidationError("All departments must be non-empty strings")
    
    # Validate tasks
    if not isinstance(data["tasks"], list) or not data["tasks"]:
        raise ValidationError("Tasks must be a non-empty list of strings")
    
    if not all(isinstance(t, str) and t.strip() for t in data["tasks"]):
        raise ValidationError("All tasks must be non-empty strings")
    
    # Validate assets (optional)
    if "assets" in data:
        if not isinstance(data["assets"], list):
            raise ValidationError("Assets must be a list")
        
        for i, asset in enumerate(data["assets"]):
            if not isinstance(asset, dict):
                raise ValidationError(f"Asset {i} must be a dictionary")
            
            if "name" not in asset or "type" not in asset:
                raise ValidationError(f"Asset {i} must have 'name' and 'type' fields")
            
            if not isinstance(asset["name"], str) or not asset["name"].strip():
                raise ValidationError(f"Asset {i} name must be a non-empty string")
            
            if not isinstance(asset["type"], str) or not asset["type"].strip():
                raise ValidationError(f"Asset {i} type must be a non-empty string")
    
    # Validate shots (optional)
    if "shots" in data:
        if not isinstance(data["shots"], list):
            raise ValidationError("Shots must be a list")
        
        for i, shot in enumerate(data["shots"]):
            if not isinstance(shot, dict):
                raise ValidationError(f"Shot {i} must be a dictionary")
            
            if "sequence" not in shot or "name" not in shot:
                raise ValidationError(f"Shot {i} must have 'sequence' and 'name' fields")
            
            if not isinstance(shot["sequence"], str) or not shot["sequence"].strip():
                raise ValidationError(f"Shot {i} sequence must be a non-empty string")
            
            if not isinstance(shot["name"], str) or not shot["name"].strip():
                raise ValidationError(f"Shot {i} name must be a non-empty string")
    
    # Validate versions (optional)
    if "versions" in data:
        if not isinstance(data["versions"], dict):
            raise ValidationError("Versions must be a dictionary")
        
        for entity_key, versions in data["versions"].items():
            if not isinstance(versions, list):
                raise ValidationError(f"Versions for {entity_key} must be a list")
            
            for i, version in enumerate(versions):
                if not isinstance(version, dict):
                    raise ValidationError(f"Version {i} for {entity_key} must be a dictionary")
                
                required_version_fields = ["version", "user", "date", "comment", "path"]
                for field in required_version_fields:
                    if field not in version:
                        raise ValidationError(f"Version {i} for {entity_key} missing field: {field}")
                
                if not isinstance(version["version"], str) or not version["version"].startswith("v"):
                    raise ValidationError(f"Version {i} for {entity_key} must start with 'v'")
                
                if not isinstance(version["user"], str) or not version["user"].strip():
                    raise ValidationError(f"Version {i} for {entity_key} user must be non-empty string")
                
                if not isinstance(version["date"], str):
                    raise ValidationError(f"Version {i} for {entity_key} date must be a string")
                
                # Validate ISO 8601 date format
                try:
                    datetime.fromisoformat(version["date"].replace('Z', '+00:00'))
                except ValueError:
                    raise ValidationError(f"Version {i} for {entity_key} date must be valid ISO 8601 format")


def create_default_pipeline(name: str, path: str, fps: int = 24, resolution: List[int] = None) -> Dict[str, Any]:
    """
    Create a minimal valid pipeline.json structure
    
    Args:
        name: Project name
        path: Project path
        fps: Frames per second
        resolution: [width, height] resolution
        
    Returns:
        Dictionary containing minimal pipeline data
    """
    if resolution is None:
        resolution = [1920, 1080]
    
    return {
        "name": name,
        "path": path,
        "fps": fps,
        "resolution": resolution,
        "departments": ["Model", "Rig", "Anim", "LookDev", "FX", "Lighting", "Comp"],
        "tasks": ["WIP", "Review", "Final"],
        "assets": [],
        "shots": [],
        "versions": {}
    }


def pipeline_to_project(data: Dict[str, Any]) -> Project:
    """
    Convert pipeline.json data to Project object
    
    Args:
        data: Pipeline data dictionary
        
    Returns:
        Project object
    """
    # Validate first
    validate_pipeline(data)
    
    # Create assets
    assets = []
    for asset_data in data.get("assets", []):
        asset = Asset(
            name=asset_data["name"],
            type=asset_data["type"],
            path=asset_data.get("path", ""),
            meta=asset_data.get("meta", {})
        )
        assets.append(asset)
    
    # Create shots
    shots = []
    for shot_data in data.get("shots", []):
        shot = Shot(
            sequence=shot_data["sequence"],
            name=shot_data["name"],
            path=shot_data.get("path", ""),
            meta=shot_data.get("meta", {})
        )
        shots.append(shot)
    
    # Create versions
    versions = {}
    for entity_key, version_list in data.get("versions", {}).items():
        versions[entity_key] = []
        for version_data in version_list:
            version = Version(
                version=version_data["version"],
                user=version_data["user"],
                date=version_data["date"],
                comment=version_data["comment"],
                path=version_data["path"],
                thumbnail=version_data.get("thumbnail")
            )
            versions[entity_key].append(version)
    
    # Create project
    project = Project(
        name=data["name"],
        path=data["path"],
        fps=data["fps"],
        resolution=data["resolution"],
        departments=data["departments"],
        tasks=data["tasks"],
        assets=assets,
        shots=shots,
        versions=versions
    )
    
    return project


def project_to_pipeline(project: Project) -> Dict[str, Any]:
    """
    Convert Project object to pipeline.json data
    
    Args:
        project: Project object
        
    Returns:
        Pipeline data dictionary
    """
    # Convert assets
    assets = []
    for asset in project.assets:
        asset_data = {
            "name": asset.name,
            "type": asset.type,
            "path": asset.path,
            "meta": asset.meta
        }
        assets.append(asset_data)
    
    # Convert shots
    shots = []
    for shot in project.shots:
        shot_data = {
            "sequence": shot.sequence,
            "name": shot.name,
            "path": shot.path,
            "meta": shot.meta
        }
        shots.append(shot_data)
    
    # Convert versions
    versions = {}
    for entity_key, version_list in project.versions.items():
        versions[entity_key] = []
        for version in version_list:
            version_data = {
                "version": version.version,
                "user": version.user,
                "date": version.date,
                "comment": version.comment,
                "path": version.path
            }
            if version.thumbnail:
                version_data["thumbnail"] = version.thumbnail
            versions[entity_key].append(version_data)
    
    return {
        "name": project.name,
        "path": project.path,
        "fps": project.fps,
        "resolution": project.resolution,
        "departments": project.departments,
        "tasks": project.tasks,
        "assets": assets,
        "shots": shots,
        "versions": versions
    }


class ValidationError(Exception):
    """Raised when pipeline data validation fails"""
    pass
