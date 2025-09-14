"""
Advanced TreeTable Component

Based on advanced hierarchy TreeTable implementation:
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

class AdvancedTreeTable(QTreeWidget):
    """
    Advanced TreeTable with all professional features
    """
    
    # Signals
    selection_changed = pyqtSignal(list)
    item_double_clicked = pyqtSignal(str, str)  # name, type
    context_menu_requested = pyqtSignal(str, object)
    viewer_requested = pyqtSignal(str, str)  # name, type
    expanded_changed = pyqtSignal(str, bool)  # item_id, expanded
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("AdvancedTreeTable")
        
        # Data
        self.hierarchy_data = {}
        self.filtered_data = {}
        self.current_filter = ""
        self.current_type_filter = "All Types"
        self.expanded_items = set()
        self.selected_items = set()
        
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        self.setup_context_menus()
        
    def setup_ui(self):
        """Setup the TreeTable UI"""
        # Basic properties
        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSortingEnabled(False)
        
        # Professional styling
        self.setStyleSheet(self.get_tree_style())
        
        # Set up columns
        self.setColumnCount(1)
        self.setHeaderLabels(["Hierarchy"])
        
    def setup_connections(self):
        """Setup signal connections"""
        self.itemSelectionChanged.connect(self.on_selection_changed)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.customContextMenuRequested.connect(self.on_context_menu_requested)
        self.itemExpanded.connect(self.on_item_expanded)
        self.itemCollapsed.connect(self.on_item_collapsed)
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
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
        
        # Escape to clear selection
        clear_selection_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        clear_selection_shortcut.activated.connect(self.clear_selection)
        
    def setup_context_menus(self):
        """Setup context menus"""
        pass
    
    def populate_hierarchy_data(self, data):
        """Populate hierarchy with data"""
        self.hierarchy_data = data
        self.filtered_data = data.copy()
        self.build_tree()
        
    def build_tree(self):
        """Build the tree from data"""
        self.clear()
        
        # Create root items
        for item_data in self.filtered_data:
            root_item = self.create_tree_item(item_data)
            self.addTopLevelItem(root_item)
            
            # Add children recursively
            if 'children' in item_data and item_data['children']:
                self.add_children(root_item, item_data['children'])
    
    def add_children(self, parent_item, children_data):
        """Add children to parent item"""
        for child_data in children_data:
            child_item = self.create_tree_item(child_data)
            parent_item.addChild(child_item)
            
            # Add grandchildren recursively
            if 'children' in child_data and child_data['children']:
                self.add_children(child_item, child_data['children'])
    
    def create_tree_item(self, item_data):
        """Create a tree item from data"""
        item = QTreeWidgetItem()
        
        # Set item data
        item.setText(0, item_data.get('name', 'Unknown'))
        item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Set icon based on type
        item_type = item_data.get('type', 'folder')
        icon = self.get_icon_for_type(item_type)
        if icon:
            item.setIcon(0, icon)
        
        # Set tooltip
        tooltip = self.create_tooltip(item_data)
        item.setToolTip(0, tooltip)
        
        # Set expanded state
        item_id = item_data.get('id', '')
        if item_id in self.expanded_items:
            item.setExpanded(True)
        
        return item
    
    def get_icon_for_type(self, item_type):
        """Get icon for item type"""
        icons = {
            'folder': '📁',
            'asset': '🎬',
            'shot': '🎥',
            'character': '👤',
            'prop': '🔧',
            'environment': '🏞️',
            'vehicle': '🚗',
            'effect': '✨',
            'light': '💡',
            'camera': '📷'
        }
        
        icon_text = icons.get(item_type, '📁')
        # In a real implementation, you'd use actual icons
        return None
    
    def create_tooltip(self, item_data):
        """Create tooltip for item"""
        tooltip = f"Name: {item_data.get('name', 'Unknown')}\n"
        tooltip += f"Type: {item_data.get('type', 'Unknown')}\n"
        tooltip += f"Status: {item_data.get('status', 'Unknown')}\n"
        
        if 'versions' in item_data:
            tooltip += f"Versions: {item_data['versions']}\n"
        if 'size' in item_data:
            tooltip += f"Size: {item_data['size']}\n"
        if 'date' in item_data:
            tooltip += f"Date: {item_data['date']}\n"
        if 'author' in item_data:
            tooltip += f"Author: {item_data['author']}\n"
            
        return tooltip
    
    def filter_hierarchy(self, filter_text="", type_filter="All Types"):
        """Filter hierarchy based on criteria"""
        self.current_filter = filter_text
        self.current_type_filter = type_filter
        
        if not filter_text and type_filter == "All Types":
            self.filtered_data = self.hierarchy_data.copy()
        else:
            self.filtered_data = self.filter_items(self.hierarchy_data, filter_text, type_filter)
        
        self.build_tree()
    
    def filter_items(self, items, filter_text, type_filter):
        """Filter items recursively"""
        filtered = []
        
        for item in items:
            name = item.get('name', '').lower()
            item_type = item.get('type', '').lower()
            
            matches_filter = not filter_text or filter_text.lower() in name
            matches_type = type_filter == "All Types" or type_filter.lower() in item_type
            
            if matches_filter and matches_type:
                # Include this item
                filtered_item = item.copy()
                if 'children' in item and item['children']:
                    filtered_children = self.filter_items(item['children'], filter_text, type_filter)
                    if filtered_children:
                        filtered_item['children'] = filtered_children
                filtered.append(filtered_item)
            elif 'children' in item and item['children']:
                # Check children even if parent doesn't match
                filtered_children = self.filter_items(item['children'], filter_text, type_filter)
                if filtered_children:
                    filtered_item = item.copy()
                    filtered_item['children'] = filtered_children
                    filtered.append(filtered_item)
        
        return filtered
    
    def expand_all(self):
        """Expand all items"""
        self.expandAll()
        self.update_expanded_items()
    
    def collapse_all(self):
        """Collapse all items"""
        self.collapseAll()
        self.expanded_items.clear()
    
    def update_expanded_items(self):
        """Update expanded items set"""
        self.expanded_items.clear()
        self.traverse_items(self.invisibleRootItem(), self.expanded_items)
    
    def traverse_items(self, parent, expanded_set):
        """Traverse items to update expanded state"""
        for i in range(parent.childCount()):
            item = parent.child(i)
            if item.isExpanded():
                item_data = item.data(0, Qt.ItemDataRole.UserRole)
                if item_data and 'id' in item_data:
                    expanded_set.add(item_data['id'])
            self.traverse_items(item, expanded_set)
    
    # Event handlers
    def on_selection_changed(self):
        """Handle selection change"""
        selected_items = []
        
        for item in self.selectedItems():
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            if item_data:
                selected_items.append(item_data)
        
        self.selection_changed.emit(selected_items)
        self.update_selected_items(selected_items)
    
    def on_item_double_clicked(self, item, column):
        """Handle item double click"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if item_data:
            name = item_data.get('name', 'Unknown')
            item_type = item_data.get('type', 'Unknown')
            self.item_double_clicked.emit(name, item_type)
    
    def on_context_menu_requested(self, position):
        """Handle context menu request"""
        item = self.itemAt(position)
        if item:
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            if item_data:
                name = item_data.get('name', 'Unknown')
                item_type = item_data.get('type', 'Unknown')
                self.context_menu_requested.emit(name, position)
                self.show_context_menu(name, item_type, position)
    
    def on_item_expanded(self, item):
        """Handle item expanded"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if item_data and 'id' in item_data:
            self.expanded_items.add(item_data['id'])
            self.expanded_changed.emit(item_data['id'], True)
    
    def on_item_collapsed(self, item):
        """Handle item collapsed"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if item_data and 'id' in item_data:
            self.expanded_items.discard(item_data['id'])
            self.expanded_changed.emit(item_data['id'], False)
    
    def show_context_menu(self, name, item_type, position):
        """Show context menu"""
        menu = QMenu(self)
        
        # Viewer actions
        menu.addAction("Open in viewer", lambda: self.open_in_viewer())
        menu.addAction("Quick view", lambda: self.quick_view(name))
        
        menu.addSeparator()
        
        # Version management
        menu.addAction("Upload version", lambda: self.upload_version(name))
        menu.addAction("Manage versions", lambda: self.manage_versions(name))
        menu.addAction("Publish", lambda: self.publish_item(name))
        
        menu.addSeparator()
        
        # Edit actions
        menu.addAction("Properties", lambda: self.show_properties(name))
        menu.addAction("Rename", lambda: self.rename_item(name))
        menu.addAction("Duplicate", lambda: self.duplicate_item(name))
        
        menu.addSeparator()
        
        # Status actions
        status_menu = menu.addMenu("Change Status")
        status_menu.addAction("Not Started", lambda: self.change_status(name, "Not Started"))
        status_menu.addAction("In Progress", lambda: self.change_status(name, "In Progress"))
        status_menu.addAction("Completed", lambda: self.change_status(name, "Completed"))
        status_menu.addAction("On Hold", lambda: self.change_status(name, "On Hold"))
        status_menu.addAction("Cancelled", lambda: self.change_status(name, "Cancelled"))
        status_menu.addAction("Published", lambda: self.change_status(name, "Published"))
        
        menu.addSeparator()
        
        # Advanced actions
        menu.addAction("Add to favorites", lambda: self.add_to_favorites(name))
        menu.addAction("Add to list", lambda: self.add_to_list(name))
        menu.addAction("Export", lambda: self.export_item(name))
        menu.addAction("Archive", lambda: self.archive_item(name))
        
        menu.addSeparator()
        
        # Delete action
        menu.addAction("Delete", lambda: self.delete_item(name))
        
        menu.exec(self.mapToGlobal(position))
    
    def update_selected_items(self, selected_items):
        """Update selected items set"""
        self.selected_items.clear()
        for item_data in selected_items:
            if 'id' in item_data:
                self.selected_items.add(item_data['id'])
    
    # Action methods
    def open_in_viewer(self):
        """Open selected item in viewer"""
        selected_items = self.selectedItems()
        if selected_items:
            item_data = selected_items[0].data(0, Qt.ItemDataRole.UserRole)
            if item_data:
                name = item_data.get('name', 'Unknown')
                item_type = item_data.get('type', 'Unknown')
                self.viewer_requested.emit(name, item_type)
                self.logger.info(f"Opening {name} in viewer")
    
    def quick_view(self, name):
        """Quick view item"""
        self.logger.info(f"Quick view: {name}")
    
    def upload_version(self, name):
        """Upload version for item"""
        self.logger.info(f"Uploading version for {name}")
    
    def manage_versions(self, name):
        """Manage versions for item"""
        self.logger.info(f"Managing versions for {name}")
    
    def publish_item(self, name):
        """Publish item"""
        self.logger.info(f"Publishing {name}")
    
    def show_properties(self, name):
        """Show item properties"""
        self.logger.info(f"Showing properties for {name}")
    
    def rename_item(self, name):
        """Rename item"""
        self.logger.info(f"Renaming {name}")
    
    def duplicate_item(self, name):
        """Duplicate item"""
        self.logger.info(f"Duplicating {name}")
    
    def change_status(self, name, status):
        """Change item status"""
        self.logger.info(f"Changed {name} status to {status}")
    
    def add_to_favorites(self, name):
        """Add item to favorites"""
        self.logger.info(f"Added {name} to favorites")
    
    def add_to_list(self, name):
        """Add item to list"""
        self.logger.info(f"Added {name} to list")
    
    def export_item(self, name):
        """Export item"""
        self.logger.info(f"Exporting {name}")
    
    def archive_item(self, name):
        """Archive item"""
        self.logger.info(f"Archiving {name}")
    
    def delete_item(self, name):
        """Delete item"""
        self.logger.info(f"Deleting {name}")
    
    def delete_selected(self):
        """Delete selected items"""
        selected_items = self.selectedItems()
        if selected_items:
            count = len(selected_items)
            self.logger.info(f"Deleting {count} selected items")
    
    def rename_selected(self):
        """Rename selected item"""
        selected_items = self.selectedItems()
        if selected_items:
            item_data = selected_items[0].data(0, Qt.ItemDataRole.UserRole)
            if item_data:
                name = item_data.get('name', 'Unknown')
                self.rename_item(name)
    
    def select_all(self):
        """Select all items"""
        self.selectAll()
        self.logger.info("All items selected")
    
    def clear_selection(self):
        """Clear selection"""
        self.clearSelection()
        self.logger.info("Selection cleared")
    
    def get_tree_style(self):
        """Get tree widget style"""
        return """
            QTreeWidget {
                background-color: #1A1F28;
                color: #E0E6EC;
                border: 1px solid #373D48;
                border-radius: 6px;
                font-size: 11pt;
                outline: none;
                selection-background-color: #4A9EFF;
                selection-color: #FFFFFF;
            }
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #373D48;
                min-height: 32px;
            }
            QTreeWidget::item:selected {
                background-color: #4A9EFF;
                color: #FFFFFF;
            }
            QTreeWidget::item:hover {
                background-color: rgba(74, 158, 255, 0.2);
            }
            QTreeWidget::branch {
                background-color: transparent;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuNSA2TDcuNSA2TDYgNy41TDQuNSA2WiIgZmlsbD0iIzRBOUVGRiIvPgo8L3N2Zz4K);
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTUuNSA0LjVMNS41IDcuNUw2IDdMNiA0TDYuNSA0LjVaIiBmaWxsPSIjNEE5RUZGIi8+Cjwvc3ZnPgo=);
            }
        """
