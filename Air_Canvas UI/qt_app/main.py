"""Air Canvas Pro — PyQt6 Desktop Application Entry Point."""
import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase

# Ensure 'ui/' is importable from this file's directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Air Canvas Pro")
    app.setOrganizationName("AirCanvas")
    app.setApplicationVersion("1.0.0")

    # Load stylesheet
    qss_path = os.path.join(os.path.dirname(__file__), "ui", "style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())

    # Prefer a clean sans-serif font if available
    QFontDatabase.addApplicationFont(":/fonts/Inter-Regular.ttf")
    app.setFont(QFont("Segoe UI", 10))

    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
