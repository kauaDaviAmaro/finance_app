"""
Router para planejamento financeiro: metas de investimento, planos financeiros,
planejamento de aposentadoria e análise de patrimônio.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List, Optional
from datetime import date, datetime

from app.db.database import get_db
from app.db.models import (
    User, InvestmentGoal, FinancialPlan, RetirementPlan, WealthHistory,
    InvestmentGoalStatus, Portfolio
)
from app.core.security import get_current_user
from app.schemas.financial_planning import (
    InvestmentGoalCreate, InvestmentGoalUpdate, InvestmentGoalOut, InvestmentGoalList,
    FinancialPlanCreate, FinancialPlanUpdate, FinancialPlanOut, FinancialPlanList,
    RetirementPlanCreate, RetirementPlanUpdate, RetirementPlanOut, RetirementPlanList,
    WealthHistoryCreate, WealthHistoryUpdate, WealthHistoryOut, WealthHistoryList,
    PortfolioProjectionRequest, PortfolioProjectionResponse,
    ContributionSimulationRequest, ContributionSimulationResponse,
    WealthAnalysisResponse
)
from app.core.financial_planning import (
    calculate_portfolio_projection,
    calculate_retirement_plan,
    simulate_contributions,
    analyze_wealth_history
)

router = APIRouter(prefix="/financial-planning", tags=["Financial Planning"])


# Investment Goals Endpoints
@router.get("/goals", response_model=InvestmentGoalList)
def get_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todas as metas de investimento do usuário."""
    goals = db.query(InvestmentGoal).filter(
        InvestmentGoal.user_id == current_user.id
    ).order_by(InvestmentGoal.created_at.desc()).all()
    
    return InvestmentGoalList(goals=goals)


