"""
Router para CRUD de estratégias de backtesting.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.db.database import get_db
from app.db.models import User, Strategy, StrategyCondition, UserRole, StrategyType
from app.schemas.backtesting import (
    StrategyCreate, StrategyCreateJSON, StrategyUpdate, StrategyOut
)
from app.core.security import get_current_user, get_pro_user

router = APIRouter()


def check_strategy_limit(user: User, db: Session) -> None:
    """Valida se o usuário pode criar mais estratégias baseado no seu plano."""
    if user.role == UserRole.ADMIN:
        return
    
    current_count = db.query(func.count(Strategy.id)).filter(
        Strategy.user_id == user.id
    ).scalar() or 0
    
    limit = 5 if user.role == UserRole.USER else 50
    
    if current_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Limite de estratégias atingido. Seu plano permite {limit} estratégias."
        )


@router.post("/strategies", response_model=StrategyOut, status_code=status.HTTP_201_CREATED)
def create_strategy(
    payload: StrategyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Criar estratégia via interface gráfica (todos os usuários)."""
    check_strategy_limit(current_user, db)
    
    # Verificar se já existe estratégia com mesmo nome
    existing = db.query(Strategy).filter(
        Strategy.user_id == current_user.id,
        Strategy.name == payload.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma estratégia com este nome"
        )
    
    # Criar estratégia
    strategy = Strategy(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        strategy_type=payload.strategy_type,
        initial_capital=payload.initial_capital,
        position_size=payload.position_size
    )
    
    db.add(strategy)
    db.flush()
    
    # Criar condições
    for cond_data in payload.conditions:
        condition = StrategyCondition(
            strategy_id=strategy.id,
            condition_type=cond_data.condition_type,
            indicator=cond_data.indicator,
            operator=cond_data.operator,
            value=cond_data.value,
            logic=cond_data.logic,
            order=cond_data.order
        )
        db.add(condition)
    
    db.commit()
    db.refresh(strategy)
    
    # Carregar condições
    strategy.conditions = db.query(StrategyCondition).filter(
        StrategyCondition.strategy_id == strategy.id
    ).all()
    
    return StrategyOut.from_orm(strategy)


@router.post("/strategies/json", response_model=StrategyOut, status_code=status.HTTP_201_CREATED)
def create_strategy_json(
    payload: StrategyCreateJSON,
    current_user: User = Depends(get_pro_user),  # PRO only
    db: Session = Depends(get_db)
):
    """Criar estratégia via JSON (PRO only)."""
    check_strategy_limit(current_user, db)
    
    existing = db.query(Strategy).filter(
        Strategy.user_id == current_user.id,
        Strategy.name == payload.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma estratégia com este nome"
        )
    
    strategy = Strategy(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        strategy_type=StrategyType.JSON,
        json_config=payload.json_config,
        initial_capital=payload.initial_capital,
        position_size=payload.position_size
    )
    
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
    return StrategyOut.from_orm(strategy)


@router.get("/strategies", response_model=List[StrategyOut])
def list_strategies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar estratégias do usuário."""
    strategies = db.query(Strategy).filter(
        Strategy.user_id == current_user.id
    ).order_by(Strategy.created_at.desc()).all()
    
    # Limitar histórico para usuários não-PRO
    if current_user.role == UserRole.USER:
        strategies = strategies[:5]  # Limite de 5 estratégias visíveis
    
    result = []
    for strategy in strategies:
        strategy.conditions = db.query(StrategyCondition).filter(
            StrategyCondition.strategy_id == strategy.id
        ).order_by(StrategyCondition.order).all()
        result.append(StrategyOut.from_orm(strategy))
    
    return result


@router.get("/strategies/{strategy_id}", response_model=StrategyOut)
def get_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obter detalhes de uma estratégia."""
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estratégia não encontrada"
        )
    
    strategy.conditions = db.query(StrategyCondition).filter(
        StrategyCondition.strategy_id == strategy.id
    ).order_by(StrategyCondition.order).all()
    
    return StrategyOut.from_orm(strategy)


@router.put("/strategies/{strategy_id}", response_model=StrategyOut)
def update_strategy(
    strategy_id: int,
    payload: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualizar estratégia."""
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estratégia não encontrada"
        )
    
    if payload.name and payload.name != strategy.name:
        existing = db.query(Strategy).filter(
            Strategy.user_id == current_user.id,
            Strategy.name == payload.name,
            Strategy.id != strategy_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe uma estratégia com este nome"
            )
        strategy.name = payload.name
    
    if payload.description is not None:
        strategy.description = payload.description
    if payload.initial_capital is not None:
        strategy.initial_capital = payload.initial_capital
    if payload.position_size is not None:
        strategy.position_size = payload.position_size
    
    # Atualizar condições se fornecidas
    if payload.conditions is not None:
        # Deletar condições antigas
        db.query(StrategyCondition).filter(
            StrategyCondition.strategy_id == strategy_id
        ).delete()
        
        # Criar novas condições
        for cond_data in payload.conditions:
            condition = StrategyCondition(
                strategy_id=strategy.id,
                condition_type=cond_data.condition_type,
                indicator=cond_data.indicator,
                operator=cond_data.operator,
                value=cond_data.value,
                logic=cond_data.logic,
                order=cond_data.order
            )
            db.add(condition)
    
    db.commit()
    db.refresh(strategy)
    
    strategy.conditions = db.query(StrategyCondition).filter(
        StrategyCondition.strategy_id == strategy.id
    ).order_by(StrategyCondition.order).all()
    
    return StrategyOut.from_orm(strategy)


@router.delete("/strategies/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletar estratégia."""
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estratégia não encontrada"
        )
    
    db.delete(strategy)
    db.commit()
    
    return None

