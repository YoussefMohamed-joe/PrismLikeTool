#!/usr/bin/env python3
"""
Simple test to check if PyQt6 UI works
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test UI")
        self.setGeometry(100, 100, 400, 300)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Label
        label = QLabel("Hello! This is a test window.")
        layout.addWidget(label)
        
        # Button
        button = QPushButton("Click Me!")
        button.clicked.connect(self.button_clicked)
        layout.addWidget(button)
        
        print("Test window created successfully!")
    
    def button_clicked(self):
        print("Button clicked!")

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    print("Window should be visible now!")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
