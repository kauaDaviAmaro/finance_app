"""
Cálculo de beta para portfólios.
"""
import numpy as np
from typing import Dict, List, Any
from decimal import Decimal

from .utils import get_historical_returns_df, get_benchmark_returns


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
    benchmark_returns = get_benchmark_returns(benchmark, period)
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
        returns_df = get_historical_returns_df(ticker, period)
        
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

