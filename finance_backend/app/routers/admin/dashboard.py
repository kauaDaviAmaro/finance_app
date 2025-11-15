from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta
from app.db.database import get_db
from app.db.models import User, Alert, PortfolioItem, Portfolio, WatchlistItem, TickerPrice, DailyScanResult, SupportMessage, UserRole
from app.schemas.admin import AdminStats
from app.core.security import get_admin_user

router = APIRouter()


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

