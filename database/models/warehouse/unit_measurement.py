from sqlalchemy import Column, Integer, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DimensionUnit(Base):
    __tablename__ = 'dimension_units'
    id = Column(Integer, primary_key=True)
    meter = Column(Float, nullable=True)
    centimeter = Column(Float, nullable=True)
    inch = Column(Float, nullable=True)


class WeightUnit(Base):
    __tablename__ = 'weight_units'
    id = Column(Integer, primary_key=True)
    gram = Column(Float, nullable=True)
    kilogram = Column(Float, nullable=True)
    milligram = Column(Float, nullable=True)
    ton = Column(Float, nullable=True)


class VolumeUnit(Base):
    __tablename__ = 'volume_units'
    id = Column(Integer, primary_key=True)
    liter = Column(Float, nullable=True)
    milliliter = Column(Float, nullable=True)
    gallon = Column(Float, nullable=True)


class AreaUnit(Base):
    __tablename__ = 'area_units'
    id = Column(Integer, primary_key=True)
    square_meter = Column(Float, nullable=True)
    square_centimeter = Column(Float, nullable=True)


class CountUnit(Base):
    __tablename__ = 'count_units'
    id = Column(Integer, primary_key=True)
    quantity_per_unit = Column(Integer, nullable=True)