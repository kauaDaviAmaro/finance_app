"""
Módulo para cálculo de indicadores técnicos.
"""
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Optional, Literal

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


def calculate_moving_averages(data: pd.DataFrame, mm9_period: int = 9, mm21_period: int = 21) -> pd.DataFrame:
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


def detect_moving_average_cross(data: pd.DataFrame, mm9_col: str = 'MM9', mm21_col: str = 'MM21') -> Optional[Literal['BULLISH', 'BEARISH', 'NEUTRAL']]:
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


def get_scanner_indicators(ticker: str, period: str = "1y") -> dict:
    """
    Calcula indicadores técnicos necessários para o scanner:
    RSI_14, MACD signal, e cruzamento de médias móveis (MM9 x MM21).
    
    Args:
        ticker: Ticker da ação (ex: 'PETR4')
        period: Período de dados históricos (padrão: '1y')
    
    Returns:
        Dicionário com:
        - rsi_14: Valor do RSI(14) mais recente
        - macd_signal: Valor do MACD signal mais recente
        - mm_9_cruza_mm_21: 'BULLISH', 'BEARISH' ou 'NEUTRAL'
    """
    formatted_ticker = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(formatted_ticker)
        data: pd.DataFrame = stock.history(period=period)
        
        if data.empty:
            return {
                'rsi_14': None,
                'macd_signal': None,
                'mm_9_cruza_mm_21': 'NEUTRAL'
            }
        
        data.reset_index(inplace=True)
        data.rename(columns={
            'Date': 'date',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)
        
        # Calcular RSI
        rsi_14 = None
        try:
            rsi = ta.rsi(data['close'], length=14)
            if rsi is not None and not rsi.empty:
                rsi_14 = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        except Exception:
            pass
        
        # Calcular MACD
        macd_signal = None
        try:
            macd = ta.macd(data['close'], fast=12, slow=26, signal=9)
            if macd is not None and not macd.empty and 'MACDs_12_26_9' in macd.columns:
                macd_signal = float(macd['MACDs_12_26_9'].iloc[-1]) if not pd.isna(macd['MACDs_12_26_9'].iloc[-1]) else None
        except Exception:
            pass
        
        # Calcular médias móveis e detectar cruzamento
        data_with_ma = calculate_moving_averages(data)
        mm_cross = detect_moving_average_cross(data_with_ma)
        
        return {
            'rsi_14': rsi_14,
            'macd_signal': macd_signal,
            'mm_9_cruza_mm_21': mm_cross or 'NEUTRAL'
        }
        
    except Exception as e:
        print(f"Erro ao calcular indicadores do scanner para {formatted_ticker}: {e}")
        return {
            'rsi_14': None,
            'macd_signal': None,
            'mm_9_cruza_mm_21': 'NEUTRAL'
        }


def get_all_scanner_indicators(ticker: str, period: str = "1y") -> dict:
    """
    Calcula TODOS os indicadores técnicos necessários para ambos ScannerData e DailyScanResult
    em uma única chamada ao yfinance (otimização para evitar chamadas duplicadas).
    
    Args:
        ticker: Ticker da ação (ex: 'PETR4')
        period: Período de dados históricos (padrão: '1y')
    
    Returns:
        Dicionário com todos os indicadores:
        - last_price: Último preço de fechamento
        - rsi_14: Valor do RSI(14) mais recente
        - macd_signal: Valor do MACD signal mais recente
        - macd_h: Valor do MACD histogram mais recente
        - mm_9_cruza_mm_21: 'BULLISH', 'BEARISH' ou 'NEUTRAL'
        - bb_upper: Banda superior de Bollinger
        - bb_lower: Banda inferior de Bollinger
    """
    formatted_ticker = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(formatted_ticker)
        data: pd.DataFrame = stock.history(period=period)
        
        if data.empty:
            return {
                'last_price': None,
                'rsi_14': None,
                'macd_signal': None,
                'macd_h': None,
                'mm_9_cruza_mm_21': 'NEUTRAL',
                'bb_upper': None,
                'bb_lower': None
            }
        
        data.reset_index(inplace=True)
        data.rename(columns={
            'Date': 'date',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)
        
        # Último preço
        last_price = float(data['close'].iloc[-1]) if not data['close'].empty else None
        
        # Calcular RSI (usado por ambos)
        rsi_14 = None
        try:
            rsi = ta.rsi(data['close'], length=14)
            if rsi is not None and not rsi.empty:
                rsi_14 = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        except Exception:
            pass
        
        # Calcular MACD (obtém signal e histogram de uma vez)
        macd_signal = None
        macd_h = None
        try:
            macd = ta.macd(data['close'], fast=12, slow=26, signal=9)
            if macd is not None and not macd.empty:
                if 'MACDs_12_26_9' in macd.columns:
                    macd_signal = float(macd['MACDs_12_26_9'].iloc[-1]) if not pd.isna(macd['MACDs_12_26_9'].iloc[-1]) else None
                if 'MACDh_12_26_9' in macd.columns:
                    macd_h = float(macd['MACDh_12_26_9'].iloc[-1]) if not pd.isna(macd['MACDh_12_26_9'].iloc[-1]) else None
        except Exception:
            pass
        
        # Calcular médias móveis e detectar cruzamento
        data_with_ma = calculate_moving_averages(data)
        mm_cross = detect_moving_average_cross(data_with_ma)
        
        # Calcular Bollinger Bands (precisa de pelo menos 20 períodos)
        bb_upper = None
        bb_lower = None
        try:
            if len(data) >= 20:  # Bollinger Bands precisa de pelo menos 20 períodos
                bbands = ta.bbands(data['close'], length=20, std=2)
                if bbands is not None and not bbands.empty:
                    # Verificar se bbands é um DataFrame
                    if isinstance(bbands, pd.DataFrame):
                        # Verificar todas as colunas possíveis
                        for col in bbands.columns:
                            if 'BBU' in col or 'BBU_20_2.0' in col:
                                bb_upper_val = bbands[col].iloc[-1]
                                if not pd.isna(bb_upper_val):
                                    bb_upper = float(bb_upper_val)
                                    break
                        for col in bbands.columns:
                            if 'BBL' in col or 'BBL_20_2.0' in col:
                                bb_lower_val = bbands[col].iloc[-1]
                                if not pd.isna(bb_lower_val):
                                    bb_lower = float(bb_lower_val)
                                    break
                    else:
                        # Se não for DataFrame, pode ser que retorne um dict ou outra estrutura
                        print(f"Bollinger Bands retornou tipo inesperado: {type(bbands)} para {formatted_ticker}")
        except Exception as e:
            print(f"Erro ao calcular Bollinger Bands para {formatted_ticker}: {e}")
            import traceback
            traceback.print_exc()
        
        return {
            'last_price': last_price,
            'rsi_14': rsi_14,
            'macd_signal': macd_signal,
            'macd_h': macd_h,
            'mm_9_cruza_mm_21': mm_cross or 'NEUTRAL',
            'bb_upper': bb_upper,
            'bb_lower': bb_lower
        }
        
    except Exception as e:
        print(f"Erro ao calcular indicadores do scanner para {formatted_ticker}: {e}")
        return {
            'last_price': None,
            'rsi_14': None,
            'macd_signal': None,
            'macd_h': None,
            'mm_9_cruza_mm_21': 'NEUTRAL',
            'bb_upper': None,
            'bb_lower': None
        }


def get_daily_scan_indicators(ticker: str, period: str = "1y") -> dict:
    """
    Calcula indicadores técnicos necessários para DailyScanResult:
    RSI_14, MACD histogram, Bollinger Bands, e último preço.
    
    Args:
        ticker: Ticker da ação (ex: 'PETR4')
        period: Período de dados históricos (padrão: '1y')
    
    Returns:
        Dicionário com:
        - last_price: Último preço de fechamento
        - rsi_14: Valor do RSI(14) mais recente
        - macd_h: Valor do MACD histogram mais recente
        - bb_upper: Banda superior de Bollinger
        - bb_lower: Banda inferior de Bollinger
    """
    formatted_ticker = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(formatted_ticker)
        data: pd.DataFrame = stock.history(period=period)
        
        if data.empty:
            return {
                'last_price': None,
                'rsi_14': None,
                'macd_h': None,
                'bb_upper': None,
                'bb_lower': None
            }
        
        data.reset_index(inplace=True)
        data.rename(columns={
            'Date': 'date',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)
        
        # Último preço
        last_price = float(data['close'].iloc[-1]) if not data['close'].empty else None
        
        # Calcular RSI
        rsi_14 = None
        try:
            rsi = ta.rsi(data['close'], length=14)
            if rsi is not None and not rsi.empty:
                rsi_14 = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        except Exception:
            pass
        
        # Calcular MACD histogram
        macd_h = None
        try:
            macd = ta.macd(data['close'], fast=12, slow=26, signal=9)
            if macd is not None and not macd.empty and 'MACDh_12_26_9' in macd.columns:
                macd_h = float(macd['MACDh_12_26_9'].iloc[-1]) if not pd.isna(macd['MACDh_12_26_9'].iloc[-1]) else None
        except Exception:
            pass
        
        # Calcular Bollinger Bands (precisa de pelo menos 20 períodos)
        bb_upper = None
        bb_lower = None
        try:
            if len(data) >= 20:  # Bollinger Bands precisa de pelo menos 20 períodos
                bbands = ta.bbands(data['close'], length=20, std=2)
                if bbands is not None and not bbands.empty:
                    # Verificar se bbands é um DataFrame
                    if isinstance(bbands, pd.DataFrame):
                        # Verificar todas as colunas possíveis
                        for col in bbands.columns:
                            if 'BBU' in col or 'BBU_20_2.0' in col:
                                bb_upper_val = bbands[col].iloc[-1]
                                if not pd.isna(bb_upper_val):
                                    bb_upper = float(bb_upper_val)
                                    break
                        for col in bbands.columns:
                            if 'BBL' in col or 'BBL_20_2.0' in col:
                                bb_lower_val = bbands[col].iloc[-1]
                                if not pd.isna(bb_lower_val):
                                    bb_lower = float(bb_lower_val)
                                    break
                    else:
                        # Se não for DataFrame, pode ser que retorne um dict ou outra estrutura
                        print(f"Bollinger Bands retornou tipo inesperado: {type(bbands)} para {formatted_ticker}")
        except Exception as e:
            print(f"Erro ao calcular Bollinger Bands para {formatted_ticker}: {e}")
            import traceback
            traceback.print_exc()
        
        return {
            'last_price': last_price,
            'rsi_14': rsi_14,
            'macd_h': macd_h,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower
        }
        
    except Exception as e:
        print(f"Erro ao calcular indicadores do daily scan para {formatted_ticker}: {e}")
        return {
            'last_price': None,
            'rsi_14': None,
            'macd_h': None,
            'bb_upper': None,
            'bb_lower': None
        }

