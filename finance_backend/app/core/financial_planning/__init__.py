"""
Módulo de planejamento financeiro com calculadoras e analisadores.
"""
from .projection_calculator import calculate_portfolio_projection
from .retirement_calculator import calculate_retirement_plan
from .contribution_simulator import simulate_contributions
from .wealth_analyzer import analyze_wealth_history

__all__ = [
    'calculate_portfolio_projection',
    'calculate_retirement_plan',
    'simulate_contributions',
    'analyze_wealth_history',
]

