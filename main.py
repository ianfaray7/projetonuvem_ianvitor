from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import Base, engine, SessionLocal
from models import User, FinancialData
from pydantic import BaseModel
from scraper import scrape_currency_data
from typing import List
from datetime import datetime, date

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Usuario(BaseModel):
    nome: str
    email: str
    senha: str

class Login(BaseModel):
    email: str
    senha: str


app = FastAPI()

@app.post("/registrar")
def registrar(user: Usuario, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=409, detail="Email já registrado")

    hashed_password = hash_password(user.senha)
    new_user = User(nome=user.nome, email=user.email, senha=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Usuário registrado com sucesso!"}

@app.post("/login")
def logar(user: Login, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    
    if db_user is None:
        raise HTTPException(status_code=404, detail="Email não encontrado")

    if not pwd_context.verify(user.senha, db_user.senha):
        raise HTTPException(status_code=401, detail="Senha incorreta")    
    return {"message": "Login realizado com sucesso"}

@app.get("/consultar")
def get_rates(db: Session = Depends(get_db)):
    """Endpoint que retorna as últimas cotações"""
    try:
        new_data = scrape_currency_data(db)
        
        if not new_data:
            db_data = db.query(FinancialData).order_by(FinancialData.last_updated.desc()).limit(2).all()
            if not db_data:
                raise HTTPException(status_code=404, detail="Nenhum dado disponível")
            return {"data": [{"pair": d.currency_pair, "value": d.value} for d in db_data]}
        
        for data in new_data:
            # Verifica se já existe registro para este par de moedas
            existing = db.query(FinancialData)\
                       .filter(FinancialData.currency_pair == data.currency_pair)\
                       .order_by(FinancialData.last_updated.desc())\
                       .first()
            
            if existing:
                existing.value = data.value
            else:
                db.add(data)
        
        db.commit()
        
        # Retorna os dados mais recentes
        latest = db.query(FinancialData)\
                 .order_by(FinancialData.last_updated.desc())\
                 .limit(2)\
                 .all()
        
        return {"data": [{"pair": d.currency_pair, "value": d.value} for d in latest]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))