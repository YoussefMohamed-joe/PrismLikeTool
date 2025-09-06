"""
Vogue Manager Maya Integration

Provides Maya-specific functionality for Vogue Manager production pipeline.
"""

__version__ = "1.0.0"
__author__ = "Vogue Manager Team"

from .tool import show_vogue_manager
from .maya_bridge import open_scene, maya_main_window

__all__ = ["show_vogue_manager", "open_scene", "maya_main_window"]
