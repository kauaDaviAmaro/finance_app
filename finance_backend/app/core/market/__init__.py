"""
Módulo de serviços de mercado - exporta todas as funções públicas para compatibilidade.
"""
from app.core.market.ticker_utils import format_ticker
from app.core.market.data_fetcher import get_historical_data, get_company_fundamentals
from app.core.market.technical_analysis import get_technical_analysis
from app.core.market.price_cache import (
    get_current_price,
    update_ticker_prices,
    get_all_tracked_tickers
)
from app.core.market.alert_checker import check_and_trigger_alerts

# Exportar tudo para manter compatibilidade com imports antigos
__all__ = [
    'format_ticker',
    'get_historical_data',
    'get_company_fundamentals',
    'get_technical_analysis',
    'get_current_price',
    'update_ticker_prices',
    'get_all_tracked_tickers',
    'check_and_trigger_alerts',
]





