from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# MySQL connection (local)
URL_DATABASE = "mysql+mysqlconnector://root:isfa2007@localhost:3306/cloud"
engine = create_engine(URL_DATABASE, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
engine.connect()