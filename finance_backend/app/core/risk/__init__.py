"""
Módulo de gestão de risco para portfólios.
"""
from app.core.risk.risk_calculator import (
    calculate_var,
    calculate_drawdown,
    calculate_portfolio_beta,
    calculate_volatility,
    calculate_diversification_metrics,
    suggest_stop_loss_take_profit,
    analyze_position_risk,
)

__all__ = [
    'calculate_var',
    'calculate_drawdown',
    'calculate_portfolio_beta',
    'calculate_volatility',
    'calculate_diversification_metrics',
    'suggest_stop_loss_take_profit',
    'analyze_position_risk',
]

