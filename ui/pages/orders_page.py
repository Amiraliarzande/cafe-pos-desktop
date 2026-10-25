from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError

from database.db import init_db
from database.models.cafe.order_archive import OrderArchive

# ==========================================================
# پالت رنگی و استایل‌های مشترک
# ==========================================================
GREEN = "#28745A"
GREEN_DARK = "#1E5844"
GREEN_LIGHT = "#E8F3EB"
MUTED = "#6F7D76"
BORDER = "#E2E8E4"
WHITE = "#FFFFFF"
BG = "#F7FAF8"
TEXT = "#203028"
DANGER = "#D64545"
DANGER_LIGHT = "#FDE8E8"

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def to_persian_digits(value) -> str:
    """تبدیل رقم‌ها به فارسی."""
    return str(value).translate(PERSIAN_DIGITS)


def money(value) -> str:
    """قالب‌بندی مبلغ به تومان با جداکننده هزارگان و ارقام فارسی."""
    try:
        val = int(round(float(value or 0)))
    except (ValueError, TypeError):
        val = 0
    formatted = f"{val:,}".replace(",", "٬")
    return f"{to_persian_digits(formatted)} تومان"


def format_number(value) -> str:
    """نمایش عدد با جداکننده هزارگان و ارقام فارسی."""
    try:
        val = int(value or 0)
    except (ValueError, TypeError):
        val = 0
    return to_persian_digits(f"{val:,}".replace(",", "٬"))


def customer_text(customer_name: str | None) -> str:
    return customer_name.strip() if customer_name and customer_name.strip() else "مشتری آزاد (مهمان)"


# ==========================================================
# ویجت وضعیت پرداخت (Badge)
# ==========================================================
class PaymentBadge(QWidget):
    """بج کپسولی وضعیت پرداخت در جدول."""

    def __init__(self, is_paid: bool, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("پرداخت‌شده" if is_paid else "پرداخت‌نشده")
        bg_color = GREEN_LIGHT if is_paid else DANGER_LIGHT
        fg_color = GREEN if is_paid else DANGER

        label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg_color};
                color: {fg_color};
                border-radius: 9px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 700;
            }}
            """
        )
        layout.addWidget(label)


# ==========================================================
# کارت‌های آماری بالای صفحه
# ==========================================================
class StatCard(QFrame):
    def __init__(self, title: str, value: str = "۰", icon: str = "◈", accent: str = GREEN, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setMinimumHeight(96)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        icon_box = QLabel(icon)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setFixedSize(44, 44)
        icon_box.setStyleSheet(
            f"""
            background: {accent}18;
            color: {accent};
            border-radius: 22px;
            font-size: 20px;
            font-weight: 800;
            """
        )

        content = QVBoxLayout()
        content.setSpacing(4)
        content.setContentsMargins(0, 2, 0, 2)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"color: {MUTED}; font-size: 12px; font-weight: 600;")

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {TEXT}; font-size: 18px; font-weight: 800;")

        content.addWidget(self.title_label)
        content.addWidget(self.value_label)
        content.addStretch()

        layout.addWidget(icon_box, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(content, 1)

        self.setStyleSheet(
            f"""
            QFrame#statCard {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            """
        )

    def set_value(self, value: str):
        self.value_label.setText(str(value))


