"""
Calculadora de projeções de portfólio.
"""
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import date, timedelta
import math


def calculate_portfolio_projection(
    initial_value: Decimal,
    years: int,
    monthly_contribution: Decimal,
    expected_return_rate: Decimal,
    include_scenarios: bool = True
) -> Dict:
    """
    Calcula projeção de portfólio com diferentes cenários.
    
    Args:
        initial_value: Valor inicial do portfólio
        years: Anos para projetar
        monthly_contribution: Aporte mensal
        expected_return_rate: Taxa de retorno esperada (% anual)
        include_scenarios: Se deve incluir cenários otimista/pessimista
    
    Returns:
        Dict com projeções realista, otimista e pessimista
    """
    # Taxa mensal de retorno
    monthly_rate = Decimal(str(expected_return_rate)) / Decimal('100') / Decimal('12')
    
    # Cenário realista
    realistic = _calculate_scenario(
        initial_value, years, monthly_contribution, monthly_rate, "realistic"
    )
    
    result = {
        "realistic": realistic,
        "optimistic": None,
        "pessimistic": None
    }
    
    if include_scenarios:
        # Cenário otimista: +2% ao ano
        optimistic_rate = monthly_rate + Decimal('0.02') / Decimal('12')
        result["optimistic"] = _calculate_scenario(
            initial_value, years, monthly_contribution, optimistic_rate, "optimistic"
        )
        
        # Cenário pessimista: -2% ao ano
        pessimistic_rate = max(Decimal('0'), monthly_rate - Decimal('0.02') / Decimal('12'))
        result["pessimistic"] = _calculate_scenario(
            initial_value, years, monthly_contribution, pessimistic_rate, "pessimistic"
        )
    
    return result


def _calculate_scenario(
    initial_value: Decimal,
    years: int,
    monthly_contribution: Decimal,
    monthly_rate: Decimal,
    scenario_name: str
) -> Dict:
    """
    Calcula um cenário específico de projeção.
    """
    current_value = initial_value
    total_contributions = Decimal('0')
    points = []
    
    for year in range(1, years + 1):
        year_contributions = Decimal('0')
        year_returns = Decimal('0')
        
        # Calcular mês a mês
        for month in range(12):
            # Aporte no início do mês
            if monthly_contribution > 0:
                current_value += monthly_contribution
                year_contributions += monthly_contribution
                total_contributions += monthly_contribution
            
            # Retorno no final do mês
            monthly_return = current_value * monthly_rate
            current_value = current_value + monthly_return
            year_returns += monthly_return
        
        points.append({
            "year": year,
            "value": round(current_value, 2),
            "contributions": round(year_contributions, 2),
            "returns": round(year_returns, 2)
        })
    
    return {
        "scenario": scenario_name,
        "points": points,
        "final_value": round(current_value, 2),
        "total_contributions": round(total_contributions, 2),
        "total_returns": round(current_value - initial_value - total_contributions, 2)
    }

