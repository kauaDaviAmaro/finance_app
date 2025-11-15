# Export all admin schemas
from .user import UserAdminOut, UserAdminCreate, UserAdminUpdate
from .alert import AlertAdminOut, AlertAdminCreate, AlertAdminUpdate
from .portfolio import (
    PortfolioAdminOut, PortfolioAdminCreate, PortfolioAdminUpdate,
    PortfolioItemAdminOut, PortfolioItemAdminCreate, PortfolioItemAdminUpdate
)
from .watchlist import WatchlistItemAdminOut, WatchlistItemAdminCreate, WatchlistItemAdminUpdate
from .ticker_price import TickerPriceAdminOut, TickerPriceAdminCreate, TickerPriceAdminUpdate
from .scan_result import DailyScanResultAdminOut, DailyScanResultAdminCreate, DailyScanResultAdminUpdate
from .support import SupportMessageAdminOut, SupportMessageAdminCreate, SupportMessageAdminUpdate
from .stats import AdminStats

__all__ = [
    # User schemas
    "UserAdminOut",
    "UserAdminCreate",
    "UserAdminUpdate",
    # Alert schemas
    "AlertAdminOut",
    "AlertAdminCreate",
    "AlertAdminUpdate",
    # Portfolio schemas
    "PortfolioAdminOut",
    "PortfolioAdminCreate",
    "PortfolioAdminUpdate",
    "PortfolioItemAdminOut",
    "PortfolioItemAdminCreate",
    "PortfolioItemAdminUpdate",
    # Watchlist schemas
    "WatchlistItemAdminOut",
    "WatchlistItemAdminCreate",
    "WatchlistItemAdminUpdate",
    # Ticker price schemas
    "TickerPriceAdminOut",
    "TickerPriceAdminCreate",
    "TickerPriceAdminUpdate",
    # Scan result schemas
    "DailyScanResultAdminOut",
    "DailyScanResultAdminCreate",
    "DailyScanResultAdminUpdate",
    # Support schemas
    "SupportMessageAdminOut",
    "SupportMessageAdminCreate",
    "SupportMessageAdminUpdate",
    # Stats schema
    "AdminStats",
]

