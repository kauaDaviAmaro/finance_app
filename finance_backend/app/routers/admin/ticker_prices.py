from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import User, TickerPrice
from app.schemas.admin import TickerPriceAdminOut, TickerPriceAdminCreate, TickerPriceAdminUpdate
from app.core.security import get_admin_user

router = APIRouter()


@router.get("/ticker-prices", response_model=List[TickerPriceAdminOut])
def list_ticker_prices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Listar todos os preços de tickers"""
    prices = db.query(TickerPrice).offset(skip).limit(limit).all()
    return prices


@router.get("/ticker-prices/{ticker}", response_model=TickerPriceAdminOut)
def get_ticker_price(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes de um preço de ticker"""
    price = db.query(TickerPrice).filter(TickerPrice.ticker == ticker).first()
    if not price:
        raise HTTPException(status_code=404, detail="Ticker price not found")
    return price


@router.post("/ticker-prices", response_model=TickerPriceAdminOut, status_code=status.HTTP_201_CREATED)
def create_ticker_price(
    payload: TickerPriceAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Criar novo preço de ticker"""
    existing = db.query(TickerPrice).filter(TickerPrice.ticker == payload.ticker).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ticker price already exists")
    
    price = TickerPrice(
        ticker=payload.ticker,
        last_price=payload.last_price
    )
    db.add(price)
    db.commit()
    db.refresh(price)
    return price


@router.put("/ticker-prices/{ticker}", response_model=TickerPriceAdminOut)
def update_ticker_price(
    ticker: str,
    payload: TickerPriceAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Atualizar preço de ticker"""
    price = db.query(TickerPrice).filter(TickerPrice.ticker == ticker).first()
    if not price:
        raise HTTPException(status_code=404, detail="Ticker price not found")
    
    if payload.last_price is not None:
        price.last_price = payload.last_price
    if payload.timestamp is not None:
        price.timestamp = payload.timestamp
    
    db.commit()
    db.refresh(price)
    return price


@router.delete("/ticker-prices/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticker_price(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Deletar preço de ticker"""
    price = db.query(TickerPrice).filter(TickerPrice.ticker == ticker).first()
    if not price:
        raise HTTPException(status_code=404, detail="Ticker price not found")
    
    db.delete(price)
    db.commit()
    return None

