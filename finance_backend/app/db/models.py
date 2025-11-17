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


class ScannerData(Base):
    __tablename__ = "scanner_data"
    
    ticker = Column(String(20), primary_key=True, index=True)
    rsi_14 = Column(Numeric(9, 4), nullable=True)
    macd_signal = Column(Numeric(9, 4), nullable=True)
    mm_9_cruza_mm_21 = Column(String(20), nullable=True)  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return (
            f"<ScannerData(ticker='{self.ticker}', rsi_14={self.rsi_14}, "
            f"macd_signal={self.macd_signal}, mm_9_cruza_mm_21='{self.mm_9_cruza_mm_21}', "
            f"last_updated={self.last_updated})>"
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


class TickerSearch(Base):
    __tablename__ = "ticker_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    user = relationship("User", backref="ticker_searches")
    
    def __repr__(self):
        return f"<TickerSearch(id={self.id}, user_id={self.user_id}, ticker='{self.ticker}', created_at={self.created_at})>"


class StrategyType(PyEnum):
    GRAPHICAL = "GRAPHICAL"
    JSON = "JSON"


class ConditionType(PyEnum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"


class ConditionLogic(PyEnum):
    AND = "AND"
    OR = "OR"


class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    strategy_type = Column(SAEnum(StrategyType, name="strategy_type"), nullable=False, default=StrategyType.GRAPHICAL)
    json_config = Column(JSON, nullable=True)  # Para estratégias JSON customizadas
    initial_capital = Column(Numeric(18, 2), nullable=False, default=100000.00)
    position_size = Column(Numeric(5, 2), nullable=False, default=100.00)  # % do capital por trade
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="strategies")
    conditions = relationship("StrategyCondition", back_populates="strategy", cascade="all, delete-orphan")
    backtests = relationship("Backtest", back_populates="strategy", cascade="all, delete-orphan")
    paper_trades = relationship("PaperTrade", back_populates="strategy", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_strategy_name'),
    )
    
    def __repr__(self):
        return f"<Strategy(id={self.id}, user_id={self.user_id}, name='{self.name}', type='{self.strategy_type}')>"


class StrategyCondition(Base):
    __tablename__ = "strategy_conditions"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True)
    condition_type = Column(SAEnum(ConditionType, name="condition_type"), nullable=False)
    indicator = Column(String(50), nullable=False)  # RSI, MACD, etc.
    operator = Column(String(20), nullable=False)  # GREATER_THAN, LESS_THAN, CROSS_ABOVE, etc.
    value = Column(Numeric(18, 6), nullable=True)  # Valor de comparação
    logic = Column(SAEnum(ConditionLogic, name="condition_logic"), nullable=False, default=ConditionLogic.AND)
    order = Column(Integer, nullable=False, default=0)  # Ordem de avaliação
    
    strategy = relationship("Strategy", back_populates="conditions")
    
    def __repr__(self):
        return f"<StrategyCondition(id={self.id}, strategy_id={self.strategy_id}, type='{self.condition_type}', indicator='{self.indicator}')>"


class Backtest(Base):
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker = Column(String(20), nullable=False)
    period = Column(String(20), nullable=False)  # 1y, 6mo, etc.
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Métricas de performance
    total_return = Column(Numeric(10, 4), nullable=True)  # %
    annualized_return = Column(Numeric(10, 4), nullable=True)  # %
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    max_drawdown = Column(Numeric(10, 4), nullable=True)  # %
    win_rate = Column(Numeric(5, 2), nullable=True)  # %
    profit_factor = Column(Numeric(10, 4), nullable=True)
    total_trades = Column(Integer, nullable=False, default=0)
    winning_trades = Column(Integer, nullable=False, default=0)
    losing_trades = Column(Integer, nullable=False, default=0)
    avg_win = Column(Numeric(18, 2), nullable=True)
    avg_loss = Column(Numeric(18, 2), nullable=True)
    final_capital = Column(Numeric(18, 2), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", backref="backtests")
    strategy = relationship("Strategy", back_populates="backtests")
    trades = relationship("BacktestTrade", back_populates="backtest", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Backtest(id={self.id}, strategy_id={self.strategy_id}, ticker='{self.ticker}', return={self.total_return}%)>"


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id", ondelete="CASCADE"), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    trade_type = Column(String(10), nullable=False)  # BUY, SELL
    price = Column(Numeric(18, 6), nullable=False)
    quantity = Column(Integer, nullable=False)
    pnl = Column(Numeric(18, 2), nullable=True)  # P&L realizado
    capital_after = Column(Numeric(18, 2), nullable=True)
    
    backtest = relationship("Backtest", back_populates="trades")
    
    def __repr__(self):
        return f"<BacktestTrade(id={self.id}, backtest_id={self.backtest_id}, type='{self.trade_type}', pnl={self.pnl})>"


class PaperTradeStatus(PyEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class PaperTrade(Base):
    __tablename__ = "paper_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker = Column(String(20), nullable=False)
    initial_capital = Column(Numeric(18, 2), nullable=False)
    current_capital = Column(Numeric(18, 2), nullable=False)
    status = Column(SAEnum(PaperTradeStatus, name="paper_trade_status"), nullable=False, default=PaperTradeStatus.ACTIVE)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    stopped_at = Column(DateTime(timezone=True), nullable=True)
    last_update = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", backref="paper_trades")
    strategy = relationship("Strategy", back_populates="paper_trades")
    positions = relationship("PaperTradePosition", back_populates="paper_trade", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PaperTrade(id={self.id}, user_id={self.user_id}, ticker='{self.ticker}', status='{self.status}')>"


class PaperTradePosition(Base):
    __tablename__ = "paper_trade_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_trade_id = Column(Integer, ForeignKey("paper_trades.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Numeric(18, 6), nullable=False)
    entry_date = Column(DateTime(timezone=True), server_default=func.now())
    exit_price = Column(Numeric(18, 6), nullable=True)
    exit_date = Column(DateTime(timezone=True), nullable=True)
    pnl = Column(Numeric(18, 2), nullable=True)
    
    paper_trade = relationship("PaperTrade", back_populates="positions")
    
    def __repr__(self):
        return f"<PaperTradePosition(id={self.id}, paper_trade_id={self.paper_trade_id}, ticker='{self.ticker}', quantity={self.quantity})>"