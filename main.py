from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import Base, engine, SessionLocal
from models import User, BovespaData
from pydantic import BaseModel
from .scraper import scrape_bovespa_data
from typing import List
from datetime import datetime

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

class BovespaResponse(BaseModel):
    Date: str
    Open: float
    High: float
    Low: float
    Close: float
    Volume: int
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

@app.get("/consultar", response_model=List[BovespaResponse])
def consultar_bovespa(db: Session = Depends(get_db)):
    try:
        # Obtém dados via scraping
        scraped_data = scrape_bovespa_data()
        
        # Converte os dados para o formato do modelo SQLAlchemy e salva no banco
        for data in scraped_data:
            # Verifica se a data já existe no banco
            existing_data = db.query(BovespaData).filter(
                BovespaData.date == datetime.strptime(data.Date, "%Y-%m-%d").date()
            ).first()
            
            if not existing_data:
                # Se não existir, cria um novo registro
                db_data = BovespaData(
                    date=datetime.strptime(data.Date, "%Y-%m-%d").date(),
                    open_value=data.Open,
                    high=data.High,
                    low=data.Low,
                    close=data.Close,
                    volume=data.Volume
                )
                db.add(db_data)
        
        db.commit()
        
        # Retorna os dados mais recentes do banco (últimos 10 dias)
        db_data = db.query(BovespaData).order_by(BovespaData.date.desc()).limit(10).all()
        
        return [
            BovespaResponse(
                Date=data.date.strftime("%Y-%m-%d"),
                Open=data.open_value,
                High=data.high,
                Low=data.low,
                Close=data.close,
                Volume=data.volume
            ) for data in db_data
        ]
        
    except Exception as e:
        # Em caso de erro, tenta retornar dados do banco
        db_data = db.query(BovespaData).order_by(BovespaData.date.desc()).limit(10).all()
        if db_data:
            return [
                BovespaResponse(
                    Date=data.date.strftime("%Y-%m-%d"),
                    Open=data.open_value,
                    High=data.high,
                    Low=data.low,
                    Close=data.close,
                    Volume=data.volume
                ) for data in db_data
            ]
        
        # Se não houver dados no banco, retorna erro
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível obter dados da Bovespa"
        )