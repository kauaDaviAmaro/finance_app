from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, Alert
from app.schemas.alert import AlertCreate, AlertOut, AlertListResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# Validações de tipos de indicadores e condições permitidas
VALID_INDICATORS = ["MACD", "RSI", "STOCHASTIC", "BBANDS"]
VALID_CONDITIONS = ["CROSS_ABOVE", "CROSS_BELOW", "GREATER_THAN", "LESS_THAN"]


def validate_alert_data(indicator_type: str, condition: str, threshold_value: float = None):
    """
    Valida se o tipo de indicador e condição são válidos.
    """
    if indicator_type.upper() not in VALID_INDICATORS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de indicador inválido. Permitidos: {', '.join(VALID_INDICATORS)}"
        )
    
    if condition.upper() not in VALID_CONDITIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Condição inválida. Permitidas: {', '.join(VALID_CONDITIONS)}"
        )
    
    # Para condições GREATER_THAN e LESS_THAN, threshold_value é obrigatório
    if condition.upper() in ["GREATER_THAN", "LESS_THAN"] and threshold_value is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"threshold_value é obrigatório para a condição {condition}"
        )


@router.post("", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cria um novo alerta para um indicador técnico.
    """
    validate_alert_data(payload.indicator_type, payload.condition, payload.threshold_value)
    
    alert = Alert(
        user_id=current_user.id,
        ticker=payload.ticker.upper(),
        indicator_type=payload.indicator_type.upper(),
        condition=payload.condition.upper(),
        threshold_value=payload.threshold_value
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return alert


@router.get("", response_model=AlertListResponse)
def get_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos os alertas do usuário (ativos e inativos).
    """
    alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id
    ).order_by(Alert.created_at.desc()).all()
    
    return AlertListResponse(alerts=alerts)


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de um alerta específico.
    """
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta não encontrado"
        )
    
    return alert


@router.patch("/{alert_id}/toggle", response_model=AlertOut)
def toggle_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ativa ou desativa um alerta.
    """
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta não encontrado"
        )
    
    alert.is_active = not alert.is_active
    db.commit()
    db.refresh(alert)
    
    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deleta um alerta.
    """
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta não encontrado"
        )
    
    db.delete(alert)
    db.commit()
    
    return None

