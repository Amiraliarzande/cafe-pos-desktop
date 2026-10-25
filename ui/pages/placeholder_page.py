from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QFrame

class PlaceholderPage(QWidget):

  def __init__(self, title, description, parent=None):
    super().__init__(parent)
    layout = QVBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    card = QFrame()
    card.setObjectName("panel")
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(32, 32, 32, 32)
    card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    heading = QLabel(title)
    heading.setObjectName("panelTitle")
    heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
    desc = QLabel(description)
    desc.setObjectName("muted")
    desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
    desc.setWordWrap(True)
    card_layout.addWidget(heading)
    card_layout.addSpacing(12)
    card_layout.addWidget(desc)
    layout.addWidget(card)