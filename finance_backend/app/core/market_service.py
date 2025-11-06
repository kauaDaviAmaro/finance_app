import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import re
from typing import Optional, Dict, Any

def _format_ticker(ticker: str) -> str:
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

def get_historical_data(ticker: str, period: str = "1y") -> list[dict]:
    """
    Busca dados históricos de um ticker, formatando-o se for da B3.
    """
    formatted_ticker = _format_ticker(ticker)
    
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


def get_technical_analysis(ticker: str, period: str = "1y") -> list[dict]:
    """
    Busca dados históricos de um ticker e calcula indicadores técnicos:
    MACD, Stochastic, ATR, Bollinger Bands, OBV, RSI.
    """
    formatted_ticker = _format_ticker(ticker)
    
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
        
        # Calcular indicadores técnicos usando pandas-ta
        try:
            # MACD (12, 26, 9)
            macd = ta.macd(data['close'], fast=12, slow=26, signal=9)
            if macd is not None and not macd.empty:
                data['MACD_12_26_9'] = macd['MACD_12_26_9']
                data['MACDh_12_26_9'] = macd['MACDh_12_26_9']
                data['MACDs_12_26_9'] = macd['MACDs_12_26_9']
        except Exception:
            pass
        
        try:
            # Stochastic Oscillator (14, 3, 3)
            stoch = ta.stoch(data['high'], data['low'], data['close'], k=14, d=3, smooth_k=3)
            if stoch is not None and not stoch.empty:
                data['STOCHk_14_3_3'] = stoch['STOCHk_14_3_3']
                data['STOCHd_14_3_3'] = stoch['STOCHd_14_3_3']
        except Exception:
            pass
        
        try:
            # ATR (14)
            atr = ta.atr(data['high'], data['low'], data['close'], length=14)
            if atr is not None and not atr.empty:
                data['ATRr_14'] = atr
        except Exception:
            pass
        
        try:
            # Bollinger Bands (20, 2)
            bbands = ta.bbands(data['close'], length=20, std=2)
            if bbands is not None and not bbands.empty:
                data['BBL_20_2.0'] = bbands['BBL_20_2.0']
                data['BBM_20_2.0'] = bbands['BBM_20_2.0']
                data['BBU_20_2.0'] = bbands['BBU_20_2.0']
        except Exception:
            pass
        
        try:
            # OBV (On Balance Volume)
            obv = ta.obv(data['close'], data['volume'])
            if obv is not None and not obv.empty:
                data['OBV'] = obv
        except Exception:
            pass
        
        try:
            # RSI (14)
            rsi = ta.rsi(data['close'], length=14)
            if rsi is not None and not rsi.empty:
                data['RSI_14'] = rsi
        except Exception:
            pass
        
        # Formatar data
        data['date'] = data['date'].dt.strftime('%Y-%m-%d')
        
        # Selecionar colunas base + indicadores
        base_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        indicator_columns = [
            'MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9',
            'STOCHk_14_3_3', 'STOCHd_14_3_3',
            'ATRr_14',
            'BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0',
            'OBV',
            'RSI_14'
        ]
        
        # Selecionar apenas colunas que existem no DataFrame
        available_columns = base_columns + [col for col in indicator_columns if col in data.columns]
        data = data[available_columns]
        
        # Converter NaN para None para JSON
        data = data.fillna(value=None)
        
        return data.to_dict(orient='records')
        
    except Exception as e:
        print(f"Erro ao buscar análise técnica do ticker {formatted_ticker}: {e}")
        raise


def get_company_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Busca dados fundamentalistas de uma empresa usando yfinance.
    Retorna: P/E, P/VP, Dividend Yield, Beta, Setor, Indústria, Market Cap.
    """
    formatted_ticker = _format_ticker(ticker)
    
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


def get_current_price(ticker: str) -> Optional[float]:
    """
    Busca o preço atual (último fechamento) de um ticker.
    Retorna None se não conseguir buscar.
    """
    formatted_ticker = _format_ticker(ticker)
    
    try:
        stock = yf.Ticker(formatted_ticker)
        data = stock.history(period="1d")
        
        if data.empty:
            return None
        
        # Retornar o último preço de fechamento
        return float(data['Close'].iloc[-1])
        
    except Exception as e:
        print(f"Erro ao buscar preço atual do ticker {formatted_ticker}: {e}")
        return None