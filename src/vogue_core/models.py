"""
Data models for Vogue Manager

Defines the core data structures for projects, assets, shots, and versions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import os


@dataclass
class Department:
    """Represents a department in the pipeline"""
    name: str
    description: str = ""
    color: str = "#3498db"

@dataclass
class Folder:
    """Represents a folder in the project hierarchy"""
    name: str
    type: str  # "asset" or "shot"
    parent: Optional[str] = None  # Parent folder name, None for root folders
    assets: List[str] = field(default_factory=list)  # Asset names in this folder
    shots: List[str] = field(default_factory=list)   # Shot names in this folder

    def __post_init__(self):
        """Validate folder data"""
        if not self.name or not self.name.strip():
            raise ValueError("Folder name cannot be empty")
        if self.type not in ["asset", "shot"]:
            raise ValueError(f"Folder type must be 'asset' or 'shot', got: {self.type}")


@dataclass 
class Task:
    """Represents a task in the pipeline"""
    name: str
    department: str = ""  # Department this task belongs to
    status: str = "Pending"
    description: str = ""


@dataclass
class Version:
    """Represents a version of an asset or shot"""
    version: str
    user: str
    date: str  # ISO 8601 format
    comment: str = ""
    path: str = ""
    thumbnail: Optional[str] = None
    dcc_app: Optional[str] = None  # DCC application used (maya, blender, etc.)
    task_name: str = ""  # Task this version belongs to
    workfile_path: Optional[str] = None  # Original workfile path
    status: str = "WIP"  # WIP, Review, Approved, Published
    tags: List[str] = field(default_factory=list)  # Version tags
    
    def __post_init__(self):
        """Validate version format"""
        if not self.version.startswith('v'):
            raise ValueError(f"Version must start with 'v', got: {self.version}")
        
        # Validate version number format (v001, v002, etc.)
        try:
            version_num = int(self.version[1:])
            if version_num < 1:
                raise ValueError(f"Version number must be >= 1, got: {version_num}")
        except (ValueError, IndexError):
            raise ValueError(f"Invalid version format: {self.version}")
    
    def get_thumbnail_path(self, project_path: str) -> str:
        """Get thumbnail path for this version"""
        if self.thumbnail:
            return self.thumbnail
        
        # Generate thumbnail path based on version path
        if self.path:
            thumb_dir = os.path.join(project_path, "thumbnails", "versions")
            os.makedirs(thumb_dir, exist_ok=True)
            version_name = os.path.splitext(os.path.basename(self.path))[0]
            return os.path.join(thumb_dir, f"{version_name}_thumb.png")
        
        return ""
    
    def get_dcc_app_icon(self) -> str:
        """Get icon for the DCC app used"""
        icon_map = {
            "maya": "🎨",
            "blender": "🎭",
            "houdini": "🌀", 
            "nuke": "🎬",
            "3dsmax": "📐",
            "cinema4d": "🎪"
        }
        return icon_map.get(self.dcc_app or "", "📁")


@dataclass
class Asset:
    """Represents an asset in the project"""
    name: str
    type: str  # Characters, Props, Environments, etc.
    path: str = ""
    versions: List[Version] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate asset name and type"""
        if not self.name or not self.name.strip():
            raise ValueError("Asset name cannot be empty")
        if not self.type or not self.type.strip():
            raise ValueError("Asset type cannot be empty")


@dataclass
class Shot:
    """Represents a shot in the project"""
    sequence: str
    name: str
    versions: List[Version] = field(default_factory=list)
    path: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate shot sequence and name"""
        if not self.sequence or not self.sequence.strip():
            raise ValueError("Shot sequence cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Shot name cannot be empty")
    
    @property
    def key(self) -> str:
        """Get the unique key for this shot (sequence/name)"""
        return f"{self.sequence}/{self.name}"


@dataclass
class Project:
    """Represents a complete Vogue project"""
    name: str
    path: str
    fps: int = 24
    resolution: List[int] = field(default_factory=lambda: [1920, 1080])
    departments: List[Department] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    assets: List[Asset] = field(default_factory=list)
    shots: List[Shot] = field(default_factory=list)
    folders: List[Folder] = field(default_factory=list)  # Custom folder structure
    versions: Dict[str, List[Version]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate project data"""
        if not self.name or not self.name.strip():
            raise ValueError("Project name cannot be empty")
        if not self.path or not self.path.strip():
            raise ValueError("Project path cannot be empty")
        if self.fps <= 0:
            raise ValueError(f"FPS must be positive, got: {self.fps}")
        if len(self.resolution) != 2 or any(r <= 0 for r in self.resolution):
            raise ValueError(f"Resolution must be [width, height] with positive values, got: {self.resolution}")
    
    def get_asset(self, name: str) -> Optional[Asset]:
        """Get an asset by name"""
        for asset in self.assets:
            if asset.name == name:
                return asset
        return None
    
    def get_shot(self, sequence: str, name: str) -> Optional[Shot]:
        """Get a shot by sequence and name"""
        for shot in self.shots:
            if shot.sequence == sequence and shot.name == name:
                return shot
        return None
    
    def add_asset(self, asset: Asset) -> None:
        """Add an asset to the project"""
        if self.get_asset(asset.name):
            raise ValueError(f"Asset '{asset.name}' already exists")
        self.assets.append(asset)
    
    def add_shot(self, shot: Shot) -> None:
        """Add a shot to the project"""
        if self.get_shot(shot.sequence, shot.name):
            raise ValueError(f"Shot '{shot.sequence}/{shot.name}' already exists")
        self.shots.append(shot)
    
    def add_version(self, entity_key: str, version: Version) -> None:
        """Add a version for an entity (asset or shot)"""
        if entity_key not in self.versions:
            self.versions[entity_key] = []
        self.versions[entity_key].append(version)
    
    def get_versions(self, entity_key: str) -> List[Version]:
        """Get all versions for an entity"""
        return self.versions.get(entity_key, [])
    
    def get_info(self) -> Dict[str, Any]:
        """Get project summary information"""
        return {
            "name": self.name,
            "path": self.path,
            "fps": self.fps,
            "resolution": self.resolution,
            "departments": self.departments,
            "tasks": self.tasks,
            "asset_count": len(self.assets),
            "shot_count": len(self.shots),
            "total_versions": sum(len(versions) for versions in self.versions.values()),
            "asset_types": list(set(asset.type for asset in self.assets)),
            "sequences": list(set(shot.sequence for shot in self.shots))
        }
