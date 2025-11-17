from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from app.db.models import InvestmentGoalStatus


# Investment Goals Schemas
class InvestmentGoalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Nome da meta")
    target_amount: Decimal = Field(..., gt=0, description="Valor alvo")
    current_amount: Decimal = Field(default=0, ge=0, description="Valor atual")
    target_date: date = Field(..., description="Data alvo")
    portfolio_id: Optional[int] = Field(None, description="ID do portfolio (opcional)")


class InvestmentGoalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    target_amount: Optional[Decimal] = Field(None, gt=0)
    current_amount: Optional[Decimal] = Field(None, ge=0)
    target_date: Optional[date] = None
    portfolio_id: Optional[int] = None
    status: Optional[InvestmentGoalStatus] = None


class InvestmentGoalOut(BaseModel):
    id: int
    name: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: date
    portfolio_id: Optional[int] = None
    status: InvestmentGoalStatus
    progress_percentage: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class InvestmentGoalList(BaseModel):
    goals: List[InvestmentGoalOut]


# Financial Plans Schemas
class FinancialPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Nome do plano")
    description: Optional[str] = Field(None, description="Descrição do plano")
    monthly_income: Optional[Decimal] = Field(None, ge=0, description="Renda mensal")
    monthly_expenses: Optional[Decimal] = Field(None, ge=0, description="Despesas mensais")
    emergency_fund_target: Optional[Decimal] = Field(None, ge=0, description="Meta de reserva de emergência")


class FinancialPlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    monthly_income: Optional[Decimal] = Field(None, ge=0)
    monthly_expenses: Optional[Decimal] = Field(None, ge=0)
    emergency_fund_target: Optional[Decimal] = Field(None, ge=0)


class FinancialPlanOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    monthly_income: Optional[Decimal] = None
    monthly_expenses: Optional[Decimal] = None
    emergency_fund_target: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FinancialPlanList(BaseModel):
    plans: List[FinancialPlanOut]


# Retirement Plans Schemas
class RetirementPlanCreate(BaseModel):
    current_age: int = Field(..., ge=18, le=100, description="Idade atual")
    retirement_age: int = Field(..., ge=18, le=100, description="Idade desejada para aposentadoria")
    current_savings: Decimal = Field(default=0, ge=0, description="Poupança atual")
    monthly_contribution: Decimal = Field(default=0, ge=0, description="Contribuição mensal")
    expected_return_rate: Decimal = Field(default=7.0, ge=0, le=100, description="Taxa de retorno esperada (% anual)")
    inflation_rate: Decimal = Field(default=3.0, ge=0, le=100, description="Taxa de inflação (% anual)")
    target_monthly_income: Decimal = Field(..., gt=0, description="Renda mensal desejada na aposentadoria")


class RetirementPlanUpdate(BaseModel):
    current_age: Optional[int] = Field(None, ge=18, le=100)
    retirement_age: Optional[int] = Field(None, ge=18, le=100)
    current_savings: Optional[Decimal] = Field(None, ge=0)
    monthly_contribution: Optional[Decimal] = Field(None, ge=0)
    expected_return_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    inflation_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    target_monthly_income: Optional[Decimal] = Field(None, gt=0)


class RetirementPlanOut(BaseModel):
    id: int
    current_age: int
    retirement_age: int
    current_savings: Decimal
    monthly_contribution: Decimal
    expected_return_rate: Decimal
    inflation_rate: Decimal
    target_monthly_income: Decimal
    years_until_retirement: int
    projected_savings: Decimal
    required_savings: Decimal
    is_on_track: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RetirementPlanList(BaseModel):
    plans: List[RetirementPlanOut]


# Wealth History Schemas
class WealthHistoryCreate(BaseModel):
    snapshot_date: date = Field(..., alias="date", description="Data do snapshot")
    total_value: Decimal = Field(..., ge=0, description="Valor total do patrimônio")
    portfolio_value: Decimal = Field(default=0, ge=0, description="Valor em portfolios")
    cash_value: Decimal = Field(default=0, ge=0, description="Valor em dinheiro")
    notes: Optional[str] = Field(None, description="Notas adicionais")
    
    class Config:
        populate_by_name = True


class WealthHistoryUpdate(BaseModel):
    snapshot_date: Optional[date] = Field(None, alias="date")
    total_value: Optional[Decimal] = Field(None, ge=0)
    portfolio_value: Optional[Decimal] = Field(None, ge=0)
    cash_value: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    
    class Config:
        populate_by_name = True


class WealthHistoryOut(BaseModel):
    id: int
    date: date
    total_value: Decimal
    portfolio_value: Decimal
    cash_value: Decimal
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class WealthHistoryList(BaseModel):
    history: List[WealthHistoryOut]


# Portfolio Projection Schemas
class PortfolioProjectionRequest(BaseModel):
    portfolio_id: Optional[int] = Field(None, description="ID do portfolio (None para todos)")
    years: int = Field(default=10, ge=1, le=50, description="Anos para projetar")
    monthly_contribution: Decimal = Field(default=0, ge=0, description="Aporte mensal")
    expected_return_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Taxa de retorno esperada (% anual, None para usar histórico)")
    scenarios: bool = Field(default=True, description="Incluir cenários otimista/pessimista")


class ProjectionPoint(BaseModel):
    year: int
    value: Decimal
    contributions: Decimal
    returns: Decimal


class ScenarioProjection(BaseModel):
    scenario: str  # optimistic, realistic, pessimistic
    points: List[ProjectionPoint]
    final_value: Decimal
    total_contributions: Decimal
    total_returns: Decimal


class PortfolioProjectionResponse(BaseModel):
    initial_value: Decimal
    years: int
    monthly_contribution: Decimal
    expected_return_rate: Decimal
    realistic: ScenarioProjection
    optimistic: Optional[ScenarioProjection] = None
    pessimistic: Optional[ScenarioProjection] = None


# Contribution Simulator Schemas
class ContributionStrategy(BaseModel):
    type: str = Field(..., description="FIXED, GROWING, VARIABLE")
    initial_amount: Decimal = Field(..., ge=0, description="Valor inicial do aporte")
    growth_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Taxa de crescimento anual (%)")
    periods: Optional[List[dict]] = Field(None, description="Períodos para aporte variável")


class ContributionSimulationRequest(BaseModel):
    initial_value: Decimal = Field(..., ge=0, description="Valor inicial")
    years: int = Field(..., ge=1, le=50, description="Anos para simular")
    expected_return_rate: Decimal = Field(..., ge=0, le=100, description="Taxa de retorno esperada (% anual)")
    strategies: List[ContributionStrategy] = Field(..., min_items=1, description="Estratégias de aporte")


class ContributionSimulationResult(BaseModel):
    strategy_name: str
    strategy_type: str
    final_value: Decimal
    total_contributions: Decimal
    total_returns: Decimal
    points: List[ProjectionPoint]


class ContributionSimulationResponse(BaseModel):
    initial_value: Decimal
    years: int
    expected_return_rate: Decimal
    results: List[ContributionSimulationResult]


# Wealth Analysis Schemas
class WealthAnalysisResponse(BaseModel):
    current_value: Decimal
    historical_data: List[WealthHistoryOut]
    growth_rate: Optional[Decimal] = None  # CAGR
    annual_returns: List[dict] = []  # [{year: 2024, return: 10.5, value: 100000}]
    projection_comparison: Optional[dict] = None

