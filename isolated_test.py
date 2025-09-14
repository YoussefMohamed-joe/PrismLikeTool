#!/usr/bin/env python3
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("Testing PyQt6 import...")
try:
    from PyQt6.QtWidgets import QApplication, QLabel, QWidget
    print("PyQt6 imported successfully!")
    
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Isolated Test")
    window.setGeometry(100, 100, 300, 200)
    
    label = QLabel("Hello World!", window)
    label.move(50, 50)
    
    window.show()
    print("Window created and shown!")
    print("If you can see a window, PyQt6 is working!")
    
    # Don't run app.exec() to avoid blocking
    print("Test completed - window should be visible")
    
except ImportError as e:
    print(f"PyQt6 import failed: {e}")
except Exception as e:
    print(f"Error: {e}")
