"""
Router para análise de risco de portfólios.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List, Dict, Any

from app.db.database import get_db
from app.db.models import User, PortfolioItem, Portfolio
from app.core.security import get_current_user
from app.core.market_service import get_current_price
from app.db.models import UserRole
from app.schemas.risk import (
    PortfolioRiskAnalysis,
    RiskMetrics,
    PositionRiskAnalysis,
    VarResult,
    DrawdownAnalysis,
    DrawdownPoint,
    BetaAnalysis,
    PositionBeta,
    VolatilityAnalysis,
    PositionVolatility,
    DiversificationMetrics,
    TickerConcentration,
    SectorDiversification,
    StopLossTakeProfit,
    PositionCorrelation,
)
from app.core.risk import (
    calculate_var,
    calculate_drawdown,
    calculate_portfolio_beta,
    calculate_volatility,
    calculate_diversification_metrics,
    suggest_stop_loss_take_profit,
    analyze_position_risk,
)

router = APIRouter(prefix="/risk", tags=["Risk"])


def _prepare_portfolio_positions(
    items: List[PortfolioItem],
    current_user: User,
    db: Session
) -> List[Dict[str, Any]]:
    """
    Prepara lista de posições para análise de risco.
    
    Args:
        items: Lista de PortfolioItem
        current_user: Usuário atual
        db: Sessão do banco de dados
    
    Returns:
        Lista de dicionários com dados das posições
    """
    positions = []
    
    for item in items:
        # Apenas posições ativas (não vendidas)
        if item.sold_price and item.sold_date:
            continue
        
        # Buscar preço atual
        cache_threshold = 300 if current_user.role in [UserRole.PRO, UserRole.ADMIN] else 0
        current_price = get_current_price(item.ticker, db, cache_threshold_seconds=cache_threshold)
        
        if current_price is None:
            continue
        
        positions.append({
            'ticker': item.ticker,
            'quantity': item.quantity,
            'purchase_price': float(item.purchase_price),
            'current_price': float(current_price)
        })
    
    return positions


@router.get("/portfolio/{portfolio_id}", response_model=PortfolioRiskAnalysis)
def get_portfolio_risk_analysis(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtém análise completa de risco de um portfólio.
    """
    # Verificar se o portfolio existe e pertence ao usuário
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio não encontrado"
        )
    
    # Buscar posições ativas
    items = db.query(PortfolioItem).filter(
        PortfolioItem.portfolio_id == portfolio_id,
        PortfolioItem.user_id == current_user.id
    ).all()
    
    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portfolio não possui posições ativas para análise"
        )
    
    # Preparar posições para análise
    positions = _prepare_portfolio_positions(items, current_user, db)
    
    if not positions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível obter preços atuais das posições"
        )
    
    try:
        # Calcular VaR
        var_result = calculate_var(positions, confidence_level=0.95, horizon_days=1, method="historical")
        
        # Calcular drawdown
        drawdown_result = calculate_drawdown(positions, period="1y")
        
        # Calcular beta
        beta_result = calculate_portfolio_beta(positions, benchmark="^BVSP", period="1y")
        
        # Calcular volatilidade
        volatility_result = calculate_volatility(positions, period="1y", annualized=True)
        
        # Calcular diversificação
        diversification_result = calculate_diversification_metrics(positions)
        
        # Construir resposta de métricas
        metrics = RiskMetrics(
            var=VarResult(**var_result),
            drawdown=DrawdownAnalysis(
                max_drawdown=drawdown_result.get('max_drawdown'),
                current_drawdown=drawdown_result.get('current_drawdown'),
                max_drawdown_date=drawdown_result.get('max_drawdown_date'),
                recovery_days=drawdown_result.get('recovery_days'),
                drawdown_history=[
                    DrawdownPoint(**point) for point in drawdown_result.get('drawdown_history', [])
                ]
            ),
            beta=BetaAnalysis(
                portfolio_beta=beta_result.get('portfolio_beta'),
                position_betas=[
                    PositionBeta(**pb) for pb in beta_result.get('position_betas', [])
                ],
                benchmark=beta_result.get('benchmark', '^BVSP'),
                error=beta_result.get('error')
            ),
            volatility=VolatilityAnalysis(
                portfolio_volatility=volatility_result.get('portfolio_volatility'),
                position_volatilities=[
                    PositionVolatility(**pv) for pv in volatility_result.get('position_volatilities', [])
                ]
            ),
            diversification=DiversificationMetrics(
                herfindahl_index=diversification_result.get('herfindahl_index'),
                concentration_by_ticker=[
                    TickerConcentration(**tc) for tc in diversification_result.get('concentration_by_ticker', [])
                ],
                sector_diversification=[
                    SectorDiversification(**sd) for sd in diversification_result.get('sector_diversification', [])
                ],
                effective_positions=diversification_result.get('effective_positions'),
                warnings=diversification_result.get('warnings', [])
            )
        )
        
        # Análise por posição
        position_analyses = []
        for position in positions:
            try:
                pos_analysis = analyze_position_risk(position, positions, benchmark="^BVSP")
                position_analyses.append(PositionRiskAnalysis(
                    ticker=pos_analysis.get('ticker'),
                    var=pos_analysis.get('var'),
                    var_percentage=pos_analysis.get('var_percentage'),
                    beta=pos_analysis.get('beta'),
                    volatility=pos_analysis.get('volatility'),
                    portfolio_weight=pos_analysis.get('portfolio_weight', 0.0),
                    correlations=[
                        PositionCorrelation(**corr) for corr in pos_analysis.get('correlations', [])
                    ],
                    stop_loss=pos_analysis.get('stop_loss'),
                    take_profit=pos_analysis.get('take_profit'),
                    stop_loss_percentage=pos_analysis.get('stop_loss_percentage'),
                    take_profit_percentage=pos_analysis.get('take_profit_percentage'),
                    error=pos_analysis.get('error')
                ))
            except Exception as e:
                # Se falhar análise de uma posição, adicionar com erro
                position_analyses.append(PositionRiskAnalysis(
                    ticker=position.get('ticker', 'UNKNOWN'),
                    portfolio_weight=0.0,
                    error=f"Erro ao analisar posição: {str(e)}"
                ))
        
        return PortfolioRiskAnalysis(
            portfolio_id=portfolio_id,
            metrics=metrics,
            position_analyses=position_analyses
        )
    
    except Exception as e:
        import traceback
        print(f"Erro ao calcular análise de risco: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao calcular análise de risco: {str(e)}"
        )


