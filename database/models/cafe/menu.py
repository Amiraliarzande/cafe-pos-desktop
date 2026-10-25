from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.models.warehouse.unit_measurement import Base
from database.models.warehouse.product import Product


class MenuCategory(Base):
    __tablename__ = 'menu_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    items = relationship("MenuItem", back_populates="category")


class MenuItem(Base):
    __tablename__ = 'menu_items'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    sale_price = Column(Float, nullable=False)
    image_path = Column(String(500), nullable=True)
    
    category_id = Column(Integer, ForeignKey('menu_categories.id'), nullable=True)
    category = relationship("MenuCategory", back_populates="items")

    recipe_items = relationship("RecipeItem", back_populates="menu_item", cascade="all, delete-orphan")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecipeItem(Base):
    __tablename__ = 'recipe_items'
    
    id = Column(Integer, primary_key=True)
    
    menu_item_id = Column(Integer, ForeignKey('menu_items.id'), nullable=False)
    menu_item = relationship("MenuItem", back_populates="recipe_items")

    warehouse_product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    warehouse_product = relationship("Product")

    required_amount = Column(Float, nullable=False)