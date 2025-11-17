"""
Router para CRUD de portfolios.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.db.models import User, Portfolio, PortfolioItem, UserRole
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioOut, PortfolioList
)
from app.core.security import get_current_user

router = APIRouter()


def check_portfolio_limit(user: User, db: Session) -> None:
    """
    Valida se o usuário pode criar mais portfolios baseado no seu plano.
    Limites: USER=3, PRO=10, ADMIN=ilimitado
    """
    if user.role == UserRole.ADMIN:
        return  # Admin não tem limite
    
    current_count = db.query(func.count(Portfolio.id)).filter(
        Portfolio.user_id == user.id
    ).scalar() or 0
    
    limit = 3 if user.role == UserRole.USER else 10
    
    if current_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Limite de portfolios atingido. Seu plano permite {limit} portfolios."
        )


@router.get("/portfolios", response_model=PortfolioList)
def list_portfolios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos os portfolios do usuário.
    """
    try:
        portfolios = db.query(Portfolio).filter(
            Portfolio.user_id == current_user.id
        ).order_by(Portfolio.created_at.desc()).all()
        
        portfolio_list = []
        for portfolio in portfolios:
            item_count = db.query(func.count(PortfolioItem.id)).filter(
                PortfolioItem.portfolio_id == portfolio.id
            ).scalar() or 0
            
            portfolio_list.append(PortfolioOut(
                id=portfolio.id,
                name=portfolio.name,
                category=portfolio.category,
                description=portfolio.description,
                created_at=portfolio.created_at,
                updated_at=portfolio.updated_at,
                item_count=item_count
            ))
        
        return PortfolioList(portfolios=portfolio_list)
    except Exception as e:
        # Se a tabela não existir, retornar lista vazia
        import traceback
        print(f"Erro ao listar portfolios: {e}")
        print(traceback.format_exc())
        # Verificar se é erro de tabela não encontrada
        if "does not exist" in str(e) or "relation" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Tabela de portfolios não encontrada. Execute a migração add_portfolios.sql primeiro."
            )
        raise


@router.post("/portfolios", response_model=PortfolioOut, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    payload: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cria um novo portfolio.
    """
    # Verificar limite de portfolios
    check_portfolio_limit(current_user, db)
    
    # Verificar se já existe portfolio com mesmo nome
    existing = db.query(Portfolio).filter(
        Portfolio.user_id == current_user.id,
        Portfolio.name == payload.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um portfolio com este nome"
        )
    
    portfolio = Portfolio(
        user_id=current_user.id,
        name=payload.name,
        category=payload.category,
        description=payload.description
    )
    
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    return PortfolioOut(
        id=portfolio.id,
        name=portfolio.name,
        category=portfolio.category,
        description=portfolio.description,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        item_count=0
    )


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioOut)
def get_portfolio_by_id(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtém um portfolio específico.
    """
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio não encontrado"
        )
    
    item_count = db.query(func.count(PortfolioItem.id)).filter(
        PortfolioItem.portfolio_id == portfolio.id
    ).scalar() or 0
    
    return PortfolioOut(
        id=portfolio.id,
        name=portfolio.name,
        category=portfolio.category,
        description=portfolio.description,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        item_count=item_count
    )


@router.patch("/portfolios/{portfolio_id}", response_model=PortfolioOut)
def update_portfolio(
    portfolio_id: int,
    payload: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza um portfolio.
    """
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio não encontrado"
        )
    
    # Verificar se o novo nome já existe (se estiver sendo alterado)
    if payload.name and payload.name != portfolio.name:
        existing = db.query(Portfolio).filter(
            Portfolio.user_id == current_user.id,
            Portfolio.name == payload.name,
            Portfolio.id != portfolio_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um portfolio com este nome"
            )
    
    # Atualizar campos
    if payload.name is not None:
        portfolio.name = payload.name
    if payload.category is not None:
        portfolio.category = payload.category
    if payload.description is not None:
        portfolio.description = payload.description
    
    db.commit()
    db.refresh(portfolio)
    
    item_count = db.query(func.count(PortfolioItem.id)).filter(
        PortfolioItem.portfolio_id == portfolio.id
    ).scalar() or 0
    
    return PortfolioOut(
        id=portfolio.id,
        name=portfolio.name,
        category=portfolio.category,
        description=portfolio.description,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        item_count=item_count
    )


@router.delete("/portfolios/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deleta um portfolio e todas as suas posições (cascade delete).
    """
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio não encontrado"
        )
    
    # Deletar portfolio (os itens serão deletados automaticamente via cascade)
    db.delete(portfolio)
    db.commit()
    
    return None

