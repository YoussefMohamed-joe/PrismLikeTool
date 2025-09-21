"""
QSS (Qt Style Sheets) builder for Vogue Manager

Builds Qt stylesheets from the color palette.
"""

from .colors import COLORS


def build_qss(colors: dict = None) -> str:
    """
    Build QSS stylesheet from color palette
    
    Args:
        colors: Color dictionary (uses default if None)
        
    Returns:
        QSS stylesheet string
    """
    if colors is None:
        colors = COLORS
    
    qss = f"""
    /* Main Window - Calm Blue Dark Theme */
    QMainWindow {{
        background-color: {colors['bg']};
        color: {colors['fg']};
        font-family: "Segoe UI", "Roboto", "Arial", sans-serif;
        font-size: 13px;
    }}

    /* Central Widget */
    QWidget {{
        background-color: transparent;
        color: {colors['fg']};
    }}
    
    /* Menu Bar - Calm Blue Style */
    QMenuBar {{
        background-color: {colors['surface']};
        color: {colors['fg']};
        border-bottom: 1px solid {colors['accent']};
        padding: 6px 12px;
        font-weight: 500;
        font-size: 13px;
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: 8px 14px;
        border-radius: 6px;
        margin: 2px;
        border: 1px solid transparent;
    }}
    
    QMenuBar::item:selected {{
        background-color: {colors['accent']};
        color: white;
        font-weight: 600;
        border: 1px solid {colors['accent_hover']};
    }}
    
    QMenuBar::item:hover {{
        background-color: {colors['hover']};
        border: 1px solid {colors['accent']};
    }}
    
    /* Menu - Calm Blue Style */
    QMenu {{
        background-color: {colors['surface_high']};
        color: {colors['fg']};
        border: 1px solid {colors['accent']};
        border-radius: 8px;
        padding: 8px;
        font-size: 13px;
        font-weight: 500;
    }}
    
    QMenu::item {{
        padding: 10px 16px;
        border-radius: 6px;
        margin: 2px;
        border: 1px solid transparent;
    }}
    
    QMenu::item:selected {{
        background-color: {colors['accent']};
        color: white;
        font-weight: 600;
        border: 1px solid {colors['accent_hover']};
    }}
    
    QMenu::item:hover {{
        background-color: {colors['hover']};
        border: 1px solid {colors['accent']};
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {colors['accent']};
        margin: 6px 10px;
    }}
    
    /* Tool Bar - Ayon Style */
    QToolBar {{
        background-color: {colors['surface']};
        border: none;
        border-bottom: 1px solid {colors['outline']};
        spacing: 4px;
        padding: 8px;
    }}
    
    QToolButton {{
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 8px 12px;
        margin: 2px;
        font-weight: 500;
    }}
    
    QToolButton:hover {{
        background-color: {colors['hover']};
        border: 1px solid {colors['accent']};
    }}
    
    QToolButton:pressed {{
        background-color: {colors['accent']};
        color: white;
    }}
    
    /* Status Bar - Ayon Style */
    QStatusBar {{
        background-color: {colors['surface']};
        color: {colors['fg_variant']};
        border-top: 1px solid {colors['outline']};
        padding: 4px 12px;
        font-size: 12px;
    }}
    
    /* Tab Widget - Calm Blue Style */
    QTabWidget::pane {{
        border: 1px solid {colors['accent']};
        background-color: {colors['surface_high']};
        border-radius: 8px;
    }}

    QTabBar::tab {{
        background-color: {colors['surface']};
        color: {colors['fg_variant']};
        padding: 12px 24px;
        margin-right: 2px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        border: 1px solid {colors['outline']};
        border-bottom: none;
        font-weight: 500;
        font-size: 13px;
        min-width: 100px;
    }}

    QTabBar::tab:selected {{
        background-color: {colors['accent']};
        color: white;
        border: 1px solid {colors['accent']};
        border-bottom: 2px solid {colors['accent']};
        font-weight: 600;
    }}

    QTabBar::tab:hover {{
        background-color: {colors['hover']};
        color: {colors['fg']};
        border: 1px solid {colors['accent']};
    }}

    QTabBar::tab:!selected {{
        margin-top: 2px;
    }}
    
    /* Push Buttons - Calm Blue Style */
    QPushButton {{
        background-color: {colors['accent']};
        color: white;
        border: 1px solid {colors['accent']};
        border-radius: 8px;
        padding: 12px 20px;
        font-weight: 600;
        font-size: 13px;
        min-height: 20px;
        font-family: "Segoe UI", "Roboto", sans-serif;
    }}

    QPushButton:hover {{
        background-color: {colors['accent_hover']};
        border: 1px solid {colors['accent_hover']};
    }}

    QPushButton:pressed {{
        background-color: {colors['accent_active']};
        border: 1px solid {colors['accent_active']};
    }}

    QPushButton:disabled {{
        background-color: {colors['surface']};
        color: {colors['muted']};
        border: 1px solid {colors['outline']};
    }}

    /* Primary Buttons - Ayon Style */
    QPushButton[class="primary"] {{
        background-color: {colors['accent']};
        color: white;
        border: 2px solid {colors['accent']};
        font-weight: 700;
        font-size: 14px;
        padding: 14px 24px;
    }}

    QPushButton[class="primary"]:hover {{
        background-color: {colors['accent_hover']};
        border-color: {colors['accent_hover']};
    }}

    QPushButton[class="primary"]:pressed {{
        background-color: {colors['accent_active']};
        border-color: {colors['accent_active']};
    }}

    /* Secondary Buttons - Ayon Style */
    QPushButton[class="secondary"] {{
        background-color: {colors['surface']};
        color: {colors['fg']};
        border: 1px solid {colors['outline']};
        font-weight: 500;
    }}

    QPushButton[class="secondary"]:hover {{
        background-color: {colors['hover']};
        border-color: {colors['accent']};
        color: {colors['accent']};
    }}

    QPushButton[class="secondary"]:pressed {{
        background-color: {colors['surface_high']};
    }}

    /* Danger Buttons - Ayon Style */
    QPushButton[class="danger"] {{
        background-color: {colors['error']};
        color: white;
        border: 1px solid {colors['error']};
    }}

    QPushButton[class="danger"]:hover {{
        background-color: #E53E3E;
        border-color: #E53E3E;
    }}

    QPushButton[class="danger"]:pressed {{
        background-color: #C53030;
        border-color: #C53030;
    }}
    
    /* Tree Widget - Calm Blue Style */
    QTreeWidget {{
        background-color: {colors['surface']};
        color: {colors['fg']};
        border: 1px solid {colors['accent']};
        border-radius: 8px;
        selection-background-color: {colors['accent']};
        alternate-background-color: {colors['surface_high']};
        font-size: 13px;
        font-weight: 500;
    }}

    QTreeWidget::item {{
        padding: 8px 12px;
        border: none;
        color: {colors['fg']};
        border-radius: 6px;
        margin: 1px;
        border: 1px solid transparent;
    }}

    QTreeWidget::item:selected {{
        background-color: {colors['accent']};
        color: white;
        border: 1px solid {colors['accent_hover']};
        font-weight: 600;
    }}

    QTreeWidget::item:hover {{
        background-color: {colors['hover']};
        color: {colors['fg']};
        border: 1px solid {colors['accent']};
    }}
    
    QTreeWidget::branch {{
        background-color: transparent;
    }}
    
    QTreeWidget::branch:has-children:!has-siblings:closed,
    QTreeWidget::branch:closed:has-children:has-siblings {{
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuNSA2TDcuNSA2TDYgNy41TDQuNSA2WiIgZmlsbD0iI0RDRERERCIvPgo8L3N2Zz4K);
    }}
    
    QTreeWidget::branch:open:has-children:!has-siblings,
    QTreeWidget::branch:open:has-children:has-siblings {{
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTUuNSA0LjVMNS41IDcuNUw2IDdMNi41IDcuNUw1LjUgNC41WiIgZmlsbD0iI0RDRERERCIvPgo8L3N2Zz4K);
    }}
    
    /* Table Widget - Calm Blue Style */
    QTableWidget {{
        background-color: {colors['surface']};
        color: {colors['fg']};
        border: 1px solid {colors['accent']};
        border-radius: 8px;
        gridline-color: {colors['outline']};
        selection-background-color: {colors['accent']};
        alternate-background-color: {colors['surface_high']};
        font-size: 13px;
        font-weight: 500;
    }}
    
    QTableWidget::item {{
        padding: 10px 14px;
        border: none;
        border-radius: 4px;
        margin: 1px;
    }}
    
    QTableWidget::item:selected {{
        background-color: {colors['accent']};
        color: white;
        font-weight: 600;
    }}
    
    QTableWidget::item:hover {{
        background-color: {colors['hover']};
    }}
    
    QHeaderView::section {{
        background-color: {colors['accent']};
        color: white;
        padding: 12px 14px;
        border: 1px solid {colors['accent']};
        border-left: none;
        font-weight: 600;
        font-size: 12px;
    }}
    
    QHeaderView::section:first {{
        border-left: 1px solid {colors['accent']};
    }}
    
    /* Plain Text Edit - Ayon Style */
    QPlainTextEdit {{
        background-color: {colors['surface']};
        color: {colors['fg']};
        border: 1px solid {colors['outline']};
        border-radius: 8px;
        selection-background-color: {colors['accent']};
        padding: 8px;
        font-size: 13px;
    }}
    
    /* Line Edit - Ayon Style */
    QLineEdit {{
        background-color: {colors['surface']};
        color: {colors['fg']};
        border: 1px solid {colors['outline']};
        border-radius: 8px;
        padding: 10px 12px;
        selection-background-color: {colors['accent']};
        font-size: 13px;
    }}
    
    QLineEdit:focus {{
        border-color: {colors['accent']};
        border-width: 2px;
    }}
    
    /* Combo Box - Ayon Style */
    QComboBox {{
        background-color: {colors['surface']};
        color: {colors['fg']};
        border: 1px solid {colors['outline']};
        border-radius: 8px;
        padding: 10px 12px;
        min-width: 120px;
        font-size: 13px;
    }}
    
    QComboBox:hover {{
        border-color: {colors['accent']};
    }}
    
    QComboBox:focus {{
        border-color: {colors['accent']};
        border-width: 2px;
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    
    QComboBox::down-arrow {{
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgNEw2IDdMOCA0SDNaIiBmaWxsPSIjRENERERERCIvPgo8L3N2Zz4K);
        width: 12px;
        height: 12px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {colors['surface_high']};
        color: {colors['fg']};
        border: 1px solid {colors['outline']};
        border-radius: 8px;
        selection-background-color: {colors['accent']};
        font-size: 13px;
    }}
    
    /* Scroll Bars - Ayon Style */
    QScrollBar:vertical {{
        background-color: {colors['surface']};
        width: 12px;
        border: none;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {colors['outline']};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {colors['accent']};
    }}
    
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background-color: {colors['surface']};
        height: 12px;
        border: none;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {colors['outline']};
        border-radius: 6px;
        min-width: 20px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {colors['accent']};
    }}
    
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    /* Labels - Ayon Style */
    QLabel {{
        color: {colors['fg']};
        background-color: transparent;
        font-size: 13px;
    }}
    
    QLabel[class="title"] {{
        font-size: 18px;
        font-weight: 700;
        color: {colors['accent']};
        font-family: "Roboto", "Segoe UI", sans-serif;
    }}
    
    QLabel[class="subtitle"] {{
        font-size: 16px;
        font-weight: 600;
        color: {colors['fg']};
        font-family: "Roboto", "Segoe UI", sans-serif;
    }}
    
    QLabel[class="muted"] {{
        color: {colors['muted']};
        font-size: 12px;
    }}
    
    /* Progress Bar - Ayon Style */
    QProgressBar {{
        background-color: {colors['surface']};
        border: 1px solid {colors['outline']};
        border-radius: 8px;
        text-align: center;
        color: {colors['fg']};
        font-size: 12px;
        font-weight: 500;
    }}
    
    QProgressBar::chunk {{
        background-color: {colors['accent']};
        border-radius: 6px;
    }}
    
    /* Group Box - Calm Blue Style */
    QGroupBox {{
        color: {colors['fg']};
        border: 1px solid {colors['accent']};
        border-radius: 10px;
        margin-top: 16px;
        font-weight: 600;
        font-size: 13px;
        padding-top: 12px;
        background-color: {colors['surface']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 4px 16px;
        background-color: {colors['accent']};
        color: white;
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-radius: 6px;
        border: 1px solid {colors['accent']};
    }}
    
    /* Splitter - Ayon Style */
    QSplitter::handle {{
        background-color: {colors['outline']};
    }}
    
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    
    QSplitter::handle:vertical {{
        height: 2px;
    }}
    
    QSplitter::handle:hover {{
        background-color: {colors['accent']};
    }}
    
    /* Dock Widget - Ayon Style */
    QDockWidget {{
        background-color: {colors['surface']};
        color: {colors['fg']};
        border: 1px solid {colors['outline']};
        border-radius: 8px;
        titlebar-close-icon: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTkgM0w2IDZMMyAzTDkgM1oiIGZpbGw9IiNEQ0REREMiLz4KPC9zdmc+Cg==);
        titlebar-normal-icon: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgM0w5IDlNOSAzTDMgOVoiIGZpbGw9IiNEQ0REREMiLz4KPC9zdmc+Cg==);
    }}
    
    QDockWidget::title {{
        background-color: {colors['accent']};
        color: white;
        padding: 8px 12px;
        font-weight: 600;
        font-size: 13px;
        border-radius: 8px 8px 0 0;
    }}
    
    QDockWidget::close-button,
    QDockWidget::float-button {{
        background-color: transparent;
        border: none;
        padding: 4px;
        border-radius: 4px;
    }}
    
    QDockWidget::close-button:hover,
    QDockWidget::float-button:hover {{
        background-color: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
    }}
    
    /* List Widget - Ayon Style */
    QListWidget {{
        background-color: {colors['surface']};
        color: {colors['fg']};
        border: 1px solid {colors['outline']};
        border-radius: 8px;
        selection-background-color: {colors['accent']};
        alternate-background-color: {colors['surface_high']};
        font-size: 13px;
    }}
    
    QListWidget::item {{
        padding: 8px 12px;
        border: none;
        color: {colors['fg']};
        border-radius: 4px;
        margin: 1px;
    }}
    
    QListWidget::item:selected {{
        background-color: {colors['accent']};
        color: white;
    }}
    
    QListWidget::item:hover {{
        background-color: {colors['hover']};
        color: {colors['fg']};
    }}
    """
    
    return qss
