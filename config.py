from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Scraper
    SCRAPER_USER_AGENT: str = "Mozilla/5.0"
    SCRAPER_TIMEOUT: int = 10
    SCRAPER_URL: str = "https://www.x-rates.com/table/?from=USD&amount=1"
    
    # App
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()