"""
Ayon-Style Backend with Prism Local Storage

Combines Ayon's full functionality and hierarchy structure with Prism's local JSON storage.
Provides all Ayon features but saves everything locally as JSON files like Prism.
"""

import os
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

from vogue_core.logging_utils import get_logger
from vogue_core.models import BaseEntity, Project, Folder, Task, Product, Version, Representation, FileInfo

# Ayon-style enums and types
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

# Ayon-style data models
@dataclass
class AyonProject(BaseEntity):
    """Ayon-style project with full functionality"""
    code: str = ""
    library: bool = False
    config: Dict[str, Any] = field(default_factory=dict)
    folder_types: List[Dict[str, Any]] = field(default_factory=list)
    task_types: List[Dict[str, Any]] = field(default_factory=list)
    statuses: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[Dict[str, Any]] = field(default_factory=list)
    link_types: List[Dict[str, Any]] = field(default_factory=list)
    anatomy: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if not self.folder_types:
            self.folder_types = [
                {"name": "Asset", "icon": "folder", "color": "#4A9EFF"},
                {"name": "Shot", "icon": "video", "color": "#51CF66"},
                {"name": "Sequence", "icon": "film", "color": "#FFD43B"},
                {"name": "Episode", "icon": "tv", "color": "#FF6B6B"},
            ]
        if not self.task_types:
            self.task_types = [
                {"name": "Modeling", "icon": "cube", "color": "#4A9EFF"},
                {"name": "Texturing", "icon": "paint-brush", "color": "#51CF66"},
                {"name": "Rigging", "icon": "cog", "color": "#FFD43B"},
                {"name": "Animation", "icon": "play", "color": "#FF6B6B"},
                {"name": "Lighting", "icon": "lightbulb", "color": "#9C27B0"},
                {"name": "Rendering", "icon": "image", "color": "#00BCD4"},
                {"name": "Compositing", "icon": "layers", "color": "#8BC34A"},
                {"name": "Review", "icon": "eye", "color": "#FF9800"},
            ]
        if not self.statuses:
            self.statuses = [
                {"name": "Not Started", "color": "#A0A6AC", "icon": "circle"},
                {"name": "In Progress", "color": "#4A9EFF", "icon": "play-circle"},
                {"name": "Review", "color": "#FFD43B", "icon": "eye"},
                {"name": "Done", "color": "#51CF66", "icon": "check-circle"},
                {"name": "On Hold", "color": "#FF9800", "icon": "pause-circle"},
                {"name": "Cancelled", "color": "#F44336", "icon": "times-circle"},
            ]

@dataclass
class AyonFolder(BaseEntity):
    """Ayon-style folder with hierarchy support"""
    folder_type: str = "Asset"
    parent_id: Optional[str] = None
    path: str = ""
    thumbnail_id: Optional[str] = None
    active: bool = True
    has_versions: bool = False
    children: List[str] = field(default_factory=list)
    products: List[str] = field(default_factory=list)
    tasks: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        if not self.label:
            self.label = self.name

@dataclass
class AyonProduct(BaseEntity):
    """Ayon-style product (asset/shot)"""
    product_type: str = "Asset"
    folder_id: str = ""
    active: bool = True
    versions: List[str] = field(default_factory=list)
    representations: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        if not self.label:
            self.label = self.name

@dataclass
class AyonVersion(BaseEntity):
    """Ayon-style version"""
    version: int = 1
    product_id: str = ""
    task_id: Optional[str] = None
    thumbnail_id: Optional[str] = None
    representations: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        if not self.label:
            self.label = f"v{self.version:03d}"

@dataclass
class AyonRepresentation(BaseEntity):
    """Ayon-style representation"""
    version_id: str = ""
    name: str = ""
    files: List[str] = field(default_factory=list)
    active: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        if not self.label:
            self.label = self.name

@dataclass
class AyonTask(BaseEntity):
    """Ayon-style task"""
    task_type: str = "Modeling"
    folder_id: str = ""
    assignees: List[str] = field(default_factory=list)
    due_date: Optional[datetime] = None
    progress: float = 0.0
    active: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        if not self.label:
            self.label = self.name

@dataclass
class AyonUser(BaseEntity):
    """Ayon-style user"""
    email: str = ""
    password_hash: str = ""
    role: str = "Artist"
    active: bool = True
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if not self.label:
            self.label = self.name

@dataclass
class AyonWorkfile(BaseEntity):
    """Ayon-style workfile"""
    task_id: str = ""
    folder_id: str = ""
    file_path: str = ""
    file_size: int = 0
    modified_at: Optional[datetime] = None
    active: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        if not self.label:
            self.label = Path(self.file_path).name

