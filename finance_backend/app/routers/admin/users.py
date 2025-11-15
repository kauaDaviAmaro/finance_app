from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import User, UserRole
from app.schemas.admin import UserAdminOut, UserAdminCreate, UserAdminUpdate
from app.core.security import get_admin_user, get_current_user, hash_password

router = APIRouter()


def create_new_admin_automatically(db: Session) -> User:
    """
    Cria automaticamente um novo admin quando um admin remove seus privilégios.
    Busca o primeiro usuário PRO ativo, ou se não houver, o primeiro usuário USER ativo.
    Se não houver nenhum, cria um novo usuário admin padrão.
    Nota: Esta função não faz commit, o commit deve ser feito pelo chamador.
    """
    # Primeiro, tentar promover um usuário PRO ativo
    pro_user = db.query(User).filter(
        User.role == UserRole.PRO,
        User.is_active == True,
        User.can_be_admin == True
    ).first()
    
    if pro_user:
        pro_user.role = UserRole.ADMIN
        db.flush()  # Flush para garantir que a mudança seja aplicada antes do commit
        return pro_user
    
    # Se não houver PRO, tentar promover um usuário USER ativo
    user_user = db.query(User).filter(
        User.role == UserRole.USER,
        User.is_active == True,
        User.can_be_admin == True
    ).first()
    
    if user_user:
        user_user.role = UserRole.ADMIN
        db.flush()  # Flush para garantir que a mudança seja aplicada antes do commit
        return user_user
    
    # Se não houver nenhum usuário disponível, criar um novo admin padrão
    # Usar email e username únicos baseados em timestamp
    import time
    timestamp = int(time.time())
    default_email = f"admin_{timestamp}@example.com"
    default_username = f"admin_{timestamp}"
    default_password = f"admin_{timestamp}_change_me"
    
    new_admin = User(
        email=default_email,
        username=default_username,
        hashed_password=hash_password(default_password),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        can_be_admin=True
    )
    db.add(new_admin)
    db.flush()  # Flush para garantir que o novo admin seja adicionado antes do commit
    return new_admin


@router.get("/users", response_model=List[UserAdminOut])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Listar todos os usuários com paginação"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserAdminOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes de um usuário"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users/{user_id}/details")
def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes completos de um usuário (portfolio, alerts, watchlist, support)"""
    from app.db.models import Portfolio, PortfolioItem, Alert, WatchlistItem, SupportMessage
    from app.schemas.admin import (
        PortfolioAdminOut, PortfolioItemAdminOut, AlertAdminOut,
        WatchlistItemAdminOut, SupportMessageAdminOut
    )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Buscar portfolios
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
    portfolios_with_counts = []
    for portfolio in portfolios:
        item_count = db.query(func.count(PortfolioItem.id)).filter(
            PortfolioItem.portfolio_id == portfolio.id
        ).scalar() or 0
        portfolio_dict = PortfolioAdminOut.model_validate(portfolio).model_dump()
        portfolio_dict['item_count'] = item_count
        portfolios_with_counts.append(portfolio_dict)
    
    # Buscar portfolio items
    portfolio_items = db.query(PortfolioItem).filter(PortfolioItem.user_id == user_id).all()
    
    # Buscar alerts
    alerts = db.query(Alert).filter(Alert.user_id == user_id).all()
    
    # Buscar watchlist items
    watchlist_items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user_id).all()
    
    # Buscar support messages
    support_messages = db.query(SupportMessage).filter(SupportMessage.user_id == user_id).all()
    
    return {
        "user": UserAdminOut.model_validate(user),
        "portfolios": portfolios_with_counts,
        "portfolio_items": [PortfolioItemAdminOut.model_validate(item) for item in portfolio_items],
        "alerts": [AlertAdminOut.model_validate(alert) for alert in alerts],
        "watchlist_items": [WatchlistItemAdminOut.model_validate(item) for item in watchlist_items],
        "support_messages": [SupportMessageAdminOut.model_validate(msg) for msg in support_messages]
    }


@router.post("/users", response_model=UserAdminOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Criar novo usuário"""
    # Verificar email único
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Verificar username único
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        is_active=payload.is_active,
        is_verified=payload.is_verified,
        role=payload.role,
        stripe_customer_id=payload.stripe_customer_id,
        subscription_status=payload.subscription_status
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserAdminOut)
def update_user(
    user_id: int,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Atualizar usuário"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar email único se estiver sendo alterado
    if payload.email and payload.email != user.email:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = payload.email
    
    # Verificar username único se estiver sendo alterado
    if payload.username and payload.username != user.username:
        existing = db.query(User).filter(User.username == payload.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = payload.username
    
    # Atualizar outros campos
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.is_verified is not None:
        user.is_verified = payload.is_verified
    
    # Lógica especial para mudança de role de admin
    if payload.role is not None and payload.role != user.role:
        # Se o usuário sendo atualizado é o próprio admin atual e está mudando de ADMIN para outro role
        if user.id == current_user.id and user.role == UserRole.ADMIN and payload.role != UserRole.ADMIN:
            # Impedir que ele volte a ser admin
            user.can_be_admin = False
            user.role = payload.role
            # Criar automaticamente um novo admin
            create_new_admin_automatically(db)
        # Se está tentando tornar um usuário admin, verificar se ele pode ser admin
        elif payload.role == UserRole.ADMIN and not user.can_be_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este usuário não pode voltar a ser admin"
            )
        else:
            user.role = payload.role
    
    if payload.stripe_customer_id is not None:
        user.stripe_customer_id = payload.stripe_customer_id
    if payload.subscription_status is not None:
        user.subscription_status = payload.subscription_status
    
    # Atualizar password se fornecido
    if payload.password:
        user.hashed_password = hash_password(payload.password)
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Deletar usuário (CASCADE deletará alerts, portfolios, watchlists)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevenir deletar o último admin
    if user.role == UserRole.ADMIN:
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível deletar o último usuário admin. Promova outro usuário a admin primeiro."
            )
    
    db.delete(user)
    db.commit()
    return None


class ChangeRoleRequest(BaseModel):
    role: UserRole


@router.post("/change-my-role", response_model=UserAdminOut)
def change_my_role(
    payload: ChangeRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permite que um admin mude seu próprio role (tier).
    Se um admin muda de ADMIN para outro role, não pode mais voltar a ser admin
    e um novo admin é criado automaticamente.
    """
    if payload.role not in [UserRole.ADMIN, UserRole.PRO, UserRole.USER]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role inválido"
        )
    
    # Se está tentando voltar a ser ADMIN
    if payload.role == UserRole.ADMIN:
        # Verificar se o usuário pode ser admin
        if not current_user.can_be_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não pode voltar a ser admin"
            )
        # Permitir mudança para ADMIN
        current_user.role = payload.role
    # Se está mudando de ADMIN para outro role
    elif current_user.role == UserRole.ADMIN and payload.role != UserRole.ADMIN:
        # Impedir que ele volte a ser admin
        current_user.can_be_admin = False
        current_user.role = payload.role
        # Criar automaticamente um novo admin
        create_new_admin_automatically(db)
    # Se não é admin e está tentando mudar para outro role (não ADMIN)
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas admins podem mudar seu próprio role"
        )
    else:
        # Caso normal: admin mudando para outro role (já tratado acima)
        current_user.role = payload.role
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

