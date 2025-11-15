from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, Date, ForeignKey, UniqueConstraint, JSON
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from sqlalchemy.sql import func
from datetime import datetime
from app.db.database import Base


class UserRole(PyEnum):
    ADMIN = "ADMIN"
    PRO = "PRO"
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
    can_be_admin = Column(Boolean, default=True, nullable=False)  # Se False, usuário não pode voltar a ser admin
    stripe_customer_id = Column(String(255), unique=True, nullable=True, index=True)
    subscription_status = Column(String(50), nullable=True, default="inactive")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ticker = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", backref="watchlist_items")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'ticker', name='uq_user_ticker'),
    )
    
    def __repr__(self):
        return f"<WatchlistItem(id={self.id}, user_id={self.user_id}, ticker='{self.ticker}')>"


class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="portfolios")
    items = relationship("PortfolioItem", back_populates="portfolio", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_portfolio_name'),
    )
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, user_id={self.user_id}, name='{self.name}')>"


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    ticker = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    purchase_price = Column(Numeric(10, 2), nullable=False)
    purchase_date = Column(Date, nullable=False)
    sold_price = Column(Numeric(10, 2), nullable=True)
    sold_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="portfolio_items")
    portfolio = relationship("Portfolio", back_populates="items")
    
    def __repr__(self):
        return f"<PortfolioItem(id={self.id}, user_id={self.user_id}, portfolio_id={self.portfolio_id}, ticker='{self.ticker}', quantity={self.quantity})>"


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
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


class TickerPrice(Base):
    __tablename__ = "ticker_prices"
    
    ticker = Column(String(20), primary_key=True, index=True)
    last_price = Column(Numeric(10, 4), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<TickerPrice(ticker='{self.ticker}', price={self.last_price}, timestamp={self.timestamp})>"


class DailyScanResult(Base):
    __tablename__ = "daily_scan_results"
    
    ticker = Column(String(20), primary_key=True, index=True)
    last_price = Column(Numeric(18, 6), nullable=False)
    rsi_14 = Column(Numeric(9, 4), nullable=True)
    macd_h = Column(Numeric(9, 4), nullable=True)
    bb_upper = Column(Numeric(18, 6), nullable=True)
    bb_lower = Column(Numeric(18, 6), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return (
            f"<DailyScanResult(ticker='{self.ticker}', price={self.last_price}, "
            f"rsi_14={self.rsi_14}, macd_h={self.macd_h}, "
            f"bb_upper={self.bb_upper}, bb_lower={self.bb_lower}, timestamp={self.timestamp})>"
        )


class SupportMessage(Base):
    __tablename__ = "support_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    email = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # general, technical, billing, feature
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, in_progress, resolved, closed
    admin_response = Column(Text, nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    responded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", foreign_keys=[user_id], backref="support_messages")
    responder = relationship("User", foreign_keys=[responded_by])
    
    def __repr__(self):
        return f"<SupportMessage(id={self.id}, email='{self.email}', category='{self.category}', status='{self.status}')>"


class NotificationType(PyEnum):
    ALERT_TRIGGERED = "ALERT_TRIGGERED"
    PORTFOLIO_CHANGE = "PORTFOLIO_CHANGE"
    SUPPORT_RESPONSE = "SUPPORT_RESPONSE"
    SUBSCRIPTION_UPDATE = "SUBSCRIPTION_UPDATE"
    SYSTEM = "SYSTEM"


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(SAEnum(NotificationType, name="notification_type"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Dados adicionais em formato JSON
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    user = relationship("User", backref="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}', is_read={self.is_read})>"


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(Text, nullable=False)
    p256dh_key = Column(Text, nullable=False)  # Chave pública do cliente
    auth_key = Column(Text, nullable=False)  # Chave de autenticação do cliente
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", backref="push_subscriptions")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'endpoint', name='uq_user_endpoint'),
    )
    
    def __repr__(self):
        return f"<PushSubscription(id={self.id}, user_id={self.user_id}, endpoint='{self.endpoint[:50]}...')>"