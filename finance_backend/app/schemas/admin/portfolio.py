from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class PortfolioAdminOut(BaseModel):
    id: int
    user_id: int
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    item_count: Optional[int] = None

    class Config:
        from_attributes = True


class PortfolioAdminCreate(BaseModel):
    user_id: int
    name: str = Field(min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None


class PortfolioAdminUpdate(BaseModel):
    user_id: Optional[int] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None


class PortfolioItemAdminOut(BaseModel):
    id: int
    user_id: int
    portfolio_id: int
    ticker: str
    quantity: int
    purchase_price: Decimal
    purchase_date: date
    sold_price: Optional[Decimal] = None
    sold_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PortfolioItemAdminCreate(BaseModel):
    user_id: int
    portfolio_id: int
    ticker: str = Field(min_length=1, max_length=20)
    quantity: int = Field(gt=0)
    purchase_price: Decimal = Field(gt=0)
    purchase_date: date
    sold_price: Optional[Decimal] = None
    sold_date: Optional[date] = None


class PortfolioItemAdminUpdate(BaseModel):
    user_id: Optional[int] = None
    portfolio_id: Optional[int] = None
    ticker: Optional[str] = Field(default=None, min_length=1, max_length=20)
    quantity: Optional[int] = Field(default=None, gt=0)
    purchase_price: Optional[Decimal] = Field(default=None, gt=0)
    purchase_date: Optional[date] = None
    sold_price: Optional[Decimal] = None
    sold_date: Optional[date] = None

