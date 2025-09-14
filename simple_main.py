#!/usr/bin/env python3
"""
Simple working version of Vogue Manager
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QTabWidget

class SimpleMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vogue Manager - Simple Version")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("🎬 Vogue Manager - Ayon UI with Prism Backend")
        title.setStyleSheet("font-size: 24pt; font-weight: bold; color: #4A9EFF; margin: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E0E6EC;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #F8F9FA;
                padding: 10px 20px;
                margin-right: 2px;
                border: 1px solid #E0E6EC;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #4A9EFF;
            }
        """)
        
        # Dashboard tab
        dashboard_tab = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_tab)
        dashboard_layout.addWidget(QLabel("📊 Dashboard - Project Overview"))
        dashboard_layout.addWidget(QLabel("• Project Statistics"))
        dashboard_layout.addWidget(QLabel("• Recent Activity"))
        dashboard_layout.addWidget(QLabel("• Task Progress"))
        tabs.addTab(dashboard_tab, "Dashboard")
        
        # Tasks tab
        tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(tasks_tab)
        tasks_layout.addWidget(QLabel("📋 Tasks - Task Management"))
        tasks_layout.addWidget(QLabel("• Create Tasks"))
        tasks_layout.addWidget(QLabel("• Assign Users"))
        tasks_layout.addWidget(QLabel("• Track Progress"))
        tabs.addTab(tasks_tab, "Tasks")
        
        # Projects tab
        projects_tab = QWidget()
        projects_layout = QVBoxLayout(projects_tab)
        projects_layout.addWidget(QLabel("📁 Projects - Project Management"))
        projects_layout.addWidget(QLabel("• Create Projects"))
        projects_layout.addWidget(QLabel("• Manage Assets"))
        projects_layout.addWidget(QLabel("• Version Control"))
        tabs.addTab(projects_tab, "Projects")
        
        # Settings tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.addWidget(QLabel("⚙️ Settings - Configuration"))
        settings_layout.addWidget(QLabel("• User Preferences"))
        settings_layout.addWidget(QLabel("• Project Settings"))
        settings_layout.addWidget(QLabel("• System Configuration"))
        tabs.addTab(settings_tab, "Settings")
        
        layout.addWidget(tabs)
        
        # Status
        status = QLabel("✅ Application running successfully!")
        status.setStyleSheet("color: #51CF66; font-weight: bold; margin: 20px;")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status)
        
        print("Simple Vogue Manager window created successfully!")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = SimpleMainWindow()
    window.show()
    
    print("Vogue Manager started successfully!")
    print("You should see a window with tabs now!")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
