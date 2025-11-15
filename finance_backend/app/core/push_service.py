"""
Serviço para envio de push notifications usando Web Push API.
"""
import json
import logging
from typing import Optional, Dict, Any
from pywebpush import webpush, WebPushException
from app.core.config import settings

logger = logging.getLogger(__name__)


def send_push_notification(
    subscription_info: Dict[str, Any],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    icon: Optional[str] = None,
    badge: Optional[str] = None,
    tag: Optional[str] = None
) -> bool:
    """
    Envia uma push notification para um subscription.
    
    Args:
        subscription_info: Dicionário com endpoint, keys (p256dh, auth)
        title: Título da notificação
        body: Corpo da notificação
        data: Dados adicionais (opcional)
        icon: URL do ícone (opcional)
        badge: URL do badge (opcional)
        tag: Tag para agrupar notificações (opcional)
    
    Returns:
        True se enviado com sucesso, False caso contrário
    """
    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        logger.warning("VAPID keys não configuradas. Push notification não será enviada.")
        return False
    
    try:
        # Prepara o payload da notificação
        notification_payload = {
            "title": title,
            "body": body,
            "icon": icon or "/favicon.ico",
            "badge": badge or "/favicon.ico",
            "tag": tag,
            "data": data or {}
        }
        
        # Prepara o subscription info no formato esperado pelo pywebpush
        subscription = {
            "endpoint": subscription_info["endpoint"],
            "keys": {
                "p256dh": subscription_info["keys"]["p256dh"],
                "auth": subscription_info["keys"]["auth"]
            }
        }
        
        # Prepara o VAPID info
        vapid_claims = {
            "sub": settings.VAPID_CLAIM_EMAIL
        }
        
        # Envia a push notification
        webpush(
            subscription_info=subscription,
            data=json.dumps(notification_payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims=vapid_claims
        )
        
        logger.info(f"Push notification enviada com sucesso para {subscription_info['endpoint'][:50]}...")
        return True
        
    except WebPushException as e:
        logger.error(f"Erro ao enviar push notification: {e}")
        # Se o subscription é inválido (410), pode ser removido
        if e.response and e.response.status_code == 410:
            logger.warning("Subscription inválido (410). Deve ser removido.")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar push notification: {e}", exc_info=True)
        return False


def send_push_to_user(
    user_subscriptions: list[Dict[str, Any]],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None
) -> int:
    """
    Envia push notification para todas as subscriptions de um usuário.
    
    Args:
        user_subscriptions: Lista de subscriptions do usuário
        title: Título da notificação
        body: Corpo da notificação
        data: Dados adicionais (opcional)
    
    Returns:
        Número de notificações enviadas com sucesso
    """
    success_count = 0
    for subscription in user_subscriptions:
        if send_push_notification(subscription, title, body, data):
            success_count += 1
    
    return success_count
