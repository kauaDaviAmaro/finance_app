"""
Calculadora de planejamento de aposentadoria.
"""
from decimal import Decimal
from typing import Dict
import math


def calculate_retirement_plan(
    current_age: int,
    retirement_age: int,
    current_savings: Decimal,
    monthly_contribution: Decimal,
    expected_return_rate: Decimal,
    inflation_rate: Decimal,
    target_monthly_income: Decimal
) -> Dict:
    """
    Calcula projeção de aposentadoria e verifica se está no caminho.
    
    Args:
        current_age: Idade atual
        retirement_age: Idade desejada para aposentadoria
        current_savings: Poupança atual
        monthly_contribution: Contribuição mensal
        expected_return_rate: Taxa de retorno esperada (% anual)
        inflation_rate: Taxa de inflação (% anual)
        target_monthly_income: Renda mensal desejada na aposentadoria
    
    Returns:
        Dict com projeções e análise
    """
    years_until_retirement = retirement_age - current_age
    
    if years_until_retirement <= 0:
        return {
            "years_until_retirement": 0,
            "projected_savings": current_savings,
            "required_savings": Decimal('0'),
            "is_on_track": True,
            "error": "Já atingiu a idade de aposentadoria"
        }
    
    # Taxa mensal de retorno
    monthly_rate = Decimal(str(expected_return_rate)) / Decimal('100') / Decimal('12')
    months = years_until_retirement * 12
    
    # Calcular valor futuro com contribuições mensais
    # FV = PV * (1 + r)^n + PMT * [((1 + r)^n - 1) / r]
    if monthly_rate > 0:
        # Usar float para exponenciação e depois converter de volta
        monthly_rate_float = float(monthly_rate)
        months_int = int(months)
        future_value_factor = Decimal(str((1 + monthly_rate_float) ** months_int))
        projected_savings = (
            current_savings * future_value_factor +
            monthly_contribution * (future_value_factor - Decimal('1')) / monthly_rate
        )
    else:
        projected_savings = current_savings + (monthly_contribution * months)
    
    # Calcular valor necessário considerando inflação
    # Renda mensal ajustada pela inflação
    inflation_rate_float = float(inflation_rate) / 100.0
    inflation_factor = Decimal(str((1 + inflation_rate_float) ** years_until_retirement))
    adjusted_monthly_income = target_monthly_income * inflation_factor
    
    # Usar regra dos 4% (25x a renda anual desejada)
    # Ou seja, precisa ter 25 * 12 * renda_mensal_ajustada
    required_savings = adjusted_monthly_income * Decimal('12') * Decimal('25')
    
    # Verificar se está no caminho (com margem de 5%)
    is_on_track = projected_savings >= required_savings * Decimal('0.95')
    
    return {
        "years_until_retirement": years_until_retirement,
        "projected_savings": round(projected_savings, 2),
        "required_savings": round(required_savings, 2),
        "is_on_track": is_on_track,
        "shortfall": max(Decimal('0'), round(required_savings - projected_savings, 2)) if not is_on_track else Decimal('0')
    }

