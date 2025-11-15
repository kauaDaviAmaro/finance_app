from fastapi import APIRouter
from .dashboard import router as dashboard_router
from .users import router as users_router
from .alerts import router as alerts_router
from .portfolios import router as portfolios_router
from .watchlist import router as watchlist_router
from .ticker_prices import router as ticker_prices_router
from .scan_results import router as scan_results_router
from .support import router as support_router
from .scanner import router as scanner_router

# Create main admin router
router = APIRouter()

# Include all sub-routers
router.include_router(dashboard_router)
router.include_router(users_router)
router.include_router(alerts_router)
router.include_router(portfolios_router)
router.include_router(watchlist_router)
router.include_router(ticker_prices_router)
router.include_router(scan_results_router)
router.include_router(support_router)
router.include_router(scanner_router)

__all__ = ["router"]

