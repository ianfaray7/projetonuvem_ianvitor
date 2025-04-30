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
@app.get("/cotacoes/dolar")
def get_usd_rates(db: Session = Depends(get_db)):
    """Retorna as últimas 10 cotações do dólar (USD_BRL)"""
    try:
        # 1. Atualiza com dados mais recentes (opcional)
        scrape_currency_data(db)
        
        # 2. Busca as últimas 10 cotações do banco
        usd_rates = db.query(FinancialData)\
                     .filter(FinancialData.currency_pair == "USD_BRL")\
                     .order_by(FinancialData.last_updated.desc())\
                     .limit(10)\
                     .all()
        
        if not usd_rates:
            raise HTTPException(
                status_code=404,
                detail="Nenhuma cotação do dólar encontrada no banco de dados"
            )
        
        # 3. Formata a resposta
        return {
            "ultima_consulta": datetime.now().isoformat(),
            "cotacoes": [
                {
                    "valor": rate.value,
                    "data": rate.last_updated.isoformat()
                } for rate in usd_rates
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar a requisição: {str(e)}"
        )