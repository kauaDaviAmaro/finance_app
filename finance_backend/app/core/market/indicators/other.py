"""
Outros indicadores técnicos (ATR, OBV, Stochastic).
"""
import pandas as pd
import pandas_ta as ta
from typing import Optional


def calculate_atr(
    data: pd.DataFrame,
    length: int = 14
) -> Optional[pd.Series]:
    """
    Calcula o ATR (Average True Range) para um DataFrame.
    
    Args:
        data: DataFrame com colunas 'high', 'low', 'close'
        length: Período do ATR (padrão: 14)
    
    Returns:
        Series com valores do ATR ou None
    """
    if data.empty or not all(col in data.columns for col in ['high', 'low', 'close']):
        return None
    
    try:
        atr = ta.atr(data['high'], data['low'], data['close'], length=length)
        if atr is not None and not atr.empty:
            return atr
    except Exception:
        pass
    
    return None


def calculate_obv(
    data: pd.DataFrame
) -> Optional[pd.Series]:
    """
    Calcula o OBV (On Balance Volume) para um DataFrame.
    
    Args:
        data: DataFrame com colunas 'close' e 'volume'
    
    Returns:
        Series com valores do OBV ou None
    """
    if data.empty or 'close' not in data.columns or 'volume' not in data.columns:
        return None
    
    try:
        obv = ta.obv(data['close'], data['volume'])
        if obv is not None and not obv.empty:
            return obv
    except Exception:
        pass
    
    return None


def calculate_stochastic(
    data: pd.DataFrame,
    k: int = 14,
    d: int = 3,
    smooth_k: int = 3
) -> Optional[pd.DataFrame]:
    """
    Calcula o Stochastic Oscillator para um DataFrame.
    
    Args:
        data: DataFrame com colunas 'high', 'low', 'close'
        k: Período %K (padrão: 14)
        d: Período %D (padrão: 3)
        smooth_k: Suavização de %K (padrão: 3)
    
    Returns:
        DataFrame com colunas STOCHk e STOCHd ou None
    """
    if data.empty or not all(col in data.columns for col in ['high', 'low', 'close']):
        return None
    
    try:
        stoch = ta.stoch(data['high'], data['low'], data['close'], k=k, d=d, smooth_k=smooth_k)
        if stoch is not None and not stoch.empty:
            return stoch
    except Exception:
        pass
    
    return None

