"""


Bootstrap the PySide2 application and show the main window.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

# Try to import PyQt6, fallback to PySide2
try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt
    QT_AVAILABLE = True
    QT_VERSION = "PyQt6"
except ImportError:
    try:
        from PySide2.QtWidgets import QApplication, QMessageBox
        from PySide2.QtCore import Qt
        QT_AVAILABLE = True
        QT_VERSION = "PySide2"
    except ImportError:
        QT_AVAILABLE = False
        QT_VERSION = None

from vogue_core.logging_utils import setup_logging, get_logger
from vogue_app.controller import VogueController

# Global controller reference
_current_controller = None

def get_current_controller():
    """Get the current controller instance"""
    return _current_controller

# Import set_current_controller from ui module
from vogue_app.ui import set_current_controller


def main():
    """Main entry point for Vogue Manager desktop application"""
    
    # Check if Qt is available
    if not QT_AVAILABLE:
        print("Error: PyQt6 or PySide2 is required but neither is installed.")
        print("Please install one of: pip install PyQt6 or pip install PySide2")
        sys.exit(1)
    
    # Set up logging
    setup_logging(level="INFO")
    logger = get_logger("Main")
    
    logger.info("Starting Vogue Manager Desktop Application")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Vogue Manager")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Vogue Manager Team")
    
    # Set application style
    app.setStyle('Fusion')  # Use Fusion style for better cross-platform appearance
    
    try:
        # Create and show main controller
        controller = VogueController()
        set_current_controller(controller)  # Set global reference
        controller.show()
        
        logger.info("Vogue Manager started successfully")
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start Vogue Manager: {e}")
        
        # Show error message
        if 'app' in locals():
            QMessageBox.critical(
                None, 
                "Startup Error", 
                f"Failed to start Vogue Manager:\n\n{str(e)}"
            )
        else:
            print(f"Failed to start Vogue Manager: {e}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
