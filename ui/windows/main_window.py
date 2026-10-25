from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.components.sidebar import Sidebar
from ui.components.topbar import Topbar
from ui.pages.dashboard_page import DashboardPage
from ui.pages.placeholder_page import PlaceholderPage
from ui.pages.pos_page import PosPage
from ui.pages.menu_page import MenuPage
from ui.pages.inventory_page import InventoryPage
from ui.pages.customers_page import CustomersPage
from ui.pages.orders_page import OrdersPage
from ui.pages.reports_page import ReportsPage



class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("مدیریت کافه")
        self.resize(1440, 900)
        self.setMinimumSize(1080, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        root = QWidget()
        root.setObjectName("root")

        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_requested.connect(self.show_page)
        outer.addWidget(self.sidebar)

        content = QWidget()

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(26, 20, 26, 14)
        content_layout.setSpacing(18)

        self.topbar = Topbar()
        content_layout.addWidget(self.topbar)

        self.stack = QStackedWidget()
        self.pages = {}

        self.add_page("dashboard", DashboardPage())

        self.add_page("pos", PosPage())

        self.add_page("menu", MenuPage())

        self.add_page("customers", CustomersPage())

        self.add_page("inventory", InventoryPage())

        self.add_page("orders", OrdersPage())

        self.add_page("reports", ReportsPage())

        content_layout.addWidget(self.stack, 1)

        footer = QHBoxLayout()

        status = QLabel("●  نسخه نمایشی — اطلاعات فعلاً آزمایشی است")
        status.setObjectName("muted")

        footer.addWidget(status)
        footer.addStretch(1)

        version = QLabel("نسخه ۱.۰.۰")
        version.setObjectName("muted")
        footer.addWidget(version)

        content_layout.addLayout(footer)

        outer.addWidget(content, 1)

        self.setCentralWidget(root)

        self.apply_styles()

        self.show_page("dashboard")

    def add_page(self, key, page):
        self.pages[key] = page
        self.stack.addWidget(page)

    def show_page(self, key):
        page = self.pages.get(key)

        if page is None:
            return

        self.stack.setCurrentWidget(page)
        self.sidebar.set_active(key)
        self.topbar.set_page_title(
            self.sidebar.page_title(key)
        )

    def apply_styles(self):

        self.setStyleSheet("""
            QWidget {
                font-family: "Vazirmatn", "Noto Sans Arabic", "DejaVu Sans";
                color: #1D3037;
            }

            #root {
                background: #F5F8FA;
            }

            #muted {
                color: #71808D;
                font-size: 11px;
            }

            #panel {
                background: white;
                border: 1px solid #E2E9EC;
                border-radius: 12px;
            }

            #panelTitle {
                font-size: 16px;
                font-weight: 700;
            }

            #statCard {
                background: white;
                border: 1px solid #E2E9EC;
                border-radius: 12px;
            }

            #statTitle {
                color: #52636D;
                font-size: 12px;
            }

            #statValue {
                font-size: 19px;
                font-weight: 700;
            }

            #statNote {
                font-size: 11px;
            }

            #productTile {
                background: #FBFCFD;
                border: 1px solid #E8EEF1;
                border-radius: 10px;
            }

            #productName {
                font-size: 12px;
                font-weight: 700;
            }

            QTableWidget {
                background: white;
                border: none;
                alternate-background-color: #F8FAFB;
                font-size: 11px;
            }

            QHeaderView::section {
                background: #F2F6F8;
                color: #647681;
                border: none;
                padding: 9px 4px;
                font-weight: 600;
            }

            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #EDF1F3;
            }
        """)