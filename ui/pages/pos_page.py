# /home/amirali-arzande/cafe-pos-desktop/ui/pages/pos_page.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError

from database.db import init_db
from database.models.cafe.customer import Customer
from database.models.cafe.menu import MenuCategory, MenuItem
from services.order_service import process_order

# =========================================================
# توابع کمکی تبدیل ارقام و فرمت‌ها
# =========================================================

def to_persian_digits(text: str) -> str:
    """تبدیل اعداد انگلیسی به ارقام فارسی"""
    if text is None:
        return ""
    trans = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(text).translate(trans)


def money(value):
    """نمایش مبلغ به تومان با جداکننده سه رقمی و ارقام فارسی"""
    try:
        val = int(round(float(value or 0)))
        return f"{to_persian_digits(f'{val:,}')} تومان"
    except (ValueError, TypeError):
        return "۰ تومان"


def product_emoji(name, category_name=""):
    """انتخاب آیکون ایموجی مرتبط با نام محصول"""
    text = f"{name} {category_name}".casefold()
    if "کیک" in text or "چیزکیک" in text:
        return "🍰"
    if "کوکی" in text or "بیسکوئیت" in text:
        return "🍪"
    if "شکلات" in text or "موکا" in text or "هات چاکلت" in text:
        return "🍫"
    if "چای" in text or "دمنوش" in text or "ماسالا" in text:
        return "🍵"
    if "آیس" in text or "سرد" in text or "شیک" in text or "اسموتی" in text:
        return "🧊"
    if "شیر" in text or "لاته" in text or "کاپوچینو" in text:
        return "🥛"
    if "کروسان" in text or "نان" in text or "پیراشکی" in text:
        return "🥐"
    if "آبمیوه" in text or "موهیتو" in text:
        return "🍹"
    return "☕"


# =========================================================
# استایل‌های سراسری کامپوننت
# =========================================================

PAGE_STYLESHEET = """
QWidget {
    font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif;
    color: #1E293B;
}

QFrame.cardPanel {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}

QLineEdit, QComboBox {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
    color: #0F172A;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #28745A;
    background-color: #FFFFFF;
}

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

QPushButton.primaryBtn {
    background-color: #28745A;
    color: #FFFFFF;
    border: none;
    font-weight: 700;
}

QPushButton.primaryBtn:hover {
    background-color: #1F5E48;
}

QPushButton.primaryBtn:disabled {
    background-color: #A3C7BC;
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

QScrollArea {
    border: none;
    background: transparent;
}
"""


# =========================================================
# کارت آیتم در کاتالوگ فروش (ProductCard)
# =========================================================

