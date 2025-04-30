from sqlalchemy import Column, String
from database import Base

class User(Base):
    __tablename__ = "users"
    email = Column(String(255), unique=True, index=True, nullable=False, primary_key=True)
    nome = Column(String(255), nullable=False)
    senha = Column(String(255), nullable=False)