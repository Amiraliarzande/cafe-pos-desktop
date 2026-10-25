import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Enum as SQLEnum, Text, String
from sqlalchemy.orm import relationship
from database.models.warehouse.unit_measurement import Base
from database.models.warehouse.product import Product


class InventoryStock(Base):
    __tablename__ = 'inventory_stocks'
    id = Column(Integer, primary_key=True)
    
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, unique=True)
    product = relationship("Product", back_populates="stocks")

    initial_quantity = Column(Float, default=0.0)  
    current_quantity = Column(Float, default=0.0)  

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TransactionType(enum.Enum):
    STOCK_IN = "stock_in"    
    STOCK_OUT = "stock_out"  
    INITIAL = "initial"      


class StockOutReason(enum.Enum):
    SALE = "sale"         
    DAMAGE = "damage"     
    TRANSFER = "transfer"  
    OTHER = "other"        


class StockTransaction(Base):
    __tablename__ = 'stock_transactions'
    id = Column(Integer, primary_key=True)

    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product = relationship("Product", back_populates="transactions")

    performed_by = Column(String(100), nullable=True) 

    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    quantity_changed = Column(Float, nullable=False)
    quantity_before = Column(Float, nullable=False)
    quantity_after = Column(Float, nullable=False)

    stock_out_reason = Column(SQLEnum(StockOutReason), nullable=True)
    note = Column(Text, nullable=True)

    transaction_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)