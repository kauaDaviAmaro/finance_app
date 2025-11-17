"""
Cálculo de drawdown para portfólios.
"""
from typing import Dict, List, Any
from decimal import Decimal
from datetime import datetime

from .utils import get_historical_returns_df


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
            data = get_historical_returns_df(ticker, period)
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

