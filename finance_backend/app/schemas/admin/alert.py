from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class AlertAdminOut(BaseModel):
    id: int
    user_id: int
    ticker: str
    indicator_type: str
    condition: str
    threshold_value: Optional[Decimal] = None
    is_active: bool
    triggered_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertAdminCreate(BaseModel):
    user_id: int
    ticker: str = Field(min_length=1, max_length=20)
    indicator_type: str
    condition: str
    threshold_value: Optional[Decimal] = None
    is_active: bool = True


class AlertAdminUpdate(BaseModel):
    user_id: Optional[int] = None
    ticker: Optional[str] = Field(default=None, min_length=1, max_length=20)
    indicator_type: Optional[str] = None
    condition: Optional[str] = None
    threshold_value: Optional[Decimal] = None
    is_active: Optional[bool] = None
    triggered_at: Optional[datetime] = None

