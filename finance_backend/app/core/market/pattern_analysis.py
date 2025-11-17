"""
Módulo para análise avançada de padrões técnicos.
Inclui detecção de padrões gráficos, suporte/resistência, padrões de candlestick,
retrações de Fibonacci e análise de ondas de Elliott.
"""
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import List, Dict, Optional, Tuple, Literal
from scipy import signal
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist

from app.core.market.ticker_utils import format_ticker
from app.core.redis_cache import get_cached_dataframe, set_cached_dataframe


def _fetch_historical_dataframe_from_yfinance(ticker: str, period: str = "1y") -> pd.DataFrame:
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


def get_historical_dataframe(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Busca dados históricos e retorna como DataFrame.
    Usa cache Redis para evitar múltiplas requisições ao yfinance.
    """
    formatted_ticker = format_ticker(ticker)
    cache_key = f"yfinance:historical:{formatted_ticker}:{period}"
    
    # 1. TENTA BUSCAR NO CACHE
    data = get_cached_dataframe(cache_key)
    
    # 2. NÃO ACHOU NO CACHE? BUSCA NA API (E SALVA)
    if data is None or data.empty:
        print(f"📡 CACHE MISS: Ticker {formatted_ticker} (period={period}). Buscando no yfinance...")
        data = _fetch_historical_dataframe_from_yfinance(ticker, period)
        
        if data is not None and not data.empty:
            set_cached_dataframe(cache_key, data)
    
    if data.empty:
        return pd.DataFrame()
    
    data = data.copy()
    data.reset_index(inplace=True)
    data.rename(columns={
        'Date': 'date',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    }, inplace=True)
    
    return data[['date', 'open', 'high', 'low', 'close', 'volume']]


def find_pivot_points(data: pd.DataFrame, window: int = 5) -> Tuple[List[Dict], List[Dict]]:
    """
    Encontra pontos pivô (máximos e mínimos locais).
    
    Args:
        data: DataFrame com colunas 'date', 'high', 'low', 'close'
        window: Janela para identificar máximos/mínimos locais
    
    Returns:
        Tuple com (lista de máximos, lista de mínimos)
    """
    if len(data) < window * 2:
        return [], []
    
    highs = data['high'].values
    lows = data['low'].values
    dates = data['date'].values
    
    # Encontrar máximos locais
    max_indices = signal.argrelextrema(highs, np.greater, order=window)[0]
    maxima = []
    for idx in max_indices:
        maxima.append({
            'date': str(dates[idx]),
            'price': float(highs[idx]),
            'index': int(idx)
        })
    
    # Encontrar mínimos locais
    min_indices = signal.argrelextrema(lows, np.less, order=window)[0]
    minima = []
    for idx in min_indices:
        minima.append({
            'date': str(dates[idx]),
            'price': float(lows[idx]),
            'index': int(idx)
        })
    
    return maxima, minima


def identify_support_resistance(data: pd.DataFrame, window: int = 5, cluster_threshold: float = 0.02) -> Dict[str, List[Dict]]:
    """
    Identifica níveis de suporte e resistência usando pivot points e clustering.
    
    Args:
        data: DataFrame com dados históricos
        window: Janela para identificar pivot points
        cluster_threshold: Threshold para agrupar níveis próximos (2% por padrão)
    
    Returns:
        Dict com 'support_levels' e 'resistance_levels'
    """
    if data.empty or len(data) < window * 2:
        return {'support_levels': [], 'resistance_levels': []}
    
    maxima, minima = find_pivot_points(data, window)
    
    if not maxima and not minima:
        return {'support_levels': [], 'resistance_levels': []}
    
    # Agrupar níveis próximos usando clustering
    support_levels = _cluster_levels(minima, data['close'].iloc[-1], cluster_threshold)
    resistance_levels = _cluster_levels(maxima, data['close'].iloc[-1], cluster_threshold)
    
    return {
        'support_levels': support_levels,
        'resistance_levels': resistance_levels
    }


def _cluster_levels(points: List[Dict], current_price: float, threshold: float) -> List[Dict]:
    """
    Agrupa níveis próximos usando clustering hierárquico.
    """
    if not points:
        return []
    
    prices = np.array([p['price'] for p in points])
    
    if len(prices) < 2:
        return [{
            'price': float(prices[0]),
            'strength': 1,
            'test_count': 1,
            'distance_from_current': abs(float(prices[0]) - current_price) / current_price * 100
        }]
    
    # Normalizar preços para clustering
    normalized = prices / current_price
    
    # Calcular distâncias
    distances = pdist(normalized.reshape(-1, 1))
    
    if len(distances) == 0:
        return [{
            'price': float(prices[0]),
            'strength': 1,
            'test_count': 1,
            'distance_from_current': abs(float(prices[0]) - current_price) / current_price * 100
        }]
    
    # Clustering hierárquico
    linkage_matrix = linkage(distances, method='ward')
    clusters = fcluster(linkage_matrix, threshold, criterion='distance')
    
    # Agrupar pontos por cluster
    clustered_levels = []
    for cluster_id in np.unique(clusters):
        cluster_points = prices[clusters == cluster_id]
        cluster_price = float(np.mean(cluster_points))
        test_count = len(cluster_points)
        
        clustered_levels.append({
            'price': cluster_price,
            'strength': min(test_count / 3.0, 1.0),  # Normalizar força (máx 1.0)
            'test_count': test_count,
            'distance_from_current': abs(cluster_price - current_price) / current_price * 100
        })
    
    # Ordenar por força (mais testado primeiro)
    clustered_levels.sort(key=lambda x: x['strength'], reverse=True)
    
    return clustered_levels


def calculate_fibonacci_levels(data: pd.DataFrame) -> Dict[str, float]:
    """
    Calcula níveis de retração de Fibonacci baseado no swing high e swing low do período.
    
    Args:
        data: DataFrame com dados históricos
    
    Returns:
        Dict com níveis de Fibonacci
    """
    if data.empty:
        return {}
    
    swing_high = float(data['high'].max())
    swing_low = float(data['low'].min())
    diff = swing_high - swing_low
    
    if diff == 0:
        return {}
    
    # Níveis de retração padrão
    fib_levels = {
        'swing_high': swing_high,
        'swing_low': swing_low,
        'level_0': swing_high,
        'level_236': swing_high - (diff * 0.236),
        'level_382': swing_high - (diff * 0.382),
        'level_500': swing_high - (diff * 0.5),
        'level_618': swing_high - (diff * 0.618),
        'level_786': swing_high - (diff * 0.786),
        'level_1000': swing_low,
        # Extensões
        'level_1272': swing_low - (diff * 0.272),
        'level_1618': swing_low - (diff * 0.618),
    }
    
    return fib_levels


def detect_chart_patterns(data: pd.DataFrame) -> List[Dict]:
    """
    Detecta padrões gráficos comuns (cabeça e ombros, triângulos, duplo topo/fundo).
    
    Args:
        data: DataFrame com dados históricos
    
    Returns:
        Lista de padrões detectados com confiança
    """
    patterns = []
    
    if data.empty or len(data) < 20:
        return patterns
    
    maxima, minima = find_pivot_points(data, window=3)
    
    if len(maxima) < 3 or len(minima) < 2:
        return patterns
    
    # Detectar cabeça e ombros
    head_shoulders = _detect_head_shoulders(maxima, minima, data)
    if head_shoulders:
        patterns.append(head_shoulders)
    
    # Detectar duplo topo/fundo
    double_top = _detect_double_top(maxima, data)
    if double_top:
        patterns.append(double_top)
    
    double_bottom = _detect_double_bottom(minima, data)
    if double_bottom:
        patterns.append(double_bottom)
    
    # Detectar triângulos
    triangles = _detect_triangles(data, maxima, minima)
    patterns.extend(triangles)
    
    return patterns


def _detect_head_shoulders(maxima: List[Dict], minima: List[Dict], data: pd.DataFrame) -> Optional[Dict]:
    """
    Detecta padrão cabeça e ombros.
    """
    if len(maxima) < 3:
        return None
    
    # Ordenar máximos por índice
    sorted_maxima = sorted(maxima, key=lambda x: x['index'])
    
    # Procurar padrão: ombro esquerdo < cabeça > ombro direito
    for i in range(len(sorted_maxima) - 2):
        left_shoulder = sorted_maxima[i]
        head = sorted_maxima[i + 1]
        right_shoulder = sorted_maxima[i + 2]
        
        # Verificar se cabeça é mais alta que os ombros
        if (head['price'] > left_shoulder['price'] and 
            head['price'] > right_shoulder['price']):
            
            # Verificar se ombros são similares em altura
            shoulder_diff = abs(left_shoulder['price'] - right_shoulder['price']) / head['price']
            if shoulder_diff < 0.05:  # 5% de tolerância
                # Calcular linha de pescoço (mínimo entre ombros)
                neckline_start = left_shoulder['index']
                neckline_end = right_shoulder['index']
                neckline_low = float(data.iloc[neckline_start:neckline_end]['low'].min())
                
                confidence = 0.7 if shoulder_diff < 0.03 else 0.5
                
                return {
                    'pattern_type': 'HEAD_AND_SHOULDERS',
                    'pattern_name': 'Cabeça e Ombros',
                    'start_date': str(data.iloc[left_shoulder['index']]['date']),
                    'end_date': str(data.iloc[right_shoulder['index']]['date']),
                    'confidence': confidence,
                    'head_price': head['price'],
                    'neckline': neckline_low
                }
    
    return None


def _detect_double_top(maxima: List[Dict], data: pd.DataFrame) -> Optional[Dict]:
    """
    Detecta padrão duplo topo.
    """
    if len(maxima) < 2:
        return None
    
    sorted_maxima = sorted(maxima, key=lambda x: x['price'], reverse=True)
    
    # Pegar os dois topos mais altos
    top1 = sorted_maxima[0]
    top2 = sorted_maxima[1]
    
    # Verificar se são similares em altura e não muito próximos
    price_diff = abs(top1['price'] - top2['price']) / top1['price']
    index_diff = abs(top1['index'] - top2['index'])
    
    if price_diff < 0.03 and index_diff > 10:  # 3% de tolerância, pelo menos 10 períodos de distância
        # Encontrar mínimo entre os topos (vala)
        start_idx = min(top1['index'], top2['index'])
        end_idx = max(top1['index'], top2['index'])
        valley = float(data.iloc[start_idx:end_idx]['low'].min())
        
        return {
            'pattern_type': 'DOUBLE_TOP',
            'pattern_name': 'Duplo Topo',
            'start_date': str(data.iloc[top1['index']]['date']),
            'end_date': str(data.iloc[top2['index']]['date']),
            'confidence': 0.6 if price_diff < 0.02 else 0.4,
            'top_price': (top1['price'] + top2['price']) / 2,
            'valley': valley
        }
    
    return None


def _detect_double_bottom(minima: List[Dict], data: pd.DataFrame) -> Optional[Dict]:
    """
    Detecta padrão duplo fundo.
    """
    if len(minima) < 2:
        return None
    
    sorted_minima = sorted(minima, key=lambda x: x['price'])
    
    # Pegar os dois fundos mais baixos
    bottom1 = sorted_minima[0]
    bottom2 = sorted_minima[1]
    
    # Verificar se são similares em altura e não muito próximos
    price_diff = abs(bottom1['price'] - bottom2['price']) / bottom1['price']
    index_diff = abs(bottom1['index'] - bottom2['index'])
    
    if price_diff < 0.03 and index_diff > 10:
        # Encontrar máximo entre os fundos (pico)
        start_idx = min(bottom1['index'], bottom2['index'])
        end_idx = max(bottom1['index'], bottom2['index'])
        peak = float(data.iloc[start_idx:end_idx]['high'].max())
        
        return {
            'pattern_type': 'DOUBLE_BOTTOM',
            'pattern_name': 'Duplo Fundo',
            'start_date': str(data.iloc[bottom1['index']]['date']),
            'end_date': str(data.iloc[bottom2['index']]['date']),
            'confidence': 0.6 if price_diff < 0.02 else 0.4,
            'bottom_price': (bottom1['price'] + bottom2['price']) / 2,
            'peak': peak
        }
    
    return None


def _detect_triangles(data: pd.DataFrame, maxima: List[Dict], minima: List[Dict]) -> List[Dict]:
    """
    Detecta padrões de triângulo (ascendente, descendente, simétrico).
    """
    triangles = []
    
    if len(maxima) < 3 or len(minima) < 3:
        return triangles
    
    # Ordenar por índice
    sorted_maxima = sorted(maxima, key=lambda x: x['index'])
    sorted_minima = sorted(minima, key=lambda x: x['index'])
    
    # Pegar últimos 3 topos e 3 fundos
    recent_maxima = sorted_maxima[-3:]
    recent_minima = sorted_minima[-3:]
    
    if len(recent_maxima) < 3 or len(recent_minima) < 3:
        return triangles
    
    # Calcular tendências
    max_trend = np.polyfit([m['index'] for m in recent_maxima], [m['price'] for m in recent_maxima], 1)[0]
    min_trend = np.polyfit([m['index'] for m in recent_minima], [m['price'] for m in recent_minima], 1)[0]
    
    # Triângulo ascendente: fundos ascendentes, topos horizontais
    if min_trend > 0 and abs(max_trend) < 0.001:
        triangles.append({
            'pattern_type': 'ASCENDING_TRIANGLE',
            'pattern_name': 'Triângulo Ascendente',
            'start_date': str(data.iloc[recent_minima[0]['index']]['date']),
            'end_date': str(data.iloc[-1]['date']),
            'confidence': 0.5,
            'trend': 'BULLISH'
        })
    
    # Triângulo descendente: topos descendentes, fundos horizontais
    elif max_trend < 0 and abs(min_trend) < 0.001:
        triangles.append({
            'pattern_type': 'DESCENDING_TRIANGLE',
            'pattern_name': 'Triângulo Descendente',
            'start_date': str(data.iloc[recent_maxima[0]['index']]['date']),
            'end_date': str(data.iloc[-1]['date']),
            'confidence': 0.5,
            'trend': 'BEARISH'
        })
    
    # Triângulo simétrico: ambos convergindo
    elif (max_trend < 0 and min_trend > 0) or (abs(max_trend) > 0.001 and abs(min_trend) > 0.001):
        triangles.append({
            'pattern_type': 'SYMMETRIC_TRIANGLE',
            'pattern_name': 'Triângulo Simétrico',
            'start_date': str(data.iloc[min(recent_minima[0]['index'], recent_maxima[0]['index'])]['date']),
            'end_date': str(data.iloc[-1]['date']),
            'confidence': 0.4,
            'trend': 'NEUTRAL'
        })
    
    return triangles


def detect_candlestick_patterns(data: pd.DataFrame) -> List[Dict]:
    """
    Detecta padrões de candlestick usando pandas-ta.
    
    Args:
        data: DataFrame com dados históricos
    
    Returns:
        Lista de padrões de candlestick detectados
    """
    patterns = []
    
    if data.empty or len(data) < 5:
        return patterns
    
    try:
        # Tentar usar pandas-ta para detectar padrões de candlestick
        # Verificar se a função existe antes de usar
        if hasattr(ta, 'cdl_pattern'):
            cdl_patterns = ta.cdl_pattern(data['open'], data['high'], data['low'], data['close'])
            
            if cdl_patterns is not None and not cdl_patterns.empty:
                # Iterar sobre os últimos 20 períodos para encontrar padrões
                for idx in range(max(0, len(data) - 20), len(data)):
                    row = cdl_patterns.iloc[idx]
                    
                    # Verificar cada coluna de padrão (pandas-ta retorna múltiplas colunas)
                    for col in cdl_patterns.columns:
                        if row[col] != 0:  # 0 significa sem padrão, valores positivos/negativos indicam padrão
                            pattern_name = col.replace('CDL_', '').replace('_', ' ').title()
                            signal_type = 'BULLISH' if row[col] > 0 else 'BEARISH'
                            
                            patterns.append({
                                'pattern_name': pattern_name,
                                'pattern_type': col,
                                'date': str(data.iloc[idx]['date']),
                                'signal': signal_type,
                                'price': float(data.iloc[idx]['close'])
                            })
        
        # Se pandas-ta não tiver cdl_pattern ou não encontrou padrões, usar detecção manual básica
        if not patterns:
            patterns = _detect_basic_candlestick_patterns(data)
            
    except Exception as e:
        print(f"Erro ao detectar padrões de candlestick: {e}")
        # Fallback para detecção manual
        patterns = _detect_basic_candlestick_patterns(data)
    
    # Remover duplicatas e retornar apenas os mais recentes
    seen = set()
    unique_patterns = []
    for p in reversed(patterns):  # Começar pelos mais recentes
        key = (p['date'], p['pattern_type'])
        if key not in seen:
            seen.add(key)
            unique_patterns.append(p)
    
    return list(reversed(unique_patterns))[:10]  # Retornar até 10 padrões mais recentes


def _detect_basic_candlestick_patterns(data: pd.DataFrame) -> List[Dict]:
    """
    Detecção manual básica de alguns padrões de candlestick comuns.
    """
    patterns = []
    
    for i in range(1, min(len(data), 20)):  # Verificar últimos 20 períodos
        idx = len(data) - i - 1
        if idx < 1:
            break
        
        current = data.iloc[idx]
        prev = data.iloc[idx - 1]
        
        open_price = current['open']
        close_price = current['close']
        high_price = current['high']
        low_price = current['low']
        prev_open = prev['open']
        prev_close = prev['close']
        
        body = abs(close_price - open_price)
        total_range = high_price - low_price
        
        if total_range == 0:
            continue
        
        body_ratio = body / total_range
        
        # Doji: corpo muito pequeno
        if body_ratio < 0.1:
            patterns.append({
                'pattern_name': 'Doji',
                'pattern_type': 'DOJI',
                'date': str(current['date']),
                'signal': 'NEUTRAL',
                'price': float(close_price)
            })
        
        # Hammer: corpo pequeno, sombra inferior longa, sem sombra superior
        upper_shadow = high_price - max(open_price, close_price)
        lower_shadow = min(open_price, close_price) - low_price
        
        if body_ratio < 0.3 and lower_shadow > body * 2 and upper_shadow < body * 0.5:
            patterns.append({
                'pattern_name': 'Hammer',
                'pattern_type': 'HAMMER',
                'date': str(current['date']),
                'signal': 'BULLISH',
                'price': float(close_price)
            })
        
        # Engulfing: corpo atual engole corpo anterior
        if (prev_close < prev_open and close_price > open_price and
            open_price < prev_close and close_price > prev_open):
            patterns.append({
                'pattern_name': 'Bullish Engulfing',
                'pattern_type': 'BULLISH_ENGULFING',
                'date': str(current['date']),
                'signal': 'BULLISH',
                'price': float(close_price)
            })
        
        if (prev_close > prev_open and close_price < open_price and
            open_price > prev_close and close_price < prev_open):
            patterns.append({
                'pattern_name': 'Bearish Engulfing',
                'pattern_type': 'BEARISH_ENGULFING',
                'date': str(current['date']),
                'signal': 'BEARISH',
                'price': float(close_price)
            })
    
    return patterns


def analyze_elliott_waves(data: pd.DataFrame) -> Dict:
    """
    Análise básica de ondas de Elliott (identificação de padrões de 5 ondas e 3 ondas).
    
    Args:
        data: DataFrame com dados históricos
    
    Returns:
        Dict com estrutura de ondas identificada
    """
    if data.empty or len(data) < 20:
        return {
            'pattern_type': None,
            'waves': [],
            'confidence': 0.0
        }
    
    try:
        # Usar análise de momentum e estrutura de preços para identificar ondas
        closes = data['close'].values
        
        # Calcular RSI para identificar momentum
        rsi = ta.rsi(data['close'], length=14)
        
        if rsi is None or rsi.empty:
            return {
                'pattern_type': None,
                'waves': [],
                'confidence': 0.0
            }
        
        # Identificar pontos de reversão usando RSI e preços
        maxima, minima = find_pivot_points(data, window=3)
        
        if len(maxima) < 3 or len(minima) < 2:
            return {
                'pattern_type': None,
                'waves': [],
                'confidence': 0.0
            }
        
        # Tentar identificar padrão de 5 ondas (impulso)
        impulse_waves = _identify_impulse_waves(data, maxima, minima)
        
        if impulse_waves and len(impulse_waves) >= 5:
            return {
                'pattern_type': 'IMPULSE',
                'waves': impulse_waves[:5],
                'confidence': 0.6,
                'wave_labels': ['1', '2', '3', '4', '5']
            }
        
        # Tentar identificar padrão de 3 ondas (correção)
        correction_waves = _identify_correction_waves(data, maxima, minima)
        
        if correction_waves and len(correction_waves) >= 3:
            return {
                'pattern_type': 'CORRECTION',
                'waves': correction_waves[:3],
                'confidence': 0.5,
                'wave_labels': ['A', 'B', 'C']
            }
        
        return {
            'pattern_type': None,
            'waves': [],
            'confidence': 0.0
        }
        
    except Exception as e:
        print(f"Erro ao analisar ondas de Elliott: {e}")
        return {
            'pattern_type': None,
            'waves': [],
            'confidence': 0.0
        }


def _identify_impulse_waves(data: pd.DataFrame, maxima: List[Dict], minima: List[Dict]) -> Optional[List[Dict]]:
    """
    Tenta identificar padrão de 5 ondas de impulso.
    """
    if len(maxima) < 3 or len(minima) < 2:
        return None
    
    # Ordenar por índice
    sorted_maxima = sorted(maxima, key=lambda x: x['index'])
    sorted_minima = sorted(minima, key=lambda x: x['index'])
    
    # Padrão de impulso: onda 1 (alta), onda 2 (baixa), onda 3 (alta maior), onda 4 (baixa), onda 5 (alta)
    # Simplificado: procurar sequência de altas e baixas alternadas
    waves = []
    
    # Pegar últimos pontos relevantes
    all_points = sorted_maxima + sorted_minima
    all_points.sort(key=lambda x: x['index'])
    
    if len(all_points) < 5:
        return None
    
    recent_points = all_points[-10:]  # Últimos 10 pontos
    
    # Verificar se há padrão de alternância e onda 3 é a mais forte
    for i in range(len(recent_points) - 4):
        points = recent_points[i:i+5]
        
        # Verificar se alternam entre máximo e mínimo
        is_alternating = True
        for j in range(len(points) - 1):
            if j % 2 == 0:  # Deve ser máximo
                if points[j] not in sorted_maxima:
                    is_alternating = False
                    break
            else:  # Deve ser mínimo
                if points[j] not in sorted_minima:
                    is_alternating = False
                    break
        
        if is_alternating:
            # Verificar se onda 3 (índice 2) é a mais forte
            wave3_price = points[2]['price']
            wave1_price = points[0]['price']
            wave5_price = points[4]['price']
            
            if wave3_price > wave1_price and wave3_price > wave5_price:
                # Formar ondas
                for idx, point in enumerate(points):
                    waves.append({
                        'wave': str(idx + 1),
                        'date': str(data.iloc[point['index']]['date']),
                        'price': point['price'],
                        'index': point['index']
                    })
                
                return waves
    
    return None


def _identify_correction_waves(data: pd.DataFrame, maxima: List[Dict], minima: List[Dict]) -> Optional[List[Dict]]:
    """
    Tenta identificar padrão de 3 ondas de correção (A, B, C).
    """
    if len(maxima) < 2 or len(minima) < 1:
        return None
    
    sorted_maxima = sorted(maxima, key=lambda x: x['index'])
    sorted_minima = sorted(minima, key=lambda x: x['index'])
    
    waves = []
    
    # Padrão ABC: A (baixa), B (alta menor), C (baixa mais profunda)
    all_points = sorted_maxima + sorted_minima
    all_points.sort(key=lambda x: x['index'])
    
    if len(all_points) < 3:
        return None
    
    recent_points = all_points[-6:]  # Últimos 6 pontos
    
    # Procurar padrão ABC
    for i in range(len(recent_points) - 2):
        points = recent_points[i:i+3]
        
        # Verificar se é mínimo, máximo, mínimo
        if (points[0] in sorted_minima and 
            points[1] in sorted_maxima and 
            points[2] in sorted_minima):
            
            wave_a_price = points[0]['price']
            wave_b_price = points[1]['price']
            wave_c_price = points[2]['price']
            
            # Verificar se C é mais baixo que A (correção completa)
            if wave_c_price < wave_a_price:
                waves.append({
                    'wave': 'A',
                    'date': str(data.iloc[points[0]['index']]['date']),
                    'price': wave_a_price,
                    'index': points[0]['index']
                })
                waves.append({
                    'wave': 'B',
                    'date': str(data.iloc[points[1]['index']]['date']),
                    'price': wave_b_price,
                    'index': points[1]['index']
                })
                waves.append({
                    'wave': 'C',
                    'date': str(data.iloc[points[2]['index']]['date']),
                    'price': wave_c_price,
                    'index': points[2]['index']
                })
                
                return waves
    
    return None


def get_advanced_analysis(ticker: str, period: str = "1y") -> Dict:
    """
    Função principal que retorna toda a análise avançada.
    
    Args:
        ticker: Símbolo do ativo
        period: Período dos dados históricos
    
    Returns:
        Dict com todas as análises: padrões, suporte/resistência, candlestick, Fibonacci, Elliott
    """
    data = get_historical_dataframe(ticker, period)
    
    if data.empty:
        return {
            'ticker': ticker,
            'period': period,
            'patterns': [],
            'support_levels': [],
            'resistance_levels': [],
            'candlestick_patterns': [],
            'fibonacci_levels': {},
            'elliott_waves': {
                'pattern_type': None,
                'waves': [],
                'confidence': 0.0
            }
        }
    
    # Converter date para string para JSON (se ainda não estiver convertido)
    if len(data) > 0:
        if data['date'].dtype != 'object':
            data['date'] = data['date'].dt.strftime('%Y-%m-%d')
        elif len(data) > 0 and hasattr(data['date'].iloc[0], 'strftime'):
            data['date'] = data['date'].dt.strftime('%Y-%m-%d')
    
    # Executar todas as análises
    support_resistance = identify_support_resistance(data)
    patterns = detect_chart_patterns(data)
    candlestick_patterns = detect_candlestick_patterns(data)
    fibonacci_levels = calculate_fibonacci_levels(data)
    elliott_waves = analyze_elliott_waves(data)
    
    return {
        'ticker': ticker,
        'period': period,
        'patterns': patterns,
        'support_levels': support_resistance['support_levels'],
        'resistance_levels': support_resistance['resistance_levels'],
        'candlestick_patterns': candlestick_patterns,
        'fibonacci_levels': fibonacci_levels,
        'elliott_waves': elliott_waves
    }

