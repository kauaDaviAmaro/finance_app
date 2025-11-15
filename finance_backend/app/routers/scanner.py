"""
Router para o Scanner de Oportunidades (Feature PRO).
Endpoint que retorna dados pré-calculados do scanner assíncrono.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.security import get_pro_user
from app.db.models import User, ScannerData
from app.db.database import get_db
from sqlalchemy.orm import Session
from typing import Optional, Literal, List

router = APIRouter(prefix="/scanner", tags=["Scanner"])


@router.get("/")
def get_scanner_results(
    rsi_lt: Optional[float] = Query(default=None, description="RSI menor que"),
    rsi_gt: Optional[float] = Query(default=None, description="RSI maior que"),
    macd_signal_lt: Optional[float] = Query(default=None, description="MACD signal menor que"),
    macd_signal_gt: Optional[float] = Query(default=None, description="MACD signal maior que"),
    mm_cross: Optional[Literal['BULLISH', 'BEARISH', 'NEUTRAL']] = Query(
        default=None, 
        description="Cruzamento de médias móveis (MM9 x MM21)"
    ),
    sort: Optional[Literal['rsi_asc', 'rsi_desc', 'macd_desc']] = Query(
        default=None,
        description="Ordenação dos resultados"
    ),
    limit: int = Query(default=100, ge=1, le=500, description="Limite de resultados"),
    current_user: User = Depends(get_pro_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint PRO: retorna dados filtrados do scanner pré-calculado.
    
    Não faz cálculos em tempo real - apenas consulta rápida na tabela scanner_data.
    Os dados são pré-calculados pela task Celery que roda toda madrugada às 3:00 AM.
    
    Filtros disponíveis:
    - rsi_lt: RSI menor que valor especificado
    - rsi_gt: RSI maior que valor especificado
    - macd_signal_lt: MACD signal menor que valor especificado
    - macd_signal_gt: MACD signal maior que valor especificado
    - mm_cross: Tipo de cruzamento de médias móveis (BULLISH, BEARISH, NEUTRAL)
    - sort: Ordenação (rsi_asc, rsi_desc, macd_desc)
    - limit: Limite de resultados (1-500)
    """
    try:
        # Query base
        query = db.query(ScannerData)
        
        # Aplicar filtros
        if rsi_lt is not None:
            query = query.filter(
                ScannerData.rsi_14.isnot(None),
                ScannerData.rsi_14 < rsi_lt
            )
        
        if rsi_gt is not None:
            query = query.filter(
                ScannerData.rsi_14.isnot(None),
                ScannerData.rsi_14 > rsi_gt
            )
        
        if macd_signal_lt is not None:
            query = query.filter(
                ScannerData.macd_signal.isnot(None),
                ScannerData.macd_signal < macd_signal_lt
            )
        
        if macd_signal_gt is not None:
            query = query.filter(
                ScannerData.macd_signal.isnot(None),
                ScannerData.macd_signal > macd_signal_gt
            )
        
        if mm_cross is not None:
            query = query.filter(ScannerData.mm_9_cruza_mm_21 == mm_cross)
        
        # Aplicar ordenação
        if sort == 'rsi_asc':
            query = query.order_by(ScannerData.rsi_14.asc().nulls_last())
        elif sort == 'rsi_desc':
            query = query.order_by(ScannerData.rsi_14.desc().nulls_last())
        elif sort == 'macd_desc':
            query = query.order_by(ScannerData.macd_signal.desc().nulls_last())
        else:
            # Ordenação padrão: por ticker
            query = query.order_by(ScannerData.ticker.asc())
        
        # Aplicar limite e executar query
        results: List[ScannerData] = query.limit(limit).all()
        
        # Formatar resposta
        return [
            {
                "ticker": r.ticker,
                "rsi_14": float(r.rsi_14) if r.rsi_14 is not None else None,
                "macd_signal": float(r.macd_signal) if r.macd_signal is not None else None,
                "mm_9_cruza_mm_21": r.mm_9_cruza_mm_21,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
            }
            for r in results
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no servidor ao consultar scanner: {e}"
        )

