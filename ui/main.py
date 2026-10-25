import os
import sys

# Work around the GNOME xsettings issue observed on this machine.
os.environ.setdefault("QT_QPA_PLATFORMTHEME", "generic")

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from ui.windows.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Cafe POS")
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setFont(QFont("Vazirmatn", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()