"""
Módulo para cálculo de indicadores técnicos.
"""
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta

from app.core.market.ticker_utils import format_ticker


def get_technical_analysis(ticker: str, period: str = "1y") -> list[dict]:
    """
    Busca dados históricos de um ticker e calcula indicadores técnicos:
    MACD, Stochastic, ATR, Bollinger Bands, OBV, RSI.
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
        
        # Converter DataFrame para dict e limpar NaN recursivamente
        records = data.to_dict(orient='records')
        
        # Limpar valores NaN/Inf que não são JSON-compliant
        def clean_nan_values(obj):
            if isinstance(obj, dict):
                return {k: clean_nan_values(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan_values(item) for item in obj]
            elif isinstance(obj, (float, np.floating)):
                if pd.isna(obj) or np.isinf(obj):
                    return None
                return obj
            return obj
        
        return clean_nan_values(records)
        
    except Exception as e:
        print(f"Erro ao buscar análise técnica do ticker {formatted_ticker}: {e}")
        raise

