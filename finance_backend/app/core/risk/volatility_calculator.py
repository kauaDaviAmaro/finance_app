"""
Cálculo de volatilidade para portfólios.
"""
import numpy as np
from typing import Dict, List, Any
from decimal import Decimal

from .utils import get_historical_returns_df


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
        returns_df = get_historical_returns_df(ticker, period)
        
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

