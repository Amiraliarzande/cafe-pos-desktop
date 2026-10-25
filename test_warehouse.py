from database.db import init_db
from database.models.warehouse.product import ProductCategory, Product, UnitType
from database.models.warehouse.unit_measurement import WeightUnit
from database.models.warehouse.warehouse_process import InventoryStock, StockTransaction, TransactionType

def run_test():
    print("--- در حال اتصال به دیتابیس و ساخت جدول‌ها ---")
    session = init_db("sqlite:///cafe.db")

    print("1. در حال ثبت واحد وزن...")
    gram_unit = WeightUnit(gram=1.0, kilogram=0.001)
    session.add(gram_unit)
    session.commit()

    print("2. در حال ثبت دسته‌بندی انبار...")
    category = ProductCategory(name="مواد اولیه بار گرم")
    session.add(category)
    session.commit()

    print("3. در حال ثبت کالای دان قهوه...")
    coffee = Product(
        name="دان قهوه عربیکا",
        category_id=category.id,
        unit_type=UnitType.WEIGHT,
        weight_unit_id=gram_unit.id
    )
    session.add(coffee)
    session.commit()

    print("4. در حال ثبت موجودی اول دوره (1000 گرم)...")
    stock = InventoryStock(
        product_id=coffee.id,
        initial_quantity=1000.0,
        current_quantity=1000.0
    )
    session.add(stock)
    
    tx = StockTransaction(
        product_id=coffee.id,
        performed_by="امیرعلی",
        transaction_type=TransactionType.INITIAL,
        quantity_changed=1000.0,
        quantity_before=0.0,
        quantity_after=1000.0,
        note="موجودی اول دوره انبار کافه"
    )
    session.add(tx)
    session.commit()

    print("\n--- نتیجه تست و خواندن اطلاعات از دیتابیس ---")
    retrieved_product = session.query(Product).filter_by(name="دان قهوه عربیکا").first()
    retrieved_stock = session.query(InventoryStock).filter_by(product_id=retrieved_product.id).first()
    
    print(f"کالا: {retrieved_product.name}")
    print(f"دسته‌بندی: {retrieved_product.category.name}")
    print(f"موجودی جاری انبار: {retrieved_stock.current_quantity} گرم")
    print("---------------------------------------------")
    print("✅ تست با موفقیت انجام شد و تمام مدل‌ها درست کار می‌کنند!")

if __name__ == "__main__":
    run_test()
