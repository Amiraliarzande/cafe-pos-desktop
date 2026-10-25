from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from database.models.warehouse.unit_measurement import Base


class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=True) 
    
    created_at = Column(DateTime, default=datetime.utcnow)