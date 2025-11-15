from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import SupportMessage, User
from app.schemas.admin import SupportMessageAdminCreate, SupportMessageAdminOut
from app.core.security import get_current_user, get_current_user_optional

router = APIRouter(prefix="/support", tags=["support"])


@router.post("", response_model=SupportMessageAdminOut, status_code=status.HTTP_201_CREATED)
def create_support_message(
    payload: SupportMessageAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Criar nova mensagem de suporte.
    Pode ser usado por usuários autenticados ou não autenticados.
    Se autenticado, o user_id será preenchido automaticamente.
    """
    # Se o usuário estiver autenticado, usar o user_id dele
    user_id = current_user.id if current_user else payload.user_id
    
    # Se não autenticado e não forneceu email, usar o email do payload
    email = current_user.email if current_user else payload.email
    
    message = SupportMessage(
        user_id=user_id,
        email=email,
        category=payload.category,
        subject=payload.subject,
        message=payload.message,
        status="pending"
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


