import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List
import re
from fake_useragent import UserAgent

from .models import BovespaData

def scrape_bovespa_data() -> List[BovespaData]:
    """
    Coleta dados históricos do IBOVESPA do Investing.com
    Retorna os últimos 10 dias de dados
    """
    url = "https://br.investing.com/indices/bovespa-historical-data"
    
    # Configurar headers para parecer um navegador real
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        # 1. Fazer requisição HTTP
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 2. Parsear o HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 3. Encontrar a tabela de dados históricos
        table = soup.find('table', {'class': 'common-table medium js-table'})
        
        if not table:
            raise ValueError("Tabela de dados não encontrada")
        
        # 4. Extrair linhas da tabela (ignorando cabeçalho)
        rows = table.find_all('tr')[1:11]  # Pega as 10 primeiras linhas de dados
        
        data = []
        
        for row in rows:
            cols = row.find_all('td')
            
            if len(cols) >= 5:  # Garante que temos todas as colunas necessárias
                # Processar e converter os dados
                date_str = cols[0].get_text(strip=True)
                date = datetime.strptime(date_str, '%d.%m.%Y').strftime('%Y-%m-%d')
                
                # Remover pontos de milhar e substituir vírgula decimal
                def clean_number(text):
                    return float(re.sub(r'\.', '', text).replace(',', '.'))
                
                open_ = clean_number(cols[1].get_text(strip=True))
                high = clean_number(cols[2].get_text(strip=True))
                low = clean_number(cols[3].get_text(strip=True))
                close = clean_number(cols[4].get_text(strip=True))
                volume = int(clean_number(cols[5].get_text(strip=True))) if len(cols) >= 6 else 0
                
                data.append(BovespaData(
                    Date=date,
                    Open=open_,
                    High=high,
                    Low=low,
                    Close=close,
                    Volume=volume
                ))
        
        return data
    
    except Exception as e:
        # Em caso de erro, retorna dados mockados como fallback
        print(f"Erro no scraping: {e}")
        return mock_bovespa_data()

def mock_bovespa_data() -> List[BovespaData]:
    """Fallback com dados mockados quando o scraping falha"""
    base_date = datetime.now()
    data = []
    
    for i in range(10):
        date = base_date - timedelta(days=i)
        data.append(BovespaData(
            Date=date.strftime("%Y-%m-%d"),
            Open=round(130000 + (i * 500) + (i % 3 * 300), 2),
            High=round(131000 + (i * 600) + (i % 2 * 400), 2),
            Low=round(129000 + (i * 400) + (i % 5 * 200), 2),
            Close=round(130500 + (i * 550) + (i % 3 * 350), 2),
            Volume=int(7000000 + (i * 100000))
        ))
    
    return data