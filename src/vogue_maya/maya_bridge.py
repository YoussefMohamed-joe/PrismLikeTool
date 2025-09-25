"""
Maya Bridge for Vogue Manager

Provides integration with Autodesk Maya for workfile management,
version creation, and scene operations.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..vogue_core.logging_utils import get_logger


class MayaBridge:
    """Bridge for Maya integration"""
    
    def __init__(self):
        self.logger = get_logger("MayaBridge")
        self.maya_python_path = None
        self._find_maya_python()
    
    def _find_maya_python(self):
        """Find Maya's Python executable (mayapy) with best-effort search."""
        try:
            maya_versions = ["2026", "2025", "2024", "2023", "2022", "2021", "2020"]
            for version in maya_versions:
                if sys.platform == "win32":
                    python_paths = [
                        f"C:\\Program Files\\Autodesk\\Maya{version}\\bin\\mayapy.exe",
                        f"C:\\Program Files\\Autodesk\\Maya{version}\\bin\\mayapy.bat",
                    ]
                elif sys.platform == "darwin":
                    python_paths = [
                        f"/Applications/Autodesk/maya{version}/Maya.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python",
                    ]
                else:
                    python_paths = [
                        f"/usr/autodesk/maya{version}/bin/mayapy",
                    ]
                for path in python_paths:
                    if os.path.exists(path):
                        self.maya_python_path = path
                        self.logger.info(f"Found Maya Python at: {path}")
                        return

            # Fallback glob on Windows
            import glob
            if sys.platform == "win32":
                for path in sorted(glob.glob(r"C:\\Program Files\\Autodesk\\Maya*\\bin\\mayapy.exe"), reverse=True):
                    if os.path.exists(path):
                        self.maya_python_path = path
                        self.logger.info(f"Found Maya Python via glob at: {path}")
                        return
            self.logger.warning("Maya Python not found")
        except Exception as e:
            self.logger.warning(f"Maya Python detection error: {e}")
    
    def is_available(self) -> bool:
        """Check if Maya is available"""
        return self.maya_python_path is not None
    
    def create_workfile(self, project_path: str, entity_name: str, 
                       task_name: str, version: int) -> str:
        """Create a new Maya workfile"""
        if not self.is_available():
            raise RuntimeError("Maya is not available")
        
        # Create workfile directory
        workfile_dir = os.path.join(project_path, "workfiles", entity_name, task_name)
        os.makedirs(workfile_dir, exist_ok=True)
        
        # Generate workfile name
        workfile_name = f"{entity_name}_{task_name}_v{version:03d}.ma"
        workfile_path = os.path.join(workfile_dir, workfile_name)
        
        # Create Maya script to generate workfile
        maya_script = self._generate_workfile_script(workfile_path, project_path)
        
        try:
            # Execute Maya script
            result = subprocess.run(
                [self.maya_python_path, "-c", maya_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Maya script failed: {result.stderr}")
            
            self.logger.info(f"Created Maya workfile: {workfile_path}")
            return workfile_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Maya script timed out")
        except Exception as e:
            raise RuntimeError(f"Failed to create Maya workfile: {e}")
    
    def _generate_workfile_script(self, workfile_path: str, project_path: str) -> str:
        """Generate Maya script to create workfile"""
        return f'''
import maya.cmds as cmds
import maya.mel as mel
import os
import json
from datetime import datetime

try:
    # Set project
    cmds.workspace(project_path, openWorkspace=True)
    
    # Create a new scene
    cmds.file(new=True, force=True)
    
    # Set up basic scene
    cmds.currentUnit(time='film')
    cmds.currentUnit(linear='cm')
    
    # Create basic scene structure
    cmds.group(empty=True, name='ROOT')
    cmds.group(empty=True, name='GEO', parent='ROOT')
    cmds.group(empty=True, name='LIGHTS', parent='ROOT')
    cmds.group(empty=True, name='CAMERAS', parent='ROOT')
    
    # Add project metadata
    metadata = {{
        'project_path': '{project_path}',
        'workfile_path': '{workfile_path}',
        'created_date': datetime.now().isoformat(),
        'maya_version': cmds.about(version=True),
        'created_by': 'Vogue Manager'
    }}
    
    # Store metadata as custom attribute on ROOT
    if not cmds.attributeQuery('vogue_metadata', node='ROOT', exists=True):
        cmds.addAttr('ROOT', longName='vogue_metadata', dataType='string')
    
    cmds.setAttr('ROOT.vogue_metadata', json.dumps(metadata), type='string')
    
    # Save the file
    cmds.file(rename='{workfile_path}')
    cmds.file(save=True, type='mayaAscii')
    
    print("SUCCESS: Workfile created successfully")
except Exception as e:
    print(f"ERROR: {{e}}")
    sys.exit(1)
'''
    
    def get_scene_info(self, workfile_path: str) -> Dict[str, Any]:
        """Get information about a Maya scene"""
        if not self.is_available():
            return {}
        
        maya_script = f'''
import maya.cmds as cmds
import json
import os

try:
    # Open the file
    if os.path.exists('{workfile_path}'):
        cmds.file('{workfile_path}', open=True, force=True)
        
        # Get scene info
        info = {{
            'file_path': '{workfile_path}',
            'file_size': os.path.getsize('{workfile_path}'),
            'maya_version': cmds.about(version=True),
            'scene_units': {{
                'time': cmds.currentUnit(time=True, query=True),
                'linear': cmds.currentUnit(linear=True, query=True),
                'angular': cmds.currentUnit(angular=True, query=True)
            }},
            'objects': {{
                'total': len(cmds.ls()),
                'transforms': len(cmds.ls(type='transform')),
                'meshes': len(cmds.ls(type='mesh')),
                'lights': len(cmds.ls(type='light')),
                'cameras': len(cmds.ls(type='camera'))
            }},
            'materials': len(cmds.ls(mat=True)),
            'textures': len(cmds.ls(type='file'))
        }}
        
        # Get metadata if available
        try:
            if cmds.attributeQuery('vogue_metadata', node='ROOT', exists=True):
                metadata_str = cmds.getAttr('ROOT.vogue_metadata')
                info['metadata'] = json.loads(metadata_str)
        except:
            pass
        
        print(json.dumps(info))
        
    else:
        print(json.dumps({{'error': 'File not found'}}))
        
except Exception as e:
    print(json.dumps({{'error': str(e)}}))
'''
        
        try:
            result = subprocess.run(
                [self.maya_python_path, "-c", maya_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}
    
    def generate_thumbnail(self, workfile_path: str, output_path: str, 
                          size: tuple = (256, 256)) -> bool:
        """Generate thumbnail for Maya scene"""
        if not self.is_available():
            return False

        maya_script = f'''
import maya.cmds as cmds
import maya.mel as mel
import os

try:
    # Open the file
    if os.path.exists('{workfile_path}'):
        cmds.file('{workfile_path}', open=True, force=True)
        
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
        cmds.setAttr('defaultResolution.width', {size[0]})
        cmds.setAttr('defaultResolution.height', {size[1]})
        cmds.setAttr('defaultResolution.pixelAspect', 1.0)
        
        # Render thumbnail
        output_dir = os.path.dirname('{output_path}')
        os.makedirs(output_dir, exist_ok=True)
        
        # Use Maya's playblast for thumbnail (capture output path)
        _pb_path = cmds.playblast(
            format='image',
            filename='{output_path}',
            sequenceTime=False,
            clearCache=True,
            viewer=False,
            showOrnaments=False,
            frame=[1],
            width={size[0]},
            height={size[1]},
            percent=100,
            quality=70,
            compression='png',
            forceOverwrite=True,
            completeFilename=True
        )
        try:
            gen_path = _pb_path if isinstance(_pb_path, str) else str(_pb_path)
            if gen_path and gen_path != '{output_path}' and os.path.exists(gen_path):
                import shutil, os as _os
                try:
                    shutil.move(gen_path, '{output_path}')
                except Exception:
                    _os.replace(gen_path, '{output_path}')
        except Exception:
            pass
        
        print("SUCCESS: Thumbnail generated")
    else:
        print("ERROR: File not found")
except Exception as e:
    print(f"ERROR: {{e}}")
'''
        
        try:
            result = subprocess.run(
                [self.maya_python_path, "-c", maya_script],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return result.returncode == 0 and "SUCCESS" in result.stdout
            
        except Exception as e:
            self.logger.error(f"Failed to generate Maya thumbnail: {e}")
            return False
    
    def launch_maya(self, workfile_path: str = None, project_path: str = None) -> bool:
        """Launch Maya with optional workfile"""
        if not self.is_available():
            return False
        
        try:
            # Find Maya executable
            maya_exe = self.maya_python_path.replace("mayapy", "maya")
            if not os.path.exists(maya_exe):
                maya_exe = self.maya_python_path.replace("mayapy.exe", "maya.exe")
            
            if not os.path.exists(maya_exe):
                self.logger.error("Maya executable not found")
                return False
            
            # Build command
            cmd = [maya_exe]
            
            if project_path:
                cmd.extend(["-proj", project_path])
            
            if workfile_path and os.path.exists(workfile_path):
                cmd.append(workfile_path)
            
            # Launch Maya
            subprocess.Popen(cmd)
            self.logger.info(f"Launched Maya: {' '.join(cmd)}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to launch Maya: {e}")
            return False

    def validate_workfile(self, workfile_path: str) -> Dict[str, Any]:
        """Validate Maya workfile"""
        if not os.path.exists(workfile_path):
            return {"valid": False, "error": "File not found"}
        
        # Check file extension
        if not workfile_path.lower().endswith(('.ma', '.mb')):
            return {"valid": False, "error": "Invalid file extension"}
        
        # Try to get scene info
        scene_info = self.get_scene_info(workfile_path)
        if "error" in scene_info:
            return {"valid": False, "error": scene_info["error"]}
        
        return {
            "valid": True,
            "scene_info": scene_info,
            "file_size": os.path.getsize(workfile_path)
        }


# Global Maya bridge instance
maya_bridge = MayaBridge()