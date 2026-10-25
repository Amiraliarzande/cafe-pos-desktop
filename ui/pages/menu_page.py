# /home/amirali-arzande/cafe-pos-desktop/ui/pages/menu_page.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
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

from sqlalchemy.exc import SQLAlchemyError

from database.db import init_db
from database.models.cafe.menu import (
    MenuCategory,
    MenuItem,
    RecipeItem,
)
from database.models.warehouse.product import Product, UnitType

# =========================================================
# توابع کمکی تبدیل ارقام و فرمت‌ها
# =========================================================

def to_persian_digits(text: str) -> str:
    """تبدیل اعداد انگلیسی به فارسی"""
    if text is None:
        return ""
    trans = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(text).translate(trans)


def format_price(amount) -> str:
    """فرمت ۳ رقم ۳ رقم قیمت با ارقام فارسی"""
    try:
        val = int(amount or 0)
        return to_persian_digits(f"{val:,}")
    except (ValueError, TypeError):
        return "۰"


def format_amount(value) -> str:
    """نمایش مقدار مواد اولیه بدون صفرهای اعشاری زائد با ارقام فارسی"""
    try:
        val = float(value or 0)
        if val.is_integer():
            formatted = str(int(val))
        else:
            formatted = f"{val:.3f}".rstrip("0").rstrip(".")
        return to_persian_digits(formatted)
    except Exception:
        return "۰"


def unit_label(product):
    """برگرداندن برچسب واحد اندازه‌گیری ماده اولیه انبار"""
    if product is None:
        return ""

    unit_type = getattr(product, "unit_type", None)

    unit_options = {
        UnitType.DIMENSION: [
            ("dimension_unit", "متر"),
            ("dimension_unit", "سانتی‌متر"),
            ("dimension_unit", "اینچ"),
        ],
        UnitType.WEIGHT: [
            ("weight_unit", "گرم"),
            ("weight_unit", "کیلوگرم"),
            ("weight_unit", "میلی‌گرم"),
            ("weight_unit", "تن"),
        ],
        UnitType.VOLUME: [
            ("volume_unit", "لیتر"),
            ("volume_unit", "میلی‌لیتر"),
            ("volume_unit", "گالن"),
        ],
        UnitType.AREA: [
            ("area_unit", "متر مربع"),
            ("area_unit", "سانتی‌متر مربع"),
        ],
        UnitType.COUNT: [
            ("count_unit", "عدد"),
        ],
    }

    options = unit_options.get(unit_type, [])
    for relationship_name, label in options:
        record = getattr(product, relationship_name, None)
        if record is not None:
            return label

    return "واحد"


# =========================================================
# استایل‌های سراسری کامپوننت
# =========================================================

PAGE_STYLESHEET = """
QWidget {
    font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif;
    color: #1E293B;
}

/* کارت‌ها/پنل‌ها */
QFrame.cardPanel {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}

/* گروه باکس */
QGroupBox {
    font-weight: 700;
    font-size: 13px;
    color: #334155;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    margin-top: 10px;
    padding-top: 14px;
    background-color: #FFFFFF;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 0 8px;
    right: 14px;
    background-color: #FFFFFF;
}

/* ورودی‌ها */
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
QComboBox::drop-down { border: none; padding-left: 8px; }

/* جدول مطابق الگوی مرجع */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    gridline-color: #F1F5F9;
    selection-background-color: #E8F5E9;
    selection-color: #1E293B;
}
QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #F1F5F9;
}
QTableWidget::item:selected {
    background: #E8F5E9;
    color: #0F172A;
}

/* هدر با نمای مرتب‌سازی */
QHeaderView::section {
    background-color: #F8FAFC;
    color: #475569;
    font-weight: 700;
    font-size: 13px;
    border: none;
    border-bottom: 2px solid #E2E8F0;
    padding: 10px 8px;
}
QHeaderView::section:horizontal {
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

/* ردیف Hover مشابه نمونه */
QTableView::item:hover {
    background: #F8FAFC;
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
QPushButton:hover { background-color: #F1F5F9; }
QPushButton:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
    border-color: #E2E8F0;
}
QPushButton.primaryBtn { background-color: #28745A; color: #FFFFFF; border: none; }
QPushButton.primaryBtn:hover { background-color: #1F5E48; }
QPushButton.primaryBtn:disabled { background-color: #A3C7BC; color: #FFFFFF; }
QPushButton.infoBtn { background-color: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; }
QPushButton.infoBtn:hover { background-color: #BAE6FD; }
QPushButton.dangerBtn { background-color: #FEE2E2; color: #DC2626; border: 1px solid #FCA5A5; }
QPushButton.dangerBtn:hover { background-color: #FCA5A5; color: #991B1B; }

/* چیپ/Badge */
.QChip {
    background-color: #F1F5F9;
    color: #334155;
    border: 1px solid #E2E8F0;
    border-radius: 999px;
    padding: 2px 10px;
    font-weight: 700;
    font-size: 11px;
}
.QChip.success {
    background-color: #DCFCE7;
    color: #166534;
    border-color: #BBF7D0;
}
.QChip.warn {
    background-color: #FEF3C7;
    color: #D97706;
    border-color: #FDE68A;
}
"""

