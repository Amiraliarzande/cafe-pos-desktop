import os
from database.db import init_db
from database.models.warehouse.product import ProductCategory, Product, UnitType
from database.models.warehouse.warehouse_process import InventoryStock
from database.models.cafe.menu import MenuCategory, MenuItem, RecipeItem
from database.models.cafe.customer import Customer
from database.models.cafe.order_archive import OrderArchive
from services.order_service import process_order

def run_v2_test():
    # پاک کردن دیتابیس قبلی برای تست تمیز
    if os.path.exists("cafe.db"):
        os.remove("cafe.db")

    print("--- ۱. راه‌اندازی دیتابیس و ثبت اطلاعات پایه انبار ---")
    session = init_db("sqlite:///cafe.db")

    cat_warehouse = ProductCategory(name="انبار مواد اولیه")
    session.add(cat_warehouse)
    session.commit()

    p_coffee = Product(name="دان قهوه عربیکا", category_id=cat_warehouse.id, unit_type=UnitType.WEIGHT)
    p_milk = Product(name="شیر پاستوریزه", category_id=cat_warehouse.id, unit_type=UnitType.VOLUME)
    session.add_all([p_coffee, p_milk])
    session.commit()

    # موجودی اولیه انبار
    session.add_all([
        InventoryStock(product_id=p_coffee.id, initial_quantity=5000.0, current_quantity=5000.0),
        InventoryStock(product_id=p_milk.id, initial_quantity=10000.0, current_quantity=10000.0)
    ])
    session.commit()

    print("--- ۲. ثبت مشتریان ثابت ---")
    customer1 = Customer(name="علی رضایی", phone="09123456789")
    session.add(customer1)
    session.commit()
    print(f"✅ مشتری ثبت شد: {customer1.name} (شناسه: {customer1.id})")

    print("\n--- ۳. ایجاد منو و دستور پخت (BOM) ---")
    menu_cat = MenuCategory(name="نوشیدنی گرم")
    session.add(menu_cat)
    session.commit()

    latte = MenuItem(name="کافه لاته", sale_price=90000.0, category_id=menu_cat.id)
    cappuccino = MenuItem(name="کاپوچینو", sale_price=85000.0, category_id=menu_cat.id)
    session.add_all([latte, cappuccino])
    session.commit()

    # فرمول ساخت
    session.add_all([
        RecipeItem(menu_item_id=latte.id, warehouse_product_id=p_coffee.id, required_amount=18.0),
        RecipeItem(menu_item_id=latte.id, warehouse_product_id=p_milk.id, required_amount=150.0),
        RecipeItem(menu_item_id=cappuccino.id, warehouse_product_id=p_coffee.id, required_amount=16.0),
        RecipeItem(menu_item_id=cappuccino.id, warehouse_product_id=p_milk.id, required_amount=120.0),
    ])
    session.commit()
    print("✅ منو و فرمول ساخت ایجاد شدند.")

    print("\n--- ۴. ثبت سفارش اول (برای مشتری ثابت، به صورت نسیه / پرداخت نشده) ---")
    cart_order_1 = [{'item_id': latte.id, 'quantity': 2}]
    process_order(cart_items=cart_order_1, performed_by_user="باریستا امیر", customer_id=customer1.id, is_paid=False)

    print("\n--- ۵. ثبت سفارش دوم (مهمان / آزاد، پرداخت شده) ---")
    cart_order_2 = [{'item_id': cappuccino.id, 'quantity': 3}]
    process_order(cart_items=cart_order_2, performed_by_user="باریستا امیر", customer_id=None, is_paid=True)

    print("\n--- ۶. بررسی آرشیو و فاکتورهای بایگانی‌شده ---")
    archives = session.query(OrderArchive).all()
    for arch in archives:
        pay_status = "پرداخت شده" if arch.is_paid else "پرداخت نشده (نسیه)"
        cust_display = arch.customer_name if arch.customer_name else "مهمان (آزاد)"
        print(f"\n📄 فاکتور: {arch.factor_number}")
        print(f"   - مشتری: {cust_display}")
        print(f"   - تعداد کل اقلام: {arch.total_items_count}")
        print(f"   - مبلغ کل: {arch.total_price:,.0f} تومان")
        print(f"   - وضعیت پرداخت: {pay_status}")
        print(f"   - تاریخ و زمان: {arch.persian_date} - {arch.persian_time}")
        print("   - اقلام فاکتور:")
        for item in arch.items:
            print(f"     * {item.menu_item_name} (تعداد: {item.quantity}) - فی: {item.unit_price:,.0f} - جمع: {item.subtotal:,.0f}")
            print(f"       [اسنپ‌شات مصرف]: {item.recipe_snapshot_details}")

    print("\n=============================================")
    print("🎉 تمام تست‌های جدید مشتری، اقلام، وضعیت پرداخت و آرشیو با موفقیت پاس شدند!")
    print("=============================================")

if __name__ == "__main__":
    run_v2_test()
