# /home/amirali-arzande/cafe-pos-desktop/ui/components/sidebar.py

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# پالت رنگی هماهنگ با تم انبار و بقیه بخش‌ها
MINT = "#38B894"
MINT_SOFT = "#93C5B5"
BRAND_DARK = "#1F5E48"


class TileIcon(QWidget):
    """کاشی گرادیانی مدرن برای لوگوی کافه"""
    def __init__(self, glyph: str = "☕", parent=None):
        super().__init__(parent)
        self._glyph = glyph
        self.setFixedSize(QSize(48, 48))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)

        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QColor(MINT))
        gradient.setColorAt(1.0, QColor(BRAND_DARK))
        painter.setPen(QPen(QColor(MINT_SOFT), 1.2))
        painter.setBrush(gradient)
        painter.drawRoundedRect(rect, 14, 14)

        font = painter.font()
        font.setPointSizeF(18)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._glyph)
        painter.end()


class NavButton(QPushButton):
    """دکمه ناوبری سفارشی با نشانگر فعال در لبه"""
    def __init__(self, icon: str, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("navButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 0, 14, 0)
        row.setSpacing(12)

        self.icon_label = QLabel(icon)
        self.icon_label.setObjectName("navIcon")
        self.icon_label.setFixedWidth(22)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.text_label = QLabel(title)
        self.text_label.setObjectName("navText")
        self.text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        row.addWidget(self.icon_label)
        row.addWidget(self.text_label, 1)

        self._chevron = QLabel("")
        self._chevron.setObjectName("navChevron")
        self._chevron.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(self._chevron)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.property("active") is True:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            pen = QPen(QColor(MINT), 3)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            # خط نشانگر فعال در لبه راست (RTL)
            painter.drawLine(self.width() - 2, 10, self.width() - 2, self.height() - 10)
            painter.end()


class Sidebar(QFrame):
    page_requested = Signal(str)

    # تب تنظیمات کاملاً حذف شد
    ITEMS = [
        ("dashboard", "⌂", "داشبورد"),
        ("pos", "＋", "سفارش جدید"),
        ("menu", "☷", "منو"),
        ("customers", "♙", "مشتریان"),
        ("inventory", "▣", "انبار"),
        ("orders", "▥", "فروش‌ها و فاکتورها"),
        ("reports", "▤", "گزارش‌ها"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(220)
        self.buttons = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 16)
        layout.setSpacing(6)

        # هدر سایدبار
        header = QFrame()
        header.setObjectName("sidebarHeader")
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(4, 2, 4, 8)
        header_row.setSpacing(10)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        brand = QLabel("کافه آرامش")
        brand.setObjectName("sidebarBrand")
        slogan = QLabel("طعم خوب، لحظه‌های بهتر")
        slogan.setObjectName("sidebarSlogan")
        title_col.addWidget(brand)
        title_col.addWidget(slogan)

        header_row.addWidget(TileIcon("☕"), 0, Qt.AlignmentFlag.AlignVCenter)
        header_row.addLayout(title_col, 1)
        layout.addWidget(header)

        # جداکننده
        divider = QFrame()
        divider.setObjectName("sidebarDivider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)
        layout.addSpacing(8)

        section = QLabel("منوی اصلی")
        section.setObjectName("sidebarSection")
        layout.addWidget(section)
        layout.addSpacing(2)

        # دکمه‌های ناوبری
        for key, icon, title in self.ITEMS:
            button = NavButton(icon, title)
            button.clicked.connect(
                lambda checked=False, page_key=key: self.page_requested.emit(page_key)
            )
            layout.addWidget(button)
            self.buttons[key] = button

        layout.addStretch(1)

        # کارت پایین سایدبار
        footer_card = QFrame()
        footer_card.setObjectName("sidebarFooterCard")
        footer_col = QVBoxLayout(footer_card)
        footer_col.setContentsMargins(12, 10, 12, 10)
        footer_col.setSpacing(2)

        footer_title = QLabel("☕  کافه آرامش")
        footer_title.setObjectName("sidebarFooterTitle")
        footer_sub = QLabel("با ما، هر روز بهتر است")
        footer_sub.setObjectName("sidebarFooterSub")
        footer_col.addWidget(footer_title)
        footer_col.addWidget(footer_sub)
        layout.addWidget(footer_card)

        version = QLabel("نسخه ۱.۰")
        version.setObjectName("sidebarVersion")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        # اعمال استایل سایدبار
        self.setStyleSheet(SIDEBAR_QSS)

    def _apply_active_style(self, button: NavButton, is_active: bool) -> None:
        button.setProperty("active", is_active)
        icon = getattr(button, "icon_label", None)
        text = getattr(button, "text_label", None)
        chevron = getattr(button, "_chevron", None)
        if icon:
            icon.setProperty("active", is_active)
        if text:
            text.setProperty("active", is_active)
        if chevron:
            chevron.setText("‹" if is_active else "")
        for widget in (button, icon, text, chevron):
            if widget:
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()

    def set_active(self, key):
        for page_key, button in self.buttons.items():
            self._apply_active_style(button, page_key == key)

    def page_title(self, key):
        for page_key, _icon, title in self.ITEMS:
            if page_key == key:
                return title
        return "مدیریت کافه"


SIDEBAR_QSS = """
QFrame#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #215C49, stop:0.45 #28745A, stop:1 #17473A);
    border: none;
}
QFrame#sidebarHeader { background: transparent; }
QLabel#sidebarBrand { color: #FFFFFF; font-size: 16px; font-weight: 800; background: transparent; }
QLabel#sidebarSlogan { color: #8FAEA5; font-size: 10px; background: transparent; }
QFrame#sidebarDivider {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 transparent,
                                stop:0.5 rgba(255, 255, 255, 70),
                                stop:1 transparent);
}
QLabel#sidebarSection {
    color: #8FAEA5; font-size: 10px; font-weight: 700;
    letter-spacing: 1px; padding-right: 8px; padding-bottom: 2px;
    background: transparent;
}
QPushButton#navButton {
    background: transparent; border: 1px solid transparent;
    border-radius: 10px; padding: 0px; text-align: right;
}
QPushButton#navButton:hover {
    background: rgba(255, 255, 255, 20);
    border: 1px solid rgba(147, 197, 181, 40);
}
QPushButton#navButton[active="true"] {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(255, 255, 255, 42),
                                stop:1 rgba(255, 255, 255, 14));
    border: 1px solid rgba(147, 197, 181, 90);
}
QLabel#navIcon { color: #BFD6CE; font-size: 15px; background: transparent; }
QLabel#navIcon[active="true"] { color: #FFFFFF; }
QLabel#navText { color: #BFD6CE; font-size: 13px; font-weight: 500; background: transparent; }
QLabel#navText[active="true"] { color: #FFFFFF; font-weight: 800; }
QLabel#navChevron { color: #38B894; font-size: 15px; font-weight: 800; background: transparent; }
QFrame#sidebarFooterCard {
    background: rgba(0, 0, 0, 35);
    border: 1px solid rgba(147, 197, 181, 50);
    border-radius: 10px;
}
QLabel#sidebarFooterTitle { color: #EAF6F0; font-size: 11px; font-weight: 700; background: transparent; }
QLabel#sidebarFooterSub { color: #8FAEA5; font-size: 9px; background: transparent; }
QLabel#sidebarVersion { color: rgba(147, 197, 181, 140); font-size: 9px; padding-top: 4px; background: transparent; }
"""
