"""
Enhanced data models for Vogue Manager

Defines the core data structures for projects, assets, shots, and versions.
Upgraded with UUID-based identification, proper relationships, and modern architecture.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import os
import uuid
import hashlib


@dataclass
class BaseEntity:
    """Base class for all entities in the system"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    label: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_by: str = ""
    status: str = "Active"
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'label': self.label,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'status': self.status,
            'tags': self.tags,
            'attributes': self.attributes
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load entity from dictionary"""
        self.id = data.get('id', str(uuid.uuid4()))
        self.name = data.get('name', '')
        self.label = data.get('label', '')
        self.created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        self.updated_at = datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
        self.created_by = data.get('created_by', '')
        self.updated_by = data.get('updated_by', '')
        self.status = data.get('status', 'Active')
        self.tags = data.get('tags', [])
        self.attributes = data.get('attributes', {})
    
    def validate(self) -> List[str]:
        """Validate entity data, return list of errors"""
        errors = []
        if not self.name or not self.name.strip():
            errors.append("Name cannot be empty")
        if not self.id:
            errors.append("ID cannot be empty")
        return errors
    
    def update_attributes(self, attrs: Dict[str, Any]) -> None:
        """Update custom attributes"""
        self.attributes.update(attrs)
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """Add tag to entity"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str) -> None:
        """Remove tag from entity"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
    
    def has_tag(self, tag: str) -> bool:
        """Check if entity has specific tag"""
        return tag in self.tags
    
    def get_attribute(self, key: str, default=None):
        """Get custom attribute value"""
        return self.attributes.get(key, default)
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set custom attribute value"""
        self.attributes[key] = value
        self.updated_at = datetime.now()


@dataclass
class Department(BaseEntity):
    """Represents a department in the pipeline"""
    description: str = ""
    color: str = "#3498db"
    
    def __post_init__(self):
        if not self.label:
            self.label = self.name

@dataclass
class Folder(BaseEntity):
    """Represents a folder in the project hierarchy"""
    folder_type: str = "Asset"  # "Asset", "Shot", "Sequence", "Episode"
    parent_id: Optional[str] = None  # Parent folder ID
    path: str = ""  # Folder path
    children: List[str] = field(default_factory=list)  # Child folder IDs
    tasks: List[str] = field(default_factory=list)  # Task IDs in this folder
    products: List[str] = field(default_factory=list)  # Product IDs in this folder

    def __post_init__(self):
        """Validate folder data"""
        if not self.name or not self.name.strip():
            raise ValueError("Folder name cannot be empty")
        if self.folder_type not in ["Asset", "Shot", "Sequence", "Episode"]:
            raise ValueError(f"Folder type must be one of ['Asset', 'Shot', 'Sequence', 'Episode'], got: {self.folder_type}")
        if not self.label:
            self.label = self.name
    
    def get_children(self) -> List['Folder']:
        """Get child folders - placeholder for future implementation"""
        return []
    
    def get_tasks(self) -> List['Task']:
        """Get tasks in this folder - placeholder for future implementation"""
        return []
    
    def get_products(self) -> List['Product']:
        """Get products in this folder - placeholder for future implementation"""
        return []
    
    def add_child(self, child: 'Folder') -> None:
        """Add child folder"""
        if child.id not in self.children:
            self.children.append(child.id)
            self.updated_at = datetime.now()
    
    def remove_child(self, child_id: str) -> None:
        """Remove child folder"""
        if child_id in self.children:
            self.children.remove(child_id)
            self.updated_at = datetime.now()
    
    def get_path_string(self) -> str:
        """Get full path as string"""
        return self.path
    
    def get_depth(self) -> int:
        """Get folder depth in hierarchy - placeholder for future implementation"""
        return 0
    
    def is_ancestor_of(self, folder_id: str) -> bool:
        """Check if this folder is ancestor of another - placeholder for future implementation"""
        return False
    
    def get_all_descendants(self) -> List['Folder']:
        """Get all descendant folders - placeholder for future implementation"""
        return []