# =========================================================
# کارت آماری هدر (StatCard)
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
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600; border: none; background: transparent;")

        self.val_label = QLabel(initial_value)
        self.val_label.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {accent_color}; border: none; background: transparent;")

        layout.addWidget(title_label)
        layout.addWidget(self.val_label)

    def set_value(self, val: str):
        self.val_label.setText(to_persian_digits(str(val)))


# =========================================================
# بج وضعیت دستور تهیه (RecipeBadge)
# =========================================================

class RecipeBadge(QFrame):
    def __init__(self, count: int, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel()
        label.setStyleSheet("font-size: 11px; font-weight: 700; background: transparent; border: none;")

        chip = QFrame()
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(8, 2, 8, 2)
        chip_layout.setSpacing(4)
        chip_layout.addWidget(label)
        chip.setObjectName("chip")

        if count > 0:
            label.setText(f"{to_persian_digits(str(count))} ماده اولیه")
            chip.setProperty("class", "QChip success")
        else:
            label.setText("بدون مواد اولیه")
            chip.setProperty("class", "QChip warn")

        layout.addWidget(chip)


# =========================================================
# فرم ایجاد و ویرایش دسته‌بندی
# =========================================================

class MenuCategoryDialog(QDialog):
    def __init__(self, parent=None, category=None):
        super().__init__(parent)
        self.category = category
        self.setWindowTitle("ویرایش دسته‌بندی" if category else "ایجاد دسته‌بندی جدید")
        self.setMinimumWidth(380)
        self.setStyleSheet(PAGE_STYLESHEET)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("نام دسته‌بندی:")
        lbl.setStyleSheet("font-weight: 600; color: #475569;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثلاً: نوشیدنی‌های گرم، ماکتل، کیک و دسر")
        self.name_input.setMinimumHeight(38)

        if category:
            self.name_input.setText(category.name)

        layout.addWidget(lbl)
        layout.addWidget(self.name_input)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        save_button = QPushButton("ذخیره دسته‌بندی")
        save_button.setProperty("class", "primaryBtn")
        save_button.setMinimumHeight(38)

        cancel_button = QPushButton("انصراف")
        cancel_button.setMinimumHeight(38)

        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)
        layout.addLayout(buttons)

    def get_data(self):
        return {"name": self.name_input.text().strip()}

    def accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "اطلاعات ناقص", "لطفاً نام دسته‌بندی را وارد کنید.")
            self.name_input.setFocus()
            return
        super().accept()


# =========================================================
# فرم ایجاد و ویرایش آیتم منو (شامل فیلد نحوه سرو)
# =========================================================

