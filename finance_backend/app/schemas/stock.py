from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date

class TickerRequest(BaseModel):
    ticker: str = Field(..., min_length=1, description="Símbolo do ativo (ex: PETR4.SA, AAPL)")
    period: str = Field("1y", description="Período dos dados (ex: 1y, 3mo, 5d, max)")

class HistoricalPrice(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class TickerHistoricalDataOut(BaseModel):
    ticker: str
    period: str
    data: List[HistoricalPrice]

class HistoricalPriceWithIndicators(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    stochastic_k: Optional[float] = None
    stochastic_d: Optional[float] = None
    atr: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_upper: Optional[float] = None
    obv: Optional[float] = None
    rsi: Optional[float] = None

class TechnicalAnalysisOut(BaseModel):
    ticker: str
    period: str
    data: List[HistoricalPriceWithIndicators]

class FundamentalsOut(BaseModel):
    ticker: str
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[int] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    net_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    ev_ebitda: Optional[float] = None
    pebit_ratio: Optional[float] = None
    quality_score: Optional[float] = None

class TickerComparisonRequest(BaseModel):
    ticker1: str = Field(..., min_length=1, description="Primeiro ticker para comparação")
    ticker2: str = Field(..., min_length=1, description="Segundo ticker para comparação")
    period: str = Field("1y", description="Período dos dados (ex: 1y, 3mo, 5d, max)")

class TickerComparisonOut(BaseModel):
    ticker1: str
    ticker2: str
    period: str
    ticker1_data: TechnicalAnalysisOut
    ticker2_data: TechnicalAnalysisOut
    ticker1_fundamentals: FundamentalsOut
    ticker2_fundamentals: FundamentalsOut

class FinancialStatementRow(BaseModel):
    account: str
    values: Dict[str, Optional[float]]

class IncomeStatementOut(BaseModel):
    ticker: str
    periods: List[str]
    data: List[FinancialStatementRow]

class BalanceSheetOut(BaseModel):
    ticker: str
    periods: List[str]
    data: List[FinancialStatementRow]

class CashFlowOut(BaseModel):
    ticker: str
    periods: List[str]
    data: List[FinancialStatementRow]

class FinancialStatementsOut(BaseModel):
    ticker: str
    income_statement: IncomeStatementOut
    balance_sheet: BalanceSheetOut
    cash_flow: CashFlowOut