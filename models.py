from sqlalchemy import Column, String, Integer, Float, Date, DateTime
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    email = Column(String(255), unique=True, index=True, nullable=False, primary_key=True)
    nome = Column(String(255), nullable=False)
    senha = Column(String(255), nullable=False)

class BovespaData(Base):
    __tablename__ = "bovespa_data"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True)
    open_value = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)