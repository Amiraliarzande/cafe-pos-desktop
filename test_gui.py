import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
)


def main():
    app = QApplication(sys.argv)

    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    window = QWidget()
    window.setWindowTitle("مدیریت کافه")
    window.resize(800, 500)

    layout = QVBoxLayout(window)

    title = QLabel("به سیستم مدیریت کافه خوش آمدید")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)

    layout.addWidget(title)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()