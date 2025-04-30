# scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict
from models import FinancialData  # Novo modelo que vamos criar
from sqlalchemy.orm import Session
import re
from typing import List


def scrape_currency_data(db: Session) -> List[FinancialData]:
    """Scraper que salva cada nova cotação como um registro independente"""
    url = "https://www.x-rates.com/table/?from=USD&amount=1"
    
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        link = soup.find('a', href=re.compile(r'from=USD&to=BRL'))
        if link:
            value = float(link.text.strip())
            new_record = FinancialData(
                currency_pair="USD_BRL",
                value=value
            )
            db.add(new_record)
            db.commit()
            return [new_record]
    
    except Exception as e:
        print(f"Erro no scraping: {e}")
    
    return []