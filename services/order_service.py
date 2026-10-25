import uuid

import jdatetime

from database.db import init_db

from database.models.cafe.menu import MenuItem
from database.models.cafe.customer import Customer

from database.models.cafe.order_archive import (
    OrderArchive,
    OrderItemSnapshot,
)

from database.models.warehouse.warehouse_process import (
    InventoryStock,
    StockTransaction,
    TransactionType,
    StockOutReason,
)


def process_order(
    cart_items,
    performed_by_user="باریستا",
    customer_id=None,
    is_paid=True,
):
    """
    ثبت سفارش، ذخیره فاکتور و کسر مواد اولیه از انبار.

    ساختار cart_items:
        [
            {"item_id": 1, "quantity": 2},
            {"item_id": 3, "quantity": 1},
        ]

    خروجی موفق:
        {
            "success": True,
            "factor_number": "...",
            "total_price": 200000,
            "total_items_count": 3,
            "message": "..."
        }

    خروجی ناموفق:
        {
            "success": False,
            "error": "..."
        }
    """

    session = init_db()

    try:
        # -----------------------------
        # 1. اعتبارسنجی سبد خرید
        # -----------------------------

        if not cart_items:
            raise ValueError("سبد خرید خالی است.")

        normalized_cart = []

        for cart_item in cart_items:
            try:
                menu_item_id = int(cart_item["item_id"])
                quantity = int(cart_item["quantity"])
            except (KeyError, TypeError, ValueError):
                raise ValueError(
                    "اطلاعات یکی از اقلام سبد خرید نامعتبر است."
                )

            if menu_item_id <= 0:
                raise ValueError(
                    "شناسه یکی از محصولات نامعتبر است."
                )

            if quantity <= 0:
                raise ValueError(
                    "تعداد سفارش باید بیشتر از صفر باشد."
                )

            normalized_cart.append({
                "item_id": menu_item_id,
                "quantity": quantity,
            })

        print(
            "\n--- شروع ثبت سفارش، فاکتور و به‌روزرسانی انبار ---"
        )

        # -----------------------------
        # 2. اطلاعات اولیه سفارش
        # -----------------------------

        grand_total = 0.0
        total_items_count = 0
        archive_items_data = []

        customer_name_snapshot = None

        # -----------------------------
        # 3. بررسی مشتری
        # -----------------------------

        if customer_id is not None:
            customer = (
                session.query(Customer)
                .filter(Customer.id == customer_id)
                .first()
            )

            if customer is None:
                raise ValueError(
                    f"مشتری با شناسه {customer_id} یافت نشد."
                )

            customer_name_snapshot = customer.name

        # -----------------------------
        # 4. بررسی محصولات و موجودی
        # -----------------------------

        for cart_item in normalized_cart:
            menu_item_id = cart_item["item_id"]
            quantity = cart_item["quantity"]

            menu_item = (
                session.query(MenuItem)
                .filter(MenuItem.id == menu_item_id)
                .first()
            )

            if menu_item is None:
                raise ValueError(
                    f"محصول منو با شناسه {menu_item_id} یافت نشد."
                )

            unit_price = float(menu_item.sale_price)
            item_subtotal = unit_price * quantity

            grand_total += item_subtotal
            total_items_count += quantity

            print(
                f"سفارش: {quantity} عدد «{menu_item.name}» "
                f"| قیمت واحد: {unit_price:,.0f} "
                f"| جمع: {item_subtotal:,.0f}"
            )

            recipe_snapshot_lines = []

            # -----------------------------
            # 5. کسر مواد اولیه
            # -----------------------------

            for recipe in menu_item.recipe_items:
                warehouse_product = recipe.warehouse_product

                if warehouse_product is None:
                    raise ValueError(
                        f"ماده اولیه یکی از دستورهای تهیه "
                        f"محصول «{menu_item.name}» معتبر نیست."
                    )

                required_amount = float(recipe.required_amount)

                if required_amount <= 0:
                    raise ValueError(
                        f"مقدار ماده اولیه "
                        f"«{warehouse_product.name}» نامعتبر است."
                    )

                total_required = required_amount * quantity

                stock = (
                    session.query(InventoryStock)
                    .filter(
                        InventoryStock.product_id
                        == warehouse_product.id
                    )
                    .with_for_update()
                    .first()
                )

                if stock is None:
                    raise ValueError(
                        f"موجودی انبار برای ماده اولیه "
                        f"«{warehouse_product.name}» تعریف نشده است."
                    )

                qty_before = float(stock.current_quantity or 0)

                if qty_before < total_required:
                    raise ValueError(
                        f"موجودی کافی نیست!\n"
                        f"ماده اولیه: {warehouse_product.name}\n"
                        f"موجودی فعلی: {qty_before:g}\n"
                        f"مقدار مورد نیاز: {total_required:g}"
                    )

                qty_after = qty_before - total_required

                stock.current_quantity = qty_after

                transaction = StockTransaction(
                    product_id=warehouse_product.id,
                    performed_by=performed_by_user,
                    transaction_type=TransactionType.STOCK_OUT,
                    quantity_changed=-total_required,
                    quantity_before=qty_before,
                    quantity_after=qty_after,
                    stock_out_reason=StockOutReason.SALE,
                    note=(
                        f"فروش {quantity} عدد "
                        f"{menu_item.name}"
                    ),
                )

                session.add(transaction)

                recipe_snapshot_lines.append(
                    f"{warehouse_product.name}: {total_required:g}"
                )

                print(
                    f"  کسر {total_required:g} از "
                    f"«{warehouse_product.name}» "
                    f"| موجودی جدید: {qty_after:g}"
                )

            # -----------------------------
            # 6. آماده‌سازی جزئیات آرشیو
            # -----------------------------

            archive_items_data.append({
                "menu_item_name": menu_item.name,
                "unit_price": unit_price,
                "quantity": quantity,
                "subtotal": item_subtotal,
                "recipe_snapshot_details": " | ".join(
                    recipe_snapshot_lines
                ),
            })

        # -----------------------------
        # 7. تولید شماره فاکتور
        # -----------------------------

        now_jalali = jdatetime.datetime.now()

        persian_date_str = now_jalali.strftime("%Y/%m/%d")
        persian_time_str = now_jalali.strftime("%H:%M:%S")

        factor_num = (
            f"FAC-{now_jalali.strftime('%Y%m%d%H%M%S')}-"
            f"{str(uuid.uuid4())[:4].upper()}"
        )

        # -----------------------------
        # 8. ثبت آرشیو فاکتور
        # -----------------------------

        order_archive = OrderArchive(
            factor_number=factor_num,
            total_price=grand_total,
            total_items_count=total_items_count,
            performed_by=performed_by_user,
            customer_id=customer_id,
            customer_name=customer_name_snapshot,
            is_paid=is_paid,
            persian_date=persian_date_str,
            persian_time=persian_time_str,
        )

        session.add(order_archive)

        session.flush()

       

        for item_data in archive_items_data:
            snapshot_item = OrderItemSnapshot(
                order_id=order_archive.id,
                menu_item_name=item_data["menu_item_name"],
                unit_price=item_data["unit_price"],
                quantity=item_data["quantity"],
                subtotal=item_data["subtotal"],
                recipe_snapshot_details=(
                    item_data["recipe_snapshot_details"]
                ),
            )

            session.add(snapshot_item)

        # -----------------------------
        # 10. ثبت نهایی تراکنش
        # -----------------------------

        session.commit()

        customer_info = (
            f"مشتری: {customer_name_snapshot}"
            if customer_name_snapshot
            else "مشتری: آزاد (مهمان)"
        )

        print(
            f"ثبت موفق فاکتور {factor_num} "
            f"| {customer_info} "
            f"| تعداد: {total_items_count} "
            f"| مبلغ: {grand_total:,.0f} تومان"
        )

        return {
            "success": True,
            "factor_number": factor_num,
            "total_price": grand_total,
            "total_items_count": total_items_count,
            "message": "سفارش با موفقیت ثبت شد.",
        }

    except Exception as error:
        session.rollback()

        print(
            f"خطا در ثبت سفارش و به‌روزرسانی انبار: {error}"
        )

        return {
            "success": False,
            "error": str(error),
        }

    finally:
        session.close()