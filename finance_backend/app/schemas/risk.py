"""
Schemas para análise de risco de portfólios.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal


class VarResult(BaseModel):
    """Resultado do cálculo de VaR."""
    var_value: Optional[float] = Field(None, description="Valor do VaR em moeda")
    var_percentage: Optional[float] = Field(None, description="VaR em porcentagem")
    method: str = Field(..., description="Método usado (historical ou parametric)")
    confidence_level: float = Field(..., description="Nível de confiança (ex: 0.95)")
    horizon_days: int = Field(..., description="Horizonte de tempo em dias")
    error: Optional[str] = Field(None, description="Mensagem de erro se houver")


class DrawdownPoint(BaseModel):
    """Ponto no histórico de drawdown."""
    date: str = Field(..., description="Data")
    value: float = Field(..., description="Valor do portfólio")
    drawdown: float = Field(..., description="Drawdown em porcentagem")


class DrawdownAnalysis(BaseModel):
    """Análise de drawdown."""
    max_drawdown: Optional[float] = Field(None, description="Drawdown máximo em %")
    current_drawdown: Optional[float] = Field(None, description="Drawdown atual em %")
    max_drawdown_date: Optional[str] = Field(None, description="Data do drawdown máximo")
    recovery_days: Optional[int] = Field(None, description="Dias desde o último pico")
    drawdown_history: List[DrawdownPoint] = Field(default_factory=list, description="Histórico de drawdown")


class PositionBeta(BaseModel):
    """Beta de uma posição."""
    ticker: str = Field(..., description="Ticker")
    beta: Optional[float] = Field(None, description="Beta")
    error: Optional[str] = Field(None, description="Mensagem de erro se houver")


class BetaAnalysis(BaseModel):
    """Análise de beta."""
    portfolio_beta: Optional[float] = Field(None, description="Beta do portfólio")
    position_betas: List[PositionBeta] = Field(default_factory=list, description="Beta por posição")
    benchmark: str = Field(..., description="Benchmark usado")
    error: Optional[str] = Field(None, description="Mensagem de erro se houver")


class PositionVolatility(BaseModel):
    """Volatilidade de uma posição."""
    ticker: str = Field(..., description="Ticker")
    volatility: Optional[float] = Field(None, description="Volatilidade anualizada em %")
    error: Optional[str] = Field(None, description="Mensagem de erro se houver")


class VolatilityAnalysis(BaseModel):
    """Análise de volatilidade."""
    portfolio_volatility: Optional[float] = Field(None, description="Volatilidade do portfólio em %")
    position_volatilities: List[PositionVolatility] = Field(default_factory=list, description="Volatilidade por posição")


class TickerConcentration(BaseModel):
    """Concentração por ticker."""
    ticker: str = Field(..., description="Ticker")
    weight: float = Field(..., description="Peso em % do portfólio")


class SectorDiversification(BaseModel):
    """Diversificação por setor."""
    sector: str = Field(..., description="Setor")
    weight: float = Field(..., description="Peso em % do portfólio")
    industries: List[str] = Field(default_factory=list, description="Indústrias no setor")
    tickers: List[str] = Field(default_factory=list, description="Tickers no setor")


class DiversificationMetrics(BaseModel):
    """Métricas de diversificação."""
    herfindahl_index: Optional[float] = Field(None, description="Índice de Herfindahl-Hirschman")
    concentration_by_ticker: List[TickerConcentration] = Field(default_factory=list, description="Concentração por ticker")
    sector_diversification: List[SectorDiversification] = Field(default_factory=list, description="Diversificação por setor")
    effective_positions: Optional[float] = Field(None, description="Número efetivo de posições")
    warnings: List[str] = Field(default_factory=list, description="Avisos de concentração")


class StopLossTakeProfit(BaseModel):
    """Sugestões de stop loss e take profit."""
    stop_loss: Optional[float] = Field(None, description="Preço sugerido para stop loss")
    take_profit: Optional[float] = Field(None, description="Preço sugerido para take profit")
    stop_loss_percentage: Optional[float] = Field(None, description="Stop loss em %")
    take_profit_percentage: Optional[float] = Field(None, description="Take profit em %")
    method: str = Field(..., description="Método usado (atr, percentage, both)")


class PositionCorrelation(BaseModel):
    """Correlação entre posições."""
    ticker: str = Field(..., description="Ticker correlacionado")
    correlation: float = Field(..., description="Coeficiente de correlação")


class PositionRiskAnalysis(BaseModel):
    """Análise de risco de uma posição individual."""
    ticker: str = Field(..., description="Ticker")
    var: Optional[float] = Field(None, description="VaR individual")
    var_percentage: Optional[float] = Field(None, description="VaR em %")
    beta: Optional[float] = Field(None, description="Beta individual")
    volatility: Optional[float] = Field(None, description="Volatilidade anualizada em %")
    portfolio_weight: float = Field(..., description="Peso no portfólio em %")
    correlations: List[PositionCorrelation] = Field(default_factory=list, description="Correlações com outras posições")
    stop_loss: Optional[float] = Field(None, description="Stop loss sugerido")
    take_profit: Optional[float] = Field(None, description="Take profit sugerido")
    stop_loss_percentage: Optional[float] = Field(None, description="Stop loss em %")
    take_profit_percentage: Optional[float] = Field(None, description="Take profit em %")
    error: Optional[str] = Field(None, description="Mensagem de erro se houver")


class RiskMetrics(BaseModel):
    """Métricas gerais de risco do portfólio."""
    var: VarResult = Field(..., description="Value at Risk")
    drawdown: DrawdownAnalysis = Field(..., description="Análise de drawdown")
    beta: BetaAnalysis = Field(..., description="Análise de beta")
    volatility: VolatilityAnalysis = Field(..., description="Análise de volatilidade")
    diversification: DiversificationMetrics = Field(..., description="Métricas de diversificação")


class PortfolioRiskAnalysis(BaseModel):
    """Análise completa de risco do portfólio."""
    portfolio_id: int = Field(..., description="ID do portfólio")
    metrics: RiskMetrics = Field(..., description="Métricas de risco")
    position_analyses: List[PositionRiskAnalysis] = Field(default_factory=list, description="Análises por posição")