class ProductCard(QPushButton):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # دایره پس‌زمینه ایموجی
        emoji_badge = QLabel(product["emoji"])
        emoji_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_badge.setFixedSize(48, 48)
        emoji_badge.setStyleSheet("""
            font-size: 26px;
            background: #E8F4F1;
            border-radius: 24px;
        """)

        name = QLabel(product["name"])
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)
        name.setStyleSheet("font-size: 13px; font-weight: 700; color: #0F172A; background: transparent;")

        category = QLabel(product["category"])
        category.setAlignment(Qt.AlignmentFlag.AlignCenter)
        category.setStyleSheet("font-size: 11px; color: #64748B; background: transparent;")

        price = QLabel(money(product["price"]))
        price.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price.setStyleSheet("font-size: 13px; font-weight: 800; color: #28745A; background: transparent;")

        layout.addWidget(emoji_badge, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name)
        layout.addWidget(category)
        layout.addWidget(price)

        self.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border: 1px solid #28745A;
            }
            QPushButton:pressed {
                background-color: #E8F4F1;
            }
        """)


# =========================================================
# ردیف آیتم در سبد خرید (CartRow)
# =========================================================

class CartRow(QFrame):
    def __init__(self, product, quantity, on_change, on_delete, parent=None):
        super().__init__(parent)
        self.product = product
        self.quantity = quantity
        self.on_change = on_change
        self.on_delete = on_delete

        self.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # جزئیات عنوان و قیمت
        details = QVBoxLayout()
        details.setSpacing(3)

        name = QLabel(product["name"])
        name.setWordWrap(True)
        name.setStyleSheet("font-weight: 700; font-size: 13px; color: #0F172A; border: none; background: transparent;")

        unit_p = QLabel(f"فی: {money(product['price'])}")
        unit_p.setStyleSheet("font-size: 11px; color: #64748B; border: none; background: transparent;")

        subtotal = QLabel(f"جمع: {money(product['price'] * quantity)}")
        subtotal.setStyleSheet("font-size: 12px; font-weight: 800; color: #28745A; border: none; background: transparent;")

        details.addWidget(name)
        details.addWidget(unit_p)
        details.addWidget(subtotal)
        layout.addLayout(details, 1)

        # کنترل‌های تعداد (- / + / سطل زباله)
        qty_box = QVBoxLayout()
        qty_box.setSpacing(6)
        qty_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(4)

        minus_btn = QPushButton("−")
        minus_btn.setFixedSize(26, 26)
        minus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        minus_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #28745A;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 800;
                padding: 0;
            }
            QPushButton:hover {
                background: #E8F4F1;
                border-color: #28745A;
            }
        """)
        minus_btn.clicked.connect(lambda: self.on_change(product["id"], -1))

        qty_lbl = QLabel(to_persian_digits(str(quantity)))
        qty_lbl.setFixedWidth(24)
        qty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qty_lbl.setStyleSheet("font-weight: 800; font-size: 13px; border: none; background: transparent; color: #0F172A;")

        plus_btn = QPushButton("+")
        plus_btn.setFixedSize(26, 26)
        plus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        plus_btn.setStyleSheet("""
            QPushButton {
                background: #28745A;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 800;
                padding: 0;
            }
            QPushButton:hover {
                background: #1F5E48;
            }
        """)
        plus_btn.clicked.connect(lambda: self.on_change(product["id"], 1))

        ctrl_row.addWidget(minus_btn)
        ctrl_row.addWidget(qty_lbl)
        ctrl_row.addWidget(plus_btn)
        qty_box.addLayout(ctrl_row)

        del_btn = QPushButton("حذف")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #DC2626;
                border: none;
                font-size: 11px;
                font-weight: 600;
                padding: 2px 4px;
            }
            QPushButton:hover {
                color: #991B1B;
                text-decoration: underline;
            }
        """)
        del_btn.clicked.connect(lambda: self.on_delete(product["id"]))
        qty_box.addWidget(del_btn, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(qty_box)


# =========================================================
# صفحه اصلی صندوق و فروش (PosPage)
# =========================================================

class PosPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.cart = {}
        self.products = []
        self.categories = []
        self.customers = []
        self.active_category_id = None
        self.category_buttons = {}

        self.setStyleSheet(PAGE_STYLESHEET)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._build_ui()
        self.load_all_data()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        # -------------------------------------------------
        # ۱. پنل کاتالوگ محصولات (سمت راست در RTL)
        # -------------------------------------------------
        catalog_panel = QFrame()
        catalog_panel.setProperty("class", "cardPanel")
        catalog_layout = QVBoxLayout(catalog_panel)
        catalog_layout.setContentsMargins(16, 14, 16, 14)
        catalog_layout.setSpacing(12)

        # هدر کاتالوگ + دکمه رفرش زنده
        cat_header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("ثبت سفارش و فاکتور فروش")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A;")

        subtitle = QLabel("برای افزودن به سبد خرید، روی آیتم مورد نظر کلیک کنید")
        subtitle.setStyleSheet("font-size: 12px; color: #64748B;")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        cat_header.addLayout(title_box)
        cat_header.addStretch()

        self.refresh_btn = QPushButton("🔄 به‌روزرسانی منو")
        self.refresh_btn.setToolTip("بارگذاری آخرین محصولات و مشتریان از دیتابیس")
        self.refresh_btn.setMinimumHeight(34)
        self.refresh_btn.clicked.connect(self.load_all_data)
        cat_header.addWidget(self.refresh_btn)

        catalog_layout.addLayout(cat_header)

        # ردیف جستجو
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 جست‌وجوی سریع نام محصول منو...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumHeight(38)
        self.search_input.textChanged.connect(self.refresh_products)
        catalog_layout.addWidget(self.search_input)

        # اسکرول دسته‌بندی‌ها (Pill bar)
        cat_scroll = QScrollArea()
        cat_scroll.setWidgetResizable(True)
        cat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cat_scroll.setFixedHeight(48)
        cat_scroll.setStyleSheet("background: transparent; border: none;")

        self.category_container = QWidget()
        self.category_bar = QHBoxLayout(self.category_container)
        self.category_bar.setContentsMargins(0, 4, 0, 4)
        self.category_bar.setSpacing(8)
        cat_scroll.setWidget(self.category_container)
        catalog_layout.addWidget(cat_scroll)

        # محفظه گرید کارت‌های محصول
        self.products_scroll = QScrollArea()
        self.products_scroll.setWidgetResizable(True)
        self.products_scroll.setStyleSheet("background: #F8FAFC; border-radius: 10px; border: 1px solid #E2E8F0;")

        self.products_container = QWidget()
        self.products_container.setStyleSheet("background: transparent;")
        self.products_grid = QGridLayout(self.products_container)
        self.products_grid.setContentsMargins(10, 10, 10, 10)
        self.products_grid.setSpacing(12)
        self.products_scroll.setWidget(self.products_container)

        catalog_layout.addWidget(self.products_scroll, 1)
        root.addWidget(catalog_panel, 1)

        # -------------------------------------------------
        # ۲. پنل فاکتور و سبد خرید (سمت چپ در RTL)
        # -------------------------------------------------
        cart_panel = QFrame()
        cart_panel.setProperty("class", "cardPanel")
        cart_panel.setMinimumWidth(330)
        cart_panel.setMaximumWidth(400)

        cart_layout = QVBoxLayout(cart_panel)
        cart_layout.setContentsMargins(16, 14, 16, 14)
        cart_layout.setSpacing(10)

        # هدر سبد خرید
        cart_header = QHBoxLayout()
        cart_title = QLabel("سبد خرید جاری")
        cart_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")

        self.cart_badge = QLabel("۰ قلم")
        self.cart_badge.setStyleSheet("""
            background: #E8F4F1;
            color: #28745A;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
        """)

        cart_header.addWidget(cart_title)
        cart_header.addStretch()
        cart_header.addWidget(self.cart_badge)
        cart_layout.addLayout(cart_header)

        # اسکرول آیتم‌های انتخابی سبد خرید
        self.cart_scroll = QScrollArea()
        self.cart_scroll.setWidgetResizable(True)
        self.cart_scroll.setStyleSheet("background: transparent; border: none;")

        self.cart_container = QWidget()
        self.cart_container.setStyleSheet("background: transparent;")
        self.cart_items_layout = QVBoxLayout(self.cart_container)
        self.cart_items_layout.setContentsMargins(0, 0, 0, 0)
        self.cart_items_layout.setSpacing(8)
        self.cart_scroll.setWidget(self.cart_container)

        cart_layout.addWidget(self.cart_scroll, 1)

        # وضعیت سبد خالی
        self.empty_label = QLabel("سبد خرید شما خالی است.\nبرای شروع، از منو اقلام را انتخاب کنید.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #94A3B8; font-size: 12px; padding: 24px;")
        cart_layout.addWidget(self.empty_label)

        # فرم فاکتور (مشتری و پرداخت)
        meta_box = QVBoxLayout()
        meta_box.setSpacing(8)

        lbl_cust = QLabel("مشتری:")
        lbl_cust.setStyleSheet("font-size: 12px; font-weight: 600; color: #475569;")
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumHeight(36)
        meta_box.addWidget(lbl_cust)
        meta_box.addWidget(self.customer_combo)

        lbl_pay = QLabel("وضعیت پرداخت فاکتور:")
        lbl_pay.setStyleSheet("font-size: 12px; font-weight: 600; color: #475569;")
        self.payment_combo = QComboBox()
        self.payment_combo.setMinimumHeight(36)
        self.payment_combo.addItem("پرداخت‌شده نقدی / پوز", True)
        self.payment_combo.addItem("حساب دفتری (پرداخت‌نشده)", False)
        meta_box.addWidget(lbl_pay)
        meta_box.addWidget(self.payment_combo)

        cart_layout.addLayout(meta_box)

        # خط جداکننده
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("border-top: 1px dashed #CBD5E1; margin: 4px 0;")
        cart_layout.addWidget(sep)

        # خلاصه محاسبات مالی
        summary_panel = QFrame()
        summary_panel.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 6px;")
        sum_layout = QVBoxLayout(summary_panel)
        sum_layout.setSpacing(6)

        sub_row = QHBoxLayout()
        sub_title = QLabel("جمع اقلام:")
        sub_title.setStyleSheet("color: #64748B; font-size: 12px;")
        self.subtotal_value = QLabel("۰ تومان")
        self.subtotal_value.setStyleSheet("font-weight: 700; color: #334155; font-size: 12px;")
        sub_row.addWidget(sub_title)
        sub_row.addStretch()
        sub_row.addWidget(self.subtotal_value)
        sum_layout.addLayout(sub_row)

        tot_row = QHBoxLayout()
        tot_title = QLabel("مبلغ نهایی فاکتور:")
        tot_title.setStyleSheet("font-weight: 800; font-size: 13px; color: #0F172A;")
        self.total_value = QLabel("۰ تومان")
        self.total_value.setStyleSheet("font-weight: 800; font-size: 16px; color: #28745A;")
        tot_row.addWidget(tot_title)
        tot_row.addStretch()
        tot_row.addWidget(self.total_value)
        sum_layout.addLayout(tot_row)

        cart_layout.addWidget(summary_panel)

        # دکمه‌های اقدام سبد خرید
        btn_box = QVBoxLayout()
        btn_box.setSpacing(6)

        self.checkout_button = QPushButton("ثبت نهایی سفارش (صدور فاکتور)")
        self.checkout_button.setProperty("class", "primaryBtn")
        self.checkout_button.setMinimumHeight(44)
        self.checkout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkout_button.setEnabled(False)
        self.checkout_button.clicked.connect(self.checkout)

        self.clear_button = QPushButton("خالی کردن سبد خرید")
        self.clear_button.setProperty("class", "dangerBtn")
        self.clear_button.setMinimumHeight(34)
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_button.clicked.connect(self.clear_cart)

        btn_box.addWidget(self.checkout_button)
        btn_box.addWidget(self.clear_button)
        cart_layout.addLayout(btn_box)

        root.addWidget(cart_panel)

    # ==================================================
    # لود یکپارچه داده‌ها (با پشتیبانی از Refresh)
    # ==================================================

    def load_all_data(self):
        """بازخوانی زنده مشتریان و کاتالوگ منو از پایگاه داده"""
        self.load_customers()
        self.load_catalog()

    def load_customers(self):
        session = init_db()
        try:
            session.expire_all()
            customers = session.query(Customer).order_by(Customer.name.asc()).all()
            self.customers = [{"id": c.id, "name": c.name} for c in customers]

            curr_id = self.customer_combo.currentData()

            self.customer_combo.blockSignals(True)
            self.customer_combo.clear()
            self.customer_combo.addItem("مشتری عمومی (آزاد / گذری)", None)

            for c in self.customers:
                self.customer_combo.addItem(c["name"], c["id"])

            idx = self.customer_combo.findData(curr_id)
            if idx >= 0:
                self.customer_combo.setCurrentIndex(idx)

            self.customer_combo.blockSignals(False)
        except SQLAlchemyError as error:
            self.customer_combo.clear()
            self.customer_combo.addItem("مشتری عمومی (آزاد / گذری)", None)
            QMessageBox.warning(self, "خطا در بارگذاری مشتریان", f"خطا در خواندن مشتریان:\n{error}")
        finally:
            session.close()

    def load_catalog(self):
        session = init_db()
        try:
            session.expire_all()
            categories = session.query(MenuCategory).order_by(MenuCategory.name.asc()).all()
            menu_items = session.query(MenuItem).order_by(MenuItem.name.asc()).all()

            self.categories = [{"id": c.id, "name": c.name} for c in categories]
            self.products = []

            for item in menu_items:
                cat_name = item.category.name if item.category is not None else "عمومی"
                self.products.append({
                    "id": item.id,
                    "name": item.name,
                    "category_id": item.category_id,
                    "category": cat_name,
                    "price": float(item.sale_price),
                    "emoji": product_emoji(item.name, cat_name),
                })
        except Exception as error:
            QMessageBox.critical(self, "خطا در بارگذاری منو", f"خواندن کاتالوگ ناموفق بود:\n{error}")
            self.categories = []
            self.products = []
        finally:
            session.close()

        valid_ids = {c["id"] for c in self.categories}
        if self.active_category_id not in valid_ids:
            self.active_category_id = None

        self.build_category_buttons()
        self.refresh_products()
        self.refresh_cart()

    # ==================================================
    # دسته‌بندی‌ها و فیلتر
    # ==================================================

    def build_category_buttons(self):
        while self.category_bar.count():
            item = self.category_bar.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.category_buttons = {}

        all_btn = QPushButton("همه محصولات")
        all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        all_btn.setMinimumHeight(32)
        all_btn.clicked.connect(lambda: self.select_category(None))
        self.category_buttons[None] = all_btn
        self.category_bar.addWidget(all_btn)

        for cat in self.categories:
            c_id = cat["id"]
            btn = QPushButton(cat["name"])
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(32)
            btn.clicked.connect(lambda _, cid=c_id: self.select_category(cid))
            self.category_buttons[c_id] = btn
            self.category_bar.addWidget(btn)

        self.category_bar.addStretch()
        self.select_category(self.active_category_id)

    def select_category(self, category_id):
        self.active_category_id = category_id
        for cid, btn in self.category_buttons.items():
            if cid == category_id:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #28745A;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 8px;
                        padding: 6px 14px;
                        font-weight: 700;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FFFFFF;
                        color: #475569;
                        border: 1px solid #CBD5E1;
                        border-radius: 8px;
                        padding: 6px 14px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #F1F5F9;
                        border-color: #94A3B8;
                    }
                """)
        self.refresh_products()

    # ==================================================
    # رندر کارت‌های محصول در گرید
    # ==================================================

    def refresh_products(self):
        while self.products_grid.count():
            item = self.products_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        search = self.search_input.text().strip().casefold()
        filtered = []

        for p in self.products:
            if self.active_category_id is not None and p["category_id"] != self.active_category_id:
                continue
            if search and search not in p["name"].casefold():
                continue
            filtered.append(p)

        columns = 3
        for idx, prod in enumerate(filtered):
            card = ProductCard(prod)
            card.clicked.connect(lambda _, p=prod: self.add_to_cart(p))
            self.products_grid.addWidget(card, idx // columns, idx % columns)

        if not filtered:
            empty = QLabel("هیچ آیتمی مطابق جست‌وجو در این دسته‌بندی یافت نشد.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #94A3B8; font-size: 13px; padding: 40px;")
            self.products_grid.addWidget(empty, 0, 0, 1, columns)

    # ==================================================
    # مدیریت سبد خرید
    # ==================================================

    def add_to_cart(self, product):
        pid = product["id"]
        if pid in self.cart:
            self.cart[pid]["quantity"] += 1
        else:
            self.cart[pid] = {"product": product.copy(), "quantity": 1}
        self.refresh_cart()

    def change_quantity(self, product_id, delta):
        if product_id not in self.cart:
            return
        self.cart[product_id]["quantity"] += delta
        if self.cart[product_id]["quantity"] <= 0:
            del self.cart[product_id]
        self.refresh_cart()

    def remove_item(self, product_id):
        if product_id in self.cart:
            del self.cart[product_id]
            self.refresh_cart()

    def refresh_cart(self):
        while self.cart_items_layout.count():
            item = self.cart_items_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        total_qty = sum(item["quantity"] for item in self.cart.values())
        total_price = sum(item["product"]["price"] * item["quantity"] for item in self.cart.values())

        for item in self.cart.values():
            row = CartRow(
                product=item["product"],
                quantity=item["quantity"],
                on_change=self.change_quantity,
                on_delete=self.remove_item,
            )
            self.cart_items_layout.addWidget(row)

        self.cart_items_layout.addStretch()
        self.empty_label.setVisible(total_qty == 0)

        self.cart_badge.setText(f"{to_persian_digits(str(total_qty))} قلم")
        self.subtotal_value.setText(money(total_price))
        self.total_value.setText(money(total_price))
        self.checkout_button.setEnabled(total_qty > 0)

    def clear_cart(self):
        if not self.cart:
            return

        reply = QMessageBox.question(
            self,
            "خالی کردن سبد",
            "آیا مطمئن هستید که می‌خواهید تمام اقلام این سفارش را پاک کنید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.cart.clear()
            self.refresh_cart()

    # ==================================================
    # تسویه و ثبت فاکتور
    # ==================================================

    def checkout(self):
        if not self.cart:
            QMessageBox.information(self, "سبد خالی", "ابتدا یک یا چند محصول را به سبد خرید اضافه کنید.")
            return

        customer_id = self.customer_combo.currentData()
        is_paid = self.payment_combo.currentData()
        customer_name = self.customer_combo.currentText()
        payment_text = "پرداخت‌شده" if is_paid else "پرداخت‌نشده (دفتری)"
        total_qty = sum(i["quantity"] for i in self.cart.values())

        reply = QMessageBox.question(
            self,
            "تأیید صدور فاکتور",
            (
                "آیا از ثبت نهایی این فاکتور اطمینان دارید؟\n\n"
                f"👤 طرف حساب: {customer_name}\n"
                f"💳 وضعیت پرداخت: {payment_text}\n"
                f"📦 تعداد کل اقلام: {to_persian_digits(str(total_qty))}\n"
                f"💰 مبلغ نهایی: {self.total_value.text()}"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        cart_items = [
            {"item_id": pid, "quantity": data["quantity"]}
            for pid, data in self.cart.items()
        ]

        self.checkout_button.setEnabled(False)
        self.checkout_button.setText("در حال ثبت و کسر از انبار...")

        try:
            result = process_order(
                cart_items=cart_items,
                performed_by_user="باریستا",
                customer_id=customer_id,
                is_paid=is_paid,
            )

            if not result.get("success"):
                QMessageBox.warning(
                    self,
                    "خطا در ثبت فاکتور",
                    f"ثبت سفارش انجام نشد و تغییرات لغو شد:\n\n{result.get('error', 'خطای نامشخص')}",
                )
                return

            fac_num = to_persian_digits(str(result["factor_number"]))
            final_price = money(result["total_price"])

            self.cart.clear()
            self.refresh_cart()
            self.customer_combo.setCurrentIndex(0)
            self.payment_combo.setCurrentIndex(0)

            QMessageBox.information(
                self,
                "ثبت موفق فاکتور",
                (
                    "✅ فاکتور با موفقیت در سیستم ثبت شد.\n\n"
                    f"شماره فاکتور: {fac_num}\n"
                    f"مشتری: {customer_name}\n"
                    f"مبلغ تسویه: {final_price}\n\n"
                    "موجودی مواد اولیه مرتبط در انبار کافه به‌طور خودکار کسر گردید."
                ),
            )

            self.load_catalog()

        except Exception as error:
            QMessageBox.critical(self, "خطای غیرمنتظره", f"خطا در حین فرآیند ثبت فاکتور:\n\n{error}")
        finally:
            self.checkout_button.setText("ثبت نهایی سفارش (صدور فاکتور)")
            self.checkout_button.setEnabled(bool(self.cart))
