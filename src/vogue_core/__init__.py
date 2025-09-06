"""
Vogue Manager Core Backend

A production pipeline management system similar to Prism but completely independent.
Provides project management, asset/shot tracking, and version control.
"""

__version__ = "1.0.0"
__author__ = "Vogue Manager Team"

from .models import Project, Asset, Shot, Version, Department, Task
from .manager import ProjectManager
from .schema import validate_pipeline, create_default_pipeline
from .fs import ensure_layout, atomic_write_json, scan_assets, scan_shots, next_version
from .settings import VogueSettings
from .logging_utils import get_logger

__all__ = [
    "Project",
    "Asset", 
    "Shot",
    "Version",
    "Department",
    "Task",
    "ProjectManager",
    "validate_pipeline",
    "create_default_pipeline",
    "ensure_layout",
    "atomic_write_json",
    "scan_assets",
    "scan_shots", 
    "next_version",
    "VogueSettings",
    "get_logger"
]
