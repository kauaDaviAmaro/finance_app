"""
Analisador de patrimônio ao longo do tempo.
"""
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import date, datetime
from collections import defaultdict


def analyze_wealth_history(
    historical_data: List[Dict],
    current_value: Optional[Decimal] = None
) -> Dict:
    """
    Analisa histórico de patrimônio e calcula métricas.
    
    Args:
        historical_data: Lista de snapshots de patrimônio [{date, total_value, ...}]
        current_value: Valor atual (opcional, para incluir no cálculo)
    
    Returns:
        Dict com análise completa
    """
    if not historical_data:
        return {
            "current_value": current_value or Decimal('0'),
            "historical_data": [],
            "growth_rate": None,
            "annual_returns": [],
            "projection_comparison": None
        }
    
    # Ordenar por data
    sorted_data = sorted(historical_data, key=lambda x: x.get("date", ""))
    
    # Calcular retornos anuais
    annual_returns = []
    previous_value = None
    previous_year = None
    
    for entry in sorted_data:
        entry_date = entry.get("date")
        if isinstance(entry_date, str):
            entry_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
        elif isinstance(entry_date, datetime):
            entry_date = entry_date.date()
        
        current_year = entry_date.year
        current_value_entry = Decimal(str(entry.get("total_value", 0)))
        
        if previous_value is not None and previous_year == current_year:
            # Mesmo ano, acumular
            continue
        
        if previous_value is not None and previous_year is not None:
            if previous_year < current_year:
                # Calcular retorno anual
                year_return = ((current_value_entry - previous_value) / previous_value) * Decimal('100')
                annual_returns.append({
                    "year": previous_year,
                    "return": float(round(year_return, 2)),
                    "value": float(previous_value),
                    "end_value": float(current_value_entry)
                })
        
        previous_value = current_value_entry
        previous_year = current_year
    
    # Calcular CAGR (Compound Annual Growth Rate)
    growth_rate = None
    if len(sorted_data) >= 2:
        first_value = Decimal(str(sorted_data[0].get("total_value", 0)))
        last_value = Decimal(str(sorted_data[-1].get("total_value", 0)))
        
        if first_value > 0:
            first_date = sorted_data[0].get("date")
            last_date = sorted_data[-1].get("date")
            
            if isinstance(first_date, str):
                first_date = datetime.strptime(first_date, "%Y-%m-%d").date()
            elif isinstance(first_date, datetime):
                first_date = first_date.date()
            
            if isinstance(last_date, str):
                last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
            elif isinstance(last_date, datetime):
                last_date = last_date.date()
            
            years = (last_date - first_date).days / 365.25
            
            if years > 0:
                growth_rate = (((last_value / first_value) ** (Decimal('1') / Decimal(str(years)))) - Decimal('1')) * Decimal('100')
    
    # Preparar dados históricos para resposta
    historical_out = []
    for entry in sorted_data:
        historical_out.append({
            "id": entry.get("id"),
            "date": entry.get("date"),
            "total_value": entry.get("total_value"),
            "portfolio_value": entry.get("portfolio_value", 0),
            "cash_value": entry.get("cash_value", 0),
            "notes": entry.get("notes"),
            "created_at": entry.get("created_at")
        })
    
    # Adicionar valor atual se fornecido
    if current_value is not None:
        current_year = datetime.now().year
        if annual_returns and annual_returns[-1].get("year") == current_year:
            # Atualizar último ano
            last_entry = sorted_data[-1]
            last_value = Decimal(str(last_entry.get("total_value", 0)))
            if last_value > 0:
                year_return = ((current_value - last_value) / last_value) * Decimal('100')
                annual_returns[-1]["return"] = float(round(year_return, 2))
                annual_returns[-1]["end_value"] = float(current_value)
        else:
            # Adicionar novo ano
            if sorted_data:
                last_value = Decimal(str(sorted_data[-1].get("total_value", 0)))
                if last_value > 0:
                    year_return = ((current_value - last_value) / last_value) * Decimal('100')
                    annual_returns.append({
                        "year": current_year,
                        "return": float(round(year_return, 2)),
                        "value": float(last_value),
                        "end_value": float(current_value)
                    })
    
    return {
        "current_value": current_value or Decimal(str(sorted_data[-1].get("total_value", 0))) if sorted_data else Decimal('0'),
        "historical_data": historical_out,
        "growth_rate": float(round(growth_rate, 2)) if growth_rate is not None else None,
        "annual_returns": annual_returns,
        "projection_comparison": None  # Pode ser preenchido depois com projeções
    }

