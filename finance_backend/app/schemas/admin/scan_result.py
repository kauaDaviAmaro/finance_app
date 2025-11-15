from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class DailyScanResultAdminOut(BaseModel):
    ticker: str
    last_price: Decimal
    rsi_14: Optional[Decimal] = None
    macd_h: Optional[Decimal] = None
    bb_upper: Optional[Decimal] = None
    bb_lower: Optional[Decimal] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class DailyScanResultAdminCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    last_price: Decimal = Field(gt=0)
    rsi_14: Optional[Decimal] = None
    macd_h: Optional[Decimal] = None
    bb_upper: Optional[Decimal] = None
    bb_lower: Optional[Decimal] = None


class DailyScanResultAdminUpdate(BaseModel):
    last_price: Optional[Decimal] = Field(default=None, gt=0)
    rsi_14: Optional[Decimal] = None
    macd_h: Optional[Decimal] = None
    bb_upper: Optional[Decimal] = None
    bb_lower: Optional[Decimal] = None
    timestamp: Optional[datetime] = None

