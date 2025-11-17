"""
Módulo de serviços de mercado - mantido para compatibilidade.
Este arquivo reexporta todas as funções do novo módulo market.
"""
from app.core.market import (
    format_ticker,
    get_historical_data,
    get_company_fundamentals,
    get_technical_analysis,
    get_current_price,
    update_ticker_prices,
    get_all_tracked_tickers,
    check_and_trigger_alerts,
    get_income_statement,
    get_balance_sheet,
    get_cashflow,
)

# Exportar tudo para manter compatibilidade
__all__ = [
    'format_ticker',
    'get_historical_data',
    'get_company_fundamentals',
    'get_technical_analysis',
    'get_current_price',
    'update_ticker_prices',
    'get_all_tracked_tickers',
    'check_and_trigger_alerts',
    'get_income_statement',
    'get_balance_sheet',
    'get_cashflow',
]

# Manter compatibilidade com código que usa _format_ticker (privado)
_format_ticker = format_ticker
