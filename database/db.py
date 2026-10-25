from pathlib import Path

from sqlalchemy import create_engine
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

    session_factory = _SESSION_FACTORY_CACHE[normalized_url]

    return session_factory()