@dataclass
class Task(BaseEntity):
    """Represents a task in the pipeline"""
    task_type: str = "General"  # "Modeling", "Animation", "Lighting", etc.
    assignee: Optional[str] = None  # Assigned user ID
    status: str = "Not Started"  # "Not Started", "In Progress", "Done", "Blocked"
    priority: int = 3  # 1-5 priority level
    due_date: Optional[datetime] = None  # Due date
    folder_id: str = ""  # Parent folder ID
    dependencies: List[str] = field(default_factory=list)  # Task IDs this task depends on
    estimated_hours: Optional[float] = None  # Estimated hours
    actual_hours: Optional[float] = None  # Actual hours worked
    
    def __post_init__(self):
        """Validate task data"""
        if not self.name or not self.name.strip():
            raise ValueError("Task name cannot be empty")
        if not self.label:
            self.label = self.name
        if self.priority < 1 or self.priority > 5:
            raise ValueError(f"Priority must be between 1 and 5, got: {self.priority}")
    
    def assign_to(self, user_id: str) -> None:
        """Assign task to user"""
        self.assignee = user_id
        self.updated_at = datetime.now()
    
    def unassign(self) -> None:
        """Unassign task from user"""
        self.assignee = None
        self.updated_at = datetime.now()
    
    def update_status(self, status: str) -> None:
        """Update task status"""
        valid_statuses = ["Not Started", "In Progress", "Done", "Blocked"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        self.status = status
        self.updated_at = datetime.now()
    
    def add_dependency(self, task_id: str) -> None:
        """Add task dependency"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            self.updated_at = datetime.now()
    
    def remove_dependency(self, task_id: str) -> None:
        """Remove task dependency"""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
            self.updated_at = datetime.now()
    
    def get_dependencies(self) -> List['Task']:
        """Get dependency tasks - placeholder for future implementation"""
        return []
    
    def get_dependents(self) -> List['Task']:
        """Get tasks that depend on this one - placeholder for future implementation"""
        return []
    
    def is_blocked(self) -> bool:
        """Check if task is blocked by dependencies - placeholder for future implementation"""
        return False
    
    def can_start(self) -> bool:
        """Check if task can start (dependencies met) - placeholder for future implementation"""
        return True
    
    def get_progress_percentage(self) -> float:
        """Get task progress percentage"""
        if self.status == "Not Started":
            return 0.0
        elif self.status == "In Progress":
            return 50.0
        elif self.status == "Done":
            return 100.0
        elif self.status == "Blocked":
            return 0.0
        return 0.0
    
    def add_time(self, hours: float) -> None:
        """Add actual hours worked"""
        if self.actual_hours is None:
            self.actual_hours = 0.0
        self.actual_hours += hours
        self.updated_at = datetime.now()


@dataclass
class Product(BaseEntity):
    """Represents a product (asset, shot, etc.)"""
    product_type: str = "Model"  # "Model", "Rig", "Animation", "Render"
    folder_id: str = ""  # Parent folder ID
    status: str = "Active"  # Product status
    latest_version: Optional[int] = None  # Latest version number
    versions: List[str] = field(default_factory=list)  # Version IDs
    
    def __post_init__(self):
        """Validate product data"""
        if not self.name or not self.name.strip():
            raise ValueError("Product name cannot be empty")
        if not self.label:
            self.label = self.name
    
    def get_latest_version(self) -> Optional['Version']:
        """Get latest version - placeholder for future implementation"""
        return None
    
    def get_versions(self) -> List['Version']:
        """Get all versions - placeholder for future implementation"""
        return []
    
    def create_version(self, author: str, comment: str = "") -> 'Version':
        """Create new version - placeholder for future implementation"""
        version_num = (self.latest_version or 0) + 1
        self.latest_version = version_num
        self.updated_at = datetime.now()
        return Version(
            version=version_num,
            product_id=self.id,
            author=author,
            comment=comment
        )
    
    def get_version(self, version_num: int) -> Optional['Version']:
        """Get specific version - placeholder for future implementation"""
        return None
    
    def get_version_count(self) -> int:
        """Get total version count"""
        return len(self.versions)
    
    def get_published_versions(self) -> List['Version']:
        """Get published versions only - placeholder for future implementation"""
        return []
    
    def get_draft_versions(self) -> List['Version']:
        """Get draft versions only - placeholder for future implementation"""
        return []
    
    def archive_old_versions(self, keep_count: int = 5) -> None:
        """Archive old versions, keep specified count - placeholder for future implementation"""
        pass


@dataclass
class Version(BaseEntity):
    """Represents a version of a product"""
    version: int = 1  # Version number
    product_id: str = ""  # Parent product ID
    author: str = ""  # Author user ID
    comment: str = ""  # Version comment
    status: str = "Draft"  # "Published", "Draft", "Archived"
    thumbnail_id: Optional[str] = None  # Thumbnail file ID
    representations: List[str] = field(default_factory=list)  # Representation IDs
    
    def __post_init__(self):
        """Validate version data"""
        if not self.name:
            self.name = f"v{self.version:03d}"
        if not self.label:
            self.label = self.name
        if self.version < 1:
            raise ValueError(f"Version number must be >= 1, got: {self.version}")
    
    def get_representations(self) -> List['Representation']:
        """Get all representations - placeholder for future implementation"""
        return []
    
    def add_representation(self, rep: 'Representation') -> None:
        """Add representation"""
        if rep.id not in self.representations:
            self.representations.append(rep.id)
            self.updated_at = datetime.now()
    
    def remove_representation(self, rep_id: str) -> None:
        """Remove representation"""
        if rep_id in self.representations:
            self.representations.remove(rep_id)
            self.updated_at = datetime.now()
    
    def get_representation(self, name: str) -> Optional['Representation']:
        """Get representation by name - placeholder for future implementation"""
        return None
    
    def publish(self) -> None:
        """Publish version"""
        self.status = "Published"
        self.updated_at = datetime.now()
    
    def archive(self) -> None:
        """Archive version"""
        self.status = "Archived"
        self.updated_at = datetime.now()
    
    def unpublish(self) -> None:
        """Unpublish version"""
        self.status = "Draft"
        self.updated_at = datetime.now()
    
    def is_published(self) -> bool:
        """Check if version is published"""
        return self.status == "Published"
    
    def get_file_count(self) -> int:
        """Get total file count across all representations - placeholder for future implementation"""
        return 0
    
    def get_total_size(self) -> int:
        """Get total size of all files - placeholder for future implementation"""
        return 0


@dataclass
class Representation(BaseEntity):
    """Represents different formats of a version"""
    name: str = ""  # Format name ("ma", "mb", "abc", "exr")
    version_id: str = ""  # Parent version ID
    files: List[str] = field(default_factory=list)  # File IDs
    attributes: Dict[str, Any] = field(default_factory=dict)  # Format-specific attributes
    active: bool = True  # Whether representation is active
    
    def __post_init__(self):
        """Validate representation data"""
        if not self.name or not self.name.strip():
            raise ValueError("Representation name cannot be empty")
        if not self.label:
            self.label = self.name
    
    def get_files(self) -> List['FileInfo']:
        """Get all files - placeholder for future implementation"""
        return []
    
    def add_file(self, file_info: 'FileInfo') -> None:
        """Add file"""
        if file_info.id not in self.files:
            self.files.append(file_info.id)
            self.updated_at = datetime.now()
    
    def remove_file(self, file_id: str) -> None:
        """Remove file"""
        if file_id in self.files:
            self.files.remove(file_id)
            self.updated_at = datetime.now()
    
    def get_file(self, file_id: str) -> Optional['FileInfo']:
        """Get specific file - placeholder for future implementation"""
        return None
    
    def activate(self) -> None:
        """Activate representation"""
        self.active = True
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """Deactivate representation"""
        self.active = False
        self.updated_at = datetime.now()
    
    def get_file_count(self) -> int:
        """Get file count"""
        return len(self.files)
    
    def get_total_size(self) -> int:
        """Get total size of all files - placeholder for future implementation"""
        return 0
    
    def get_primary_file(self) -> Optional['FileInfo']:
        """Get primary file (first file) - placeholder for future implementation"""
        return None


@dataclass
class FileInfo(BaseEntity):
    """Represents individual files"""
    name: str = ""  # File name
    path: str = ""  # File path
    size: int = 0  # File size in bytes
    hash: str = ""  # File hash
    hash_type: str = "md5"  # Hash algorithm ("md5", "sha256")
    representation_id: str = ""  # Parent representation ID
    mime_type: str = ""  # MIME type
    created_at: datetime = field(default_factory=datetime.now)  # File creation time
    
    def __post_init__(self):
        """Validate file info data"""
        if not self.name or not self.name.strip():
            raise ValueError("File name cannot be empty")
        if not self.label:
            self.label = self.name
    
    def get_absolute_path(self) -> str:
        """Get absolute file path"""
        return os.path.abspath(self.path)
    
    def exists(self) -> bool:
        """Check if file exists on disk"""
        return os.path.exists(self.path)
    
    def get_hash(self) -> str:
        """Calculate file hash"""
        if not self.exists():
            return ""
        
        hash_obj = hashlib.md5() if self.hash_type == "md5" else hashlib.sha256()
        with open(self.path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    
    def verify_hash(self) -> bool:
        """Verify file hash integrity"""
        if not self.hash:
            return False
        return self.get_hash() == self.hash
    
    def get_size_formatted(self) -> str:
        """Get formatted file size string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if self.size < 1024.0:
                return f"{self.size:.1f} {unit}"
            self.size /= 1024.0
        return f"{self.size:.1f} PB"
    
    def get_extension(self) -> str:
        """Get file extension"""
        return os.path.splitext(self.name)[1].lower()
    
    def is_image(self) -> bool:
        """Check if file is an image"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr', '.hdr', '.bmp', '.gif'}
        return self.get_extension() in image_extensions
    
    def is_video(self) -> bool:
        """Check if file is a video"""
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'}
        return self.get_extension() in video_extensions
    
    def is_3d_model(self) -> bool:
        """Check if file is a 3D model"""
        model_extensions = {'.ma', '.mb', '.fbx', '.obj', '.abc', '.usd', '.blend', '.max', '.c4d'}
        return self.get_extension() in model_extensions


@dataclass
class Asset(BaseEntity):
    """Represents an asset in the project (backward compatibility)"""
    type: str = "Character"  # Characters, Props, Environments, etc.
    path: str = ""
    versions: List[Version] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate asset name and type"""
        if not self.name or not self.name.strip():
            raise ValueError("Asset name cannot be empty")
        if not self.type or not self.type.strip():
            raise ValueError("Asset type cannot be empty")
        if not self.label:
            self.label = self.name


@dataclass
class Shot(BaseEntity):
    """Represents a shot in the project (backward compatibility)"""
    sequence: str = ""
    versions: List[Version] = field(default_factory=list)
    path: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate shot sequence and name"""
        if not self.sequence or not self.sequence.strip():
            raise ValueError("Shot sequence cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Shot name cannot be empty")
        if not self.label:
            self.label = f"{self.sequence}/{self.name}"
    
    @property
    def key(self) -> str:
        """Get the unique key for this shot (sequence/name)"""
        return f"{self.sequence}/{self.name}"


@dataclass
class Project(BaseEntity):
    """Represents a complete Vogue project (backward compatibility)"""
    path: str = ""
    fps: int = 24
    resolution: List[int] = field(default_factory=lambda: [1920, 1080])
    departments: List[str] = field(default_factory=list)
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
        if not self.label:
            self.label = self.name
    
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
