from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WatchlistItemAdminOut(BaseModel):
    id: int
    user_id: int
    ticker: str
    created_at: datetime

    class Config:
        from_attributes = True


class WatchlistItemAdminCreate(BaseModel):
    user_id: int
    ticker: str = Field(min_length=1, max_length=20)


class WatchlistItemAdminUpdate(BaseModel):
    user_id: Optional[int] = None
    ticker: Optional[str] = Field(default=None, min_length=1, max_length=20)

