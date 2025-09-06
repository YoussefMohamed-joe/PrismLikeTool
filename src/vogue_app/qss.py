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
    /* Main Window */
    QMainWindow {{
        background-color: {colors['bg']};
        color: {colors['fg']};
    }}
    
    /* Menu Bar */
    QMenuBar {{
        background-color: {colors['panel']};
        color: {colors['fg']};
        border-bottom: 1px solid {colors['border']};
        padding: 2px;
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: 4px 8px;
        border-radius: 3px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {colors['accent']};
        color: white;
    }}
    
    QMenu {{
        background-color: {colors['panel']};
        color: {colors['fg']};
        border: 1px solid {colors['border']};
        padding: 4px;
    }}
    
    QMenu::item {{
        padding: 6px 20px;
        border-radius: 3px;
    }}
    
    QMenu::item:selected {{
        background-color: {colors['accent']};
        color: white;
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {colors['border']};
        margin: 4px 0px;
    }}
    
    /* Tool Bar */
    QToolBar {{
        background-color: {colors['panel']};
        border: none;
        spacing: 3px;
        padding: 2px;
    }}
    
    QToolButton {{
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 6px;
        margin: 1px;
    }}
    
    QToolButton:hover {{
        background-color: {colors['hover']};
        border: 1px solid {colors['accent']};
    }}
    
    QToolButton:pressed {{
        background-color: {colors['accent']};
        color: white;
    }}
    
    /* Status Bar */
    QStatusBar {{
        background-color: {colors['panel']};
        color: {colors['fg']};
        border-top: 1px solid {colors['border']};
        padding: 2px;
    }}
    
    /* Tab Widget */
    QTabWidget::pane {{
        border: 1px solid {colors['border']};
        background-color: {colors['bg']};
    }}
    
    QTabBar::tab {{
        background-color: {colors['panel']};
        color: {colors['fg']};
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        border: 1px solid {colors['border']};
        border-bottom: none;
    }}
    
    QTabBar::tab:selected {{
        background-color: {colors['bg']};
        color: {colors['accent']};
        border-bottom: 1px solid {colors['bg']};
    }}
    
    QTabBar::tab:hover {{
        background-color: {colors['hover']};
    }}
    
    /* Push Buttons */
    QPushButton {{
        background-color: {colors['accent']};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: {colors['accent2']};
    }}
    
    QPushButton:pressed {{
        background-color: {colors['accent']};
    }}
    
    QPushButton:disabled {{
        background-color: {colors['muted']};
        color: {colors['border']};
    }}
    
    /* Secondary Buttons */
    QPushButton[class="secondary"] {{
        background-color: {colors['panel']};
        color: {colors['fg']};
        border: 1px solid {colors['border']};
    }}
    
    QPushButton[class="secondary"]:hover {{
        background-color: {colors['hover']};
        border-color: {colors['accent']};
    }}
    
    /* Tree Widget */
    QTreeWidget {{
        background-color: {colors['bg']};
        color: {colors['fg']};
        border: 1px solid {colors['border']};
        border-radius: 4px;
        selection-background-color: {colors['selection']};
        alternate-background-color: {colors['panel']};
    }}
    
    QTreeWidget::item {{
        padding: 4px;
        border: none;
    }}
    
    QTreeWidget::item:selected {{
        background-color: {colors['selection']};
        color: white;
    }}
    
    QTreeWidget::item:hover {{
        background-color: {colors['hover']};
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
    
    /* Table Widget */
    QTableWidget {{
        background-color: {colors['bg']};
        color: {colors['fg']};
        border: 1px solid {colors['border']};
        border-radius: 4px;
        gridline-color: {colors['border']};
        selection-background-color: {colors['selection']};
        alternate-background-color: {colors['panel']};
    }}
    
    QTableWidget::item {{
        padding: 6px;
        border: none;
    }}
    
    QTableWidget::item:selected {{
        background-color: {colors['selection']};
        color: white;
    }}
    
    QTableWidget::item:hover {{
        background-color: {colors['hover']};
    }}
    
    QHeaderView::section {{
        background-color: {colors['panel']};
        color: {colors['fg']};
        padding: 6px;
        border: 1px solid {colors['border']};
        border-left: none;
        font-weight: bold;
    }}
    
    QHeaderView::section:first {{
        border-left: 1px solid {colors['border']};
    }}
    
    /* Plain Text Edit */
    QPlainTextEdit {{
        background-color: {colors['bg']};
        color: {colors['fg']};
        border: 1px solid {colors['border']};
        border-radius: 4px;
        selection-background-color: {colors['selection']};
    }}
    
    /* Line Edit */
    QLineEdit {{
        background-color: {colors['panel']};
        color: {colors['fg']};
        border: 1px solid {colors['border']};
        border-radius: 4px;
        padding: 6px;
        selection-background-color: {colors['selection']};
    }}
    
    QLineEdit:focus {{
        border-color: {colors['accent']};
    }}
    
    /* Combo Box */
    QComboBox {{
        background-color: {colors['panel']};
        color: {colors['fg']};
        border: 1px solid {colors['border']};
        border-radius: 4px;
        padding: 6px;
        min-width: 100px;
    }}
    
    QComboBox:hover {{
        border-color: {colors['accent']};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgNEw2IDdMOCA0SDNaIiBmaWxsPSIjRENERERERCIvPgo8L3N2Zz4K);
        width: 12px;
        height: 12px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {colors['panel']};
        color: {colors['fg']};
        border: 1px solid {colors['border']};
        selection-background-color: {colors['selection']};
    }}
    
    /* Scroll Bars */
    QScrollBar:vertical {{
        background-color: {colors['panel']};
        width: 12px;
        border: none;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {colors['border']};
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
        background-color: {colors['panel']};
        height: 12px;
        border: none;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {colors['border']};
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
    
    /* Labels */
    QLabel {{
        color: {colors['fg']};
        background-color: transparent;
    }}
    
    QLabel[class="title"] {{
        font-size: 16px;
        font-weight: bold;
        color: {colors['accent']};
    }}
    
    QLabel[class="subtitle"] {{
        font-size: 14px;
        font-weight: bold;
        color: {colors['fg']};
    }}
    
    QLabel[class="muted"] {{
        color: {colors['muted']};
    }}
    
    /* Progress Bar */
    QProgressBar {{
        background-color: {colors['panel']};
        border: 1px solid {colors['border']};
        border-radius: 4px;
        text-align: center;
        color: {colors['fg']};
    }}
    
    QProgressBar::chunk {{
        background-color: {colors['accent']};
        border-radius: 3px;
    }}
    
    /* Group Box */
    QGroupBox {{
        color: {colors['fg']};
        border: 1px solid {colors['border']};
        border-radius: 4px;
        margin-top: 8px;
        font-weight: bold;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 8px 0 8px;
        background-color: {colors['bg']};
    }}
    
    /* Splitter */
    QSplitter::handle {{
        background-color: {colors['border']};
    }}
    
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    
    QSplitter::handle:vertical {{
        height: 2px;
    }}
    
    /* Dock Widget */
    QDockWidget {{
        background-color: {colors['panel']};
        color: {colors['fg']};
        border: 1px solid {colors['border']};
        titlebar-close-icon: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTkgM0w2IDZMMyAzTDkgM1oiIGZpbGw9IiNEQ0REREMiLz4KPC9zdmc+Cg==);
        titlebar-normal-icon: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgM0w5IDlNOSAzTDMgOVoiIGZpbGw9IiNEQ0REREMiLz4KPC9zdmc+Cg==);
    }}
    
    QDockWidget::title {{
        background-color: {colors['accent']};
        color: white;
        padding: 4px 8px;
        font-weight: bold;
    }}
    
    QDockWidget::close-button,
    QDockWidget::float-button {{
        background-color: transparent;
        border: none;
        padding: 2px;
    }}
    
    QDockWidget::close-button:hover,
    QDockWidget::float-button:hover {{
        background-color: rgba(255, 255, 255, 0.2);
        border-radius: 2px;
    }}
    """
    
    return qss
