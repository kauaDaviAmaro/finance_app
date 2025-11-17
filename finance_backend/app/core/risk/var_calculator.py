"""
Cálculo de Value at Risk (VaR) para portfólios.
"""
import numpy as np
from scipy import stats
from typing import Dict, List, Any
from decimal import Decimal

from .utils import get_historical_returns_df


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
        returns_df = get_historical_returns_df(ticker)
        
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

