"""
Simulador de diferentes estratégias de aporte.
"""
from decimal import Decimal
from typing import Dict, List
from datetime import date


def simulate_contributions(
    initial_value: Decimal,
    years: int,
    expected_return_rate: Decimal,
    strategies: List[Dict]
) -> List[Dict]:
    """
    Simula diferentes estratégias de aporte.
    
    Args:
        initial_value: Valor inicial
        years: Anos para simular
        expected_return_rate: Taxa de retorno esperada (% anual)
        strategies: Lista de estratégias [{type, initial_amount, growth_rate?, periods?}]
    
    Returns:
        Lista de resultados por estratégia
    """
    monthly_rate = Decimal(str(expected_return_rate)) / Decimal('100') / Decimal('12')
    results = []
    
    for i, strategy in enumerate(strategies):
        strategy_type = strategy.get("type", "FIXED")
        initial_amount = Decimal(str(strategy.get("initial_amount", 0)))
        
        if strategy_type == "FIXED":
            result = _simulate_fixed(initial_value, years, initial_amount, monthly_rate, f"Estratégia {i+1}")
        elif strategy_type == "GROWING":
            growth_rate = Decimal(str(strategy.get("growth_rate", 0))) / Decimal('100')
            result = _simulate_growing(initial_value, years, initial_amount, growth_rate, monthly_rate, f"Estratégia {i+1}")
        elif strategy_type == "VARIABLE":
            periods = strategy.get("periods", [])
            result = _simulate_variable(initial_value, years, periods, monthly_rate, f"Estratégia {i+1}")
        else:
            result = _simulate_fixed(initial_value, years, initial_amount, monthly_rate, f"Estratégia {i+1}")
        
        results.append(result)
    
    return results


def _simulate_fixed(
    initial_value: Decimal,
    years: int,
    monthly_amount: Decimal,
    monthly_rate: Decimal,
    name: str
) -> Dict:
    """Simula aporte fixo mensal."""
    current_value = initial_value
    total_contributions = Decimal('0')
    points = []
    
    for year in range(1, years + 1):
        year_contributions = Decimal('0')
        year_returns = Decimal('0')
        
        for month in range(12):
            if monthly_amount > 0:
                current_value += monthly_amount
                year_contributions += monthly_amount
                total_contributions += monthly_amount
            
            monthly_return = current_value * monthly_rate
            current_value += monthly_return
            year_returns += monthly_return
        
        points.append({
            "year": year,
            "value": round(current_value, 2),
            "contributions": round(year_contributions, 2),
            "returns": round(year_returns, 2)
        })
    
    return {
        "strategy_name": name,
        "strategy_type": "FIXED",
        "final_value": round(current_value, 2),
        "total_contributions": round(total_contributions, 2),
        "total_returns": round(current_value - initial_value - total_contributions, 2),
        "points": points
    }


def _simulate_growing(
    initial_value: Decimal,
    years: int,
    initial_amount: Decimal,
    growth_rate: Decimal,
    monthly_rate: Decimal,
    name: str
) -> Dict:
    """Simula aporte crescente."""
    current_value = initial_value
    total_contributions = Decimal('0')
    points = []
    current_monthly_amount = initial_amount
    # Calcular fator de crescimento mensal
    annual_growth_float = float(growth_rate)
    monthly_growth_factor = Decimal(str((1 + annual_growth_float) ** (1.0 / 12.0)))
    
    for year in range(1, years + 1):
        year_contributions = Decimal('0')
        year_returns = Decimal('0')
        
        for month in range(12):
            if current_monthly_amount > 0:
                current_value += current_monthly_amount
                year_contributions += current_monthly_amount
                total_contributions += current_monthly_amount
            
            monthly_return = current_value * monthly_rate
            current_value += monthly_return
            year_returns += monthly_return
            
            # Aumentar aporte mensalmente
            current_monthly_amount = current_monthly_amount * monthly_growth_factor
        
        points.append({
            "year": year,
            "value": round(current_value, 2),
            "contributions": round(year_contributions, 2),
            "returns": round(year_returns, 2)
        })
    
    return {
        "strategy_name": name,
        "strategy_type": "GROWING",
        "final_value": round(current_value, 2),
        "total_contributions": round(total_contributions, 2),
        "total_returns": round(current_value - initial_value - total_contributions, 2),
        "points": points
    }


def _simulate_variable(
    initial_value: Decimal,
    years: int,
    periods: List[Dict],
    monthly_rate: Decimal,
    name: str
) -> Dict:
    """Simula aporte variável por períodos."""
    current_value = initial_value
    total_contributions = Decimal('0')
    points = []
    
    # Criar mapa de aportes por mês
    contribution_map = {}
    for period in periods:
        start_year = period.get("start_year", 1)
        end_year = period.get("end_year", years)
        amount = Decimal(str(period.get("amount", 0)))
        
        for year in range(start_year, min(end_year + 1, years + 1)):
            for month in range(12):
                month_key = (year - 1) * 12 + month
                contribution_map[month_key] = amount
    
    for year in range(1, years + 1):
        year_contributions = Decimal('0')
        year_returns = Decimal('0')
        
        for month in range(12):
            month_key = (year - 1) * 12 + month
            monthly_amount = contribution_map.get(month_key, Decimal('0'))
            
            if monthly_amount > 0:
                current_value += monthly_amount
                year_contributions += monthly_amount
                total_contributions += monthly_amount
            
            monthly_return = current_value * monthly_rate
            current_value += monthly_return
            year_returns += monthly_return
        
        points.append({
            "year": year,
            "value": round(current_value, 2),
            "contributions": round(year_contributions, 2),
            "returns": round(year_returns, 2)
        })
    
    return {
        "strategy_name": name,
        "strategy_type": "VARIABLE",
        "final_value": round(current_value, 2),
        "total_contributions": round(total_contributions, 2),
        "total_returns": round(current_value - initial_value - total_contributions, 2),
        "points": points
    }

