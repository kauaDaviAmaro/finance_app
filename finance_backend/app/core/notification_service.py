"""
Serviço para criação e envio de notificações.
"""
import logging
from sqlalchemy.orm import Session
from app.db.models import Notification, PushSubscription, NotificationType
from app.core.push_service import send_push_to_user
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def create_notification(
    db: Session,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    send_push: bool = True
) -> Notification:
    """
    Cria uma notificação no banco de dados e opcionalmente envia push notification.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
        notification_type: Tipo da notificação
        title: Título da notificação
        message: Mensagem da notificação
        data: Dados adicionais (opcional)
        send_push: Se deve enviar push notification (padrão: True)
    
    Returns:
        Objeto Notification criado
    """
    # Cria a notificação no banco
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        data=data
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    # Envia push notification se solicitado
    if send_push:
        try:
            # Busca todas as subscriptions do usuário
            subscriptions = db.query(PushSubscription).filter(
                PushSubscription.user_id == user_id
            ).all()
            
            if subscriptions:
                # Prepara subscriptions no formato esperado
                subscription_list = []
                for sub in subscriptions:
                    subscription_list.append({
                        "endpoint": sub.endpoint,
                        "keys": {
                            "p256dh": sub.p256dh_key,
                            "auth": sub.auth_key
                        }
                    })
                
                # Envia push para todas as subscriptions
                send_push_to_user(
                    subscription_list,
                    title,
                    message,
                    data
                )
        except Exception as e:
            logger.error(f"Erro ao enviar push notification: {e}", exc_info=True)
            # Não falha a criação da notificação se o push falhar
    
    return notification

