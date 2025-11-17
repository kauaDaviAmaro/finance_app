"""
Cálculo do indicador RSI (Relative Strength Index).
"""
import pandas as pd
import pandas_ta as ta
from typing import Optional


def calculate_rsi(data: pd.DataFrame, length: int = 14) -> Optional[pd.Series]:
    """
    Calcula o RSI (Relative Strength Index) para um DataFrame.
    
    Args:
        data: DataFrame com coluna 'close'
        length: Período do RSI (padrão: 14)
    
    Returns:
        Series com valores do RSI ou None se houver erro
    """
    if data.empty or 'close' not in data.columns:
        return None
    
    try:
        rsi = ta.rsi(data['close'], length=length)
        if rsi is not None and not rsi.empty:
            return rsi
    except Exception:
        pass
    
    return None


def get_rsi_value(data: pd.DataFrame, length: int = 14) -> Optional[float]:
    """
    Obtém o valor mais recente do RSI.
    
    Args:
        data: DataFrame com coluna 'close'
        length: Período do RSI (padrão: 14)
    
    Returns:
        Valor do RSI mais recente ou None
    """
    rsi = calculate_rsi(data, length)
    if rsi is not None and not rsi.empty:
        value = rsi.iloc[-1]
        if not pd.isna(value):
            return float(value)
    return None

