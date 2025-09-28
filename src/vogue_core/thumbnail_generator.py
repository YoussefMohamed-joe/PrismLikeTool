"""
Enhanced Thumbnail Generation System

Provides comprehensive thumbnail generation for DCC applications with viewport capture,
automatic generation on app launch and file save, and integration with Prism-style folder structure.
"""

import os
import sys
import time
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import threading

# Optional file watching - gracefully handle if watchdog is not available
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Create dummy classes for when watchdog is not available
    class Observer:
        def __init__(self, *args, **kwargs): pass
        def schedule(self, *args, **kwargs): pass
        def start(self, *args, **kwargs): pass
        def stop(self, *args, **kwargs): pass
        def join(self, *args, **kwargs): pass
    
    class FileSystemEventHandler:
        def __init__(self, *args, **kwargs): pass
        def on_modified(self, *args, **kwargs): pass
        def on_created(self, *args, **kwargs): pass

# Try to import Qt for screenshot functionality
try:
    from PyQt6.QtWidgets import QApplication, QWidget, QScreen
    from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen
    from PyQt6.QtCore import Qt, QRect, QSize
    QT_AVAILABLE = True
    QT_VERSION = "PyQt6"
except ImportError:
    try:
        from PySide2.QtWidgets import QApplication, QWidget, QScreen
        from PySide2.QtGui import QPixmap, QPainter, QColor, QPen
        from PySide2.QtCore import Qt, QRect, QSize
        QT_AVAILABLE = True
        QT_VERSION = "PySide2"
    except ImportError:
        QT_AVAILABLE = False
        QT_VERSION = None

from .logging_utils import get_logger


@dataclass
class ThumbnailConfig:
    """Configuration for thumbnail generation"""
    size: Tuple[int, int] = (256, 256)
    quality: int = 85
    format: str = "PNG"
    auto_generate: bool = True
    watch_files: bool = True
    prism_integration: bool = True
    thumbnail_folder: str = "thumbnails"


