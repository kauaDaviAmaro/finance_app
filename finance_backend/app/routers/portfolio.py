from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional
from app.db.database import get_db
from app.db.models import User, PortfolioItem
from app.schemas.portfolio import (
    PortfolioItemCreate, PortfolioItemUpdate, PortfolioItemOut, PortfolioSummary
)
from app.core.security import get_current_user
from app.core.market_service import get_current_price

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


def calculate_portfolio_pnl(item: PortfolioItem, current_price: Decimal = None) -> tuple[Optional[Decimal], Optional[Decimal]]:
    """
    Calcula P&L realizado e não realizado para um PortfolioItem.
    Retorna (realized_pnl, unrealized_pnl)
    """
    purchase_value = Decimal(str(item.purchase_price)) * item.quantity
    realized_pnl = None
    unrealized_pnl = None
    
    if item.sold_price and item.sold_date:
        # Posição vendida - calcular P&L realizado
        sold_value = Decimal(str(item.sold_price)) * item.quantity
        realized_pnl = sold_value - purchase_value
    elif current_price:
        # Posição aberta - calcular P&L não realizado
        current_value = current_price * item.quantity
        unrealized_pnl = current_value - purchase_value
    
    return realized_pnl, unrealized_pnl


@router.post("", response_model=PortfolioItemOut, status_code=status.HTTP_201_CREATED)
def add_portfolio_item(
    payload: PortfolioItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Adiciona uma posição (compra) ao portfolio.
    """
    portfolio_item = PortfolioItem(
        user_id=current_user.id,
        ticker=payload.ticker.upper(),
        quantity=payload.quantity,
        purchase_price=payload.purchase_price,
        purchase_date=payload.purchase_date
    )
    
    db.add(portfolio_item)
    db.commit()
    db.refresh(portfolio_item)
    
    # Buscar preço atual e calcular P&L
    current_price = get_current_price(portfolio_item.ticker)
    current_price_decimal = Decimal(str(current_price)) if current_price else None
    realized_pnl, unrealized_pnl = calculate_portfolio_pnl(portfolio_item, current_price_decimal)
    
    return PortfolioItemOut(
        id=portfolio_item.id,
        ticker=portfolio_item.ticker,
        quantity=portfolio_item.quantity,
        purchase_price=portfolio_item.purchase_price,
        purchase_date=portfolio_item.purchase_date,
        sold_price=portfolio_item.sold_price,
        sold_date=portfolio_item.sold_date,
        realized_pnl=realized_pnl,
        unrealized_pnl=unrealized_pnl,
        current_price=current_price_decimal,
        created_at=portfolio_item.created_at,
        updated_at=portfolio_item.updated_at
    )


@router.get("", response_model=PortfolioSummary)
def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todas as posições do portfolio com cálculo de P&L.
    """
    items = db.query(PortfolioItem).filter(
        PortfolioItem.user_id == current_user.id
    ).order_by(PortfolioItem.created_at.desc()).all()
    
    positions = []
    total_invested = Decimal('0')
    total_realized_pnl = Decimal('0')
    total_unrealized_pnl = Decimal('0')
    
    for item in items:
        # Calcular valores para este item
        purchase_value = Decimal(str(item.purchase_price)) * item.quantity
        total_invested += purchase_value
        
        # Buscar preço atual
        current_price = get_current_price(item.ticker)
        current_price_decimal = Decimal(str(current_price)) if current_price else None
        
        # Calcular P&L
        realized_pnl, unrealized_pnl = calculate_portfolio_pnl(item, current_price_decimal)
        
        if realized_pnl:
            total_realized_pnl += realized_pnl
        if unrealized_pnl:
            total_unrealized_pnl += unrealized_pnl
        
        positions.append(PortfolioItemOut(
            id=item.id,
            ticker=item.ticker,
            quantity=item.quantity,
            purchase_price=item.purchase_price,
            purchase_date=item.purchase_date,
            sold_price=item.sold_price,
            sold_date=item.sold_date,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            current_price=current_price_decimal,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))
    
    return PortfolioSummary(
        total_invested=total_invested,
        total_realized_pnl=total_realized_pnl,
        total_unrealized_pnl=total_unrealized_pnl,
        positions=positions
    )


@router.get("/{item_id}", response_model=PortfolioItemOut)
def get_portfolio_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de uma posição específica do portfolio.
    """
    item = db.query(PortfolioItem).filter(
        PortfolioItem.id == item_id,
        PortfolioItem.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Posição não encontrada"
        )
    
    # Buscar preço atual e calcular P&L
    current_price = get_current_price(item.ticker)
    current_price_decimal = Decimal(str(current_price)) if current_price else None
    realized_pnl, unrealized_pnl = calculate_portfolio_pnl(item, current_price_decimal)
    
    return PortfolioItemOut(
        id=item.id,
        ticker=item.ticker,
        quantity=item.quantity,
        purchase_price=item.purchase_price,
        purchase_date=item.purchase_date,
        sold_price=item.sold_price,
        sold_date=item.sold_date,
        realized_pnl=realized_pnl,
        unrealized_pnl=unrealized_pnl,
        current_price=current_price_decimal,
        created_at=item.created_at,
        updated_at=item.updated_at
    )


@router.patch("/{item_id}/sell", response_model=PortfolioItemOut)
def sell_portfolio_item(
    item_id: int,
    payload: PortfolioItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marca uma posição como vendida (parcial ou total).
    """
    item = db.query(PortfolioItem).filter(
        PortfolioItem.id == item_id,
        PortfolioItem.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Posição não encontrada"
        )
    
    if item.sold_price and item.sold_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta posição já foi marcada como vendida"
        )
    
    # Atualizar dados de venda
    item.sold_price = payload.sold_price
    item.sold_date = payload.sold_date
    
    db.commit()
    db.refresh(item)
    
    # Calcular P&L realizado
    realized_pnl, _ = calculate_portfolio_pnl(item, None)
    
    return PortfolioItemOut(
        id=item.id,
        ticker=item.ticker,
        quantity=item.quantity,
        purchase_price=item.purchase_price,
        purchase_date=item.purchase_date,
        sold_price=item.sold_price,
        sold_date=item.sold_date,
        realized_pnl=realized_pnl,
        unrealized_pnl=None,
        current_price=None,
        created_at=item.created_at,
        updated_at=item.updated_at
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove uma posição do portfolio.
    """
    item = db.query(PortfolioItem).filter(
        PortfolioItem.id == item_id,
        PortfolioItem.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Posição não encontrada"
        )
    
    db.delete(item)
    db.commit()
    
    return None

