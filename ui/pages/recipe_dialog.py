from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QAbstractItemView,
    QWidget,
)



SAMPLE_INGREDIENTS = [
    {
        "id": 1,
        "name": "دانه قهوه",
        "unit": "گرم",
    },
    {
        "id": 2,
        "name": "شیر",
        "unit": "میلی‌لیتر",
    },
    {
        "id": 3,
        "name": "شکر",
        "unit": "گرم",
    },
    {
        "id": 4,
        "name": "شکلات",
        "unit": "گرم",
    },
    {
        "id": 5,
        "name": "سیروپ وانیل",
        "unit": "میلی‌لیتر",
    },
]


class RecipeDialog(QDialog):
    def __init__(
        self,
        product_name,
        sale_price=0,
        recipe=None,
        parent=None,
    ):
        super().__init__(parent)

        self.product_name = product_name
        self.sale_price = sale_price

        self.recipe = recipe or {}

        self.ingredients = SAMPLE_INGREDIENTS

        self.setWindowTitle("دستور تهیه محصول")
        self.setMinimumSize(650, 500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.build_ui()
        self.load_recipe()


    def build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        title = QLabel("دستور تهیه محصول")
        title.setObjectName("pageTitle")

        product_label = QLabel(
            f"محصول: {self.product_name}"
        )
        product_label.setObjectName("subtitle")

        main_layout.addWidget(title)
        main_layout.addWidget(product_label)

        ingredient_form = QFormLayout()
        ingredient_form.setSpacing(12)

        self.ingredient_combo = QComboBox()

        for ingredient in self.ingredients:
            self.ingredient_combo.addItem(
                ingredient["name"],
                ingredient["id"],
            )

        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.001, 999999)
        self.quantity_input.setDecimals(3)
        self.quantity_input.setValue(1)
        self.quantity_input.setSingleStep(1)

        self.unit_label = QLabel("—")

        self.ingredient_combo.currentIndexChanged.connect(
            self.update_unit
        )

        ingredient_form.addRow(
            "ماده اولیه:",
            self.ingredient_combo,
        )

        ingredient_form.addRow(
            "مقدار مصرف:",
            self.quantity_input,
        )

        ingredient_form.addRow(
            "واحد اندازه‌گیری:",
            self.unit_label,
        )

        main_layout.addLayout(ingredient_form)

        add_button_layout = QHBoxLayout()
        add_button_layout.addStretch()

        self.add_button = QPushButton(
            "افزودن ماده اولیه"
        )
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(
            self.add_ingredient
        )

        add_button_layout.addWidget(self.add_button)

        main_layout.addLayout(add_button_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(
            [
                "ماده اولیه",
                "مقدار مصرف",
                "واحد",
            ]
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.table.setAlternatingRowColors(True)

        main_layout.addWidget(self.table)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        self.remove_button = QPushButton(
            "حذف ماده انتخاب‌شده"
        )
        self.remove_button.setObjectName("secondaryButton")
        self.remove_button.clicked.connect(
            self.remove_ingredient
        )

        self.cancel_button = QPushButton("انصراف")
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.clicked.connect(self.reject)

        self.save_button = QPushButton("ذخیره دستور تهیه")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.save_recipe)

        bottom_layout.addWidget(self.remove_button)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.cancel_button)
        bottom_layout.addWidget(self.save_button)

        main_layout.addLayout(bottom_layout)

        self.update_unit()


    def update_unit(self):
        ingredient_id = self.ingredient_combo.currentData()

        ingredient = next(
            (
                item
                for item in self.ingredients
                if item["id"] == ingredient_id
            ),
            None,
        )

        if ingredient:
            self.unit_label.setText(
                ingredient["unit"]
            )
        else:
            self.unit_label.setText("—")


    def add_ingredient(self):
        ingredient_id = self.ingredient_combo.currentData()

        if ingredient_id is None:
            QMessageBox.warning(
                self,
                "خطا",
                "ابتدا یک ماده اولیه انتخاب کنید.",
            )
            return

        quantity = self.quantity_input.value()

        ingredient = next(
            (
                item
                for item in self.ingredients
                if item["id"] == ingredient_id
            ),
            None,
        )

        if ingredient is None:
            return


        if ingredient_id in self.recipe:
            self.recipe[ingredient_id]["quantity"] += quantity
        else:
            self.recipe[ingredient_id] = {
                "ingredient_id": ingredient_id,
                "name": ingredient["name"],
                "unit": ingredient["unit"],
                "quantity": quantity,
            }

        self.refresh_table()


    def refresh_table(self):
        self.table.setRowCount(0)

        for ingredient_id, item in self.recipe.items():
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(
                item["name"]
            )

            quantity_text = (
                f"{item['quantity']:,.3f}"
                .rstrip("0")
                .rstrip(".")
            )

            quantity_item = QTableWidgetItem(
                quantity_text
            )

            unit_item = QTableWidgetItem(
                item["unit"]
            )

            name_item.setData(
                Qt.ItemDataRole.UserRole,
                ingredient_id,
            )

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, quantity_item)
            self.table.setItem(row, 2, unit_item)


    def remove_ingredient(self):
        selected_row = self.table.currentRow()

        if selected_row < 0:
            QMessageBox.information(
                self,
                "انتخاب ماده اولیه",
                "ابتدا یک ماده اولیه از جدول انتخاب کنید.",
            )
            return

        name_item = self.table.item(selected_row, 0)

        if name_item is None:
            return

        ingredient_id = name_item.data(
            Qt.ItemDataRole.UserRole
        )

        self.recipe.pop(ingredient_id, None)

        self.refresh_table()


    def load_recipe(self):
        self.refresh_table()


    def get_recipe(self):
        return {
            ingredient_id: item.copy()
            for ingredient_id, item in self.recipe.items()
        }


    def save_recipe(self):
        if not self.recipe:
            QMessageBox.warning(
                self,
                "دستور تهیه خالی است",
                "لطفاً حداقل یک ماده اولیه اضافه کنید.",
            )
            return

        self.accept()