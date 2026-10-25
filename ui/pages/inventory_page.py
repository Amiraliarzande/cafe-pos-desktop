# /home/amirali-arzande/cafe-pos-desktop/ui/pages/inventory_page.py

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database.db import init_db
from database.models.warehouse.product import (
    Product,
    ProductCategory,
    UnitType,
)
from database.models.warehouse.unit_measurement import (
    AreaUnit,
    CountUnit,
    DimensionUnit,
    VolumeUnit,
    WeightUnit,
)
from database.models.warehouse.warehouse_process import (
    InventoryStock,
    StockOutReason,
    StockTransaction,
    TransactionType,
)


# =========================================================
# توابع کمکی تبدیل ارقام و فرمت‌ها
# =========================================================

def to_persian_digits(text: str) -> str:
    """تبدیل اعداد انگلیسی به فارسی برای سازگاری کامل با تم RTL"""
    if text is None:
        return ""
    trans = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(text).translate(trans)


def format_qty(value: float) -> str:
    """فرمت‌بندی تعداد/مقدار با اعشار تمیز و ارقام فارسی"""
    if value is None:
        return "۰"
    formatted = f"{value:,.3f}".rstrip("0").rstrip(".")
    if not formatted or formatted == "-0":
        formatted = "0"
    return to_persian_digits(formatted)


# =========================================================
# استایل‌های سراسری کامپوننت
# =========================================================

PAGE_STYLESHEET = """
QWidget {
    font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif;
    color: #1E293B;
}

/* پنل‌های کارتی */
QFrame.cardPanel {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}

/* ورودی‌ها و کمبوباکس‌ها */
QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
    color: #0F172A;
}

QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
    border: 1px solid #28745A;
    background-color: #FFFFFF;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top left;
    width: 25px;
    border-left: none;
}

/* جدول */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    gridline-color: transparent;
    selection-background-color: #E8F5E9;
    selection-color: #1E293B;
}

QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #F1F5F9;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #475569;
    font-weight: 700;
    font-size: 13px;
    border: none;
    border-bottom: 2px solid #E2E8F0;
    padding: 8px;
}

/* دکمه‌ها */
QPushButton {
    font-size: 13px;
    font-weight: 600;
    border-radius: 8px;
    padding: 7px 16px;
    border: 1px solid #CBD5E1;
    background-color: #FFFFFF;
    color: #334155;
}

QPushButton:hover {
    background-color: #F1F5F9;
}

QPushButton:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
    border-color: #E2E8F0;
}

QPushButton.primaryBtn {
    background-color: #28745A;
    color: #FFFFFF;
    border: none;
}

QPushButton.primaryBtn:hover {
    background-color: #1F5E48;
}

QPushButton.primaryBtn:disabled {
    background-color: #93C5B5;
    color: #FFFFFF;
}

QPushButton.accentBtn {
    background-color: #0284C7;
    color: #FFFFFF;
    border: none;
}

QPushButton.accentBtn:hover {
    background-color: #0369A1;
}

QPushButton.accentBtn:disabled {
    background-color: #93C5FD;
    color: #FFFFFF;
}

QPushButton.dangerBtn {
    background-color: #FEE2E2;
    color: #DC2626;
    border: 1px solid #FCA5A5;
}

QPushButton.dangerBtn:hover {
    background-color: #FCA5A5;
    color: #991B1B;
}

QPushButton.dangerBtn:disabled {
    background-color: #F8FAFC;
    color: #CBD5E1;
    border-color: #E2E8F0;
}
"""


# =========================================================
# واحدهای اندازه‌گیری
# =========================================================

UNIT_OPTIONS = {
    UnitType.DIMENSION: {
        "متر": ("dimension_unit", "meter"),
        "سانتی‌متر": ("dimension_unit", "centimeter"),
        "اینچ": ("dimension_unit", "inch"),
    },
    UnitType.WEIGHT: {
        "گرم": ("weight_unit", "gram"),
        "کیلوگرم": ("weight_unit", "kilogram"),
        "میلی‌گرم": ("weight_unit", "milligram"),
        "تن": ("weight_unit", "ton"),
    },
    UnitType.VOLUME: {
        "لیتر": ("volume_unit", "liter"),
        "میلی‌لیتر": ("volume_unit", "milliliter"),
        "گالن": ("volume_unit", "gallon"),
    },
    UnitType.AREA: {
        "متر مربع": ("area_unit", "square_meter"),
        "سانتی‌متر مربع": ("area_unit", "square_centimeter"),
    },
    UnitType.COUNT: {
        "عدد": ("count_unit", "quantity_per_unit"),
    },
}

UNIT_TYPE_LABELS = {
    UnitType.DIMENSION: "طول",
    UnitType.WEIGHT: "وزن",
    UnitType.VOLUME: "حجم",
    UnitType.AREA: "مساحت",
    UnitType.COUNT: "تعدادی",
}

UNIT_MODEL_INFO = {
    "dimension_unit": (DimensionUnit, "dimension_unit_id"),
    "weight_unit": (WeightUnit, "weight_unit_id"),
    "volume_unit": (VolumeUnit, "volume_unit_id"),
    "area_unit": (AreaUnit, "area_unit_id"),
    "count_unit": (CountUnit, "count_unit_id"),
}


