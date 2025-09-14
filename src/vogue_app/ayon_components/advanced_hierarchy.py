"""
Advanced Hierarchy Component

Implements all advanced hierarchy features:
- Advanced filtering and search
- Context menus with all actions
- Keyboard navigation
- Drag & drop
- Version management
- Viewer integration
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from vogue_core.logging_utils import get_logger
from ..vogue_components.advanced_tree_table import AdvancedTreeTable

class AdvancedHierarchy(QWidget):
    """
    Advanced Hierarchy with all features
    """
    
    # Signals
    selection_changed = pyqtSignal(list)
    item_double_clicked = pyqtSignal(str, str)  # name, type
    context_menu_requested = pyqtSignal(str, object)
    viewer_requested = pyqtSignal(str, str)  # name, type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("AdvancedHierarchy")
        
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        self.setup_context_menus()
        
        # Data
        self.hierarchy_data = {}
        self.filtered_data = {}
        self.current_filter = ""
        self.current_type_filter = "All Types"
        
    def setup_ui(self):
        """Setup the advanced hierarchy UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with advanced controls
        header = self.create_advanced_header()
        layout.addWidget(header)
        
        # Hierarchy tree with advanced features
        self.tree = self.create_advanced_tree()
        layout.addWidget(self.tree)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(self.get_status_style())
        layout.addWidget(self.status_label)
        
    def create_advanced_header(self):
        """Create advanced header with Ayon's Toolbar"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2A3441, stop:1 #1A2332);
                border: 1px solid #2A3441;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        
        # Top row - Search and filters
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        
        # Search box with advanced features
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter folders...")
        self.search_edit.setStyleSheet(self.get_input_style())
        self.search_edit.setClearButtonEnabled(True)
        top_row.addWidget(self.search_edit)
        
        # Folder type filter
        self.folder_type_filter = QComboBox()
        self.folder_type_filter.addItems([
            "All Types", "Shots", "Assets", "Characters", "Props", 
            "Environments", "Sequences", "Folders"
        ])
        self.folder_type_filter.setStyleSheet(self.get_combo_style())
        top_row.addWidget(self.folder_type_filter)
        
        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "All Status", "Active", "In Progress", "Completed", 
            "On Hold", "Cancelled", "Not Started"
        ])
        self.status_filter.setStyleSheet(self.get_combo_style())
        top_row.addWidget(self.status_filter)
        
        layout.addLayout(top_row)
        
        # Bottom row - Actions and controls
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)
        
        # Expand/Collapse buttons
        self.expand_btn = QPushButton("Expand All")
        self.collapse_btn = QPushButton("Collapse All")
        self.refresh_btn = QPushButton("🔄")
        
        for btn in [self.expand_btn, self.collapse_btn, self.refresh_btn]:
            btn.setStyleSheet(self.get_button_style())
            bottom_row.addWidget(btn)
        
        bottom_row.addStretch()
        
        # View options
        self.show_icons_check = QCheckBox("Show Icons")
        self.show_icons_check.setChecked(True)
        self.show_icons_check.setStyleSheet(self.get_checkbox_style())
        bottom_row.addWidget(self.show_icons_check)
        
        self.compact_view_check = QCheckBox("Compact View")
        self.compact_view_check.setStyleSheet(self.get_checkbox_style())
        bottom_row.addWidget(self.compact_view_check)
        
        layout.addLayout(bottom_row)
        
        return header
    
    def create_advanced_tree(self):
        """Create advanced hierarchy tree using AdvancedTreeTable"""
        tree = AdvancedTreeTable()
        return tree
    
    def setup_connections(self):
        """Setup signal connections"""
        # Tree selection - connect to AyonTreeTable signals
        self.tree.selection_changed.connect(self.on_selection_changed)
        self.tree.item_double_clicked.connect(self.on_item_double_clicked)
        self.tree.context_menu_requested.connect(self.on_context_menu_requested)
        self.tree.viewer_requested.connect(self.on_viewer_requested)
        
        # Search and filters
        self.search_edit.textChanged.connect(self.on_search_changed)
        self.folder_type_filter.currentTextChanged.connect(self.on_type_filter_changed)
        self.status_filter.currentTextChanged.connect(self.on_status_filter_changed)
        
        # Buttons
        self.expand_btn.clicked.connect(self.expand_all)
        self.collapse_btn.clicked.connect(self.collapse_all)
        self.refresh_btn.clicked.connect(self.refresh_hierarchy)
        
        # View options
        self.show_icons_check.toggled.connect(self.toggle_icons)
        self.compact_view_check.toggled.connect(self.toggle_compact_view)
    
    def setup_shortcuts(self):
        """Setup advanced keyboard shortcuts"""
        # Space bar for viewer
        space_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        space_shortcut.activated.connect(self.open_in_viewer)
        
        # Delete for removal
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        delete_shortcut.activated.connect(self.delete_selected)
        
        # F2 for rename
        rename_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F2), self)
        rename_shortcut.activated.connect(self.rename_selected)
        
        # Ctrl+A for select all
        select_all_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        select_all_shortcut.activated.connect(self.select_all)
        
        # Ctrl+F for focus search
        focus_search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        focus_search_shortcut.activated.connect(self.focus_search)
        
        # Escape to clear selection
        clear_selection_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        clear_selection_shortcut.activated.connect(self.clear_selection)
        
        # Arrow keys for navigation
        self.setup_arrow_navigation()
    
    def setup_arrow_navigation(self):
        """Setup arrow key navigation"""
        # Up/Down for item navigation
        up_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        up_shortcut.activated.connect(self.navigate_up)
        
        down_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        down_shortcut.activated.connect(self.navigate_down)
        
        # Left/Right for expand/collapse
        left_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        left_shortcut.activated.connect(self.collapse_current)
        
        right_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        right_shortcut.activated.connect(self.expand_current)
    
    def setup_context_menus(self):
        """Setup advanced context menus"""
        # This will be handled by the context menu system
        pass
    
    def populate_sample_data(self):
        """Populate with advanced sample data"""
        # Sample hierarchy data for AyonTreeTable
        hierarchy_data = [
            {
                "id": "project",
                "name": "My Project",
                "type": "project",
                "status": "Active",
                "versions": "0",
                "size": "0 KB",
                "date": "2024-01-15",
                "children": [
                    {
                        "id": "shots",
                        "name": "Shots",
                        "type": "folder",
                        "status": "Active",
                        "versions": "0",
                        "size": "0 KB",
                        "date": "2024-01-15",
                        "children": [
                            {
                                "id": "sq01",
                                "name": "SQ01",
                                "type": "sequence",
                                "status": "In Progress",
                                "versions": "2",
                                "size": "1.2 MB",
                                "date": "2024-01-16",
                                "children": [
                                    {
                                        "id": "sh001",
                                        "name": "SH001",
                                        "type": "shot",
                                        "status": "Completed",
                                        "versions": "3",
                                        "size": "850 KB",
                                        "date": "2024-01-17"
                                    },
                                    {
                                        "id": "sh002",
                                        "name": "SH002",
                                        "type": "shot",
                                        "status": "In Progress",
                                        "versions": "1",
                                        "size": "420 KB",
                                        "date": "2024-01-18"
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "id": "assets",
                        "name": "Assets",
                        "type": "folder",
                        "status": "Active",
                        "versions": "0",
                        "size": "0 KB",
                        "date": "2024-01-15",
                        "children": [
                            {
                                "id": "characters",
                                "name": "Characters",
                                "type": "folder",
                                "status": "Active",
                                "versions": "0",
                                "size": "0 KB",
                                "date": "2024-01-15",
                                "children": [
                                    {
                                        "id": "char_01",
                                        "name": "Char_01",
                                        "type": "character",
                                        "status": "In Progress",
                                        "versions": "2",
                                        "size": "2.1 MB",
                                        "date": "2024-01-19"
                                    }
                                ]
                            },
                            {
                                "id": "props",
                                "name": "Props",
                                "type": "folder",
                                "status": "Active",
                                "versions": "0",
                                "size": "0 KB",
                                "date": "2024-01-15",
                                "children": [
                                    {
                                        "id": "prop_chair",
                                        "name": "Prop_Chair",
                                        "type": "prop",
                                        "status": "Completed",
                                        "versions": "1",
                                        "size": "650 KB",
                                        "date": "2024-01-20"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        
        self.tree.populate_hierarchy_data(hierarchy_data)
        self.update_status()
    
    def on_viewer_requested(self, name, item_type):
        """Handle viewer request from AyonTreeTable"""
        self.viewer_requested.emit(name, item_type)
    
    def on_search_changed(self, text):
        """Handle search text change"""
        self.tree.filter_hierarchy(text, self.current_type_filter)
    
    def on_type_filter_changed(self, text):
        """Handle type filter change"""
        self.current_type_filter = text
        self.tree.filter_hierarchy(self.current_filter, text)
    
    def on_status_filter_changed(self, text):
        """Handle status filter change"""
        # Status filtering would be implemented in AyonTreeTable
        pass
    
    def expand_all(self):
        """Expand all items"""
        self.tree.expand_all()
        self.update_status("All items expanded")
    
    def collapse_all(self):
        """Collapse all items"""
        self.tree.collapse_all()
        self.update_status("All items collapsed")
    
    def refresh_hierarchy(self):
        """Refresh hierarchy data"""
        self.logger.info("Refreshing hierarchy...")
        self.update_status("Refreshing...")
        # In a real implementation, this would reload data
        QTimer.singleShot(1000, lambda: self.update_status("Refreshed"))
    
    def toggle_icons(self, show):
        """Toggle icon display"""
        # Icons are handled by AyonTreeTable
        pass
    
    def toggle_compact_view(self, compact):
        """Toggle compact view"""
        # Compact view would be handled by AyonTreeTable
        pass
    
    def update_status(self, message=None):
        """Update status label"""
        if message:
            self.status_label.setText(message)
        else:
            # Get status from AyonTreeTable
            self.status_label.setText("Ready")
    
    # Event handlers - these are now handled by AyonTreeTable
    def on_selection_changed(self, items):
        """Handle selection change from AyonTreeTable"""
        self.selection_changed.emit(items)
        self.update_status()
    
    def on_item_double_clicked(self, name, item_type):
        """Handle item double click from AyonTreeTable"""
        self.item_double_clicked.emit(name, item_type)
    
    def on_context_menu_requested(self, name, position):
        """Handle context menu request from AyonTreeTable"""
        self.context_menu_requested.emit(name, position)
    
    def open_in_viewer(self):
        """Open selected item in viewer"""
        self.tree.open_in_viewer()
    
    def quick_view(self, item):
        """Quick view item"""
        self.tree.quick_view(item)
    
    def upload_version(self, item):
        """Upload version for item"""
        self.tree.upload_version(item)
    
    def manage_versions(self, item):
        """Manage versions for item"""
        self.tree.manage_versions(item)
    
    def create_folder(self, parent_item):
        """Create new folder"""
        self.tree.create_folder(parent_item)
    
    def create_asset(self, parent_item):
        """Create new asset"""
        self.tree.create_asset(parent_item)
    
    def create_shot(self, parent_item):
        """Create new shot"""
        self.tree.create_shot(parent_item)
    
    def show_properties(self, item):
        """Show item properties"""
        self.tree.show_properties(item)
    
    def rename_item(self, item):
        """Rename item"""
        self.tree.rename_item(item)
    
    def duplicate_item(self, item):
        """Duplicate item"""
        self.tree.duplicate_item(item)
    
    def change_status(self, item, status):
        """Change item status"""
        self.tree.change_status(item, status)
    
    def add_to_favorites(self, item):
        """Add item to favorites"""
        self.tree.add_to_favorites(item)
    
    def add_to_list(self, item):
        """Add item to list"""
        self.tree.add_to_list(item)
    
    def export_item(self, item):
        """Export item"""
        self.tree.export_item(item)
    
    def delete_item(self, item):
        """Delete item"""
        self.tree.delete_item(item)
    
    def delete_selected(self):
        """Delete selected items"""
        self.tree.delete_selected()
    
    def rename_selected(self):
        """Rename selected item"""
        self.tree.rename_selected()
    
    def select_all(self):
        """Select all items"""
        self.tree.select_all()
    
    def focus_search(self):
        """Focus search box"""
        self.search_edit.setFocus()
        self.search_edit.selectAll()
    
    def clear_selection(self):
        """Clear selection"""
        self.tree.clear_selection()
    
    def navigate_up(self):
        """Navigate up"""
        self.tree.navigate_up()
    
    def navigate_down(self):
        """Navigate down"""
        self.tree.navigate_down()
    
    def collapse_current(self):
        """Collapse current item"""
        self.tree.collapse_current()
    
    def expand_current(self):
        """Expand current item"""
        self.tree.expand_current()
    
    # Styling methods
    def get_input_style(self):
        """Get input style"""
        return """
            QLineEdit {
                background-color: #1A2332;
                color: #E0E0E0;
                border: 1px solid #2A3441;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #73C2FB;
            }
        """
    
    def get_combo_style(self):
        """Get combo box style"""
        return """
            QComboBox {
                background-color: #1A2332;
                color: #E0E0E0;
                border: 1px solid #2A3441;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 10px;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: #73C2FB;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #73C2FB;
                margin-right: 5px;
            }
        """
    
    def get_button_style(self):
        """Get button style"""
        return """
            QPushButton {
                background-color: #2A3441;
                color: #E0E0E0;
                border: 1px solid #2A3441;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #3A75A3;
                border-color: #73C2FB;
            }
            QPushButton:pressed {
                background-color: #73C2FB;
                color: #12181F;
            }
        """
    
    def get_checkbox_style(self):
        """Get checkbox style"""
        return """
            QCheckBox {
                color: #E0E0E0;
                font-size: 10px;
            }
            QCheckBox::indicator {
                width: 12px;
                height: 12px;
                border: 1px solid #2A3441;
                border-radius: 2px;
                background-color: #1A2332;
            }
            QCheckBox::indicator:checked {
                background-color: #73C2FB;
                border-color: #73C2FB;
            }
        """
    
    def get_status_style(self):
        """Get status label style"""
        return """
            QLabel {
                color: #788490;
                font-size: 10px;
                padding: 4px 8px;
                background-color: #1A2332;
                border-top: 1px solid #2A3441;
            }
        """
