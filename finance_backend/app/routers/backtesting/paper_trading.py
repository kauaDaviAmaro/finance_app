"""
Router para paper trading (simulação em tempo real).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from decimal import Decimal
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.db.models import User, Strategy, PaperTrade, PaperTradePosition, PaperTradeStatus
from app.schemas.backtesting import (
    PaperTradeStartRequest, PaperTradeOut, PaperTradePositionOut,
    PaperTradeStatusOut
)
from app.core.security import get_pro_user
from app.core.backtesting.paper_trading import PaperTradingEngine

router = APIRouter()


@router.post("/paper-trading/start", response_model=PaperTradeOut, status_code=status.HTTP_201_CREATED)
def start_paper_trading(
    payload: PaperTradeStartRequest,
    current_user: User = Depends(get_pro_user),  # PRO only
    db: Session = Depends(get_db)
):
    """Iniciar paper trading (PRO only)."""
    # Verificar se já existe paper trading ativo ou pausado para este ticker
    active_paper = db.query(PaperTrade).filter(
        PaperTrade.user_id == current_user.id,
        PaperTrade.ticker == payload.ticker,
        PaperTrade.status.in_([PaperTradeStatus.ACTIVE, PaperTradeStatus.PAUSED])
    ).first()
    
    if active_paper:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe um paper trading {'ativo' if active_paper.status == PaperTradeStatus.ACTIVE else 'pausado'} para este ticker. Finalize ou retome a simulação existente."
        )
    
    # Verificar estratégia
    strategy = db.query(Strategy).filter(
        Strategy.id == payload.strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estratégia não encontrada"
        )
    
    initial_capital = payload.initial_capital if payload.initial_capital else strategy.initial_capital
    
    paper_trade = PaperTrade(
        user_id=current_user.id,
        strategy_id=strategy.id,
        ticker=payload.ticker,
        initial_capital=initial_capital,
        current_capital=initial_capital,
        status=PaperTradeStatus.ACTIVE
    )
    
    db.add(paper_trade)
    db.commit()
    db.refresh(paper_trade)
    
    return PaperTradeOut.from_orm(paper_trade)


@router.get("/paper-trading/active", response_model=List[PaperTradeOut])
def get_active_paper_trading(
    current_user: User = Depends(get_pro_user),  # PRO only
    db: Session = Depends(get_db)
):
    """Listar todas as simulações ativas ou pausadas do usuário (PRO only)."""
    paper_trades = db.query(PaperTrade).filter(
        PaperTrade.user_id == current_user.id,
        PaperTrade.status.in_([PaperTradeStatus.ACTIVE, PaperTradeStatus.PAUSED])
    ).order_by(desc(PaperTrade.started_at)).all()
    
    result = []
    for paper_trade in paper_trades:
        # Carregar posições abertas
        paper_trade.positions = db.query(PaperTradePosition).filter(
            PaperTradePosition.paper_trade_id == paper_trade.id,
            PaperTradePosition.exit_date.is_(None)
        ).all()
        result.append(PaperTradeOut.from_orm(paper_trade))
    
    return result


@router.get("/paper-trading", response_model=PaperTradeStatusOut)
def get_paper_trading_status(
    ticker: str = Query(..., description="Ticker para verificar status"),
    current_user: User = Depends(get_pro_user),  # PRO only
    db: Session = Depends(get_db)
):
    """Obter status do paper trading (PRO only)."""
    paper_trade = db.query(PaperTrade).filter(
        PaperTrade.user_id == current_user.id,
        PaperTrade.ticker == ticker,
        PaperTrade.status.in_([PaperTradeStatus.ACTIVE, PaperTradeStatus.PAUSED])
    ).first()
    
    if not paper_trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum paper trading ativo ou pausado encontrado para este ticker"
        )
    
    # Carregar posições
    paper_trade.positions = db.query(PaperTradePosition).filter(
        PaperTradePosition.paper_trade_id == paper_trade.id,
        PaperTradePosition.exit_date.is_(None)  # Apenas posições abertas
    ).all()
    
    # Calcular métricas
    engine = PaperTradingEngine(paper_trade.strategy, paper_trade.ticker, db)
    engine.capital = float(paper_trade.current_capital)
    engine.initial_capital = float(paper_trade.initial_capital)
    
    # Carregar posições abertas
    for pos in paper_trade.positions:
        engine.positions.append({
            'entry_date': pos.entry_date,
            'entry_price': float(pos.entry_price),
            'quantity': pos.quantity,
            'cost': float(pos.entry_price) * pos.quantity
        })
    
    metrics = engine.get_performance_metrics()
    
    return PaperTradeStatusOut(
        paper_trade=PaperTradeOut.from_orm(paper_trade),
        current_equity=Decimal(str(metrics['current_equity'])),
        total_return=Decimal(str(metrics['total_return'])),
        open_positions_count=metrics['open_positions'],
        positions_value=Decimal(str(metrics['positions_value']))
    )


@router.post("/paper-trading/stop", response_model=PaperTradeOut)
def stop_paper_trading(
    paper_trade_id: int = Query(..., description="ID do paper trade"),
    current_user: User = Depends(get_pro_user),  # PRO only
    db: Session = Depends(get_db)
):
    """Parar paper trading (PRO only)."""
    paper_trade = db.query(PaperTrade).filter(
        PaperTrade.id == paper_trade_id,
        PaperTrade.user_id == current_user.id
    ).first()
    
    if not paper_trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper trading não encontrado"
        )
    
    paper_trade.status = PaperTradeStatus.STOPPED
    paper_trade.stopped_at = datetime.now()
    
    db.commit()
    db.refresh(paper_trade)
    
    return PaperTradeOut.from_orm(paper_trade)


@router.post("/paper-trading/pause", response_model=PaperTradeOut)
def pause_paper_trading(
    paper_trade_id: int = Query(..., description="ID do paper trade"),
    current_user: User = Depends(get_pro_user),  # PRO only
    db: Session = Depends(get_db)
):
    """Pausar/retomar paper trading (PRO only)."""
    paper_trade = db.query(PaperTrade).filter(
        PaperTrade.id == paper_trade_id,
        PaperTrade.user_id == current_user.id
    ).first()
    
    if not paper_trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper trading não encontrado"
        )
    
    # Log do status atual
    print(f"Paper trade {paper_trade_id} - Status atual: {paper_trade.status}")
    
    if paper_trade.status == PaperTradeStatus.ACTIVE:
        paper_trade.status = PaperTradeStatus.PAUSED
        print(f"Alterando status de ACTIVE para PAUSED")
    elif paper_trade.status == PaperTradeStatus.PAUSED:
        paper_trade.status = PaperTradeStatus.ACTIVE
        print(f"Alterando status de PAUSED para ACTIVE")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível pausar/retomar um paper trading parado"
        )
    
    db.commit()
    db.refresh(paper_trade)
    
    print(f"Paper trade {paper_trade_id} - Status após commit: {paper_trade.status}")
    
    return PaperTradeOut.from_orm(paper_trade)


@router.get("/paper-trading/positions", response_model=List[PaperTradePositionOut])
def get_paper_trading_positions(
    ticker: str = Query(..., description="Ticker para listar posições"),
    current_user: User = Depends(get_pro_user),  # PRO only
    db: Session = Depends(get_db)
):
    """Listar posições abertas do paper trading (PRO only)."""
    paper_trade = db.query(PaperTrade).filter(
        PaperTrade.user_id == current_user.id,
        PaperTrade.ticker == ticker,
        PaperTrade.status.in_([PaperTradeStatus.ACTIVE, PaperTradeStatus.PAUSED])
    ).first()
    
    if not paper_trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum paper trading ativo ou pausado encontrado para este ticker"
        )
    
    positions = db.query(PaperTradePosition).filter(
        PaperTradePosition.paper_trade_id == paper_trade.id,
        PaperTradePosition.exit_date.is_(None)
    ).all()
    
    return [PaperTradePositionOut.from_orm(pos) for pos in positions]


@router.get("/paper-trading/history", response_model=List[PaperTradeOut])
def get_paper_trading_history(
    current_user: User = Depends(get_pro_user),  # PRO only
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100)
):
    """Histórico completo de paper trading (PRO only)."""
    paper_trades = db.query(PaperTrade).filter(
        PaperTrade.user_id == current_user.id
    ).order_by(desc(PaperTrade.started_at)).limit(limit).all()
    
    result = []
    for paper_trade in paper_trades:
        paper_trade.positions = db.query(PaperTradePosition).filter(
            PaperTradePosition.paper_trade_id == paper_trade.id
        ).all()
        result.append(PaperTradeOut.from_orm(paper_trade))
    
    return result


@router.get("/paper-trading/{paper_trade_id}", response_model=PaperTradeOut)
def get_paper_trading_detail(
    paper_trade_id: int,
    current_user: User = Depends(get_pro_user),  # PRO only
    db: Session = Depends(get_db)
):
    """Obter detalhes de uma simulação específica (PRO only)."""
    paper_trade = db.query(PaperTrade).filter(
        PaperTrade.id == paper_trade_id,
        PaperTrade.user_id == current_user.id
    ).first()
    
    if not paper_trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulação não encontrada"
        )
    
    # Carregar todas as posições (abertas e fechadas)
    paper_trade.positions = db.query(PaperTradePosition).filter(
        PaperTradePosition.paper_trade_id == paper_trade.id
    ).order_by(PaperTradePosition.entry_date.desc()).all()
    
    return PaperTradeOut.from_orm(paper_trade)


@router.get("/paper-trading/{paper_trade_id}/all-positions", response_model=List[PaperTradePositionOut])
def get_paper_trading_all_positions(
    paper_trade_id: int,
    current_user: User = Depends(get_pro_user),  # PRO only
    db: Session = Depends(get_db)
):
    """Obter todas as posições (abertas e fechadas) de uma simulação (PRO only)."""
    paper_trade = db.query(PaperTrade).filter(
        PaperTrade.id == paper_trade_id,
        PaperTrade.user_id == current_user.id
    ).first()
    
    if not paper_trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulação não encontrada"
        )
    
    positions = db.query(PaperTradePosition).filter(
        PaperTradePosition.paper_trade_id == paper_trade.id
    ).order_by(PaperTradePosition.entry_date.desc()).all()
    
    return [PaperTradePositionOut.from_orm(pos) for pos in positions]

