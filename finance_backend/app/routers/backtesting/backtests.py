"""
Router para execução e resultados de backtests.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from decimal import Decimal
from typing import List
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import User, Strategy, StrategyCondition, Backtest, BacktestTrade, UserRole
from app.schemas.backtesting import (
    BacktestRunRequest, BacktestOut, BacktestResultDetail,
    BacktestCompareRequest, BacktestCompareResult
)
from app.core.security import get_current_user, get_pro_user
from app.core.backtesting.engine import BacktestEngine

router = APIRouter()


def check_backtest_limit(user: User, db: Session) -> None:
    """Valida se o usuário pode executar mais backtests simultâneos."""
    if user.role == UserRole.ADMIN:
        return
    
    # Contar backtests criados nas últimas 5 minutos (simulação de "simultâneos")
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

