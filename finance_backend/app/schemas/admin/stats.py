from pydantic import BaseModel


class AdminStats(BaseModel):
    """Estatísticas gerais para o dashboard do admin"""
    total_users: int
    active_users: int
    pro_users: int
    admin_users: int
    total_alerts: int
    active_alerts: int
    total_portfolios: int
    total_portfolio_items: int
    total_watchlist_items: int
    total_ticker_prices: int
    total_scan_results: int
    total_support_messages: int
    pending_support_messages: int
    users_by_role: dict
    alerts_by_type: dict
    users_over_time: dict  # {date: cumulative_count}

