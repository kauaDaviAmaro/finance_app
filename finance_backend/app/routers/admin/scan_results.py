from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import User, DailyScanResult
from app.schemas.admin import DailyScanResultAdminOut, DailyScanResultAdminCreate, DailyScanResultAdminUpdate
from app.core.security import get_admin_user

router = APIRouter()


@router.get("/scan-results", response_model=List[DailyScanResultAdminOut])
def list_scan_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Listar todos os resultados de scan"""
    results = db.query(DailyScanResult).offset(skip).limit(limit).all()
    return results


@router.get("/scan-results/{ticker}", response_model=DailyScanResultAdminOut)
def get_scan_result(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes de um resultado de scan"""
    result = db.query(DailyScanResult).filter(DailyScanResult.ticker == ticker).first()
    if not result:
        raise HTTPException(status_code=404, detail="Scan result not found")
    return result


@router.post("/scan-results", response_model=DailyScanResultAdminOut, status_code=status.HTTP_201_CREATED)
def create_scan_result(
    payload: DailyScanResultAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Criar novo resultado de scan"""
    existing = db.query(DailyScanResult).filter(DailyScanResult.ticker == payload.ticker).first()
    if existing:
        raise HTTPException(status_code=400, detail="Scan result already exists")
    
    result = DailyScanResult(
        ticker=payload.ticker,
        last_price=payload.last_price,
        rsi_14=payload.rsi_14,
        macd_h=payload.macd_h,
        bb_upper=payload.bb_upper,
        bb_lower=payload.bb_lower
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


@router.put("/scan-results/{ticker}", response_model=DailyScanResultAdminOut)
def update_scan_result(
    ticker: str,
    payload: DailyScanResultAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Atualizar resultado de scan"""
    result = db.query(DailyScanResult).filter(DailyScanResult.ticker == ticker).first()
    if not result:
        raise HTTPException(status_code=404, detail="Scan result not found")
    
    if payload.last_price is not None:
        result.last_price = payload.last_price
    if payload.rsi_14 is not None:
        result.rsi_14 = payload.rsi_14
    if payload.macd_h is not None:
        result.macd_h = payload.macd_h
    if payload.bb_upper is not None:
        result.bb_upper = payload.bb_upper
    if payload.bb_lower is not None:
        result.bb_lower = payload.bb_lower
    if payload.timestamp is not None:
        result.timestamp = payload.timestamp
    
    db.commit()
    db.refresh(result)
    return result


@router.delete("/scan-results/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan_result(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Deletar resultado de scan"""
    result = db.query(DailyScanResult).filter(DailyScanResult.ticker == ticker).first()
    if not result:
        raise HTTPException(status_code=404, detail="Scan result not found")
    
    db.delete(result)
    db.commit()
    return None

