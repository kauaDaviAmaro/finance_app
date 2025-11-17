"""
Router para backtesting e simulação de estratégias.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from decimal import Decimal
from typing import List, Optional
from datetime import datetime, date

from app.db.database import get_db
from app.db.models import (
    User, Strategy, StrategyCondition, Backtest, BacktestTrade,
    PaperTrade, PaperTradePosition, UserRole, StrategyType,
    ConditionType, ConditionLogic, PaperTradeStatus
)
from app.schemas.backtesting import (
    StrategyCreate, StrategyCreateJSON, StrategyUpdate, StrategyOut,
    StrategyConditionCreate, StrategyConditionOut,
    BacktestRunRequest, BacktestOut, BacktestTradeOut, BacktestResultDetail,
    BacktestCompareRequest, BacktestCompareResult,
    PaperTradeStartRequest, PaperTradeOut, PaperTradePositionOut,
    PaperTradeStatusOut, PaperTradeSignal
)
from app.core.security import get_current_user, get_pro_user
from app.core.backtesting.engine import BacktestEngine
from app.core.backtesting.paper_trading import PaperTradingEngine

router = APIRouter(prefix="/backtesting", tags=["Backtesting"])


# ========== Helper Functions ==========

def check_strategy_limit(user: User, db: Session) -> None:
    """Valida se o usuário pode criar mais estratégias baseado no seu plano."""
    if user.role == UserRole.ADMIN:
        return
    
    current_count = db.query(func.count(Strategy.id)).filter(
        Strategy.user_id == user.id
    ).scalar() or 0
    
    limit = 5 if user.role == UserRole.USER else 50
    
    if current_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Limite de estratégias atingido. Seu plano permite {limit} estratégias."
        )


def check_backtest_limit(user: User, db: Session) -> None:
    """Valida se o usuário pode executar mais backtests simultâneos."""
    if user.role == UserRole.ADMIN:
        return
    
    # Contar backtests criados nas últimas 5 minutos (simulação de "simultâneos")
    from datetime import timedelta
    recent_time = datetime.now() - timedelta(minutes=5)
    
    recent_count = db.query(func.count(Backtest.id)).filter(
        Backtest.user_id == user.id,
        Backtest.created_at >= recent_time
    ).scalar() or 0
    
    limit = 1 if user.role == UserRole.USER else 5
    
    if recent_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Limite de backtests simultâneos atingido. Seu plano permite {limit} backtest(s) por vez."
        )


# ========== Strategy CRUD Routes ==========

@router.post("/strategies", response_model=StrategyOut, status_code=status.HTTP_201_CREATED)
def create_strategy(
    payload: StrategyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Criar estratégia via interface gráfica (todos os usuários)."""
    check_strategy_limit(current_user, db)
    
    # Verificar se já existe estratégia com mesmo nome
    existing = db.query(Strategy).filter(
        Strategy.user_id == current_user.id,
        Strategy.name == payload.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma estratégia com este nome"
        )
    
    # Criar estratégia
    strategy = Strategy(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        strategy_type=payload.strategy_type,
        initial_capital=payload.initial_capital,
        position_size=payload.position_size
    )
    
    db.add(strategy)
    db.flush()
    
    # Criar condições
    for cond_data in payload.conditions:
        condition = StrategyCondition(
            strategy_id=strategy.id,
            condition_type=cond_data.condition_type,
            indicator=cond_data.indicator,
            operator=cond_data.operator,
            value=cond_data.value,
            logic=cond_data.logic,
            order=cond_data.order
        )
        db.add(condition)
    
    db.commit()
    db.refresh(strategy)
    
    # Carregar condições
    strategy.conditions = db.query(StrategyCondition).filter(
        StrategyCondition.strategy_id == strategy.id
    ).all()
    
    return StrategyOut.from_orm(strategy)


@router.post("/strategies/json", response_model=StrategyOut, status_code=status.HTTP_201_CREATED)
def create_strategy_json(
    payload: StrategyCreateJSON,
    current_user: User = Depends(get_pro_user),  # PRO only
    db: Session = Depends(get_db)
):
    """Criar estratégia via JSON (PRO only)."""
    check_strategy_limit(current_user, db)
    
    existing = db.query(Strategy).filter(
        Strategy.user_id == current_user.id,
        Strategy.name == payload.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma estratégia com este nome"
        )
    
    strategy = Strategy(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        strategy_type=StrategyType.JSON,
        json_config=payload.json_config,
        initial_capital=payload.initial_capital,
        position_size=payload.position_size
    )
    
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
    return StrategyOut.from_orm(strategy)


