from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from database.models.warehouse.unit_measurement import (
    Base,
    DimensionUnit,
    WeightUnit,
    VolumeUnit,
    AreaUnit,
    CountUnit,
)

from database.models.warehouse.product import (
    ProductCategory,
    Product,
    UnitType,
)

from database.models.warehouse.warehouse_process import (
    InventoryStock,
    StockTransaction,
    TransactionType,
    StockOutReason,
)

from database.models.cafe.menu import (
    MenuCategory,
    MenuItem,
    RecipeItem,
)

from database.models.cafe.order_archive import (
    OrderArchive,
    OrderItemSnapshot,
)

from database.models.cafe.customer import Customer


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_ROOT / "cafe.db"

_ENGINE_CACHE = {}
_SESSION_FACTORY_CACHE = {}


def _normalize_database_url(db_url=None):

    if db_url is None:
        db_url = f"sqlite:///{DATABASE_PATH.as_posix()}"

    if not db_url.startswith("sqlite:///"):
        return db_url

    if db_url.startswith("sqlite:////"):
        return db_url

    relative_path = db_url[len("sqlite:///"):]

    absolute_path = (PROJECT_ROOT / relative_path).resolve()

    return f"sqlite:///{absolute_path.as_posix()}"


def _ensure_schema_updates(engine):
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    with engine.connect() as conn:
        # ۱. اضافه کردن description به جدول menu_items (حل مشکل اصلی)
        if "menu_items" in existing_tables:
            menu_cols = [c["name"] for c in inspector.get_columns("menu_items")]
            if "description" not in menu_cols:
                conn.execute(text("ALTER TABLE menu_items ADD COLUMN description VARCHAR(500);"))
                conn.commit()

        # ۲. بررسی جدول recipe_items در صورت نیاز
        if "recipe_items" in existing_tables:
            recipe_cols = [c["name"] for c in inspector.get_columns("recipe_items")]
            if "description" not in recipe_cols:
                conn.execute(text("ALTER TABLE recipe_items ADD COLUMN description VARCHAR(500);"))
                conn.commit()


def init_db(db_url=None):

    normalized_url = _normalize_database_url(db_url)

    if normalized_url not in _ENGINE_CACHE:
        engine = create_engine(
            normalized_url,
            echo=False,
            connect_args=(
                {"check_same_thread": False}
                if normalized_url.startswith("sqlite:")
                else {}
            ),
        )

        _ENGINE_CACHE[normalized_url] = engine

        _SESSION_FACTORY_CACHE[normalized_url] = sessionmaker(
            bind=engine,
            autoflush=True,
            expire_on_commit=False,
        )

        Base.metadata.create_all(engine)

        _ensure_schema_updates(engine)

    session_factory = _SESSION_FACTORY_CACHE[normalized_url]

    return session_factory()
