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


# Advanced Analysis Schemas
class SupportResistanceLevel(BaseModel):
    price: float
    strength: float
    test_count: int
    distance_from_current: float


class ChartPattern(BaseModel):
    pattern_type: str
    pattern_name: str
    start_date: str
    end_date: str
    confidence: float
    head_price: Optional[float] = None
    neckline: Optional[float] = None
    top_price: Optional[float] = None
    bottom_price: Optional[float] = None
    valley: Optional[float] = None
    peak: Optional[float] = None
    trend: Optional[str] = None


class CandlestickPattern(BaseModel):
    pattern_name: str
    pattern_type: str
    date: str
    signal: str  # BULLISH, BEARISH, NEUTRAL
    price: float


class FibonacciLevels(BaseModel):
    swing_high: float
    swing_low: float
    level_0: float
    level_236: float
    level_382: float
    level_500: float
    level_618: float
    level_786: float
    level_1000: float
    level_1272: Optional[float] = None
    level_1618: Optional[float] = None


class ElliottWavePoint(BaseModel):
    wave: str
    date: str
    price: float
    index: int


class ElliottWaves(BaseModel):
    pattern_type: Optional[str] = None
    waves: List[ElliottWavePoint]
    confidence: float
    wave_labels: Optional[List[str]] = None


class AdvancedAnalysisOut(BaseModel):
    ticker: str
    period: str
    patterns: List[ChartPattern]
    support_levels: List[SupportResistanceLevel]
    resistance_levels: List[SupportResistanceLevel]
    candlestick_patterns: List[CandlestickPattern]
    fibonacci_levels: Dict[str, float]
    elliott_waves: ElliottWaves


# Elliott Annotation Schemas
class WavePoint(BaseModel):
    wave: str
    date: str
    price: float


class ElliottAnnotationIn(BaseModel):
    ticker: str
    period: str
    annotations: List[WavePoint]


class ElliottAnnotationOut(BaseModel):
    id: int
    ticker: str
    period: str
    annotations: List[WavePoint]
    created_at: str
    updated_at: Optional[str] = None