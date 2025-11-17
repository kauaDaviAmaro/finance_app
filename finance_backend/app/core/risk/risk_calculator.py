"""
Módulo para cálculo de métricas de risco de portfólios.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime, timedelta

from app.core.market.data_fetcher import get_historical_data, get_company_fundamentals
from app.core.market.technical_analysis import get_technical_analysis
from app.core.market.ticker_utils import format_ticker


def _get_historical_returns_df(ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """
    Busca dados históricos e calcula retornos diários.
    
    Returns:
        DataFrame com colunas 'date' e 'returns', ou None se não houver dados
    """
    try:
        formatted_ticker = format_ticker(ticker)
        stock = yf.Ticker(formatted_ticker)
        data = stock.history(period=period)
        
        if data.empty or len(data) < 2:
            return None
        
        data.reset_index(inplace=True)
        data['returns'] = data['Close'].pct_change().dropna()
        data = data[['Date', 'Close', 'returns']].dropna()
        
        if len(data) < 2:
            return None
        
        return data
    except Exception as e:
        print(f"Erro ao buscar retornos históricos para {ticker}: {e}")
        return None


def _get_benchmark_returns(benchmark: str = "^BVSP", period: str = "1y") -> Optional[pd.Series]:
    """
    Busca retornos do benchmark (IBOVESPA por padrão).
    
    Returns:
        Series com retornos diários, ou None se não houver dados
    """
    try:
        stock = yf.Ticker(benchmark)
        data = stock.history(period=period)
        
        if data.empty or len(data) < 2:
            return None
        
        returns = data['Close'].pct_change().dropna()
        return returns
    except Exception as e:
        print(f"Erro ao buscar retornos do benchmark {benchmark}: {e}")
        return None


def calculate_var(
    portfolio_positions: List[Dict[str, Any]],
    confidence_level: float = 0.95,
    horizon_days: int = 1,
    method: str = "historical"
) -> Dict[str, Any]:
    """
    Calcula Value at Risk (VaR) do portfólio.
    
    Args:
        portfolio_positions: Lista de posições com 'ticker', 'quantity', 'purchase_price', 'current_price'
        confidence_level: Nível de confiança (0.95 para 95%, 0.99 para 99%)
        horizon_days: Horizonte de tempo em dias (1, 7, 30)
        method: Método de cálculo ('historical' ou 'parametric')
    
    Returns:
        Dict com 'var_value', 'var_percentage', 'method', 'confidence_level', 'horizon_days'
    """
    if not portfolio_positions:
        return {
            'var_value': None,
            'var_percentage': None,
            'method': method,
            'confidence_level': confidence_level,
            'horizon_days': horizon_days,
            'error': 'Portfolio vazio'
        }
    
    # Calcular valores atuais das posições
    total_value = Decimal('0')
    position_values = []
    
    for pos in portfolio_positions:
        if not pos.get('current_price') or not pos.get('quantity'):
            continue
        
        current_price = Decimal(str(pos['current_price']))
        quantity = int(pos['quantity'])
        position_value = current_price * quantity
        total_value += position_value
        position_values.append({
            'ticker': pos['ticker'],
            'value': float(position_value),
            'weight': 0.0  # Será calculado depois
        })
    
    if total_value == 0:
        return {
            'var_value': None,
            'var_percentage': None,
            'method': method,
            'confidence_level': confidence_level,
            'horizon_days': horizon_days,
            'error': 'Valor total do portfólio é zero'
        }
    
    # Calcular pesos
    for pos_val in position_values:
        pos_val['weight'] = pos_val['value'] / float(total_value)
    
    # Buscar retornos históricos de cada posição
    returns_data = {}
    min_length = float('inf')
    
    for pos_val in position_values:
        ticker = pos_val['ticker']
        returns_df = _get_historical_returns_df(ticker)
        
        if returns_df is not None and len(returns_df) > 0:
            returns_data[ticker] = returns_df['returns'].values
            min_length = min(min_length, len(returns_data[ticker]))
    
    if not returns_data or min_length < 30:
        return {
            'var_value': None,
            'var_percentage': None,
            'method': method,
            'confidence_level': confidence_level,
            'horizon_days': horizon_days,
            'error': 'Dados históricos insuficientes'
        }
    
    # Alinhar tamanho dos arrays de retornos
    aligned_returns = {}
    for ticker, returns in returns_data.items():
        if len(returns) >= min_length:
            aligned_returns[ticker] = returns[-int(min_length):]
    
    if method == "historical":
        # Método histórico: simular retornos do portfólio
        portfolio_returns = []
        
        for i in range(min_length):
            portfolio_return = 0.0
            for pos_val in position_values:
                ticker = pos_val['ticker']
                if ticker in aligned_returns:
                    portfolio_return += pos_val['weight'] * aligned_returns[ticker][i]
            portfolio_returns.append(portfolio_return)
        
        # Ajustar para horizonte de tempo
        if horizon_days > 1:
            portfolio_returns = [r * np.sqrt(horizon_days) for r in portfolio_returns]
        
        # Calcular VaR como percentil
        var_percentage = np.percentile(portfolio_returns, (1 - confidence_level) * 100)
        var_value = abs(float(total_value) * var_percentage)
        
    else:  # parametric
        # Método paramétrico: usar média e desvio padrão
        portfolio_returns = []
        
        for i in range(min_length):
            portfolio_return = 0.0
            for pos_val in position_values:
                ticker = pos_val['ticker']
                if ticker in aligned_returns:
                    portfolio_return += pos_val['weight'] * aligned_returns[ticker][i]
            portfolio_returns.append(portfolio_return)
        
        mean_return = np.mean(portfolio_returns)
        std_return = np.std(portfolio_returns)
        
        # Ajustar para horizonte de tempo
        if horizon_days > 1:
            mean_return = mean_return * horizon_days
            std_return = std_return * np.sqrt(horizon_days)
        
        # Z-score para nível de confiança
        z_score = stats.norm.ppf(1 - confidence_level)
        var_percentage = abs(mean_return + z_score * std_return)
        var_value = abs(float(total_value) * var_percentage)
    
    return {
        'var_value': round(var_value, 2),
        'var_percentage': round(abs(var_percentage) * 100, 2),
        'method': method,
        'confidence_level': confidence_level,
        'horizon_days': horizon_days
    }


def calculate_drawdown(
    portfolio_positions: List[Dict[str, Any]],
    period: str = "1y"
) -> Dict[str, Any]:
    """
    Calcula drawdown máximo e atual do portfólio.
    
    Args:
        portfolio_positions: Lista de posições com 'ticker', 'quantity', 'purchase_price', 'current_price'
        period: Período para análise histórica
    
    Returns:
        Dict com 'max_drawdown', 'current_drawdown', 'max_drawdown_date', 'recovery_days', 'drawdown_history'
    """
    if not portfolio_positions:
        return {
            'max_drawdown': None,
            'current_drawdown': None,
            'max_drawdown_date': None,
            'recovery_days': None,
            'drawdown_history': []
        }
    
    # Calcular valor do portfólio ao longo do tempo
    portfolio_values = []
    dates = []
    
    # Buscar dados históricos de todas as posições
    historical_data = {}
    for pos in portfolio_positions:
        ticker = pos['ticker']
        try:
            data = _get_historical_returns_df(ticker, period)
            if data is not None:
                historical_data[ticker] = data
        except Exception:
            continue
    
    if not historical_data:
        return {
            'max_drawdown': None,
            'current_drawdown': None,
            'max_drawdown_date': None,
            'recovery_days': None,
            'drawdown_history': []
        }
    
    # Encontrar datas comuns
    common_dates = None
    for ticker, data in historical_data.items():
        ticker_dates = set(data['Date'].dt.date)
        if common_dates is None:
            common_dates = ticker_dates
        else:
            common_dates = common_dates.intersection(ticker_dates)
    
    if not common_dates:
        return {
            'max_drawdown': None,
            'current_drawdown': None,
            'max_drawdown_date': None,
            'recovery_days': None,
            'drawdown_history': []
        }
    
    common_dates = sorted(list(common_dates))
    
    # Calcular valor do portfólio para cada data
    for date in common_dates:
        portfolio_value = Decimal('0')
        for pos in portfolio_positions:
            ticker = pos['ticker']
            quantity = int(pos.get('quantity', 0))
            
            if ticker in historical_data:
                data = historical_data[ticker]
                date_data = data[data['Date'].dt.date == date]
                if not date_data.empty:
                    price = Decimal(str(date_data['Close'].iloc[0]))
                    portfolio_value += price * quantity
        
        if portfolio_value > 0:
            portfolio_values.append(float(portfolio_value))
            dates.append(date)
    
    if len(portfolio_values) < 2:
        return {
            'max_drawdown': None,
            'current_drawdown': None,
            'max_drawdown_date': None,
            'recovery_days': None,
            'drawdown_history': []
        }
    
    # Calcular drawdown
    peak = portfolio_values[0]
    max_drawdown = 0.0
    max_drawdown_date = None
    drawdown_history = []
    current_drawdown = 0.0
    
    for i, value in enumerate(portfolio_values):
        if value > peak:
            peak = value
        
        drawdown = (peak - value) / peak if peak > 0 else 0.0
        drawdown_history.append({
            'date': dates[i].isoformat() if isinstance(dates[i], datetime) else str(dates[i]),
            'value': portfolio_values[i],
            'drawdown': round(drawdown * 100, 2)
        })
        
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            max_drawdown_date = dates[i]
        
        if i == len(portfolio_values) - 1:
            current_drawdown = drawdown
    
    # Calcular dias de recuperação (desde o último pico)
    recovery_days = None
    if current_drawdown > 0:
        last_peak_idx = None
        for i in range(len(portfolio_values) - 1, -1, -1):
            if portfolio_values[i] >= peak:
                last_peak_idx = i
                break
        
        if last_peak_idx is not None and last_peak_idx < len(portfolio_values) - 1:
            recovery_days = len(portfolio_values) - 1 - last_peak_idx
    
    return {
        'max_drawdown': round(max_drawdown * 100, 2),
        'current_drawdown': round(current_drawdown * 100, 2),
        'max_drawdown_date': max_drawdown_date.isoformat() if max_drawdown_date else None,
        'recovery_days': recovery_days,
        'drawdown_history': drawdown_history[-252:] if len(drawdown_history) > 252 else drawdown_history  # Últimos 252 dias
    }


def calculate_portfolio_beta(
    portfolio_positions: List[Dict[str, Any]],
    benchmark: str = "^BVSP",
    period: str = "1y"
) -> Dict[str, Any]:
    """
    Calcula beta do portfólio em relação ao benchmark (IBOVESPA).
    
    Args:
        portfolio_positions: Lista de posições
        benchmark: Ticker do benchmark (padrão: ^BVSP - IBOVESPA)
        period: Período para análise
    
    Returns:
        Dict com 'portfolio_beta', 'position_betas', 'benchmark'
    """
    if not portfolio_positions:
        return {
            'portfolio_beta': None,
            'position_betas': [],
            'benchmark': benchmark
        }
    
    # Buscar retornos do benchmark
    benchmark_returns = _get_benchmark_returns(benchmark, period)
    if benchmark_returns is None or len(benchmark_returns) < 30:
        return {
            'portfolio_beta': None,
            'position_betas': [],
            'benchmark': benchmark,
            'error': 'Dados do benchmark insuficientes'
        }
    
    # Calcular valores e pesos das posições
    total_value = Decimal('0')
    position_data = []
    
    for pos in portfolio_positions:
        if not pos.get('current_price') or not pos.get('quantity'):
            continue
        
        current_price = Decimal(str(pos['current_price']))
        quantity = int(pos['quantity'])
        position_value = current_price * quantity
        total_value += position_value
        
        position_data.append({
            'ticker': pos['ticker'],
            'value': float(position_value),
            'weight': 0.0
        })
    
    if total_value == 0:
        return {
            'portfolio_beta': None,
            'position_betas': [],
            'benchmark': benchmark
        }
    
    # Calcular pesos
    for pos_data in position_data:
        pos_data['weight'] = pos_data['value'] / float(total_value)
    
    # Calcular beta de cada posição
    position_betas = []
    portfolio_beta = 0.0
    
    for pos_data in position_data:
        ticker = pos_data['ticker']
        returns_df = _get_historical_returns_df(ticker, period)
        
        if returns_df is None or len(returns_df) < 30:
            position_betas.append({
                'ticker': ticker,
                'beta': None,
                'error': 'Dados insuficientes'
            })
            continue
        
        asset_returns = returns_df['returns'].values
        
        # Alinhar tamanhos
        min_len = min(len(asset_returns), len(benchmark_returns))
        asset_returns = asset_returns[-min_len:]
        benchmark_returns_aligned = benchmark_returns.values[-min_len:]
        
        # Calcular beta usando covariância e variância
        if len(asset_returns) < 30:
            position_betas.append({
                'ticker': ticker,
                'beta': None,
                'error': 'Dados insuficientes após alinhamento'
            })
            continue
        
        covariance = np.cov(asset_returns, benchmark_returns_aligned)[0][1]
        benchmark_variance = np.var(benchmark_returns_aligned)
        
        if benchmark_variance == 0:
            beta = None
        else:
            beta = covariance / benchmark_variance
        
        if beta is not None:
            position_betas.append({
                'ticker': ticker,
                'beta': round(beta, 4)
            })
            # Contribuição ponderada ao beta do portfólio
            portfolio_beta += pos_data['weight'] * beta
    
    return {
        'portfolio_beta': round(portfolio_beta, 4) if portfolio_beta else None,
        'position_betas': position_betas,
        'benchmark': benchmark
    }


def calculate_volatility(
    portfolio_positions: List[Dict[str, Any]],
    period: str = "1y",
    annualized: bool = True
) -> Dict[str, Any]:
    """
    Calcula volatilidade do portfólio (desvio padrão dos retornos).
    
    Args:
        portfolio_positions: Lista de posições
        period: Período para análise
        annualized: Se True, anualiza a volatilidade (multiplica por sqrt(252))
    
    Returns:
        Dict com 'portfolio_volatility', 'position_volatilities'
    """
    if not portfolio_positions:
        return {
            'portfolio_volatility': None,
            'position_volatilities': []
        }
    
    # Calcular valores e pesos
    total_value = Decimal('0')
    position_data = []
    
    for pos in portfolio_positions:
        if not pos.get('current_price') or not pos.get('quantity'):
            continue
        
        current_price = Decimal(str(pos['current_price']))
        quantity = int(pos['quantity'])
        position_value = current_price * quantity
        total_value += position_value
        
        position_data.append({
            'ticker': pos['ticker'],
            'value': float(position_value),
            'weight': 0.0
        })
    
    if total_value == 0:
        return {
            'portfolio_volatility': None,
            'position_volatilities': []
        }
    
    # Calcular pesos
    for pos_data in position_data:
        pos_data['weight'] = pos_data['value'] / float(total_value)
    
    # Calcular volatilidade de cada posição e retornos do portfólio
    position_volatilities = []
    portfolio_returns = None
    
    for pos_data in position_data:
        ticker = pos_data['ticker']
        returns_df = _get_historical_returns_df(ticker, period)
        
        if returns_df is None or len(returns_df) < 30:
            position_volatilities.append({
                'ticker': ticker,
                'volatility': None,
                'error': 'Dados insuficientes'
            })
            continue
        
        returns = returns_df['returns'].values
        
        # Volatilidade da posição
        volatility = np.std(returns)
        if annualized:
            volatility = volatility * np.sqrt(252)
        
        position_volatilities.append({
            'ticker': ticker,
            'volatility': round(volatility * 100, 2)  # Em porcentagem
        })
        
        # Acumular retornos do portfólio (ponderados)
        if portfolio_returns is None:
            portfolio_returns = returns * pos_data['weight']
        else:
            min_len = min(len(portfolio_returns), len(returns))
            portfolio_returns = portfolio_returns[:min_len] + returns[:min_len] * pos_data['weight']
    
    # Calcular volatilidade do portfólio
    portfolio_volatility = None
    if portfolio_returns is not None and len(portfolio_returns) >= 30:
        portfolio_volatility = np.std(portfolio_returns)
        if annualized:
            portfolio_volatility = portfolio_volatility * np.sqrt(252)
        portfolio_volatility = round(portfolio_volatility * 100, 2)  # Em porcentagem
    
    return {
        'portfolio_volatility': portfolio_volatility,
        'position_volatilities': position_volatilities
    }


def calculate_diversification_metrics(
    portfolio_positions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calcula métricas de diversificação do portfólio.
    
    Args:
        portfolio_positions: Lista de posições
    
    Returns:
        Dict com 'herfindahl_index', 'concentration_by_ticker', 'sector_diversification', 
        'effective_positions', 'warnings'
    """
    if not portfolio_positions:
        return {
            'herfindahl_index': None,
            'concentration_by_ticker': [],
            'sector_diversification': [],
            'effective_positions': None,
            'warnings': []
        }
    
    # Calcular valores e pesos
    total_value = Decimal('0')
    position_data = []
    
    for pos in portfolio_positions:
        if not pos.get('current_price') or not pos.get('quantity'):
            continue
        
        current_price = Decimal(str(pos['current_price']))
        quantity = int(pos['quantity'])
        position_value = current_price * quantity
        total_value += position_value
        
        position_data.append({
            'ticker': pos['ticker'],
            'value': float(position_value),
            'weight': 0.0
        })
    
    if total_value == 0:
        return {
            'herfindahl_index': None,
            'concentration_by_ticker': [],
            'sector_diversification': [],
            'effective_positions': None,
            'warnings': []
        }
    
    # Calcular pesos
    for pos_data in position_data:
        pos_data['weight'] = pos_data['value'] / float(total_value)
    
    # Calcular Índice de Herfindahl-Hirschman (HHI)
    hhi = sum(w['weight'] ** 2 for w in position_data)
    
    # Número efetivo de posições
    effective_positions = 1 / hhi if hhi > 0 else len(position_data)
    
    # Concentração por ticker
    concentration_by_ticker = sorted(
        [{'ticker': w['ticker'], 'weight': round(w['weight'] * 100, 2)} for w in position_data],
        key=lambda x: x['weight'],
        reverse=True
    )
    
    # Diversificação por setor
    sector_data = {}
    warnings = []
    
    for pos_data in position_data:
        ticker = pos_data['ticker']
        try:
            fundamentals = get_company_fundamentals(ticker)
            sector = fundamentals.get('sector')
            industry = fundamentals.get('industry')
            
            if sector:
                if sector not in sector_data:
                    sector_data[sector] = {'weight': 0.0, 'industries': set(), 'tickers': []}
                sector_data[sector]['weight'] += pos_data['weight']
                sector_data[sector]['tickers'].append(ticker)
                if industry:
                    sector_data[sector]['industries'].add(industry)
        except Exception:
            # Se não conseguir buscar setor, continuar
            pass
    
    # Converter set para lista para JSON
    sector_diversification = []
    for sector, data in sector_data.items():
        sector_diversification.append({
            'sector': sector,
            'weight': round(data['weight'] * 100, 2),
            'industries': list(data['industries']),
            'tickers': data['tickers']
        })
    
    sector_diversification = sorted(sector_diversification, key=lambda x: x['weight'], reverse=True)
    
    # Gerar avisos
    for ticker_concentration in concentration_by_ticker:
        if ticker_concentration['weight'] > 20:
            warnings.append(
                f"Concentração alta em {ticker_concentration['ticker']}: "
                f"{ticker_concentration['weight']:.2f}% do portfólio"
            )
    
    if hhi > 0.25:  # HHI > 0.25 indica alta concentração
        warnings.append(f"Índice de Herfindahl alto ({hhi:.3f}), indicando baixa diversificação")
    
    return {
        'herfindahl_index': round(hhi, 4),
        'concentration_by_ticker': concentration_by_ticker,
        'sector_diversification': sector_diversification,
        'effective_positions': round(effective_positions, 2),
        'warnings': warnings
    }


