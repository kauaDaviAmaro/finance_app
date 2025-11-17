"""
Cálculo do indicador MACD (Moving Average Convergence Divergence).
"""
import pandas as pd
import pandas_ta as ta
from typing import Optional, Dict


def calculate_macd(
    data: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Optional[pd.DataFrame]:
    """
    Calcula o MACD para um DataFrame.
    
    Args:
        data: DataFrame com coluna 'close'
        fast: Período da média rápida (padrão: 12)
        slow: Período da média lenta (padrão: 26)
        signal: Período da linha de sinal (padrão: 9)
    
    Returns:
        DataFrame com colunas MACD, MACDh (histogram) e MACDs (signal) ou None
    """
    if data.empty or 'close' not in data.columns:
        return None
    
    try:
        macd = ta.macd(data['close'], fast=fast, slow=slow, signal=signal)
        if macd is not None and not macd.empty:
            return macd
    except Exception:
        pass
    
    return None


def get_macd_values(
    data: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Dict[str, Optional[float]]:
    """
    Obtém os valores mais recentes do MACD (MACD, histogram e signal).
    
    Args:
        data: DataFrame com coluna 'close'
        fast: Período da média rápida (padrão: 12)
        slow: Período da média lenta (padrão: 26)
        signal: Período da linha de sinal (padrão: 9)
    
    Returns:
        Dict com 'macd', 'macd_histogram' e 'macd_signal'
    """
    macd_df = calculate_macd(data, fast, slow, signal)
    
    result = {
        'macd': None,
        'macd_histogram': None,
        'macd_signal': None
    }
    
    if macd_df is None or macd_df.empty:
        return result
    
    # Tentar encontrar as colunas corretas
    for col in macd_df.columns:
        if 'MACD_' in col and 'MACDh' not in col and 'MACDs' not in col:
            value = macd_df[col].iloc[-1]
            if not pd.isna(value):
                result['macd'] = float(value)
        elif 'MACDh' in col:
            value = macd_df[col].iloc[-1]
            if not pd.isna(value):
                result['macd_histogram'] = float(value)
        elif 'MACDs' in col:
            value = macd_df[col].iloc[-1]
            if not pd.isna(value):
                result['macd_signal'] = float(value)
    
    return result

