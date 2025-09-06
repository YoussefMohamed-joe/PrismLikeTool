"""
Settings management for Vogue Manager

Handles global settings, user preferences, and project discovery.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .logging_utils import get_logger


class VogueSettings:
    """Manages Vogue Manager settings and configuration"""
    
    def __init__(self):
        self.logger = get_logger("Settings")
        self.config_dir = self._get_config_directory()
        self.settings_file = self.config_dir / "settings.json"
        self.recent_projects_file = self.config_dir / "recent_projects.json"
        
        # Default settings
        self.default_settings = {
            "library_roots": self._get_default_library_roots(),
            "default_fps": 24,
            "default_resolution": [1920, 1080],
            "default_departments": ["Model", "Rig", "Anim", "LookDev", "FX", "Lighting", "Comp"],
            "default_tasks": ["WIP", "Review", "Final"],
            "max_recent_projects": 10,
            "auto_scan_filesystem": True,
            "thumbnail_size": [256, 256],
            "log_level": "INFO"
        }
        
        self.settings = self._load_settings()
        self.recent_projects = self._load_recent_projects()
    
    def _get_config_directory(self) -> Path:
        """Get the configuration directory for Vogue Manager"""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', '')) / "VogueManager"
        else:  # macOS/Linux
            config_dir = Path.home() / ".config" / "vogue_manager"
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def _get_default_library_roots(self) -> List[str]:
        """Get default library root directories"""
        roots = []
        
        if os.name == 'nt':  # Windows
            # Common Windows paths
            possible_roots = [
                "D:/VogueProjects",
                "C:/VogueProjects", 
                "D:/Projects",
                "C:/Projects",
                os.path.expanduser("~/Documents/VogueProjects"),
                os.path.expanduser("~/VogueProjects")
            ]
        else:  # macOS/Linux
            # Common Unix paths
            possible_roots = [
                "/mnt/projects",
                "/home/projects",
                os.path.expanduser("~/VogueProjects"),
                os.path.expanduser("~/Projects"),
                "/opt/vogue/projects"
            ]
        
        # Only add existing directories
        for root in possible_roots:
            if os.path.exists(root) and os.path.isdir(root):
                roots.append(root)
        
        # Always add user's home directory as fallback
        home_projects = os.path.expanduser("~/VogueProjects")
        if home_projects not in roots:
            roots.append(home_projects)
        
        return roots
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        if not self.settings_file.exists():
            return self.default_settings.copy()
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            merged_settings = self.default_settings.copy()
            merged_settings.update(settings)
            return merged_settings
            
        except (json.JSONDecodeError, OSError) as e:
            self.logger.error(f"Failed to load settings: {e}")
            return self.default_settings.copy()
    
    def _save_settings(self) -> None:
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except OSError as e:
            self.logger.error(f"Failed to save settings: {e}")
    
    def _load_recent_projects(self) -> List[Dict[str, str]]:
        """Load recent projects list"""
        if not self.recent_projects_file.exists():
            return []
        
        try:
            with open(self.recent_projects_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            self.logger.error(f"Failed to load recent projects: {e}")
            return []
    
    def _save_recent_projects(self) -> None:
        """Save recent projects list"""
        try:
            with open(self.recent_projects_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_projects, f, indent=2, ensure_ascii=False)
        except OSError as e:
            self.logger.error(f"Failed to save recent projects: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value"""
        self.settings[key] = value
        self._save_settings()
    
    def get_library_roots(self) -> List[str]:
        """Get library root directories"""
        return self.settings.get("library_roots", [])
    
    def add_library_root(self, path: str) -> None:
        """Add a library root directory"""
        roots = self.get_library_roots()
        if path not in roots:
            roots.append(path)
            self.set("library_roots", roots)
    
    def remove_library_root(self, path: str) -> None:
        """Remove a library root directory"""
        roots = self.get_library_roots()
        if path in roots:
            roots.remove(path)
            self.set("library_roots", roots)
    
    def add_recent_project(self, name: str, path: str) -> None:
        """Add a project to recent projects list"""
        # Remove if already exists
        self.recent_projects = [p for p in self.recent_projects if p["path"] != path]
        
        # Add to beginning
        self.recent_projects.insert(0, {"name": name, "path": path})
        
        # Limit to max_recent_projects
        max_recent = self.get("max_recent_projects", 10)
        self.recent_projects = self.recent_projects[:max_recent]
        
        self._save_recent_projects()
    
    def get_recent_projects(self) -> List[Dict[str, str]]:
        """Get recent projects list"""
        return self.recent_projects.copy()
    
    def clear_recent_projects(self) -> None:
        """Clear recent projects list"""
        self.recent_projects = []
        self._save_recent_projects()
    
    def discover_projects(self) -> List[Dict[str, str]]:
        """Discover projects in library roots"""
        projects = []
        
        for root in self.get_library_roots():
            if not os.path.exists(root):
                continue
            
            try:
                for item in os.listdir(root):
                    item_path = os.path.join(root, item)
                    if os.path.isdir(item_path):
                        pipeline_path = os.path.join(item_path, "00_Pipeline", "pipeline.json")
                        if os.path.exists(pipeline_path):
                            projects.append({
                                "name": item,
                                "path": item_path
                            })
            except OSError as e:
                self.logger.warning(f"Failed to scan library root {root}: {e}")
        
        return projects
    
    def get_project_info(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Get project information from pipeline.json"""
        pipeline_path = os.path.join(project_path, "00_Pipeline", "pipeline.json")
        
        if not os.path.exists(pipeline_path):
            return None
        
        try:
            with open(pipeline_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                "name": data.get("name", ""),
                "path": data.get("path", project_path),
                "fps": data.get("fps", 24),
                "resolution": data.get("resolution", [1920, 1080]),
                "departments": data.get("departments", []),
                "tasks": data.get("tasks", []),
                "asset_count": len(data.get("assets", [])),
                "shot_count": len(data.get("shots", [])),
                "total_versions": sum(len(versions) for versions in data.get("versions", {}).values())
            }
        except (json.JSONDecodeError, OSError) as e:
            self.logger.error(f"Failed to read project info from {pipeline_path}: {e}")
            return None


# Global settings instance
settings = VogueSettings()
