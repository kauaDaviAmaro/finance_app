"""
Cálculo de métricas de diversificação para portfólios.
"""
from typing import Dict, List, Any
from decimal import Decimal

from app.core.market.data_fetcher import get_company_fundamentals


def calculate_diversification_metrics(
    portfolio_positions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calcula métricas de diversificação do portfólio.
    
    Args:
        portfolio_positions: Lista de posições
    
    Returns:
        Dict com 'herfindahl_index', 'concentration_by_ticker', 'sector_diversification', 
        'effective_positions', 'warnings'
    """
    if not portfolio_positions:
        return {
            'herfindahl_index': None,
            'concentration_by_ticker': [],
            'sector_diversification': [],
            'effective_positions': None,
            'warnings': []
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
            'herfindahl_index': None,
            'concentration_by_ticker': [],
            'sector_diversification': [],
            'effective_positions': None,
            'warnings': []
        }
    
    # Calcular pesos
    for pos_data in position_data:
        pos_data['weight'] = pos_data['value'] / float(total_value)
    
    # Calcular Índice de Herfindahl-Hirschman (HHI)
    hhi = sum(w['weight'] ** 2 for w in position_data)
    
    # Número efetivo de posições
    effective_positions = 1 / hhi if hhi > 0 else len(position_data)
    
    # Concentração por ticker
    concentration_by_ticker = sorted(
        [{'ticker': w['ticker'], 'weight': round(w['weight'] * 100, 2)} for w in position_data],
        key=lambda x: x['weight'],
        reverse=True
    )
    
    # Diversificação por setor
    sector_data = {}
    warnings = []
    
    for pos_data in position_data:
        ticker = pos_data['ticker']
        try:
            fundamentals = get_company_fundamentals(ticker)
            sector = fundamentals.get('sector')
            industry = fundamentals.get('industry')
            
            if sector:
                if sector not in sector_data:
                    sector_data[sector] = {'weight': 0.0, 'industries': set(), 'tickers': []}
                sector_data[sector]['weight'] += pos_data['weight']
                sector_data[sector]['tickers'].append(ticker)
                if industry:
                    sector_data[sector]['industries'].add(industry)
        except Exception:
            # Se não conseguir buscar setor, continuar
            pass
    
    # Converter set para lista para JSON
    sector_diversification = []
    for sector, data in sector_data.items():
        sector_diversification.append({
            'sector': sector,
            'weight': round(data['weight'] * 100, 2),
            'industries': list(data['industries']),
            'tickers': data['tickers']
        })
    
    sector_diversification = sorted(sector_diversification, key=lambda x: x['weight'], reverse=True)
    
    # Gerar avisos
    for ticker_concentration in concentration_by_ticker:
        if ticker_concentration['weight'] > 20:
            warnings.append(
                f"Concentração alta em {ticker_concentration['ticker']}: "
                f"{ticker_concentration['weight']:.2f}% do portfólio"
            )
    
    if hhi > 0.25:  # HHI > 0.25 indica alta concentração
        warnings.append(f"Índice de Herfindahl alto ({hhi:.3f}), indicando baixa diversificação")
    
    return {
        'herfindahl_index': round(hhi, 4),
        'concentration_by_ticker': concentration_by_ticker,
        'sector_diversification': sector_diversification,
        'effective_positions': round(effective_positions, 2),
        'warnings': warnings
    }

