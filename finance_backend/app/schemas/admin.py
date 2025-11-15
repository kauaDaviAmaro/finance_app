from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from app.db.models import UserRole


# ============================================================================
# USER ADMIN SCHEMAS
# ============================================================================

class UserAdminOut(BaseModel):
    """Schema de saída para usuário no admin - SEM hashed_password"""
    id: int
    email: EmailStr
    username: str
    is_active: bool
    is_verified: bool
    role: UserRole
    stripe_customer_id: Optional[str] = None
    subscription_status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserAdminCreate(BaseModel):
    """Schema para criar usuário no admin - com password plain text"""
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=128)
    is_active: bool = True
    is_verified: bool = False
    role: UserRole = UserRole.USER
    stripe_customer_id: Optional[str] = None
    subscription_status: Optional[str] = None


class UserAdminUpdate(BaseModel):
    """Schema para atualizar usuário no admin - password opcional"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=100)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[UserRole] = None
    stripe_customer_id: Optional[str] = None
    subscription_status: Optional[str] = None


# ============================================================================
# ALERT ADMIN SCHEMAS
# ============================================================================

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


# ============================================================================
# PORTFOLIO ADMIN SCHEMAS
# ============================================================================

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


# ============================================================================
# PORTFOLIO ITEM ADMIN SCHEMAS
# ============================================================================

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


# ============================================================================
# WATCHLIST ITEM ADMIN SCHEMAS
# ============================================================================

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


# ============================================================================
# TICKER PRICE ADMIN SCHEMAS
# ============================================================================

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


# ============================================================================
# DAILY SCAN RESULT ADMIN SCHEMAS
# ============================================================================

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


# ============================================================================
# SUPPORT MESSAGE ADMIN SCHEMAS
# ============================================================================

class SupportMessageAdminOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    email: EmailStr
    category: str
    subject: str
    message: str
    status: str
    admin_response: Optional[str] = None
    responded_at: Optional[datetime] = None
    responded_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupportMessageAdminCreate(BaseModel):
    user_id: Optional[int] = None
    email: EmailStr
    category: str = Field(..., pattern="^(general|technical|billing|feature)$")
    subject: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)


class SupportMessageAdminUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(pending|in_progress|resolved|closed)$")
    admin_response: Optional[str] = None
    responded_by: Optional[int] = None


# ============================================================================
# ADMIN STATS SCHEMA
# ============================================================================

class AdminStats(BaseModel):
    """Estatísticas gerais para o dashboard do admin"""
    total_users: int
    active_users: int
    pro_users: int
    admin_users: int
    total_alerts: int
    active_alerts: int
    total_portfolios: int
    total_portfolio_items: int
    total_watchlist_items: int
    total_ticker_prices: int
    total_scan_results: int
    total_support_messages: int
    pending_support_messages: int
    users_by_role: dict
    alerts_by_type: dict
    users_over_time: dict  # {date: cumulative_count}

