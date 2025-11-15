"""
Router para gerenciar assinaturas e checkout do Stripe.
"""
import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, UserRole
from app.core.security import get_current_user
from app.core.config import settings
from app.schemas.user import SubscriptionStatus
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscription", tags=["Subscription"])

# Configurar Stripe
if hasattr(settings, 'STRIPE_SECRET_KEY') and settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


class CheckoutSessionResponse(BaseModel):
    url: str
    session_id: str


class PortalSessionResponse(BaseModel):
    url: str


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cria uma sessão de checkout do Stripe para o usuário atual.
    """
    if not hasattr(settings, 'STRIPE_SECRET_KEY') or not settings.STRIPE_SECRET_KEY or not hasattr(settings, 'STRIPE_PRICE_ID_PRO') or not settings.STRIPE_PRICE_ID_PRO:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe não configurado corretamente"
        )
    
    # Se usuário já é PRO, retornar erro
    if current_user.role == UserRole.PRO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário já possui assinatura PRO"
        )
    
    try:
        # Criar ou obter customer no Stripe
        customer_id = current_user.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": str(current_user.id)}
            )
            customer_id = customer.id
            current_user.stripe_customer_id = customer_id
            db.commit()
        
        # Criar sessão de checkout
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": settings.STRIPE_PRICE_ID_PRO,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=f"{settings.STRIPE_SUCCESS_URL if hasattr(settings, 'STRIPE_SUCCESS_URL') else 'http://localhost:3000'}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.STRIPE_CANCEL_URL if hasattr(settings, 'STRIPE_CANCEL_URL') else 'http://localhost:3000'}/subscription/cancel",
            metadata={"user_id": str(current_user.id)},
        )
        
        return CheckoutSessionResponse(
            url=checkout_session.url,
            session_id=checkout_session.id
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar sessão de checkout: {str(e)}"
        )


@router.get("/status", response_model=SubscriptionStatus)
def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna o status da assinatura do usuário atual.
    """
    is_pro = current_user.role in [UserRole.PRO, UserRole.ADMIN]
    
    return SubscriptionStatus(
        role=current_user.role,
        subscription_status=current_user.subscription_status,
        is_pro=is_pro
    )


@router.post("/cancel", response_model=PortalSessionResponse)
def create_portal_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cria uma sessão do Customer Portal do Stripe para gerenciar a assinatura.
    
    O Customer Portal permite que o usuário:
    - Cancele a assinatura
    - Atualize o método de pagamento
    - Atualize informações de cobrança
    - Veja histórico de pagamentos
    
    O cancelamento real é feito pelo usuário no portal do Stripe, que então
    dispara um webhook que atualiza o status no banco de dados.
    """
    if not hasattr(settings, 'STRIPE_SECRET_KEY') or not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe não configurado corretamente"
        )
    
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não possui assinatura ativa"
        )
    
    # Verificar se o usuário tem uma assinatura ativa
    if current_user.role != UserRole.PRO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não possui assinatura PRO ativa"
        )
    
    try:
        # Criar sessão do portal
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{settings.STRIPE_RETURN_URL if hasattr(settings, 'STRIPE_RETURN_URL') else 'http://localhost:3000'}/subscription",
        )
        
        return PortalSessionResponse(url=portal_session.url)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar sessão do portal: {str(e)}"
        )


@router.get("/me", response_model=SubscriptionStatus)
def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna informações resumidas da assinatura do usuário atual.
    Compatível com o front para exibir plano/status.
    """
    is_pro = current_user.role in [UserRole.PRO, UserRole.ADMIN]
    return SubscriptionStatus(
        role=current_user.role,
        subscription_status=current_user.subscription_status,
        is_pro=is_pro,
    )