class ThumbnailGenerator:
    """Enhanced thumbnail generation system with DCC viewport capture"""
    
    def __init__(self, project_path: str, config: Optional[ThumbnailConfig] = None):
        self.project_path = Path(project_path)
        self.config = config or ThumbnailConfig()
        self.logger = get_logger("ThumbnailGenerator")
        self.observer = None
        self.file_watcher = None
        
        # Create thumbnail directories
        self._setup_thumbnail_directories()
        
        # Start file watching if enabled
        if self.config.watch_files:
            self._start_file_watcher()
    
    def _setup_thumbnail_directories(self):
        """Create thumbnail directory structure following Prism conventions"""
        thumb_dirs = [
            self.project_path / self.config.thumbnail_folder,
            self.project_path / self.config.thumbnail_folder / "versions",
            self.project_path / self.config.thumbnail_folder / "assets",
            self.project_path / self.config.thumbnail_folder / "shots",
            self.project_path / self.config.thumbnail_folder / "launch_screenshots",
            self.project_path / "00_Pipeline" / "Assetinfo",  # Prism-style entity previews
            self.project_path / "00_Pipeline" / "Shotinfo",   # Prism-style shot previews
        ]
        
        for thumb_dir in thumb_dirs:
            thumb_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created thumbnail directory: {thumb_dir}")
    
    def _start_file_watcher(self):
        """Start watching for file changes to auto-generate thumbnails"""
        if not self.config.watch_files or not WATCHDOG_AVAILABLE:
            if not WATCHDOG_AVAILABLE:
                self.logger.info("File watching disabled - watchdog module not available")
            return
            
        try:
            self.file_watcher = FileWatcher(self)
            self.observer = Observer()
            
            # Watch workfile directories
            watch_dirs = [
                self.project_path / "06_Scenes",
                self.project_path / "01_Assets",
                self.project_path / "02_Shots"
            ]
            
            for watch_dir in watch_dirs:
                if watch_dir.exists():
                    self.observer.schedule(self.file_watcher, str(watch_dir), recursive=True)
                    self.logger.debug(f"Watching directory: {watch_dir}")
            
            self.observer.start()
            self.logger.info("File watcher started for automatic thumbnail generation")
            
        except Exception as e:
            self.logger.warning(f"Failed to start file watcher: {e}")
    
    def stop_watching(self):
        """Stop file watching"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.logger.info("File watcher stopped")
    
    def generate_launch_screenshot(self, app_name: str) -> Optional[str]:
        """Generate screenshot when launching DCC application"""
        if not QT_AVAILABLE:
            self.logger.warning("Qt not available for screenshot generation")
            return None
        
        try:
            # Wait a moment for the app to fully load
            time.sleep(2)
            
            # Take screenshot of the entire screen
            screenshot = self._capture_screen()
            if not screenshot:
                return None
            
            # Save launch screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{app_name}_launch_{timestamp}.png"
            launch_dir = self.project_path / self.config.thumbnail_folder / "launch_screenshots"
            launch_dir.mkdir(parents=True, exist_ok=True)
            
            screenshot_path = launch_dir / filename
            screenshot.save(str(screenshot_path))
            
            self.logger.info(f"Generated launch screenshot: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate launch screenshot: {e}")
            return None
    
    def generate_dcc_thumbnail(self, file_path: str, entity_type: str = "asset", 
                             entity_name: str = "", task_name: str = "") -> Optional[str]:
        """Generate thumbnail for DCC file with viewport capture"""
        if not os.path.exists(file_path):
            self.logger.warning(f"File not found: {file_path}")
            return None
        
        try:
            # Determine DCC app from file extension
            dcc_app = self._get_dcc_app_from_file(file_path)
            if not dcc_app:
                self.logger.warning(f"Unknown DCC app for file: {file_path}")
                return None
            
            # Generate thumbnail using DCC-specific method
            thumbnail_path = self._generate_dcc_viewport_thumbnail(file_path, dcc_app, entity_type, entity_name, task_name)
            
            if thumbnail_path and os.path.exists(thumbnail_path):
                self.logger.info(f"Generated DCC thumbnail: {thumbnail_path}")
                return thumbnail_path
            else:
                # Fallback to generic thumbnail
                return self._generate_generic_thumbnail(file_path, entity_type, entity_name)
                
        except Exception as e:
            self.logger.error(f"Failed to generate DCC thumbnail: {e}")
            return self._generate_generic_thumbnail(file_path, entity_type, entity_name)
    
    def _get_dcc_app_from_file(self, file_path: str) -> Optional[str]:
        """Determine DCC application from file extension"""
        ext = Path(file_path).suffix.lower()
        ext_map = {
            '.ma': 'maya', '.mb': 'maya',
            '.blend': 'blender',
            '.hip': 'houdini', '.hipnc': 'houdini',
            '.nk': 'nuke',
            '.max': '3dsmax',
            '.c4d': 'cinema4d',
            '.psd': 'photoshop'
        }
        return ext_map.get(ext)
    
    def _generate_dcc_viewport_thumbnail(self, file_path: str, dcc_app: str, 
                                       entity_type: str, entity_name: str, task_name: str) -> Optional[str]:
        """Generate thumbnail by capturing DCC viewport"""
        try:
            # Create thumbnail path
            thumbnail_path = self._get_thumbnail_path(file_path, entity_type, entity_name, task_name)
            
            # Use DCC-specific thumbnail generation
            if dcc_app == "maya":
                return self._generate_maya_thumbnail(file_path, thumbnail_path)
            elif dcc_app == "blender":
                return self._generate_blender_thumbnail(file_path, thumbnail_path)
            elif dcc_app == "houdini":
                return self._generate_houdini_thumbnail(file_path, thumbnail_path)
            elif dcc_app == "nuke":
                return self._generate_nuke_thumbnail(file_path, thumbnail_path)
            else:
                # Generic DCC thumbnail generation
                return self._generate_generic_dcc_thumbnail(file_path, thumbnail_path, dcc_app)
                
        except Exception as e:
            self.logger.error(f"Failed to generate DCC viewport thumbnail: {e}")
            return None
    
    def _generate_maya_thumbnail(self, file_path: str, thumbnail_path: str) -> Optional[str]:
        """Generate Maya viewport thumbnail"""
        try:
            maya_script = f'''
import maya.cmds as cmds
import maya.mel as mel
import os
import sys

try:
    # Open the file
    if os.path.exists('{file_path}'):
        cmds.file('{file_path}', open=True, force=True)
        
        # Set up viewport
        cmds.currentUnit(time='film')
        
        # Frame all objects
        cmds.viewFit()
        
        # Set up camera for thumbnail
        if not cmds.ls('thumbnail_cam'):
            cmds.camera(name='thumbnail_cam')
        
        cmds.lookThru('thumbnail_cam')
        cmds.viewFit()
        
        # Set render settings
        cmds.setAttr('defaultResolution.width', {self.config.size[0]})
        cmds.setAttr('defaultResolution.height', {self.config.size[1]})
        cmds.setAttr('defaultResolution.pixelAspect', 1.0)
        
        # Render thumbnail
        output_dir = os.path.dirname('{thumbnail_path}')
        os.makedirs(output_dir, exist_ok=True)
        
        # Use Maya's playblast for thumbnail
        _pb_path = cmds.playblast(
            format='image',
            filename='{thumbnail_path}',
            sequenceTime=False,
            clearCache=True,
            viewer=False,
            showOrnaments=False,
            frame=[1],
            width={self.config.size[0]},
            height={self.config.size[1]},
            percent=100,
            quality={self.config.quality},
            compression='png',
            forceOverwrite=True,
            completeFilename=True
        )
        
        print("SUCCESS: Thumbnail generated")
        
except Exception as e:
    print(f"ERROR: {{str(e)}}")
    sys.exit(1)
'''
            
            # Find Maya Python executable
            maya_python = self._find_maya_python()
            if not maya_python:
                return None
            
            result = subprocess.run(
                [maya_python, "-c", maya_script],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and "SUCCESS" in result.stdout:
                return thumbnail_path if os.path.exists(thumbnail_path) else None
            
        except Exception as e:
            self.logger.error(f"Maya thumbnail generation failed: {e}")
        
        return None
    
    def _generate_blender_thumbnail(self, file_path: str, thumbnail_path: str) -> Optional[str]:
        """Generate Blender viewport thumbnail"""
        try:
            blender_script = f'''
import bpy
import os
import sys

try:
    # Clear existing scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Open the file
    if os.path.exists('{file_path}'):
        bpy.ops.wm.open_mainfile(filepath='{file_path}')
        
        # Set up viewport
        bpy.context.scene.frame_set(1)
        
        # Set render settings
        bpy.context.scene.render.resolution_x = {self.config.size[0]}
        bpy.context.scene.render.resolution_y = {self.config.size[1]}
        bpy.context.scene.render.resolution_percentage = 100
        
        # Frame all objects
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.view3d.view_selected()
        
        # Render thumbnail
        output_dir = os.path.dirname('{thumbnail_path}')
        os.makedirs(output_dir, exist_ok=True)
        
        bpy.context.scene.render.filepath = '{thumbnail_path}'
        bpy.ops.render.render(write_still=True)
        
        print("SUCCESS: Thumbnail generated")
        
except Exception as e:
    print(f"ERROR: {{str(e)}}")
    sys.exit(1)
'''
            
            # Find Blender executable
            blender_exe = self._find_blender_executable()
            if not blender_exe:
                return None
            
            result = subprocess.run(
                [blender_exe, "--background", "--python-expr", blender_script],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and "SUCCESS" in result.stdout:
                return thumbnail_path if os.path.exists(thumbnail_path) else None
            
        except Exception as e:
            self.logger.error(f"Blender thumbnail generation failed: {e}")
        
        return None
    
    def _generate_houdini_thumbnail(self, file_path: str, thumbnail_path: str) -> Optional[str]:
        """Generate Houdini viewport thumbnail"""
        try:
            houdini_script = f'''
import hou
import os
import sys

try:
    # Open the file
    if os.path.exists('{file_path}'):
        hou.hipFile.load('{file_path}')
        
        # Set up viewport
        desktop = hou.ui.desktop()
        scene_viewer = desktop.paneTabOfType(hou.paneTabType.SceneViewer)
        if scene_viewer:
            scene_viewer.enterViewState(hou.viewerStateType.Fit)
        
        # Set render settings
        output_dir = os.path.dirname('{thumbnail_path}')
        os.makedirs(output_dir, exist_ok=True)
        
        # Render thumbnail using viewport
        scene_viewer.saveImageToFile('{thumbnail_path}', {self.config.size[0]}, {self.config.size[1]})
        
        print("SUCCESS: Thumbnail generated")
        
except Exception as e:
    print(f"ERROR: {{str(e)}}")
    sys.exit(1)
'''
            
            # Find Houdini executable
            houdini_exe = self._find_houdini_executable()
            if not houdini_exe:
                return None
            
            result = subprocess.run(
                [houdini_exe, "-c", houdini_script],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and "SUCCESS" in result.stdout:
                return thumbnail_path if os.path.exists(thumbnail_path) else None
            
        except Exception as e:
            self.logger.error(f"Houdini thumbnail generation failed: {e}")
        
        return None
    
    def _generate_nuke_thumbnail(self, file_path: str, thumbnail_path: str) -> Optional[str]:
        """Generate Nuke viewport thumbnail"""
        try:
            nuke_script = f'''
import nuke
import os
import sys

try:
    # Open the file
    if os.path.exists('{file_path}'):
        nuke.scriptOpen('{file_path}')
        
        # Set up viewport
        nuke.zoom(1, [0.5, 0.5])
        
        # Set render settings
        output_dir = os.path.dirname('{thumbnail_path}')
        os.makedirs(output_dir, exist_ok=True)
        
        # Render thumbnail
        nuke.render(nuke.thisNode(), 1, 1, 1, {self.config.size[0]}, {self.config.size[1]}, '{thumbnail_path}')
        
        print("SUCCESS: Thumbnail generated")
        
except Exception as e:
    print(f"ERROR: {{str(e)}}")
    sys.exit(1)
'''
            
            # Find Nuke executable
            nuke_exe = self._find_nuke_executable()
            if not nuke_exe:
                return None
            
            result = subprocess.run(
                [nuke_exe, "-t", "-c", nuke_script],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and "SUCCESS" in result.stdout:
                return thumbnail_path if os.path.exists(thumbnail_path) else None
            
        except Exception as e:
            self.logger.error(f"Nuke thumbnail generation failed: {e}")
        
        return None
    
    def _generate_generic_dcc_thumbnail(self, file_path: str, thumbnail_path: str, dcc_app: str) -> Optional[str]:
        """Generate generic thumbnail for unsupported DCC apps"""
        try:
            # Create a placeholder thumbnail with DCC app info
            if QT_AVAILABLE:
                pixmap = self._create_placeholder_thumbnail(dcc_app, file_path)
                if pixmap:
                    pixmap.save(thumbnail_path)
                    return thumbnail_path
        except Exception as e:
            self.logger.error(f"Generic DCC thumbnail generation failed: {e}")
        
        return None
    
    def _generate_generic_thumbnail(self, file_path: str, entity_type: str, entity_name: str) -> Optional[str]:
        """Generate generic thumbnail when DCC-specific generation fails"""
        try:
            if QT_AVAILABLE:
                pixmap = self._create_placeholder_thumbnail(entity_type, entity_name)
                if pixmap:
                    # Save to appropriate location
                    thumbnail_path = self._get_thumbnail_path(file_path, entity_type, entity_name)
                    pixmap.save(thumbnail_path)
                    return thumbnail_path
        except Exception as e:
            self.logger.error(f"Generic thumbnail generation failed: {e}")
        
        return None
    
    def _create_placeholder_thumbnail(self, entity_type: str, entity_name: str):
        """Create placeholder thumbnail with entity information"""
        if not QT_AVAILABLE:
            return None
        
        try:
            pixmap = QPixmap(self.config.size[0], self.config.size[1])
            pixmap.fill(QColor("#1A2332"))
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw background with rounded corners
            painter.setBrush(QColor("#2A3441"))
            painter.setPen(QPen(QColor("#73C2FB"), 2))
            painter.drawRoundedRect(2, 2, self.config.size[0]-4, self.config.size[1]-4, 8, 8)
            
            # Draw icon based on type
            painter.setPen(QPen(QColor("#73C2FB"), 3))
            painter.setBrush(QColor("#73C2FB"))
            
            center_x = self.config.size[0] // 2
            center_y = self.config.size[1] // 2
            
            if entity_type.lower() in ["character", "characters"]:
                # Draw character icon
                painter.drawEllipse(center_x-15, center_y-25, 30, 30)  # Head
                painter.drawRect(center_x-5, center_y+5, 10, 20)       # Body
            elif entity_type.lower() in ["prop", "props"]:
                # Draw prop icon (cube)
                painter.drawRect(center_x-15, center_y-15, 30, 30)
            elif entity_type.lower() in ["environment", "environments"]:
                # Draw environment icon
                painter.drawRect(center_x-20, center_y, 40, 15)        # Ground
                painter.drawEllipse(center_x-25, center_y-15, 50, 25)  # Sky
            elif entity_type.lower() == "shot":
                # Draw shot icon (camera)
                painter.drawRect(center_x-20, center_y-10, 40, 20)     # Camera body
                painter.drawEllipse(center_x-25, center_y-15, 10, 10)  # Lens
            else:
                # Default icon
                painter.drawEllipse(center_x-15, center_y-15, 30, 30)
            
            painter.end()
            return pixmap
            
        except Exception as e:
            self.logger.error(f"Placeholder thumbnail creation failed: {e}")
            return None
    
    def _get_thumbnail_path(self, file_path: str, entity_type: str, entity_name: str, task_name: str = "") -> str:
        """Get thumbnail path following Prism conventions"""
        file_name = Path(file_path).stem
        
        if entity_type.lower() in ["asset", "character", "prop", "environment"]:
            # Asset thumbnail
            thumb_dir = self.project_path / self.config.thumbnail_folder / "assets"
            if task_name:
                thumb_dir = thumb_dir / task_name
            thumb_dir.mkdir(parents=True, exist_ok=True)
            return str(thumb_dir / f"{file_name}_thumb.png")
        elif entity_type.lower() == "shot":
            # Shot thumbnail
            thumb_dir = self.project_path / self.config.thumbnail_folder / "shots"
            if task_name:
                thumb_dir = thumb_dir / task_name
            thumb_dir.mkdir(parents=True, exist_ok=True)
            return str(thumb_dir / f"{file_name}_thumb.png")
        else:
            # Generic version thumbnail
            thumb_dir = self.project_path / self.config.thumbnail_folder / "versions"
            thumb_dir.mkdir(parents=True, exist_ok=True)
            return str(thumb_dir / f"{file_name}_thumb.png")
    
    def _capture_screen(self):
        """Capture screenshot of the entire screen"""
        if not QT_AVAILABLE:
            return None
        
        try:
            app = QApplication.instance()
            if not app:
                return None
            
            screen = QApplication.primaryScreen()
            if screen:
                return screen.grabWindow(0)
        except Exception as e:
            self.logger.error(f"Screen capture failed: {e}")
        
        return None
    
    def _find_maya_python(self) -> Optional[str]:
        """Find Maya Python executable"""
        maya_paths = [
            r"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe",
            r"C:\Program Files\Autodesk\Maya2023\bin\mayapy.exe",
            r"C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe",
            "/Applications/Autodesk/maya2024/Maya.app/Contents/bin/mayapy",
            "/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy",
        ]
        
        for path in maya_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _find_blender_executable(self) -> Optional[str]:
        """Find Blender executable"""
        blender_paths = [
            r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "/usr/bin/blender",
        ]
        
        for path in blender_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _find_houdini_executable(self) -> Optional[str]:
        """Find Houdini executable"""
        houdini_paths = [
            r"C:\Program Files\Side Effects Software\Houdini 20.0.506\bin\houdini.exe",
            r"C:\Program Files\Side Effects Software\Houdini 19.5.569\bin\houdini.exe",
            "/Applications/Houdini/Houdini20.0.506/Frameworks/Houdini.framework/Versions/Current/Resources/bin/houdini",
        ]
        
        for path in houdini_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _find_nuke_executable(self) -> Optional[str]:
        """Find Nuke executable"""
        nuke_paths = [
            r"C:\Program Files\Nuke14.0v1\Nuke14.0.exe",
            r"C:\Program Files\Nuke13.2v5\Nuke13.2.exe",
            "/Applications/Nuke14.0v1/Nuke14.0v1.app/Contents/MacOS/Nuke14.0v1",
        ]
        
        for path in nuke_paths:
            if os.path.exists(path):
                return path
        
        return None


class FileWatcher(FileSystemEventHandler):
    """File system watcher for automatic thumbnail generation"""
    
    def __init__(self, thumbnail_generator: ThumbnailGenerator):
        self.thumbnail_generator = thumbnail_generator
        self.logger = get_logger("FileWatcher")
        self.dcc_extensions = {'.ma', '.mb', '.blend', '.hip', '.hipnc', '.nk', '.max', '.c4d', '.psd'}
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        if Path(file_path).suffix.lower() in self.dcc_extensions:
            self.logger.info(f"File modified, generating thumbnail: {file_path}")
            
            # Generate thumbnail in a separate thread to avoid blocking
            def generate_thumbnail():
                try:
                    self.thumbnail_generator.generate_dcc_thumbnail(file_path)
                except Exception as e:
                    self.logger.error(f"Failed to generate thumbnail for {file_path}: {e}")
            
            thread = threading.Thread(target=generate_thumbnail)
            thread.daemon = True
            thread.start()
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        if Path(file_path).suffix.lower() in self.dcc_extensions:
            self.logger.info(f"File created, generating thumbnail: {file_path}")
            
            # Generate thumbnail in a separate thread
            def generate_thumbnail():
                try:
                    self.thumbnail_generator.generate_dcc_thumbnail(file_path)
                except Exception as e:
                    self.logger.error(f"Failed to generate thumbnail for {file_path}: {e}")
            
            thread = threading.Thread(target=generate_thumbnail)
            thread.daemon = True
            thread.start()
