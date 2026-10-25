from datetime import timedelta

import jdatetime

from sqlalchemy import func

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.db import init_db
from database.models.cafe.order_archive import OrderArchive
from database.models.warehouse.product import Product
from database.models.warehouse.warehouse_process import InventoryStock


# ─── پالت رنگی ─────────────────────────────────────────────────────
GREEN = "#28745A"
GREEN_LIGHT = "#E8F3EB"
MUTED = "#7B8580"
BORDER = "#E5EAE6"
WHITE = "#FFFFFF"
BG = "#F8FAF8"
TEXT = "#26352D"

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

WEEKDAY_NAMES = [
    "دوشنبه",
    "سه‌شنبه",
    "چهارشنبه",
    "پنجشنبه",
    "جمعه",
    "شنبه",
    "یکشنبه",
]


def to_persian_digits(value: str) -> str:
    """تبدیل رقم‌های انگلیسی به فارسی."""
    return str(value).translate(PERSIAN_DIGITS)


def format_number(value) -> str:
    """نمایش عدد با جداکننده هزارگان و رقم‌های فارسی."""
    try:
        number = int(round(float(value or 0)))
    except (TypeError, ValueError):
        number = 0

    formatted = f"{number:,}".replace(",", "٬")
    return to_persian_digits(formatted)


def format_amount(value, with_currency=True) -> str:
    """نمایش مبلغ."""
    result = format_number(value)
    return f"{result} تومان" if with_currency else result


