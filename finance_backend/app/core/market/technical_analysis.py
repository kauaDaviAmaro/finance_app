"""
Módulo para cálculo de indicadores técnicos.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Literal

from app.core.market.ticker_utils import format_ticker
from app.core.market.data_fetcher import get_company_fundamentals
from app.core.market.indicators.rsi import calculate_rsi
from app.core.market.indicators.macd import calculate_macd
from app.core.market.indicators.moving_averages import calculate_moving_averages, detect_moving_average_cross
from app.core.market.indicators.bollinger_bands import calculate_bollinger_bands
from app.core.market.indicators.other import calculate_atr, calculate_obv, calculate_stochastic
from app.core.redis_cache import get_cached_dataframe, set_cached_dataframe


def _fetch_historical_data_from_yfinance(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Busca dados históricos diretamente do yfinance (sem cache).
    """
    formatted_ticker = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(formatted_ticker)
        data: pd.DataFrame = stock.history(period=period)
        
        if data.empty:
            return pd.DataFrame()
        
        return data
    except Exception as e:
        print(f"Erro ao buscar dados do ticker {formatted_ticker}: {e}")
        raise


def _get_historical_data_with_cache(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Busca dados históricos com cache Redis.
    """
    formatted_ticker = format_ticker(ticker)
    cache_key = f"yfinance:historical:{formatted_ticker}:{period}"
    
    # 1. TENTA BUSCAR NO CACHE
    data = get_cached_dataframe(cache_key)
    
    # 2. NÃO ACHOU NO CACHE? BUSCA NA API (E SALVA)
    if data is None or data.empty:
        print(f"📡 CACHE MISS: Ticker {formatted_ticker} (period={period}). Buscando no yfinance...")
        data = _fetch_historical_data_from_yfinance(ticker, period)
        
        if data is not None and not data.empty:
            set_cached_dataframe(cache_key, data)
    
    return data if data is not None else pd.DataFrame()


def get_technical_analysis(ticker: str, period: str = "1y") -> list[dict]:
    """
    Busca dados históricos de um ticker e calcula indicadores técnicos:
    MACD, Stochastic, ATR, Bollinger Bands, OBV, RSI.
    Usa cache Redis para evitar múltiplas requisições ao yfinance.
    """
    formatted_ticker = format_ticker(ticker)
    
    try:
        data = _get_historical_data_with_cache(ticker, period)
        
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
        
        # Calcular indicadores técnicos usando módulos separados
        try:
            # MACD (12, 26, 9)
            macd = calculate_macd(data, fast=12, slow=26, signal=9)
            if macd is not None and not macd.empty:
                if 'MACD_12_26_9' in macd.columns:
                    data['MACD_12_26_9'] = macd['MACD_12_26_9']
                if 'MACDh_12_26_9' in macd.columns:
                    data['MACDh_12_26_9'] = macd['MACDh_12_26_9']
                if 'MACDs_12_26_9' in macd.columns:
                    data['MACDs_12_26_9'] = macd['MACDs_12_26_9']
        except Exception:
            pass
        
        try:
            # Stochastic Oscillator (14, 3, 3)
            stoch = calculate_stochastic(data, k=14, d=3, smooth_k=3)
            if stoch is not None and not stoch.empty:
                if 'STOCHk_14_3_3' in stoch.columns:
                    data['STOCHk_14_3_3'] = stoch['STOCHk_14_3_3']
                if 'STOCHd_14_3_3' in stoch.columns:
                    data['STOCHd_14_3_3'] = stoch['STOCHd_14_3_3']
        except Exception:
            pass
        
        try:
            # ATR (14)
            atr = calculate_atr(data, length=14)
            if atr is not None and not atr.empty:
                data['ATRr_14'] = atr
        except Exception:
            pass
        
        try:
            # Bollinger Bands (20, 2)
            bbands = calculate_bollinger_bands(data, length=20, std=2)
            if bbands is not None and not bbands.empty:
                if 'BBL_20_2.0' in bbands.columns:
                    data['BBL_20_2.0'] = bbands['BBL_20_2.0']
                if 'BBM_20_2.0' in bbands.columns:
                    data['BBM_20_2.0'] = bbands['BBM_20_2.0']
                if 'BBU_20_2.0' in bbands.columns:
                    data['BBU_20_2.0'] = bbands['BBU_20_2.0']
        except Exception:
            pass
        
        try:
            # OBV (On Balance Volume)
            obv = calculate_obv(data)
            if obv is not None and not obv.empty:
                data['OBV'] = obv
        except Exception:
            pass
        
        try:
            # RSI (14)
            rsi = calculate_rsi(data, length=14)
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


# Re-exportar funções de moving_averages para compatibilidade
from app.core.market.indicators.moving_averages import calculate_moving_averages, detect_moving_average_cross


def get_scanner_indicators(ticker: str, period: str = "1y") -> dict:
    """
    Calcula indicadores técnicos necessários para o scanner:
    RSI_14, MACD signal, e cruzamento de médias móveis (MM9 x MM21).
    Usa cache Redis para evitar múltiplas requisições ao yfinance.
    
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
        data = _get_historical_data_with_cache(ticker, period)
        
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
        from app.core.market.indicators.rsi import get_rsi_value
        rsi_14 = get_rsi_value(data, length=14)
        
        # Calcular MACD
        from app.core.market.indicators.macd import get_macd_values
        macd_values = get_macd_values(data, fast=12, slow=26, signal=9)
        macd_signal = macd_values.get('macd_signal')
        
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
    Usa cache Redis para evitar múltiplas requisições ao yfinance.
    
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
        data = _get_historical_data_with_cache(ticker, period)
        
        if data.empty:
            return {
                'last_price': None,
                'rsi_14': None,
                'macd_signal': None,
                'macd_h': None,
                'mm_9_cruza_mm_21': 'NEUTRAL',
                'bb_upper': None,
                'bb_lower': None,
                'quality_score': None
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
        from app.core.market.indicators.rsi import get_rsi_value
        rsi_14 = get_rsi_value(data, length=14)
        
        # Calcular MACD (obtém signal e histogram de uma vez)
        from app.core.market.indicators.macd import get_macd_values
        macd_values = get_macd_values(data, fast=12, slow=26, signal=9)
        macd_signal = macd_values.get('macd_signal')
        macd_h = macd_values.get('macd_histogram')
        
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
        
        # Buscar quality_score dos fundamentos
        quality_score = None
        try:
            fundamentals = get_company_fundamentals(ticker)
            quality_score = fundamentals.get('quality_score')
        except Exception as e:
            print(f"Erro ao buscar quality_score para {formatted_ticker}: {e}")
        
        return {
            'last_price': last_price,
            'rsi_14': rsi_14,
            'macd_signal': macd_signal,
            'macd_h': macd_h,
            'mm_9_cruza_mm_21': mm_cross or 'NEUTRAL',
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'quality_score': quality_score
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
            'bb_lower': None,
            'quality_score': None
        }


def get_daily_scan_indicators(ticker: str, period: str = "1y") -> dict:
    """
    Calcula indicadores técnicos necessários para DailyScanResult:
    RSI_14, MACD histogram, Bollinger Bands, e último preço.
    Usa cache Redis para evitar múltiplas requisições ao yfinance.
    
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
        data = _get_historical_data_with_cache(ticker, period)
        
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
        from app.core.market.indicators.rsi import get_rsi_value
        rsi_14 = get_rsi_value(data, length=14)
        
        # Calcular MACD histogram
        from app.core.market.indicators.macd import get_macd_values
        macd_values = get_macd_values(data, fast=12, slow=26, signal=9)
        macd_h = macd_values.get('macd_histogram')
        
        # Calcular Bollinger Bands (precisa de pelo menos 20 períodos)
        from app.core.market.indicators.bollinger_bands import get_bollinger_bands_values
        bb_values = get_bollinger_bands_values(data, length=20, std=2)
        bb_upper = bb_values.get('bb_upper')
        bb_lower = bb_values.get('bb_lower')
        
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

