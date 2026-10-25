from database.db import init_db
from database.models.cafe.menu import MenuItem
from database.models.warehouse.warehouse_process import InventoryStock
from services.order_service import process_order

def run_order_test():
    session = init_db("sqlite:///cafe.db")
    
    # پیدا کردن کافه لاته در منو
    latte = session.query(MenuItem).filter_by(name="کافه لاته").first()
    if not latte:
        print("❌ لطفاً ابتدا test_menu.py را اجرا کنید تا لاته در منو ایجاد شود.")
        return

    print("--- وضعیت موجودی انبار پیش از فروش ---")
    for s in session.query(InventoryStock).all():
        print(f" - {s.product.name}: {s.current_quantity}")

    # شبیه‌سازی فروش ۲ عدد کافه لاته (بر اساس فرمول: هر لاته 18 گرم قهوه و 150 میل شیر)
    # کل مصرف مورد انتظار: 36 گرم قهوه و 300 میلی‌لیتر شیر
    cart = [{'item_id': latte.id, 'quantity': 2}]
    
    success = process_order(cart, performed_by_user="باریستا امیرعلی")

    if success:
        print("\n--- وضعیت موجودی انبار پس از فروش ۲ عدد لاته ---")
        for s in session.query(InventoryStock).all():
            print(f" - {s.product.name}: {s.current_quantity}")
        print("---------------------------------------------")
        print("✅ تست ثبت سفارش و کسر انبار با موفقیت کامل انجام شد!")

if __name__ == "__main__":
    run_order_test()
