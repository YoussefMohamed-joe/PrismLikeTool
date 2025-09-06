"""
Publishing hooks for Vogue Manager

Provides a simple hook system for pre/post publish operations.
"""

from typing import Dict, Any, List, Callable
from .logging_utils import get_logger


class PublishHook:
    """Base class for publish hooks"""
    
    def pre_publish(self, entity_key: str, version_meta: Dict[str, Any]) -> None:
        """
        Called before publishing a version
        
        Args:
            entity_key: Asset name or "sequence/shot" for shots
            version_meta: Version metadata
        """
        pass
    
    def post_publish(self, entity_key: str, version_meta: Dict[str, Any]) -> None:
        """
        Called after publishing a version
        
        Args:
            entity_key: Asset name or "sequence/shot" for shots
            version_meta: Version metadata
        """
        pass


class PublishManager:
    """Manages publish hooks and operations"""
    
    def __init__(self):
        self.hooks: List[PublishHook] = []
        self.logger = get_logger("PublishManager")
    
    def register_hook(self, hook: PublishHook) -> None:
        """Register a publish hook"""
        self.hooks.append(hook)
        self.logger.info(f"Registered publish hook: {hook.__class__.__name__}")
    
    def unregister_hook(self, hook: PublishHook) -> None:
        """Unregister a publish hook"""
        if hook in self.hooks:
            self.hooks.remove(hook)
            self.logger.info(f"Unregistered publish hook: {hook.__class__.__name__}")
    
    def run_pre_publish(self, entity_key: str, version_meta: Dict[str, Any]) -> None:
        """Run all pre-publish hooks"""
        for hook in self.hooks:
            try:
                hook.pre_publish(entity_key, version_meta)
            except Exception as e:
                self.logger.error(f"Pre-publish hook {hook.__class__.__name__} failed: {e}")
    
    def run_post_publish(self, entity_key: str, version_meta: Dict[str, Any]) -> None:
        """Run all post-publish hooks"""
        for hook in self.hooks:
            try:
                hook.post_publish(entity_key, version_meta)
            except Exception as e:
                self.logger.error(f"Post-publish hook {hook.__class__.__name__} failed: {e}")


# Example hooks
class ValidationHook(PublishHook):
    """Example hook for validation"""
    
    def pre_publish(self, entity_key: str, version_meta: Dict[str, Any]) -> None:
        """Validate before publishing"""
        # TODO: Add validation logic
        # - Check file exists
        # - Validate naming conventions
        # - Check file size limits
        # - Verify dependencies
        pass


class NotificationHook(PublishHook):
    """Example hook for notifications"""
    
    def post_publish(self, entity_key: str, version_meta: Dict[str, Any]) -> None:
        """Send notification after publishing"""
        # TODO: Add notification logic
        # - Send email notifications
        # - Update project status
        # - Notify team members
        pass


class BackupHook(PublishHook):
    """Example hook for backup operations"""
    
    def pre_publish(self, entity_key: str, version_meta: Dict[str, Any]) -> None:
        """Create backup before publishing"""
        # TODO: Add backup logic
        # - Create backup of previous version
        # - Archive old versions
        pass


# Global publish manager instance
publish_manager = PublishManager()

# Register default hooks
publish_manager.register_hook(ValidationHook())
publish_manager.register_hook(NotificationHook())
publish_manager.register_hook(BackupHook())
