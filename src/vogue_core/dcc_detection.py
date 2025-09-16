"""
DCC application detection utilities.

Currently focused on Windows (as per environment), with simple heuristics for:
- Autodesk Maya
- Blender
- Foundry Nuke
- SideFX Houdini
- Autodesk 3ds Max
- Unreal Engine

Returns structured data suitable for UI listing and launching.
"""

from __future__ import annotations

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


class DccApp:
    """Represents a detected DCC application."""

    def __init__(self, name: str, executable: Path, version: Optional[str] = None, args: Optional[List[str]] = None):
        self.name = name
        self.executable = Path(executable)
        self.version = version or "unknown"
        self.args = args or []

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "path": str(self.executable),
            "version": self.version,
            "args": json.dumps(self.args),
        }


def _find_candidates(paths: List[Path], patterns: List[str]) -> List[Path]:
    results: List[Path] = []
    for base in paths:
        if not base.exists():
            continue
        try:
            for pattern in patterns:
                for p in base.rglob(pattern):
                    # Skip obviously invalid files
                    if p.is_file():
                        results.append(p)
        except Exception:
            continue
    return results


def _detect_maya() -> List[DccApp]:
    candidates: List[DccApp] = []
    program_files = [
        Path(os.environ.get("ProgramFiles", "C:/Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")),
    ]
    exe_candidates = _find_candidates(program_files, ["Autodesk/Maya*/bin/maya.exe"])  # e.g., Maya2024
    version_re = re.compile(r"Maya(\d{4})", re.IGNORECASE)
    for exe in exe_candidates:
        m = version_re.search(str(exe))
        version = m.group(1) if m else "unknown"
        candidates.append(DccApp("Maya", exe, version))
    # Also check MAYA_LOCATION
    maya_loc = os.environ.get("MAYA_LOCATION")
    if maya_loc:
        exe = Path(maya_loc) / "bin" / "maya.exe"
        if exe.exists():
            candidates.append(DccApp("Maya", exe, os.environ.get("MAYA_VER", "unknown")))
    return _dedupe(candidates)


def _detect_blender() -> List[DccApp]:
    candidates: List[DccApp] = []
    program_files = [Path(os.environ.get("ProgramFiles", "C:/Program Files"))]
    exe_candidates = _find_candidates(program_files, ["Blender Foundation/Blender*/blender.exe"])
    version_re = re.compile(r"Blender(\s*|/)([0-9.]+)", re.IGNORECASE)
    for exe in exe_candidates:
        m = version_re.search(str(exe))
        version = m.group(2) if m and m.lastindex and m.lastindex >= 2 else "unknown"
        candidates.append(DccApp("Blender", exe, version))
    return _dedupe(candidates)


def _detect_nuke() -> List[DccApp]:
    candidates: List[DccApp] = []
    program_files = [Path(os.environ.get("ProgramFiles", "C:/Program Files"))]
    patterns = [
        "Nuke*/Nuke*.exe",  # Nuke13.2v5/Nuke13.2.exe
    ]
    exe_candidates = _find_candidates(program_files, patterns)
    version_re = re.compile(r"Nuke(\d+\.[\dv]+)", re.IGNORECASE)
    for exe in exe_candidates:
        m = version_re.search(str(exe))
        version = m.group(1) if m else "unknown"
        candidates.append(DccApp("Nuke", exe, version))
    return _dedupe(candidates)


def _detect_houdini() -> List[DccApp]:
    candidates: List[DccApp] = []
    program_files = [Path(os.environ.get("ProgramFiles", "C:/Program Files"))]
    exe_candidates = _find_candidates(program_files, ["Side Effects Software/Houdini *\*/bin/houdinifx.exe"])  # includes build
    version_re = re.compile(r"Houdini\s*([0-9.]+)", re.IGNORECASE)
    for exe in exe_candidates:
        m = version_re.search(str(exe))
        version = m.group(1) if m else "unknown"
        candidates.append(DccApp("Houdini", exe, version))
    return _dedupe(candidates)


def _detect_3dsmax() -> List[DccApp]:
    candidates: List[DccApp] = []
    program_files = [
        Path(os.environ.get("ProgramFiles", "C:/Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")),
    ]
    exe_candidates = _find_candidates(program_files, ["Autodesk/3ds Max */3dsmax.exe"])
    version_re = re.compile(r"3ds Max (\d{4})", re.IGNORECASE)
    for exe in exe_candidates:
        m = version_re.search(str(exe))
        version = m.group(1) if m else "unknown"
        candidates.append(DccApp("3ds Max", exe, version))
    return _dedupe(candidates)


def _detect_unreal() -> List[DccApp]:
    candidates: List[DccApp] = []
    program_files = [Path(os.environ.get("ProgramFiles", "C:/Program Files"))]
    patterns = [
        "Epic Games/UE_*/Engine/Binaries/Win64/UE4Editor.exe",
        "Epic Games/UE_*/Engine/Binaries/Win64/UnrealEditor.exe",
    ]
    exe_candidates = _find_candidates(program_files, patterns)
    version_re = re.compile(r"UE_([0-9.]+)")
    for exe in exe_candidates:
        m = version_re.search(str(exe))
        version = m.group(1) if m else "unknown"
        candidates.append(DccApp("Unreal Engine", exe, version))
    return _dedupe(candidates)


def _dedupe(apps: List[DccApp]) -> List[DccApp]:
    seen = set()
    unique: List[DccApp] = []
    for app in apps:
        key = (app.name, str(app.executable))
        if key in seen:
            continue
        seen.add(key)
        unique.append(app)
    return unique


def detect_dcc_apps() -> List[Dict[str, str]]:
    """
    Detect installed DCC applications.

    Returns a list of dicts: {name, path, version, args(json)}
    """
    detected: List[DccApp] = []
    # Windows-focused detection; extend with platform checks if needed
    detected.extend(_detect_maya())
    detected.extend(_detect_blender())
    detected.extend(_detect_nuke())
    detected.extend(_detect_houdini())
    detected.extend(_detect_3dsmax())
    detected.extend(_detect_unreal())
    return [app.to_dict() for app in _dedupe(detected)]


