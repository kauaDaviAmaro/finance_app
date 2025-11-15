from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import User, Alert
from app.schemas.admin import AlertAdminOut, AlertAdminCreate, AlertAdminUpdate
from app.core.security import get_admin_user

router = APIRouter()


@router.get("/alerts", response_model=List[AlertAdminOut])
def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Listar todos os alertas"""
    alerts = db.query(Alert).offset(skip).limit(limit).all()
    return alerts


@router.get("/alerts/{alert_id}", response_model=AlertAdminOut)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes de um alerta"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts", response_model=AlertAdminOut, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Criar novo alerta"""
    # Verificar se user existe
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    alert = Alert(
        user_id=payload.user_id,
        ticker=payload.ticker,
        indicator_type=payload.indicator_type,
        condition=payload.condition,
        threshold_value=payload.threshold_value,
        is_active=payload.is_active
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.put("/alerts/{alert_id}", response_model=AlertAdminOut)
def update_alert(
    alert_id: int,
    payload: AlertAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Atualizar alerta"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if payload.user_id is not None:
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        alert.user_id = payload.user_id
    
    if payload.ticker is not None:
        alert.ticker = payload.ticker
    if payload.indicator_type is not None:
        alert.indicator_type = payload.indicator_type
    if payload.condition is not None:
        alert.condition = payload.condition
    if payload.threshold_value is not None:
        alert.threshold_value = payload.threshold_value
    if payload.is_active is not None:
        alert.is_active = payload.is_active
    if payload.triggered_at is not None:
        alert.triggered_at = payload.triggered_at
    
    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Deletar alerta"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    db.delete(alert)
    db.commit()
    return None