@router.get("/strategies", response_model=List[StrategyOut])
def list_strategies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar estratégias do usuário."""
    strategies = db.query(Strategy).filter(
        Strategy.user_id == current_user.id
    ).order_by(Strategy.created_at.desc()).all()
    
    # Limitar histórico para usuários não-PRO
    if current_user.role == UserRole.USER:
        strategies = strategies[:5]  # Limite de 5 estratégias visíveis
    
    result = []
    for strategy in strategies:
        strategy.conditions = db.query(StrategyCondition).filter(
            StrategyCondition.strategy_id == strategy.id
        ).order_by(StrategyCondition.order).all()
        result.append(StrategyOut.from_orm(strategy))
    
    return result


@router.get("/strategies/{strategy_id}", response_model=StrategyOut)
def get_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obter detalhes de uma estratégia."""
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estratégia não encontrada"
        )
    
    strategy.conditions = db.query(StrategyCondition).filter(
        StrategyCondition.strategy_id == strategy.id
    ).order_by(StrategyCondition.order).all()
    
    return StrategyOut.from_orm(strategy)


@router.put("/strategies/{strategy_id}", response_model=StrategyOut)
def update_strategy(
    strategy_id: int,
    payload: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualizar estratégia."""
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estratégia não encontrada"
        )
    
    if payload.name and payload.name != strategy.name:
        existing = db.query(Strategy).filter(
            Strategy.user_id == current_user.id,
            Strategy.name == payload.name,
            Strategy.id != strategy_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe uma estratégia com este nome"
            )
        strategy.name = payload.name
    
    if payload.description is not None:
        strategy.description = payload.description
    if payload.initial_capital is not None:
        strategy.initial_capital = payload.initial_capital
    if payload.position_size is not None:
        strategy.position_size = payload.position_size
    
    # Atualizar condições se fornecidas
    if payload.conditions is not None:
        # Deletar condições antigas
        db.query(StrategyCondition).filter(
            StrategyCondition.strategy_id == strategy_id
        ).delete()
        
        # Criar novas condições
        for cond_data in payload.conditions:
            condition = StrategyCondition(
                strategy_id=strategy.id,
                condition_type=cond_data.condition_type,
                indicator=cond_data.indicator,
                operator=cond_data.operator,
                value=cond_data.value,
                logic=cond_data.logic,
                order=cond_data.order
            )
            db.add(condition)
    
    db.commit()
    db.refresh(strategy)
    
    strategy.conditions = db.query(StrategyCondition).filter(
        StrategyCondition.strategy_id == strategy.id
    ).order_by(StrategyCondition.order).all()
    
    return StrategyOut.from_orm(strategy)


@router.delete("/strategies/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletar estratégia."""
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estratégia não encontrada"
        )
    
    db.delete(strategy)
    db.commit()
    
    return None


# ========== Backtest Routes ==========

