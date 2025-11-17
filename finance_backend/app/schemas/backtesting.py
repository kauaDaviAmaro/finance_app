"""
Schemas Pydantic para backtesting e simulação de estratégias.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from app.db.models import StrategyType, ConditionType, ConditionLogic, PaperTradeStatus


# ========== Strategy Schemas ==========

class StrategyConditionCreate(BaseModel):
    condition_type: ConditionType
    indicator: str = Field(..., min_length=1, max_length=50)
    operator: str = Field(..., min_length=1, max_length=20)
    value: Optional[Decimal] = None
    logic: ConditionLogic = ConditionLogic.AND
    order: int = Field(0, ge=0)


class StrategyConditionOut(BaseModel):
    id: int
    strategy_id: int
    condition_type: ConditionType
    indicator: str
    operator: str
    value: Optional[Decimal] = None
    logic: ConditionLogic
    order: int
    
    class Config:
        from_attributes = True


class StrategyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    strategy_type: StrategyType = StrategyType.GRAPHICAL
    json_config: Optional[Dict[str, Any]] = None
    initial_capital: Decimal = Field(100000.00, ge=0)
    position_size: Decimal = Field(100.00, ge=0, le=100)
    conditions: List[StrategyConditionCreate] = Field(default_factory=list)


class StrategyCreateJSON(BaseModel):
    """Schema para criar estratégia via JSON (PRO only)."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    json_config: Dict[str, Any] = Field(..., description="Configuração JSON da estratégia")
    initial_capital: Decimal = Field(100000.00, ge=0)
    position_size: Decimal = Field(100.00, ge=0, le=100)


class StrategyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    initial_capital: Optional[Decimal] = Field(None, ge=0)
    position_size: Optional[Decimal] = Field(None, ge=0, le=100)
    conditions: Optional[List[StrategyConditionCreate]] = None


class StrategyOut(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    strategy_type: StrategyType
    json_config: Optional[Dict[str, Any]] = None
    initial_capital: Decimal
    position_size: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    conditions: List[StrategyConditionOut] = []
    
    class Config:
        from_attributes = True


# ========== Backtest Schemas ==========

class BacktestRunRequest(BaseModel):
    strategy_id: int
    ticker: str = Field(..., min_length=1, max_length=20)
    period: str = Field("1y", description="Período: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max")


class BacktestTradeOut(BaseModel):
    id: int
    backtest_id: int
    trade_date: date
    trade_type: str
    price: Decimal
    quantity: int
    pnl: Optional[Decimal] = None
    capital_after: Optional[Decimal] = None
    
    class Config:
        from_attributes = True


class BacktestMetrics(BaseModel):
    total_return: Decimal
    annualized_return: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: Decimal
    avg_loss: Decimal
    final_capital: Decimal


class BacktestOut(BaseModel):
    id: int
    user_id: int
    strategy_id: int
    ticker: str
    period: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_return: Optional[Decimal] = None
    annualized_return: Optional[Decimal] = None
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    win_rate: Optional[Decimal] = None
    profit_factor: Optional[Decimal] = None
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: Optional[Decimal] = None
    avg_loss: Optional[Decimal] = None
    final_capital: Optional[Decimal] = None
    created_at: datetime
    trades: List[BacktestTradeOut] = []
    
    class Config:
        from_attributes = True


class BacktestResultDetail(BaseModel):
    """Resultado detalhado do backtest com equity curve."""
    backtest: BacktestOut
    equity_curve: List[Dict[str, Any]] = Field(default_factory=list, description="Lista de {date, equity}")


class BacktestCompareRequest(BaseModel):
    """Request para comparar múltiplas estratégias."""
    strategy_ids: List[int] = Field(..., min_items=2, max_items=10)
    ticker: str = Field(..., min_length=1, max_length=20)
    period: str = Field("1y", description="Período: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max")


class BacktestCompareResult(BaseModel):
    """Resultado da comparação de estratégias."""
    ticker: str
    period: str
    strategies: List[BacktestOut] = []


# ========== Paper Trading Schemas ==========

class PaperTradeStartRequest(BaseModel):
    strategy_id: int
    ticker: str = Field(..., min_length=1, max_length=20)
    initial_capital: Optional[Decimal] = Field(None, ge=0)


class PaperTradePositionOut(BaseModel):
    id: int
    paper_trade_id: int
    ticker: str
    quantity: int
    entry_price: Decimal
    entry_date: datetime
    exit_price: Optional[Decimal] = None
    exit_date: Optional[datetime] = None
    pnl: Optional[Decimal] = None
    
    class Config:
        from_attributes = True


class PaperTradeOut(BaseModel):
    id: int
    user_id: int
    strategy_id: int
    ticker: str
    initial_capital: Decimal
    current_capital: Decimal
    status: PaperTradeStatus
    started_at: datetime
    stopped_at: Optional[datetime] = None
    last_update: datetime
    positions: List[PaperTradePositionOut] = []
    
    class Config:
        from_attributes = True


class PaperTradeStatusOut(BaseModel):
    """Status atual do paper trading com métricas."""
    paper_trade: PaperTradeOut
    current_equity: Decimal
    total_return: Decimal
    open_positions_count: int
    positions_value: Decimal


class PaperTradeSignal(BaseModel):
    """Sinal de entrada/saída detectado."""
    entry_signal: bool
    exit_signal: bool
    current_price: Decimal
    timestamp: datetime

