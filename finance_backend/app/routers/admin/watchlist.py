from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from app.db.database import get_db
from app.db.models import User, WatchlistItem
from app.schemas.admin import WatchlistItemAdminOut, WatchlistItemAdminCreate, WatchlistItemAdminUpdate
from app.core.security import get_admin_user

router = APIRouter()


@router.get("/watchlist", response_model=List[WatchlistItemAdminOut])
def list_watchlist_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Listar todos os itens de watchlist"""
    items = db.query(WatchlistItem).offset(skip).limit(limit).all()
    return items


@router.get("/watchlist/{item_id}", response_model=WatchlistItemAdminOut)
def get_watchlist_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes de um item de watchlist"""
    item = db.query(WatchlistItem).filter(WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return item


@router.post("/watchlist", response_model=WatchlistItemAdminOut, status_code=status.HTTP_201_CREATED)
def create_watchlist_item(
    payload: WatchlistItemAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Criar novo item de watchlist"""
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar constraint único
    existing = db.query(WatchlistItem).filter(
        and_(WatchlistItem.user_id == payload.user_id, WatchlistItem.ticker == payload.ticker)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Watchlist item already exists for this user and ticker")
    
    item = WatchlistItem(
        user_id=payload.user_id,
        ticker=payload.ticker
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/watchlist/{item_id}", response_model=WatchlistItemAdminOut)
def update_watchlist_item(
    item_id: int,
    payload: WatchlistItemAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Atualizar item de watchlist"""
    item = db.query(WatchlistItem).filter(WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    if payload.user_id is not None:
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        item.user_id = payload.user_id
    
    if payload.ticker is not None:
        # Verificar constraint único se user_id ou ticker mudarem
        user_id = payload.user_id if payload.user_id is not None else item.user_id
        ticker = payload.ticker
        existing = db.query(WatchlistItem).filter(
            and_(WatchlistItem.user_id == user_id, WatchlistItem.ticker == ticker, WatchlistItem.id != item_id)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Watchlist item already exists for this user and ticker")
        item.ticker = ticker
    
    db.commit()
    db.refresh(item)
    return item


@router.delete("/watchlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Deletar item de watchlist"""
    item = db.query(WatchlistItem).filter(WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    db.delete(item)
    db.commit()
    return None