@router.post("/run", response_model=BacktestOut, status_code=status.HTTP_201_CREATED)
def run_backtest(
    payload: BacktestRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Executar backtest (1 por vez para USER)."""
    check_backtest_limit(current_user, db)
    
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
    
    # Carregar condições da estratégia
    strategy.conditions = db.query(StrategyCondition).filter(
        StrategyCondition.strategy_id == strategy.id
    ).order_by(StrategyCondition.order).all()
    
    if not strategy.conditions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A estratégia não possui condições definidas"
        )
    
    # Executar backtest
    try:
        engine = BacktestEngine(strategy, payload.ticker, payload.period)
        result = engine.run()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao executar backtest: {str(e)}"
        )
    
    # Salvar resultados
    backtest = Backtest(
        user_id=current_user.id,
        strategy_id=strategy.id,
        ticker=payload.ticker,
        period=payload.period,
        start_date=result.get('start_date'),
        end_date=result.get('end_date'),
        total_return=Decimal(str(result['metrics']['total_return'])),
        annualized_return=Decimal(str(result['metrics']['annualized_return'])),
        sharpe_ratio=Decimal(str(result['metrics']['sharpe_ratio'])),
        max_drawdown=Decimal(str(result['metrics']['max_drawdown'])),
        win_rate=Decimal(str(result['metrics']['win_rate'])),
        profit_factor=Decimal(str(result['metrics']['profit_factor'])),
        total_trades=result['metrics']['total_trades'],
        winning_trades=result['metrics']['winning_trades'],
        losing_trades=result['metrics']['losing_trades'],
        avg_win=Decimal(str(result['metrics']['avg_win'])) if result['metrics']['avg_win'] else None,
        avg_loss=Decimal(str(result['metrics']['avg_loss'])) if result['metrics']['avg_loss'] else None,
        final_capital=Decimal(str(result['metrics']['final_capital']))
    )
    
    db.add(backtest)
    db.flush()
    
    # Salvar trades
    for trade_data in result['trades']:
        trade = BacktestTrade(
            backtest_id=backtest.id,
            trade_date=trade_data['date'],
            trade_type=trade_data['type'],
            price=Decimal(str(trade_data['price'])),
            quantity=trade_data['quantity'],
            pnl=Decimal(str(trade_data['pnl'])) if trade_data['pnl'] is not None else None,
            capital_after=Decimal(str(trade_data['capital_after'])) if trade_data['capital_after'] is not None else None
        )
        db.add(trade)
    
    db.commit()
    db.refresh(backtest)
    
    # Carregar trades
    backtest.trades = db.query(BacktestTrade).filter(
        BacktestTrade.backtest_id == backtest.id
    ).order_by(BacktestTrade.trade_date).all()
    
    return BacktestOut.from_orm(backtest)


@router.get("/results/{backtest_id}", response_model=BacktestResultDetail)
def get_backtest_result(
    backtest_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obter resultado detalhado de um backtest."""
    backtest = db.query(Backtest).filter(
        Backtest.id == backtest_id,
        Backtest.user_id == current_user.id
    ).first()
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest não encontrado"
        )
    
    # Carregar trades
    backtest.trades = db.query(BacktestTrade).filter(
        BacktestTrade.backtest_id == backtest.id
    ).order_by(BacktestTrade.trade_date).all()
    
    # Re-executar para obter equity curve (ou buscar de cache se disponível)
    try:
        strategy = db.query(Strategy).filter(Strategy.id == backtest.strategy_id).first()
        engine = BacktestEngine(strategy, backtest.ticker, backtest.period)
        result = engine.run()
        equity_curve = result.get('equity_curve', [])
    except Exception:
        equity_curve = []
    
    return BacktestResultDetail(
        backtest=BacktestOut.from_orm(backtest),
        equity_curve=equity_curve
    )


@router.get("/results", response_model=List[BacktestOut])
def list_backtest_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100)
):
    """Listar histórico de backtests."""
    query = db.query(Backtest).filter(
        Backtest.user_id == current_user.id
    ).order_by(desc(Backtest.created_at))
    
    # Limitar para usuários não-PRO
    if current_user.role == UserRole.USER:
        limit = min(limit, 10)
    
    backtests = query.limit(limit).all()
    
    result = []
    for backtest in backtests:
        backtest.trades = db.query(BacktestTrade).filter(
            BacktestTrade.backtest_id == backtest.id
        ).order_by(BacktestTrade.trade_date).all()
        result.append(BacktestOut.from_orm(backtest))
    
    return result


