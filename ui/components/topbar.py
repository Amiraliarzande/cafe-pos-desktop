# /home/amirali-arzande/cafe-pos-desktop/ui/components/topbar.py

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class Topbar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topbar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(80)

        row = QHBoxLayout(self)
        row.setContentsMargins(20, 10, 20, 10)
        row.setSpacing(14)

        # عنوان صفحه و زیرعنوان
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.title = QLabel("داشبورد")
        self.title.setObjectName("topbarTitle")
        tagline = QLabel("کافه آرامش · طعم خوب، لحظه‌های بهتر")
        tagline.setObjectName("topbarTagline")
        title_col.addWidget(self.title)
        title_col.addWidget(tagline)
        row.addLayout(title_col, 1)

        # تاریخ روز (چیپ)
        today = datetime.now().strftime("%Y/%m/%d")
        self.date_label = QLabel(f"📅  {today}")
        self.date_label.setObjectName("topbarPill")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setFixedHeight(30)
        row.addWidget(self.date_label, 0, Qt.AlignmentFlag.AlignVCenter)

        # کارت کاربر / باریستا
        user_card = QFrame()
        user_card.setObjectName("topbarUser")
        user_row = QHBoxLayout(user_card)
        user_row.setContentsMargins(10, 6, 6, 6)
        user_row.setSpacing(8)

        avatar = QLabel("ب")
        avatar.setObjectName("topbarAvatar")
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        user_col = QVBoxLayout()
        user_col.setSpacing(0)
        greeting = QLabel("سلام، باریستا!")
        greeting.setObjectName("topbarUserGreeting")
        role = QLabel("کاربر فعلی")
        role.setObjectName("topbarUserRole")
        user_col.addWidget(greeting)
        user_col.addWidget(role)

        user_row.addLayout(user_col, 1)
        user_row.addWidget(avatar)
        row.addWidget(user_card, 0, Qt.AlignmentFlag.AlignVCenter)

        self.setStyleSheet(TOPBAR_QSS)

    def set_page_title(self, title):
        self.title.setText(title)


TOPBAR_QSS = """
QFrame#topbar {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}
QLabel#topbarTitle {
    color: #0F172A; font-size: 18px; font-weight: 800; background: transparent;
}
QLabel#topbarTagline {
    color: #64748B; font-size: 11px; background: transparent;
}
QLabel#topbarPill {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 0 12px;
    color: #475569;
    font-size: 11px;
    font-weight: 600;
}
QFrame#topbarUser {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}
QFrame#topbarUser:hover {
    border-color: #93C5B5;
    background: #F1F7F4;
}
QLabel#topbarAvatar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #38B894, stop:1 #28745A);
    color: #FFFFFF; font-size: 13px; font-weight: 800;
    border-radius: 16px;
}
QLabel#topbarUserGreeting {
    color: #0F172A; font-size: 11px; font-weight: 700; background: transparent;
}
QLabel#topbarUserRole {
    color: #94A3B8; font-size: 9px; background: transparent;
}
"""