# ==========================================================
# دیالوگ مدرن جزئیات فاکتور
# ==========================================================
class OrderDetailsDialog(QDialog):
    def __init__(self, order_data: dict, parent=None):
        super().__init__(parent)
        self.order_data = order_data

        self.setWindowTitle(f"جزئیات فاکتور {order_data['factor_number']}")
        self.resize(820, 600)
        self.setMinimumSize(720, 480)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(16)

        # ۱. هدر دیالوگ
        header_row = QHBoxLayout()
        title = QLabel(f"فاکتور فروش: {to_persian_digits(order_data['factor_number'])}")
        title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {TEXT};")
        header_row.addWidget(title)
        header_row.addStretch()

        is_paid = order_data["is_paid"]
        status_lbl = QLabel("پرداخت‌شده" if is_paid else "پرداخت‌نشده")
        status_lbl.setStyleSheet(
            f"""
            background: {GREEN_LIGHT if is_paid else DANGER_LIGHT};
            color: {GREEN if is_paid else DANGER};
            padding: 6px 14px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 700;
            """
        )
        header_row.addWidget(status_lbl)
        root.addLayout(header_row)

        # ۲. اطلاعات متای فاکتور
        info_box = QFrame()
        info_box.setObjectName("infoBox")
        info_grid = QGridLayout(info_box)
        info_grid.setContentsMargins(16, 14, 16, 14)
        info_grid.setHorizontalSpacing(24)
        info_grid.setVerticalSpacing(10)

        meta = [
            ("تاریخ ثبت:", to_persian_digits(order_data["persian_date"])),
            ("ساعت ثبت:", to_persian_digits(order_data["persian_time"])),
            ("نام مشتری:", customer_text(order_data["customer_name"])),
            ("ثبت‌کننده:", order_data["performed_by"] or "نامشخص"),
        ]

        for i, (lbl, val) in enumerate(meta):
            r = i // 2
            c = (i % 2) * 2
            lbl_w = QLabel(lbl)
            lbl_w.setStyleSheet(f"color: {MUTED}; font-size: 12px; font-weight: 500;")
            val_w = QLabel(val)
            val_w.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 700;")
            info_grid.addWidget(lbl_w, r, c)
            info_grid.addWidget(val_w, r, c + 1)

        root.addWidget(info_box)

        # ۳. جدول اقلام سفارش
        table_title = QLabel("اقلام سفارش داده شده")
        table_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {TEXT};")
        root.addWidget(table_title)

        items_table = QTableWidget(len(order_data["items"]), 5)
        items_table.setHorizontalHeaderLabels([
            "نام محصول",
            "قیمت واحد",
            "تعداد",
            "جمع ردیف",
            "دستور تهیه و مواد مصرفی",
        ])
        items_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        items_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        items_table.setAlternatingRowColors(True)
        items_table.setShowGrid(False)
        items_table.verticalHeader().setVisible(False)
        items_table.verticalHeader().setDefaultSectionSize(40)

        header = items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        for row, item in enumerate(order_data["items"]):
            values = [
                item["menu_item_name"],
                money(item["unit_price"]),
                format_number(item["quantity"]),
                money(item["subtotal"]),
                item["recipe_snapshot_details"] or "—",
            ]

            for col, val in enumerate(values):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter if col in (1, 2, 3) else (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                )
                items_table.setItem(row, col, cell)

        root.addWidget(items_table, 1)

        # ۴. فوتر دیالوگ: خلاصه و دکمه بستن
        footer = QHBoxLayout()

        total_box = QHBoxLayout()
        total_box.setSpacing(16)

        count_lbl = QLabel(f"تعداد کل اقلام: <b>{format_number(order_data['total_items_count'])}</b>")
        count_lbl.setStyleSheet(f"color: {MUTED}; font-size: 13px;")

        total_lbl = QLabel(f"مبلغ نهایی فاکتور: <b style='color: {GREEN};'>{money(order_data['total_price'])}</b>")
        total_lbl.setStyleSheet("font-size: 15px;")

        total_box.addWidget(count_lbl)
        total_box.addWidget(total_lbl)
        footer.addLayout(total_box)
        footer.addStretch()

        close_btn = QPushButton("بستن")
        close_btn.setMinimumSize(100, 36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)

        root.addLayout(footer)

        self.setStyleSheet(
            f"""
            QDialog {{
                background: {BG};
                font-family: "Vazirmatn", "Noto Sans Arabic", "DejaVu Sans";
            }}
            QFrame#infoBox {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
            QTableWidget {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 10px;
                alternate-background-color: #F8FAF9;
                font-size: 12px;
            }}
            QHeaderView::section {{
                background: #EFF4F0;
                color: {MUTED};
                border: none;
                padding: 8px 6px;
                font-weight: 700;
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 6px;
                border-bottom: 1px solid #EDF1EE;
            }}
            QPushButton {{
                background: {WHITE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                font-weight: 600;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background: #F0F4F2;
            }}
            """
        )