# =========================================================
# نشانگر گرافیکی وضعیت موجودی (Badge)
# =========================================================

class StockBadge(QFrame):
    """بج مدرن برای نمایش وضعیت موجود بودن کالا"""
    def __init__(self, quantity: float, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel()
        label.setStyleSheet("font-size: 11px; font-weight: 700; background: transparent; border: none;")

        if quantity <= 0:
            label.setText("ناموجود")
            label.setStyleSheet("color: #DC2626;")
            self.setStyleSheet("background-color: #FEE2E2; border: 1px solid #FECACA; border-radius: 6px;")
        elif quantity < 5:
            label.setText("موجودی کم")
            label.setStyleSheet("color: #D97706;")
            self.setStyleSheet("background-color: #FEF3C7; border: 1px solid #FDE68A; border-radius: 6px;")
        else:
            label.setText("موجود")
            label.setStyleSheet("color: #166534;")
            self.setStyleSheet("background-color: #DCFCE7; border: 1px solid #BBF7D0; border-radius: 6px;")

        layout.addWidget(label)


# =========================================================
# کارت آماری هدر (Stat Card)
# =========================================================

class StatCard(QFrame):
    def __init__(self, title: str, initial_value: str = "۰", accent_color: str = "#28745A", parent=None):
        super().__init__(parent)
        self.setProperty("class", "cardPanel")
        self.setStyleSheet(f"""
            QFrame.cardPanel {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-right: 4px solid {accent_color};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600; border: none; background: transparent;")

        self.val_label = QLabel(initial_value)
        self.val_label.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {accent_color}; border: none; background: transparent;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.val_label)

    def set_value(self, val: str):
        self.val_label.setText(to_persian_digits(str(val)))


# =========================================================
# دیالوگ ورود و خروج کالا
# =========================================================

class StockMovementDialog(QDialog):
    def __init__(self, parent, title, movement_type, current_quantity):
        super().__init__(parent)
        self.movement_type = movement_type

        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(PAGE_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # باکس اطلاعات کالا
        info_box = QFrame()
        info_box.setProperty("class", "cardPanel")
        info_box_layout = QHBoxLayout(info_box)
        info_box_layout.setContentsMargins(12, 10, 12, 10)

        info_title = QLabel("موجودی فعلی کالا در انبار:")
        info_title.setStyleSheet("font-weight: 600; color: #475569;")
        current_label = QLabel(format_qty(current_quantity))
        current_label.setStyleSheet("font-size: 15px; font-weight: 800; color: #28745A;")

        info_box_layout.addWidget(info_title)
        info_box_layout.addStretch()
        info_box_layout.addWidget(current_label)
        layout.addWidget(info_box)

        # فرم دریافت مقادیر بدون ارجاع ناهمگون به لایه
        form_frame = QFrame()
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)

        # مقدار تغییر
        qty_title = QLabel("مقدار عملیات:" if movement_type == TransactionType.STOCK_IN else "مقدار خروج:")
        qty_title.setStyleSheet("font-weight: 600; color: #334155;")
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setDecimals(3)
        self.quantity_input.setRange(0.001, 1_000_000_000)
        self.quantity_input.setValue(1)
        self.quantity_input.setSingleStep(1)
        self.quantity_input.setMinimumHeight(38)
        form_layout.addWidget(qty_title)
        form_layout.addWidget(self.quantity_input)

        # علت عملیات
        reason_title = QLabel("دلیل / بابت:")
        reason_title.setStyleSheet("font-weight: 600; color: #334155;")
        self.reason_combo = QComboBox()
        self.reason_combo.setMinimumHeight(38)
        self.reason_map = {}

        if movement_type == TransactionType.STOCK_IN:
            self.reason_combo.addItem("خرید / تأمین جدید")
            self.reason_combo.addItem("اصلاح موجودی (انبارگردانی)")
            self.reason_combo.addItem("برگشت از سفارش")
            self.reason_combo.addItem("سایر موارد")

            self.reason_map = {
                "خرید / تأمین جدید": "خرید / تأمین",
                "اصلاح موجودی (انبارگردانی)": "اصلاح موجودی",
                "برگشت از سفارش": "برگشت از فروش",
                "سایر موارد": "سایر",
            }
        else:
            self.reason_combo.addItem("مصرف روزانه کافه / تولید")
            self.reason_combo.addItem("فروش مستقیم")
            self.reason_combo.addItem("ضایعات و خرابی")
            self.reason_combo.addItem("انتقال به انبار دیگر")
            self.reason_combo.addItem("سایر موارد")

            self.reason_map = {
                "مصرف روزانه کافه / تولید": StockOutReason.OTHER,
                "فروش مستقیم": StockOutReason.SALE,
                "ضایعات و خرابی": StockOutReason.DAMAGE,
                "انتقال به انبار دیگر": StockOutReason.TRANSFER,
                "سایر موارد": StockOutReason.OTHER,
            }

        form_layout.addWidget(reason_title)
        form_layout.addWidget(self.reason_combo)

        # فیلد توضیحات
        note_title = QLabel("توضیحات تکمیلی (اختیاری):")
        note_title.setStyleSheet("font-weight: 600; color: #334155;")
        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText("مثلاً شماره فاکتور خرید، علت ضایعات و...")
        self.note_input.setMaximumHeight(75)
        form_layout.addWidget(note_title)
        form_layout.addWidget(self.note_input)

        layout.addWidget(form_frame)

        # دکمه‌ها
        buttons_layout = QHBoxLayout()
        self.submit_btn = QPushButton("ثبت عملیات انبار")
        self.submit_btn.setProperty("class", "primaryBtn")
        self.submit_btn.setMinimumHeight(38)
        self.submit_btn.clicked.connect(self.validate_and_accept)

        self.cancel_btn = QPushButton("انصراف")
        self.cancel_btn.setMinimumHeight(38)
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(self.submit_btn, 2)
        buttons_layout.addWidget(self.cancel_btn, 1)
        layout.addLayout(buttons_layout)

    def validate_and_accept(self):
        if self.quantity_input.value() <= 0:
            QMessageBox.warning(self, "خطا", "مقدار باید بزرگتر از صفر باشد.")
            return
        self.accept()

    def get_data(self):
        reason_text = self.reason_combo.currentText()
        reason = self.reason_map.get(reason_text, None) if self.movement_type == TransactionType.STOCK_OUT else None

        return {
            "quantity": self.quantity_input.value(),
            "reason": reason,
            "note": self.note_input.toPlainText().strip(),
            "reason_text": reason_text,
        }


# =========================================================
# صفحه تاریخچه گردش انبار
# =========================================================

class StockHistoryDialog(QDialog):
    def __init__(self, parent, product_name: str, transactions: list):
        super().__init__(parent)
        self.setWindowTitle(f"گردش انبار: {product_name}")
        self.resize(880, 520)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(PAGE_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # عنوان
        title_box = QHBoxLayout()
        title = QLabel(f"تاریخچه گردش کالا: {product_name}")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #1E293B;")
        title_box.addWidget(title)
        title_box.addStretch()

        count_badge = QLabel(f"تعداد تراکنش‌ها: {to_persian_digits(str(len(transactions)))}")
        count_badge.setStyleSheet("background: #F1F5F9; padding: 4px 10px; border-radius: 6px; font-weight: 600; color: #475569;")
        title_box.addWidget(count_badge)
        layout.addLayout(title_box)

        # جدول تراکنش‌ها
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "نوع عملیات",
            "مقدار تغییر",
            "موجودی قبل",
            "موجودی پس از تغییر",
            "تاریخ ثبت",
            "توضیحات",
        ])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(40)

        header = table.horizontalHeader()
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        for col in range(5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        table.setRowCount(len(transactions))
        type_labels = {
            TransactionType.INITIAL: "موجودی اولیه",
            TransactionType.STOCK_IN: "افزایش (ورود)",
            TransactionType.STOCK_OUT: "کاهش (خروج)",
        }

        for row, tx in enumerate(transactions):
            date_str = tx.transaction_date.strftime("%Y/%m/%d %H:%M") if tx.transaction_date else "—"
            op_label = type_labels.get(tx.transaction_type, "نامشخص")

            items = [
                QTableWidgetItem(op_label),
                QTableWidgetItem(format_qty(tx.quantity_changed)),
                QTableWidgetItem(format_qty(tx.quantity_before)),
                QTableWidgetItem(format_qty(tx.quantity_after)),
                QTableWidgetItem(to_persian_digits(date_str)),
                QTableWidgetItem(tx.note or "—"),
            ]

            for c, itm in enumerate(items):
                if c in (1, 2, 3, 4):
                    itm.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, c, itm)

        layout.addWidget(table)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        close_btn = QPushButton("بستن")
        close_btn.setFixedWidth(120)
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)


# =========================================================
# صفحه اصلی مدیریت انبار (InventoryPage)
# =========================================================

class InventoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = init_db()
        self.selected_product_id = None
        self._closing = False

        self.setStyleSheet(PAGE_STYLESHEET)
        self.setup_ui()
        self.load_categories()
        self.load_products()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        # -------------------------------------------------
        # ۱. هدر و کارت‌های آماری سریع
        # -------------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # عنوان و توضیحات
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("مدیریت جامع انبار")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A;")
        subtitle = QLabel("کنترل لحظه‌ای موجودی کالاها، دسته‌بندی و گردش انبار کافه")
        subtitle.setStyleSheet("font-size: 12px; color: #64748B;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box, 2)

        # کارت‌های آمار
        self.card_total = StatCard("کل کالاها", "۰", "#28745A")
        self.card_available = StatCard("کالاهای موجود", "۰", "#16A34A")
        self.card_low = StatCard("موجودی کم", "۰", "#D97706")
        self.card_out = StatCard("ناموجود", "۰", "#DC2626")

        header_layout.addWidget(self.card_total, 1)
        header_layout.addWidget(self.card_available, 1)
        header_layout.addWidget(self.card_low, 1)
        header_layout.addWidget(self.card_out, 1)

        root.addLayout(header_layout)

        # -------------------------------------------------
        # ۲. پنل تعریف و ویرایش کالا
        # -------------------------------------------------
        form_panel = QFrame()
        form_panel.setProperty("class", "cardPanel")
        form_layout = QVBoxLayout(form_panel)
        form_layout.setContentsMargins(16, 14, 16, 14)
        form_layout.setSpacing(12)

        form_title = QLabel("مشخصات و ثبت کالا")
        form_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1E293B;")
        form_layout.addWidget(form_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        # فیلد نام
        lbl_name = QLabel("نام کالا:")
        lbl_name.setStyleSheet("font-weight: 600; color: #475569;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثلاً: قهوه کلمبیا ۱۰۰٪ عربیکا")
        self.name_input.setMinimumHeight(36)
        grid.addWidget(lbl_name, 0, 0)
        grid.addWidget(self.name_input, 1, 0)

        # فیلد دسته‌بندی
        lbl_cat = QLabel("دسته‌بندی:")
        lbl_cat.setStyleSheet("font-weight: 600; color: #475569;")

        cat_box = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.setMinimumHeight(36)
        self.add_category_button = QPushButton("＋ دسته جدید")
        self.add_category_button.setMinimumHeight(36)
        self.add_category_button.clicked.connect(self.add_category)
        cat_box.addWidget(self.category_combo, 1)
        cat_box.addWidget(self.add_category_button)

        grid.addWidget(lbl_cat, 0, 1)
        grid.addLayout(cat_box, 1, 1)

        # نوع واحد و واحد سنجش
        lbl_unit_type = QLabel("نوع واحد:")
        lbl_unit_type.setStyleSheet("font-weight: 600; color: #475569;")
        self.unit_type_combo = QComboBox()
        self.unit_type_combo.setMinimumHeight(36)
        for unit_type, label in UNIT_TYPE_LABELS.items():
            self.unit_type_combo.addItem(label, unit_type)
        self.unit_type_combo.currentIndexChanged.connect(self.update_unit_options)

        grid.addWidget(lbl_unit_type, 0, 2)
        grid.addWidget(self.unit_type_combo, 1, 2)

        lbl_unit = QLabel("واحد اندازه‌گیری:")
        lbl_unit.setStyleSheet("font-weight: 600; color: #475569;")
        self.unit_combo = QComboBox()
        self.unit_combo.setMinimumHeight(36)

        grid.addWidget(lbl_unit, 0, 3)
        grid.addWidget(self.unit_combo, 1, 3)

        # موجودی اول دوره
        lbl_init_qty = QLabel("موجودی اول دوره:")
        lbl_init_qty.setStyleSheet("font-weight: 600; color: #475569;")
        self.initial_quantity_input = QDoubleSpinBox()
        self.initial_quantity_input.setDecimals(3)
        self.initial_quantity_input.setRange(0, 1_000_000_000)
        self.initial_quantity_input.setSingleStep(1)
        self.initial_quantity_input.setMinimumHeight(36)
        self.initial_quantity_input.setToolTip("این مقدار فقط در زمان ایجاد اولیه کالا قابل تعیین است.")

        grid.addWidget(lbl_init_qty, 0, 4)
        grid.addWidget(self.initial_quantity_input, 1, 4)

        form_layout.addLayout(grid)

        # راهنما و دکمه‌های فرم
        form_actions = QHBoxLayout()
        form_actions.setContentsMargins(0, 4, 0, 0)

        self.initial_quantity_hint = QLabel("💡 موجودی اولیه فقط هنگام ثبت اولیه کالا اعمال می‌شود.")
        self.initial_quantity_hint.setStyleSheet("color: #64748B; font-size: 12px;")
        form_actions.addWidget(self.initial_quantity_hint)
        form_actions.addStretch()

        self.save_product_button = QPushButton("ثبت کالای جدید")
        self.save_product_button.setProperty("class", "primaryBtn")
        self.save_product_button.setMinimumHeight(36)
        self.save_product_button.clicked.connect(self.save_product)

        self.clear_button = QPushButton("پاک‌کردن فرم")
        self.clear_button.setMinimumHeight(36)
        self.clear_button.clicked.connect(self.clear_form)

        self.delete_product_button = QPushButton("حذف کالا")
        self.delete_product_button.setProperty("class", "dangerBtn")
        self.delete_product_button.setMinimumHeight(36)
        self.delete_product_button.setEnabled(False)
        self.delete_product_button.clicked.connect(self.delete_product)

        form_actions.addWidget(self.clear_button)
        form_actions.addWidget(self.delete_product_button)
        form_actions.addWidget(self.save_product_button)

        form_layout.addLayout(form_actions)
        root.addWidget(form_panel)

        # -------------------------------------------------
        # ۳. پنل فیلترها و عملیات سریع کالاها
        # -------------------------------------------------
        filters_panel = QFrame()
        filters_panel.setProperty("class", "cardPanel")
        filters_layout = QHBoxLayout(filters_panel)
        filters_layout.setContentsMargins(14, 10, 14, 10)
        filters_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 جستجوی نام کالا...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumHeight(36)
        self.search_input.textChanged.connect(self.load_products)

        self.filter_category_combo = QComboBox()
        self.filter_category_combo.setMinimumHeight(36)
        self.filter_category_combo.currentIndexChanged.connect(self.load_products)

        self.stock_filter_combo = QComboBox()
        self.stock_filter_combo.setMinimumHeight(36)
        self.stock_filter_combo.addItem("همه موجودی‌ها", "all")
        self.stock_filter_combo.addItem("کالاهای موجود", "available")
        self.stock_filter_combo.addItem("کالاهای ناموجود", "empty")
        self.stock_filter_combo.addItem("موجودی کم (کمتر از ۵)", "low")
        self.stock_filter_combo.currentIndexChanged.connect(self.load_products)

        filters_layout.addWidget(self.search_input, 2)
        filters_layout.addWidget(self.filter_category_combo, 1)
        filters_layout.addWidget(self.stock_filter_combo, 1)

        root.addWidget(filters_panel)

        # -------------------------------------------------
        # ۴. پنل جدول و دکمه‌های گردش انبار
        # -------------------------------------------------
        table_panel = QFrame()
        table_panel.setProperty("class", "cardPanel")
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(14, 14, 14, 14)
        table_layout.setSpacing(10)

        table_top_bar = QHBoxLayout()
        table_title = QLabel("فهرست و موجودی انبار")
        table_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1E293B;")
        table_top_bar.addWidget(table_title)
        table_top_bar.addStretch()

        # دکمه رفرش / به‌روزرسانی زنده اطلاعات دیتابیس
        self.refresh_button = QPushButton("🔄 به‌روزرسانی")
        self.refresh_button.setToolTip("بارگذاری مجدد اطلاعات از دیتابیس")
        self.refresh_button.setMinimumHeight(34)
        self.refresh_button.clicked.connect(self.refresh_data)

        # دکمه‌های تغییر موجودی
        self.stock_in_button = QPushButton("➕ افزایش موجودی")
        self.stock_in_button.setProperty("class", "primaryBtn")
        self.stock_in_button.setMinimumHeight(34)
        self.stock_in_button.clicked.connect(self.increase_stock)
        self.stock_in_button.setEnabled(False)

        self.stock_out_button = QPushButton("➖ خروج / مصرف")
        self.stock_out_button.setMinimumHeight(34)
        self.stock_out_button.clicked.connect(self.decrease_stock)
        self.stock_out_button.setEnabled(False)

        self.history_button = QPushButton("📊 گردش انبار")
        self.history_button.setProperty("class", "accentBtn")
        self.history_button.setMinimumHeight(34)
        self.history_button.clicked.connect(self.show_stock_history)
        self.history_button.setEnabled(False)

        table_top_bar.addWidget(self.refresh_button)
        table_top_bar.addWidget(self.stock_in_button)
        table_top_bar.addWidget(self.stock_out_button)
        table_top_bar.addWidget(self.history_button)
        table_layout.addLayout(table_top_bar)

        # جدول کالاها
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "شناسه",
            "نام کالا",
            "دسته‌بندی",
            "نوع واحد",
            "واحد اندازه‌گیری",
            "موجودی فعلی",
            "وضعیت",
        ])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)

        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in range(2, 7):
            header_view.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        self.table.itemSelectionChanged.connect(self.on_product_selected)
        table_layout.addWidget(self.table, 1)

        root.addWidget(table_panel, 1)
        self.update_unit_options()

    # -----------------------------------------------------
    # ابزارهای کمکی
    # -----------------------------------------------------

    def refresh_data(self):
        """بازخوانی تازه تمام داده‌ها مستقیماً از دیتابیس"""
        try:
            self.db.expire_all()
            self.load_categories()
            self.load_products()
        except Exception as exc:
            QMessageBox.critical(self, "خطا", f"خطا در به‌روزرسانی اطلاعات:\n{exc}")

    def get_current_product(self):
        if self.selected_product_id is None:
            QMessageBox.warning(self, "انتخاب کالا", "لطفاً ابتدا یک کالا را از جدول انتخاب کنید.")
            return None

        return self.db.query(Product).filter(Product.id == self.selected_product_id).first()

    def get_stock(self, product_id):
        return self.db.query(InventoryStock).filter(InventoryStock.product_id == product_id).first()

    # -----------------------------------------------------
    # دسته‌بندی‌ها
    # -----------------------------------------------------

    def load_categories(self):
        try:
            current_category_id = self.category_combo.currentData()
            current_filter_cat_id = self.filter_category_combo.currentData()

            categories = self.db.query(ProductCategory).order_by(ProductCategory.name).all()

            self.category_combo.blockSignals(True)
            self.category_combo.clear()
            self.category_combo.addItem("بدون دسته‌بندی", None)
            for cat in categories:
                self.category_combo.addItem(cat.name, cat.id)

            idx = self.category_combo.findData(current_category_id)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            self.category_combo.blockSignals(False)

            self.filter_category_combo.blockSignals(True)
            self.filter_category_combo.clear()
            self.filter_category_combo.addItem("همه دسته‌بندی‌ها", None)
            for cat in categories:
                self.filter_category_combo.addItem(cat.name, cat.id)

            filter_idx = self.filter_category_combo.findData(current_filter_cat_id)
            if filter_idx >= 0:
                self.filter_category_combo.setCurrentIndex(filter_idx)
            self.filter_category_combo.blockSignals(False)
        except Exception as exc:
            QMessageBox.critical(self, "خطا", f"خطا در دریافت دسته‌بندی‌ها: {exc}")

    def add_category(self):
        name, accepted = QInputDialog.getText(self, "دسته‌بندی جدید", "نام دسته‌بندی را وارد کنید:")
        if not accepted:
            return

        name = name.strip()
        if not name:
            QMessageBox.warning(self, "نام نامعتبر", "نام دسته‌بندی نمی‌تواند خالی باشد.")
            return

        try:
            existing = self.db.query(ProductCategory).filter(ProductCategory.name == name).first()
            if existing:
                QMessageBox.information(self, "دسته‌بندی تکراری", "این دسته‌بندی از قبل ثبت شده است.")
                return

            category = ProductCategory(name=name)
            self.db.add(category)
            self.db.commit()

            self.load_categories()
            idx = self.category_combo.findData(category.id)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            self.load_products()

        except Exception as exc:
            self.db.rollback()
            QMessageBox.critical(self, "خطا", f"ثبت دسته‌بندی انجام نشد:\n{exc}")

    # -----------------------------------------------------
    # واحدهای اندازه‌گیری
    # -----------------------------------------------------

    def update_unit_options(self, *_):
        unit_type = self.unit_type_combo.currentData()
        self.unit_combo.clear()

        if unit_type is None:
            return

        for label, unit_info in UNIT_OPTIONS.get(unit_type, {}).items():
            self.unit_combo.addItem(label, unit_info)

    def get_unit_label(self, product):
        unit_type = product.unit_type
        if unit_type not in UNIT_OPTIONS:
            return "—"

        unit_info = None
        for relationship_name, (model, foreign_key_name) in UNIT_MODEL_INFO.items():
            unit_record = getattr(product, relationship_name, None)
            if unit_record is not None:
                unit_info = (relationship_name, unit_record)
                break

        if unit_info is None:
            return "—"

        rel_name, unit_record = unit_info
        for label, (r_name, field_name) in UNIT_OPTIONS[unit_type].items():
            if r_name == rel_name:
                if getattr(unit_record, field_name, None) is not None:
                    return label

        return "—"

    def create_unit_record(self, unit_type, unit_info):
        relationship_name, field_name = unit_info
        model, foreign_key_name = UNIT_MODEL_INFO[relationship_name]

        unit_record = model()
        setattr(unit_record, field_name, 1)
        self.db.add(unit_record)
        self.db.flush()

        return {
            "relationship_name": relationship_name,
            "foreign_key_name": foreign_key_name,
            "unit_id": unit_record.id,
        }

    def assign_unit(self, product, unit_type, unit_info):
        unit_data = self.create_unit_record(unit_type, unit_info)
        for _, (_, foreign_key_name) in UNIT_MODEL_INFO.items():
            setattr(product, foreign_key_name, None)

        setattr(product, unit_data["foreign_key_name"], unit_data["unit_id"])
        product.unit_type = unit_type

    # -----------------------------------------------------
    # ثبت، ویرایش و فیلتر کالاها
    # -----------------------------------------------------

    def save_product(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "خطا", "نام کالا الزامی است.")
            self.name_input.setFocus()
            return

        unit_type = self.unit_type_combo.currentData()
        unit_info = self.unit_combo.currentData()
        if unit_type is None or unit_info is None:
            QMessageBox.warning(self, "خطا", "لطفاً نوع واحد و واحد اندازه‌گیری را مشخص کنید.")
            return

        category_id = self.category_combo.currentData()

        try:
            dup_query = self.db.query(Product).filter(Product.name == name)
            if self.selected_product_id is not None:
                dup_query = dup_query.filter(Product.id != self.selected_product_id)

            if dup_query.first():
                QMessageBox.warning(self, "نام تکراری", "کالایی با این نام قبلاً تعریف شده است.")
                return

            if self.selected_product_id is None:
                product = Product(name=name, category_id=category_id)
                self.db.add(product)
                self.db.flush()

                self.assign_unit(product, unit_type, unit_info)

                initial_qty = self.initial_quantity_input.value()
                stock = InventoryStock(
                    product_id=product.id,
                    initial_quantity=initial_qty,
                    current_quantity=initial_qty,
                )
                self.db.add(stock)
                self.db.flush()

                if initial_qty > 0:
                    tx = StockTransaction(
                        product_id=product.id,
                        transaction_type=TransactionType.INITIAL,
                        quantity_changed=initial_qty,
                        quantity_before=0,
                        quantity_after=initial_qty,
                        note="ثبت موجودی اول دوره",
                    )
                    self.db.add(tx)

                msg = "کالای جدید با موفقیت ثبت شد."
            else:
                product = self.db.query(Product).filter(Product.id == self.selected_product_id).first()
                if not product:
                    QMessageBox.warning(self, "خطا", "کالای موردنظر یافت نشد.")
                    self.clear_form()
                    self.load_products()
                    return

                product.name = name
                product.category_id = category_id
                self.assign_unit(product, unit_type, unit_info)
                msg = "اطلاعات کالا با موفقیت ویرایش شد."

            self.db.commit()
            self.clear_form()
            self.load_products()
            QMessageBox.information(self, "موفق", msg)

        except Exception as exc:
            self.db.rollback()
            QMessageBox.critical(self, "خطا", f"عملیات ذخیره‌سازی ناموفق بود:\n{exc}")

    def load_products(self, *_):
        try:
            query = self.db.query(Product)
            search_text = self.search_input.text().strip()
            if search_text:
                query = query.filter(Product.name.ilike(f"%{search_text}%"))

            cat_id = self.filter_category_combo.currentData()
            if cat_id is not None:
                query = query.filter(Product.category_id == cat_id)

            products = query.order_by(Product.id.desc()).all()
            stock_filter = self.stock_filter_combo.currentData()

            total_count = len(products)
            available_count = 0
            low_count = 0
            out_count = 0

            filtered_products = []

            for product in products:
                stock = self.get_stock(product.id)
                current_qty = stock.current_quantity if stock else 0

                # محاسبه آمارها
                if current_qty <= 0:
                    out_count += 1
                elif current_qty < 5:
                    low_count += 1
                    available_count += 1
                else:
                    available_count += 1

                # اعمال فیلتر استاک
                if stock_filter == "available" and current_qty <= 0:
                    continue
                elif stock_filter == "empty" and current_qty > 0:
                    continue
                elif stock_filter == "low" and not (0 < current_qty < 5):
                    continue

                filtered_products.append((product, stock, current_qty))

            # به‌روزرسانی کارت‌های هدر
            self.card_total.set_value(str(total_count))
            self.card_available.set_value(str(available_count))
            self.card_low.set_value(str(low_count))
            self.card_out.set_value(str(out_count))

            # پر کردن جدول
            self.table.blockSignals(True)
            self.table.setRowCount(0)

            for product, stock, current_qty in filtered_products:
                row = self.table.rowCount()
                self.table.insertRow(row)

                cat_name = product.category.name if product.category else "بدون دسته‌بندی"
                unit_label = self.get_unit_label(product)
                unit_type_name = UNIT_TYPE_LABELS.get(product.unit_type, "—")

                # ستون ۰: نگهداری دقیق ID در UserRole
                id_item = QTableWidgetItem(str(product.id))
                id_item.setData(Qt.ItemDataRole.UserRole, product.id)
                self.table.setItem(row, 0, id_item)

                name_item = QTableWidgetItem(product.name)
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 1, name_item)

                cat_item = QTableWidgetItem(cat_name)
                cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 2, cat_item)

                type_item = QTableWidgetItem(unit_type_name)
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 3, type_item)

                unit_item = QTableWidgetItem(unit_label)
                unit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 4, unit_item)

                qty_item = QTableWidgetItem(format_qty(current_qty))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 5, qty_item)

                # ستون بج وضعیت
                badge_widget = QWidget()
                b_layout = QHBoxLayout(badge_widget)
                b_layout.setContentsMargins(4, 4, 4, 4)
                b_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                b_layout.addWidget(StockBadge(current_qty))
                self.table.setCellWidget(row, 6, badge_widget)

            self.table.blockSignals(False)

        except Exception as exc:
            self.table.blockSignals(False)
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری اطلاعات انبار:\n{exc}")

    def on_product_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return

        id_item = self.table.item(row, 0)
        if id_item is None:
            return

        # دریافت ایمن ID از UserRole یا با تبدیل ارقام فارسی به انگلیسی
        p_id = id_item.data(Qt.ItemDataRole.UserRole)
        if p_id is None:
            raw_text = id_item.text().translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
            try:
                p_id = int(raw_text)
            except ValueError:
                return

        product = self.db.query(Product).filter(Product.id == p_id).first()
        if not product:
            return

        self.selected_product_id = product.id
        self.name_input.setText(product.name)

        idx = self.category_combo.findData(product.category_id)
        self.category_combo.setCurrentIndex(max(idx, 0))

        unit_type_idx = self.unit_type_combo.findData(product.unit_type)
        if unit_type_idx >= 0:
            self.unit_type_combo.setCurrentIndex(unit_type_idx)

        unit_str = self.get_unit_label(product)
        unit_idx = self.unit_combo.findText(unit_str)
        if unit_idx >= 0:
            self.unit_combo.setCurrentIndex(unit_idx)

        self.initial_quantity_input.setValue(0)
        self.initial_quantity_input.setEnabled(False)
        self.initial_quantity_hint.setText("⚠️ موجودی کالا تنها از طریق دکمه‌های ورود/خروج قابل ویرایش است.")

        self.save_product_button.setText("ذخیره تغییرات")
        self.delete_product_button.setEnabled(True)
        self.stock_in_button.setEnabled(True)
        self.stock_out_button.setEnabled(True)
        self.history_button.setEnabled(True)

    def clear_form(self):
        self.selected_product_id = None
        self.name_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.unit_type_combo.setCurrentIndex(0)
        self.update_unit_options()

        self.initial_quantity_input.setEnabled(True)
        self.initial_quantity_input.setValue(0)
        self.initial_quantity_hint.setText("💡 موجودی اولیه فقط هنگام ثبت اولیه کالا اعمال می‌شود.")

        self.save_product_button.setText("ثبت کالای جدید")
        self.delete_product_button.setEnabled(False)
        self.stock_in_button.setEnabled(False)
        self.stock_out_button.setEnabled(False)
        self.history_button.setEnabled(False)

        self.table.clearSelection()
        self.name_input.setFocus()

    # -----------------------------------------------------
    # افزایش، کاهش و گردش انبار
    # -----------------------------------------------------

    def increase_stock(self):
        self.change_stock(TransactionType.STOCK_IN)

    def decrease_stock(self):
        self.change_stock(TransactionType.STOCK_OUT)

    def change_stock(self, movement_type):
        product = self.get_current_product()
        if not product:
            return

        stock = self.get_stock(product.id)
        if not stock:
            QMessageBox.warning(self, "خطا", "رکورد موجودی برای این کالا تعریف نشده است.")
            return

        is_in = movement_type == TransactionType.STOCK_IN
        title = "ثبت ورود کالا به انبار" if is_in else "ثبت خروج / مصرف کالا"

        dialog = StockMovementDialog(self, title, movement_type, stock.current_quantity)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()
        qty = data["quantity"]
        before = stock.current_quantity

        if is_in:
            after = before + qty
        else:
            if qty > before:
                QMessageBox.warning(
                    self,
                    "موجودی ناکافی",
                    f"مقدار خروجی درخواستی ({format_qty(qty)}) از موجودی فعلی انبار ({format_qty(before)}) بیشتر است.",
                )
                return
            after = before - qty

        try:
            stock.current_quantity = after
            stock.updated_at = datetime.utcnow()

            note_parts = [data["reason_text"]]
            if data["note"]:
                note_parts.append(data["note"])

            tx = StockTransaction(
                product_id=product.id,
                transaction_type=movement_type,
                quantity_changed=qty,
                quantity_before=before,
                quantity_after=after,
                stock_out_reason=data["reason"],
                note=" - ".join(note_parts),
            )

            self.db.add(tx)
            self.db.commit()

            self.load_products()
            QMessageBox.information(
                self,
                "عملیات موفق",
                f"عملیات با موفقیت انجام شد.\nموجودی جدید: {format_qty(after)}",
            )
        except Exception as exc:
            self.db.rollback()
            QMessageBox.critical(self, "خطا", f"تغییر موجودی ناموفق بود:\n{exc}")

    def show_stock_history(self):
        product = self.get_current_product()
        if not product:
            return

        try:
            transactions = (
                self.db.query(StockTransaction)
                .filter(StockTransaction.product_id == product.id)
                .order_by(StockTransaction.transaction_date.desc(), StockTransaction.id.desc())
                .all()
            )
            dlg = StockHistoryDialog(self, product.name, transactions)
            dlg.exec()
        except Exception as exc:
            QMessageBox.critical(self, "خطا", f"خطا در دریافت تاریخچه گردش کالا:\n{exc}")

    # -----------------------------------------------------
    # حذف کالا
    # -----------------------------------------------------

    def delete_product(self):
        product = self.get_current_product()
        if not product:
            return

        stock = self.get_stock(product.id)
        has_history = self.db.query(StockTransaction.id).filter(StockTransaction.product_id == product.id).first() is not None

        if has_history:
            QMessageBox.warning(
                self,
                "امکان حذف وجود ندارد",
                "این کالا دارای گردش انبار و تراکنش‌های ثبت‌شده است و برای حفظ یکپارچگی گزارش‌ها امکان حذف فیزیکی آن وجود ندارد.",
            )
            return

        if stock and stock.current_quantity != 0:
            QMessageBox.warning(
                self,
                "خطا در حذف",
                f"موجودی کالا باید صفر باشد. موجودی فعلی: {format_qty(stock.current_quantity)}",
            )
            return

        answer = QMessageBox.question(
            self,
            "تأیید حذف",
            f"آیا از حذف کامل کالای «{product.name}» مطمئن هستید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            if stock:
                self.db.delete(stock)
            self.db.delete(product)
            self.db.commit()

            self.clear_form()
            self.load_products()
            QMessageBox.information(self, "موفق", "کالا با موفقیت حذف گردید.")
        except Exception as exc:
            self.db.rollback()
            QMessageBox.critical(self, "خطا", f"خطا در حذف کالا:\n{exc}")

    def closeEvent(self, event):
        if not self._closing:
            self._closing = True
            try:
                self.db.close()
            except Exception:
                pass
        super().closeEvent(event)
