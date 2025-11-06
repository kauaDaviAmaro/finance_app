from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class WatchlistItemCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20, description="Símbolo do ativo (ex: PETR4)")

class WatchlistItemOut(BaseModel):
    id: int
    ticker: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class WatchlistResponse(BaseModel):
    items: List[WatchlistItemOut]

