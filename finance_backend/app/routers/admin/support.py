from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.db.models import User, SupportMessage, NotificationType
from app.schemas.admin import SupportMessageAdminOut, SupportMessageAdminCreate, SupportMessageAdminUpdate
from app.core.security import get_admin_user
from app.core.notification_service import create_notification

router = APIRouter()


@router.get("/support", response_model=List[SupportMessageAdminOut])
def list_support_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Listar todas as mensagens de suporte"""
    query = db.query(SupportMessage)
    if status:
        query = query.filter(SupportMessage.status == status)
    messages = query.order_by(SupportMessage.created_at.desc()).offset(skip).limit(limit).all()
    return messages


@router.get("/support/{message_id}", response_model=SupportMessageAdminOut)
def get_support_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes de uma mensagem de suporte"""
    message = db.query(SupportMessage).filter(SupportMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Support message not found")
    return message


@router.post("/support", response_model=SupportMessageAdminOut, status_code=status.HTTP_201_CREATED)
def create_support_message(
    payload: SupportMessageAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Criar nova mensagem de suporte"""
    # Verificar se user existe se user_id fornecido
    if payload.user_id:
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    message = SupportMessage(
        user_id=payload.user_id,
        email=payload.email,
        category=payload.category,
        subject=payload.subject,
        message=payload.message,
        status="pending"
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.put("/support/{message_id}", response_model=SupportMessageAdminOut)
def update_support_message(
    message_id: int,
    payload: SupportMessageAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Atualizar mensagem de suporte (responder ou mudar status)"""
    message = db.query(SupportMessage).filter(SupportMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Support message not found")
    
    if payload.status is not None:
        message.status = payload.status
    
    if payload.admin_response is not None:
        message.admin_response = payload.admin_response
        message.responded_at = datetime.now()
        message.responded_by = current_user.id
        if message.status == "pending":
            message.status = "in_progress"
        
        # Cria notificação para o usuário se ele tiver user_id
        if message.user_id:
            create_notification(
                db=db,
                user_id=message.user_id,
                notification_type=NotificationType.SUPPORT_RESPONSE,
                title="📧 Resposta ao seu suporte",
                message=f"Seu ticket '{message.subject}' foi respondido",
                data={
                    "support_message_id": message.id,
                    "subject": message.subject,
                    "category": message.category
                },
                send_push=True
            )
    
    if payload.responded_by is not None:
        responder = db.query(User).filter(User.id == payload.responded_by).first()
        if not responder:
            raise HTTPException(status_code=404, detail="Responder user not found")
        message.responded_by = payload.responded_by
    
    db.commit()
    db.refresh(message)
    return message


@router.delete("/support/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_support_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Deletar mensagem de suporte"""
    message = db.query(SupportMessage).filter(SupportMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Support message not found")
    
    db.delete(message)
    db.commit()
    return None

