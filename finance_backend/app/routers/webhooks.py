"""
Router para processar webhooks do Stripe relacionados a assinaturas.
"""
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, UserRole
from app.core.config import settings
from app.core.notification_service import create_notification
from app.db.models import NotificationType
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# Configurar Stripe
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint para receber webhooks do Stripe.
    Processa eventos de assinatura para atualizar o status do usuário.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe webhook secret não configurado"
        )
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    
    # Processar eventos de assinatura
    if event["type"] == "customer.subscription.created":
        handle_subscription_created(event, db)
    elif event["type"] == "customer.subscription.updated":
        handle_subscription_updated(event, db)
    elif event["type"] == "customer.subscription.deleted":
        handle_subscription_deleted(event, db)
    elif event["type"] == "checkout.session.completed":
        handle_checkout_completed(event, db)
    else:
        logger.info(f"Unhandled event type: {event['type']}")
    
    return {"status": "success"}


def handle_subscription_created(event: dict, db: Session):
    """Processa criação de assinatura."""
    try:
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.warning(f"User not found for customer_id: {customer_id}")
            return
        
        # Atualizar usuário para PRO
        user.role = UserRole.PRO
        user.subscription_status = subscription["status"]
        db.commit()
        logger.info(f"User {user.id} upgraded to PRO (subscription created)")
        
        # Criar notificação
        create_notification(
            db=db,
            user_id=user.id,
            notification_type=NotificationType.SUBSCRIPTION_UPDATE,
            title="🎉 Assinatura PRO Ativada!",
            message="Sua assinatura PRO foi ativada com sucesso. Aproveite todos os recursos!",
            data={"subscription_status": subscription["status"]},
            send_push=True
        )
    except Exception as e:
        logger.error(f"Error handling subscription created: {e}")
        db.rollback()
        raise


def handle_subscription_updated(event: dict, db: Session):
    """Processa atualização de assinatura."""
    try:
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.warning(f"User not found for customer_id: {customer_id}")
            return
        
        # Atualizar status da assinatura
        subscription_status = subscription["status"]
        user.subscription_status = subscription_status
        
        # Se assinatura cancelada ou expirada, rebaixar para USER
        if subscription_status in ["canceled", "unpaid", "past_due"]:
            user.role = UserRole.USER
            logger.info(f"User {user.id} downgraded to USER (subscription {subscription_status})")
            
            # Criar notificação
            create_notification(
                db=db,
                user_id=user.id,
                notification_type=NotificationType.SUBSCRIPTION_UPDATE,
                title="⚠️ Assinatura Cancelada",
                message=f"Sua assinatura PRO foi cancelada. Status: {subscription_status}",
                data={"subscription_status": subscription_status},
                send_push=True
            )
        elif subscription_status == "active":
            user.role = UserRole.PRO
            logger.info(f"User {user.id} subscription active (PRO)")
            
            # Criar notificação
            create_notification(
                db=db,
                user_id=user.id,
                notification_type=NotificationType.SUBSCRIPTION_UPDATE,
                title="✅ Assinatura Reativada",
                message="Sua assinatura PRO foi reativada com sucesso!",
                data={"subscription_status": subscription_status},
                send_push=True
            )
        
        db.commit()
    except Exception as e:
        logger.error(f"Error handling subscription updated: {e}")
        db.rollback()
        raise


def handle_subscription_deleted(event: dict, db: Session):
    """Processa cancelamento de assinatura."""
    try:
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.warning(f"User not found for customer_id: {customer_id}")
            return
        
        # Rebaixar para USER
        user.role = UserRole.USER
        user.subscription_status = "canceled"
        db.commit()
        logger.info(f"User {user.id} downgraded to USER (subscription deleted)")
        
        # Criar notificação
        create_notification(
            db=db,
            user_id=user.id,
            notification_type=NotificationType.SUBSCRIPTION_UPDATE,
            title="❌ Assinatura Cancelada",
            message="Sua assinatura PRO foi cancelada. Você ainda pode fazer upgrade a qualquer momento.",
            data={"subscription_status": "canceled"},
            send_push=True
        )
    except Exception as e:
        logger.error(f"Error handling subscription deleted: {e}")
        db.rollback()
        raise


def handle_checkout_completed(event: dict, db: Session):
    """Processa conclusão do checkout."""
    try:
        session = event["data"]["object"]
        customer_id = session.get("customer")
        
        if not customer_id:
            logger.warning("No customer_id in checkout session")
            return
        
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.warning(f"User not found for customer_id: {customer_id}")
            return
        
        # Se já não for PRO, atualizar
        if user.role != UserRole.PRO:
            user.role = UserRole.PRO
            user.subscription_status = "active"
            db.commit()
            logger.info(f"User {user.id} upgraded to PRO (checkout completed)")
            
            # Criar notificação
            create_notification(
                db=db,
                user_id=user.id,
                notification_type=NotificationType.SUBSCRIPTION_UPDATE,
                title="🎉 Bem-vindo ao PRO!",
                message="Pagamento confirmado! Sua assinatura PRO está ativa.",
                data={"subscription_status": "active"},
                send_push=True
            )
    except Exception as e:
        logger.error(f"Error handling checkout completed: {e}")
        db.rollback()
        raise





