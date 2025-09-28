"""
Thumbnail Preview Widget

Provides enhanced thumbnail preview functionality with DCC viewport thumbnails,
launch screenshots, and Prism-style entity previews.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QGridLayout,
                             QSizePolicy, QMenu, QAction, QFileDialog,
                             QMessageBox, QProgressBar, QGroupBox)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QFont, QIcon

from vogue_core.logging_utils import get_logger


class ThumbnailPreviewWidget(QWidget):
    """Enhanced thumbnail preview widget with DCC viewport support"""
    
    # Signals
    thumbnail_clicked = pyqtSignal(str)  # Emitted when thumbnail is clicked
    thumbnail_double_clicked = pyqtSignal(str)  # Emitted when thumbnail is double-clicked
    generate_thumbnail_requested = pyqtSignal(str, str, str)  # file_path, entity_type, entity_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("ThumbnailPreview")
        self.current_thumbnails = {}  # Cache for loaded thumbnails
        self.thumbnail_size = (200, 150)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Thumbnail Preview")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #73C2FB;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh thumbnails")
        self.refresh_btn.setFixedSize(30, 30)
        self.refresh_btn.clicked.connect(self.refresh_thumbnails)
        header_layout.addWidget(self.refresh_btn)
        
        # Generate thumbnail button
        self.generate_btn = QPushButton("📷")
        self.generate_btn.setToolTip("Generate thumbnail")
        self.generate_btn.setFixedSize(30, 30)
        self.generate_btn.clicked.connect(self.generate_thumbnail)
        header_layout.addWidget(self.generate_btn)
        
        layout.addLayout(header_layout)
        
        # Thumbnail display area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.thumbnail_widget = QWidget()
        self.thumbnail_layout = QGridLayout(self.thumbnail_widget)
        self.thumbnail_layout.setSpacing(10)
        self.thumbnail_layout.setContentsMargins(5, 5, 5, 5)
        
        self.scroll_area.setWidget(self.thumbnail_widget)
        layout.addWidget(self.scroll_area)
        
        # Status bar
        self.status_label = QLabel("No thumbnails loaded")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
    
    def load_thumbnails(self, thumbnails: List[Dict[str, Any]]):
        """Load and display thumbnails"""
        self.clear_thumbnails()
        
        if not thumbnails:
            self.status_label.setText("No thumbnails available")
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(thumbnails))
        self.progress_bar.setValue(0)
        
        # Load thumbnails in batches to avoid UI freezing
        self.thumbnail_data = thumbnails
        self.current_index = 0
        self.load_batch()
    
    def load_batch(self, batch_size: int = 6):
        """Load a batch of thumbnails"""
        if not hasattr(self, 'thumbnail_data'):
            return
        
        end_index = min(self.current_index + batch_size, len(self.thumbnail_data))
        
        for i in range(self.current_index, end_index):
            thumbnail_info = self.thumbnail_data[i]
            self.add_thumbnail_widget(thumbnail_info, i)
            self.progress_bar.setValue(i + 1)
        
        self.current_index = end_index
        
        if self.current_index < len(self.thumbnail_data):
            # Load next batch after a short delay
            QTimer.singleShot(50, lambda: self.load_batch(batch_size))
        else:
            # All thumbnails loaded
            self.progress_bar.setVisible(False)
            self.status_label.setText(f"Loaded {len(self.thumbnail_data)} thumbnails")
    
    def add_thumbnail_widget(self, thumbnail_info: Dict[str, Any], index: int):
        """Add a single thumbnail widget"""
        file_path = thumbnail_info.get('file_path', '')
        entity_type = thumbnail_info.get('entity_type', 'asset')
        entity_name = thumbnail_info.get('entity_name', '')
        task_name = thumbnail_info.get('task_name', '')
        thumbnail_path = thumbnail_info.get('thumbnail_path', '')
        
        # Create thumbnail frame
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        frame.setStyleSheet("""
            QFrame {
                border: 2px solid #2A3441;
                border-radius: 8px;
                background-color: #1A2332;
            }
            QFrame:hover {
                border-color: #73C2FB;
                background-color: #2A3441;
            }
        """)
        frame.setFixedSize(self.thumbnail_size[0] + 20, self.thumbnail_size[1] + 60)
        
        # Create layout for thumbnail
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Thumbnail image
        thumbnail_label = QLabel()
        thumbnail_label.setFixedSize(self.thumbnail_size[0], self.thumbnail_size[1])
        thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail_label.setStyleSheet("""
            QLabel {
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #0F1419;
            }
        """)
        
        # Load thumbnail image
        pixmap = self.load_thumbnail_image(thumbnail_path, file_path, entity_type)
        if pixmap:
            scaled_pixmap = pixmap.scaled(
                self.thumbnail_size[0], 
                self.thumbnail_size[1], 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            thumbnail_label.setPixmap(scaled_pixmap)
        else:
            # Show placeholder
            thumbnail_label.setText("📁")
            thumbnail_label.setStyleSheet(thumbnail_label.styleSheet() + """
                QLabel {
                    font-size: 48px;
                    color: #666;
                }
            """)
        
        layout.addWidget(thumbnail_label)
        
        # Entity info
        info_label = QLabel(f"{entity_name}\n{task_name}" if task_name else entity_name)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                color: #73C2FB;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # File info
        file_label = QLabel(Path(file_path).name)
        file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 10px;
            }
        """)
        file_label.setWordWrap(True)
        layout.addWidget(file_label)
        
        # Connect signals
        frame.mousePressEvent = lambda event, path=file_path: self.thumbnail_clicked.emit(path)
        frame.mouseDoubleClickEvent = lambda event, path=file_path: self.thumbnail_double_clicked.emit(path)
        
        # Add context menu
        frame.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        frame.customContextMenuRequested.connect(
            lambda pos, path=file_path, entity_type=entity_type, entity_name=entity_name: 
            self.show_context_menu(pos, path, entity_type, entity_name)
        )
        
        # Add to grid layout
        row = index // 3
        col = index % 3
        self.thumbnail_layout.addWidget(frame, row, col)
    
    def load_thumbnail_image(self, thumbnail_path: str, file_path: str, entity_type: str) -> Optional[QPixmap]:
        """Load thumbnail image with fallback options"""
        # Try to load from thumbnail path
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                pixmap = QPixmap(thumbnail_path)
                if not pixmap.isNull():
                    return pixmap
            except Exception as e:
                self.logger.warning(f"Failed to load thumbnail {thumbnail_path}: {e}")
        
        # Try to load from file directory
        file_dir = Path(file_path).parent
        possible_thumbnails = [
            file_dir / "_thumbs" / f"{Path(file_path).stem}.jpg",
            file_dir / f"{Path(file_path).stem}_thumb.png",
            file_dir / f"{Path(file_path).stem}_preview.jpg",
        ]
        
        for thumb_path in possible_thumbnails:
            if thumb_path.exists():
                try:
                    pixmap = QPixmap(str(thumb_path))
                    if not pixmap.isNull():
                        return pixmap
                except Exception as e:
                    self.logger.warning(f"Failed to load thumbnail {thumb_path}: {e}")
        
        # Try Prism-style entity previews
        if hasattr(self, 'project_path') and self.project_path:
            prism_preview_path = self.get_prism_preview_path(file_path, entity_type)
            if prism_preview_path and os.path.exists(prism_preview_path):
                try:
                    pixmap = QPixmap(prism_preview_path)
                    if not pixmap.isNull():
                        return pixmap
                except Exception as e:
                    self.logger.warning(f"Failed to load Prism preview {prism_preview_path}: {e}")
        
        return None
    
    def get_prism_preview_path(self, file_path: str, entity_type: str) -> Optional[str]:
        """Get Prism-style entity preview path"""
        try:
            if entity_type.lower() in ["asset", "character", "prop", "environment"]:
                # Asset preview
                entity_name = Path(file_path).stem.split('_')[0]  # Extract entity name
                preview_dir = Path(self.project_path) / "00_Pipeline" / "Assetinfo"
                preview_path = preview_dir / f"{entity_name}_preview.jpg"
                return str(preview_path)
            elif entity_type.lower() == "shot":
                # Shot preview
                shot_name = Path(file_path).stem.split('_')[0]  # Extract shot name
                preview_dir = Path(self.project_path) / "00_Pipeline" / "Shotinfo"
                preview_path = preview_dir / f"seq_{shot_name}_preview.jpg"
                return str(preview_path)
        except Exception as e:
            self.logger.warning(f"Failed to get Prism preview path: {e}")
        
        return None
    
    def show_context_menu(self, pos, file_path: str, entity_type: str, entity_name: str):
        """Show context menu for thumbnail"""
        menu = QMenu(self)
        
        # Generate thumbnail action
        generate_action = QAction("Generate Thumbnail", self)
        generate_action.triggered.connect(
            lambda: self.generate_thumbnail_requested.emit(file_path, entity_type, entity_name)
        )
        menu.addAction(generate_action)
        
        # Open file action
        open_action = QAction("Open File", self)
        open_action.triggered.connect(lambda: self.open_file(file_path))
        menu.addAction(open_action)
        
        # Show in explorer action
        show_action = QAction("Show in Explorer", self)
        show_action.triggered.connect(lambda: self.show_in_explorer(file_path))
        menu.addAction(show_action)
        
        menu.exec(self.mapToGlobal(pos))
    
    def open_file(self, file_path: str):
        """Open file with default application"""
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", file_path])
        except Exception as e:
            self.logger.error(f"Failed to open file {file_path}: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open file:\n{str(e)}")
    
    def show_in_explorer(self, file_path: str):
        """Show file in file explorer"""
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", file_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", os.path.dirname(file_path)])
        except Exception as e:
            self.logger.error(f"Failed to show file in explorer {file_path}: {e}")
            QMessageBox.warning(self, "Error", f"Failed to show file in explorer:\n{str(e)}")
    
    def generate_thumbnail(self):
        """Generate thumbnail for selected item"""
        # This would be connected to the main application's thumbnail generation
        pass
    
    def refresh_thumbnails(self):
        """Refresh all thumbnails"""
        if hasattr(self, 'thumbnail_data'):
            self.load_thumbnails(self.thumbnail_data)
    
    def clear_thumbnails(self):
        """Clear all thumbnails"""
        # Clear layout
        while self.thumbnail_layout.count():
            child = self.thumbnail_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.current_thumbnails.clear()
        self.status_label.setText("No thumbnails loaded")
    
    def set_project_path(self, project_path: str):
        """Set project path for Prism-style previews"""
        self.project_path = project_path
    
    def add_launch_screenshot(self, app_name: str, screenshot_path: str):
        """Add launch screenshot to thumbnails"""
        if os.path.exists(screenshot_path):
            thumbnail_info = {
                'file_path': screenshot_path,
                'entity_type': 'launch',
                'entity_name': f"{app_name} Launch",
                'task_name': '',
                'thumbnail_path': screenshot_path
            }
            
            # Add to current thumbnails if they exist
            if hasattr(self, 'thumbnail_data'):
                self.thumbnail_data.insert(0, thumbnail_info)
                self.refresh_thumbnails()
    
    def update_thumbnail(self, file_path: str, new_thumbnail_path: str):
        """Update thumbnail for a specific file"""
        # Find and update the thumbnail in the current display
        for i in range(self.thumbnail_layout.count()):
            item = self.thumbnail_layout.itemAt(i)
            if item and item.widget():
                frame = item.widget()
                # Check if this frame corresponds to the file
                if hasattr(frame, 'file_path') and frame.file_path == file_path:
                    # Update the thumbnail image
                    thumbnail_label = frame.findChild(QLabel)
                    if thumbnail_label:
                        pixmap = QPixmap(new_thumbnail_path)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(
                                self.thumbnail_size[0], 
                                self.thumbnail_size[1], 
                                Qt.AspectRatioMode.KeepAspectRatio, 
                                Qt.TransformationMode.SmoothTransformation
                            )
                            thumbnail_label.setPixmap(scaled_pixmap)
                    break


class ThumbnailGeneratorThread(QThread):
    """Thread for generating thumbnails without blocking UI"""
    
    thumbnail_generated = pyqtSignal(str, str)  # file_path, thumbnail_path
    generation_failed = pyqtSignal(str, str)  # file_path, error_message
    
    def __init__(self, file_path: str, entity_type: str, entity_name: str, task_name: str, manager):
        super().__init__()
        self.file_path = file_path
        self.entity_type = entity_type
        self.entity_name = entity_name
        self.task_name = task_name
        self.manager = manager
    
    def run(self):
        """Generate thumbnail in background thread"""
        try:
            thumbnail_path = self.manager.generate_enhanced_thumbnail(
                self.file_path, 
                self.entity_type, 
                self.entity_name, 
                self.task_name
            )
            
            if thumbnail_path and os.path.exists(thumbnail_path):
                self.thumbnail_generated.emit(self.file_path, thumbnail_path)
            else:
                self.generation_failed.emit(self.file_path, "Thumbnail generation failed")
                
        except Exception as e:
            self.generation_failed.emit(self.file_path, str(e))

