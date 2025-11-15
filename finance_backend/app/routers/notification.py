from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.db.models import User, Notification, PushSubscription, NotificationType
from app.schemas.notification import (
    PushSubscriptionCreate,
    PushSubscriptionOut,
    NotificationOut,
    NotificationListResponse,
    NotificationReadResponse
)
from app.core.security import get_current_user
from app.core.push_service import send_push_notification
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/vapid-public-key")
def get_vapid_public_key():
    """
    Retorna a chave pública VAPID para o frontend.
    """
    from app.core.config import settings
    
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VAPID public key não configurada"
        )
    
    return {"public_key": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe", response_model=PushSubscriptionOut, status_code=status.HTTP_201_CREATED)
def subscribe_push(
    subscription: PushSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registra uma subscription de push notification para o usuário.
    """
    # Verifica se já existe uma subscription com o mesmo endpoint para este usuário
    existing = db.query(PushSubscription).filter(
        PushSubscription.user_id == current_user.id,
        PushSubscription.endpoint == subscription.endpoint
    ).first()
    
    if existing:
        # Atualiza as chaves se já existe
        existing.p256dh_key = subscription.keys.get("p256dh", "")
        existing.auth_key = subscription.keys.get("auth", "")
        db.commit()
        db.refresh(existing)
        return existing
    
    # Cria nova subscription
    push_sub = PushSubscription(
        user_id=current_user.id,
        endpoint=subscription.endpoint,
        p256dh_key=subscription.keys.get("p256dh", ""),
        auth_key=subscription.keys.get("auth", "")
    )
    
    db.add(push_sub)
    db.commit()
    db.refresh(push_sub)
    
    logger.info(f"Push subscription registrada para usuário {current_user.id}")
    return push_sub


@router.get("", response_model=NotificationListResponse)
def get_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista notificações do usuário.
    """
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    total_unread = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    
    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    return NotificationListResponse(
        notifications=notifications,
        unread_count=total_unread
    )


@router.get("/{notification_id}", response_model=NotificationOut)
def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes de uma notificação específica.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificação não encontrada"
        )
    
    return notification


@router.patch("/{notification_id}/read", response_model=NotificationReadResponse)
def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marca uma notificação como lida.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificação não encontrada"
        )
    
    notification.is_read = True
    db.commit()
    
    return NotificationReadResponse()


@router.patch("/read-all", response_model=dict)
def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marca todas as notificações do usuário como lidas.
    """
    updated = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {"message": f"{updated} notificações marcadas como lidas"}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deleta uma notificação.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificação não encontrada"
        )
    
    db.delete(notification)
    db.commit()
    
    return None
