from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class TickerPriceAdminOut(BaseModel):
    ticker: str
    last_price: Decimal
    timestamp: datetime

    class Config:
        from_attributes = True


class TickerPriceAdminCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    last_price: Decimal = Field(gt=0)


class TickerPriceAdminUpdate(BaseModel):
    last_price: Optional[Decimal] = Field(default=None, gt=0)
    timestamp: Optional[datetime] = None