class MenuItemDialog(QDialog):
    def __init__(self, parent=None, item=None, categories=None, db=None):
        super().__init__(parent)
        self.item = item
        self.categories = list(categories or [])
        self.db = db

        self.setWindowTitle("ویرایش آیتم منو" if item else "افزودن آیتم جدید به منو")
        self.setMinimumWidth(480)
        self.setStyleSheet(PAGE_STYLESHEET)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # نام آیتم
        lbl_name = QLabel("نام آیتم منو:")
        lbl_name.setStyleSheet("font-weight: 600; color: #475569;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثلاً: لاته فندقی، کارامل ماکیاتو، چیزکیک")
        self.name_input.setMinimumHeight(38)
        layout.addWidget(lbl_name)
        layout.addWidget(self.name_input)

        # قیمت فروش
        lbl_price = QLabel("قیمت فروش (تومان):")
        lbl_price.setStyleSheet("font-weight: 600; color: #475569;")
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 1_000_000_000)
        self.price_input.setDecimals(0)
        self.price_input.setSingleStep(5000)
        self.price_input.setSuffix(" تومان")
        self.price_input.setMinimumHeight(38)
        layout.addWidget(lbl_price)
        layout.addWidget(self.price_input)

        # دسته‌بندی
        lbl_cat = QLabel("دسته‌بندی:")
        lbl_cat.setStyleSheet("font-weight: 600; color: #475569;")
        layout.addWidget(lbl_cat)

        cat_layout = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.setMinimumHeight(38)
        self.category_combo.addItem("بدون دسته‌بندی", None)
        for cat in self.categories:
            self.category_combo.addItem(cat.name, cat.id)

        self.add_category_button = QPushButton("+ دسته‌بندی جدید")
        self.add_category_button.setMinimumHeight(38)
        self.add_category_button.clicked.connect(self.create_category)

        cat_layout.addWidget(self.category_combo, 1)
        cat_layout.addWidget(self.add_category_button)
        layout.addLayout(cat_layout)

        # توضیحات نحوه سرو کردن
        lbl_desc = QLabel("توضیحات و نحوه سرو (اختیاری):")
        lbl_desc.setStyleSheet("font-weight: 600; color: #475569;")
        layout.addWidget(lbl_desc)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("مثلاً: همراه با یک برش لیمو و یخ سرو شود؛ سس شکلات در ظرف جداگانه ارائه گردد...")
        self.description_input.setMinimumHeight(75)
        self.description_input.setMaximumHeight(110)
        self.description_input.setAcceptRichText(False)
        self.description_input.setTabChangesFocus(True)
        layout.addWidget(self.description_input)

        hint = QLabel("💡 مواد اولیه و دستور پخت را می‌توانید بعد از ثبت از بخش «دستور تهیه» تکمیل کنید.")
        hint.setStyleSheet("color: #64748B; font-size: 11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # دکمه‌ها
        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        save_button = QPushButton("ذخیره آیتم")
        save_button.setProperty("class", "primaryBtn")
        save_button.setMinimumHeight(38)

        cancel_button = QPushButton("انصراف")
        cancel_button.setMinimumHeight(38)

        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)
        layout.addLayout(buttons)

        # در صورت ویرایش، مقادیر قبلی پر می‌شوند
        if item:
            self.name_input.setText(item.name or "")
            self.price_input.setValue(float(item.sale_price or 0))
            self.description_input.setPlainText(item.description or "")
            idx = self.category_combo.findData(item.category_id)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)

    def create_category(self):
        if self.db is None:
            QMessageBox.critical(self, "خطا", "اتصال به پایگاه داده برقرار نیست.")
            return

        dialog = MenuCategoryDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        name = dialog.get_data()["name"].strip()
        if not name:
            return

        try:
            existing = self.db.query(MenuCategory).filter(MenuCategory.name == name).first()
            if existing:
                idx = self.category_combo.findData(existing.id)
                if idx >= 0:
                    self.category_combo.setCurrentIndex(idx)
                QMessageBox.information(self, "اطلاع", "این دسته‌بندی از قبل موجود بود و انتخاب گردید.")
                return

            category = MenuCategory(name=name)
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

            self.categories.append(category)
            self.category_combo.addItem(category.name, category.id)
            self.category_combo.setCurrentIndex(self.category_combo.count() - 1)
        except SQLAlchemyError as error:
            self.db.rollback()
            QMessageBox.critical(self, "خطا در ایجاد دسته‌بندی", str(error))

    def get_data(self):
        desc = self.description_input.toPlainText().strip()
        return {
            "name": self.name_input.text().strip(),
            "sale_price": self.price_input.value(),
            "category_id": self.category_combo.currentData(),
            "description": desc if desc else None,
        }

    def accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "اطلاعات ناقص", "لطفاً نام آیتم منو را وارد کنید.")
            self.name_input.setFocus()
            return

        if self.price_input.value() <= 0:
            QMessageBox.warning(self, "قیمت نامعتبر", "قیمت فروش باید بزرگ‌تر از صفر باشد.")
            self.price_input.setFocus()
            return

        desc = self.description_input.toPlainText().strip()
        if len(desc) > 500:
            QMessageBox.warning(self, "توضیحات طولانی", "توضیحات نحوه سرو نمی‌تواند بیش از ۵۰۰ کاراکتر باشد.")
            self.description_input.setFocus()
            return

        super().accept()


# =========================================================
# دیالوگ نمایش جزئیات آیتم (Read-Only)
# =========================================================

class MenuItemDetailsDialog(QDialog):
    def __init__(self, parent=None, item: MenuItem = None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle(f"جزئیات آیتم: {item.name if item else ''}")
        self.setMinimumWidth(520)
        self.setStyleSheet(PAGE_STYLESHEET)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # نام
        lbl_name = QLabel("نام آیتم منو:")
        lbl_name.setStyleSheet("font-weight: 600; color: #475569;")
        name_val = QLineEdit(item.name if item else "")
        name_val.setReadOnly(True)
        name_val.setMinimumHeight(38)
        layout.addWidget(lbl_name)
        layout.addWidget(name_val)

        # قیمت
        lbl_price = QLabel("قیمت فروش (تومان):")
        lbl_price.setStyleSheet("font-weight: 600; color: #475569;")
        price_val = QLineEdit(format_price(item.sale_price if item else 0))
        price_val.setReadOnly(True)
        price_val.setMinimumHeight(38)
        layout.addWidget(lbl_price)
        layout.addWidget(price_val)

        # دسته‌بندی
        lbl_cat = QLabel("دسته‌بندی:")
        lbl_cat.setStyleSheet("font-weight: 600; color: #475569;")
        cat_name = item.category.name if (item and item.category) else "بدون دسته‌بندی"
        cat_val = QLineEdit(cat_name)
        cat_val.setReadOnly(True)
        cat_val.setMinimumHeight(38)
        layout.addWidget(lbl_cat)
        layout.addWidget(cat_val)

        # توضیحات و نحوه سرو
        lbl_desc = QLabel("توضیحات و نحوه سرو:")
        lbl_desc.setStyleSheet("font-weight: 600; color: #475569;")
        layout.addWidget(lbl_desc)

        desc_val = QTextEdit()
        desc_val.setReadOnly(True)
        desc_val.setAcceptRichText(False)
        desc_val.setMinimumHeight(110)
        desc_val.setPlainText(item.description or "—")
        layout.addWidget(desc_val)

        # دکمه‌ها
        buttons = QHBoxLayout()
        buttons.addStretch()
        close_btn = QPushButton("بستن")
        close_btn.setMinimumHeight(36)
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)


