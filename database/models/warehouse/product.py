import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.models.warehouse.unit_measurement import Base


class UnitType(enum.Enum):
    DIMENSION = "dimension" 
    WEIGHT = "weight"        
    VOLUME = "volume"        
    AREA = "area"            
    COUNT = "count"       


class ProductCategory(Base):
    __tablename__ = 'product_categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    
    category_id = Column(Integer, ForeignKey('product_categories.id'), nullable=True)
    category = relationship("ProductCategory", back_populates="products")

    unit_type = Column(SQLEnum(UnitType), nullable=True)

    dimension_unit_id = Column(Integer, ForeignKey('dimension_units.id'), nullable=True)
    weight_unit_id = Column(Integer, ForeignKey('weight_units.id'), nullable=True)
    volume_unit_id = Column(Integer, ForeignKey('volume_units.id'), nullable=True)
    area_unit_id = Column(Integer, ForeignKey('area_units.id'), nullable=True)
    count_unit_id = Column(Integer, ForeignKey('count_units.id'), nullable=True)

    dimension_unit = relationship("DimensionUnit")
    weight_unit = relationship("WeightUnit")
    volume_unit = relationship("VolumeUnit")
    area_unit = relationship("AreaUnit")
    count_unit = relationship("CountUnit")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stocks = relationship("InventoryStock", back_populates="product", cascade="all, delete-orphan")
    transactions = relationship("StockTransaction", back_populates="product")