def suggest_stop_loss_take_profit(
    ticker: str,
    current_price: float,
    method: str = "atr"
) -> Dict[str, Any]:
    """
    Sugere níveis de stop loss e take profit.
    
    Args:
        ticker: Ticker do ativo
        current_price: Preço atual
        method: Método ('atr', 'percentage', ou 'both')
    
    Returns:
        Dict com 'stop_loss', 'take_profit', 'stop_loss_percentage', 'take_profit_percentage', 'method'
    """
    suggestions = {
        'stop_loss': None,
        'take_profit': None,
        'stop_loss_percentage': None,
        'take_profit_percentage': None,
        'method': method
    }
    
    try:
        # Buscar análise técnica para obter ATR
        technical_data = get_technical_analysis(ticker, period="3mo")
        
        if technical_data and len(technical_data) > 0:
            # Pegar último ATR
            last_data = technical_data[-1]
            atr = last_data.get('ATRr_14')
            
            if atr and method in ['atr', 'both']:
                # Stop Loss: preço atual - (2 × ATR)
                # Take Profit: preço atual + (3 × ATR)
                stop_loss = current_price - (2 * atr)
                take_profit = current_price + (3 * atr)
                
                suggestions['stop_loss'] = round(max(0, stop_loss), 2)
                suggestions['take_profit'] = round(take_profit, 2)
                suggestions['stop_loss_percentage'] = round(((stop_loss - current_price) / current_price) * 100, 2)
                suggestions['take_profit_percentage'] = round(((take_profit - current_price) / current_price) * 100, 2)
        
        # Método baseado em percentual
        if method in ['percentage', 'both']:
            # Valores padrão: -5% stop loss, +10% take profit
            stop_loss_pct = -5.0
            take_profit_pct = 10.0
            
            # Ajustar baseado em volatilidade se disponível
            returns_df = _get_historical_returns_df(ticker, period="3mo")
            if returns_df is not None and len(returns_df) >= 30:
                volatility = np.std(returns_df['returns'].values) * np.sqrt(252) * 100  # Volatilidade anualizada em %
                
                # Ajustar stop loss baseado em volatilidade (mais volátil = stop loss maior)
                if volatility > 30:
                    stop_loss_pct = -7.0
                    take_profit_pct = 15.0
                elif volatility > 20:
                    stop_loss_pct = -6.0
                    take_profit_pct = 12.0
            
            if not suggestions['stop_loss'] or method == 'percentage':
                suggestions['stop_loss'] = round(current_price * (1 + stop_loss_pct / 100), 2)
                suggestions['stop_loss_percentage'] = stop_loss_pct
            
            if not suggestions['take_profit'] or method == 'percentage':
                suggestions['take_profit'] = round(current_price * (1 + take_profit_pct / 100), 2)
                suggestions['take_profit_percentage'] = take_profit_pct
    
    except Exception as e:
        print(f"Erro ao calcular stop loss/take profit para {ticker}: {e}")
        # Valores padrão em caso de erro
        if not suggestions['stop_loss']:
            suggestions['stop_loss'] = round(current_price * 0.95, 2)
            suggestions['stop_loss_percentage'] = -5.0
        if not suggestions['take_profit']:
            suggestions['take_profit'] = round(current_price * 1.10, 2)
            suggestions['take_profit_percentage'] = 10.0
    
    return suggestions