@router.get("/position/{item_id}", response_model=PositionRiskAnalysis)
def get_position_risk_analysis(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtém análise de risco de uma posição específica.
    """
    # Buscar posição
    item = db.query(PortfolioItem).filter(
        PortfolioItem.id == item_id,
        PortfolioItem.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Posição não encontrada"
        )
    
    # Verificar se está vendida
    if item.sold_price and item.sold_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Posição já foi vendida"
        )
    
    # Buscar preço atual
    cache_threshold = 300 if current_user.role in [UserRole.PRO, UserRole.ADMIN] else 0
    current_price = get_current_price(item.ticker, db, cache_threshold_seconds=cache_threshold)
    
    if current_price is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Não foi possível obter preço atual da posição"
        )
    
    # Preparar posição
    position = {
        'ticker': item.ticker,
        'quantity': item.quantity,
        'purchase_price': float(item.purchase_price),
        'current_price': float(current_price)
    }
    
    # Buscar todas as posições do portfólio para análise de correlação
    portfolio_items = db.query(PortfolioItem).filter(
        PortfolioItem.portfolio_id == item.portfolio_id,
        PortfolioItem.user_id == current_user.id
    ).all()
    
    portfolio_positions = _prepare_portfolio_positions(portfolio_items, current_user, db)
    
    try:
        # Analisar risco da posição
        analysis = analyze_position_risk(position, portfolio_positions, benchmark="^BVSP")
        
        return PositionRiskAnalysis(
            ticker=analysis.get('ticker'),
            var=analysis.get('var'),
            var_percentage=analysis.get('var_percentage'),
            beta=analysis.get('beta'),
            volatility=analysis.get('volatility'),
            portfolio_weight=analysis.get('portfolio_weight', 0.0),
            correlations=[
                PositionCorrelation(**corr) for corr in analysis.get('correlations', [])
            ],
            stop_loss=analysis.get('stop_loss'),
            take_profit=analysis.get('take_profit'),
            stop_loss_percentage=analysis.get('stop_loss_percentage'),
            take_profit_percentage=analysis.get('take_profit_percentage'),
            error=analysis.get('error')
        )
    
    except Exception as e:
        import traceback
        print(f"Erro ao calcular análise de risco da posição: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao calcular análise de risco: {str(e)}"
        )



