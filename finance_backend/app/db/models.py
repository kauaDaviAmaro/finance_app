from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, Date, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from sqlalchemy.sql import func
from datetime import datetime
from app.db.database import Base


class UserRole(PyEnum):
    ADMIN = "ADMIN"
    USER = "USER"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(SAEnum(UserRole, name="user_role"), nullable=False, default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", backref="watchlist_items")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'ticker', name='uq_user_ticker'),
    )
    
    def __repr__(self):
        return f"<WatchlistItem(id={self.id}, user_id={self.user_id}, ticker='{self.ticker}')>"


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    purchase_price = Column(Numeric(10, 2), nullable=False)
    purchase_date = Column(Date, nullable=False)
    sold_price = Column(Numeric(10, 2), nullable=True)
    sold_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="portfolio_items")
    
    def __repr__(self):
        return f"<PortfolioItem(id={self.id}, user_id={self.user_id}, ticker='{self.ticker}', quantity={self.quantity})>"


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String(20), nullable=False)
    indicator_type = Column(String(50), nullable=False)  # MACD, RSI, STOCHASTIC, BBANDS
    condition = Column(String(50), nullable=False)  # CROSS_ABOVE, CROSS_BELOW, GREATER_THAN, LESS_THAN
    threshold_value = Column(Numeric(10, 4), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", backref="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, user_id={self.user_id}, ticker='{self.ticker}', indicator='{self.indicator_type}')>"