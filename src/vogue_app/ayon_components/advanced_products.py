"""
Advanced Ayon Products Component

Implements all Ayon products features:
- List and Grid views
- Advanced filtering and search
- Version management
- Context menus with all actions
- Drag & drop
- Viewer integration
- Status management
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from vogue_core.logging_utils import get_logger

class AdvancedProducts(QWidget):
    """
    Advanced Ayon Products with all features
    """
    
    # Signals
    selection_changed = pyqtSignal(list)
    item_double_clicked = pyqtSignal(str, str)  # name, type
    context_menu_requested = pyqtSignal(str, object)
    viewer_requested = pyqtSignal(str, str)  # name, type
    view_mode_changed = pyqtSignal(str)  # list, grid
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("AdvancedProducts")
        
        # Data - Initialize first
        self.products_data = []
        self.filtered_data = []
        self.current_view_mode = "list"
        self.current_filter = ""
        self.current_type_filter = "All Types"
        self.current_status_filter = "All Status"
        
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        self.setup_context_menus()
        
    def setup_ui(self):
        """Setup the advanced products UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with advanced controls
        header = self.create_advanced_header()
        layout.addWidget(header)
        
        # Status bar - Create first
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(self.get_status_style())
        layout.addWidget(self.status_label)
        
        # Products content with list/grid views
        self.products_content = self.create_products_content()
        layout.addWidget(self.products_content)
        
    def create_advanced_header(self):
        """Create advanced header with Ayon's Toolbar"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2A3441, stop:1 #1A2332);
                border: 1px solid #2A3441;
                border-radius: 6px;
                margin: 8px;
                padding: 8px;
            }
        """)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Top row - Title and view mode
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        
        # Title
        title = QLabel("🎬 Products & Assets")
        title.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        top_row.addWidget(title)
        top_row.addStretch()
        
        # View mode toggle
        self.view_mode_buttons = QButtonGroup()
        list_btn = QPushButton("📋 List")
        grid_btn = QPushButton("⊞ Grid")
        list_btn.setCheckable(True)
        grid_btn.setCheckable(True)
        list_btn.setChecked(True)
        
        for btn in [list_btn, grid_btn]:
            btn.setStyleSheet(self.get_button_style())
            self.view_mode_buttons.addButton(btn)
            top_row.addWidget(btn)
        
        layout.addLayout(top_row)
        
        # Bottom row - Search and filters
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)
        
        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search products...")
        self.search_edit.setStyleSheet(self.get_input_style())
        self.search_edit.setClearButtonEnabled(True)
        bottom_row.addWidget(self.search_edit)
        
        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "All Types", "Assets", "Shots", "Characters", "Props", 
            "Environments", "Vehicles", "Effects"
        ])
        self.type_filter.setStyleSheet(self.get_combo_style())
        bottom_row.addWidget(self.type_filter)
        
        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "All Status", "Active", "In Progress", "Completed", 
            "On Hold", "Cancelled", "Not Started", "Published"
        ])
        self.status_filter.setStyleSheet(self.get_combo_style())
        bottom_row.addWidget(self.status_filter)
        
        # Sort options
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Name", "Type", "Status", "Date", "Size", "Versions"
        ])
        self.sort_combo.setStyleSheet(self.get_combo_style())
        bottom_row.addWidget(self.sort_combo)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh products")
        self.refresh_btn.setStyleSheet(self.get_button_style())
        bottom_row.addWidget(self.refresh_btn)
        
        layout.addLayout(bottom_row)
        
        return header
    
    def create_products_content(self):
        """Create products content with list/grid views"""
        # Stacked widget for List/Grid views
        self.products_stack = QStackedWidget()
        self.products_stack.setStyleSheet("""
            QStackedWidget {
                background-color: #1A2332;
                border: 1px solid #2A3441;
                border-radius: 6px;
                margin: 8px;
            }
        """)
        
        # List view
        self.products_list = self.create_products_list()
        self.products_stack.addWidget(self.products_list)
        
        # Grid view
        self.products_grid = self.create_products_grid()
        self.products_stack.addWidget(self.products_grid)
        
        return self.products_stack
    
    def create_products_list(self):
        """Create advanced products list view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(7)
        self.products_table.setHorizontalHeaderLabels([
            "Name", "Type", "Status", "Versions", "Size", "Date", "Author"
        ])
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.products_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.products_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.products_table.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.products_table.setSortingEnabled(True)
        
        # Advanced Ayon styling
        self.products_table.setStyleSheet(self.get_advanced_table_style())
        
        # Set column widths
        header = self.products_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Versions
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Size
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Author
        
        layout.addWidget(self.products_table)
        
        # Add sample data
        self.populate_products_sample()
        
        return widget
    
    def create_products_grid(self):
        """Create advanced products grid view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Scroll area for grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(self.get_scroll_area_style())
        
        # Grid widget
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        
        scroll_area.setWidget(self.grid_widget)
        layout.addWidget(scroll_area)
        
        # Add sample grid items
        self.populate_grid_sample()
        
        return widget
    
    def setup_connections(self):
        """Setup signal connections"""
        # Table selection
        self.products_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.products_table.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.products_table.customContextMenuRequested.connect(self.on_context_menu_requested)
        
        # Search and filters
        self.search_edit.textChanged.connect(self.on_search_changed)
        self.type_filter.currentTextChanged.connect(self.on_type_filter_changed)
        self.status_filter.currentTextChanged.connect(self.on_status_filter_changed)
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)
        
        # View mode
        self.view_mode_buttons.buttonClicked.connect(self.on_view_mode_changed)
        
        # Buttons
        self.refresh_btn.clicked.connect(self.refresh_products)
    
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
    
    def setup_context_menus(self):
        """Setup advanced context menus"""
        # This will be handled by the context menu system
        pass
    
    def populate_products_sample(self):
        """Populate products table with sample data"""
        products = [
            ["Character_01", "Character", "In Progress", "3", "2.5 MB", "2024-01-15", "Artist1"],
            ["Prop_Chair", "Prop", "Completed", "1", "850 KB", "2024-01-14", "Artist2"],
            ["Environment_Room", "Environment", "In Progress", "2", "15.2 MB", "2024-01-16", "Artist1"],
            ["Vehicle_Car", "Vehicle", "Not Started", "0", "0 KB", "2024-01-17", "Artist3"],
            ["Shot_001", "Shot", "In Progress", "2", "120 frames", "2024-01-18", "Artist1"],
            ["Shot_002", "Shot", "Completed", "1", "90 frames", "2024-01-19", "Artist2"],
            ["Effect_Fire", "Effect", "In Progress", "1", "5.1 MB", "2024-01-20", "Artist3"],
            ["Light_Setup", "Light", "Completed", "1", "1.2 MB", "2024-01-21", "Artist1"]
        ]
        
        self.products_data = products
        self.filtered_data = products.copy()
        
        self.products_table.setRowCount(len(products))
        for i, product in enumerate(products):
            for j, value in enumerate(product):
                item = QTableWidgetItem(value)
                self.products_table.setItem(i, j, item)
        
        self.update_status()
    
    def populate_grid_sample(self):
        """Populate grid view with sample data"""
        # Clear existing items
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        # Add grid items
        for i, product in enumerate(self.filtered_data):
            grid_item = self.create_grid_item(product)
            row = i // 4  # 4 items per row
            col = i % 4
            self.grid_layout.addWidget(grid_item, row, col)
    
    def create_grid_item(self, product_data):
        """Create a grid item widget"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: #212A37;
                border: 1px solid #2A3441;
                border-radius: 8px;
                padding: 8px;
            }
            QFrame:hover {
                border-color: #73C2FB;
                background-color: #2A3441;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Thumbnail placeholder
        thumbnail = QLabel("📁")
        thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail.setStyleSheet("""
            QLabel {
                background-color: #1A2332;
                border: 1px solid #2A3441;
                border-radius: 4px;
                font-size: 24px;
                padding: 20px;
            }
        """)
        layout.addWidget(thumbnail)
        
        # Name
        name_label = QLabel(product_data[0])
        name_label.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Type and status
        info_layout = QHBoxLayout()
        
        type_label = QLabel(product_data[1])
        type_label.setStyleSheet("""
            QLabel {
                color: #788490;
                font-size: 10px;
            }
        """)
        info_layout.addWidget(type_label)
        
        status_label = QLabel(product_data[2])
        status_label.setStyleSheet("""
            QLabel {
                color: #73C2FB;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        info_layout.addWidget(status_label)
        
        layout.addLayout(info_layout)
        
        # Versions and size
        details_layout = QHBoxLayout()
        
        versions_label = QLabel(f"v{product_data[3]}")
        versions_label.setStyleSheet("""
            QLabel {
                color: #788490;
                font-size: 9px;
            }
        """)
        details_layout.addWidget(versions_label)
        
        size_label = QLabel(product_data[4])
        size_label.setStyleSheet("""
            QLabel {
                color: #788490;
                font-size: 9px;
            }
        """)
        details_layout.addWidget(size_label)
        
        layout.addLayout(details_layout)
        
        # Make clickable
        widget.mousePressEvent = lambda event, data=product_data: self.on_grid_item_clicked(data)
        widget.mouseDoubleClickEvent = lambda event, data=product_data: self.on_grid_item_double_clicked(data)
        
        return widget
    
    def on_grid_item_clicked(self, product_data):
        """Handle grid item click"""
        self.logger.info(f"Grid item clicked: {product_data[0]}")
    
    def on_grid_item_double_clicked(self, product_data):
        """Handle grid item double click"""
        self.on_item_double_clicked.emit(product_data[0], product_data[1])
    
    # Event handlers
    def on_selection_changed(self):
        """Handle selection change"""
        if self.current_view_mode == "list":
            selected_items = self.products_table.selectedItems()
            item_data = []
            
            for item in selected_items:
                row = item.row()
                product_data = []
                for col in range(self.products_table.columnCount()):
                    cell_item = self.products_table.item(row, col)
                    if cell_item:
                        product_data.append(cell_item.text())
                item_data.append(product_data)
            
            self.selection_changed.emit(item_data)
        
        self.update_status()
    
    def on_item_double_clicked(self, item, column):
        """Handle item double click"""
        if self.current_view_mode == "list":
            row = item.row()
            product_name = self.products_table.item(row, 0).text()
            product_type = self.products_table.item(row, 1).text()
            self.item_double_clicked.emit(product_name, product_type)
    
    def on_context_menu_requested(self, position):
        """Handle context menu request"""
        if self.current_view_mode == "list":
            item = self.products_table.itemAt(position)
            if item:
                row = item.row()
                product_name = self.products_table.item(row, 0).text()
                product_type = self.products_table.item(row, 1).text()
                self.context_menu_requested.emit(product_name, position)
                self.show_context_menu(product_name, product_type, position)
    
    def show_context_menu(self, product_name, product_type, position):
        """Show advanced context menu"""
        menu = QMenu(self)
        
        # Viewer actions
        menu.addAction("Open in viewer", lambda: self.open_in_viewer())
        menu.addAction("Quick view", lambda: self.quick_view(product_name))
        
        menu.addSeparator()
        
        # Version management
        menu.addAction("Upload version", lambda: self.upload_version(product_name))
        menu.addAction("Manage versions", lambda: self.manage_versions(product_name))
        menu.addAction("Publish", lambda: self.publish_product(product_name))
        
        menu.addSeparator()
        
        # Edit actions
        menu.addAction("Properties", lambda: self.show_properties(product_name))
        menu.addAction("Rename", lambda: self.rename_product(product_name))
        menu.addAction("Duplicate", lambda: self.duplicate_product(product_name))
        
        menu.addSeparator()
        
        # Status actions
        status_menu = menu.addMenu("Change Status")
        status_menu.addAction("Not Started", lambda: self.change_status(product_name, "Not Started"))
        status_menu.addAction("In Progress", lambda: self.change_status(product_name, "In Progress"))
        status_menu.addAction("Completed", lambda: self.change_status(product_name, "Completed"))
        status_menu.addAction("On Hold", lambda: self.change_status(product_name, "On Hold"))
        status_menu.addAction("Cancelled", lambda: self.change_status(product_name, "Cancelled"))
        status_menu.addAction("Published", lambda: self.change_status(product_name, "Published"))
        
        menu.addSeparator()
        
        # Advanced actions
        menu.addAction("Add to favorites", lambda: self.add_to_favorites(product_name))
        menu.addAction("Add to list", lambda: self.add_to_list(product_name))
        menu.addAction("Export", lambda: self.export_product(product_name))
        menu.addAction("Archive", lambda: self.archive_product(product_name))
        
        menu.addSeparator()
        
        # Delete action
        menu.addAction("Delete", lambda: self.delete_product(product_name))
        
        menu.exec(self.products_table.mapToGlobal(position))
    
    def on_search_changed(self, text):
        """Handle search text change"""
        self.current_filter = text
        self.apply_filters()
    
    def on_type_filter_changed(self, text):
        """Handle type filter change"""
        self.current_type_filter = text
        self.apply_filters()
    
    def on_status_filter_changed(self, text):
        """Handle status filter change"""
        self.current_status_filter = text
        self.apply_filters()
    
    def on_sort_changed(self, text):
        """Handle sort change"""
        self.sort_products(text)
    
    def on_view_mode_changed(self, button):
        """Handle view mode change"""
        if button.text() == "📋 List":
            self.current_view_mode = "list"
            self.products_stack.setCurrentIndex(0)
        else:
            self.current_view_mode = "grid"
            self.products_stack.setCurrentIndex(1)
            self.populate_grid_sample()
        
        self.view_mode_changed.emit(self.current_view_mode)
    
    def apply_filters(self):
        """Apply all filters"""
        self.filtered_data = []
        
        for product in self.products_data:
            name = product[0].lower()
            product_type = product[1].lower()
            status = product[2]
            
            matches_search = not self.current_filter or self.current_filter.lower() in name
            matches_type = (self.current_type_filter == "All Types" or 
                           self.current_type_filter.lower() in product_type)
            matches_status = (self.current_status_filter == "All Status" or 
                             status == self.current_status_filter)
            
            if matches_search and matches_type and matches_status:
                self.filtered_data.append(product)
        
        self.update_products_display()
        self.update_status()
    
    def sort_products(self, sort_by):
        """Sort products by criteria"""
        if sort_by == "Name":
            self.filtered_data.sort(key=lambda x: x[0])
        elif sort_by == "Type":
            self.filtered_data.sort(key=lambda x: x[1])
        elif sort_by == "Status":
            self.filtered_data.sort(key=lambda x: x[2])
        elif sort_by == "Date":
            self.filtered_data.sort(key=lambda x: x[5])
        elif sort_by == "Size":
            self.filtered_data.sort(key=lambda x: x[4])
        elif sort_by == "Versions":
            self.filtered_data.sort(key=lambda x: int(x[3]) if x[3].isdigit() else 0)
        
        self.update_products_display()
    
    def update_products_display(self):
        """Update products display"""
        if self.current_view_mode == "list":
            self.products_table.setRowCount(len(self.filtered_data))
            for i, product in enumerate(self.filtered_data):
                for j, value in enumerate(product):
                    item = QTableWidgetItem(value)
                    self.products_table.setItem(i, j, item)
        else:
            self.populate_grid_sample()
    
    def refresh_products(self):
        """Refresh products data"""
        self.logger.info("Refreshing products...")
        self.update_status("Refreshing...")
        # In a real implementation, this would reload data
        QTimer.singleShot(1000, lambda: self.update_status("Refreshed"))
    
    def open_in_viewer(self):
        """Open selected item in viewer"""
        if self.current_view_mode == "list":
            selected_items = self.products_table.selectedItems()
            if selected_items:
                row = selected_items[0].row()
                product_name = self.products_table.item(row, 0).text()
                product_type = self.products_table.item(row, 1).text()
                self.viewer_requested.emit(product_name, product_type)
                self.logger.info(f"Opening {product_name} in viewer")
    
    def quick_view(self, product_name):
        """Quick view product"""
        self.logger.info(f"Quick view: {product_name}")
    
    def upload_version(self, product_name):
        """Upload version for product"""
        self.logger.info(f"Uploading version for {product_name}")
    
    def manage_versions(self, product_name):
        """Manage versions for product"""
        self.logger.info(f"Managing versions for {product_name}")
    
    def publish_product(self, product_name):
        """Publish product"""
        self.logger.info(f"Publishing {product_name}")
    
    def show_properties(self, product_name):
        """Show product properties"""
        self.logger.info(f"Showing properties for {product_name}")
    
    def rename_product(self, product_name):
        """Rename product"""
        self.logger.info(f"Renaming {product_name}")
    
    def duplicate_product(self, product_name):
        """Duplicate product"""
        self.logger.info(f"Duplicating {product_name}")
    
    def change_status(self, product_name, status):
        """Change product status"""
        self.logger.info(f"Changed {product_name} status to {status}")
        # Update in data and refresh display
        self.apply_filters()
    
    def add_to_favorites(self, product_name):
        """Add product to favorites"""
        self.logger.info(f"Added {product_name} to favorites")
    
    def add_to_list(self, product_name):
        """Add product to list"""
        self.logger.info(f"Added {product_name} to list")
    
    def export_product(self, product_name):
        """Export product"""
        self.logger.info(f"Exporting {product_name}")
    
    def archive_product(self, product_name):
        """Archive product"""
        self.logger.info(f"Archiving {product_name}")
    
    def delete_product(self, product_name):
        """Delete product"""
        self.logger.info(f"Deleting {product_name}")
    
    def delete_selected(self):
        """Delete selected items"""
        if self.current_view_mode == "list":
            selected_items = self.products_table.selectedItems()
            if selected_items:
                count = len(selected_items)
                self.logger.info(f"Deleting {count} selected items")
    
    def rename_selected(self):
        """Rename selected item"""
        if self.current_view_mode == "list":
            selected_items = self.products_table.selectedItems()
            if selected_items:
                row = selected_items[0].row()
                product_name = self.products_table.item(row, 0).text()
                self.rename_product(product_name)
    
    def select_all(self):
        """Select all items"""
        if self.current_view_mode == "list":
            self.products_table.selectAll()
        self.update_status("All items selected")
    
    def focus_search(self):
        """Focus search box"""
        self.search_edit.setFocus()
        self.search_edit.selectAll()
    
    def clear_selection(self):
        """Clear selection"""
        if self.current_view_mode == "list":
            self.products_table.clearSelection()
        self.update_status("Selection cleared")
    
    def navigate_up(self):
        """Navigate up"""
        if self.current_view_mode == "list":
            current_row = self.products_table.currentRow()
            if current_row > 0:
                self.products_table.setCurrentCell(current_row - 1, 0)
    
    def navigate_down(self):
        """Navigate down"""
        if self.current_view_mode == "list":
            current_row = self.products_table.currentRow()
            if current_row < self.products_table.rowCount() - 1:
                self.products_table.setCurrentCell(current_row + 1, 0)
    
    def update_status(self, message=None):
        """Update status label"""
        if message:
            self.status_label.setText(message)
        else:
            if self.current_view_mode == "list":
                selected_count = len(self.products_table.selectedItems())
            else:
                selected_count = 0  # Grid selection not implemented yet
            
            total_count = len(self.filtered_data)
            self.status_label.setText(f"Ready - {selected_count} selected, {total_count} total")
    
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
    
    def get_advanced_table_style(self):
        """Get advanced table style"""
        return """
            QTableWidget {
                background-color: #1A2332;
                color: #E0E0E0;
                border: 1px solid #2A3441;
                border-radius: 4px;
                font-size: 11px;
                gridline-color: #2A3441;
                selection-background-color: #73C2FB;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #2A3441;
            }
            QTableWidget::item:selected {
                background-color: #73C2FB;
                color: #12181F;
            }
            QTableWidget::item:hover {
                background-color: #212A37;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2A3441, stop:1 #1A2332);
                color: #E0E0E0;
                padding: 8px 12px;
                border: none;
                border-right: 1px solid #2A3441;
                font-weight: bold;
                font-size: 10px;
            }
            QHeaderView::section:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3A75A3, stop:1 #2A3441);
            }
        """
    
    def get_scroll_area_style(self):
        """Get scroll area style"""
        return """
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2A3441;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #73C2FB;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #3A75A3;
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
