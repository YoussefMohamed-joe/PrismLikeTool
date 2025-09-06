"""
Maya bridge utilities for Vogue Manager

Provides Maya-safe wrappers for Maya commands and UI operations.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Maya imports with error handling
try:
    import maya.cmds as cmds
    import maya.OpenMayaUI as omui
    from maya import mel
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False
    # Create dummy functions for when Maya is not available
    def cmds():
        pass
    def omui():
        pass
    def mel():
        pass

try:
    from PySide2.QtWidgets import QWidget
    from PySide2.QtCore import Qt
    from shiboken2 import wrapInstance
    PYSIDE2_AVAILABLE = True
except ImportError:
    try:
        from PyQt5.QtWidgets import QWidget
        from PyQt5.QtCore import Qt
        from sip import wrapinstance as wrapInstance
        PYSIDE2_AVAILABLE = True
    except ImportError:
        PYSIDE2_AVAILABLE = False
        def wrapInstance(*args, **kwargs):
            return None

from ..vogue_core.logging_utils import get_logger


def open_scene(file_path: str, force: bool = True) -> bool:
    """
    Open a Maya scene file
    
    Args:
        file_path: Path to the Maya scene file
        force: Whether to force open (close current scene without saving)
        
    Returns:
        True if successful, False otherwise
    """
    if not MAYA_AVAILABLE:
        get_logger("MayaBridge").error("Maya not available")
        return False
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            get_logger("MayaBridge").error(f"File does not exist: {file_path}")
            return False
        
        # Open the scene
        if force:
            cmds.file(file_path, open=True, force=True)
        else:
            cmds.file(file_path, open=True)
        
        get_logger("MayaBridge").info(f"Opened scene: {file_path}")
        return True
        
    except Exception as e:
        get_logger("MayaBridge").error(f"Failed to open scene {file_path}: {e}")
        return False


def maya_main_window() -> Optional[QWidget]:
    """
    Get the Maya main window as a QWidget
    
    Returns:
        Maya main window widget or None if not available
    """
    if not MAYA_AVAILABLE or not PYSIDE2_AVAILABLE:
        return None
    
    try:
        # Get Maya main window
        maya_window = omui.MQtUtil.mainWindow()
        if maya_window is None:
            return None
        
        # Convert to QWidget
        maya_widget = wrapInstance(int(maya_window), QWidget)
        return maya_widget
        
    except Exception as e:
        get_logger("MayaBridge").error(f"Failed to get Maya main window: {e}")
        return None


def create_dock_widget(widget_class, title: str, area: int = 1) -> Optional[str]:
    """
    Create a dockable widget in Maya
    
    Args:
        widget_class: Widget class to dock
        title: Dock widget title
        area: Dock area (1=right, 2=left, 3=top, 4=bottom)
        
    Returns:
        Dock control name or None if failed
    """
    if not MAYA_AVAILABLE:
        return None
    
    try:
        # Create dock control
        dock_control = cmds.dockControl(
            title=title,
            area=area,
            content=widget_class.__name__,
            allowedArea=[1, 2, 3, 4],
            width=400,
            height=600
        )
        
        get_logger("MayaBridge").info(f"Created dock widget: {title}")
        return dock_control
        
    except Exception as e:
        get_logger("MayaBridge").error(f"Failed to create dock widget: {e}")
        return None


def delete_dock_widget(dock_control: str) -> bool:
    """
    Delete a dock widget
    
    Args:
        dock_control: Dock control name
        
    Returns:
        True if successful, False otherwise
    """
    if not MAYA_AVAILABLE:
        return False
    
    try:
        if cmds.dockControl(dock_control, exists=True):
            cmds.deleteUI(dock_control)
            get_logger("MayaBridge").info(f"Deleted dock widget: {dock_control}")
            return True
        return False
        
    except Exception as e:
        get_logger("MayaBridge").error(f"Failed to delete dock widget: {e}")
        return False


def get_current_scene_path() -> Optional[str]:
    """
    Get the current Maya scene path
    
    Returns:
        Current scene path or None if not saved
    """
    if not MAYA_AVAILABLE:
        return None
    
    try:
        scene_path = cmds.file(query=True, sceneName=True)
        if scene_path:
            return scene_path
        return None
        
    except Exception as e:
        get_logger("MayaBridge").error(f"Failed to get current scene path: {e}")
        return None


def is_scene_modified() -> bool:
    """
    Check if the current scene has been modified
    
    Returns:
        True if modified, False otherwise
    """
    if not MAYA_AVAILABLE:
        return False
    
    try:
        return cmds.file(query=True, modified=True)
    except Exception as e:
        get_logger("MayaBridge").error(f"Failed to check scene modification: {e}")
        return False


def save_scene(file_path: str = None, force: bool = False) -> bool:
    """
    Save the current Maya scene
    
    Args:
        file_path: Optional file path to save to
        force: Whether to force save
        
    Returns:
        True if successful, False otherwise
    """
    if not MAYA_AVAILABLE:
        return False
    
    try:
        if file_path:
            cmds.file(rename=file_path)
        
        if force:
            cmds.file(save=True, force=True)
        else:
            cmds.file(save=True)
        
        get_logger("MayaBridge").info(f"Saved scene: {file_path or 'current'}")
        return True
        
    except Exception as e:
        get_logger("MayaBridge").error(f"Failed to save scene: {e}")
        return False


def get_scene_info() -> dict:
    """
    Get information about the current scene
    
    Returns:
        Dictionary with scene information
    """
    if not MAYA_AVAILABLE:
        return {}
    
    try:
        info = {
            "path": get_current_scene_path(),
            "modified": is_scene_modified(),
            "units": cmds.currentUnit(query=True, linear=True),
            "time_unit": cmds.currentUnit(query=True, time=True),
            "fps": cmds.currentUnit(query=True, time=True),
        }
        
        # Get frame range
        try:
            info["start_frame"] = cmds.playbackOptions(query=True, min=True)
            info["end_frame"] = cmds.playbackOptions(query=True, max=True)
        except:
            info["start_frame"] = 1
            info["end_frame"] = 100
        
        return info
        
    except Exception as e:
        get_logger("MayaBridge").error(f"Failed to get scene info: {e}")
        return {}


def create_playblast(output_path: str, width: int = 1920, height: int = 1080, 
                    start_frame: int = None, end_frame: int = None) -> bool:
    """
    Create a playblast of the current scene
    
    Args:
        output_path: Output file path
        width: Playblast width
        height: Playblast height
        start_frame: Start frame (uses current if None)
        end_frame: End frame (uses current if None)
        
    Returns:
        True if successful, False otherwise
    """
    if not MAYA_AVAILABLE:
        return False
    
    try:
        # Set playblast options
        options = {
            "filename": output_path,
            "width": width,
            "height": height,
            "format": "image",
            "compression": "jpg",
            "quality": 100,
            "showOrnaments": True,
            "offScreen": False,
            "framePadding": 4
        }
        
        if start_frame is not None:
            options["startTime"] = start_frame
        if end_frame is not None:
            options["endTime"] = end_frame
        
        # Create playblast
        cmds.playblast(**options)
        
        get_logger("MayaBridge").info(f"Created playblast: {output_path}")
        return True
        
    except Exception as e:
        get_logger("MayaBridge").error(f"Failed to create playblast: {e}")
        return False


def get_maya_version() -> str:
    """
    Get Maya version string
    
    Returns:
        Maya version or "Unknown" if not available
    """
    if not MAYA_AVAILABLE:
        return "Unknown"
    
    try:
        return cmds.about(version=True)
    except:
        return "Unknown"


def is_maya_running() -> bool:
    """
    Check if Maya is currently running
    
    Returns:
        True if Maya is running, False otherwise
    """
    return MAYA_AVAILABLE and cmds.about(batch=True) == False
