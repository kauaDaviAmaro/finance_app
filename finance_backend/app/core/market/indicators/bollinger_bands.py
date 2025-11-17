"""
Cálculo das Bandas de Bollinger.
"""
import pandas as pd
import pandas_ta as ta
from typing import Optional, Dict


def calculate_bollinger_bands(
    data: pd.DataFrame,
    length: int = 20,
    std: float = 2.0
) -> Optional[pd.DataFrame]:
    """
    Calcula as Bandas de Bollinger para um DataFrame.
    
    Args:
        data: DataFrame com coluna 'close'
        length: Período da média móvel (padrão: 20)
        std: Desvio padrão (padrão: 2.0)
    
    Returns:
        DataFrame com colunas BBL (lower), BBM (middle), BBU (upper) ou None
    """
    if data.empty or 'close' not in data.columns:
        return None
    
    if len(data) < length:
        return None
    
    try:
        bbands = ta.bbands(data['close'], length=length, std=std)
        if bbands is not None and not bbands.empty:
            return bbands
    except Exception:
        pass
    
    return None


def get_bollinger_bands_values(
    data: pd.DataFrame,
    length: int = 20,
    std: float = 2.0
) -> Dict[str, Optional[float]]:
    """
    Obtém os valores mais recentes das Bandas de Bollinger.
    
    Args:
        data: DataFrame com coluna 'close'
        length: Período da média móvel (padrão: 20)
        std: Desvio padrão (padrão: 2.0)
    
    Returns:
        Dict com 'bb_upper', 'bb_middle' e 'bb_lower'
    """
    bbands_df = calculate_bollinger_bands(data, length, std)
    
    result = {
        'bb_upper': None,
        'bb_middle': None,
        'bb_lower': None
    }
    
    if bbands_df is None or bbands_df.empty:
        return result
    
    # Tentar encontrar as colunas corretas
    for col in bbands_df.columns:
        if 'BBU' in col or 'BBU_20_2.0' in col:
            value = bbands_df[col].iloc[-1]
            if not pd.isna(value):
                result['bb_upper'] = float(value)
        elif 'BBM' in col or 'BBM_20_2.0' in col:
            value = bbands_df[col].iloc[-1]
            if not pd.isna(value):
                result['bb_middle'] = float(value)
        elif 'BBL' in col or 'BBL_20_2.0' in col:
            value = bbands_df[col].iloc[-1]
            if not pd.isna(value):
                result['bb_lower'] = float(value)
    
    return result