class StatCard(QFrame):
    """کارت آماری با ظاهر تمیز و حرفه‌ای."""

    def __init__(
        self,
        title: str,
        value: str,
        note: str,
        icon: str,
        accent: str = GREEN,
    ):
        super().__init__()

        self.setObjectName("statCard")
        self.setMinimumHeight(118)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        icon_box = QLabel(icon)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setFixedSize(48, 48)
        icon_box.setStyleSheet(
            f"""
            background: {accent}18;
            color: {accent};
            border-radius: 24px;
            font-size: 20px;
            font-weight: 700;
            """
        )

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.setContentsMargins(0, 2, 0, 2)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"color: {MUTED}; font-size: 12px; font-weight: 500;"
        )

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 20px;
            font-weight: 800;
            letter-spacing: -0.3px;
            """
        )

        self.note_label = QLabel(note)
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet(
            f"color: {accent}; font-size: 11px; font-weight: 600;"
        )

        text_col.addWidget(self.title_label)
        text_col.addWidget(self.value_label)
        text_col.addWidget(self.note_label)
        text_col.addStretch()

        layout.addWidget(icon_box, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(text_col, 1)

        self.setStyleSheet(
            f"""
            QFrame#statCard {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
            """
        )

    def set_data(self, value: str, note: str | None = None):
        self.value_label.setText(value)

        if note is not None:
            self.note_label.setText(note)


class SalesChart(QWidget):
    """نمودار فروش هفتگی که داده‌های آن از دیتابیس دریافت می‌شود."""

    def __init__(self):
        super().__init__()

        self.setMinimumHeight(240)
        self.values = [0.0] * 7
        self.labels = [""] * 7

    def set_data(self, values: list[float], labels: list[str]):
        self.values = list(values)
        self.labels = list(labels)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin_left = 82
        margin_right = 16
        margin_top = 16
        margin_bottom = 36

        rect = self.rect().adjusted(
            margin_left,
            margin_top,
            -margin_right,
            -margin_bottom,
        )

        left = rect.x()
        top = rect.y()
        width = max(1, rect.width())
        height = max(1, rect.height())

        max_sales = max(self.values, default=0)
        max_axis_value = max(
            500_000,
            int((max_sales + 499_999) // 500_000) * 500_000,
        )

        painter.setFont(QFont("Vazirmatn", 8))

        # خطوط افقی و برچسب‌های محور Y
        for i in range(7):
            ratio = i / 6
            y = top + ratio * height
            axis_value = max_axis_value * (1 - ratio)

            painter.setPen(QPen(QColor(BORDER), 1, Qt.PenStyle.DotLine))
            painter.drawLine(
                int(left),
                int(y),
                int(left + width),
                int(y),
            )

            painter.setPen(QColor(MUTED))
            painter.drawText(
                QRectF(0, y - 10, left - 10, 20),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                format_number(axis_value),
            )

        # اگر داده‌ای وجود ندارد، فقط محور و برچسب‌ها نمایش داده می‌شوند.
        if len(self.values) < 2:
            return

        points = [
            QPointF(
                left + i * width / (len(self.values) - 1),
                top + height - (value / max_axis_value) * height,
            )
            for i, value in enumerate(self.values)
        ]

        # ناحیه زیر خط با گرادیان
        area = QPainterPath()
        area.moveTo(points[0].x(), top + height)
        area.lineTo(points[0])

        for point in points[1:]:
            area.lineTo(point)

        area.lineTo(points[-1].x(), top + height)
        area.closeSubpath()

        gradient = QLinearGradient(0, top, 0, top + height)
        gradient.setColorAt(0, QColor(40, 116, 90, 55))
        gradient.setColorAt(1, QColor(40, 116, 90, 5))
        painter.fillPath(area, gradient)

        # خط اصلی نمودار
        line = QPainterPath()
        line.moveTo(points[0])

        for point in points[1:]:
            line.lineTo(point)

        painter.setPen(
            QPen(
                QColor(GREEN),
                2.8,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        painter.drawPath(line)

        # نقاط نمودار
        for point in points:
            painter.setBrush(QColor(GREEN))
            painter.setPen(QPen(QColor(WHITE), 2.5))
            painter.drawEllipse(point, 4.5, 4.5)

        # برچسب روزها
        painter.setFont(QFont("Vazirmatn", 8))
        painter.setPen(QColor(MUTED))

        for i, label in enumerate(self.labels):
            x = left + i * width / (len(self.labels) - 1)
            painter.drawText(
                QRectF(x - 36, top + height + 10, 72, 20),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                label,
            )


class Panel(QFrame):
    """پنل استاندارد با هدر."""

    def __init__(self, title: str, subtitle: str | None = None):
        super().__init__()

        self.setObjectName("panel")

        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 16, 18, 16)
        self.body.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"color: {TEXT}; font-size: 15px; font-weight: 800;"
        )

        header.addWidget(title_label)
        header.addStretch()

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet(
                f"color: {MUTED}; font-size: 11px;"
            )
            header.addWidget(subtitle_label)

        self.body.addLayout(header)

        self.setStyleSheet(
            f"""
            QFrame#panel {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
            """
        )


class InventoryTile(QFrame):
    """کاشی محصول انبار؛ بدون نمایش مقدار موجودی."""

    def __init__(
        self,
        name: str,
        category: str,
        status: str = "محصول انبار",
        color: str = GREEN,
    ):
        super().__init__()

        self.setObjectName("inventoryTile")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        icon_label = QLabel("▱")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            f"color: {color}; font-size: 24px; font-weight: 700;"
        )

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(
            f"color: {TEXT}; font-size: 12px; font-weight: 700;"
        )

        category_label = QLabel(category)
        category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        category_label.setWordWrap(True)
        category_label.setStyleSheet(
            f"color: {MUTED}; font-size: 10px;"
        )

        status_label = QLabel(status)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet(
            f"""
            color: {color};
            background: {color}18;
            padding: 5px 8px;
            border-radius: 8px;
            font-size: 10px;
            font-weight: 600;
            """
        )

        layout.addWidget(icon_label)
        layout.addWidget(name_label)
        layout.addWidget(category_label)
        layout.addWidget(status_label)

        self.setStyleSheet(
            f"""
            QFrame#inventoryTile {{
                background: {BG};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QFrame#inventoryTile:hover {{
                border: 1px solid {GREEN}55;
                background: {GREEN_LIGHT};
            }}
            """
        )


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        # ─── کارت‌های آماری ───────────────────────────────────────
        stats = QGridLayout()
        stats.setSpacing(14)

        self.sales_card = StatCard(
            "فروش امروز",
            "—",
            "در حال دریافت اطلاعات",
            "▤",
            GREEN,
        )

        self.orders_card = StatCard(
            "تعداد سفارش‌ها",
            "—",
            "در حال دریافت اطلاعات",
            "▧",
            "#2587C7",
        )

        self.customers_card = StatCard(
            "مشتریان امروز",
            "—",
            "در حال دریافت اطلاعات",
            "♙",
            "#7652C8",
        )

        self.inventory_card = StatCard(
            "موجودی انبار",
            "—",
            "در حال دریافت اطلاعات",
            "⬡",
            "#D58A16",
        )

        stats.addWidget(self.sales_card, 0, 0)
        stats.addWidget(self.orders_card, 0, 1)
        stats.addWidget(self.customers_card, 0, 2)
        stats.addWidget(self.inventory_card, 0, 3)

        root.addLayout(stats)

        # ─── بخش میانی: نمودار و سفارش‌های اخیر ──────────────────
        middle = QHBoxLayout()
        middle.setSpacing(16)

        chart_panel = Panel("روند فروش", "۷ روز گذشته")
        self.sales_chart = SalesChart()
        chart_panel.body.addWidget(self.sales_chart, 1)
        middle.addWidget(chart_panel, 12)

        orders_panel = Panel("سفارش‌های اخیر")

        self.orders_table = QTableWidget(0, 4)
        self.orders_table.setHorizontalHeaderLabels(
            ["شماره فاکتور", "مشتری", "مبلغ", "زمان"]
        )
        self.orders_table.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.orders_table.verticalHeader().setVisible(False)
        self.orders_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.orders_table.setAlternatingRowColors(True)
        self.orders_table.setShowGrid(False)
        self.orders_table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection
        )
        self.orders_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.orders_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.orders_table.setMinimumHeight(240)
        self.orders_table.verticalHeader().setDefaultSectionSize(42)

        self.orders_table.setStyleSheet(
            f"""
            QTableWidget {{
                background: transparent;
                border: none;
                font-size: 12px;
                alternate-background-color: #F7FAF8;
            }}
            QHeaderView::section {{
                background: #F3F7F4;
                color: {MUTED};
                border: none;
                padding: 10px 6px;
                font-weight: 700;
                font-size: 11px;
            }}
            QTableWidget::item {{
                border-bottom: 1px solid #EDF1ED;
                padding: 6px;
            }}
            """
        )

        orders_panel.body.addWidget(self.orders_table)
        middle.addWidget(orders_panel, 10)

        root.addLayout(middle, 1)

        # ─── وضعیت محصولات انبار ─────────────────────────────────
        self.inventory_panel = Panel(
            "وضعیت موجودی انبار",
            "نمای سریع",
        )

        self.inventory_layout = QHBoxLayout()
        self.inventory_layout.setSpacing(12)
        self.inventory_panel.body.addLayout(self.inventory_layout)

        root.addWidget(self.inventory_panel)

        # استایل کلی صفحه
        self.setStyleSheet(
            f"""
            QWidget {{
                font-family: "Vazirmatn", "Noto Sans Arabic", "DejaVu Sans";
                color: {TEXT};
            }}
            """
        )

        # بارگذاری اولیه
        self.refresh_data()

        # تازه‌سازی خودکار برای دریافت تغییرات جدید دیتابیس
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(30_000)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start()

    def _load_dashboard_data(self) -> dict:
        """خواندن اطلاعات داشبورد از دیتابیس."""
        session = init_db()

        try:
            today = jdatetime.date.today()
            today_key = today.strftime("%Y/%m/%d")

            last_seven_days = [
                today - timedelta(days=offset)
                for offset in range(6, -1, -1)
            ]
            day_keys = [
                day.strftime("%Y/%m/%d")
                for day in last_seven_days
            ]

            # فروش امروز؛ فقط سفارش‌های پرداخت‌شده
            today_sales = (
                session.query(
                    func.coalesce(func.sum(OrderArchive.total_price), 0)
                )
                .filter(
                    OrderArchive.persian_date == today_key,
                    OrderArchive.is_paid.is_(True),
                )
                .scalar()
                or 0
            )

            # تعداد کل سفارش‌های ثبت‌شده امروز
            today_orders_count = (
                session.query(OrderArchive)
                .filter(OrderArchive.persian_date == today_key)
                .count()
            )

            # تعداد مشتریان ثبت‌شده‌ای که امروز سفارش داشته‌اند
            today_customers_count = (
                session.query(
                    func.count(func.distinct(OrderArchive.customer_id))
                )
                .filter(
                    OrderArchive.persian_date == today_key,
                    OrderArchive.customer_id.isnot(None),
                )
                .scalar()
                or 0
            )

            # مجموع فروش هر روز در بازه هفت‌روزه
            weekly_rows = (
                session.query(
                    OrderArchive.persian_date,
                    func.coalesce(func.sum(OrderArchive.total_price), 0),
                )
                .filter(
                    OrderArchive.persian_date.in_(day_keys),
                    OrderArchive.is_paid.is_(True),
                )
                .group_by(OrderArchive.persian_date)
                .all()
            )

            sales_by_date = {
                date_key: float(total or 0)
                for date_key, total in weekly_rows
            }

            weekly_sales = [
                sales_by_date.get(date_key, 0.0)
                for date_key in day_keys
            ]

            weekly_labels = [
                WEEKDAY_NAMES[day.togregorian().weekday()]
                for day in last_seven_days
            ]

            # آخرین پنج سفارش
            recent_orders_query = (
                session.query(OrderArchive)
                .order_by(
                    OrderArchive.created_at.desc(),
                    OrderArchive.id.desc(),
                )
                .limit(5)
                .all()
            )

            recent_orders = []

            for order in recent_orders_query:
                customer_name = (
                    order.customer_name
                    or (
                        order.customer.name
                        if order.customer is not None
                        else None
                    )
                    or "مشتری آزاد"
                )

                order_time = order.persian_time or ""

                if not order_time and order.created_at:
                    order_time = order.created_at.strftime("%H:%M")

                recent_orders.append(
                    {
                        "factor_number": order.factor_number or "—",
                        "customer_name": customer_name,
                        "total_price": float(order.total_price or 0),
                        "time": to_persian_digits(order_time),
                    }
                )

            # محصولاتی که برایشان رکورد موجودی انبار ثبت شده است.
            # مقدار اولیه و مقدار فعلی موجودی خوانده یا نمایش داده نمی‌شود.
            inventory_products_query = (
                session.query(Product)
                .join(
                    InventoryStock,
                    InventoryStock.product_id == Product.id,
                )
                .order_by(Product.name.asc())
                .all()
            )

            inventory_products = []

            for product in inventory_products_query:
                category_name = (
                    product.category.name
                    if product.category is not None
                    else "بدون دسته‌بندی"
                )

                inventory_products.append(
                    {
                        "name": product.name,
                        "category": category_name,
                    }
                )

            return {
                "today_sales": float(today_sales or 0),
                "today_orders_count": today_orders_count,
                "today_customers_count": today_customers_count,
                "weekly_sales": weekly_sales,
                "weekly_labels": weekly_labels,
                "recent_orders": recent_orders,
                "inventory_count": len(inventory_products),
                "inventory_products": inventory_products,
            }

        finally:
            session.close()

    def refresh_data(self):
        """به‌روزرسانی اطلاعات نمایشی داشبورد."""
        try:
            data = self._load_dashboard_data()
        except Exception as error:
            print(f"خطا در دریافت اطلاعات داشبورد: {error}")

            self.sales_card.set_data(
                "—",
                "خطا در دریافت اطلاعات",
            )
            self.orders_card.set_data(
                "—",
                "خطا در دریافت اطلاعات",
            )
            self.customers_card.set_data(
                "—",
                "خطا در دریافت اطلاعات",
            )
            self.inventory_card.set_data(
                "—",
                "خطا در دریافت اطلاعات",
            )

            self.sales_chart.set_data(
                [0.0] * 7,
                [""] * 7,
            )

            self._render_orders([])
            self._render_inventory([])
            return

        self.sales_card.set_data(
            format_amount(data["today_sales"]),
            "مجموع سفارش‌های پرداخت‌شده امروز",
        )

        self.orders_card.set_data(
            to_persian_digits(str(data["today_orders_count"])),
            "فاکتورهای ثبت‌شده امروز",
        )

        self.customers_card.set_data(
            to_persian_digits(str(data["today_customers_count"])),
            "مشتریان دارای سفارش امروز",
        )

        self.inventory_card.set_data(
            to_persian_digits(str(data["inventory_count"])),
            "محصولات دارای رکورد انبار",
        )

        self.sales_chart.set_data(
            data["weekly_sales"],
            data["weekly_labels"],
        )

        self._render_orders(data["recent_orders"])
        self._render_inventory(data["inventory_products"])

    def _render_orders(self, orders: list[dict]):
        """نمایش سفارش‌های دریافت‌شده در جدول."""
        self.orders_table.clearSpans()

        if not orders:
            self.orders_table.setRowCount(1)

            empty_item = QTableWidgetItem(
                "هنوز سفارشی ثبت نشده است"
            )
            empty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.orders_table.setItem(0, 0, empty_item)
            self.orders_table.setSpan(0, 0, 1, 4)
            return

        self.orders_table.setRowCount(len(orders))

        for row_index, order in enumerate(orders):
            values = [
                order["factor_number"],
                order["customer_name"],
                format_amount(order["total_price"]),
                order["time"],
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )
                self.orders_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    def _render_inventory(self, products: list[dict]):
        """نمایش نام محصولات انبار بدون نمایش مقدار موجودی."""
        while self.inventory_layout.count():
            item = self.inventory_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        if not products:
            empty_label = QLabel(
                "محصولی برای نمایش در انبار ثبت نشده است"
            )
            empty_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            empty_label.setStyleSheet(
                f"color: {MUTED}; font-size: 12px; padding: 16px;"
            )
            self.inventory_layout.addWidget(empty_label)
            return

        # برای حفظ چیدمان، حداکثر شش محصول به‌صورت کاشی نمایش داده می‌شود.
        for product in products[:6]:
            tile = InventoryTile(
                name=product["name"],
                category=product["category"],
            )
            self.inventory_layout.addWidget(tile)
