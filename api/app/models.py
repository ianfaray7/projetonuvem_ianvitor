# models.py
from sqlalchemy import Column, String, Float, DateTime, Integer
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    email = Column(String(255), primary_key=True)
    nome = Column(String(255))
    senha = Column(String(255))

class FinancialData(Base):
    __tablename__ = "financial_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True) 
    currency_pair = Column(String(10), nullable=False) 
    value = Column(Float, nullable=False)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)