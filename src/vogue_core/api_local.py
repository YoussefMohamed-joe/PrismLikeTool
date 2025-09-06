"""
Local HTTP API for Vogue Manager

Provides a FastAPI-based REST API for remote access to Vogue Manager functionality.
This is a scaffold implementation that can be enabled optionally.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json

try:
    from fastapi import FastAPI, HTTPException, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Create dummy classes for when FastAPI is not available
    class BaseModel:
        pass
    class FastAPI:
        pass
    class HTTPException(Exception):
        pass
    class Depends:
        pass
    class CORSMiddleware:
        pass

from .manager import ProjectManager
from .models import Project, Asset, Shot, Version
from .logging_utils import get_logger


# Pydantic models for API
class ProjectCreate(BaseModel):
    name: str
    parent_dir: str
    fps: int = 24
    resolution: List[int] = [1920, 1080]


class AssetCreate(BaseModel):
    type: str
    name: str
    meta: Dict[str, Any] = {}


class ShotCreate(BaseModel):
    sequence: str
    name: str
    meta: Dict[str, Any] = {}


class VersionCreate(BaseModel):
    entity_key: str
    source_file: str
    user: str
    comment: str = ""
    version: Optional[str] = None


class VogueAPI:
    """Vogue Manager HTTP API"""
    
    def __init__(self):
        self.app = None
        self.manager = ProjectManager()
        self.logger = get_logger("API")
        
        if FASTAPI_AVAILABLE:
            self._setup_fastapi()
        else:
            self.logger.warning("FastAPI not available. API functionality disabled.")
    
    def _setup_fastapi(self):
        """Set up FastAPI application"""
        self.app = FastAPI(
            title="Vogue Manager API",
            description="REST API for Vogue Manager production pipeline",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up API routes"""
        if not self.app:
            return
        
        @self.app.get("/")
        async def root():
            return {"message": "Vogue Manager API", "version": "1.0.0"}
        
        @self.app.get("/projects")
        async def list_projects():
            """List all discovered projects"""
            try:
                from .settings import settings
                projects = settings.discover_projects()
                return {"projects": projects}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/projects")
        async def create_project(project_data: ProjectCreate):
            """Create a new project"""
            try:
                project = self.manager.create_project(
                    name=project_data.name,
                    parent_dir=project_data.parent_dir,
                    fps=project_data.fps,
                    resolution=project_data.resolution
                )
                return {"message": "Project created", "project": project.get_info()}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/projects/load")
        async def load_project(project_path: str):
            """Load an existing project"""
            try:
                project = self.manager.load_project(project_path)
                return {"message": "Project loaded", "project": project.get_info()}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/project/info")
        async def get_project_info():
            """Get current project information"""
            if not self.manager.current_project:
                raise HTTPException(status_code=404, detail="No project loaded")
            
            return {"project": self.manager.current_project.get_info()}
        
        @self.app.post("/project/save")
        async def save_project():
            """Save current project"""
            try:
                self.manager.save_project()
                return {"message": "Project saved"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/assets")
        async def list_assets():
            """List all assets"""
            assets = self.manager.list_assets()
            return {"assets": [{"name": a.name, "type": a.type, "path": a.path, "meta": a.meta} for a in assets]}
        
        @self.app.post("/assets")
        async def create_asset(asset_data: AssetCreate):
            """Create a new asset"""
            try:
                asset = self.manager.add_asset(
                    type=asset_data.type,
                    name=asset_data.name,
                    meta=asset_data.meta
                )
                return {"message": "Asset created", "asset": {"name": asset.name, "type": asset.type, "path": asset.path}}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/assets/{asset_name}")
        async def get_asset(asset_name: str):
            """Get asset by name"""
            asset = self.manager.get_asset(asset_name)
            if not asset:
                raise HTTPException(status_code=404, detail="Asset not found")
            
            return {"asset": {"name": asset.name, "type": asset.type, "path": asset.path, "meta": asset.meta}}
        
        @self.app.get("/shots")
        async def list_shots():
            """List all shots"""
            shots = self.manager.list_shots()
            return {"shots": [{"sequence": s.sequence, "name": s.name, "path": s.path, "meta": s.meta} for s in shots]}
        
        @self.app.post("/shots")
        async def create_shot(shot_data: ShotCreate):
            """Create a new shot"""
            try:
                shot = self.manager.add_shot(
                    sequence=shot_data.sequence,
                    name=shot_data.name,
                    meta=shot_data.meta
                )
                return {"message": "Shot created", "shot": {"sequence": shot.sequence, "name": shot.name, "path": shot.path}}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/shots/{sequence}/{name}")
        async def get_shot(sequence: str, name: str):
            """Get shot by sequence and name"""
            shot = self.manager.get_shot(sequence, name)
            if not shot:
                raise HTTPException(status_code=404, detail="Shot not found")
            
            return {"shot": {"sequence": shot.sequence, "name": shot.name, "path": shot.path, "meta": shot.meta}}
        
        @self.app.get("/versions/{entity_key}")
        async def list_versions(entity_key: str):
            """List versions for an entity"""
            versions = self.manager.list_versions(entity_key)
            return {"versions": [{"version": v.version, "user": v.user, "date": v.date, "comment": v.comment, "path": v.path} for v in versions]}
        
        @self.app.post("/versions")
        async def create_version(version_data: VersionCreate):
            """Create a new version"""
            try:
                version = self.manager.add_version(
                    entity_key=version_data.entity_key,
                    source_file=version_data.source_file,
                    user=version_data.user,
                    comment=version_data.comment,
                    version=version_data.version
                )
                return {"message": "Version created", "version": {"version": version.version, "user": version.user, "date": version.date, "path": version.path}}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/departments")
        async def list_departments():
            """List departments"""
            departments = self.manager.get_departments()
            return {"departments": departments}
        
        @self.app.get("/tasks")
        async def list_tasks():
            """List tasks"""
            tasks = self.manager.get_tasks()
            return {"tasks": tasks}
        
        @self.app.post("/scan")
        async def scan_filesystem(update_missing: bool = True):
            """Scan filesystem and update project"""
            try:
                self.manager.scan_filesystem(update_missing=update_missing)
                return {"message": "Filesystem scan completed"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
    
    def run(self, host: str = "127.0.0.1", port: int = 8000, debug: bool = False):
        """Run the API server"""
        if not self.app:
            self.logger.error("FastAPI not available. Cannot run API server.")
            return
        
        import uvicorn
        uvicorn.run(self.app, host=host, port=port, log_level="info" if not debug else "debug")


# Global API instance
api = VogueAPI()


def run_api_server(host: str = "127.0.0.1", port: int = 8000, debug: bool = False):
    """Run the Vogue Manager API server"""
    api.run(host=host, port=port, debug=debug)
