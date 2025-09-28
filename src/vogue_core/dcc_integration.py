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
import tempfile

from .models import Version, Project
from .logging_utils import get_logger
from .thumbnail_generator import ThumbnailGenerator, ThumbnailConfig


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
    
    def __init__(self, project_path: str = None):
        self.logger = get_logger("DCCManager")
        self.apps: Dict[str, DCCApp] = {}
        self.last_error: str = ""
        self.project_path = project_path
        self.thumbnail_generator = None
        
        # Initialize thumbnail generator if project path is provided
        if project_path:
            self.thumbnail_generator = ThumbnailGenerator(project_path)
        
        # First load user-defined paths if present, then auto-detect missing
        self._load_from_settings()
        self._detect_applications()

    def _load_from_settings(self):
        """Load DCC executable paths from settings.json if available."""
        try:
            settings_paths = [
                Path.cwd() / "settings.json",
                Path("settings.json"),
            ]
            settings = None
            for p in settings_paths:
                if p.exists():
                    with open(p, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                    break
            if not settings:
                return
            dcc = settings.get('dcc_apps', {}) if isinstance(settings, dict) else {}
            for name, exe in dcc.items():
                if isinstance(exe, str) and exe and os.path.isfile(exe):
                    self._register_app(name, exe)
                else:
                    if isinstance(exe, str) and exe:
                        self.last_error = f"Configured path for {name} is invalid: {exe}"
        except Exception as e:
            self.logger.warning(f"Failed to load DCC paths from settings: {e}")
            self.last_error = str(e)
    
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

    def initialize_workfile(self, app_name: str, dest_path: str, preferred_extension: Optional[str] = None) -> bool:
        """Create a valid default workfile for the DCC so it opens externally.

        Returns True on success. Uses preset files from 'dcc new apps' folder when available.
        """
        try:
            app = self.get_app(app_name)
            dest_path = str(Path(dest_path))
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # First, try to use preset files from 'dcc new apps' folder
            preset_path = self._get_preset_path(app_name, preferred_extension)
            if preset_path and os.path.exists(preset_path):
                try:
                    shutil.copy2(preset_path, dest_path)
                    self.logger.info(f"Created workfile from preset: {preset_path} -> {dest_path}")
                    return True
                except Exception as e:
                    self.logger.warning(f"Failed to copy preset file {preset_path}: {e}")
                    # Fall through to original initialization method

            # Maya: prefer batch save to ensure valid defaults; fallback to minimal ASCII
            if app_name == "maya":
                # Ensure ASCII extension for better portability
                picked_ext = preferred_extension.lower() if preferred_extension in (".ma", ".mb") else None
                if Path(dest_path).suffix.lower() not in [".ma", ".mb"]:
                    dest_path = str(Path(dest_path).with_suffix(picked_ext or ".ma"))
                if app and os.path.isfile(app.executable_path):
                    try:
                        # Use maya in batch to create a new scene and save as ASCII
                        maya_dest = dest_path.replace("\\", "/")
                        # Choose mayaAscii or mayaBinary based on extension
                        maya_type = "mayaAscii" if maya_dest.lower().endswith(".ma") else "mayaBinary"
                        cmd = [app.executable_path, "-batch", "-command",
                               f'file -f -new; file -rename "{maya_dest}"; file -save -type "{maya_type}";']
                        self.logger.info(f"Initializing Maya workfile via batch: {' '.join(cmd)}")
                        creationflags = 0
                        startupinfo = None
                        # Hide console window on Windows
                        if os.name == 'nt':
                            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        subprocess.check_call(cmd, creationflags=creationflags, startupinfo=startupinfo)
                        return os.path.isfile(dest_path)
                    except Exception as e:
                        self.logger.warning(f"Maya batch initialization failed, falling back to template: {e}")
                        self.last_error = str(e)
                # Fallback: minimal .ma header (opens as empty scene in Maya)
                try:
                    if dest_path.lower().endswith('.ma'):
                        content = (
                            "//Maya ASCII 2020 scene\n"
                            "requires maya \"2020\";\n"
                            "currentUnit -l centimeter -a degree -t film;\n"
                            "fileInfo \"application\" \"maya\";\n"
                        )
                        with open(dest_path, "w", encoding="utf-8") as f:
                            f.write(content)
                    else:
                        # Minimal mayaBinary is non-trivial; create ASCII and rename if .mb requested
                        ascii_tmp = dest_path[:-3] + 'ma'
                        content = (
                            "//Maya ASCII 2020 scene\n"
                            "requires maya \"2020\";\n"
                            "currentUnit -l centimeter -a degree -t film;\n"
                            "fileInfo \"application\" \"maya\";\n"
                        )
                        with open(ascii_tmp, "w", encoding="utf-8") as f:
                            f.write(content)
                        try:
                            os.replace(ascii_tmp, dest_path)
                        except Exception:
                            shutil.copy2(ascii_tmp, dest_path)
                            try:
                                os.remove(ascii_tmp)
                            except Exception:
                                pass
                    return True
                except Exception as e:
                    self.last_error = str(e)
                    return False

            # Blender: use headless save
            if app_name == "blender":
                if Path(dest_path).suffix.lower() != ".blend":
                    dest_path = str(Path(dest_path).with_suffix(".blend"))
                if app and os.path.isfile(app.executable_path):
                    blender_dest = dest_path.replace("\\", "/")
                    script = (
                        "import bpy\n"
                        "bpy.ops.wm.read_factory_settings(use_empty=True)\n"
                        f"bpy.ops.wm.save_as_mainfile(filepath=r'{blender_dest}', copy=False)\n"
                    )
                    with tempfile.NamedTemporaryFile("w", suffix="_init_blender.py", delete=False) as tf:
                        tf.write(script)
                        tf_path = tf.name
                    try:
                        cmd = [app.executable_path, "-b", "-noaudio", "-y", "-P", tf_path]
                        self.logger.info(f"Initializing Blender workfile: {' '.join(cmd)}")
                        creationflags = 0
                        startupinfo = None
                        if os.name == 'nt':
                            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        subprocess.check_call(cmd, creationflags=creationflags, startupinfo=startupinfo)
                        return os.path.isfile(dest_path)
                    except Exception as e:
                        self.logger.error(f"Failed to initialize Blender file: {e}")
                        self.last_error = str(e)
                        return False
                    finally:
                        try:
                            os.unlink(tf_path)
                        except Exception:
                            pass
                return False

            # Nuke: write minimal .nk
            if app_name == "nuke":
                if Path(dest_path).suffix.lower() != ".nk":
                    dest_path = str(Path(dest_path).with_suffix(".nk"))
                try:
                    # Minimal Nuke script that opens as empty project
                    content = (
                        "Root {\n"
                        " version 13.2\n"
                        " name \"Untitled\"\n"
                        "}\n"
                    )
                    with open(dest_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to write Nuke file: {e}")
                    self.last_error = str(e)
                    return False

            # Houdini and others: attempt to create empty file is unsafe; require app-side creation
            # Return False to indicate the file could not be initialized here
            return False
        except Exception as e:
            self.logger.error(f"initialize_workfile error for {app_name}: {e}")
            self.last_error = str(e)
            return False
    
    def launch_app(self, app_name: str, workfile_path: Optional[str] = None, 
                   project_path: Optional[str] = None) -> bool:
        """Launch DCC application with optional workfile"""
        app = self.get_app(app_name) if app_name else None
        if not app:
            # If app missing but we have a file path, try OS default app as a graceful fallback
            if workfile_path and os.path.exists(workfile_path):
                try:
                    if os.name == 'nt':
                        os.startfile(workfile_path)  # type: ignore[attr-defined]
                        return True
                    else:
                        import subprocess as _sp
                        _sp.Popen(['xdg-open', workfile_path])
                        return True
                except Exception as e:
                    msg = f"DCC app '{app_name}' not found and OS open failed: {e}"
                    self.logger.error(msg)
                    self.last_error = msg
                    return False
            msg = f"DCC app '{app_name}' not found"
            self.logger.error(msg)
            self.last_error = msg
            return False
        
        try:
            args = [app.executable_path] + app.launch_args.copy()
            
            if workfile_path and os.path.exists(workfile_path):
                # App-specific flags to open a file directly
                if app_name == "maya":
                    # Maya can open file by passing path
                    args.append(workfile_path)
                elif app_name == "blender":
                    # Blender opens file when path is last arg
                    args.append(workfile_path)
                elif app_name == "nuke":
                    # Nuke opens script when path is first arg after exe
                    args.append(workfile_path)
                elif app_name == "houdini":
                    # Houdini opens hip by path
                    args.append(workfile_path)
            
            if project_path:
                # Set project directory for the DCC app
                if app_name == "maya":
                    args.extend(["-proj", project_path])
            
            self.logger.info(f"Launching {app.display_name}: {' '.join(args)}")
            # Ensure the executable exists
            if not os.path.isfile(app.executable_path):
                msg = f"Executable not found: {app.executable_path}"
                self.logger.error(msg)
                self.last_error = msg
                return False
            # Ensure workfile exists if provided
            if workfile_path and not os.path.exists(workfile_path):
                msg = f"Workfile not found: {workfile_path}"
                self.logger.error(msg)
                self.last_error = msg
                return False
            subprocess.Popen(args, cwd=project_path or os.path.dirname(app.executable_path))
            return True
            
        except Exception as e:
            msg = f"Failed to launch {app.display_name}: {e}"
            self.logger.error(msg)
            self.last_error = msg
            return False

    def get_last_error(self) -> str:
        return self.last_error
    
    def _get_preset_path(self, app_name: str, preferred_extension: Optional[str] = None) -> Optional[str]:
        """Get the path to the preset file for a given DCC app.
        
        Args:
            app_name: Name of the DCC application
            preferred_extension: Preferred file extension (e.g., '.ma', '.mb')
            
        Returns:
            Path to preset file if found, None otherwise
        """
        try:
            # Get the path to the 'dcc new apps' folder
            current_file = Path(__file__)
            preset_dir = current_file.parent.parent / "vogue_app" / "dcc new apps"
            
            if not preset_dir.exists():
                return None
            
            # Map DCC app names to their preset file names
            preset_mapping = {
                "maya": ["mayaAscii.ma", "mayaBinary.mb"],
                "blender": ["blender.blend"],
                "houdini": ["houdini.hip"],
                "nuke": ["Nuke.nk"]
            }
            
            app_name_lower = app_name.lower()
            if app_name_lower not in preset_mapping:
                return None
            
            # If preferred extension is specified, try to match it
            if preferred_extension:
                preferred_ext = preferred_extension.lower()
                for preset_file in preset_mapping[app_name_lower]:
                    if preset_file.lower().endswith(preferred_ext):
                        preset_path = preset_dir / preset_file
                        if preset_path.exists():
                            return str(preset_path)
            
            # Fall back to first available preset file for this app
            for preset_file in preset_mapping[app_name_lower]:
                preset_path = preset_dir / preset_file
                if preset_path.exists():
                    return str(preset_path)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error getting preset path for {app_name}: {e}")
            return None
    
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
            elif ext in ['.blend']:
                try:
                    from ..vogue_app.integrations.blender_bridge import blender_bridge  # type: ignore
                    if getattr(blender_bridge, 'is_available', lambda: False)():
                        return blender_bridge.generate_thumbnail(file_path, output_path, size)
                except Exception:
                    pass
            elif ext in ['.hip', '.hipnc']:
                try:
                    from ..vogue_app.integrations.houdini_bridge import houdini_bridge  # type: ignore
                    if getattr(houdini_bridge, 'is_available', lambda: False)():
                        return houdini_bridge.generate_thumbnail(file_path, output_path, size)
                except Exception:
                    pass
            elif ext in ['.nk']:
                try:
                    from ..vogue_app.integrations.nuke_bridge import nuke_bridge  # type: ignore
                    if getattr(nuke_bridge, 'is_available', lambda: False)():
                        return nuke_bridge.generate_thumbnail(file_path, output_path, size)
                except Exception:
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
    
    def generate_launch_screenshot(self, app_name: str) -> Optional[str]:
        """Generate screenshot when launching DCC application"""
        if not self.thumbnail_generator:
            self.logger.warning("Thumbnail generator not initialized")
            return None
        
        return self.thumbnail_generator.generate_launch_screenshot(app_name)
    
    def generate_enhanced_thumbnail(self, file_path: str, entity_type: str = "asset", 
                                  entity_name: str = "", task_name: str = "") -> Optional[str]:
        """Generate enhanced thumbnail for DCC file with viewport capture"""
        if not self.thumbnail_generator:
            self.logger.warning("Thumbnail generator not initialized")
            return None
        
        return self.thumbnail_generator.generate_dcc_thumbnail(file_path, entity_type, entity_name, task_name)
    
    def set_project_path(self, project_path: str):
        """Set project path and initialize thumbnail generator"""
        self.project_path = project_path
        if self.thumbnail_generator:
            self.thumbnail_generator.stop_watching()
        self.thumbnail_generator = ThumbnailGenerator(project_path)
        self.logger.info(f"Thumbnail generator initialized for project: {project_path}")
    
    def stop_thumbnail_generation(self):
        """Stop thumbnail generation and file watching"""
        if self.thumbnail_generator:
            self.thumbnail_generator.stop_watching()
            self.logger.info("Thumbnail generation stopped")


# Global DCC manager instance
dcc_manager = DCCManager()