@router.post("/goals", response_model=InvestmentGoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: InvestmentGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cria uma nova meta de investimento."""
    # Verifica se o portfolio existe (se fornecido)
    if payload.portfolio_id:
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == payload.portfolio_id,
            Portfolio.user_id == current_user.id
        ).first()
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
    
    goal = InvestmentGoal(
        user_id=current_user.id,
        name=payload.name,
        target_amount=payload.target_amount,
        current_amount=payload.current_amount,
        target_date=payload.target_date,
        portfolio_id=payload.portfolio_id,
        status=InvestmentGoalStatus.ACTIVE
    )
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    return goal


@router.get("/goals/{goal_id}", response_model=InvestmentGoalOut)
def get_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém uma meta de investimento específica."""
    goal = db.query(InvestmentGoal).filter(
        InvestmentGoal.id == goal_id,
        InvestmentGoal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    return goal


@router.put("/goals/{goal_id}", response_model=InvestmentGoalOut)
def update_goal(
    goal_id: int,
    payload: InvestmentGoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza uma meta de investimento."""
    goal = db.query(InvestmentGoal).filter(
        InvestmentGoal.id == goal_id,
        InvestmentGoal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Atualiza campos fornecidos
    if payload.name is not None:
        goal.name = payload.name
    if payload.target_amount is not None:
        goal.target_amount = payload.target_amount
    if payload.current_amount is not None:
        goal.current_amount = payload.current_amount
    if payload.target_date is not None:
        goal.target_date = payload.target_date
    if payload.portfolio_id is not None:
        if payload.portfolio_id:
            portfolio = db.query(Portfolio).filter(
                Portfolio.id == payload.portfolio_id,
                Portfolio.user_id == current_user.id
            ).first()
            if not portfolio:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Portfolio not found"
                )
        goal.portfolio_id = payload.portfolio_id
    if payload.status is not None:
        goal.status = payload.status
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    return goal


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deleta uma meta de investimento."""
    goal = db.query(InvestmentGoal).filter(
        InvestmentGoal.id == goal_id,
        InvestmentGoal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    db.delete(goal)
    db.commit()
    return None


# Financial Plans Endpoints
@router.get("/plans", response_model=FinancialPlanList)
def get_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos os planos financeiros do usuário."""
    plans = db.query(FinancialPlan).filter(
        FinancialPlan.user_id == current_user.id
    ).order_by(FinancialPlan.created_at.desc()).all()
    
    return FinancialPlanList(plans=plans)


@router.post("/plans", response_model=FinancialPlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: FinancialPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cria um novo plano financeiro."""
    # Verifica se já existe um plano com o mesmo nome
    existing = db.query(FinancialPlan).filter(
        FinancialPlan.user_id == current_user.id,
        FinancialPlan.name == payload.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A plan with this name already exists"
        )
    
    plan = FinancialPlan(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        monthly_income=payload.monthly_income,
        monthly_expenses=payload.monthly_expenses,
        emergency_fund_target=payload.emergency_fund_target
    )
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return plan


@router.get("/plans/{plan_id}", response_model=FinancialPlanOut)
def get_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém um plano financeiro específico."""
    plan = db.query(FinancialPlan).filter(
        FinancialPlan.id == plan_id,
        FinancialPlan.user_id == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    return plan


@router.put("/plans/{plan_id}", response_model=FinancialPlanOut)
def update_plan(
    plan_id: int,
    payload: FinancialPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza um plano financeiro."""
    plan = db.query(FinancialPlan).filter(
        FinancialPlan.id == plan_id,
        FinancialPlan.user_id == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Verifica nome único se estiver mudando
    if payload.name is not None and payload.name != plan.name:
        existing = db.query(FinancialPlan).filter(
            FinancialPlan.user_id == current_user.id,
            FinancialPlan.name == payload.name,
            FinancialPlan.id != plan_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A plan with this name already exists"
            )
        plan.name = payload.name
    
    if payload.description is not None:
        plan.description = payload.description
    if payload.monthly_income is not None:
        plan.monthly_income = payload.monthly_income
    if payload.monthly_expenses is not None:
        plan.monthly_expenses = payload.monthly_expenses
    if payload.emergency_fund_target is not None:
        plan.emergency_fund_target = payload.emergency_fund_target
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return plan


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deleta um plano financeiro."""
    plan = db.query(FinancialPlan).filter(
        FinancialPlan.id == plan_id,
        FinancialPlan.user_id == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    db.delete(plan)
    db.commit()
    return None


# Retirement Plans Endpoints
@router.get("/retirement-plans", response_model=RetirementPlanList)
def get_retirement_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos os planos de aposentadoria do usuário."""
    plans = db.query(RetirementPlan).filter(
        RetirementPlan.user_id == current_user.id
    ).order_by(RetirementPlan.created_at.desc()).all()
    
    # Calcula projeções para cada plano
    results = []
    for plan in plans:
        calculation = calculate_retirement_plan(
            current_age=plan.current_age,
            retirement_age=plan.retirement_age,
            current_savings=plan.current_savings,
            monthly_contribution=plan.monthly_contribution,
            expected_return_rate=plan.expected_return_rate,
            inflation_rate=plan.inflation_rate,
            target_monthly_income=plan.target_monthly_income
        )
        
        result = RetirementPlanOut(
            id=plan.id,
            current_age=plan.current_age,
            retirement_age=plan.retirement_age,
            current_savings=plan.current_savings,
            monthly_contribution=plan.monthly_contribution,
            expected_return_rate=plan.expected_return_rate,
            inflation_rate=plan.inflation_rate,
            target_monthly_income=plan.target_monthly_income,
            years_until_retirement=calculation['years_until_retirement'],
            projected_savings=calculation['projected_savings'],
            required_savings=calculation['required_savings'],
            is_on_track=calculation['is_on_track'],
            created_at=plan.created_at,
            updated_at=plan.updated_at
        )
        results.append(result)
    
    return RetirementPlanList(plans=results)


@router.post("/retirement-plans", response_model=RetirementPlanOut, status_code=status.HTTP_201_CREATED)
def create_retirement_plan(
    payload: RetirementPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cria um novo plano de aposentadoria."""
    plan = RetirementPlan(
        user_id=current_user.id,
        current_age=payload.current_age,
        retirement_age=payload.retirement_age,
        current_savings=payload.current_savings,
        monthly_contribution=payload.monthly_contribution,
        expected_return_rate=payload.expected_return_rate,
        inflation_rate=payload.inflation_rate,
        target_monthly_income=payload.target_monthly_income
    )
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    # Calcula projeção
    calculation = calculate_retirement_plan(
        current_age=plan.current_age,
        retirement_age=plan.retirement_age,
        current_savings=plan.current_savings,
        monthly_contribution=plan.monthly_contribution,
        expected_return_rate=plan.expected_return_rate,
        inflation_rate=plan.inflation_rate,
        target_monthly_income=plan.target_monthly_income
    )
    
    return RetirementPlanOut(
        id=plan.id,
        current_age=plan.current_age,
        retirement_age=plan.retirement_age,
        current_savings=plan.current_savings,
        monthly_contribution=plan.monthly_contribution,
        expected_return_rate=plan.expected_return_rate,
        inflation_rate=plan.inflation_rate,
        target_monthly_income=plan.target_monthly_income,
        years_until_retirement=calculation['years_until_retirement'],
        projected_savings=calculation['projected_savings'],
        required_savings=calculation['required_savings'],
        is_on_track=calculation['is_on_track'],
        created_at=plan.created_at,
        updated_at=plan.updated_at
    )


@router.get("/retirement-plans/{plan_id}", response_model=RetirementPlanOut)
def get_retirement_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém um plano de aposentadoria específico."""
    plan = db.query(RetirementPlan).filter(
        RetirementPlan.id == plan_id,
        RetirementPlan.user_id == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retirement plan not found"
        )
    
    # Calcula projeção
    calculation = calculate_retirement_plan(
        current_age=plan.current_age,
        retirement_age=plan.retirement_age,
        current_savings=plan.current_savings,
        monthly_contribution=plan.monthly_contribution,
        expected_return_rate=plan.expected_return_rate,
        inflation_rate=plan.inflation_rate,
        target_monthly_income=plan.target_monthly_income
    )
    
    return RetirementPlanOut(
        id=plan.id,
        current_age=plan.current_age,
        retirement_age=plan.retirement_age,
        current_savings=plan.current_savings,
        monthly_contribution=plan.monthly_contribution,
        expected_return_rate=plan.expected_return_rate,
        inflation_rate=plan.inflation_rate,
        target_monthly_income=plan.target_monthly_income,
        years_until_retirement=calculation['years_until_retirement'],
        projected_savings=calculation['projected_savings'],
        required_savings=calculation['required_savings'],
        is_on_track=calculation['is_on_track'],
        created_at=plan.created_at,
        updated_at=plan.updated_at
    )


@router.put("/retirement-plans/{plan_id}", response_model=RetirementPlanOut)
def update_retirement_plan(
    plan_id: int,
    payload: RetirementPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza um plano de aposentadoria."""
    plan = db.query(RetirementPlan).filter(
        RetirementPlan.id == plan_id,
        RetirementPlan.user_id == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retirement plan not found"
        )
    
    # Atualiza campos fornecidos
    if payload.current_age is not None:
        plan.current_age = payload.current_age
    if payload.retirement_age is not None:
        plan.retirement_age = payload.retirement_age
    if payload.current_savings is not None:
        plan.current_savings = payload.current_savings
    if payload.monthly_contribution is not None:
        plan.monthly_contribution = payload.monthly_contribution
    if payload.expected_return_rate is not None:
        plan.expected_return_rate = payload.expected_return_rate
    if payload.inflation_rate is not None:
        plan.inflation_rate = payload.inflation_rate
    if payload.target_monthly_income is not None:
        plan.target_monthly_income = payload.target_monthly_income
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    # Calcula projeção atualizada
    calculation = calculate_retirement_plan(
        current_age=plan.current_age,
        retirement_age=plan.retirement_age,
        current_savings=plan.current_savings,
        monthly_contribution=plan.monthly_contribution,
        expected_return_rate=plan.expected_return_rate,
        inflation_rate=plan.inflation_rate,
        target_monthly_income=plan.target_monthly_income
    )
    
    return RetirementPlanOut(
        id=plan.id,
        current_age=plan.current_age,
        retirement_age=plan.retirement_age,
        current_savings=plan.current_savings,
        monthly_contribution=plan.monthly_contribution,
        expected_return_rate=plan.expected_return_rate,
        inflation_rate=plan.inflation_rate,
        target_monthly_income=plan.target_monthly_income,
        years_until_retirement=calculation['years_until_retirement'],
        projected_savings=calculation['projected_savings'],
        required_savings=calculation['required_savings'],
        is_on_track=calculation['is_on_track'],
        created_at=plan.created_at,
        updated_at=plan.updated_at
    )


@router.delete("/retirement-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_retirement_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deleta um plano de aposentadoria."""
    plan = db.query(RetirementPlan).filter(
        RetirementPlan.id == plan_id,
        RetirementPlan.user_id == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retirement plan not found"
        )
    
    db.delete(plan)
    db.commit()
    return None


# Wealth History Endpoints
@router.get("/wealth-history", response_model=WealthHistoryList)
def get_wealth_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista o histórico de patrimônio do usuário."""
    history = db.query(WealthHistory).filter(
        WealthHistory.user_id == current_user.id
    ).order_by(WealthHistory.date.desc()).all()
    
    return WealthHistoryList(history=history)


@router.post("/wealth-history", response_model=WealthHistoryOut, status_code=status.HTTP_201_CREATED)
def create_wealth_history(
    payload: WealthHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cria um novo registro de histórico de patrimônio."""
    # Verifica se já existe registro para esta data
    existing = db.query(WealthHistory).filter(
        WealthHistory.user_id == current_user.id,
        WealthHistory.date == payload.snapshot_date
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A wealth history entry for this date already exists"
        )
    
    history = WealthHistory(
        user_id=current_user.id,
        date=payload.snapshot_date,
        total_value=payload.total_value,
        portfolio_value=payload.portfolio_value,
        cash_value=payload.cash_value,
        notes=payload.notes
    )
    
    db.add(history)
    db.commit()
    db.refresh(history)
    
    return history


@router.put("/wealth-history/{history_id}", response_model=WealthHistoryOut)
def update_wealth_history(
    history_id: int,
    payload: WealthHistoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza um registro de histórico de patrimônio."""
    history = db.query(WealthHistory).filter(
        WealthHistory.id == history_id,
        WealthHistory.user_id == current_user.id
    ).first()
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wealth history entry not found"
        )
    
    # Verifica data única se estiver mudando
    if payload.snapshot_date is not None and payload.snapshot_date != history.date:
        existing = db.query(WealthHistory).filter(
            WealthHistory.user_id == current_user.id,
            WealthHistory.date == payload.snapshot_date,
            WealthHistory.id != history_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A wealth history entry for this date already exists"
            )
        history.date = payload.snapshot_date
    
    if payload.total_value is not None:
        history.total_value = payload.total_value
    if payload.portfolio_value is not None:
        history.portfolio_value = payload.portfolio_value
    if payload.cash_value is not None:
        history.cash_value = payload.cash_value
    if payload.notes is not None:
        history.notes = payload.notes
    
    db.add(history)
    db.commit()
    db.refresh(history)
    
    return history


@router.delete("/wealth-history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wealth_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deleta um registro de histórico de patrimônio."""
    history = db.query(WealthHistory).filter(
        WealthHistory.id == history_id,
        WealthHistory.user_id == current_user.id
    ).first()
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wealth history entry not found"
        )
    
    db.delete(history)
    db.commit()
    return None


# Analysis Endpoints
@router.post("/portfolio-projection", response_model=PortfolioProjectionResponse)
def get_portfolio_projection(
    payload: PortfolioProjectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calcula projeção de portfólio."""
    # Obtém portfolios do usuário
    if payload.portfolio_id:
        portfolios = db.query(Portfolio).filter(
            Portfolio.id == payload.portfolio_id,
            Portfolio.user_id == current_user.id
        ).all()
        if not portfolios:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
    else:
        portfolios = db.query(Portfolio).filter(
            Portfolio.user_id == current_user.id
        ).all()
    
    # Calcula valor total inicial
    initial_value = Decimal(0)
    for portfolio in portfolios:
        # Aqui você precisaria calcular o valor atual do portfolio
        # Por enquanto, vamos usar um valor placeholder
        initial_value += Decimal(0)  # TODO: calcular valor real do portfolio
    
    # Calcula projeção
    projection = calculate_portfolio_projection(
        initial_value=float(initial_value),
        years=payload.years,
        monthly_contribution=float(payload.monthly_contribution),
        expected_return_rate=float(payload.expected_return_rate) if payload.expected_return_rate else None,
        scenarios=payload.scenarios
    )
    
    return projection


@router.post("/contribution-simulation", response_model=ContributionSimulationResponse)
def simulate_contribution_strategies(
    payload: ContributionSimulationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Simula diferentes estratégias de aporte."""
    results = simulate_contributions(
        initial_value=float(payload.initial_value),
        years=payload.years,
        expected_return_rate=float(payload.expected_return_rate),
        strategies=[{
            'type': s.type,
            'initial_amount': float(s.initial_amount),
            'growth_rate': float(s.growth_rate) if s.growth_rate else None,
            'periods': s.periods
        } for s in payload.strategies]
    )
    
    return ContributionSimulationResponse(
        initial_value=payload.initial_value,
        years=payload.years,
        expected_return_rate=payload.expected_return_rate,
        results=results
    )


@router.get("/wealth-analysis", response_model=WealthAnalysisResponse)
def get_wealth_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém análise de patrimônio do usuário."""
    history = db.query(WealthHistory).filter(
        WealthHistory.user_id == current_user.id
    ).order_by(WealthHistory.date.asc()).all()
    
    if not history:
        # Retorna análise vazia se não houver histórico
        return WealthAnalysisResponse(
            current_value=Decimal(0),
            historical_data=[],
            growth_rate=None,
            annual_returns=[],
            projection_comparison=None
        )
    
    # Calcula valor atual (último registro)
    current_value = history[-1].total_value
    
    # Analisa histórico
    analysis = analyze_wealth_history([
        {
            'date': h.date,
            'total_value': float(h.total_value),
            'portfolio_value': float(h.portfolio_value),
            'cash_value': float(h.cash_value)
        }
        for h in history
    ])
    
    return WealthAnalysisResponse(
        current_value=current_value,
        historical_data=[WealthHistoryOut.model_validate(h) for h in history],
        growth_rate=Decimal(str(analysis.get('growth_rate', 0))) if analysis.get('growth_rate') else None,
        annual_returns=analysis.get('annual_returns', []),
        projection_comparison=analysis.get('projection_comparison')
    )