@router.post("/compare", response_model=BacktestCompareResult)
def compare_strategies(
    payload: BacktestCompareRequest,
    current_user: User = Depends(get_pro_user),  # PRO only
    db: Session = Depends(get_db)
):
    """Comparar múltiplas estratégias (PRO only)."""
    if len(payload.strategy_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="É necessário pelo menos 2 estratégias para comparação"
        )
    
    # Verificar se todas as estratégias pertencem ao usuário
    strategies = db.query(Strategy).filter(
        Strategy.id.in_(payload.strategy_ids),
        Strategy.user_id == current_user.id
    ).all()
    
    if len(strategies) != len(payload.strategy_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uma ou mais estratégias não foram encontradas"
        )
    
    # Executar backtests para cada estratégia
    backtest_results = []
    errors = []
    
    for strategy in strategies:
        try:
            # Carregar condições da estratégia
            strategy.conditions = db.query(StrategyCondition).filter(
                StrategyCondition.strategy_id == strategy.id
            ).order_by(StrategyCondition.order).all()
            
            if not strategy.conditions:
                errors.append(f"Estratégia '{strategy.name}' não possui condições definidas")
                continue
            
            engine = BacktestEngine(strategy, payload.ticker, payload.period)
            result = engine.run()
            
            if not result or 'metrics' not in result:
                errors.append(f"Estratégia '{strategy.name}' não retornou resultados válidos")
                continue
            
            # Criar objeto BacktestOut diretamente
            backtest_out = BacktestOut(
                id=0,  # ID temporário para comparação
                user_id=current_user.id,
                strategy_id=strategy.id,
                ticker=payload.ticker,
                period=payload.period,
                start_date=result.get('start_date'),
                end_date=result.get('end_date'),
                total_return=Decimal(str(result['metrics']['total_return'])),
                annualized_return=Decimal(str(result['metrics']['annualized_return'])),
                sharpe_ratio=Decimal(str(result['metrics']['sharpe_ratio'])),
                max_drawdown=Decimal(str(result['metrics']['max_drawdown'])),
                win_rate=Decimal(str(result['metrics']['win_rate'])),
                profit_factor=Decimal(str(result['metrics']['profit_factor'])),
                total_trades=result['metrics']['total_trades'],
                winning_trades=result['metrics']['winning_trades'],
                losing_trades=result['metrics']['losing_trades'],
                avg_win=Decimal(str(result['metrics']['avg_win'])) if result['metrics']['avg_win'] else None,
                avg_loss=Decimal(str(result['metrics']['avg_loss'])) if result['metrics']['avg_loss'] else None,
                final_capital=Decimal(str(result['metrics']['final_capital'])),
                created_at=datetime.now(),
                trades=[]
            )
            backtest_results.append(backtest_out)
        except Exception as e:
            import traceback
            error_msg = f"Erro ao executar backtest para estratégia '{strategy.name}': {str(e)}"
            errors.append(error_msg)
            print(f"Erro no backtest: {error_msg}")
            print(traceback.format_exc())
            continue
    
    if not backtest_results:
        error_detail = "Nenhuma estratégia retornou resultados válidos."
        if errors:
            error_detail += f" Erros: {'; '.join(errors[:3])}"  # Limitar a 3 erros para não ficar muito longo
            if len(errors) > 3:
                error_detail += f" (e mais {len(errors) - 3} erro(s))"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )
    
    # Se algumas estratégias falharam mas outras funcionaram, ainda retornamos os resultados
    # mas podemos adicionar um aviso se necessário
    if errors and len(backtest_results) < len(strategies):
        print(f"Aviso: {len(errors)} estratégia(s) falharam, mas {len(backtest_results)} retornaram resultados")
    
    return BacktestCompareResult(
        ticker=payload.ticker,
        period=payload.period,
        strategies=backtest_results
    )


# ========== Paper Trading Routes (PRO only) ==========

@router.post("/paper-trading/start", response_model=PaperTradeOut, status_code=status.HTTP_201_CREATED)
def start_paper_trading(
    payload: PaperTradeStartRequest,
    current_user: User = Depends(get_pro_user),  # PRO only
    db: Session = Depends(get_db)
):
    """Iniciar paper trading (PRO only)."""
    # Verificar se já existe paper trading ativo para este ticker
    active_paper = db.query(PaperTrade).filter(
        PaperTrade.user_id == current_user.id,
        PaperTrade.ticker == payload.ticker,
        PaperTrade.status == PaperTradeStatus.ACTIVE
    ).first()
    
    if active_paper:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um paper trading ativo para este ticker"
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
        PaperTrade.status == PaperTradeStatus.ACTIVE
    ).first()
    
    if not paper_trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum paper trading ativo encontrado para este ticker"
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
    
    if paper_trade.status == PaperTradeStatus.ACTIVE:
        paper_trade.status = PaperTradeStatus.PAUSED
    elif paper_trade.status == PaperTradeStatus.PAUSED:
        paper_trade.status = PaperTradeStatus.ACTIVE
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível pausar/retomar um paper trading parado"
        )
    
    db.commit()
    db.refresh(paper_trade)
    
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
        PaperTrade.status == PaperTradeStatus.ACTIVE
    ).first()
    
    if not paper_trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum paper trading ativo encontrado para este ticker"
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

