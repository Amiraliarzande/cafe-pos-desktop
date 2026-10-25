from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from database.models.warehouse.unit_measurement import Base
from database.models.cafe.customer import Customer


class OrderArchive(Base):
    __tablename__ = 'order_archives'
    
    id = Column(Integer, primary_key=True)
    factor_number = Column(String(50), nullable=False, unique=True)  
    total_price = Column(Float, nullable=False, default=0.0)        
    performed_by = Column(String(100), nullable=True)                
    
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    customer = relationship("Customer")
    customer_name = Column(String(150), nullable=True)  
    
    total_items_count = Column(Integer, nullable=False, default=0)  
    is_paid = Column(Boolean, nullable=False, default=True)         

    persian_date = Column(String(20), nullable=False)                
    persian_time = Column(String(20), nullable=False)                
    
    created_at = Column(DateTime, default=datetime.utcnow)          

    items = relationship("OrderItemSnapshot", back_populates="order", cascade="all, delete-orphan")


class OrderItemSnapshot(Base):
    __tablename__ = 'order_item_snapshots'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('order_archives.id'), nullable=False)
    order = relationship("OrderArchive", back_populates="items")

    menu_item_name = Column(String(200), nullable=False)
    unit_price = Column(Float, nullable=False)    
    quantity = Column(Integer, nullable=False)     
    subtotal = Column(Float, nullable=False)       

    recipe_snapshot_details = Column(Text, nullable=False)