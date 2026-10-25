from database.db import init_db
from database.models.warehouse.product import ProductCategory, Product, UnitType
from database.models.warehouse.warehouse_process import InventoryStock, StockTransaction, TransactionType, StockOutReason
from database.models.cafe.menu import MenuCategory, MenuItem, RecipeItem
from database.models.cafe.order_archive import OrderArchive
from services.order_service import process_order

def run_full_test():
    # بازنشانی دیتابیس برای تست تمیز
    import os
    if os.path.exists("cafe.db"):
        os.remove("cafe.db")

    print("--- ۱. اتصال به دیتابیس و راه‌اندازی اولیه ---")
    session = init_db("sqlite:///cafe.db")

    # ایجاد دسته‌بندی انبار
    cat_warehouse = ProductCategory(name="انبار مواد اولیه کافه")
    session.add(cat_warehouse)
    session.commit()

    # ایجاد محصولات انبار
    p_coffee = Product(name="دان قهوه عربیکا", category_id=cat_warehouse.id, unit_type=UnitType.WEIGHT)
    p_milk = Product(name="شیر پاستوریزه", category_id=cat_warehouse.id, unit_type=UnitType.VOLUME)
    p_cocoa = Product(name="پودر کاکائو", category_id=cat_warehouse.id, unit_type=UnitType.WEIGHT)
    session.add_all([p_coffee, p_milk, p_cocoa])
    session.commit()

    # ثبت موجودی اولیه انبار
    stocks = [
        InventoryStock(product_id=p_coffee.id, initial_quantity=3000.0, current_quantity=3000.0), # 3000 گرم قهوه
        InventoryStock(product_id=p_milk.id, initial_quantity=10000.0, current_quantity=10000.0),  # 10000 میل شیر
        InventoryStock(product_id=p_cocoa.id, initial_quantity=1000.0, current_quantity=1000.0)    # 1000 گرم کاکائو
    ]
    session.add_all(stocks)
    session.commit()

    print("--- ۲. تست ثبت خروج انبار به دلیل ضایعات (Damage) ---")
    # مثلاً 200 گرم شیر فاسد شده و دور ریخته شده است
    milk_stock = session.query(InventoryStock).filter_by(product_id=p_milk.id).first()
    q_before = milk_stock.current_quantity
    q_after = q_before - 200.0
    milk_stock.current_quantity = q_after

    waste_tx = StockTransaction(
        product_id=p_milk.id,
        performed_by="انباردار",
        transaction_type=TransactionType.STOCK_OUT,
        quantity_changed=-200.0,
        quantity_before=q_before,
        quantity_after=q_after,
        stock_out_reason=StockOutReason.DAMAGE,
        note="فساد شیر و خروج به عنوان ضایعات"
    )
    session.add(waste_tx)
    session.commit()
    print(f"✅ ضایعات ثبت شد. موجودی جدید شیر: {milk_stock.current_quantity} میلی‌لیتر")

    print("\n--- ۳. ایجاد ۳ آیتم در منو و فرمول ساخت (BOM) ---")
    menu_cat = MenuCategory(name="نوشیدنی‌ها")
    session.add(menu_cat)
    session.commit()

    # آیتم اول: کافه لاته
    latte = MenuItem(name="کافه لاته", sale_price=90000.0, category_id=menu_cat.id)
    # آیتم دوم: کاپوچینو
    cappuccino = MenuItem(name="کاپوچینو", sale_price=85000.0, category_id=menu_cat.id)
    # آیتم سوم: هات چاکلت
    hot_chocolate = MenuItem(name="هات چاکلت", sale_price=95000.0, category_id=menu_cat.id)
    session.add_all([latte, cappuccino, hot_chocolate])
    session.commit()

    # تعریف فرمول ساخت (BOM) برای محصولات منو
    recipes = [
        # لاته: 18 گرم قهوه + 150 میل شیر
        RecipeItem(menu_item_id=latte.id, warehouse_product_id=p_coffee.id, required_amount=18.0),
        RecipeItem(menu_item_id=latte.id, warehouse_product_id=p_milk.id, required_amount=150.0),
        
        # کاپوچینو: 16 گرم قهوه + 120 میل شیر
        RecipeItem(menu_item_id=cappuccino.id, warehouse_product_id=p_coffee.id, required_amount=16.0),
        RecipeItem(menu_item_id=cappuccino.id, warehouse_product_id=p_milk.id, required_amount=120.0),
        
        # هات چاکلت: 40 گرم پودر کاکائو + 200 میل شیر
        RecipeItem(menu_item_id=hot_chocolate.id, warehouse_product_id=p_cocoa.id, required_amount=40.0),
        RecipeItem(menu_item_id=hot_chocolate.id, warehouse_product_id=p_milk.id, required_amount=200.0),
    ]
    session.add_all(recipes)
    session.commit()
    print("✅ ۳ آیتم منو به همراه فرمول ساخت (BOM) ایجاد شدند.")

    print("\n--- ۴. ثبت سفارش با استفاده از order_service.py ---")
    # شبیه‌سازی خرید مشتری: ۲ عدد لاته، ۱ عدد کاپوچینو، ۱ عدد هات چاکلت
    cart = [
        {'item_id': latte.id, 'quantity': 2},
        {'item_id': cappuccino.id, 'quantity': 1},
        {'item_id': hot_chocolate.id, 'quantity': 1}
    ]

    success = process_order(cart, performed_by_user="باریستا سارا")

    if success:
        print("\n--- ۵. بررسی اطلاعات آرشیو و بایگانی فاکتور ---")
        archive_record = session.query(OrderArchive).order_by(OrderArchive.id.desc()).first()
        
        print(f"شماره فاکتور: {archive_record.factor_number}")
        print(f"صادرکننده: {archive_record.performed_by}")
        print(f"تاریخ شمسی: {archive_record.persian_date} | ساعت: {archive_record.persian_time}")
        print(f"مجموع کل مبلغ فاکتور: {archive_record.total_price:,.0f} تومان")
        print("اقلام فاکتور و اسنپ‌شات‌ها:")
        for item in archive_record.items:
            print(f" - {item.menu_item_name} | تعداد: {item.quantity} | فی: {item.unit_price:,.0f} | زیرجمع: {item.subtotal:,.0f}")
            print(f"   [اسنپ‌شات مصرف انبار]: {item.recipe_snapshot_details}")

        print("\n--- ۶. وضعیت نهایی موجودی انبار ---")
        for s in session.query(InventoryStock).all():
            print(f" - {s.product.name}: {s.current_quantity}")

        print("\n=============================================")
        print("🎉 تمام تست‌های انبار، ضایعات، منو، سفارش و آرشیو با موفقیت پاس شدند!")
        print("=============================================")

if __name__ == "__main__":
    run_full_test()
