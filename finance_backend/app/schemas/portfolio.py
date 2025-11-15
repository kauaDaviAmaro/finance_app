from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Nome do portfolio")
    category: Optional[str] = Field(None, max_length=100, description="Categoria do portfolio (opcional)")
    description: Optional[str] = Field(None, description="Descrição do portfolio (opcional)")

class PortfolioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Nome do portfolio")
    category: Optional[str] = Field(None, max_length=100, description="Categoria do portfolio (opcional)")
    description: Optional[str] = Field(None, description="Descrição do portfolio (opcional)")

class PortfolioOut(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    item_count: Optional[int] = None
    
    class Config:
        from_attributes = True

class PortfolioList(BaseModel):
    portfolios: List[PortfolioOut]

class PortfolioItemCreate(BaseModel):
    portfolio_id: int = Field(..., description="ID do portfolio")
    ticker: str = Field(..., min_length=1, max_length=20, description="Símbolo do ativo (ex: PETR4)")
    quantity: int = Field(..., gt=0, description="Quantidade de ações")
    purchase_price: Decimal = Field(..., gt=0, description="Preço de compra unitário")
    purchase_date: date = Field(..., description="Data de compra")

class PortfolioItemUpdate(BaseModel):
    sold_price: Decimal = Field(..., gt=0, description="Preço de venda unitário")
    sold_date: date = Field(..., description="Data de venda")

class PortfolioItemOut(BaseModel):
    id: int
    portfolio_id: int
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