def analyze_position_risk(
    position: Dict[str, Any],
    portfolio_positions: List[Dict[str, Any]],
    benchmark: str = "^BVSP"
) -> Dict[str, Any]:
    """
    Analisa risco de uma posição individual.
    
    Args:
        position: Posição individual com 'ticker', 'quantity', 'purchase_price', 'current_price'
        portfolio_positions: Todas as posições do portfólio (para calcular correlação)
        benchmark: Benchmark para cálculo de beta
    
    Returns:
        Dict com análise completa de risco da posição
    """
    ticker = position.get('ticker')
    current_price = position.get('current_price')
    
    if not ticker or not current_price:
        return {
            'ticker': ticker,
            'error': 'Dados da posição incompletos'
        }
    
    # Calcular VaR individual
    var_result = calculate_var([position], confidence_level=0.95, horizon_days=1)
    
    # Calcular beta individual
    beta_result = calculate_portfolio_beta([position], benchmark=benchmark)
    position_beta = beta_result.get('portfolio_beta')
    
    # Calcular volatilidade individual
    volatility_result = calculate_volatility([position])
    position_volatility = volatility_result.get('portfolio_volatility')
    
    # Calcular correlação com outras posições
    correlations = []
    position_returns_df = _get_historical_returns_df(ticker)
    
    if position_returns_df is not None:
        position_returns = position_returns_df['returns'].values
        
        for other_pos in portfolio_positions:
            other_ticker = other_pos.get('ticker')
            if other_ticker == ticker:
                continue
            
            other_returns_df = _get_historical_returns_df(other_ticker)
            if other_returns_df is not None:
                other_returns = other_returns_df['returns'].values
                
                # Alinhar tamanhos
                min_len = min(len(position_returns), len(other_returns))
                if min_len >= 30:
                    pos_ret_aligned = position_returns[-min_len:]
                    other_ret_aligned = other_returns[-min_len:]
                    
                    correlation = np.corrcoef(pos_ret_aligned, other_ret_aligned)[0][1]
                    if not np.isnan(correlation):
                        correlations.append({
                            'ticker': other_ticker,
                            'correlation': round(correlation, 4)
                        })
    
    # Calcular contribuição ao risco do portfólio
    portfolio_value = sum(
        Decimal(str(p.get('current_price', 0))) * int(p.get('quantity', 0))
        for p in portfolio_positions
    )
    position_value = Decimal(str(current_price)) * int(position.get('quantity', 0))
    portfolio_weight = float(position_value / portfolio_value) if portfolio_value > 0 else 0.0
    
    # Sugestões de stop loss/take profit
    stop_loss_tp = suggest_stop_loss_take_profit(ticker, float(current_price), method='both')
    
    return {
        'ticker': ticker,
        'var': var_result.get('var_value'),
        'var_percentage': var_result.get('var_percentage'),
        'beta': position_beta,
        'volatility': position_volatility,
        'portfolio_weight': round(portfolio_weight * 100, 2),
        'correlations': sorted(correlations, key=lambda x: abs(x['correlation']), reverse=True)[:5],  # Top 5
        'stop_loss': stop_loss_tp.get('stop_loss'),
        'take_profit': stop_loss_tp.get('take_profit'),
        'stop_loss_percentage': stop_loss_tp.get('stop_loss_percentage'),
        'take_profit_percentage': stop_loss_tp.get('take_profit_percentage')
    }

