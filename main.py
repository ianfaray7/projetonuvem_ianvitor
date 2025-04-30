from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from database import SessionLocal, engine, Base
from models import User, FinancialData
from scraper import scrape_currency_data
from config import settings
import os

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str

class UsuarioLogin(BaseModel):
    email: str
    senha: str

class CotacaoResponse(BaseModel):
    valor: float
    data: str

# Utilitários
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.senha):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

app = FastAPI()

@app.post("/registrar", response_model=Token)   
def registrar(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == usuario.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado"
        )
    
    hashed_password = get_password_hash(usuario.senha)
    new_user = User(
        email=usuario.email,
        nome=usuario.nome,
        senha=hashed_password
    )
    db.add(new_user)
    db.commit()
    
    access_token = create_access_token(
        data={"sub": usuario.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(
    user_data: UsuarioLogin,  # Agora aceita JSON
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, user_data.email, user_data.senha)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/consultar")
def get_usd_rates(
    current_user: User = Depends(get_current_user),  # <<-- Adicionei esta dependência
    db: Session = Depends(get_db)
):
    """Retorna as últimas 10 cotações do dólar (USD_BRL) - Requer autenticação"""
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
                detail="Nenhuma cotação do dólar encontrada"
            )
        
        return {
            "ultima_consulta": datetime.now().isoformat(),
            "cotacoes": [
                {
                    "valor": rate.value,
                    "data": rate.last_updated.isoformat()
                } for rate in usd_rates
            ]
        }
        
    except HTTPException:
        # Já trata erros conhecidos (como 404)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )