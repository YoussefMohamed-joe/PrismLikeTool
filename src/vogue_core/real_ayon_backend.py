"""
Vogue Project Backend Implementation

This implements a complete project management backend functionality,
storing everything locally in JSON files instead of using a server.
"""

import os
import json
import uuid
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Any, Union, Sequence
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

from vogue_core.logging_utils import get_logger

# Project management enums and types
class FolderType(Enum):
    ASSET = "Asset"
    SHOT = "Shot"
    SEQUENCE = "Sequence"
    EPISODE = "Episode"
    LIBRARY = "Library"

class TaskType(Enum):
    MODELING = "Modeling"
    TEXTURING = "Texturing"
    RIGGING = "Rigging"
    ANIMATION = "Animation"
    LIGHTING = "Lighting"
    RENDERING = "Rendering"
    COMPOSITING = "Compositing"
    REVIEW = "Review"

class Status(Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    REVIEW = "Review"
    DONE = "Done"
    ON_HOLD = "On Hold"
    CANCELLED = "Cancelled"

class UserRole(Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    SUPERVISOR = "Supervisor"
    ARTIST = "Artist"
    CLIENT = "Client"

# Project management data models
@dataclass
class VogueProject:
    """Vogue project with complete project management functionality"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    code: str = ""
    library: bool = False
    config: Dict[str, Any] = field(default_factory=dict)
    attrib: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    path: str = ""  # Add path attribute
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_by: str = ""
    
    # Ayon aux tables
    folder_types: List[Dict[str, Any]] = field(default_factory=list)
    task_types: List[Dict[str, Any]] = field(default_factory=list)
    statuses: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[Dict[str, Any]] = field(default_factory=list)
    link_types: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.folder_types:
            self.folder_types = [
                {"name": "Asset", "icon": "folder", "color": "#4A9EFF", "position": 0},
                {"name": "Shot", "icon": "video", "color": "#51CF66", "position": 1},
                {"name": "Sequence", "icon": "film", "color": "#FFD43B", "position": 2},
                {"name": "Episode", "icon": "tv", "color": "#FF6B6B", "position": 3},
            ]
        if not self.task_types:
            self.task_types = [
                {"name": "Modeling", "icon": "cube", "color": "#4A9EFF", "position": 0},
                {"name": "Texturing", "icon": "paint-brush", "color": "#51CF66", "position": 1},
                {"name": "Rigging", "icon": "cog", "color": "#FFD43B", "position": 2},
                {"name": "Animation", "icon": "play", "color": "#FF6B6B", "position": 3},
                {"name": "Lighting", "icon": "lightbulb", "color": "#9C27B0", "position": 4},
                {"name": "Rendering", "icon": "image", "color": "#00BCD4", "position": 5},
                {"name": "Compositing", "icon": "layers", "color": "#8BC34A", "position": 6},
                {"name": "Review", "icon": "eye", "color": "#FF9800", "position": 7},
            ]
        if not self.statuses:
            self.statuses = [
                {"name": "Not Started", "color": "#A0A6AC", "icon": "circle", "position": 0},
                {"name": "In Progress", "color": "#4A9EFF", "icon": "play-circle", "position": 1},
                {"name": "Review", "color": "#FFD43B", "icon": "eye", "position": 2},
                {"name": "Done", "color": "#51CF66", "icon": "check-circle", "position": 3},
                {"name": "On Hold", "color": "#FF9800", "icon": "pause-circle", "position": 4},
                {"name": "Cancelled", "color": "#F44336", "icon": "times-circle", "position": 5},
            ]
        if not self.tags:
            self.tags = []
        if not self.link_types:
            self.link_types = []

@dataclass
class AyonFolder:
    """Real Ayon folder with hierarchy support from ayon_server/entities/folder.py"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    label: str = ""
    folder_type: str = "Asset"
    parent_id: Optional[str] = None
    path: str = ""
    thumbnail_id: Optional[str] = None
    attrib: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    status: str = "Not Started"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_by: str = ""
    project_name: str = ""
    
    # Hierarchy properties
    has_versions: bool = False
    children: List[str] = field(default_factory=list)
    products: List[str] = field(default_factory=list)
    tasks: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.label:
            self.label = self.name

@dataclass
class AyonProduct:
    """Real Ayon product from ayon_server/entities/product.py"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    folder_id: str = ""
    product_type: str = "Asset"
    attrib: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    status: str = "Not Started"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_by: str = ""
    project_name: str = ""
    
    # Product properties
    versions: List[str] = field(default_factory=list)
    representations: List[str] = field(default_factory=list)
    
    @property
    def parent_id(self) -> str:
        return self.folder_id
    
    @property
    def path(self) -> str:
        return f"/{self.folder_id}/{self.name}"

@dataclass
class AyonTask:
    """Real Ayon task from ayon_server/entities/task.py"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    label: str = ""
    task_type: str = "Modeling"
    folder_id: str = ""
    assignees: List[str] = field(default_factory=list)
    thumbnail_id: Optional[str] = None
    attrib: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    status: str = "Not Started"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_by: str = ""
    project_name: str = ""
    
    def __post_init__(self):
        if not self.label:
            self.label = self.name
    
    @property
    def parent_id(self) -> str:
        return self.folder_id
    
    @property
    def path(self) -> str:
        return f"/{self.folder_id}/{self.name}"
    
    @property
    def entity_subtype(self) -> str:
        return self.task_type

@dataclass
class AyonVersion:
    """Real Ayon version"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    version: int = 1
    product_id: str = ""
    task_id: Optional[str] = None
    thumbnail_id: Optional[str] = None
    attrib: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    status: str = "Not Started"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_by: str = ""
    project_name: str = ""
    
    # Version properties
    representations: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.name:
            self.name = f"v{self.version:03d}"

@dataclass
class AyonRepresentation:
    """Real Ayon representation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    version_id: str = ""
    attrib: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    status: str = "Not Started"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_by: str = ""
    project_name: str = ""
    
    # Representation properties
    files: List[str] = field(default_factory=list)

@dataclass
class AyonUser:
    """Real Ayon user with access control"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    password_hash: str = ""
    attrib: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    is_manager: bool = False
    is_guest: bool = False
    is_admin: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_by: str = ""
    
    # User properties
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Ayon access control
    access_groups: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    studio_access: bool = True
    project_access: List[str] = field(default_factory=list)

@dataclass
class AyonWorkfile:
    """Real Ayon workfile"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    task_id: str = ""
    folder_id: str = ""
    file_path: str = ""
    file_size: int = 0
    attrib: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    status: str = "Not Started"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_by: str = ""
    project_name: str = ""
    
    # Workfile properties
    modified_at: Optional[datetime] = None

class VogueProjectBackend:
    """
    Vogue Project backend implementation with local storage
    
    This implements a complete project management backend functionality,
    storing everything locally as JSON files.
    """
    
    def __init__(self, local_root: str = "VogueProjects"):
        self.logger = get_logger("VogueProjectBackend")
        self.local_root = Path(local_root)
        self.local_root.mkdir(exist_ok=True)
        
        # Current project
        self.current_project: Optional[VogueProject] = None
        self.current_project_path: Optional[Path] = None
        
        # Data caches
        self._projects_cache: Dict[str, VogueProject] = {}
        self._folders_cache: Dict[str, AyonFolder] = {}
        self._products_cache: Dict[str, AyonProduct] = {}
        self._tasks_cache: Dict[str, AyonTask] = {}
        self._versions_cache: Dict[str, AyonVersion] = {}
        self._representations_cache: Dict[str, AyonRepresentation] = {}
        self._users_cache: Dict[str, AyonUser] = {}
        self._workfiles_cache: Dict[str, AyonWorkfile] = {}
        
        self.logger.info(f"Vogue Project backend initialized with local root: {self.local_root.absolute()}")
    
    # Project Management (from ayon_server/entities/project.py)
    def create_project(self, name: str, code: str = "", library: bool = False) -> VogueProject:
        """Create a new Ayon project with full structure"""
        project_id = str(uuid.uuid4())
        project_path = self.local_root / name
        
        # Create project directory structure (like Ayon)
        project_path.mkdir(exist_ok=True)
        (project_path / "Assets").mkdir(exist_ok=True)
        (project_path / "Shots").mkdir(exist_ok=True)
        (project_path / "Library").mkdir(exist_ok=True)
        (project_path / "Workfiles").mkdir(exist_ok=True)
        (project_path / "Publish").mkdir(exist_ok=True)
        
        # Create project
        project = VogueProject(
            id=project_id,
            name=name,
            code=code or name.upper(),
            library=library,
            created_by="local_user",
            updated_by="local_user"
        )
        
        # Save project
        self._save_project(project)
        self._projects_cache[project_id] = project
        
        self.logger.info(f"Created Ayon project: {name} at {project_path}")
        return project
    
    def load_project(self, project_name: str) -> Optional[VogueProject]:
        """Load an existing project"""
        project_path = self.local_root / project_name
        project_file = project_path / "project.json"
        
        if not project_file.exists():
            self.logger.error(f"Project file not found: {project_file}")
            return None
        
        try:
            with open(project_file, 'r') as f:
                data = json.load(f)
            
            # Convert datetime strings back to datetime objects
            if 'created_at' in data:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            if 'updated_at' in data:
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
            # Set the path for the project
            data['path'] = str(project_path)
            
            project = VogueProject(**data)
            self._projects_cache[project.id] = project
            self.current_project = project
            self.current_project_path = project_path
            
            self.logger.info(f"Loaded Ayon project: {project_name}")
            return project
            
        except Exception as e:
            self.logger.error(f"Failed to load project {project_name}: {e}")
            return None
    
    def save_project(self, project: VogueProject) -> bool:
        """Save project to local storage"""
        try:
            self._save_project(project)
            self._projects_cache[project.id] = project
            return True
        except Exception as e:
            self.logger.error(f"Failed to save project {project.name}: {e}")
            return False
    
    def _save_project(self, project: VogueProject):
        """Internal method to save project data"""
        project_path = self.local_root / project.name
        project_path.mkdir(exist_ok=True)
        project_file = project_path / "project.json"
        
        # Convert to dict and handle datetime serialization
        data = asdict(project)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        
        with open(project_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_projects(self) -> List[VogueProject]:
        """Get all available projects"""
        projects = []
        for project_dir in self.local_root.iterdir():
            if project_dir.is_dir() and (project_dir / "project.json").exists():
                project = self.load_project(project_dir.name)
                if project:
                    projects.append(project)
        return projects
    
    # Folder Management (from ayon_server/entities/folder.py)
    def create_folder(self, name: str, folder_type: str, parent_id: Optional[str] = None) -> AyonFolder:
        """Create a new folder in Ayon hierarchy"""
        if not self.current_project:
            raise ValueError("No current project")
        
        folder_id = str(uuid.uuid4())
        
        # Calculate path (like Ayon)
        if parent_id:
            parent = self.get_folder(parent_id)
            if parent:
                path = f"{parent.path}/{name}" if parent.path else name
            else:
                path = name
        else:
            path = name
        
        folder = AyonFolder(
            id=folder_id,
            name=name,
            folder_type=folder_type,
            parent_id=parent_id,
            path=path,
            project_name=self.current_project.name,
            created_by="local_user",
            updated_by="local_user"
        )
        
        # Update parent's children (like Ayon hierarchy)
        if parent_id:
            parent = self.get_folder(parent_id)
            if parent:
                parent.children.append(folder_id)
                self.save_folder(parent)
        
        # Save folder
        self._save_folder(folder)
        self._folders_cache[folder_id] = folder
        
        self.logger.info(f"Created Ayon folder: {name} ({folder_type}) at {path}")
        return folder
    
    def get_folder(self, folder_id: str) -> Optional[AyonFolder]:
        """Get folder by ID"""
        if folder_id in self._folders_cache:
            return self._folders_cache[folder_id]
        
        if not self.current_project_path:
            return None
        
        folder_file = self.current_project_path / "folders" / f"{folder_id}.json"
        if folder_file.exists():
            try:
                with open(folder_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                folder = AyonFolder(**data)
                self._folders_cache[folder_id] = folder
                return folder
            except Exception as e:
                self.logger.error(f"Failed to load folder {folder_id}: {e}")
        
        return None
    
    def save_folder(self, folder: AyonFolder) -> bool:
        """Save folder to local storage"""
        try:
            self._save_folder(folder)
            self._folders_cache[folder.id] = folder
            return True
        except Exception as e:
            self.logger.error(f"Failed to save folder {folder.name}: {e}")
            return False
    
    def _save_folder(self, folder: AyonFolder):
        """Internal method to save folder data"""
        if not self.current_project_path:
            return
        
        folders_dir = self.current_project_path / "folders"
        folders_dir.mkdir(exist_ok=True)
        
        folder_file = folders_dir / f"{folder.id}.json"
        
        # Convert to dict and handle datetime serialization
        data = asdict(folder)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        
        with open(folder_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_hierarchy(self, project_name: str) -> List[Dict[str, Any]]:
        """Get Ayon-style hierarchy for UI"""
        project = self.load_project(project_name)
        if not project:
            return []
        
        # Load all folders for this project
        folders_dir = self.current_project_path / "folders"
        if not folders_dir.exists():
            return []
        
        folders = []
        for folder_file in folders_dir.glob("*.json"):
            try:
                with open(folder_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data and isinstance(data['created_at'], str):
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data and isinstance(data['updated_at'], str):
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                folders.append(AyonFolder(**data))
            except Exception as e:
                self.logger.error(f"Failed to load folder from {folder_file}: {e}")
        
        # Build hierarchy tree (like Ayon)
        return self._build_hierarchy_tree(folders)
    
    def _build_hierarchy_tree(self, folders: List[AyonFolder]) -> List[Dict[str, Any]]:
        """Build hierarchy tree from folders (like Ayon)"""
        folder_map = {f.id: f for f in folders}
        root_folders = [f for f in folders if f.parent_id is None]
        
        def build_node(folder: AyonFolder) -> Dict[str, Any]:
            children = [build_node(folder_map[child_id]) for child_id in folder.children if child_id in folder_map]
            
            return {
                "id": folder.id,
                "name": folder.name,
                "label": folder.label,
                "type": folder.folder_type.lower(),
                "path": folder.path,
                "status": folder.status,
                "active": folder.active,
                "has_versions": folder.has_versions,
                "created_at": folder.created_at.isoformat(),
                "updated_at": folder.updated_at.isoformat(),
                "children": children
            }
        
        return [build_node(folder) for folder in root_folders]
    
    # Product Management (from ayon_server/entities/product.py)
    def create_product(self, name: str, product_type: str, folder_id: str) -> AyonProduct:
        """Create a new product"""
        if not self.current_project:
            raise ValueError("No current project")
        
        product_id = str(uuid.uuid4())
        
        product = AyonProduct(
            id=product_id,
            name=name,
            product_type=product_type,
            folder_id=folder_id,
            project_name=self.current_project.name,
            created_by="local_user",
            updated_by="local_user"
        )
        
        # Update folder's products
        folder = self.get_folder(folder_id)
        if folder:
            folder.products.append(product_id)
            self.save_folder(folder)
        
        # Save product
        self._save_product(product)
        self._products_cache[product_id] = product
        
        self.logger.info(f"Created Ayon product: {name} ({product_type})")
        return product
    
    def get_product(self, product_id: str) -> Optional[AyonProduct]:
        """Get product by ID"""
        if product_id in self._products_cache:
            return self._products_cache[product_id]
        
        if not self.current_project_path:
            return None
        
        product_file = self.current_project_path / "products" / f"{product_id}.json"
        if product_file.exists():
            try:
                with open(product_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                product = AyonProduct(**data)
                self._products_cache[product_id] = product
                return product
            except Exception as e:
                self.logger.error(f"Failed to load product {product_id}: {e}")
        
        return None
    
    def save_product(self, product: AyonProduct) -> bool:
        """Save product to local storage"""
        try:
            self._save_product(product)
            self._products_cache[product.id] = product
            return True
        except Exception as e:
            self.logger.error(f"Failed to save product {product.name}: {e}")
            return False
    
    def _save_product(self, product: AyonProduct):
        """Internal method to save product data"""
        if not self.current_project_path:
            return
        
        products_dir = self.current_project_path / "products"
        products_dir.mkdir(exist_ok=True)
        
        product_file = products_dir / f"{product.id}.json"
        
        # Convert to dict and handle datetime serialization
        data = asdict(product)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        
        with open(product_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    # Task Management (from ayon_server/entities/task.py)
    def create_task(self, name: str, task_type: str, folder_id: str) -> AyonTask:
        """Create a new task"""
        if not self.current_project:
            raise ValueError("No current project")
        
        task_id = str(uuid.uuid4())
        
        task = AyonTask(
            id=task_id,
            name=name,
            task_type=task_type,
            folder_id=folder_id,
            project_name=self.current_project.name,
            created_by="local_user",
            updated_by="local_user"
        )
        
        # Update folder's tasks
        folder = self.get_folder(folder_id)
        if folder:
            folder.tasks.append(task_id)
            self.save_folder(folder)
        
        # Save task
        self._save_task(task)
        self._tasks_cache[task_id] = task
        
        self.logger.info(f"Created Ayon task: {name} ({task_type})")
        return task
    
    def get_task(self, task_id: str) -> Optional[AyonTask]:
        """Get task by ID"""
        if task_id in self._tasks_cache:
            return self._tasks_cache[task_id]
        
        if not self.current_project_path:
            return None
        
        task_file = self.current_project_path / "tasks" / f"{task_id}.json"
        if task_file.exists():
            try:
                with open(task_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                task = AyonTask(**data)
                self._tasks_cache[task_id] = task
                return task
            except Exception as e:
                self.logger.error(f"Failed to load task {task_id}: {e}")
        
        return None
    
    def save_task(self, task: AyonTask) -> bool:
        """Save task to local storage"""
        try:
            self._save_task(task)
            self._tasks_cache[task.id] = task
            return True
        except Exception as e:
            self.logger.error(f"Failed to save task {task.name}: {e}")
            return False
    
    def _save_task(self, task: AyonTask):
        """Internal method to save task data"""
        if not self.current_project_path:
            return
        
        tasks_dir = self.current_project_path / "tasks"
        tasks_dir.mkdir(exist_ok=True)
        
        task_file = tasks_dir / f"{task.id}.json"
        
        # Convert to dict and handle datetime serialization
        data = asdict(task)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        
        with open(task_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    # Version Management
    def create_version(self, product_id: str, version: int = 1, task_id: Optional[str] = None) -> AyonVersion:
        """Create a new version"""
        if not self.current_project:
            raise ValueError("No current project")
        
        version_id = str(uuid.uuid4())
        
        version_obj = AyonVersion(
            id=version_id,
            name=f"v{version:03d}",
            version=version,
            product_id=product_id,
            task_id=task_id,
            project_name=self.current_project.name,
            created_by="local_user",
            updated_by="local_user"
        )
        
        # Update product's versions
        product = self.get_product(product_id)
        if product:
            product.versions.append(version_id)
            self.save_product(product)
        
        # Save version
        self._save_version(version_obj)
        self._versions_cache[version_id] = version_obj
        
        self.logger.info(f"Created Ayon version: v{version:03d} for product {product_id}")
        return version_obj
    
    def get_version(self, version_id: str) -> Optional[AyonVersion]:
        """Get version by ID"""
        if version_id in self._versions_cache:
            return self._versions_cache[version_id]
        
        if not self.current_project_path:
            return None
        
        version_file = self.current_project_path / "versions" / f"{version_id}.json"
        if version_file.exists():
            try:
                with open(version_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                version = AyonVersion(**data)
                self._versions_cache[version_id] = version
                return version
            except Exception as e:
                self.logger.error(f"Failed to load version {version_id}: {e}")
        
        return None
    
    def save_version(self, version: AyonVersion) -> bool:
        """Save version to local storage"""
        try:
            self._save_version(version)
            self._versions_cache[version.id] = version
            return True
        except Exception as e:
            self.logger.error(f"Failed to save version {version.name}: {e}")
            return False
    
    def _save_version(self, version: AyonVersion):
        """Internal method to save version data"""
        if not self.current_project_path:
            return
        
        versions_dir = self.current_project_path / "versions"
        versions_dir.mkdir(exist_ok=True)
        
        version_file = versions_dir / f"{version.id}.json"
        
        # Convert to dict and handle datetime serialization
        data = asdict(version)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        
        with open(version_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    # User Management
    def create_user(self, name: str, email: str, role: str = "Artist") -> AyonUser:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        
        user = AyonUser(
            id=user_id,
            name=name,
            email=email,
            created_by="local_user",
            updated_by="local_user"
        )
        
        # Save user
        self._save_user(user)
        self._users_cache[user_id] = user
        
        self.logger.info(f"Created Ayon user: {name} ({email})")
        return user
    
    def get_user(self, user_id: str) -> Optional[AyonUser]:
        """Get user by ID"""
        if user_id in self._users_cache:
            return self._users_cache[user_id]
        
        users_file = self.local_root / "users.json"
        if users_file.exists():
            try:
                with open(users_file, 'r') as f:
                    users_data = json.load(f)
                
                for user_data in users_data:
                    if user_data["id"] == user_id:
                        # Convert datetime strings back to datetime objects
                        if 'created_at' in user_data:
                            user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
                        if 'updated_at' in user_data:
                            user_data['updated_at'] = datetime.fromisoformat(user_data['updated_at'])
                        if 'last_login' in user_data and user_data['last_login']:
                            user_data['last_login'] = datetime.fromisoformat(user_data['last_login'])
                        
                        user = AyonUser(**user_data)
                        self._users_cache[user_id] = user
                        return user
            except Exception as e:
                self.logger.error(f"Failed to load user {user_id}: {e}")
        
        return None
    
    def save_user(self, user: AyonUser) -> bool:
        """Save user to local storage"""
        try:
            self._save_user(user)
            self._users_cache[user.id] = user
            return True
        except Exception as e:
            self.logger.error(f"Failed to save user {user.name}: {e}")
            return False
    
    def _save_user(self, user: AyonUser):
        """Internal method to save user data"""
        users_file = self.local_root / "users.json"
        
        # Load existing users
        users = []
        if users_file.exists():
            try:
                with open(users_file, 'r') as f:
                    users = json.load(f)
            except:
                users = []
        
        # Update or add user
        user_data = asdict(user)
        for key, value in user_data.items():
            if isinstance(value, datetime):
                user_data[key] = value.isoformat()
        
        user_found = False
        for i, existing_user in enumerate(users):
            if existing_user["id"] == user.id:
                users[i] = user_data
                user_found = True
                break
        
        if not user_found:
            users.append(user_data)
        
        # Save users
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=4)
    
    def get_users(self) -> List[AyonUser]:
        """Get all users"""
        users_file = self.local_root / "users.json"
        if not users_file.exists():
            return []
        
        try:
            with open(users_file, 'r') as f:
                users_data = json.load(f)
            
            users = []
            for user_data in users_data:
                # Convert datetime strings back to datetime objects
                if 'created_at' in user_data:
                    user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
                if 'updated_at' in user_data:
                    user_data['updated_at'] = datetime.fromisoformat(user_data['updated_at'])
                if 'last_login' in user_data and user_data['last_login']:
                    user_data['last_login'] = datetime.fromisoformat(user_data['last_login'])
                
                user = AyonUser(**user_data)
                users.append(user)
                self._users_cache[user.id] = user
            
            return users
        except Exception as e:
            self.logger.error(f"Failed to load users: {e}")
            return []
    
    # Utility methods
    def get_project_stats(self, project_name: str) -> Dict[str, Any]:
        """Get project statistics"""
        project = self.load_project(project_name)
        if not project:
            return {}
        
        # Count entities
        folders_count = len(list((self.current_project_path / "folders").glob("*.json")))
        products_count = len(list((self.current_project_path / "products").glob("*.json")))
        tasks_count = len(list((self.current_project_path / "tasks").glob("*.json")))
        versions_count = len(list((self.current_project_path / "versions").glob("*.json")))
        
        return {
            "folders": folders_count,
            "products": products_count,
            "tasks": tasks_count,
            "versions": versions_count,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    
    def search_entities(self, query: str, entity_types: List[str] = None) -> List[Dict[str, Any]]:
        """Search entities across the project"""
        if not self.current_project_path:
            return []
        
        results = []
        
        # Search folders
        if not entity_types or "folder" in entity_types:
            folders_dir = self.current_project_path / "folders"
            if folders_dir.exists():
                for folder_file in folders_dir.glob("*.json"):
                    try:
                        with open(folder_file, 'r') as f:
                            data = json.load(f)
                        if query.lower() in data.get("name", "").lower():
                            results.append({
                                "type": "folder",
                                "id": data["id"],
                                "name": data["name"],
                                "path": data.get("path", ""),
                                "folder_type": data.get("folder_type", "")
                            })
                    except:
                        continue
        
        # Search products
        if not entity_types or "product" in entity_types:
            products_dir = self.current_project_path / "products"
            if products_dir.exists():
                for product_file in products_dir.glob("*.json"):
                    try:
                        with open(product_file, 'r') as f:
                            data = json.load(f)
                        if query.lower() in data.get("name", "").lower():
                            results.append({
                                "type": "product",
                                "id": data["id"],
                                "name": data["name"],
                                "product_type": data.get("product_type", "")
                            })
                    except:
                        continue
        
        return results
    
    # Missing Ayon Backend Methods for UI Integration
    
    def get_products(self, folder_id: str) -> List[Dict[str, Any]]:
        """Get products for a specific folder"""
        if not self.current_project_path:
            return []
        
        products = []
        products_dir = self.current_project_path / "products"
        if not products_dir.exists():
            return []
        
        for product_file in products_dir.glob("*.json"):
            try:
                with open(product_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                product = AyonProduct(**data)
                
                # Filter by folder_id
                if product.folder_id == folder_id:
                    products.append({
                        "id": product.id,
                        "name": product.name,
                        "product_type": product.product_type,
                        "status": product.status,
                        "active": product.active,
                        "created_at": product.created_at.isoformat(),
                        "updated_at": product.updated_at.isoformat(),
                        "versions_count": len(product.versions),
                        "representations_count": len(product.representations)
                    })
                    
            except Exception as e:
                self.logger.error(f"Failed to load product from {product_file}: {e}")
        
        return products
    
    def get_tasks(self, folder_id: str) -> List[Dict[str, Any]]:
        """Get tasks for a specific folder"""
        if not self.current_project_path:
            return []
        
        tasks = []
        tasks_dir = self.current_project_path / "tasks"
        if not tasks_dir.exists():
            return []
        
        for task_file in tasks_dir.glob("*.json"):
            try:
                with open(task_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                task = AyonTask(**data)
                
                # Filter by folder_id
                if task.folder_id == folder_id:
                    tasks.append({
                        "id": task.id,
                        "name": task.name,
                        "label": task.label,
                        "task_type": task.task_type,
                        "status": task.status,
                        "active": task.active,
                        "assignees": task.assignees,
                        "created_at": task.created_at.isoformat(),
                        "updated_at": task.updated_at.isoformat()
                    })
                    
            except Exception as e:
                self.logger.error(f"Failed to load task from {task_file}: {e}")
        
        return tasks
    
    def get_versions(self, product_id: str) -> List[Dict[str, Any]]:
        """Get versions for a specific product"""
        if not self.current_project_path:
            return []
        
        versions = []
        versions_dir = self.current_project_path / "versions"
        if not versions_dir.exists():
            return []
        
        for version_file in versions_dir.glob("*.json"):
            try:
                with open(version_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                version = AyonVersion(**data)
                
                # Filter by product_id
                if version.product_id == product_id:
                    versions.append({
                        "id": version.id,
                        "name": version.name,
                        "version": version.version,
                        "status": version.status,
                        "active": version.active,
                        "task_id": version.task_id,
                        "created_at": version.created_at.isoformat(),
                        "updated_at": version.updated_at.isoformat(),
                        "representations_count": len(version.representations),
                        "files_count": len(version.files)
                    })
                    
            except Exception as e:
                self.logger.error(f"Failed to load version from {version_file}: {e}")
        
        # Sort by version number
        versions.sort(key=lambda x: x["version"])
        return versions
    
    def get_representations(self, version_id: str) -> List[Dict[str, Any]]:
        """Get representations for a specific version"""
        if not self.current_project_path:
            return []
        
        representations = []
        representations_dir = self.current_project_path / "representations"
        if not representations_dir.exists():
            return []
        
        for rep_file in representations_dir.glob("*.json"):
            try:
                with open(rep_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                representation = AyonRepresentation(**data)
                
                # Filter by version_id
                if representation.version_id == version_id:
                    representations.append({
                        "id": representation.id,
                        "name": representation.name,
                        "status": representation.status,
                        "active": representation.active,
                        "created_at": representation.created_at.isoformat(),
                        "updated_at": representation.updated_at.isoformat(),
                        "files_count": len(representation.files)
                    })
                    
            except Exception as e:
                self.logger.error(f"Failed to load representation from {rep_file}: {e}")
        
        return representations
    
    def create_representation(self, name: str, version_id: str) -> AyonRepresentation:
        """Create a new representation"""
        if not self.current_project:
            raise ValueError("No current project")
        
        representation_id = str(uuid.uuid4())
        
        representation = AyonRepresentation(
            id=representation_id,
            name=name,
            version_id=version_id,
            project_name=self.current_project.name,
            created_by="local_user",
            updated_by="local_user"
        )
        
        # Update version's representations
        version = self.get_version(version_id)
        if version:
            version.representations.append(representation_id)
            self.save_version(version)
        
        # Save representation
        self._save_representation(representation)
        self._representations_cache[representation_id] = representation
        
        self.logger.info(f"Created Ayon representation: {name} for version {version_id}")
        return representation
    
    def get_representation(self, representation_id: str) -> Optional[AyonRepresentation]:
        """Get representation by ID"""
        if representation_id in self._representations_cache:
            return self._representations_cache[representation_id]
        
        if not self.current_project_path:
            return None
        
        rep_file = self.current_project_path / "representations" / f"{representation_id}.json"
        if rep_file.exists():
            try:
                with open(rep_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                representation = AyonRepresentation(**data)
                self._representations_cache[representation_id] = representation
                return representation
            except Exception as e:
                self.logger.error(f"Failed to load representation {representation_id}: {e}")
        
        return None
    
    def save_representation(self, representation: AyonRepresentation) -> bool:
        """Save representation to local storage"""
        try:
            self._save_representation(representation)
            self._representations_cache[representation.id] = representation
            return True
        except Exception as e:
            self.logger.error(f"Failed to save representation {representation.name}: {e}")
            return False
    
    def _save_representation(self, representation: AyonRepresentation):
        """Internal method to save representation data"""
        if not self.current_project_path:
            return
        
        representations_dir = self.current_project_path / "representations"
        representations_dir.mkdir(exist_ok=True)
        
        rep_file = representations_dir / f"{representation.id}.json"
        
        # Convert to dict and handle datetime serialization
        data = asdict(representation)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        
        with open(rep_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_folders_by_type(self, folder_type: str) -> List[Dict[str, Any]]:
        """Get all folders of a specific type"""
        if not self.current_project_path:
            return []
        
        folders = []
        folders_dir = self.current_project_path / "folders"
        if not folders_dir.exists():
            return []
        
        for folder_file in folders_dir.glob("*.json"):
            try:
                with open(folder_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                folder = AyonFolder(**data)
                
                # Filter by folder_type
                if folder.folder_type == folder_type:
                    folders.append({
                        "id": folder.id,
                        "name": folder.name,
                        "label": folder.label,
                        "path": folder.path,
                        "status": folder.status,
                        "active": folder.active,
                        "parent_id": folder.parent_id,
                        "created_at": folder.created_at.isoformat(),
                        "updated_at": folder.updated_at.isoformat(),
                        "children_count": len(folder.children),
                        "products_count": len(folder.products),
                        "tasks_count": len(folder.tasks)
                    })
                    
            except Exception as e:
                self.logger.error(f"Failed to load folder from {folder_file}: {e}")
        
        return folders
    
    def get_products_by_type(self, product_type: str) -> List[Dict[str, Any]]:
        """Get all products of a specific type"""
        if not self.current_project_path:
            return []
        
        products = []
        products_dir = self.current_project_path / "products"
        if not products_dir.exists():
            return []
        
        for product_file in products_dir.glob("*.json"):
            try:
                with open(product_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                product = AyonProduct(**data)
                
                # Filter by product_type
                if product.product_type == product_type:
                    products.append({
                        "id": product.id,
                        "name": product.name,
                        "folder_id": product.folder_id,
                        "status": product.status,
                        "active": product.active,
                        "created_at": product.created_at.isoformat(),
                        "updated_at": product.updated_at.isoformat(),
                        "versions_count": len(product.versions),
                        "representations_count": len(product.representations)
                    })
                    
            except Exception as e:
                self.logger.error(f"Failed to load product from {product_file}: {e}")
        
        return products
    
    def get_tasks_by_type(self, task_type: str) -> List[Dict[str, Any]]:
        """Get all tasks of a specific type"""
        if not self.current_project_path:
            return []
        
        tasks = []
        tasks_dir = self.current_project_path / "tasks"
        if not tasks_dir.exists():
            return []
        
        for task_file in tasks_dir.glob("*.json"):
            try:
                with open(task_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                task = AyonTask(**data)
                
                # Filter by task_type
                if task.task_type == task_type:
                    tasks.append({
                        "id": task.id,
                        "name": task.name,
                        "label": task.label,
                        "folder_id": task.folder_id,
                        "status": task.status,
                        "active": task.active,
                        "assignees": task.assignees,
                        "created_at": task.created_at.isoformat(),
                        "updated_at": task.updated_at.isoformat()
                    })
                    
            except Exception as e:
                self.logger.error(f"Failed to load task from {task_file}: {e}")
        
        return tasks
    
    def update_entity_status(self, entity_type: str, entity_id: str, status: str) -> bool:
        """Update status of any entity"""
        try:
            if entity_type == "folder":
                entity = self.get_folder(entity_id)
            elif entity_type == "product":
                entity = self.get_product(entity_id)
            elif entity_type == "task":
                entity = self.get_task(entity_id)
            elif entity_type == "version":
                entity = self.get_version(entity_id)
            elif entity_type == "representation":
                entity = self.get_representation(entity_id)
            else:
                return False
            
            if entity:
                entity.status = status
                entity.updated_at = datetime.now()
                
                if entity_type == "folder":
                    return self.save_folder(entity)
                elif entity_type == "product":
                    return self.save_product(entity)
                elif entity_type == "task":
                    return self.save_task(entity)
                elif entity_type == "version":
                    return self.save_version(entity)
                elif entity_type == "representation":
                    return self.save_representation(entity)
            
            return False
        except Exception as e:
            self.logger.error(f"Failed to update {entity_type} {entity_id} status: {e}")
            return False
    
    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """Delete any entity"""
        try:
            if entity_type == "folder":
                entity_file = self.current_project_path / "folders" / f"{entity_id}.json"
            elif entity_type == "product":
                entity_file = self.current_project_path / "products" / f"{entity_id}.json"
            elif entity_type == "task":
                entity_file = self.current_project_path / "tasks" / f"{entity_id}.json"
            elif entity_type == "version":
                entity_file = self.current_project_path / "versions" / f"{entity_id}.json"
            elif entity_type == "representation":
                entity_file = self.current_project_path / "representations" / f"{entity_id}.json"
            else:
                return False
            
            if entity_file.exists():
                entity_file.unlink()
                
                # Remove from cache
                if entity_type == "folder" and entity_id in self._folders_cache:
                    del self._folders_cache[entity_id]
                elif entity_type == "product" and entity_id in self._products_cache:
                    del self._products_cache[entity_id]
                elif entity_type == "task" and entity_id in self._tasks_cache:
                    del self._tasks_cache[entity_id]
                elif entity_type == "version" and entity_id in self._versions_cache:
                    del self._versions_cache[entity_id]
                elif entity_type == "representation" and entity_id in self._representations_cache:
                    del self._representations_cache[entity_id]
                
                self.logger.info(f"Deleted {entity_type}: {entity_id}")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete {entity_type} {entity_id}: {e}")
            return False
    
    # Ayon Anatomy System (from ayon_server/settings/anatomy)
    def get_anatomy(self, project_name: str) -> Dict[str, Any]:
        """Get project anatomy configuration"""
        project = self.load_project(project_name)
        if not project:
            return {}
        
        return {
            "project": {
                "name": project.name,
                "code": project.code,
                "library": project.library,
                "config": project.config,
                "attrib": project.attrib,
                "data": project.data
            },
            "folder_types": project.folder_types,
            "task_types": project.task_types,
            "statuses": project.statuses,
            "tags": project.tags,
            "link_types": project.link_types
        }
    
    def update_anatomy(self, project_name: str, anatomy_data: Dict[str, Any]) -> bool:
        """Update project anatomy configuration"""
        project = self.load_project(project_name)
        if not project:
            return False
        
        try:
            if "folder_types" in anatomy_data:
                project.folder_types = anatomy_data["folder_types"]
            if "task_types" in anatomy_data:
                project.task_types = anatomy_data["task_types"]
            if "statuses" in anatomy_data:
                project.statuses = anatomy_data["statuses"]
            if "tags" in anatomy_data:
                project.tags = anatomy_data["tags"]
            if "link_types" in anatomy_data:
                project.link_types = anatomy_data["link_types"]
            
            return self.save_project(project)
        except Exception as e:
            self.logger.error(f"Failed to update anatomy: {e}")
            return False
    
    # Ayon File Management System (from ayon_server/files)
    def create_file(self, file_path: str, file_data: bytes, metadata: Dict[str, Any] = None) -> str:
        """Create a file in the project storage"""
        if not self.current_project_path:
            raise ValueError("No current project")
        
        file_id = str(uuid.uuid4())
        storage_path = self.current_project_path / "files" / file_id
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(storage_path, 'wb') as f:
            f.write(file_data)
        
        # Save file metadata
        metadata_file = storage_path.with_suffix('.json')
        file_metadata = {
            "id": file_id,
            "path": file_path,
            "size": len(file_data),
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(file_metadata, f, indent=4)
        
        self.logger.info(f"Created file: {file_path} ({len(file_data)} bytes)")
        return file_id
    
    def get_file(self, file_id: str) -> Optional[bytes]:
        """Get file data by ID"""
        if not self.current_project_path:
            return None
        
        file_path = self.current_project_path / "files" / file_id
        if file_path.exists():
            with open(file_path, 'rb') as f:
                return f.read()
        return None
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file metadata by ID"""
        if not self.current_project_path:
            return None
        
        metadata_file = self.current_project_path / "files" / f"{file_id}.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return None
    
    # Ayon Thumbnails System (from ayon_server/thumbnails)
    def create_thumbnail(self, entity_id: str, thumbnail_data: bytes, thumbnail_type: str = "image") -> str:
        """Create a thumbnail for an entity"""
        if not self.current_project_path:
            raise ValueError("No current project")
        
        thumbnail_id = str(uuid.uuid4())
        thumbnails_dir = self.current_project_path / "thumbnails"
        thumbnails_dir.mkdir(exist_ok=True)
        
        # Save thumbnail file
        thumbnail_file = thumbnails_dir / f"{thumbnail_id}.{thumbnail_type}"
        with open(thumbnail_file, 'wb') as f:
            f.write(thumbnail_data)
        
        # Save thumbnail metadata
        metadata = {
            "id": thumbnail_id,
            "entity_id": entity_id,
            "type": thumbnail_type,
            "size": len(thumbnail_data),
            "created_at": datetime.now().isoformat()
        }
        
        metadata_file = thumbnails_dir / f"{thumbnail_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        self.logger.info(f"Created thumbnail: {thumbnail_id} for entity {entity_id}")
        return thumbnail_id
    
    def get_thumbnail(self, thumbnail_id: str) -> Optional[bytes]:
        """Get thumbnail data by ID"""
        if not self.current_project_path:
            return None
        
        thumbnails_dir = self.current_project_path / "thumbnails"
        for ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
            thumbnail_file = thumbnails_dir / f"{thumbnail_id}.{ext}"
            if thumbnail_file.exists():
                with open(thumbnail_file, 'rb') as f:
                    return f.read()
        return None
    
    # Ayon Links System (from ayon_server/entities/links)
    def create_link(self, input_id: str, output_id: str, link_type: str = "reference") -> str:
        """Create a link between entities"""
        if not self.current_project:
            raise ValueError("No current project")
        
        link_id = str(uuid.uuid4())
        
        link = {
            "id": link_id,
            "input_id": input_id,
            "output_id": output_id,
            "link_type": link_type,
            "project_name": self.current_project.name,
            "created_at": datetime.now().isoformat(),
            "created_by": "local_user"
        }
        
        # Save link
        links_dir = self.current_project_path / "links"
        links_dir.mkdir(exist_ok=True)
        
        link_file = links_dir / f"{link_id}.json"
        with open(link_file, 'w') as f:
            json.dump(link, f, indent=4)
        
        self.logger.info(f"Created link: {link_type} from {input_id} to {output_id}")
        return link_id
    
    def get_links(self, entity_id: str = None, link_type: str = None) -> List[Dict[str, Any]]:
        """Get links for an entity or all links"""
        if not self.current_project_path:
            return []
        
        links_dir = self.current_project_path / "links"
        if not links_dir.exists():
            return []
        
        links = []
        for link_file in links_dir.glob("*.json"):
            try:
                with open(link_file, 'r') as f:
                    link_data = json.load(f)
                
                # Filter by entity_id if specified
                if entity_id and entity_id not in [link_data.get("input_id"), link_data.get("output_id")]:
                    continue
                
                # Filter by link_type if specified
                if link_type and link_data.get("link_type") != link_type:
                    continue
                
                links.append(link_data)
                
            except Exception as e:
                self.logger.error(f"Failed to load link from {link_file}: {e}")
        
        return links
    
    # Ayon Review System (from ayon_server/review)
    def create_review(self, entity_id: str, entity_type: str, comment: str, 
                     status: str = "pending", reviewer_id: str = None) -> str:
        """Create a review for an entity"""
        if not self.current_project:
            raise ValueError("No current project")
        
        review_id = str(uuid.uuid4())
        
        review = {
            "id": review_id,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "comment": comment,
            "status": status,
            "reviewer_id": reviewer_id,
            "project_name": self.current_project.name,
            "created_at": datetime.now().isoformat(),
            "created_by": "local_user"
        }
        
        # Save review
        reviews_dir = self.current_project_path / "reviews"
        reviews_dir.mkdir(exist_ok=True)
        
        review_file = reviews_dir / f"{review_id}.json"
        with open(review_file, 'w') as f:
            json.dump(review, f, indent=4)
        
        self.logger.info(f"Created review: {review_id} for {entity_type} {entity_id}")
        return review_id
    
    def get_reviews(self, entity_id: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Get reviews for an entity or all reviews"""
        if not self.current_project_path:
            return []
        
        reviews_dir = self.current_project_path / "reviews"
        if not reviews_dir.exists():
            return []
        
        reviews = []
        for review_file in reviews_dir.glob("*.json"):
            try:
                with open(review_file, 'r') as f:
                    review_data = json.load(f)
                
                # Filter by entity_id if specified
                if entity_id and review_data.get("entity_id") != entity_id:
                    continue
                
                # Filter by status if specified
                if status and review_data.get("status") != status:
                    continue
                
                reviews.append(review_data)
                
            except Exception as e:
                self.logger.error(f"Failed to load review from {review_file}: {e}")
        
        return reviews
    
    # Ayon Events System (from ayon_server/events)
    def dispatch_event(self, event_type: str, data: Dict[str, Any] = None) -> str:
        """Dispatch an event"""
        if not self.current_project:
            raise ValueError("No current project")
        
        event_id = str(uuid.uuid4())
        
        event = {
            "id": event_id,
            "type": event_type,
            "project_name": self.current_project.name,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "sender": "local_user"
        }
        
        # Save event
        events_dir = self.current_project_path / "events"
        events_dir.mkdir(exist_ok=True)
        
        event_file = events_dir / f"{event_id}.json"
        with open(event_file, 'w') as f:
            json.dump(event, f, indent=4)
        
        self.logger.info(f"Dispatched event: {event_type}")
        return event_id
    
    def get_events(self, event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events"""
        if not self.current_project_path:
            return []
        
        events_dir = self.current_project_path / "events"
        if not events_dir.exists():
            return []
        
        events = []
        for event_file in events_dir.glob("*.json"):
            try:
                with open(event_file, 'r') as f:
                    event_data = json.load(f)
                
                # Filter by event_type if specified
                if event_type and event_data.get("type") != event_type:
                    continue
                
                events.append(event_data)
                
            except Exception as e:
                self.logger.error(f"Failed to load event from {event_file}: {e}")
        
        # Sort by timestamp and limit
        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return events[:limit]
    
    # Ayon Query System (from ayon_server/query)
    def query_entities(self, entity_type: str, filters: Dict[str, Any] = None, 
                      limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Query entities with filters"""
        if not self.current_project_path:
            return []
        
        entities_dir = self.current_project_path / entity_type
        if not entities_dir.exists():
            return []
        
        entities = []
        for entity_file in entities_dir.glob("*.json"):
            try:
                with open(entity_file, 'r') as f:
                    entity_data = json.load(f)
                
                # Apply filters
                if filters:
                    match = True
                    for key, value in filters.items():
                        if key not in entity_data or entity_data[key] != value:
                            match = False
                            break
                    if not match:
                        continue
                
                entities.append(entity_data)
                
            except Exception as e:
                self.logger.error(f"Failed to load {entity_type} from {entity_file}: {e}")
        
        # Apply pagination
        return entities[offset:offset + limit]
    
    # Ayon Operations System (from ayon_server/operations)
    def create_operation(self, operation_type: str, data: Dict[str, Any]) -> str:
        """Create an operation"""
        if not self.current_project:
            raise ValueError("No current project")
        
        operation_id = str(uuid.uuid4())
        
        operation = {
            "id": operation_id,
            "type": operation_type,
            "data": data,
            "project_name": self.current_project.name,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "created_by": "local_user"
        }
        
        # Save operation
        operations_dir = self.current_project_path / "operations"
        operations_dir.mkdir(exist_ok=True)
        
        operation_file = operations_dir / f"{operation_id}.json"
        with open(operation_file, 'w') as f:
            json.dump(operation, f, indent=4)
        
        self.logger.info(f"Created operation: {operation_type}")
        return operation_id
    
    def get_operations(self, status: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get operations"""
        if not self.current_project_path:
            return []
        
        operations_dir = self.current_project_path / "operations"
        if not operations_dir.exists():
            return []
        
        operations = []
        for operation_file in operations_dir.glob("*.json"):
            try:
                with open(operation_file, 'r') as f:
                    operation_data = json.load(f)
                
                # Filter by status if specified
                if status and operation_data.get("status") != status:
                    continue
                
                operations.append(operation_data)
                
            except Exception as e:
                self.logger.error(f"Failed to load operation from {operation_file}: {e}")
        
        # Sort by timestamp and limit
        operations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return operations[:limit]
    
    # Ayon Access Control System
    def authenticate_user(self, email: str, password: str) -> Optional[AyonUser]:
        """Authenticate user with email and password"""
        users = self.get_users()
        for user in users:
            if user.email == email and user.password_hash == self._hash_password(password):
                user.last_login = datetime.now()
                self.save_user(user)
                self.logger.info(f"User authenticated: {user.name} ({email})")
                return user
        return None
    
    def _hash_password(self, password: str) -> str:
        """Hash password (simple implementation)"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user_with_access(self, name: str, email: str, password: str, 
                              access_groups: List[str] = None, permissions: List[str] = None) -> AyonUser:
        """Create user with access control"""
        user = AyonUser(
            name=name,
            email=email,
            password_hash=self._hash_password(password),
            access_groups=access_groups or [],
            permissions=permissions or [],
            created_by="system",
            updated_by="system"
        )
        
        # Set default permissions based on access groups
        if "admin" in (access_groups or []):
            user.is_admin = True
            user.is_manager = True
            user.permissions = ["studio.create_projects", "studio.manage_users", "studio.manage_settings"]
        elif "manager" in (access_groups or []):
            user.is_manager = True
            user.permissions = ["studio.create_projects", "project.manage_tasks", "project.manage_assets"]
        elif "artist" in (access_groups or []):
            user.permissions = ["project.view", "project.create_tasks", "project.publish"]
        elif "client" in (access_groups or []):
            user.is_guest = True
            user.permissions = ["project.view"]
        
        self.save_user(user)
        self.logger.info(f"Created user with access: {name} ({email}) - Groups: {access_groups}")
        return user
    
    def check_user_permission(self, user: AyonUser, permission: str, project_name: str = None) -> bool:
        """Check if user has specific permission"""
        if user.is_admin:
            return True
        
        if permission in user.permissions:
            return True
        
        # Check project-specific access
        if project_name and project_name in user.project_access:
            return True
        
        return False
    
    def ensure_user_access(self, user: AyonUser, action: str, entity_type: str = None, entity_id: str = None) -> bool:
        """Ensure user has access to perform action"""
        if user.is_admin:
            return True
        
        # Check studio-level permissions
        if action in ["create_project", "manage_users", "manage_settings"]:
            return self.check_user_permission(user, "studio.create_projects")
        
        # Check project-level permissions
        if action in ["view", "create", "update", "delete"]:
            if entity_type == "project":
                return self.check_user_permission(user, "project.view")
            elif entity_type == "folder":
                return self.check_user_permission(user, "project.view")
            elif entity_type == "task":
                return self.check_user_permission(user, "project.create_tasks")
            elif entity_type == "product":
                return self.check_user_permission(user, "project.publish")
        
        return False
    
    # Ayon File Management System
    def create_workfile(self, task_id: str, folder_id: str, file_path: str, 
                       file_size: int = 0) -> AyonWorkfile:
        """Create a new workfile"""
        if not self.current_project:
            raise ValueError("No current project")
        
        workfile_id = str(uuid.uuid4())
        
        workfile = AyonWorkfile(
            id=workfile_id,
            name=Path(file_path).name,
            task_id=task_id,
            folder_id=folder_id,
            file_path=file_path,
            file_size=file_size,
            project_name=self.current_project.name,
            created_by="local_user",
            updated_by="local_user"
        )
        
        # Save workfile
        self._save_workfile(workfile)
        self._workfiles_cache[workfile_id] = workfile
        
        self.logger.info(f"Created workfile: {workfile.name} at {file_path}")
        return workfile
    
    def _save_workfile(self, workfile: AyonWorkfile):
        """Internal method to save workfile data"""
        if not self.current_project_path:
            return
        
        workfiles_dir = self.current_project_path / "workfiles"
        workfiles_dir.mkdir(exist_ok=True)
        
        workfile_file = workfiles_dir / f"{workfile.id}.json"
        
        # Convert to dict and handle datetime serialization
        data = asdict(workfile)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        
        with open(workfile_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_workfiles(self, task_id: str = None, folder_id: str = None) -> List[AyonWorkfile]:
        """Get workfiles for task or folder"""
        if not self.current_project_path:
            return []
        
        workfiles_dir = self.current_project_path / "workfiles"
        if not workfiles_dir.exists():
            return []
        
        workfiles = []
        for workfile_file in workfiles_dir.glob("*.json"):
            try:
                with open(workfile_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if 'updated_at' in data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                if 'modified_at' in data and data['modified_at']:
                    data['modified_at'] = datetime.fromisoformat(data['modified_at'])
                
                workfile = AyonWorkfile(**data)
                
                # Filter by task_id or folder_id if specified
                if task_id and workfile.task_id != task_id:
                    continue
                if folder_id and workfile.folder_id != folder_id:
                    continue
                
                workfiles.append(workfile)
                self._workfiles_cache[workfile.id] = workfile
                
            except Exception as e:
                self.logger.error(f"Failed to load workfile from {workfile_file}: {e}")
        
        return workfiles
    
    # Ayon Activity Logging System
    def log_activity(self, user_id: str, action: str, entity_type: str, entity_id: str, 
                    details: Dict[str, Any] = None) -> None:
        """Log user activity"""
        if not self.current_project_path:
            return
        
        activity = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
            "project_name": self.current_project.name if self.current_project else None
        }
        
        # Save activity log
        activities_file = self.current_project_path / "activities.json"
        activities = []
        
        if activities_file.exists():
            try:
                with open(activities_file, 'r') as f:
                    activities = json.load(f)
            except:
                activities = []
        
        activities.append(activity)
        
        # Keep only last 1000 activities
        if len(activities) > 1000:
            activities = activities[-1000:]
        
        with open(activities_file, 'w') as f:
            json.dump(activities, f, indent=4)
        
        self.logger.info(f"Logged activity: {action} on {entity_type} {entity_id} by user {user_id}")
    
    def get_activities(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent activities"""
        if not self.current_project_path:
            return []
        
        activities_file = self.current_project_path / "activities.json"
        if not activities_file.exists():
            return []
        
        try:
            with open(activities_file, 'r') as f:
                activities = json.load(f)
            return activities[-limit:] if limit else activities
        except Exception as e:
            self.logger.error(f"Failed to load activities: {e}")
            return []

# Global backend instance
_vogue_backend_instance: Optional[VogueProjectBackend] = None

def get_real_ayon_backend() -> VogueProjectBackend:
    """Get the global Vogue Project backend instance"""
    global _vogue_backend_instance
    if _vogue_backend_instance is None:
        _vogue_backend_instance = VogueProjectBackend()
    return _vogue_backend_instance
