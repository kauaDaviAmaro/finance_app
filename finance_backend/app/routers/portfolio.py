from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import Optional
from app.db.database import get_db
from app.db.models import User, PortfolioItem, Portfolio
from app.schemas.portfolio import (
    PortfolioItemCreate, PortfolioItemUpdate, PortfolioItemOut, PortfolioSummary,
    PortfolioCreate, PortfolioUpdate, PortfolioOut, PortfolioList
)
from app.core.security import get_current_user
from app.core.market_service import get_current_price
from app.db.models import UserRole

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


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


# ========== Portfolio CRUD Routes ==========

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


# ========== Portfolio Item Routes ==========

@router.post("", response_model=PortfolioItemOut, status_code=status.HTTP_201_CREATED)
def add_portfolio_item(
    payload: PortfolioItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Adiciona uma posição (compra) ao portfolio.
    """
    # Verificar se o portfolio existe e pertence ao usuário
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == payload.portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio não encontrado"
        )
    
    portfolio_item = PortfolioItem(
        user_id=current_user.id,
        portfolio_id=payload.portfolio_id,
        ticker=payload.ticker.upper(),
        quantity=payload.quantity,
        purchase_price=payload.purchase_price,
        purchase_date=payload.purchase_date
    )
    
    db.add(portfolio_item)
    db.commit()
    db.refresh(portfolio_item)
    
    # Buscar preço atual e calcular P&L
    # PRO: usa cache rápido (5 minutos), USER: força busca direta (sem cache)
    cache_threshold = 300 if current_user.role in [UserRole.PRO, UserRole.ADMIN] else 0
    current_price = get_current_price(portfolio_item.ticker, db, cache_threshold_seconds=cache_threshold)
    current_price_decimal = Decimal(str(current_price)) if current_price else None
    realized_pnl, unrealized_pnl = calculate_portfolio_pnl(portfolio_item, current_price_decimal)
    
    return PortfolioItemOut(
        id=portfolio_item.id,
        portfolio_id=portfolio_item.portfolio_id,
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
    portfolio_id: int = Query(..., description="ID do portfolio"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todas as posições de um portfolio específico com cálculo de P&L.
    """
    # Verificar se o portfolio existe e pertence ao usuário
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio não encontrado"
        )
    
    items = db.query(PortfolioItem).filter(
        PortfolioItem.portfolio_id == portfolio_id,
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
        # PRO: usa cache rápido (5 minutos), USER: força busca direta (sem cache)
        cache_threshold = 300 if current_user.role in [UserRole.PRO, UserRole.ADMIN] else 0
        current_price = get_current_price(item.ticker, db, cache_threshold_seconds=cache_threshold)
        current_price_decimal = Decimal(str(current_price)) if current_price else None
        
        # Calcular P&L
        realized_pnl, unrealized_pnl = calculate_portfolio_pnl(item, current_price_decimal)
        
        if realized_pnl:
            total_realized_pnl += realized_pnl
        if unrealized_pnl:
            total_unrealized_pnl += unrealized_pnl
        
        positions.append(PortfolioItemOut(
            id=item.id,
            portfolio_id=item.portfolio_id,
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
    # PRO: usa cache rápido (5 minutos), USER: força busca direta (sem cache)
    cache_threshold = 300 if current_user.role in [UserRole.PRO, UserRole.ADMIN] else 0
    current_price = get_current_price(item.ticker, db, cache_threshold_seconds=cache_threshold)
    current_price_decimal = Decimal(str(current_price)) if current_price else None
    realized_pnl, unrealized_pnl = calculate_portfolio_pnl(item, current_price_decimal)
    
    return PortfolioItemOut(
        id=item.id,
        portfolio_id=item.portfolio_id,
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
        portfolio_id=item.portfolio_id,
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

