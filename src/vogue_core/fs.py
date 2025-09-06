"""
Filesystem utilities for Vogue Manager

Provides atomic file operations, project layout creation, and filesystem scanning.
"""

import os
import json
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


def ensure_layout(root: str, name: str) -> None:
    """
    Create the complete Vogue project folder layout
    
    Args:
        root: Parent directory for the project
        name: Project name
    """
    project_path = Path(root) / name
    
    # Create main project directory
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Create standard folder structure
    folders = [
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
    
    for folder in folders:
        folder_path = project_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep files to ensure folders are tracked
    for folder in folders:
        gitkeep_path = project_path / folder / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()


def atomic_write_json(path: str, data: Dict[str, Any], backup: bool = True) -> None:
    """
    Atomically write JSON data to file with backup
    
    Args:
        path: Target file path
        data: Data to write
        backup: Whether to create a backup file
    """
    path = Path(path)
    
    # Create backup if requested and file exists
    if backup and path.exists():
        backup_path = path.with_suffix(path.suffix + '.bak')
        shutil.copy2(path, backup_path)
    
    # Write to temporary file first
    temp_dir = path.parent
    temp_file = tempfile.NamedTemporaryFile(
        mode='w',
        dir=temp_dir,
        prefix='.tmp_',
        suffix='.json',
        delete=False,
        encoding='utf-8'
    )
    
    try:
        json.dump(data, temp_file, indent=2, ensure_ascii=False)
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_file.close()
        
        # Atomic move
        if os.name == 'nt':  # Windows
            if path.exists():
                os.remove(path)
            os.rename(temp_file.name, str(path))
        else:  # Unix-like
            os.rename(temp_file.name, str(path))
            
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass
        raise


def scan_assets(root: str) -> List[Dict[str, Any]]:
    """
    Scan filesystem for assets based on folder structure
    
    Args:
        root: Project root directory
        
    Returns:
        List of asset dictionaries found
    """
    assets = []
    assets_dir = Path(root) / "01_Assets"
    
    if not assets_dir.exists():
        return assets
    
    # Scan each asset type directory
    for asset_type_dir in assets_dir.iterdir():
        if not asset_type_dir.is_dir() or asset_type_dir.name.startswith('.'):
            continue
            
        asset_type = asset_type_dir.name
        
        # Look for asset subdirectories
        for asset_dir in asset_type_dir.iterdir():
            if not asset_dir.is_dir() or asset_dir.name.startswith('.'):
                continue
                
            asset_name = asset_dir.name
            asset_path = str(asset_dir)
            
            # Look for existing meta files or create default
            meta_file = asset_dir / "meta.json"
            meta = {}
            if meta_file.exists():
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                except (json.JSONDecodeError, OSError):
                    meta = {}
            
            assets.append({
                "name": asset_name,
                "type": asset_type,
                "path": asset_path,
                "meta": meta
            })
    
    return assets


def scan_shots(root: str) -> List[Dict[str, Any]]:
    """
    Scan filesystem for shots based on folder structure
    
    Args:
        root: Project root directory
        
    Returns:
        List of shot dictionaries found
    """
    shots = []
    shots_dir = Path(root) / "02_Shots"
    
    if not shots_dir.exists():
        return shots
    
    # Scan sequence directories
    for seq_dir in shots_dir.iterdir():
        if not seq_dir.is_dir() or seq_dir.name.startswith('.'):
            continue
            
        sequence = seq_dir.name
        
        # Look for shot subdirectories
        for shot_dir in seq_dir.iterdir():
            if not shot_dir.is_dir() or shot_dir.name.startswith('.'):
                continue
                
            shot_name = shot_dir.name
            shot_path = str(shot_dir)
            
            # Look for existing meta files or create default
            meta_file = shot_dir / "meta.json"
            meta = {}
            if meta_file.exists():
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                except (json.JSONDecodeError, OSError):
                    meta = {}
            
            shots.append({
                "sequence": sequence,
                "name": shot_name,
                "path": shot_path,
                "meta": meta
            })
    
    return shots


def next_version(versions: List[str]) -> str:
    """
    Generate the next version number
    
    Args:
        versions: List of existing version strings (e.g., ["v001", "v002"])
        
    Returns:
        Next version string (e.g., "v003")
    """
    if not versions:
        return "v001"
    
    # Extract version numbers
    version_nums = []
    for version in versions:
        if version.startswith('v'):
            try:
                num = int(version[1:])
                version_nums.append(num)
            except ValueError:
                continue
    
    if not version_nums:
        return "v001"
    
    # Find next number
    max_num = max(version_nums)
    next_num = max_num + 1
    
    return f"v{next_num:03d}"


def get_canonical_version_path(project_path: str, entity_key: str, version: str, file_extension: str = ".ma") -> str:
    """
    Get the canonical path for a version file
    
    Args:
        project_path: Project root directory
        entity_key: Asset name or "sequence/shot" for shots
        version: Version string (e.g., "v001")
        file_extension: File extension (default: ".ma")
        
    Returns:
        Canonical file path
    """
    project_path = Path(project_path)
    scenes_dir = project_path / "06_Scenes"
    
    if "/" in entity_key:
        # This is a shot (sequence/shot)
        sequence, shot_name = entity_key.split("/", 1)
        shot_dir = scenes_dir / "Shots" / sequence / shot_name
        shot_dir.mkdir(parents=True, exist_ok=True)
        return str(shot_dir / f"{shot_name}_{version}{file_extension}")
    else:
        # This is an asset - need to determine type
        # For now, assume we can find it in the project data
        # This is a limitation that should be addressed by the caller
        asset_name = entity_key
        # Default to Characters if we can't determine type
        asset_type = "Characters"
        asset_dir = scenes_dir / "Assets" / asset_type / asset_name
        asset_dir.mkdir(parents=True, exist_ok=True)
        return str(asset_dir / f"{asset_name}_{version}{file_extension}")


def copy_version_file(source_path: str, target_path: str) -> None:
    """
    Copy or hardlink a version file to its canonical location
    
    Args:
        source_path: Source file path
        target_path: Target file path
    """
    source_path = Path(source_path)
    target_path = Path(target_path)
    
    # Ensure target directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try hardlink first (more efficient), fall back to copy
    try:
        os.link(source_path, target_path)
    except OSError:
        # Hardlink failed, use copy
        shutil.copy2(source_path, target_path)


def scan_filesystem_for_versions(project_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scan filesystem for existing version files
    
    Args:
        project_path: Project root directory
        
    Returns:
        Dictionary mapping entity keys to lists of version info
    """
    versions = {}
    project_path = Path(project_path)
    
    # Scan asset versions
    assets_scenes_dir = project_path / "06_Scenes" / "Assets"
    if assets_scenes_dir.exists():
        for asset_type_dir in assets_scenes_dir.iterdir():
            if not asset_type_dir.is_dir():
                continue
                
            for asset_dir in asset_type_dir.iterdir():
                if not asset_dir.is_dir():
                    continue
                    
                asset_name = asset_dir.name
                entity_key = asset_name
                
                if entity_key not in versions:
                    versions[entity_key] = []
                
                # Look for version files
                for file_path in asset_dir.iterdir():
                    if file_path.is_file() and file_path.suffix == ".ma":
                        # Extract version from filename (asset_name_v001.ma)
                        filename = file_path.stem
                        if filename.endswith(f"_{asset_name}"):
                            continue  # Skip base files
                        
                        if f"_{asset_name}_" in filename:
                            version_part = filename.split(f"_{asset_name}_")[-1]
                            if version_part.startswith("v"):
                                versions[entity_key].append({
                                    "version": version_part,
                                    "path": str(file_path),
                                    "date": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                                    "user": "unknown",  # Can't determine from filesystem
                                    "comment": ""
                                })
    
    # Scan shot versions
    shots_scenes_dir = project_path / "06_Scenes" / "Shots"
    if shots_scenes_dir.exists():
        for seq_dir in shots_scenes_dir.iterdir():
            if not seq_dir.is_dir():
                continue
                
            sequence = seq_dir.name
            
            for shot_dir in seq_dir.iterdir():
                if not shot_dir.is_dir():
                    continue
                    
                shot_name = shot_dir.name
                entity_key = f"{sequence}/{shot_name}"
                
                if entity_key not in versions:
                    versions[entity_key] = []
                
                # Look for version files
                for file_path in shot_dir.iterdir():
                    if file_path.is_file() and file_path.suffix == ".ma":
                        # Extract version from filename (shot_name_v001.ma)
                        filename = file_path.stem
                        if f"_{shot_name}_" in filename:
                            version_part = filename.split(f"_{shot_name}_")[-1]
                            if version_part.startswith("v"):
                                versions[entity_key].append({
                                    "version": version_part,
                                    "path": str(file_path),
                                    "date": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                                    "user": "unknown",  # Can't determine from filesystem
                                    "comment": ""
                                })
    
    return versions
