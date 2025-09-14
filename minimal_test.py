#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("Minimal Test")
window.setGeometry(100, 100, 300, 200)

label = QLabel("Hello World!", window)
label.move(50, 50)

window.show()
print("Window should be visible now!")
app.exec()
