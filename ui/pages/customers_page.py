# /home/amirali-arzande/cafe-pos-desktop/ui/pages/customers_page.py

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
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

from database.db import init_db
from database.models.cafe.customer import Customer

# =========================================================
# توابع کمکی تبدیل ارقام و فرمت‌ها
# =========================================================

def to_persian_digits(text: str) -> str:
    """تبدیل اعداد انگلیسی به فارسی برای سازگاری کامل با تم RTL"""
    if text is None:
        return ""
    trans = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(text).translate(trans)

def format_date(dt: datetime) -> str:
    """فرمت‌بندی تاریخ ثبت با ارقام فارسی"""
    if not dt:
        return "—"
    return to_persian_digits(dt.strftime("%Y/%m/%d %H:%M"))

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

/* ورودی‌ها */
QLineEdit {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
    color: #0F172A;
}
QLineEdit:focus {
    border: 1px solid #28745A;
    background-color: #FFFFFF;
}

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
QPushButton.dangerBtn { background-color: #FEE2E2; color: #DC2626; border: 1px solid #FCA5A5; }
QPushButton.dangerBtn:hover { background-color: #FCA5A5; color: #991B1B; }
QPushButton.dangerBtn:disabled { background-color: #F8FAFC; color: #CBD5E1; border-color: #E2E8F0; }

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

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600; border: none; background: transparent;")

        self.val_label = QLabel(initial_value)
        self.val_label.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {accent_color}; border: none; background: transparent;")

        layout.addWidget(title_label)
        layout.addWidget(self.val_label)

    def set_value(self, val: str):
        self.val_label.setText(to_persian_digits(str(val)))

# =========================================================
# بج وضعیت تلفن مشتری
# =========================================================

class PhoneBadge(QFrame):
    def __init__(self, has_phone: bool, parent=None):
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

        if has_phone:
            label.setText("دارای شماره")
            chip.setProperty("class", "QChip success")
        else:
            label.setText("بدون شماره")
            chip.setProperty("class", "QChip warn")

        layout.addWidget(chip)

# =========================================================
# صفحه اصلی مدیریت مشتریان (CustomersPage)
# =========================================================

class CustomersPage(QWidget):
    def __init__(self):
        super().__init__()

        self.db = init_db()
        self.selected_customer_id = None
        self._closing = False

        self.setStyleSheet(PAGE_STYLESHEET)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.setup_ui()
        self.load_customers()

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

        title = QLabel("مدیریت مشتریان")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A;")

        subtitle = QLabel("ثبت، مشاهده، ویرایش و مدیریت اطلاعات مشتریان کافه")
        subtitle.setStyleSheet("font-size: 12px; color: #64748B;")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box, 2)

        # کارت‌های آمار
        self.card_total = StatCard("کل مشتریان", "۰", "#28745A")
        self.card_with_phone = StatCard("دارای شماره تماس", "۰", "#0284C7")
        self.card_no_phone = StatCard("بدون شماره تماس", "۰", "#D97706")
        self.card_month = StatCard("ثبت‌شدهٔ این ماه", "۰", "#16A34A")

        header_layout.addWidget(self.card_total, 1)
        header_layout.addWidget(self.card_with_phone, 1)
        header_layout.addWidget(self.card_no_phone, 1)
        header_layout.addWidget(self.card_month, 1)

        root.addLayout(header_layout)

        # -------------------------------------------------
        # ۲. پنل ثبت و ویرایش مشتری
        # -------------------------------------------------
        form_panel = QFrame()
        form_panel.setProperty("class", "cardPanel")
        form_layout = QVBoxLayout(form_panel)
        form_layout.setContentsMargins(16, 14, 16, 14)
        form_layout.setSpacing(12)

        form_title = QLabel("اطلاعات مشتری")
        form_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1E293B;")
        form_layout.addWidget(form_title)

        fields_row = QHBoxLayout()
        fields_row.setSpacing(14)

        # فیلد نام
        name_box = QVBoxLayout()
        lbl_name = QLabel("نام مشتری:")
        lbl_name.setStyleSheet("font-weight: 600; color: #475569;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("نام و نام خانوادگی مشتری")
        self.name_input.setMinimumHeight(36)
        name_box.addWidget(lbl_name)
        name_box.addWidget(self.name_input)
        fields_row.addLayout(name_box, 2)

        # فیلد تلفن
        phone_box = QVBoxLayout()
        lbl_phone = QLabel("شماره تلفن:")
        lbl_phone.setStyleSheet("font-weight: 600; color: #475569;")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("مثال: 09123456789")
        self.phone_input.setMinimumHeight(36)
        self.phone_input.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.phone_input.setAlignment(Qt.AlignmentFlag.AlignLeft)
        phone_box.addWidget(lbl_phone)
        phone_box.addWidget(self.phone_input)
        fields_row.addLayout(phone_box, 1)

        form_layout.addLayout(fields_row)

        # دکمه‌های فرم
        form_actions = QHBoxLayout()
        form_actions.setContentsMargins(0, 4, 0, 0)

        hint = QLabel("💡 برای ویرایش، مشتری را از جدول انتخاب کنید.")
        hint.setStyleSheet("color: #64748B; font-size: 12px;")
        form_actions.addWidget(hint)
        form_actions.addStretch()

        self.save_button = QPushButton("ثبت مشتری")
        self.save_button.setProperty("class", "primaryBtn")
        self.save_button.setMinimumHeight(36)
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_button.clicked.connect(self.save_customer)

        self.clear_button = QPushButton("فرم جدید")
        self.clear_button.setMinimumHeight(36)
        self.clear_button.clicked.connect(self.clear_form)

        self.delete_button = QPushButton("حذف مشتری")
        self.delete_button.setProperty("class", "dangerBtn")
        self.delete_button.setMinimumHeight(36)
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.delete_customer)

        form_actions.addWidget(self.clear_button)
        form_actions.addWidget(self.delete_button)
        form_actions.addWidget(self.save_button)

        form_layout.addLayout(form_actions)
        root.addWidget(form_panel)

        # -------------------------------------------------
        # ۳. پنل جدول، جست‌وجو و دکمه رفرش
        # -------------------------------------------------
        table_panel = QFrame()
        table_panel.setProperty("class", "cardPanel")
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(14, 14, 14, 14)
        table_layout.setSpacing(10)

        table_header = QHBoxLayout()

        table_title = QLabel("فهرست مشتریان")
        table_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1E293B;")
        table_header.addWidget(table_title)
        table_header.addStretch()

        # دکمه رفرش
        self.refresh_button = QPushButton("🔄 به‌روزرسانی")
        self.refresh_button.setToolTip("بارگذاری مجدد اطلاعات از دیتابیس")
        self.refresh_button.setMinimumHeight(34)
        self.refresh_button.clicked.connect(self.refresh_data)
        table_header.addWidget(self.refresh_button)

        # جست‌وجو
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 جست‌وجو بر اساس نام یا شماره تلفن...")
        self.search_input.setMinimumHeight(34)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.load_customers)
        table_header.addWidget(self.search_input, 1)

        table_layout.addLayout(table_header)

        # جدول مشتریان
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "شناسه",
            "نام مشتری",
            "شماره تلفن",
            "تاریخ ثبت",
            "وضعیت تماس",
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
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in range(2, 5):
            header_view.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSortIndicatorShown(True)
        self.table.setSortingEnabled(True)

        self.table.itemSelectionChanged.connect(self.on_customer_selected)
        table_layout.addWidget(self.table, 1)

        root.addWidget(table_panel, 1)

    # -----------------------------------------------------
    # رفرش و ابزارهای کمکی
    # -----------------------------------------------------

    def refresh_data(self):
        """بازخوانی تازه تمام داده‌ها مستقیماً از دیتابیس"""
        try:
            self.db.expire_all()
            self.load_customers()
        except Exception as exc:
            QMessageBox.critical(self, "خطا", f"خطا در به‌روزرسانی اطلاعات:\n{exc}")

    def get_current_customer(self):
        if self.selected_customer_id is None:
            QMessageBox.warning(self, "انتخاب مشتری", "لطفاً ابتدا یک مشتری را از جدول انتخاب کنید.")
            return None
        return self.db.query(Customer).filter(Customer.id == self.selected_customer_id).first()

    # -----------------------------------------------------
    # بارگذاری مشتریان
    # -----------------------------------------------------

    def load_customers(self, *_):
        try:
            query = self.db.query(Customer)

            search_text = self.search_input.text().strip()
            if search_text:
                search_pattern = f"%{search_text}%"
                query = query.filter(
                    Customer.name.ilike(search_pattern)
                    | Customer.phone.ilike(search_pattern)
                )

            customers = query.order_by(Customer.id.desc()).all()

            # محاسبه آمارها
            # توجه: expire_all قبل از all_customers لازم نیست؛ از تعارض سیگنال‌ها جلوگیری می‌کنیم
            all_customers = self.db.query(Customer).all()
            total = len(all_customers)
            with_phone = sum(1 for c in all_customers if c.phone)
            now = datetime.utcnow()
            this_month = sum(
                1 for c in all_customers
                if c.created_at and c.created_at.year == now.year and c.created_at.month == now.month
            )

            self.card_total.set_value(str(total))
            self.card_with_phone.set_value(str(with_phone))
            self.card_no_phone.set_value(str(total - with_phone))
            self.card_month.set_value(str(this_month))

            # پر کردن جدول
            self.table.blockSignals(True)
            self.table.setRowCount(0)

            for customer in customers:
                row = self.table.rowCount()
                self.table.insertRow(row)

                # ستون ۰: شناسه یکتا در UserRole
                id_item = QTableWidgetItem(str(customer.id))
                id_item.setData(Qt.ItemDataRole.UserRole, customer.id)
                self.table.setItem(row, 0, id_item)

                # ستون ۱: نام
                name_item = QTableWidgetItem(customer.name)
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 1, name_item)

                # ستون ۲: تلفن
                phone_text = customer.phone if customer.phone else "—"
                phone_item = QTableWidgetItem(phone_text)
                phone_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 2, phone_item)

                # ستون ۳: تاریخ ثبت با ارقام فارسی
                date_item = QTableWidgetItem(format_date(customer.created_at))
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 3, date_item)

                # ستون ۴: چیپ وضعیت تماس
                badge_widget = QWidget()
                b_layout = QHBoxLayout(badge_widget)
                b_layout.setContentsMargins(0, 0, 0, 0)
                b_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                b_layout.addWidget(PhoneBadge(bool(customer.phone)))
                self.table.setCellWidget(row, 4, badge_widget)

            self.table.blockSignals(False)

        except Exception as exc:
            self.table.blockSignals(False)
            QMessageBox.critical(self, "خطای دیتابیس", f"بارگذاری مشتریان انجام نشد.\n{exc}")

    # -----------------------------------------------------
    # انتخاب مشتری از جدول
    # -----------------------------------------------------

    def on_customer_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return

        id_item = self.table.item(row, 0)
        if id_item is None:
            return

        c_id = id_item.data(Qt.ItemDataRole.UserRole)
        if c_id is None:
            raw_text = id_item.text().translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
            try:
                c_id = int(raw_text)
            except ValueError:
                return

        customer = self.db.query(Customer).filter(Customer.id == c_id).first()
        if not customer:
            return

        self.selected_customer_id = customer.id
        self.name_input.setText(customer.name)
        self.phone_input.setText(customer.phone or "")

        self.save_button.setText("ذخیره تغییرات")
        self.delete_button.setEnabled(True)

    # -----------------------------------------------------
    # ثبت و ویرایش مشتری
    # -----------------------------------------------------

    def save_customer(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()

        if not name:
            QMessageBox.warning(self, "اطلاعات ناقص", "لطفاً نام مشتری را وارد کنید.")
            self.name_input.setFocus()
            return

        if len(name) > 150:
            QMessageBox.warning(self, "نام نامعتبر", "نام مشتری نباید بیشتر از ۱۵۰ کاراکتر باشد.")
            return

        if len(phone) > 20:
            QMessageBox.warning(self, "شماره نامعتبر", "شماره تلفن نباید بیشتر از ۲۰ کاراکتر باشد.")
            return

        try:
            if self.selected_customer_id is not None:
                customer = (
                    self.db.query(Customer)
                    .filter(Customer.id == self.selected_customer_id)
                    .first()
                )

                if customer is None:
                    QMessageBox.warning(self, "مشتری پیدا نشد", "مشتری موردنظر در دیتابیس وجود ندارد.")
                    self.clear_form()
                    self.load_customers()
                    return

                customer.name = name
                customer.phone = phone or None
                success_message = "اطلاعات مشتری با موفقیت ویرایش شد."
            else:
                customer = Customer(
                    name=name,
                    phone=phone or None,
                    created_at=datetime.utcnow(),
                )
                self.db.add(customer)
                success_message = "مشتری جدید با موفقیت ثبت شد."

            self.db.commit()
            self.clear_form()
            self.load_customers()

            QMessageBox.information(self, "عملیات موفق", success_message)

        except Exception as exc:
            self.db.rollback()
            QMessageBox.critical(self, "خطا", f"ذخیره اطلاعات انجام نشد.\n{exc}")

    # -----------------------------------------------------
    # حذف مشتری
    # -----------------------------------------------------

    def delete_customer(self):
        customer = self.get_current_customer()
        if not customer:
            return

        answer = QMessageBox.question(
            self,
            "تأیید حذف",
            f"آیا از حذف مشتری «{customer.name}» مطمئن هستید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db.delete(customer)
            self.db.commit()

            self.clear_form()
            self.load_customers()

            QMessageBox.information(self, "عملیات موفق", "مشتری با موفقیت حذف شد.")

        except Exception as exc:
            self.db.rollback()
            QMessageBox.critical(self, "خطا در حذف", f"حذف مشتری انجام نشد.\n{exc}")

    # -----------------------------------------------------
    # پاک‌کردن فرم
    # -----------------------------------------------------

    def clear_form(self):
        self.selected_customer_id = None

        self.name_input.clear()
        self.phone_input.clear()

        self.save_button.setText("ثبت مشتری")
        self.delete_button.setEnabled(False)

        self.table.clearSelection()
        self.name_input.setFocus()

    def closeEvent(self, event):
        if not self._closing:
            self._closing = True
            try:
                self.db.close()
            except Exception:
                pass
        super().closeEvent(event)
