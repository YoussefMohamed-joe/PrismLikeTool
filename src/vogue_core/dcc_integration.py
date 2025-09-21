"""
DCC Application Integration System

Provides integration with various DCC applications like Maya, Blender, Houdini, etc.
Handles workfile management, version creation, and application launching.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from .models import Version, Project
from .logging_utils import get_logger


@dataclass
class DCCApp:
    """Represents a DCC application"""
    name: str
    display_name: str
    executable_path: str
    file_extensions: List[str]
    icon_path: Optional[str] = None
    launch_args: List[str] = None
    workfile_template: str = ""
    
    def __post_init__(self):
        if self.launch_args is None:
            self.launch_args = []
        if not self.icon_path:
            self.icon_path = self._get_default_icon()
    
    def _get_default_icon(self) -> str:
        """Get default icon path for the DCC app"""
        icon_map = {
            "maya": "🎨",
            "blender": "🎭", 
            "houdini": "🌀",
            "nuke": "🎬",
            "3dsmax": "📐",
            "cinema4d": "🎪"
        }
        return icon_map.get(self.name.lower(), "📁")


class DCCManager:
    """Manages DCC application integrations"""
    
    def __init__(self):
        self.logger = get_logger("DCCManager")
        self.apps: Dict[str, DCCApp] = {}
        self._detect_applications()
    
    def _detect_applications(self):
        """Auto-detect installed DCC applications"""
        self.logger.info("Detecting DCC applications...")
        
        # Common DCC application paths
        dcc_paths = {
            "maya": [
                r"C:\Program Files\Autodesk\Maya*\bin\maya.exe",
                r"C:\Program Files\Autodesk\Maya*\bin\maya.bat",
                "/Applications/Autodesk/maya*/Maya.app/Contents/MacOS/Maya",
                "/usr/autodesk/maya*/bin/maya"
            ],
            "blender": [
                r"C:\Program Files\Blender Foundation\Blender*\blender.exe",
                r"C:\Program Files\Blender Foundation\Blender*\blender-launcher.exe",
                "/Applications/Blender.app/Contents/MacOS/Blender",
                "/usr/bin/blender",
                "/usr/local/bin/blender"
            ],
            "houdini": [
                r"C:\Program Files\Side Effects Software\Houdini*\bin\houdini.exe",
                r"C:\Program Files\Side Effects Software\Houdini*\bin\houdini.bat",
                "/Applications/Houdini*/Houdini.app/Contents/MacOS/Houdini",
                "/opt/hfs*/bin/houdini"
            ],
            "nuke": [
                r"C:\Program Files\Nuke*\Nuke*.exe",
                r"C:\Program Files\Nuke*\Nuke*.bat",
                "/Applications/Nuke*/Nuke*.app/Contents/MacOS/Nuke*",
                "/usr/local/Nuke*/Nuke*"
            ]
        }
        
        for app_name, paths in dcc_paths.items():
            executable = self._find_executable(paths)
            if executable:
                self._register_app(app_name, executable)
    
    def _find_executable(self, paths: List[str]) -> Optional[str]:
        """Find executable from list of possible paths"""
        import glob
        
        for path_pattern in paths:
            matches = glob.glob(path_pattern)
            for match in matches:
                if os.path.isfile(match) and os.access(match, os.X_OK):
                    return match
        return None
    
    def _register_app(self, name: str, executable_path: str):
        """Register a DCC application"""
        file_extensions = {
            "maya": [".ma", ".mb"],
            "blender": [".blend"],
            "houdini": [".hip", ".hipnc"],
            "nuke": [".nk"],
            "3dsmax": [".max"],
            "cinema4d": [".c4d"]
        }
        
        display_names = {
            "maya": "Autodesk Maya",
            "blender": "Blender",
            "houdini": "SideFX Houdini", 
            "nuke": "Foundry Nuke",
            "3dsmax": "3ds Max",
            "cinema4d": "Cinema 4D"
        }
        
        app = DCCApp(
            name=name,
            display_name=display_names.get(name, name.title()),
            executable_path=executable_path,
            file_extensions=file_extensions.get(name, []),
            workfile_template=self._get_workfile_template(name)
        )
        
        self.apps[name] = app
        self.logger.info(f"Registered DCC app: {app.display_name} at {executable_path}")
    
    def _get_workfile_template(self, app_name: str) -> str:
        """Get workfile naming template for DCC app"""
        templates = {
            "maya": "{entity_name}_{task_name}_v{version:03d}.ma",
            "blender": "{entity_name}_{task_name}_v{version:03d}.blend",
            "houdini": "{entity_name}_{task_name}_v{version:03d}.hip",
            "nuke": "{entity_name}_{task_name}_v{version:03d}.nk"
        }
        return templates.get(app_name, "{entity_name}_{task_name}_v{version:03d}")
    
    def get_app(self, name: str) -> Optional[DCCApp]:
        """Get DCC app by name"""
        return self.apps.get(name)
    
    def list_apps(self) -> List[DCCApp]:
        """Get list of all registered DCC apps"""
        return list(self.apps.values())
    
    def launch_app(self, app_name: str, workfile_path: Optional[str] = None, 
                   project_path: Optional[str] = None) -> bool:
        """Launch DCC application with optional workfile"""
        app = self.get_app(app_name)
        if not app:
            self.logger.error(f"DCC app '{app_name}' not found")
            return False
        
        try:
            args = [app.executable_path] + app.launch_args.copy()
            
            if workfile_path and os.path.exists(workfile_path):
                args.append(workfile_path)
            
            if project_path:
                # Set project directory for the DCC app
                if app_name == "maya":
                    args.extend(["-proj", project_path])
                elif app_name == "blender":
                    args.extend(["--", workfile_path] if workfile_path else [])
            
            self.logger.info(f"Launching {app.display_name}: {' '.join(args)}")
            subprocess.Popen(args, cwd=project_path or os.path.dirname(app.executable_path))
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to launch {app.display_name}: {e}")
            return False
    
    def create_workfile_path(self, app_name: str, entity_name: str, 
                           task_name: str, version: int, project_path: str) -> str:
        """Create workfile path for DCC app"""
        app = self.get_app(app_name)
        if not app:
            raise ValueError(f"DCC app '{app_name}' not found")
        
        # Create workfile directory structure
        workfile_dir = os.path.join(
            project_path, 
            "workfiles", 
            entity_name, 
            task_name
        )
        os.makedirs(workfile_dir, exist_ok=True)
        
        # Generate filename using template
        filename = app.workfile_template.format(
            entity_name=entity_name,
            task_name=task_name,
            version=version
        )
        
        return os.path.join(workfile_dir, filename)
    
    def generate_thumbnail(self, file_path: str, output_path: str, 
                          size: Tuple[int, int] = (256, 256)) -> bool:
        """Generate thumbnail for DCC file"""
        if not os.path.exists(file_path):
            return False
        
        try:
            # Try to use DCC-specific thumbnail generation
            ext = Path(file_path).suffix.lower()
            if ext in ['.ma', '.mb']:
                # Use Maya bridge for Maya files
                try:
                    from ..vogue_maya.maya_bridge import maya_bridge
                    if maya_bridge.is_available():
                        return maya_bridge.generate_thumbnail(file_path, output_path, size)
                except ImportError:
                    pass
            
            # Fallback to placeholder thumbnail
            self._create_placeholder_thumbnail(file_path, output_path, size)
            return True
        except Exception as e:
            self.logger.error(f"Failed to generate thumbnail for {file_path}: {e}")
            return False
    
    def _create_placeholder_thumbnail(self, file_path: str, output_path: str, 
                                    size: Tuple[int, int]):
        """Create a placeholder thumbnail"""
        from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor
        from PyQt6.QtCore import Qt
        
        # Create pixmap
        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(QColor(60, 60, 60))  # Dark background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get file extension for icon
        ext = Path(file_path).suffix.lower()
        icon_map = {
            ".ma": "🎨", ".mb": "🎨",  # Maya
            ".blend": "🎭",  # Blender
            ".hip": "🌀", ".hipnc": "🌀",  # Houdini
            ".nk": "🎬",  # Nuke
            ".max": "📐",  # 3ds Max
            ".c4d": "🎪"  # Cinema 4D
        }
        
        icon = icon_map.get(ext, "📁")
        
        # Draw icon
        font = QFont()
        font.setPointSize(48)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(0, 0, size[0], size[1], Qt.AlignmentFlag.AlignCenter, icon)
        
        # Draw filename
        font.setPointSize(12)
        painter.setFont(font)
        filename = Path(file_path).stem
        if len(filename) > 15:
            filename = filename[:12] + "..."
        painter.drawText(0, size[1] - 20, size[0], 20, Qt.AlignmentFlag.AlignCenter, filename)
        
        painter.end()
        
        # Save thumbnail
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pixmap.save(output_path, "PNG")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a DCC file"""
        if not os.path.exists(file_path):
            return {}
        
        stat = os.stat(file_path)
        ext = Path(file_path).suffix.lower()
        
        # Determine DCC app from extension
        app_map = {
            ".ma": "maya", ".mb": "maya",
            ".blend": "blender",
            ".hip": "houdini", ".hipnc": "houdini",
            ".nk": "nuke",
            ".max": "3dsmax",
            ".c4d": "cinema4d"
        }
        
        return {
            "path": file_path,
            "name": Path(file_path).name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "dcc_app": app_map.get(ext, "unknown"),
            "extension": ext
        }


# Global DCC manager instance
dcc_manager = DCCManager()