class AyonBackend:
    """
    Ayon-style backend with Prism local storage
    
    Provides all Ayon functionality but saves everything locally as JSON files
    like Prism, maintaining the desktop-first approach.
    """
    
    def __init__(self, local_root: str = "VogueProjects"):
        self.logger = get_logger("AyonBackend")
        self.local_root = Path(local_root)
        self.local_root.mkdir(exist_ok=True)
        
        # Current project
        self.current_project: Optional[AyonProject] = None
        self.current_project_path: Optional[Path] = None
        
        # Data caches
        self._projects_cache: Dict[str, AyonProject] = {}
        self._folders_cache: Dict[str, AyonFolder] = {}
        self._products_cache: Dict[str, AyonProduct] = {}
        self._versions_cache: Dict[str, AyonVersion] = {}
        self._tasks_cache: Dict[str, AyonTask] = {}
        self._users_cache: Dict[str, AyonUser] = {}
        
        self.logger.info(f"Ayon backend initialized with local root: {self.local_root.absolute()}")
    
    # Project Management
    def create_project(self, name: str, code: str = "", library: bool = False) -> AyonProject:
        """Create a new Ayon-style project"""
        project_id = str(uuid.uuid4())
        project_path = self.local_root / name
        
        # Create project directory structure
        project_path.mkdir(exist_ok=True)
        (project_path / "Assets").mkdir(exist_ok=True)
        (project_path / "Shots").mkdir(exist_ok=True)
        (project_path / "Library").mkdir(exist_ok=True)
        (project_path / "Workfiles").mkdir(exist_ok=True)
        (project_path / "Publish").mkdir(exist_ok=True)
        
        # Create project
        project = AyonProject(
            id=project_id,
            name=name,
            code=code or name.upper(),
            library=library,
            path=str(project_path),
            created_by="local_user",
            updated_by="local_user"
        )
        
        # Save project
        self._save_project(project)
        self._projects_cache[project_id] = project
        
        self.logger.info(f"Created project: {name} at {project_path}")
        return project
    
    def load_project(self, project_name: str) -> Optional[AyonProject]:
        """Load an existing project"""
        project_path = self.local_root / project_name
        project_file = project_path / "project.json"
        
        if not project_file.exists():
            self.logger.error(f"Project file not found: {project_file}")
            return None
        
        try:
            with open(project_file, 'r') as f:
                data = json.load(f)
            
            project = AyonProject(**data)
            self._projects_cache[project.id] = project
            self.current_project = project
            self.current_project_path = project_path
            
            self.logger.info(f"Loaded project: {project_name}")
            return project
            
        except Exception as e:
            self.logger.error(f"Failed to load project {project_name}: {e}")
            return None
    
    def save_project(self, project: AyonProject) -> bool:
        """Save project to local storage"""
        try:
            self._save_project(project)
            self._projects_cache[project.id] = project
            return True
        except Exception as e:
            self.logger.error(f"Failed to save project {project.name}: {e}")
            return False
    
    def _save_project(self, project: AyonProject):
        """Internal method to save project data"""
        project_path = Path(project.path)
        project_file = project_path / "project.json"
        
        with open(project_file, 'w') as f:
            json.dump(asdict(project), f, indent=4, default=str)
    
    def get_projects(self) -> List[AyonProject]:
        """Get all available projects"""
        projects = []
        for project_dir in self.local_root.iterdir():
            if project_dir.is_dir() and (project_dir / "project.json").exists():
                project = self.load_project(project_dir.name)
                if project:
                    projects.append(project)
        return projects
    
    # Folder Management (Ayon hierarchy)
    def create_folder(self, name: str, folder_type: str, parent_id: Optional[str] = None) -> AyonFolder:
        """Create a new folder in Ayon hierarchy"""
        if not self.current_project:
            raise ValueError("No current project")
        
        folder_id = str(uuid.uuid4())
        
        # Calculate path
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
            project_id=self.current_project.id,
            created_by="local_user",
            updated_by="local_user"
        )
        
        # Update parent's children
        if parent_id:
            parent = self.get_folder(parent_id)
            if parent:
                parent.children.append(folder_id)
                self.save_folder(parent)
        
        # Save folder
        self._save_folder(folder)
        self._folders_cache[folder_id] = folder
        
        self.logger.info(f"Created folder: {name} ({folder_type}) at {path}")
        return folder
    
    def get_folder(self, folder_id: str) -> Optional[AyonFolder]:
        """Get folder by ID"""
        if folder_id in self._folders_cache:
            return self._folders_cache[folder_id]
        
        if not self.current_project:
            return None
        
        folder_file = self.current_project_path / "folders" / f"{folder_id}.json"
        if folder_file.exists():
            try:
                with open(folder_file, 'r') as f:
                    data = json.load(f)
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
        with open(folder_file, 'w') as f:
            json.dump(asdict(folder), f, indent=4, default=str)
    
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
                folders.append(AyonFolder(**data))
            except Exception as e:
                self.logger.error(f"Failed to load folder from {folder_file}: {e}")
        
        # Build hierarchy tree
        return self._build_hierarchy_tree(folders)
    
    def _build_hierarchy_tree(self, folders: List[AyonFolder]) -> List[Dict[str, Any]]:
        """Build hierarchy tree from folders"""
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
    
    # Product Management
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
            project_id=self.current_project.id,
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
        
        self.logger.info(f"Created product: {name} ({product_type})")
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
        with open(product_file, 'w') as f:
            json.dump(asdict(product), f, indent=4, default=str)
    
    # Task Management
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
            project_id=self.current_project.id,
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
        
        self.logger.info(f"Created task: {name} ({task_type})")
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
        with open(task_file, 'w') as f:
            json.dump(asdict(task), f, indent=4, default=str)
    
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
            project_id=self.current_project.id,
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
        
        self.logger.info(f"Created version: v{version:03d} for product {product_id}")
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
        with open(version_file, 'w') as f:
            json.dump(asdict(version), f, indent=4, default=str)
    
    # User Management
    def create_user(self, name: str, email: str, role: str = "Artist") -> AyonUser:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        
        user = AyonUser(
            id=user_id,
            name=name,
            email=email,
            role=role,
            created_by="local_user",
            updated_by="local_user"
        )
        
        # Save user
        self._save_user(user)
        self._users_cache[user_id] = user
        
        self.logger.info(f"Created user: {name} ({email})")
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
            json.dump(users, f, indent=4, default=str)
    
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

# Global backend instance
_ayon_backend_instance: Optional[AyonBackend] = None

def get_ayon_backend() -> AyonBackend:
    """Get the global Ayon backend instance"""
    global _ayon_backend_instance
    if _ayon_backend_instance is None:
        _ayon_backend_instance = AyonBackend()
    return _ayon_backend_instance
