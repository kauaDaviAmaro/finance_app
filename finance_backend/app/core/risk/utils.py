"""
Utilitários compartilhados para cálculos de risco.
"""
import yfinance as yf
import pandas as pd
from typing import Optional

from app.core.market.ticker_utils import format_ticker
from app.core.redis_cache import get_cached_dataframe, set_cached_dataframe


def _fetch_historical_data_from_yfinance(ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """
    Busca dados históricos diretamente do yfinance (sem cache).
    """
    try:
        formatted_ticker = format_ticker(ticker)
        stock = yf.Ticker(formatted_ticker)
        data = stock.history(period=period)
        
        if data.empty:
            return None
        
        return data
    except Exception as e:
        print(f"Erro ao buscar dados históricos para {ticker}: {e}")
        return None


def get_historical_returns_df(ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """
    Busca dados históricos e calcula retornos diários.
    Usa cache Redis para evitar múltiplas requisições ao yfinance.
    
    Returns:
        DataFrame com colunas 'date' e 'returns', ou None se não houver dados
    """
    formatted_ticker = format_ticker(ticker)
    cache_key = f"yfinance:historical:{formatted_ticker}:{period}"
    
    # 1. TENTA BUSCAR NO CACHE
    data = get_cached_dataframe(cache_key)
    
    # 2. NÃO ACHOU NO CACHE? BUSCA NA API (E SALVA)
    if data is None or data.empty:
        print(f"📡 CACHE MISS: Retornos do ticker {formatted_ticker} (period={period}). Buscando no yfinance...")
        data = _fetch_historical_data_from_yfinance(ticker, period)
        
        if data is not None and not data.empty:
            set_cached_dataframe(cache_key, data)
    
    if data is None or data.empty or len(data) < 2:
        return None
    
    data = data.copy()
    data.reset_index(inplace=True)
    data['returns'] = data['Close'].pct_change().dropna()
    data = data[['Date', 'Close', 'returns']].dropna()
    
    if len(data) < 2:
        return None
    
    return data


def get_benchmark_returns(benchmark: str = "^BVSP", period: str = "1y") -> Optional[pd.Series]:
    """
    Busca retornos do benchmark (IBOVESPA por padrão).
    Usa cache Redis para evitar múltiplas requisições ao yfinance.
    
    Returns:
        Series com retornos diários, ou None se não houver dados
    """
    cache_key = f"yfinance:historical:{benchmark}:{period}"
    
    # 1. TENTA BUSCAR NO CACHE
    data = get_cached_dataframe(cache_key)
    
    # 2. NÃO ACHOU NO CACHE? BUSCA NA API (E SALVA)
    if data is None or data.empty:
        print(f"📡 CACHE MISS: Benchmark {benchmark} (period={period}). Buscando no yfinance...")
        data = _fetch_historical_data_from_yfinance(benchmark, period)
        
        if data is not None and not data.empty:
            set_cached_dataframe(cache_key, data)
    
    if data is None or data.empty or len(data) < 2:
        return None
    
    returns = data['Close'].pct_change().dropna()
    return returns

