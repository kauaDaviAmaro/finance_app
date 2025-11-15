from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, cast, Date
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import (
    User, Alert, PortfolioItem, Portfolio, WatchlistItem, 
    TickerPrice, DailyScanResult, SupportMessage, UserRole
)
from app.schemas.admin import (
    UserAdminOut, UserAdminCreate, UserAdminUpdate,
    AlertAdminOut, AlertAdminCreate, AlertAdminUpdate,
    PortfolioAdminOut, PortfolioAdminCreate, PortfolioAdminUpdate,
    PortfolioItemAdminOut, PortfolioItemAdminCreate, PortfolioItemAdminUpdate,
    WatchlistItemAdminOut, WatchlistItemAdminCreate, WatchlistItemAdminUpdate,
    TickerPriceAdminOut, TickerPriceAdminCreate, TickerPriceAdminUpdate,
    DailyScanResultAdminOut, DailyScanResultAdminCreate, DailyScanResultAdminUpdate,
    SupportMessageAdminOut, SupportMessageAdminCreate, SupportMessageAdminUpdate,
    AdminStats
)
from app.core.security import get_admin_user, get_current_user, hash_password
from app.core.notification_service import create_notification
from app.db.models import NotificationType

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
    default_email = f"admin_{timestamp}@system.local"
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


# ============================================================================
# DASHBOARD / STATS
# ============================================================================

@router.get("/stats", response_model=AdminStats)
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Estatísticas gerais para o dashboard do admin"""
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    pro_users = db.query(func.count(User.id)).filter(User.role == UserRole.PRO).scalar() or 0
    admin_users = db.query(func.count(User.id)).filter(User.role == UserRole.ADMIN).scalar() or 0
    
    total_alerts = db.query(func.count(Alert.id)).scalar() or 0
    active_alerts = db.query(func.count(Alert.id)).filter(Alert.is_active == True).scalar() or 0
    
    total_portfolios = db.query(func.count(Portfolio.id)).scalar() or 0
    total_portfolio_items = db.query(func.count(PortfolioItem.id)).scalar() or 0
    total_watchlist_items = db.query(func.count(WatchlistItem.id)).scalar() or 0
    total_ticker_prices = db.query(func.count(TickerPrice.ticker)).scalar() or 0
    total_scan_results = db.query(func.count(DailyScanResult.ticker)).scalar() or 0
    total_support_messages = db.query(func.count(SupportMessage.id)).scalar() or 0
    pending_support_messages = db.query(func.count(SupportMessage.id)).filter(SupportMessage.status == "pending").scalar() or 0
    
    # Users por role
    users_by_role = {}
    for role in UserRole:
        count = db.query(func.count(User.id)).filter(User.role == role).scalar() or 0
        users_by_role[role.value] = count
    
    # Alerts por tipo
    alerts_by_type = {}
    alert_types = db.query(Alert.indicator_type).distinct().all()
    for (alert_type,) in alert_types:
        count = db.query(func.count(Alert.id)).filter(Alert.indicator_type == alert_type).scalar() or 0
        alerts_by_type[alert_type] = count
    
    # Usuários ao longo do tempo (últimos 30 dias ou desde o primeiro usuário)
    users_over_time = {}
    if total_users > 0:
        # Buscar data do primeiro usuário
        first_user_date = db.query(func.min(User.created_at)).scalar()
        if first_user_date:
            # Converter para datetime se necessário
            if isinstance(first_user_date, datetime):
                first_date = first_user_date.date()
            else:
                first_date = first_user_date
            
            # Determinar período: últimos 30 dias ou desde o primeiro usuário
            today = datetime.now().date()
            days_since_first = (today - first_date).days
            
            if days_since_first > 30:
                start_date = today - timedelta(days=30)
            else:
                start_date = first_date
            
            # Query para contar usuários criados até cada data
            # Para cada data no intervalo, contar quantos usuários foram criados até aquela data
            current_date = start_date
            end_date = today
            
            # Primeiro, buscar contagem de usuários criados antes do período
            users_before = db.query(func.count(User.id)).filter(
                cast(User.created_at, Date) < start_date
            ).scalar() or 0
            
            # Agrupar novos usuários por data no período
            user_counts = db.query(
                cast(User.created_at, Date).label('date'),
                func.count(User.id).label('count')
            ).filter(
                cast(User.created_at, Date) >= start_date
            ).group_by(
                cast(User.created_at, Date)
            ).order_by(
                cast(User.created_at, Date)
            ).all()
            
            # Criar dicionário com contagem por data
            date_counts = {row.date: row.count for row in user_counts}
            
            # Criar contagem cumulativa
            cumulative = users_before
            while current_date <= end_date:
                if current_date in date_counts:
                    cumulative += date_counts[current_date]
                users_over_time[current_date.isoformat()] = cumulative
                current_date += timedelta(days=1)
    
    return AdminStats(
        total_users=total_users,
        active_users=active_users,
        pro_users=pro_users,
        admin_users=admin_users,
        total_alerts=total_alerts,
        active_alerts=active_alerts,
        total_portfolios=total_portfolios,
        total_portfolio_items=total_portfolio_items,
        total_watchlist_items=total_watchlist_items,
        total_ticker_prices=total_ticker_prices,
        total_scan_results=total_scan_results,
        total_support_messages=total_support_messages,
        pending_support_messages=pending_support_messages,
        users_by_role=users_by_role,
        alerts_by_type=alerts_by_type,
        users_over_time=users_over_time
    )


# ============================================================================
# USERS CRUD
# ============================================================================

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


# ============================================================================
# ALERTS CRUD
# ============================================================================

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


# ============================================================================
# PORTFOLIOS CRUD
# ============================================================================

@router.get("/portfolios", response_model=List[PortfolioAdminOut])
def list_portfolios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = Query(None, description="Filtrar por user_id"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Listar todos os portfolios"""
    query = db.query(Portfolio)
    if user_id:
        query = query.filter(Portfolio.user_id == user_id)
    
    portfolios = query.offset(skip).limit(limit).all()
    
    result = []
    for portfolio in portfolios:
        item_count = db.query(func.count(PortfolioItem.id)).filter(
            PortfolioItem.portfolio_id == portfolio.id
        ).scalar() or 0
        portfolio_dict = PortfolioAdminOut.model_validate(portfolio).model_dump()
        portfolio_dict['item_count'] = item_count
        result.append(PortfolioAdminOut(**portfolio_dict))
    
    return result


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioAdminOut)
def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes de um portfolio"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    item_count = db.query(func.count(PortfolioItem.id)).filter(
        PortfolioItem.portfolio_id == portfolio.id
    ).scalar() or 0
    
    portfolio_dict = PortfolioAdminOut.model_validate(portfolio).model_dump()
    portfolio_dict['item_count'] = item_count
    return PortfolioAdminOut(**portfolio_dict)


