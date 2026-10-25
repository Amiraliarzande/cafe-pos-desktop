import os
import sys
from datetime import datetime

# On some Ubuntu/GNOME setups, the system Qt theme integration crashes because
# of a missing xsettings schema key. Set a safe theme before importing Qt.
os.environ.setdefault("QT_QPA_PLATFORMTHEME", "generic")

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget, QTableWidget,
    QTableWidgetItem, QHeaderView
)

GREEN = "#279D78"
GREEN_DARK = "#173B35"
TEXT = "#1D3037"
MUTED = "#71808D"
BORDER = "#E2E9EC"
BG = "#F5F8FA"
WHITE = "#FFFFFF"


class StatCard(QFrame):
    def __init__(self, title, value, note, icon, accent=GREEN, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setMinimumHeight(136)
        row = QHBoxLayout(self)
        row.setContentsMargins(18, 16, 18, 16)
        row.setSpacing(12)

        icon_box = QLabel(icon)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setFixedSize(46, 46)
        icon_box.setStyleSheet(
            f"background:{accent}18; color:{accent}; border-radius:23px;"
            "font-size:22px; font-weight:700;"
        )

        text_col = QVBoxLayout()
        text_col.setSpacing(8)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("statTitle")
        value_lbl = QLabel(value)
        value_lbl.setObjectName("statValue")
        note_lbl = QLabel(note)
        note_lbl.setObjectName("statNote")
        note_lbl.setStyleSheet(f"color:{accent};")
        text_col.addWidget(title_lbl)
        text_col.addWidget(value_lbl)
        text_col.addWidget(note_lbl)
        text_col.addStretch(1)

        row.addWidget(icon_box, 0, Qt.AlignmentFlag.AlignTop)
        row.addLayout(text_col, 1)


class SalesChart(QWidget):
    """Small custom-painted chart; no extra chart dependency required."""
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(230)
        self.values = [0.5, 1.0, 1.35, 1.15, 1.7, 1.42, 2.5]
        self.labels = ["پنجشنبه", "جمعه", "شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه"]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(42, 12, -18, -28)
        left, top, width, height = rect.x(), rect.y(), rect.width(), rect.height()

        # Grid and Y labels
        painter.setFont(QFont("Vazirmatn", 9))
        for i, label in enumerate(["۳,۰۰۰,۰۰۰", "۲,۵۰۰,۰۰۰", "۲,۰۰۰,۰۰۰",
                                   "۱,۵۰۰,۰۰۰", "۱,۰۰۰,۰۰۰", "۵۰۰,۰۰۰", "۰"]):
            y = top + i * height / 6
            painter.setPen(QPen(QColor(BORDER), 1))
            painter.drawLine(int(left), int(y), int(left + width), int(y))
            painter.setPen(QColor(MUTED))
            painter.drawText(QRectF(0, y - 9, left - 8, 18),
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)

        points = []
        max_val = 3.0
        for i, value in enumerate(self.values):
            x = left + i * width / (len(self.values) - 1)
            y = top + height - (value / max_val) * height
            points.append(QPointF(x, y))

        area = QPainterPath()
        area.moveTo(points[0].x(), top + height)
        area.lineTo(points[0])
        for p in points[1:]:
            area.lineTo(p)
        area.lineTo(points[-1].x(), top + height)
        area.closeSubpath()
        painter.fillPath(area, QColor(39, 157, 120, 30))

        line = QPainterPath()
        line.moveTo(points[0])
        for p in points[1:]:
            line.lineTo(p)
        painter.setPen(QPen(QColor(GREEN), 3, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(line)

        for p in points:
            painter.setBrush(QColor(GREEN))
            painter.setPen(QPen(QColor(WHITE), 2))
            painter.drawEllipse(p, 4.5, 4.5)

        painter.setFont(QFont("Vazirmatn", 9))
        painter.setPen(QColor(MUTED))
        for i, label in enumerate(self.labels):
            x = left + i * width / (len(self.labels) - 1)
            painter.drawText(QRectF(x - 37, top + height + 7, 74, 20),
                            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, label)


class Panel(QFrame):
    def __init__(self, title, subtitle=None):
        super().__init__()
        self.setObjectName("panel")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 16, 18, 16)
        self.layout.setSpacing(12)
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        header.addWidget(title_label)
        header.addStretch(1)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("muted")
            header.addWidget(sub)
        self.layout.addLayout(header)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("مدیریت کافه")
        self.resize(1440, 900)
        self.setMinimumSize(1080, 700)

        root = QWidget()
        root.setObjectName("root")
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # RTL means the first widget is placed at the right edge.
        outer.addWidget(self.make_sidebar())
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(26, 20, 26, 14)
        content_layout.setSpacing(18)
        content_layout.addWidget(self.make_topbar())

        stats = QGridLayout()
        stats.setSpacing(16)
        stats.addWidget(StatCard("فروش امروز", "۲,۸۵۰,۰۰۰ تومان", "↑ ۱۲٪ نسبت به دیروز", "▤", GREEN), 0, 0)
        stats.addWidget(StatCard("تعداد سفارش‌ها", "۲۳", "↑ ۸٪ نسبت به دیروز", "▧", "#2587C7"), 0, 1)
        stats.addWidget(StatCard("مشتریان امروز", "۱۵", "۵٪+ نسبت به دیروز", "♙", "#7652C8"), 0, 2)
        stats.addWidget(StatCard("موجودی کل انبار", "۴۲ قلم", "۲ قلم زیر حد مجاز", "⬡", "#D58A16"), 0, 3)
        content_layout.addLayout(stats)

        middle = QHBoxLayout()
        middle.setSpacing(16)
        chart_panel = Panel("روند فروش", "۷ روز گذشته")
        chart_panel.layout.addWidget(SalesChart(), 1)
        middle.addWidget(chart_panel, 11)

        orders_panel = Panel("سفارش‌های اخیر")
        table = QTableWidget(5, 4)
        table.setHorizontalHeaderLabels(["شماره فاکتور", "مشتری", "مبلغ", "زمان"])
        table.setRowCount(5)
        rows = [
            ("FAC-20260725-001", "مشتری آزاد", "۸۵۰,۰۰۰", "۱۷:۴۲"),
            ("FAC-20260725-002", "آقای رضایی", "۱,۲۰۰,۰۰۰", "۱۶:۳۵"),
            ("FAC-20260725-003", "مشتری آزاد", "۴۵۰,۰۰۰", "۱۵:۲۷"),
            ("FAC-20260725-004", "خانم احمدی", "۶۸۰,۰۰۰", "۱۴:۱۵"),
            ("FAC-20260725-005", "مشتری آزاد", "۹۷۰,۰۰۰", "۱۲:۴۸"),
        ]
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(r, c, item)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setMinimumHeight(250)
        orders_panel.layout.addWidget(table)
        middle.addWidget(orders_panel, 10)
        content_layout.addLayout(middle, 1)

        inventory_panel = Panel("وضعیت موجودی انبار", "مشاهده همه  ←")
        inventory = QHBoxLayout()
        inventory.setSpacing(12)
        products = [
            ("☕", "قهوه عربیکا", "۲.۵ کیلوگرم", "موجود", GREEN),
            ("🥛", "شیر", "۳.۲ لیتر", "موجود", GREEN),
            ("▱", "شکر", "۱.۸ کیلوگرم", "موجود", GREEN),
            ("🍰", "کیک شکلاتی", "۵ عدد", "موجود", GREEN),
            ("🍋", "لیمو", "۰.۸ کیلوگرم", "کمتر از حد مجاز", "#D58A16"),
            ("✿", "چای سیاه", "۲.۳ کیلوگرم", "موجود", GREEN),
        ]
        for icon, name, quantity, status, color in products:
            tile = QFrame()
            tile.setObjectName("productTile")
            tile_l = QVBoxLayout(tile)
            tile_l.setContentsMargins(12, 12, 12, 12)
            tile_l.setSpacing(5)
            emoji = QLabel(icon)
            emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
            emoji.setStyleSheet("font-size:25px;")
            name_l = QLabel(name)
            name_l.setObjectName("productName")
            qty = QLabel(quantity)
            qty.setObjectName("muted")
            stat = QLabel(status)
            stat.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat.setStyleSheet(f"color:{color}; background:{color}18; padding:4px; border-radius:9px;")
            tile_l.addWidget(emoji)
            tile_l.addWidget(name_l)
            tile_l.addWidget(qty)
            tile_l.addWidget(stat)
            inventory.addWidget(tile)
        inventory_panel.layout.addLayout(inventory)
        content_layout.addWidget(inventory_panel)

        footer = QHBoxLayout()
        db_status = QLabel("●  سیستم متصل به پایگاه داده: cafe.db")
        db_status.setObjectName("muted")
        version = QLabel("نسخه ۱.۰.۰")
        version.setObjectName("muted")
        footer.addWidget(db_status)
        footer.addStretch(1)
        footer.addWidget(version)
        content_layout.addLayout(footer)

        outer.addWidget(content, 1)
        self.setCentralWidget(root)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.apply_styles()

    def make_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(205)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 22, 14, 18)
        layout.setSpacing(9)

        logo = QLabel("☕")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size:42px; color:#38B894; padding:6px;")
        brand = QLabel("کافه آرامش")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setStyleSheet("font-size:18px; font-weight:700; color:white;")
        slogan = QLabel("طعم خوب، لحظه‌های بهتر")
        slogan.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slogan.setStyleSheet("font-size:10px; color:#A8BBB7;")
        layout.addWidget(logo)
        layout.addWidget(brand)
        layout.addWidget(slogan)
        layout.addSpacing(24)

        items = [
            ("⌂", "داشبورد", True),
            ("🛒", "سفارش جدید", False),
            ("☷", "منو", False),
            ("♙", "مشتریان", False),
            ("▣", "انبار", False),
            ("▥", "فروش‌ها", False),
            ("▤", "گزارشات", False),
            ("⚙", "تنظیمات", False),
        ]
        for icon, title, active in items:
            button = QPushButton(f"{icon}     {title}")
            button.setObjectName("navActive" if active else "navButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(46)
            layout.addWidget(button)
        layout.addStretch(1)
        bottom = QLabel("☕\n\nکافه آرامش\nبا ما، هر روز بهتر است")
        bottom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom.setStyleSheet("color:#91AAA4; font-size:12px; padding:12px;")
        layout.addWidget(bottom)
        return sidebar

    def make_topbar(self):
        bar = QFrame()
        bar.setObjectName("topbar")
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 10)
        greeting = QLabel("سلام، باریستا!\nکاربر فعلی")
        greeting.setObjectName("muted")
        row.addWidget(greeting)
        row.addStretch(1)
        date = QLabel("چهارشنبه ۲۵ تیر ۱۴۰۵   ◷  ۱۷:۵۸")
        date.setObjectName("muted")
        row.addWidget(date)
        row.addSpacing(28)
        title_col = QVBoxLayout()
        title = QLabel("کافه آرامش")
        title.setObjectName("brandTitle")
        tagline = QLabel("طعم خوب، لحظه‌های بهتر")
        tagline.setObjectName("muted")
        title_col.addWidget(title)
        title_col.addWidget(tagline)
        row.addLayout(title_col)
        return bar

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { font-family: "Vazirmatn", "Noto Sans Arabic", "DejaVu Sans"; color: #1D3037; }
            #root { background: #F5F8FA; }
            #sidebar { background: #173B35; }
            #navButton, #navActive {
                text-align: right; border: none; border-radius: 9px; padding: 8px 12px;
                font-size: 13px; color: #D7E3E0; background: transparent;
            }
            #navButton:hover { background: #244D45; }
            #navActive { color: white; background: #279D78; font-weight: 700; }
            #topbar { background: transparent; border-bottom: 1px solid #E2E9EC; }
            #brandTitle { font-size: 20px; font-weight: 700; }
            #muted { color: #71808D; font-size: 11px; }
            #statCard, #panel { background: white; border: 1px solid #E2E9EC; border-radius: 12px; }
            #statTitle { color: #52636D; font-size: 12px; }
            #statValue { font-size: 20px; font-weight: 700; }
            #statNote { font-size: 11px; }
            #panelTitle { font-size: 16px; font-weight: 700; }
            #productTile { background: #FBFCFD; border: 1px solid #E8EEF1; border-radius: 10px; }
            #productName { font-size: 12px; font-weight: 700; }
            QTableWidget { background: white; border: none; alternate-background-color: #F8FAFB; font-size: 11px; }
            QHeaderView::section { background: #F2F6F8; color: #647681; border: none; padding: 9px 4px; font-weight: 600; }
            QTableWidget::item { padding: 6px; border-bottom: 1px solid #EDF1F3; }
        """)


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
