"""
Módulo para buscar dados básicos de mercado (históricos e fundamentais).
"""
import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional, Tuple

from app.core.market.ticker_utils import format_ticker
from app.core.redis_cache import get_cached_dataframe, set_cached_dataframe, get_cached_dict, set_cached_dict


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


def get_historical_data(ticker: str, period: str = "1y") -> list[dict]:
    """
    Busca dados históricos de um ticker, formatando-o se for da B3.
    Usa cache Redis para evitar múltiplas requisições ao yfinance.
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
    
    if data.empty:
        return []

    data = data.copy()
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


def calculate_quality_score(
    roe: Optional[float],
    roa: Optional[float],
    net_margin: Optional[float],
    debt_to_equity: Optional[float]
) -> Tuple[Optional[float], Dict[str, Optional[float]]]:
    """
    Calcula o score de qualidade (0-100) baseado em métricas fundamentais.
    
    Args:
        roe: Return on Equity (em decimal, ex: 0.15 = 15%)
        roa: Return on Assets (em decimal, ex: 0.10 = 10%)
        net_margin: Net Profit Margin (em decimal, ex: 0.12 = 12%)
        debt_to_equity: Debt to Equity ratio (em decimal, ex: 0.50 = 50%)
    
    Returns:
        Tuple com (quality_score, dict com métricas normalizadas)
    """
    # Pesos originais
    weights = {
        'roe': 0.30,
        'roa': 0.25,
        'net_margin': 0.25,
        'debt_to_equity': 0.20
    }
    
    # Normalizar métricas para escala 0-100
    normalized = {}
    
    # ROE: 0-30% → 0-100 (valores acima de 30% = 100)
    if roe is not None and not pd.isna(roe):
        roe_pct = roe * 100  # Converter para porcentagem
        normalized['roe'] = min(100, max(0, (roe_pct / 30) * 100))
    else:
        normalized['roe'] = None
    
    # ROA: 0-15% → 0-100 (valores acima de 15% = 100)
    if roa is not None and not pd.isna(roa):
        roa_pct = roa * 100  # Converter para porcentagem
        normalized['roa'] = min(100, max(0, (roa_pct / 15) * 100))
    else:
        normalized['roa'] = None
    
    # Margem Líquida: 0-20% → 0-100 (valores acima de 20% = 100)
    if net_margin is not None and not pd.isna(net_margin):
        margin_pct = net_margin * 100  # Converter para porcentagem
        normalized['net_margin'] = min(100, max(0, (margin_pct / 20) * 100))
    else:
        normalized['net_margin'] = None
    
    # Dívida/Patrimônio: 0-100% → 100-0 (invertido, menor é melhor)
    if debt_to_equity is not None and not pd.isna(debt_to_equity):
        debt_eq_pct = debt_to_equity * 100  # Converter para porcentagem
        # Inverter: 0% dívida = 100 pontos, 100%+ dívida = 0 pontos
        normalized['debt_to_equity'] = max(0, min(100, 100 - debt_eq_pct))
    else:
        normalized['debt_to_equity'] = None
    
    # Calcular score apenas com métricas disponíveis
    available_metrics = {k: v for k, v in normalized.items() if v is not None}
    
    if not available_metrics:
        return None, normalized
    
    # Ajustar pesos proporcionalmente se alguma métrica estiver ausente
    total_weight = sum(weights[k] for k in available_metrics.keys())
    if total_weight == 0:
        return None, normalized
    
    # Calcular média ponderada
    score = 0.0
    for metric, value in available_metrics.items():
        adjusted_weight = weights[metric] / total_weight
        score += value * adjusted_weight
    
    return round(score, 2), normalized


def _fetch_fundamentals_from_yfinance(ticker: str) -> Dict[str, Any]:
    """
    Busca dados fundamentalistas diretamente do yfinance (sem cache).
    """
    formatted_ticker = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(formatted_ticker)
        info = stock.info
        return info
    except Exception as e:
        print(f"Erro ao buscar fundamentos do ticker {formatted_ticker}: {e}")
        raise


def get_company_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Busca dados fundamentalistas de uma empresa usando yfinance.
    Retorna: P/E, P/VP, Dividend Yield, Beta, Setor, Indústria, Market Cap,
    ROE, ROA, Margem Líquida, Dívida/Patrimônio, EV/EBITDA, P/EBIT e Quality Score.
    Usa cache Redis para evitar múltiplas requisições ao yfinance.
    """
    formatted_ticker = format_ticker(ticker)
    cache_key = f"yfinance:fundamentals:{formatted_ticker}"
    
    # 1. TENTA BUSCAR NO CACHE
    cached_info = get_cached_dict(cache_key)
    
    # 2. NÃO ACHOU NO CACHE? BUSCA NA API (E SALVA)
    if cached_info is None:
        print(f"📡 CACHE MISS: Fundamentos do ticker {formatted_ticker}. Buscando no yfinance...")
        info = _fetch_fundamentals_from_yfinance(ticker)
        
        if info:
            set_cached_dict(cache_key, info)
    else:
        info = cached_info
    
    try:
        # Extrair dados básicos, tratando valores None ou indisponíveis
        fundamentals = {
            'pe_ratio': info.get('trailingPE') or info.get('forwardPE'),
            'pb_ratio': info.get('priceToBook'),
            'dividend_yield': info.get('dividendYield'),
            'beta': info.get('beta'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'market_cap': info.get('marketCap')
        }
        
        # Extrair EV/EBITDA
        ev_ebitda = info.get('enterpriseToEbitda')
        if ev_ebitda is not None and (pd.isna(ev_ebitda) or ev_ebitda == 0):
            ev_ebitda = None
        fundamentals['ev_ebitda'] = ev_ebitda
        
        # Extrair/calcular P/EBIT
        # Tentar primeiro buscar diretamente (se disponível)
        pebit_ratio = None
        
        # Tentar calcular P/EBIT: currentPrice / (ebit / sharesOutstanding)
        current_price = info.get('currentPrice')
        ebit = info.get('ebit')
        shares_outstanding = info.get('sharesOutstanding')
        
        if current_price and ebit and shares_outstanding:
            if not pd.isna(current_price) and not pd.isna(ebit) and not pd.isna(shares_outstanding):
                if ebit != 0 and shares_outstanding != 0:
                    ebit_per_share = ebit / shares_outstanding
                    if ebit_per_share != 0:
                        pebit_ratio = current_price / ebit_per_share
        
        # Validar P/EBIT calculado
        if pebit_ratio is not None and (pd.isna(pebit_ratio) or pebit_ratio <= 0):
            pebit_ratio = None
        
        fundamentals['pebit_ratio'] = pebit_ratio
        
        # Extrair métricas de qualidade
        roe = info.get('returnOnEquity')
        roa = info.get('returnOnAssets')
        net_margin = info.get('profitMargins')
        debt_to_equity = info.get('debtToEquity')
        
        # Converter para None se não existir ou for inválido
        for key, value in fundamentals.items():
            if value is None or (isinstance(value, float) and (pd.isna(value) or value == 0)):
                fundamentals[key] = None
        
        # Tratar métricas de qualidade
        if roe is not None and (pd.isna(roe) or roe == 0):
            roe = None
        if roa is not None and (pd.isna(roa) or roa == 0):
            roa = None
        if net_margin is not None and (pd.isna(net_margin) or net_margin == 0):
            net_margin = None
        if debt_to_equity is not None and (pd.isna(debt_to_equity) or debt_to_equity < 0):
            debt_to_equity = None
        
        # Adicionar métricas de qualidade ao dict
        fundamentals['roe'] = roe
        fundamentals['roa'] = roa
        fundamentals['net_margin'] = net_margin
        fundamentals['debt_to_equity'] = debt_to_equity
        
        # Calcular score de qualidade
        quality_score, _ = calculate_quality_score(roe, roa, net_margin, debt_to_equity)
        fundamentals['quality_score'] = quality_score
        
        return fundamentals
        
    except Exception as e:
        print(f"Erro ao buscar fundamentos do ticker {formatted_ticker}: {e}")
        raise


def _format_financial_statement(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Converte um DataFrame de demonstração financeira em formato JSON estruturado.
    
    Args:
        df: DataFrame do pandas com índices (nomes das contas) e colunas (períodos)
    
    Returns:
        Dict com 'periods' (lista de períodos) e 'data' (lista de linhas com conta e valores)
    """
    if df.empty:
        return {'periods': [], 'data': []}
    
    # Converter colunas (períodos) para strings no formato YYYY-MM-DD
    periods = [str(col).split()[0] if isinstance(col, pd.Timestamp) else str(col) for col in df.columns]
    
    # Ordenar períodos do mais recente para o mais antigo
    try:
        # Tentar ordenar por data se possível
        period_dates = [pd.to_datetime(p) for p in periods]
        sorted_indices = sorted(range(len(period_dates)), key=lambda i: period_dates[i], reverse=True)
        periods = [periods[i] for i in sorted_indices]
    except (ValueError, TypeError):
        # Se não conseguir ordenar, manter ordem original
        periods = list(periods)
    
    # Converter DataFrame para lista de dicionários
    data = []
    for account_name in df.index:
        row = {'account': str(account_name)}
        values = {}
        # Reordenar colunas do DataFrame se necessário para corresponder aos períodos ordenados
        for period in periods:
            # Tentar encontrar a coluna correspondente ao período
            matching_col = None
            for col in df.columns:
                col_str = str(col).split()[0] if isinstance(col, pd.Timestamp) else str(col)
                if col_str == period:
                    matching_col = col
                    break
            
            if matching_col is not None:
                value = df.loc[account_name, matching_col]
                # Converter NaN para None
                if pd.isna(value):
                    values[period] = None
                else:
                    # Converter para float (pode ser int64, float64, etc)
                    values[period] = float(value)
            else:
                values[period] = None
        row['values'] = values
        data.append(row)
    
    return {'periods': periods, 'data': data}


def get_income_statement(ticker: str) -> Dict[str, Any]:
    """
    Busca a Demonstração do Resultado do Exercício (DRE / Income Statement) de uma empresa.
    
    Args:
        ticker: Símbolo do ativo
    
    Returns:
        Dict com 'periods' (lista de períodos) e 'data' (lista de linhas da DRE)
    """
    formatted_ticker = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(formatted_ticker)
        financials = stock.financials
        
        if financials.empty:
            return {'periods': [], 'data': []}
        
        return _format_financial_statement(financials)
        
    except Exception as e:
        print(f"Erro ao buscar DRE do ticker {formatted_ticker}: {e}")
        raise


def get_balance_sheet(ticker: str) -> Dict[str, Any]:
    """
    Busca o Balanço Patrimonial (Balance Sheet) de uma empresa.
    
    Args:
        ticker: Símbolo do ativo
    
    Returns:
        Dict com 'periods' (lista de períodos) e 'data' (lista de linhas do balanço)
    """
    formatted_ticker = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(formatted_ticker)
        balance_sheet = stock.balance_sheet
        
        if balance_sheet.empty:
            return {'periods': [], 'data': []}
        
        return _format_financial_statement(balance_sheet)
        
    except Exception as e:
        print(f"Erro ao buscar balanço patrimonial do ticker {formatted_ticker}: {e}")
        raise


def get_cashflow(ticker: str) -> Dict[str, Any]:
    """
    Busca a Demonstração dos Fluxos de Caixa (Cash Flow Statement) de uma empresa.
    
    Args:
        ticker: Símbolo do ativo
    
    Returns:
        Dict com 'periods' (lista de períodos) e 'data' (lista de linhas do fluxo de caixa)
    """
    formatted_ticker = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(formatted_ticker)
        cashflow = stock.cashflow
        
        if cashflow.empty:
            return {'periods': [], 'data': []}
        
        return _format_financial_statement(cashflow)
        
    except Exception as e:
        print(f"Erro ao buscar fluxo de caixa do ticker {formatted_ticker}: {e}")
        raise