# ==========================================================
# صفحه بایگانی سفارش‌ها
# ==========================================================
class OrdersPage(QWidget):
    """صفحه بایگانی سفارش‌ها و فاکتورها."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.orders = []
        self.filtered_orders = []

        self._build_ui()
        self.refresh_orders()

    # --------------------------------------------------
    # ساخت رابط کاربری
    # --------------------------------------------------
    def _build_ui(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 20)
        root.setSpacing(16)

        # ─── ۱. هدر صفحه ──────────────────────────────
        heading = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        title = QLabel("بایگانی سفارش‌ها و فاکتورها")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {TEXT};")

        subtitle = QLabel("مشاهده، جست‌وجو، فیلتر و بررسی جزئیات فاکتورهای ثبت‌شده")
        subtitle.setStyleSheet(f"color: {MUTED}; font-size: 12px;")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        heading.addLayout(title_box)
        heading.addStretch()

        self.refresh_button = QPushButton("↻  به‌روزرسانی")
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.setObjectName("primaryButton")
        self.refresh_button.setMinimumHeight(38)
        self.refresh_button.clicked.connect(self.refresh_orders)
        heading.addWidget(self.refresh_button)

        root.addLayout(heading)

        # ─── ۲. کارت‌های آماری ─────────────────────────
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)

        self.orders_stat = StatCard("تعداد کل فاکتورها", "۰", "▤", "#2587C7")
        self.sales_stat = StatCard("مجموع مبالغ فاکتورها", "۰ تومان", "▲", GREEN)
        self.paid_stat = StatCard("مجموع مبالغ پرداخت‌شده", "۰ تومان", "✓", "#2E8B57")
        self.unpaid_stat = StatCard("فاکتورهای پرداخت‌نشده", "۰", "!", DANGER)

        stats_layout.addWidget(self.orders_stat)
        stats_layout.addWidget(self.sales_stat)
        stats_layout.addWidget(self.paid_stat)
        stats_layout.addWidget(self.unpaid_stat)
        root.addLayout(stats_layout)

        # ─── ۳. پنل فیلتر و جستجو ─────────────────────
        filter_panel = QFrame()
        filter_panel.setObjectName("filterPanel")
        filter_layout = QVBoxLayout(filter_panel)
        filter_layout.setContentsMargins(16, 14, 16, 14)
        filter_layout.setSpacing(12)

        # ردیف اول فیلترها
        row_one = QHBoxLayout()
        row_one.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("شماره فاکتور، نام مشتری یا ثبت‌کننده...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumHeight(38)
        self.search_input.textChanged.connect(self.apply_filters)

        self.payment_filter = QComboBox()
        self.payment_filter.addItem("تمام وضعیت‌های پرداخت", "all")
        self.payment_filter.addItem("فقط پرداخت‌شده", "paid")
        self.payment_filter.addItem("فقط پرداخت‌نشده", "unpaid")
        self.payment_filter.setMinimumHeight(38)
        self.payment_filter.currentIndexChanged.connect(self.apply_filters)

        row_one.addWidget(self.search_input, 5)
        row_one.addWidget(self.payment_filter, 2)
        filter_layout.addLayout(row_one)

        # ردیف دوم فیلترها (تاریخ و اقدامات)
        row_two = QHBoxLayout()
        row_two.setSpacing(10)

        date_lbl = QLabel("بازه تاریخ شمسی:")
        date_lbl.setStyleSheet(f"color: {MUTED}; font-size: 12px; font-weight: 600;")
        row_two.addWidget(date_lbl)

        self.date_from_input = QLineEdit()
        self.date_from_input.setPlaceholderText("از: 1403/01/01")
        self.date_from_input.setMinimumHeight(36)
        self.date_from_input.setFixedWidth(140)

        self.date_to_input = QLineEdit()
        self.date_to_input.setPlaceholderText("تا: 1403/12/29")
        self.date_to_input.setMinimumHeight(36)
        self.date_to_input.setFixedWidth(140)

        row_two.addWidget(self.date_from_input)
        row_two.addWidget(self.date_to_input)

        self.apply_filter_button = QPushButton("اعمال تاریخ")
        self.apply_filter_button.setMinimumHeight(36)
        self.apply_filter_button.clicked.connect(self.apply_filters)
        row_two.addWidget(self.apply_filter_button)

        self.clear_filter_button = QPushButton("پاک‌سازی فیلترها")
        self.clear_filter_button.setMinimumHeight(36)
        self.clear_filter_button.clicked.connect(self.clear_filters)
        row_two.addWidget(self.clear_filter_button)

        row_two.addStretch()

        self.result_count = QLabel("۰ فاکتور یافت شد")
        self.result_count.setStyleSheet(f"color: {MUTED}; font-size: 12px; font-weight: 700;")
        row_two.addWidget(self.result_count)

        filter_layout.addLayout(row_two)
        root.addWidget(filter_panel)

        # ─── ۴. جدول فاکتورها ─────────────────────────
        table_panel = QFrame()
        table_panel.setObjectName("tablePanel")
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(14, 14, 14, 14)
        table_layout.setSpacing(10)

        self.orders_table = QTableWidget(0, 7)
        self.orders_table.setHorizontalHeaderLabels([
            "شماره فاکتور",
            "تاریخ",
            "زمان",
            "مشتری",
            "تعداد اقلام",
            "مبلغ کل",
            "وضعیت پرداخت",
        ])
        self.orders_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.orders_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.orders_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.orders_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.orders_table.setAlternatingRowColors(True)
        self.orders_table.setShowGrid(False)
        self.orders_table.verticalHeader().setVisible(False)
        self.orders_table.verticalHeader().setDefaultSectionSize(44)

        header = self.orders_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.orders_table.cellDoubleClicked.connect(self.open_selected_order)
        table_layout.addWidget(self.orders_table, 1)

        # فوتر جدول
        table_footer = QHBoxLayout()
        hint = QLabel("💡 برای مشاهده ریزاقلام فاکتور، می‌توانید روی ردیف آن دوبار کلیک کنید.")
        hint.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        table_footer.addWidget(hint)
        table_footer.addStretch()

        self.details_button = QPushButton("مشاهده فاکتور انتخاب‌شده")
        self.details_button.setObjectName("primaryButton")
        self.details_button.setMinimumHeight(38)
        self.details_button.clicked.connect(self.open_selected_order)
        table_footer.addWidget(self.details_button)

        table_layout.addLayout(table_footer)
        root.addWidget(table_panel, 1)

        # ─── ۵. شیوه ظاهری جامع (QSS) ─────────────────
        self.setStyleSheet(
            f"""
            QWidget {{
                color: {TEXT};
                font-family: "Vazirmatn", "Noto Sans Arabic", "DejaVu Sans";
                font-size: 12px;
            }}
            QFrame#filterPanel, QFrame#tablePanel {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QLineEdit, QComboBox {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 6px 12px;
                color: {TEXT};
                selection-background-color: {GREEN_LIGHT};
                selection-color: {TEXT};
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1.5px solid {GREEN};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QPushButton {{
                background: {WHITE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 6px 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: #F2F7F4;
                border-color: #D3DFD7;
            }}
            QPushButton#primaryButton {{
                background: {GREEN};
                color: {WHITE};
                border: none;
                font-weight: 700;
                padding: 6px 18px;
            }}
            QPushButton#primaryButton:hover {{
                background: {GREEN_DARK};
            }}
            QTableWidget {{
                background: {WHITE};
                border: none;
                alternate-background-color: #F8FAF9;
                selection-background-color: {GREEN_LIGHT};
                selection-color: {TEXT};
            }}
            QHeaderView::section {{
                background: #F1F6F3;
                color: {MUTED};
                border: none;
                padding: 10px 8px;
                font-weight: 700;
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid #EDF2EF;
            }}
            """
        )

    # --------------------------------------------------
    # بارگذاری سفارش‌ها
    # --------------------------------------------------
    def refresh_orders(self):
        self.refresh_button.setEnabled(False)
        session = init_db()

        try:
            db_orders = (
                session.query(OrderArchive)
                .order_by(OrderArchive.id.desc())
                .all()
            )

            self.orders = [
                {
                    "id": order.id,
                    "factor_number": order.factor_number or "",
                    "total_price": float(order.total_price or 0),
                    "performed_by": order.performed_by or "",
                    "customer_name": customer_text(order.customer_name),
                    "total_items_count": int(order.total_items_count or 0),
                    "is_paid": bool(order.is_paid),
                    "persian_date": order.persian_date or "",
                    "persian_time": order.persian_time or "",
                }
                for order in db_orders
            ]
        except SQLAlchemyError as error:
            self.orders = []
            QMessageBox.critical(
                self,
                "خطا در بارگذاری فاکتورها",
                f"خطایی هنگام دریافت اطلاعات از دیتابیس رخ داد:\n{error}",
            )
        finally:
            session.close()
            self.refresh_button.setEnabled(True)

        self.apply_filters()

    # --------------------------------------------------
    # فیلتر کردن سفارش‌ها
    # --------------------------------------------------
    def apply_filters(self):
        search = self.search_input.text().strip().casefold()
        payment_status = self.payment_filter.currentData()

        date_from = self.date_from_input.text().strip()
        date_to = self.date_to_input.text().strip()

        if date_from and not self._valid_date(date_from):
            self.result_count.setText("فرمت تاریخ شروع نامعتبر است (مثال: 1403/01/01)")
            return

        if date_to and not self._valid_date(date_to):
            self.result_count.setText("فرمت تاریخ پایان نامعتبر است (مثال: 1403/12/29)")
            return

        if date_from and date_to and date_from > date_to:
            self.result_count.setText("تاریخ شروع نباید بعد از تاریخ پایان باشد")
            return

        filtered = []

        for order in self.orders:
            searchable = " ".join([
                order["factor_number"],
                order["customer_name"],
                order["performed_by"],
            ]).casefold()

            if search and search not in searchable:
                continue

            if payment_status == "paid" and not order["is_paid"]:
                continue
            if payment_status == "unpaid" and order["is_paid"]:
                continue

            order_date = order["persian_date"]
            if date_from and order_date < date_from:
                continue
            if date_to and order_date > date_to:
                continue

            filtered.append(order)

        self.filtered_orders = filtered
        self.populate_table(filtered)
        self.update_statistics(filtered)

    @staticmethod
    def _valid_date(value: str) -> bool:
        parts = value.split("/")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            return False
        year, month, day = map(int, parts)
        return year >= 1300 and 1 <= month <= 12 and 1 <= day <= 31

    def clear_filters(self):
        self.search_input.clear()
        self.payment_filter.setCurrentIndex(0)
        self.date_from_input.clear()
        self.date_to_input.clear()
        self.apply_filters()

    # --------------------------------------------------
    # نمایش جدول
    # --------------------------------------------------
    def populate_table(self, orders: list[dict]):
        self.orders_table.setRowCount(0)

        for row, order in enumerate(orders):
            self.orders_table.insertRow(row)

            cells = [
                (order["factor_number"], Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                (to_persian_digits(order["persian_date"]), Qt.AlignmentFlag.AlignCenter),
                (to_persian_digits(order["persian_time"]), Qt.AlignmentFlag.AlignCenter),
                (order["customer_name"], Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                (format_number(order["total_items_count"]), Qt.AlignmentFlag.AlignCenter),
                (money(order["total_price"]), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            ]

            for col, (val, align) in enumerate(cells):
                cell_item = QTableWidgetItem(str(val))
                cell_item.setTextAlignment(align)
                if col == 0:
                    cell_item.setData(Qt.ItemDataRole.UserRole, order["id"])
                self.orders_table.setItem(row, col, cell_item)

            # استفاده از Badge وضعیت پرداخت
            badge = PaymentBadge(order["is_paid"])
            self.orders_table.setCellWidget(row, 6, badge)

        self.result_count.setText(f"{format_number(len(orders))} فاکتور یافت شد")

    # --------------------------------------------------
    # محاسبه آمار
    # --------------------------------------------------
    def update_statistics(self, orders: list[dict]):
        total_count = len(orders)
        total_sales = sum(o["total_price"] for o in orders)
        paid_sales = sum(o["total_price"] for o in orders if o["is_paid"])
        unpaid_count = sum(1 for o in orders if not o["is_paid"])

        self.orders_stat.set_value(format_number(total_count))
        self.sales_stat.set_value(money(total_sales))
        self.paid_stat.set_value(money(paid_sales))
        self.unpaid_stat.set_value(format_number(unpaid_count))

    # --------------------------------------------------
    # مشاهده جزئیات
    # --------------------------------------------------
    def open_selected_order(self, row: int = None, column: int = None):
        if row is None or isinstance(row, bool):
            row = self.orders_table.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                "انتخاب فاکتور",
                "ابتدا یک فاکتور را از جدول انتخاب کنید.",
            )
            return

        factor_cell = self.orders_table.item(row, 0)
        if factor_cell is None:
            return

        order_id = factor_cell.data(Qt.ItemDataRole.UserRole)
        if order_id is None:
            return

        session = init_db()
        try:
            order = (
                session.query(OrderArchive)
                .filter(OrderArchive.id == order_id)
                .first()
            )

            if order is None:
                QMessageBox.warning(
                    self,
                    "فاکتور یافت نشد",
                    "این فاکتور دیگر در دیتابیس وجود ندارد.",
                )
                return

            order_data = {
                "factor_number": order.factor_number,
                "total_price": float(order.total_price or 0),
                "performed_by": order.performed_by or "",
                "customer_name": customer_text(order.customer_name),
                "total_items_count": int(order.total_items_count or 0),
                "is_paid": bool(order.is_paid),
                "persian_date": order.persian_date or "",
                "persian_time": order.persian_time or "",
                "items": [
                    {
                        "menu_item_name": item.menu_item_name,
                        "unit_price": float(item.unit_price or 0),
                        "quantity": int(item.quantity or 0),
                        "subtotal": float(item.subtotal or 0),
                        "recipe_snapshot_details": item.recipe_snapshot_details or "",
                    }
                    for item in order.items
                ],
            }
        except SQLAlchemyError as error:
            QMessageBox.critical(
                self,
                "خطا در خواندن فاکتور",
                f"دریافت اطلاعات با خطا مواجه شد:\n{error}",
            )
            return
        finally:
            session.close()

        dialog = OrderDetailsDialog(order_data, self)
        dialog.exec()