# =========================================================
# دیالوگ مدیریت مواد اولیه و فرمول ساخت (RecipeDialog)
# =========================================================

class RecipeDialog(QDialog):
    def __init__(self, parent, db, menu_item):
        super().__init__(parent)
        self.db = db
        self.menu_item = menu_item
        self.selected_recipe_id = None

        self.setWindowTitle(f"دستور تهیه و مواد اولیه: {menu_item.name}")
        self.resize(780, 520)
        self.setStyleSheet(PAGE_STYLESHEET)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        title = QLabel(f"مواد اولیه موردنیاز برای یک واحد «{menu_item.name}»")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")
        desc = QLabel("برای هر ماده، میزان مصرف از انبار را مشخص کنید تا در هنگام ثبت فاکتور از موجودی کسر گردد.")
        desc.setStyleSheet("font-size: 12px; color: #64748B;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        input_panel = QFrame()
        input_panel.setProperty("class", "cardPanel")
        form_box = QVBoxLayout(input_panel)
        form_box.setContentsMargins(14, 12, 14, 12)
        form_box.setSpacing(10)

        inputs_row = QHBoxLayout()
        inputs_row.setSpacing(12)

        prod_box = QVBoxLayout()
        lbl_p = QLabel("انتخاب ماده اولیه از انبار:")
        lbl_p.setStyleSheet("font-weight: 600; color: #475569;")
        self.product_combo = QComboBox()
        self.product_combo.setMinimumHeight(36)
        prod_box.addWidget(lbl_p)
        prod_box.addWidget(self.product_combo)
        inputs_row.addLayout(prod_box, 3)

        amt_box = QVBoxLayout()
        lbl_a = QLabel("مقدار مصرف:")
        lbl_a.setStyleSheet("font-weight: 600; color: #475569;")
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.001, 1_000_000_000)
        self.amount_input.setDecimals(3)
        self.amount_input.setSingleStep(0.5)
        self.amount_input.setValue(1.0)
        self.amount_input.setMinimumHeight(36)
        amt_box.addWidget(lbl_a)
        amt_box.addWidget(self.amount_input)
        inputs_row.addLayout(amt_box, 1)

        form_box.addLayout(inputs_row)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)

        self.add_button = QPushButton("+ افزودن به دستور تهیه")
        self.add_button.setProperty("class", "primaryBtn")
        self.add_button.setMinimumHeight(34)
        self.add_button.clicked.connect(self.add_recipe_item)

        self.update_button = QPushButton("ویرایش مقدار")
        self.update_button.setMinimumHeight(34)
        self.update_button.setEnabled(False)
        self.update_button.clicked.connect(self.update_recipe_item)

        self.delete_button = QPushButton("حذف ماده")
        self.delete_button.setProperty("class", "dangerBtn")
        self.delete_button.setMinimumHeight(34)
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.delete_recipe_item)

        actions_row.addWidget(self.add_button)
        actions_row.addWidget(self.update_button)
        actions_row.addWidget(self.delete_button)
        actions_row.addStretch()

        form_box.addLayout(actions_row)
        layout.addWidget(input_panel)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "شناسه",
            "نام ماده اولیه",
            "مقدار مصرف",
            "واحد اندازه‌گیری",
        ])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table, 1)

        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        close_button = QPushButton("بستن پنجره")
        close_button.setMinimumHeight(36)
        close_button.clicked.connect(self.accept)
        footer_layout.addWidget(close_button)
        layout.addLayout(footer_layout)

        self.load_products()
        self.refresh_table()

    def load_products(self):
        self.product_combo.clear()
        products = self.db.query(Product).order_by(Product.name).all()

        for product in products:
            label = f"{product.name} ({unit_label(product)})"
            self.product_combo.addItem(label, product.id)

        if not products:
            self.product_combo.addItem("هیچ ماده اولیه‌ای در انبار ثبت نشده است", None)
            self.add_button.setEnabled(False)

    def refresh_table(self):
        self.table.setRowCount(0)
        recipe_items = (
            self.db.query(RecipeItem)
            .filter(RecipeItem.menu_item_id == self.menu_item.id)
            .all()
        )

        for recipe in recipe_items:
            product = recipe.warehouse_product
            product_name = product.name if product else "محصول حذف‌شده"
            unit = unit_label(product) if product else "—"

            row = self.table.rowCount()
            self.table.insertRow(row)

            id_item = QTableWidgetItem(str(recipe.id))
            id_item.setData(Qt.ItemDataRole.UserRole, recipe.id)
            self.table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem(product_name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, name_item)

            amt_item = QTableWidgetItem(format_amount(recipe.required_amount))
            amt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, amt_item)

            unit_item = QTableWidgetItem(unit)
            unit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, unit_item)

        self.selected_recipe_id = None
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    def on_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.selected_recipe_id = None
            self.update_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            return

        row = selected_rows[0].row()
        id_item = self.table.item(row, 0)
        recipe_id = id_item.data(Qt.ItemDataRole.UserRole)
        if recipe_id is None:
            try:
                recipe_id = int(id_item.text())
            except ValueError:
                return

        recipe = self.db.query(RecipeItem).filter(RecipeItem.id == recipe_id).first()
        if not recipe:
            return

        self.selected_recipe_id = recipe.id
        idx = self.product_combo.findData(recipe.warehouse_product_id)
        if idx >= 0:
            self.product_combo.setCurrentIndex(idx)

        self.amount_input.setValue(float(recipe.required_amount))
        self.update_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def add_recipe_item(self):
        product_id = self.product_combo.currentData()
        if product_id is None:
            QMessageBox.warning(self, "خطا", "ابتدا یک محصول را در بخش انبار تعریف کنید.")
            return

        existing = (
            self.db.query(RecipeItem)
            .filter(
                RecipeItem.menu_item_id == self.menu_item.id,
                RecipeItem.warehouse_product_id == product_id,
            )
            .first()
        )
        if existing:
            QMessageBox.warning(
                self,
                "ماده تکراری",
                "این ماده اولیه قبلاً به دستور تهیه اضافه شده است. برای تغییر، آن را انتخاب و «ویرایش مقدار» را بزنید.",
            )
            return

        try:
            recipe = RecipeItem(
                menu_item_id=self.menu_item.id,
                warehouse_product_id=product_id,
                required_amount=self.amount_input.value(),
            )
            self.db.add(recipe)
            self.db.commit()
            self.refresh_table()
        except SQLAlchemyError as error:
            self.db.rollback()
            QMessageBox.critical(self, "خطا در ثبت ماده اولیه", str(error))

    def update_recipe_item(self):
        if self.selected_recipe_id is None:
            return

        product_id = self.product_combo.currentData()
        if product_id is None:
            return

        try:
            recipe = self.db.query(RecipeItem).filter(RecipeItem.id == self.selected_recipe_id).first()
            if not recipe:
                self.refresh_table()
                return

            duplicate = (
                self.db.query(RecipeItem)
                .filter(
                    RecipeItem.menu_item_id == self.menu_item.id,
                    RecipeItem.warehouse_product_id == product_id,
                    RecipeItem.id != recipe.id,
                )
                .first()
            )
            if duplicate:
                QMessageBox.warning(self, "ماده تکراری", "این ماده اولیه در فهرست دستور تهیه وجود دارد.")
                return

            recipe.warehouse_product_id = product_id
            recipe.required_amount = self.amount_input.value()
            self.db.commit()
            self.refresh_table()
        except SQLAlchemyError as error:
            self.db.rollback()
            QMessageBox.critical(self, "خطا در ویرایش", str(error))

    def delete_recipe_item(self):
        if self.selected_recipe_id is None:
            return

        reply = QMessageBox.question(
            self,
            "تأیید حذف",
            "آیا از حذف این ماده اولیه از دستور تهیه اطمینان دارید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            recipe = self.db.query(RecipeItem).filter(RecipeItem.id == self.selected_recipe_id).first()
            if recipe:
                self.db.delete(recipe)
                self.db.commit()
            self.refresh_table()
        except SQLAlchemyError as error:
            self.db.rollback()
            QMessageBox.critical(self, "خطا در حذف", str(error))


# =========================================================
# صفحه اصلی مدیریت منو (MenuPage)
# =========================================================

class MenuPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = init_db()
        self._closing = False

        self.setStyleSheet(PAGE_STYLESHEET)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.setup_ui()
        self.load_categories()
        self.refresh_table()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        # -------------------------------------------------
        # ۱. هدر و کارت‌های آماری
        # -------------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("مدیریت منو و رسپی")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A;")
        subtitle = QLabel("تعریف آیتم‌ها، قیمت‌گذاری، دسته‌بندی و فرمول ساخت از انبار")
        subtitle.setStyleSheet("font-size: 12px; color: #64748B;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box, 2)

        self.card_total_items = StatCard("کل آیتم‌های منو", "۰", "#28745A")
        self.card_total_cats = StatCard("تعداد دسته‌بندی‌ها", "۰", "#0284C7")
        self.card_avg_price = StatCard("میانگین قیمت (تومان)", "۰", "#8B5CF6")
        self.card_no_recipe = StatCard("بدون دستور تهیه", "۰", "#D97706")

        header_layout.addWidget(self.card_total_items, 1)
        header_layout.addWidget(self.card_total_cats, 1)
        header_layout.addWidget(self.card_avg_price, 1)
        header_layout.addWidget(self.card_no_recipe, 1)

        root.addLayout(header_layout)

        # -------------------------------------------------
        # ۲. پنل نوار ابزار و مدیریت دسته‌بندی‌ها
        # -------------------------------------------------
        toolbar_panel = QFrame()
        toolbar_panel.setProperty("class", "cardPanel")
        toolbar_layout = QVBoxLayout(toolbar_panel)
        toolbar_layout.setContentsMargins(14, 12, 14, 12)
        toolbar_layout.setSpacing(10)

        row1 = QHBoxLayout()
        row1.setSpacing(10)

        lbl_s = QLabel("جست‌وجو:")
        lbl_s.setStyleSheet("font-weight: 600; color: #475569;")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("نام یا توضیحات آیتم منو را جست‌وجو کنید...")
        self.search_input.setMinimumHeight(36)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.refresh_table)

        lbl_c = QLabel("دسته‌بندی:")
        lbl_c.setStyleSheet("font-weight: 600; color: #475569;")
        self.category_filter = QComboBox()
        self.category_filter.setMinimumWidth(180)
        self.category_filter.setMinimumHeight(36)
        self.category_filter.currentIndexChanged.connect(self.refresh_table)

        self.add_item_button = QPushButton("+ آیتم جدید منو")
        self.add_item_button.setProperty("class", "primaryBtn")
        self.add_item_button.setMinimumHeight(36)
        self.add_item_button.clicked.connect(self.create_menu_item)

        self.refresh_button = QPushButton("🔄 به‌روزرسانی")
        self.refresh_button.setToolTip("بازخوانی کامل آیتم‌ها و دسته‌بندی‌ها از دیتابیس")
        self.refresh_button.setMinimumHeight(36)
        self.refresh_button.clicked.connect(self.refresh_all)

        row1.addWidget(lbl_s)
        row1.addWidget(self.search_input, 2)
        row1.addWidget(lbl_c)
        row1.addWidget(self.category_filter, 1)
        row1.addWidget(self.add_item_button)
        row1.addWidget(self.refresh_button)
        toolbar_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)

        cat_ops_label = QLabel("عملیات دسته:")
        cat_ops_label.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        row2.addWidget(cat_ops_label)

        self.add_category_button = QPushButton("+ دسته جدید")
        self.add_category_button.setMinimumHeight(32)
        self.add_category_button.clicked.connect(self.create_category)
        row2.addWidget(self.add_category_button)

        self.edit_category_button = QPushButton("ویرایش دسته جاری")
        self.edit_category_button.setMinimumHeight(32)
        self.edit_category_button.clicked.connect(self.edit_category)
        row2.addWidget(self.edit_category_button)

        self.delete_category_button = QPushButton("حذف دسته جاری")
        self.delete_category_button.setProperty("class", "dangerBtn")
        self.delete_category_button.setMinimumHeight(32)
        self.delete_category_button.clicked.connect(self.delete_category)
        row2.addWidget(self.delete_category_button)

        row2.addStretch()

        # دکمه‌های عملیاتی آیتم
        self.recipe_button = QPushButton("📋 دستور تهیه و مواد اولیه")
        self.recipe_button.setProperty("class", "infoBtn")
        self.recipe_button.setMinimumHeight(32)
        self.recipe_button.setEnabled(False)
        self.recipe_button.clicked.connect(self.open_recipe)
        row2.addWidget(self.recipe_button)

        self.detail_item_button = QPushButton("جزئیات آیتم")
        self.detail_item_button.setMinimumHeight(32)
        self.detail_item_button.setEnabled(False)
        self.detail_item_button.clicked.connect(self.show_item_details)
        row2.addWidget(self.detail_item_button)

        self.edit_item_button = QPushButton("ویرایش آیتم")
        self.edit_item_button.setMinimumHeight(32)
        self.edit_item_button.setEnabled(False)
        self.edit_item_button.clicked.connect(self.edit_menu_item)
        row2.addWidget(self.edit_item_button)

        self.delete_item_button = QPushButton("حذف آیتم")
        self.delete_item_button.setProperty("class", "dangerBtn")
        self.delete_item_button.setMinimumHeight(32)
        self.delete_item_button.setEnabled(False)
        self.delete_item_button.clicked.connect(self.delete_menu_item)
        row2.addWidget(self.delete_item_button)

        toolbar_layout.addLayout(row2)
        root.addWidget(toolbar_panel)

        # -------------------------------------------------
        # ۳. پنل جدول آیتم‌ها (ستون نحوه سرو اضافه شد)
        # -------------------------------------------------
        table_panel = QFrame()
        table_panel.setProperty("class", "cardPanel")
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(0, 0, 12, 12)
        table_layout.setSpacing(0)

        inner = QVBoxLayout()
        inner.setContentsMargins(14, 14, 14, 0)
        inner.setSpacing(10)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "شناسه",
            "نام آیتم منو",
            "دسته‌بندی",
            "قیمت فروش (تومان)",
            "نحوه سرو",
            "دستور تهیه (رسپی)",
        ])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)

        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        self.table.itemDoubleClicked.connect(lambda _: self.edit_menu_item())

        inner.addWidget(self.table, 1)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(14, 8, 14, 14)
        self.status_label = QLabel("تعداد آیتم‌ها: ۰")
        self.status_label.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        status_row.addWidget(self.status_label)
        status_row.addStretch()

        hint_lbl = QLabel("💡 با دوبار کلیک روی هر سطر، می‌توانید آیتم را ویرایش کنید.")
        hint_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
        status_row.addWidget(hint_lbl)

        inner.addLayout(status_row)
        table_layout.addLayout(inner)
        root.addWidget(table_panel, 1)

    def on_table_selection_changed(self):
        has_sel = bool(self.table.selectionModel().selectedRows())
        self.edit_item_button.setEnabled(has_sel)
        self.delete_item_button.setEnabled(has_sel)
        self.recipe_button.setEnabled(has_sel)
        self.detail_item_button.setEnabled(has_sel)

    def load_categories(self):
        current_cat_id = self.category_filter.currentData()
        categories = self.db.query(MenuCategory).order_by(MenuCategory.name).all()

        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("همه دسته‌بندی‌ها", None)

        for cat in categories:
            self.category_filter.addItem(cat.name, cat.id)

        idx = self.category_filter.findData(current_cat_id)
        if idx >= 0:
            self.category_filter.setCurrentIndex(idx)

        self.category_filter.blockSignals(False)

    def create_category(self):
        dialog = MenuCategoryDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        name = dialog.get_data()["name"]
        try:
            existing = self.db.query(MenuCategory).filter(MenuCategory.name == name).first()
            if existing:
                QMessageBox.warning(self, "دسته‌بندی تکراری", "این نام دسته‌بندی قبلاً ثبت شده است.")
                return

            category = MenuCategory(name=name)
            self.db.add(category)
            self.db.commit()

            self.load_categories()
            self.refresh_table()
        except SQLAlchemyError as error:
            self.db.rollback()
            QMessageBox.critical(self, "خطا در ایجاد دسته‌بندی", str(error))

    def get_selected_category(self):
        category_id = self.category_filter.currentData()
        if category_id is None:
            return None
        return self.db.query(MenuCategory).filter(MenuCategory.id == category_id).first()

    def edit_category(self):
        category = self.get_selected_category()
        if category is None:
            QMessageBox.information(self, "انتخاب دسته‌بندی", "لطفاً ابتدا یک دسته‌بندی مشخص را از منوی کشویی انتخاب کنید.")
            return

        dialog = MenuCategoryDialog(self, category=category)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        name = dialog.get_data()["name"]
        try:
            duplicate = (
                self.db.query(MenuCategory)
                .filter(MenuCategory.name == name, MenuCategory.id != category.id)
                .first()
            )
            if duplicate:
                QMessageBox.warning(self, "نام تکراری", "দسته‌بندی دیگری با این نام وجود دارد.")
                return

            category.name = name
            self.db.commit()

            self.load_categories()
            self.refresh_table()
        except SQLAlchemyError as error:
            self.db.rollback()
            QMessageBox.critical(self, "خطا در ویرایش دسته‌بندی", str(error))

    def delete_category(self):
        category = self.get_selected_category()
        if category is None:
            QMessageBox.information(self, "انتخاب دسته‌بندی", "لطفاً ابتدا یک دسته‌بندی مشخص را از منوی کشویی انتخاب کنید.")
            return

        reply = QMessageBox.question(
            self,
            "حذف دسته‌بندی",
            f"آیا از حذف دسته‌بندی «{category.name}» اطمینان دارید؟\n(آیتم‌های این گروه حذف نمی‌شوند و بدون دسته‌بندی خواهند شد)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db.query(MenuItem).filter(MenuItem.category_id == category.id).update(
                {MenuItem.category_id: None},
                synchronize_session=False,
            )
            self.db.delete(category)
            self.db.commit()

            self.load_categories()
            self.refresh_table()
        except SQLAlchemyError as error:
            self.db.rollback()
            QMessageBox.critical(self, "خطا در حذف دسته‌بندی", str(error))

    def create_menu_item(self):
        categories = self.db.query(MenuCategory).order_by(MenuCategory.name).all()
        dialog = MenuItemDialog(self, categories=categories, db=self.db)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()
        try:
            item = MenuItem(
                name=data["name"],
                sale_price=data["sale_price"],
                category_id=data["category_id"],
                description=data["description"],
            )
            self.db.add(item)
            self.db.commit()

            self.refresh_table()
            QMessageBox.information(self, "موفق", f"آیتم «{item.name}» با موفقیت افزوده شد.")
        except SQLAlchemyError as error:
            self.db.rollback()
            QMessageBox.critical(self, "خطا در ایجاد آیتم", str(error))

    def get_selected_menu_item(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        id_item = self.table.item(row, 0)
        item_id = id_item.data(Qt.ItemDataRole.UserRole)
        if item_id is None:
            try:
                item_id = int(id_item.text())
            except ValueError:
                return None

        return self.db.query(MenuItem).filter(MenuItem.id == item_id).first()

    def show_item_details(self):
        item = self.get_selected_menu_item()
        if item is None:
            QMessageBox.information(self, "انتخاب آیتم", "لطفاً یک آیتم را از جدول انتخاب کنید.")
            return

        dlg = MenuItemDetailsDialog(self, item=item)
        dlg.exec()

    def edit_menu_item(self):
        item = self.get_selected_menu_item()
        if item is None:
            QMessageBox.information(self, "انتخاب آیتم", "لطفاً ابتدا یک آیتم را از جدول انتخاب کنید.")
            return

        categories = self.db.query(MenuCategory).order_by(MenuCategory.name).all()
        dialog = MenuItemDialog(self, item=item, categories=categories, db=self.db)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()
        try:
            item.name = data["name"]
            item.sale_price = data["sale_price"]
            item.category_id = data["category_id"]
            item.description = data["description"]
            self.db.commit()

            self.refresh_table()
            QMessageBox.information(self, "موفق", "اطلاعات آیتم منو به‌روزرسانی شد.")
        except SQLAlchemyError as error:
            self.db.rollback()
            QMessageBox.critical(self, "خطا در ویرایش آیتم", str(error))

    def delete_menu_item(self):
        item = self.get_selected_menu_item()
        if item is None:
            QMessageBox.information(self, "انتخاب آیتم", "لطفاً ابتدا یک آیتم را از جدول انتخاب کنید.")
            return

        reply = QMessageBox.question(
            self,
            "حذف آیتم منو",
            f"آیا از حذف «{item.name}» مطمئن هستید؟\nکلیه دستور تهیه‌ها و پیوندهای مربوط به آن نیز حذف خواهند شد.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db.delete(item)
            self.db.commit()
            self.refresh_table()
            QMessageBox.information(self, "موفق", "آیتم منو با موفقیت حذف شد.")
        except SQLAlchemyError as error:
            self.db.rollback()
            QMessageBox.critical(
                self,
                "خطا در حذف آیتم",
                f"حذف آیتم به دلیل وابستگی در سایر بخش‌ها (مانند فاکتورها) امکان‌پذیر نیست.\n\nجزئیات: {error}",
            )

    def open_recipe(self):
        item = self.get_selected_menu_item()
        if item is None:
            QMessageBox.information(self, "انتخاب آیتم", "برای تنظیم دستور تهیه، ابتدا آیتم مورد نظر را از جدول انتخاب کنید.")
            return

        dialog = RecipeDialog(self, self.db, item)
        dialog.exec()
        self.refresh_table()

    def refresh_table(self, *_):
        try:
            query = self.db.query(MenuItem)

            search_text = self.search_input.text().strip()
            if search_text:
                query = query.filter(
                    (MenuItem.name.ilike(f"%{search_text}%")) |
                    (MenuItem.description.ilike(f"%{search_text}%"))
                )

            cat_id = self.category_filter.currentData()
            if cat_id is not None:
                query = query.filter(MenuItem.category_id == cat_id)

            items = query.order_by(MenuItem.name).all()

            all_items = self.db.query(MenuItem).all()
            total_items = len(all_items)
            total_cats = self.db.query(MenuCategory).count()
            avg_price = (sum(i.sale_price for i in all_items) / total_items) if total_items > 0 else 0

            no_recipe_count = 0
            for itm in all_items:
                if self.db.query(RecipeItem).filter(RecipeItem.menu_item_id == itm.id).count() == 0:
                    no_recipe_count += 1

            self.card_total_items.set_value(str(total_items))
            self.card_total_cats.set_value(str(total_cats))
            self.card_avg_price.set_value(format_price(avg_price))
            self.card_no_recipe.set_value(str(no_recipe_count))

            self.table.blockSignals(True)
            self.table.setRowCount(0)

            for item in items:
                row = self.table.rowCount()
                self.table.insertRow(row)

                # ۰. شناسه (مخفی)
                id_item = QTableWidgetItem(str(item.id))
                id_item.setData(Qt.ItemDataRole.UserRole, item.id)
                self.table.setItem(row, 0, id_item)

                # ۱. نام آیتم منو
                name_item = QTableWidgetItem(item.name)
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 1, name_item)

                # ۲. دسته‌بندی
                cat_name = item.category.name if item.category else "بدون دسته‌بندی"
                cat_item = QTableWidgetItem(cat_name)
                cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if not item.category:
                    cat_item.setForeground(Qt.GlobalColor.darkGray)
                self.table.setItem(row, 2, cat_item)

                # ۳. قیمت فروش
                price_item = QTableWidgetItem(format_price(item.sale_price))
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 3, price_item)

                # ۴. توضیحات و نحوه سرو
                desc_text = item.description.strip() if item.description else "—"
                desc_item = QTableWidgetItem(desc_text)
                desc_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if item.description:
                    desc_item.setToolTip(item.description)
                else:
                    desc_item.setForeground(Qt.GlobalColor.darkGray)
                self.table.setItem(row, 4, desc_item)

                # ۵. وضعیت دستور تهیه
                recipe_count = (
                    self.db.query(RecipeItem)
                    .filter(RecipeItem.menu_item_id == item.id)
                    .count()
                )
                badge_widget = QWidget()
                b_layout = QHBoxLayout(badge_widget)
                b_layout.setContentsMargins(0, 0, 0, 0)
                b_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                b_layout.addWidget(RecipeBadge(recipe_count))
                self.table.setCellWidget(row, 5, badge_widget)

            self.table.blockSignals(False)
            self.status_label.setText(f"تعداد آیتم‌های نمایش‌داده‌شده: {to_persian_digits(str(len(items)))}")
            self.on_table_selection_changed()

        except Exception as exc:
            self.table.blockSignals(False)
            QMessageBox.critical(self, "خطای دیتابیس", f"بارگذاری اطلاعات با خطا مواجه شد:\n{exc}")

    def refresh_all(self):
        try:
            self.db.expire_all()
            self.load_categories()
            self.refresh_table()
        except Exception as exc:
            QMessageBox.critical(self, "خطا در به‌روزرسانی", str(exc))

    def closeEvent(self, event):
        if not self._closing:
            self._closing = True
            try:
                self.db.close()
            except Exception:
                pass
        super().closeEvent(event)
