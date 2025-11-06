"""
Módulo para buscar dados básicos de mercado (históricos e fundamentais).
"""
import yfinance as yf
import pandas as pd
from typing import Dict, Any

from app.core.market.ticker_utils import format_ticker


def get_historical_data(ticker: str, period: str = "1y") -> list[dict]:
    """
    Busca dados históricos de um ticker, formatando-o se for da B3.
    """
    formatted_ticker = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(formatted_ticker)
        
        data: pd.DataFrame = stock.history(period=period)
        
        if data.empty:
            return []

        data.reset_index(inplace=True)
        data.rename(columns={
            'Date': 'date', 
            'Open': 'open', 
            'High': 'high', 
            'Low': 'low', 
            'Close': 'close', 
            'Volume': 'volume', 
            'Dividends': 'dividends', 
            'Stock Splits': 'stock_splits'
        }, inplace=True)
        
        data['date'] = data['date'].dt.strftime('%Y-%m-%d')
        
        data = data[['date', 'open', 'high', 'low', 'close', 'volume']]

        return data.to_dict(orient='records')
        
    except Exception as e:
        print(f"Erro ao buscar dados do ticker {formatted_ticker}: {e}")
        raise


def get_company_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Busca dados fundamentalistas de uma empresa usando yfinance.
    Retorna: P/E, P/VP, Dividend Yield, Beta, Setor, Indústria, Market Cap.
    """
    formatted_ticker = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(formatted_ticker)
        info = stock.info
        
        # Extrair dados, tratando valores None ou indisponíveis
        fundamentals = {
            'pe_ratio': info.get('trailingPE') or info.get('forwardPE'),
            'pb_ratio': info.get('priceToBook'),
            'dividend_yield': info.get('dividendYield'),
            'beta': info.get('beta'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'market_cap': info.get('marketCap')
        }
        
        # Converter para None se não existir
        for key, value in fundamentals.items():
            if value is None or (isinstance(value, float) and (pd.isna(value) or value == 0)):
                fundamentals[key] = None
        
        return fundamentals
        
    except Exception as e:
        print(f"Erro ao buscar fundamentos do ticker {formatted_ticker}: {e}")
        raise

