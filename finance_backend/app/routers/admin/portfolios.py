from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from app.db.database import get_db
from app.db.models import User, Portfolio, PortfolioItem
from app.schemas.admin import (
    PortfolioAdminOut, PortfolioAdminCreate, PortfolioAdminUpdate,
    PortfolioItemAdminOut, PortfolioItemAdminCreate, PortfolioItemAdminUpdate
)
from app.core.security import get_admin_user

router = APIRouter()


@router.get("/portfolios", response_model=List[PortfolioAdminOut])
def list_portfolios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = Query(None, description="Filtrar por user_id"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Listar todos os portfolios"""
    query = db.query(Portfolio)
    if user_id:
        query = query.filter(Portfolio.user_id == user_id)
    
    portfolios = query.offset(skip).limit(limit).all()
    
    result = []
    for portfolio in portfolios:
        item_count = db.query(func.count(PortfolioItem.id)).filter(
            PortfolioItem.portfolio_id == portfolio.id
        ).scalar() or 0
        portfolio_dict = PortfolioAdminOut.model_validate(portfolio).model_dump()
        portfolio_dict['item_count'] = item_count
        result.append(PortfolioAdminOut(**portfolio_dict))
    
    return result


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioAdminOut)
def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes de um portfolio"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    item_count = db.query(func.count(PortfolioItem.id)).filter(
        PortfolioItem.portfolio_id == portfolio.id
    ).scalar() or 0
    
    portfolio_dict = PortfolioAdminOut.model_validate(portfolio).model_dump()
    portfolio_dict['item_count'] = item_count
    return PortfolioAdminOut(**portfolio_dict)


@router.post("/portfolios", response_model=PortfolioAdminOut, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    payload: PortfolioAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Criar novo portfolio"""
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar se já existe portfolio com mesmo nome para o usuário
    existing = db.query(Portfolio).filter(
        Portfolio.user_id == payload.user_id,
        Portfolio.name == payload.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Portfolio with this name already exists for this user")
    
    portfolio = Portfolio(
        user_id=payload.user_id,
        name=payload.name,
        category=payload.category,
        description=payload.description
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    portfolio_dict = PortfolioAdminOut.model_validate(portfolio).model_dump()
    portfolio_dict['item_count'] = 0
    return PortfolioAdminOut(**portfolio_dict)


@router.put("/portfolios/{portfolio_id}", response_model=PortfolioAdminOut)
def update_portfolio(
    portfolio_id: int,
    payload: PortfolioAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Atualizar portfolio"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    if payload.user_id is not None:
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        portfolio.user_id = payload.user_id
    
    if payload.name is not None:
        # Verificar se o novo nome já existe para o usuário
        existing = db.query(Portfolio).filter(
            Portfolio.user_id == portfolio.user_id,
            Portfolio.name == payload.name,
            Portfolio.id != portfolio_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Portfolio with this name already exists for this user")
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
    
    portfolio_dict = PortfolioAdminOut.model_validate(portfolio).model_dump()
    portfolio_dict['item_count'] = item_count
    return PortfolioAdminOut(**portfolio_dict)


@router.delete("/portfolios/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Deletar portfolio"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    db.delete(portfolio)
    db.commit()
    return None


# ============================================================================
# PORTFOLIO ITEMS CRUD
# ============================================================================

@router.get("/portfolio", response_model=List[PortfolioItemAdminOut])
def list_portfolio_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Listar todos os itens de portfólio"""
    items = db.query(PortfolioItem).offset(skip).limit(limit).all()
    return items


@router.get("/portfolio/{item_id}", response_model=PortfolioItemAdminOut)
def get_portfolio_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes de um item de portfólio"""
    item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")
    return item


@router.post("/portfolio", response_model=PortfolioItemAdminOut, status_code=status.HTTP_201_CREATED)
def create_portfolio_item(
    payload: PortfolioItemAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Criar novo item de portfólio"""
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar se o portfolio existe e pertence ao usuário
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == payload.portfolio_id,
        Portfolio.user_id == payload.user_id
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found or does not belong to user")
    
    item = PortfolioItem(
        user_id=payload.user_id,
        portfolio_id=payload.portfolio_id,
        ticker=payload.ticker,
        quantity=payload.quantity,
        purchase_price=payload.purchase_price,
        purchase_date=payload.purchase_date,
        sold_price=payload.sold_price,
        sold_date=payload.sold_date
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/portfolio/{item_id}", response_model=PortfolioItemAdminOut)
def update_portfolio_item(
    item_id: int,
    payload: PortfolioItemAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Atualizar item de portfólio"""
    item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")
    
    if payload.user_id is not None:
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        item.user_id = payload.user_id
    
    if payload.portfolio_id is not None:
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == payload.portfolio_id,
            Portfolio.user_id == item.user_id
        ).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found or does not belong to user")
        item.portfolio_id = payload.portfolio_id
    
    if payload.ticker is not None:
        item.ticker = payload.ticker
    if payload.quantity is not None:
        item.quantity = payload.quantity
    if payload.purchase_price is not None:
        item.purchase_price = payload.purchase_price
    if payload.purchase_date is not None:
        item.purchase_date = payload.purchase_date
    if payload.sold_price is not None:
        item.sold_price = payload.sold_price
    if payload.sold_date is not None:
        item.sold_date = payload.sold_date
    
    db.commit()
    db.refresh(item)
    return item


@router.delete("/portfolio/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Deletar item de portfólio"""
    item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")
    
    db.delete(item)
    db.commit()
    return None

