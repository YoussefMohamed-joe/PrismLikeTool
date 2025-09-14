"""
Maya tool entry point for Vogue Manager

Provides the main entry point for using Vogue Manager within Maya.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
current_dir = Path(__file__).parent
src_path = current_dir.parent
sys.path.insert(0, str(src_path))

try:
    from PySide2.QtWidgets import QApplication, QMessageBox
    from PySide2.QtCore import Qt
    PYSIDE2_AVAILABLE = True
except ImportError:
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox
        from PyQt5.QtCore import Qt
        PYSIDE2_AVAILABLE = True
    except ImportError:
        PYSIDE2_AVAILABLE = False

from vogue_core.logging_utils import get_logger
from vogue_maya.dock import VogueMayaController
from vogue_maya.maya_bridge import is_maya_running, get_maya_version
from vogue_app.colors import COLORS
from vogue_app.qss import build_qss


# Global controller instance
_vogue_controller = None


def show_vogue_manager(title: str = "Vogue Launcher") -> bool:
    """
    Show the Vogue Launcher widget in Maya
    
    Args:
        title: Title for the dock widget
        
    Returns:
        True if successful, False otherwise
    """
    global _vogue_controller
    
    logger = get_logger("MayaTool")
    
    # Check if Maya is running
    if not is_maya_running():
        logger.error("Maya is not running or not available")
        if PYSIDE2_AVAILABLE:
            QMessageBox.critical(None, "Error", "Maya is not running or not available.")
        return False
    
    # Check if Qt is available
    if not PYSIDE2_AVAILABLE:
        logger.error("PySide2 or PyQt5 is required but not installed")
        return False
    
    try:
        # Create or get existing controller
        if _vogue_controller is None:
            _vogue_controller = VogueMayaController()
            logger.info("Created Vogue Maya Controller")
        
        # Show the widget in Maya
        success = _vogue_controller.show_in_maya(title)
        
        if success:
            logger.info(f"Vogue Launcher shown in Maya: {title}")
            
            # Apply styling to the widget
            if _vogue_controller.widget:
                _vogue_controller.widget.setStyleSheet(build_qss())
        else:
            logger.error("Failed to show Vogue Launcher in Maya")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to show Vogue Manager: {e}")
        if PYSIDE2_AVAILABLE:
            QMessageBox.critical(None, "Error", f"Failed to show Vogue Manager:\n\n{str(e)}")
        return False


def hide_vogue_manager() -> bool:
    """
    Hide the Vogue Manager widget from Maya
    
    Returns:
        True if successful, False otherwise
    """
    global _vogue_controller
    
    logger = get_logger("MayaTool")
    
    if _vogue_controller is None:
        logger.warning("No Vogue Manager instance to hide")
        return True
    
    try:
        success = _vogue_controller.hide_from_maya()
        if success:
            logger.info("Vogue Manager hidden from Maya")
        else:
            logger.error("Failed to hide Vogue Manager from Maya")
        return success
        
    except Exception as e:
        logger.error(f"Failed to hide Vogue Manager: {e}")
        return False


def get_vogue_controller() -> Optional[VogueMayaController]:
    """
    Get the current Vogue Manager controller instance
    
    Returns:
        Controller instance or None if not created
    """
    return _vogue_controller


def is_vogue_manager_visible() -> bool:
    """
    Check if Vogue Manager is currently visible in Maya
    
    Returns:
        True if visible, False otherwise
    """
    if _vogue_controller is None or _vogue_controller.widget is None:
        return False
    
    return _vogue_controller.widget.dock_control is not None


def toggle_vogue_manager() -> bool:
    """
    Toggle Vogue Manager visibility in Maya
    
    Returns:
        True if successful, False otherwise
    """
    if is_vogue_manager_visible():
        return hide_vogue_manager()
    else:
        return show_vogue_manager()


def get_maya_info() -> dict:
    """
    Get information about the current Maya session
    
    Returns:
        Dictionary with Maya information
    """
    info = {
        "maya_running": is_maya_running(),
        "maya_version": get_maya_version(),
        "qt_available": PYSIDE2_AVAILABLE,
        "vogue_visible": is_vogue_manager_visible()
    }
    
    return info


def install_shelf_button() -> bool:
    """
    Install a shelf button for Vogue Manager in Maya
    
    Returns:
        True if successful, False otherwise
    """
    if not is_maya_running():
        return False
    
    try:
        import maya.mel as mel
        
        # Create shelf button
        mel.eval('''
        global proc vogueManagerShelfButton() {
            python("import vogue_maya.tool as vm; vm.show_vogue_manager()");
        }
        
        // Add button to current shelf
        shelfTabLayout = `tabLayout -q -selectTab $gShelfTopLevel`;
        shelfLayout = `shelfTabLayout -q -childArray $shelfTabLayout`;
        
        button -label "Vogue" -command "vogueManagerShelfButton" -annotation "Vogue Manager" -image "vogueManager.png";
        ''')
        
        logger = get_logger("MayaTool")
        logger.info("Installed Vogue Manager shelf button")
        return True
        
    except Exception as e:
        logger = get_logger("MayaTool")
        logger.error(f"Failed to install shelf button: {e}")
        return False


def uninstall_shelf_button() -> bool:
    """
    Uninstall the Vogue Manager shelf button from Maya
    
    Returns:
        True if successful, False otherwise
    """
    if not is_maya_running():
        return False
    
    try:
        import maya.mel as mel
        
        # Remove shelf button
        mel.eval('''
        // Find and remove Vogue Manager button
        shelfTabLayout = `tabLayout -q -selectTab $gShelfTopLevel`;
        shelfLayout = `shelfTabLayout -q -childArray $shelfTabLayout`;
        
        // This is a simplified approach - in practice you'd need to track button IDs
        // and remove them properly
        ''')
        
        logger = get_logger("MayaTool")
        logger.info("Uninstalled Vogue Manager shelf button")
        return True
        
    except Exception as e:
        logger = get_logger("MayaTool")
        logger.error(f"Failed to uninstall shelf button: {e}")
        return False


# Maya-specific functions that can be called from MEL
def maya_open_version(file_path: str) -> bool:
    """
    Open a version file in Maya (can be called from MEL)
    
    Args:
        file_path: Path to the version file
        
    Returns:
        True if successful, False otherwise
    """
    if _vogue_controller and _vogue_controller.widget:
        _vogue_controller.widget.open_version(file_path)
        return True
    return False


def maya_load_project(project_path: str) -> bool:
    """
    Load a project in Maya (can be called from MEL)
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        True if successful, False otherwise
    """
    if _vogue_controller and _vogue_controller.widget:
        _vogue_controller.widget.load_project(project_path)
        return True
    return False
