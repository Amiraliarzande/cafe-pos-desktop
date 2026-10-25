from database.db import init_db
from database.models.warehouse.product import ProductCategory, Product, UnitType
from database.models.warehouse.unit_measurement import WeightUnit, VolumeUnit
from database.models.warehouse.warehouse_process import InventoryStock
from database.models.cafe.menu import MenuCategory, MenuItem, RecipeItem

def run_menu_test():
    print("--- شروع تست مدل‌های منو و فرمول ساخت (BOM) ---")
    session = init_db("sqlite:///cafe.db")

    # ۱. ایجاد دسته‌بندی مواد اولیه در صورت نیاز
    cat_raw = session.query(ProductCategory).filter_by(name="مواد اولیه بار گرم").first()
    if not cat_raw:
        cat_raw = ProductCategory(name="مواد اولیه بار گرم")
        session.add(cat_raw)
        session.commit()

    # بررسی و ایجاد دان قهوه
    coffee_product = session.query(Product).filter_by(name="دان قهوه عربیکا").first()
    if not coffee_product:
        coffee_product = Product(name="دان قهوه عربیکا", category_id=cat_raw.id, unit_type=UnitType.WEIGHT)
        session.add(coffee_product)
        session.commit()
        session.add(InventoryStock(product_id=coffee_product.id, initial_quantity=2000.0, current_quantity=2000.0))
        session.commit()

    # بررسی و ایجاد شیر پاستوریزه
    milk_product = session.query(Product).filter_by(name="شیر پاستوریزه").first()
    if not milk_product:
        milk_product = Product(name="شیر پاستوریزه", category_id=cat_raw.id, unit_type=UnitType.VOLUME)
        session.add(milk_product)
        session.commit()
        session.add(InventoryStock(product_id=milk_product.id, initial_quantity=5000.0, current_quantity=5000.0))
        session.commit()

    # ۲. ایجاد دسته‌بندی منو
    menu_cat = session.query(MenuCategory).filter_by(name="نوشیدنی‌های گرم").first()
    if not menu_cat:
        menu_cat = MenuCategory(name="نوشیدنی‌های گرم")
        session.add(menu_cat)
        session.commit()

    # ۳. ایجاد محصول در منو (کافه لاته)
    print("3. در حال ثبت محصول 'کافه لاته' در منو...")
    latte = session.query(MenuItem).filter_by(name="کافه لاته").first()
    if not latte:
        latte = MenuItem(
            name="کافه لاته",
            sale_price=85000.0,
            category_id=menu_cat.id
        )
        session.add(latte)
        session.commit()

    # ۴. تعریف فرمول ساخت (BOM)
    print("4. در حال تعریف دستور پخت (فرمول ساخت) برای کافه لاته...")
    session.query(RecipeItem).filter_by(menu_item_id=latte.id).delete()
    session.commit()

    recipe_coffee = RecipeItem(
        menu_item_id=latte.id,
        warehouse_product_id=coffee_product.id,
        required_amount=18.0
    )
    recipe_milk = RecipeItem(
        menu_item_id=latte.id,
        warehouse_product_id=milk_product.id,
        required_amount=150.0
    )
    session.add_all([recipe_coffee, recipe_milk])
    session.commit()

    # ۵. تست خواندن اطلاعات
    print("\n--- نتیجه خواندن منو و فرمول ساخت از دیتابیس ---")
    retrieved_item = session.query(MenuItem).filter_by(name="کافه لاته").first()
    
    print(f"محصول منو: {retrieved_item.name}")
    print(f"دسته‌بندی: {retrieved_item.category.name}")
    print(f"قیمت فروش: {retrieved_item.sale_price} تومان")
    print("مواد اولیه مورد نیاز (دستور پخت):")
    for r in retrieved_item.recipe_items:
        print(f" - {r.warehouse_product.name}: {r.required_amount}")

    print("---------------------------------------------")
    print("✅ تست مدل‌های منو و فرمول ساخت با موفقیت انجام شد!")

if __name__ == "__main__":
    run_menu_test()
