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
    """Scraper que retorna objetos FinancialData prontos para o banco"""
    url = "https://www.x-rates.com/table/?from=USD&amount=1"
    results = []
    
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Mapeamento de pares de moedas que queremos capturar
        currency_pairs = {
            'USD_BRL': {'from': 'USD', 'to': 'BRL'},
            'EUR_BRL': {'from': 'EUR', 'to': 'BRL'}
        }

        for pair_id, currencies in currency_pairs.items():
            link = soup.find('a', href=re.compile(f"from={currencies['from']}&to={currencies['to']}"))
            if link:
                value = float(link.text.strip())
                results.append(
                    FinancialData(
                        currency_pair=pair_id,
                        value=value
                    )
                )

    except Exception as e:
        print(f"Erro no scraping: {e}")
    
    return results