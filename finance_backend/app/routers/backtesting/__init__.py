"""
Routers para backtesting e simulação de estratégias.
"""
from fastapi import APIRouter
from .strategies import router as strategies_router
from .backtests import router as backtests_router
from .paper_trading import router as paper_trading_router

router = APIRouter(prefix="/backtesting", tags=["Backtesting"])

# Incluir todos os sub-routers
router.include_router(strategies_router)
router.include_router(backtests_router)
router.include_router(paper_trading_router)

