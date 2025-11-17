"""
Routers para gerenciamento de portfolios.
"""
from fastapi import APIRouter
from .portfolios import router as portfolios_router
from .items import router as items_router

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

# Incluir todos os sub-routers
router.include_router(portfolios_router)
router.include_router(items_router, prefix="/items", tags=["Portfolio Items"])

