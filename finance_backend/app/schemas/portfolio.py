from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

class PortfolioItemCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20, description="Símbolo do ativo (ex: PETR4)")
    quantity: int = Field(..., gt=0, description="Quantidade de ações")
    purchase_price: Decimal = Field(..., gt=0, description="Preço de compra unitário")
    purchase_date: date = Field(..., description="Data de compra")

class PortfolioItemUpdate(BaseModel):
    sold_price: Decimal = Field(..., gt=0, description="Preço de venda unitário")
    sold_date: date = Field(..., description="Data de venda")

class PortfolioItemOut(BaseModel):
    id: int
    ticker: str
    quantity: int
    purchase_price: Decimal
    purchase_date: date
    sold_price: Optional[Decimal] = None
    sold_date: Optional[date] = None
    realized_pnl: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PortfolioSummary(BaseModel):
    total_invested: Decimal
    total_realized_pnl: Decimal
    total_unrealized_pnl: Decimal
    positions: List[PortfolioItemOut]