@router.post("/portfolios", response_model=PortfolioAdminOut, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    payload: PortfolioAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Criar novo portfolio"""
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar se já existe portfolio com mesmo nome para o usuário
    existing = db.query(Portfolio).filter(
        Portfolio.user_id == payload.user_id,
        Portfolio.name == payload.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Portfolio with this name already exists for this user")
    
    portfolio = Portfolio(
        user_id=payload.user_id,
        name=payload.name,
        category=payload.category,
        description=payload.description
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    portfolio_dict = PortfolioAdminOut.model_validate(portfolio).model_dump()
    portfolio_dict['item_count'] = 0
    return PortfolioAdminOut(**portfolio_dict)


@router.put("/portfolios/{portfolio_id}", response_model=PortfolioAdminOut)
def update_portfolio(
    portfolio_id: int,
    payload: PortfolioAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Atualizar portfolio"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    if payload.user_id is not None:
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        portfolio.user_id = payload.user_id
    
    if payload.name is not None:
        # Verificar se o novo nome já existe para o usuário
        existing = db.query(Portfolio).filter(
            Portfolio.user_id == portfolio.user_id,
            Portfolio.name == payload.name,
            Portfolio.id != portfolio_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Portfolio with this name already exists for this user")
        portfolio.name = payload.name
    
    if payload.category is not None:
        portfolio.category = payload.category
    if payload.description is not None:
        portfolio.description = payload.description
    
    db.commit()
    db.refresh(portfolio)
    
    item_count = db.query(func.count(PortfolioItem.id)).filter(
        PortfolioItem.portfolio_id == portfolio.id
    ).scalar() or 0
    
    portfolio_dict = PortfolioAdminOut.model_validate(portfolio).model_dump()
    portfolio_dict['item_count'] = item_count
    return PortfolioAdminOut(**portfolio_dict)


@router.delete("/portfolios/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Deletar portfolio"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    db.delete(portfolio)
    db.commit()
    return None


# ============================================================================
# PORTFOLIO ITEMS CRUD
# ============================================================================

@router.get("/portfolio", response_model=List[PortfolioItemAdminOut])
def list_portfolio_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Listar todos os itens de portfólio"""
    items = db.query(PortfolioItem).offset(skip).limit(limit).all()
    return items


@router.get("/portfolio/{item_id}", response_model=PortfolioItemAdminOut)
def get_portfolio_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes de um item de portfólio"""
    item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")
    return item


@router.post("/portfolio", response_model=PortfolioItemAdminOut, status_code=status.HTTP_201_CREATED)
def create_portfolio_item(
    payload: PortfolioItemAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Criar novo item de portfólio"""
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar se o portfolio existe e pertence ao usuário
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == payload.portfolio_id,
        Portfolio.user_id == payload.user_id
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found or does not belong to user")
    
    item = PortfolioItem(
        user_id=payload.user_id,
        portfolio_id=payload.portfolio_id,
        ticker=payload.ticker,
        quantity=payload.quantity,
        purchase_price=payload.purchase_price,
        purchase_date=payload.purchase_date,
        sold_price=payload.sold_price,
        sold_date=payload.sold_date
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/portfolio/{item_id}", response_model=PortfolioItemAdminOut)
def update_portfolio_item(
    item_id: int,
    payload: PortfolioItemAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Atualizar item de portfólio"""
    item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")
    
    if payload.user_id is not None:
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        item.user_id = payload.user_id
    
    if payload.portfolio_id is not None:
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == payload.portfolio_id,
            Portfolio.user_id == item.user_id
        ).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found or does not belong to user")
        item.portfolio_id = payload.portfolio_id
    
    if payload.ticker is not None:
        item.ticker = payload.ticker
    if payload.quantity is not None:
        item.quantity = payload.quantity
    if payload.purchase_price is not None:
        item.purchase_price = payload.purchase_price
    if payload.purchase_date is not None:
        item.purchase_date = payload.purchase_date
    if payload.sold_price is not None:
        item.sold_price = payload.sold_price
    if payload.sold_date is not None:
        item.sold_date = payload.sold_date
    
    db.commit()
    db.refresh(item)
    return item


@router.delete("/portfolio/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Deletar item de portfólio"""
    item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")
    
    db.delete(item)
    db.commit()
    return None


# ============================================================================
# WATCHLIST ITEMS CRUD
# ============================================================================

@router.get("/watchlist", response_model=List[WatchlistItemAdminOut])
def list_watchlist_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Listar todos os itens de watchlist"""
    items = db.query(WatchlistItem).offset(skip).limit(limit).all()
    return items


@router.get("/watchlist/{item_id}", response_model=WatchlistItemAdminOut)
def get_watchlist_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes de um item de watchlist"""
    item = db.query(WatchlistItem).filter(WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return item


@router.post("/watchlist", response_model=WatchlistItemAdminOut, status_code=status.HTTP_201_CREATED)
def create_watchlist_item(
    payload: WatchlistItemAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Criar novo item de watchlist"""
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar constraint único
    existing = db.query(WatchlistItem).filter(
        and_(WatchlistItem.user_id == payload.user_id, WatchlistItem.ticker == payload.ticker)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Watchlist item already exists for this user and ticker")
    
    item = WatchlistItem(
        user_id=payload.user_id,
        ticker=payload.ticker
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/watchlist/{item_id}", response_model=WatchlistItemAdminOut)
def update_watchlist_item(
    item_id: int,
    payload: WatchlistItemAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Atualizar item de watchlist"""
    item = db.query(WatchlistItem).filter(WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    if payload.user_id is not None:
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        item.user_id = payload.user_id
    
    if payload.ticker is not None:
        # Verificar constraint único se user_id ou ticker mudarem
        user_id = payload.user_id if payload.user_id is not None else item.user_id
        ticker = payload.ticker
        existing = db.query(WatchlistItem).filter(
            and_(WatchlistItem.user_id == user_id, WatchlistItem.ticker == ticker, WatchlistItem.id != item_id)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Watchlist item already exists for this user and ticker")
        item.ticker = ticker
    
    db.commit()
    db.refresh(item)
    return item


@router.delete("/watchlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Deletar item de watchlist"""
    item = db.query(WatchlistItem).filter(WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    db.delete(item)
    db.commit()
    return None


# ============================================================================
# TICKER PRICES CRUD
# ============================================================================

@router.get("/ticker-prices", response_model=List[TickerPriceAdminOut])
def list_ticker_prices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Listar todos os preços de tickers"""
    prices = db.query(TickerPrice).offset(skip).limit(limit).all()
    return prices


@router.get("/ticker-prices/{ticker}", response_model=TickerPriceAdminOut)
def get_ticker_price(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes de um preço de ticker"""
    price = db.query(TickerPrice).filter(TickerPrice.ticker == ticker).first()
    if not price:
        raise HTTPException(status_code=404, detail="Ticker price not found")
    return price


@router.post("/ticker-prices", response_model=TickerPriceAdminOut, status_code=status.HTTP_201_CREATED)
def create_ticker_price(
    payload: TickerPriceAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Criar novo preço de ticker"""
    existing = db.query(TickerPrice).filter(TickerPrice.ticker == payload.ticker).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ticker price already exists")
    
    price = TickerPrice(
        ticker=payload.ticker,
        last_price=payload.last_price
    )
    db.add(price)
    db.commit()
    db.refresh(price)
    return price


@router.put("/ticker-prices/{ticker}", response_model=TickerPriceAdminOut)
def update_ticker_price(
    ticker: str,
    payload: TickerPriceAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Atualizar preço de ticker"""
    price = db.query(TickerPrice).filter(TickerPrice.ticker == ticker).first()
    if not price:
        raise HTTPException(status_code=404, detail="Ticker price not found")
    
    if payload.last_price is not None:
        price.last_price = payload.last_price
    if payload.timestamp is not None:
        price.timestamp = payload.timestamp
    
    db.commit()
    db.refresh(price)
    return price


@router.delete("/ticker-prices/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticker_price(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Deletar preço de ticker"""
    price = db.query(TickerPrice).filter(TickerPrice.ticker == ticker).first()
    if not price:
        raise HTTPException(status_code=404, detail="Ticker price not found")
    
    db.delete(price)
    db.commit()
    return None


# ============================================================================
# DAILY SCAN RESULTS CRUD
# ============================================================================

@router.get("/scan-results", response_model=List[DailyScanResultAdminOut])
def list_scan_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Listar todos os resultados de scan"""
    results = db.query(DailyScanResult).offset(skip).limit(limit).all()
    return results


@router.get("/scan-results/{ticker}", response_model=DailyScanResultAdminOut)
def get_scan_result(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obter detalhes de um resultado de scan"""
    result = db.query(DailyScanResult).filter(DailyScanResult.ticker == ticker).first()
    if not result:
        raise HTTPException(status_code=404, detail="Scan result not found")
    return result


@router.post("/scan-results", response_model=DailyScanResultAdminOut, status_code=status.HTTP_201_CREATED)
def create_scan_result(
    payload: DailyScanResultAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Criar novo resultado de scan"""
    existing = db.query(DailyScanResult).filter(DailyScanResult.ticker == payload.ticker).first()
    if existing:
        raise HTTPException(status_code=400, detail="Scan result already exists")
    
    result = DailyScanResult(
        ticker=payload.ticker,
        last_price=payload.last_price,
        rsi_14=payload.rsi_14,
        macd_h=payload.macd_h,
        bb_upper=payload.bb_upper,
        bb_lower=payload.bb_lower
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


@router.put("/scan-results/{ticker}", response_model=DailyScanResultAdminOut)
def update_scan_result(
    ticker: str,
    payload: DailyScanResultAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Atualizar resultado de scan"""
    result = db.query(DailyScanResult).filter(DailyScanResult.ticker == ticker).first()
    if not result:
        raise HTTPException(status_code=404, detail="Scan result not found")
    
    if payload.last_price is not None:
        result.last_price = payload.last_price
    if payload.rsi_14 is not None:
        result.rsi_14 = payload.rsi_14
    if payload.macd_h is not None:
        result.macd_h = payload.macd_h
    if payload.bb_upper is not None:
        result.bb_upper = payload.bb_upper
    if payload.bb_lower is not None:
        result.bb_lower = payload.bb_lower
    if payload.timestamp is not None:
        result.timestamp = payload.timestamp
    
    db.commit()
    db.refresh(result)
    return result


@router.delete("/scan-results/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan_result(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Deletar resultado de scan"""
    result = db.query(DailyScanResult).filter(DailyScanResult.ticker == ticker).first()
    if not result:
        raise HTTPException(status_code=404, detail="Scan result not found")
    
    db.delete(result)
    db.commit()
    return None


# ============================================================================
# SUPPORT MESSAGES CRUD
# ============================================================================

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

