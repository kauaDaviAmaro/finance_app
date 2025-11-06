from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class AlertCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20, description="Símbolo do ativo (ex: PETR4)")
    indicator_type: str = Field(..., description="Tipo de indicador: MACD, RSI, STOCHASTIC, BBANDS")
    condition: str = Field(..., description="Condição: CROSS_ABOVE, CROSS_BELOW, GREATER_THAN, LESS_THAN")
    threshold_value: Optional[Decimal] = Field(None, description="Valor limite (opcional para algumas condições)")

class AlertOut(BaseModel):
    id: int
    ticker: str
    indicator_type: str
    condition: str
    threshold_value: Optional[Decimal] = None
    is_active: bool
    triggered_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class AlertListResponse(BaseModel):
    alerts: List[AlertOut]

