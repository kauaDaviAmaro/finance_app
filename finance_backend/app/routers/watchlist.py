from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, WatchlistItem
from app.schemas.watchlist import WatchlistItemCreate, WatchlistItemOut, WatchlistResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@router.post("", response_model=WatchlistItemOut, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    payload: WatchlistItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Adiciona um ticker à watchlist do usuário.
    """
    # Verificar se já existe
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.ticker == payload.ticker.upper()
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticker {payload.ticker} já está na sua watchlist"
        )
    
    watchlist_item = WatchlistItem(
        user_id=current_user.id,
        ticker=payload.ticker.upper()
    )
    
    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)
    
    return watchlist_item


@router.get("", response_model=WatchlistResponse)
def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos os tickers da watchlist do usuário.
    """
    items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id
    ).order_by(WatchlistItem.created_at.desc()).all()
    
    return WatchlistResponse(items=items)


@router.delete("/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove um ticker da watchlist do usuário.
    """
    watchlist_item = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.ticker == ticker.upper()
    ).first()
    
    if not watchlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker {ticker} não encontrado na sua watchlist"
        )
    
    db.delete(watchlist_item)
    db.commit()
    
    return None

