"""
Utilitários para formatação e validação de tickers.
"""
import re


def format_ticker(ticker: str) -> str:
    """
    Ajusta o ticker. Se for um ticker da B3 (ex: 4 letras + número),
    adiciona o '.SA' para o yfinance.
    """
    ticker_upper = ticker.upper().strip()
    
    if ticker_upper.endswith(".SA"):
        return ticker_upper
    
    b3_pattern = re.compile(r"^[A-Z]{4}\d+$")
    
    if b3_pattern.match(ticker_upper):
        return f"{ticker_upper}.SA"
        
    return ticker_upper

