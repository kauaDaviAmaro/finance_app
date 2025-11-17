"""
Cálculo de médias móveis e detecção de cruzamentos.
"""
import pandas as pd
from typing import Optional, Literal


def calculate_moving_averages(
    data: pd.DataFrame,
    mm9_period: int = 9,
    mm21_period: int = 21
) -> pd.DataFrame:
    """
    Calcula médias móveis simples (MM9 e MM21) para um DataFrame de preços.
    
    Args:
        data: DataFrame com coluna 'close'
        mm9_period: Período da média móvel curta (padrão: 9)
        mm21_period: Período da média móvel longa (padrão: 21)
    
    Returns:
        DataFrame com colunas adicionais 'MM9' e 'MM21'
    """
    if data.empty or 'close' not in data.columns:
        return data
    
    data = data.copy()
    data['MM9'] = data['close'].rolling(window=mm9_period).mean()
    data['MM21'] = data['close'].rolling(window=mm21_period).mean()
    
    return data


def detect_moving_average_cross(
    data: pd.DataFrame,
    mm9_col: str = 'MM9',
    mm21_col: str = 'MM21'
) -> Optional[Literal['BULLISH', 'BEARISH', 'NEUTRAL']]:
    """
    Detecta o cruzamento de médias móveis (MM9 e MM21).
    
    Retorna:
        - 'BULLISH': MM9 cruzou acima de MM21 (sinal de compra)
        - 'BEARISH': MM9 cruzou abaixo de MM21 (sinal de venda)
        - 'NEUTRAL': Sem cruzamento ou dados insuficientes
    
    Args:
        data: DataFrame com colunas MM9 e MM21
        mm9_col: Nome da coluna da média móvel curta
        mm21_col: Nome da coluna da média móvel longa
    
    Returns:
        String indicando o tipo de cruzamento ou None
    """
    if data.empty or mm9_col not in data.columns or mm21_col not in data.columns:
        return 'NEUTRAL'
    
    # Pegar os últimos 2 valores válidos (não NaN) para detectar cruzamento
    valid_data = data[[mm9_col, mm21_col]].dropna()
    
    if len(valid_data) < 2:
        return 'NEUTRAL'
    
    # Últimos 2 valores
    last_two = valid_data.tail(2)
    
    prev_mm9 = last_two.iloc[0][mm9_col]
    prev_mm21 = last_two.iloc[0][mm21_col]
    curr_mm9 = last_two.iloc[1][mm9_col]
    curr_mm21 = last_two.iloc[1][mm21_col]
    
    # Detectar cruzamento
    # BULLISH: MM9 estava abaixo e agora está acima de MM21
    if prev_mm9 < prev_mm21 and curr_mm9 > curr_mm21:
        return 'BULLISH'
    
    # BEARISH: MM9 estava acima e agora está abaixo de MM21
    if prev_mm9 > prev_mm21 and curr_mm9 < curr_mm21:
        return 'BEARISH'
    
    # Verificar posição atual (sem cruzamento recente)
    if curr_mm9 > curr_mm21:
        return 'BULLISH'  # MM9 acima de MM21 (tendência de alta)
    elif curr_mm9 < curr_mm21:
        return 'BEARISH'  # MM9 abaixo de MM21 (tendência de baixa)
    else:
        return 'NEUTRAL'  # MM9 igual a MM21

