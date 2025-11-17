"""
Router para o Scanner de Oportunidades (Feature PRO).
Endpoint que retorna dados pré-calculados do scanner assíncrono.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.security import get_pro_user
from app.db.models import User, ScannerData, DailyScanResult
from app.db.database import get_db
from app.core.market.data_fetcher import get_company_fundamentals
from sqlalchemy.orm import Session
from typing import Optional, Literal, List

router = APIRouter(prefix="/scanner", tags=["Scanner"])


@router.get("/")
def get_scanner_results(
    rsi_lt: Optional[float] = Query(default=None, description="RSI menor que"),
    rsi_gt: Optional[float] = Query(default=None, description="RSI maior que"),
    macd_gt: Optional[float] = Query(default=None, description="MACD histogram maior que"),
    macd_lt: Optional[float] = Query(default=None, description="MACD histogram menor que"),
    macd_signal_lt: Optional[float] = Query(default=None, description="MACD signal menor que"),
    macd_signal_gt: Optional[float] = Query(default=None, description="MACD signal maior que"),
    quality_gt: Optional[float] = Query(default=None, description="Quality score maior que"),
    quality_lt: Optional[float] = Query(default=None, description="Quality score menor que"),
    mm_cross: Optional[Literal['BULLISH', 'BEARISH', 'NEUTRAL']] = Query(
        default=None, 
        description="Cruzamento de médias móveis (MM9 x MM21)"
    ),
    sort: Optional[Literal['rsi_asc', 'rsi_desc', 'macd_desc', 'quality_desc']] = Query(
        default=None,
        description="Ordenação dos resultados"
    ),
    limit: int = Query(default=100, ge=1, le=500, description="Limite de resultados"),
    current_user: User = Depends(get_pro_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint PRO: retorna dados filtrados do scanner pré-calculado.
    
    Usa DailyScanResult como base (dados mais atuais) e combina com ScannerData
    para incluir informações adicionais como mm_9_cruza_mm_21.
    Os dados são pré-calculados pela task Celery que roda diariamente.
    
    Filtros disponíveis:
    - rsi_lt: RSI menor que valor especificado
    - rsi_gt: RSI maior que valor especificado
    - macd_gt: MACD histogram maior que valor especificado
    - macd_lt: MACD histogram menor que valor especificado
    - macd_signal_lt: MACD signal menor que valor especificado
    - macd_signal_gt: MACD signal maior que valor especificado
    - quality_gt: Quality score maior que valor especificado (0-100)
    - quality_lt: Quality score menor que valor especificado (0-100)
    - mm_cross: Tipo de cruzamento de médias móveis (BULLISH, BEARISH, NEUTRAL)
    - sort: Ordenação (rsi_asc, rsi_desc, macd_desc, quality_desc)
    - limit: Limite de resultados (1-500)
    """
    try:
        # Query base usando DailyScanResult (dados mais atuais)
        query = db.query(DailyScanResult)
        
        # Aplicar filtros de RSI
        if rsi_lt is not None:
            query = query.filter(
                DailyScanResult.rsi_14.isnot(None),
                DailyScanResult.rsi_14 < rsi_lt
            )
        
        if rsi_gt is not None:
            query = query.filter(
                DailyScanResult.rsi_14.isnot(None),
                DailyScanResult.rsi_14 > rsi_gt
            )
        
        # Aplicar filtros de MACD histogram
        if macd_gt is not None:
            query = query.filter(
                DailyScanResult.macd_h.isnot(None),
                DailyScanResult.macd_h > macd_gt
            )
        
        if macd_lt is not None:
            query = query.filter(
                DailyScanResult.macd_h.isnot(None),
                DailyScanResult.macd_h < macd_lt
            )
        
        # Aplicar ordenação (exceto quality_desc que será feito após buscar quality_scores)
        sort_by_quality = sort == 'quality_desc'
        if sort == 'rsi_asc':
            query = query.order_by(DailyScanResult.rsi_14.asc().nulls_last())
        elif sort == 'rsi_desc':
            query = query.order_by(DailyScanResult.rsi_14.desc().nulls_last())
        elif sort == 'macd_desc':
            query = query.order_by(DailyScanResult.macd_h.desc().nulls_last())
        elif not sort_by_quality:
            # Ordenação padrão: por ticker (se não for ordenar por quality)
            query = query.order_by(DailyScanResult.ticker.asc())
        
        # Aplicar limite e executar query
        # Se ordenar por quality, buscar mais resultados para depois ordenar
        query_limit = limit * 2 if sort_by_quality else limit
        results: List[DailyScanResult] = query.limit(query_limit).all()
        
        # Buscar tickers para filtros adicionais (mm_cross, macd_signal)
        tickers = [r.ticker for r in results]
        
        # Se há filtros que dependem de ScannerData, aplicar após buscar
        scanner_data_map = {}
        if mm_cross is not None or macd_signal_lt is not None or macd_signal_gt is not None:
            scanner_query = db.query(ScannerData).filter(ScannerData.ticker.in_(tickers))
            
            if mm_cross is not None:
                scanner_query = scanner_query.filter(ScannerData.mm_9_cruza_mm_21 == mm_cross)
            
            if macd_signal_lt is not None:
                scanner_query = scanner_query.filter(
                    ScannerData.macd_signal.isnot(None),
                    ScannerData.macd_signal < macd_signal_lt
                )
            
            if macd_signal_gt is not None:
                scanner_query = scanner_query.filter(
                    ScannerData.macd_signal.isnot(None),
                    ScannerData.macd_signal > macd_signal_gt
                )
            
            scanner_results = scanner_query.all()
            scanner_data_map = {sd.ticker: sd for sd in scanner_results}
            
            # Filtrar resultados baseado nos filtros de ScannerData
            if mm_cross is not None or macd_signal_lt is not None or macd_signal_gt is not None:
                results = [r for r in results if r.ticker in scanner_data_map]
        
        # Buscar todos os ScannerData de uma vez para otimização
        if not scanner_data_map and results:
            all_tickers = [r.ticker for r in results]
            scanner_results = db.query(ScannerData).filter(ScannerData.ticker.in_(all_tickers)).all()
            scanner_data_map = {sd.ticker: sd for sd in scanner_results}
        
        # Formatar resposta e buscar quality_score em tempo real
        formatted_results = []
        for r in results:
            # Buscar dados adicionais de ScannerData se disponível
            scanner_data = scanner_data_map.get(r.ticker)
            
            # Buscar quality_score
            quality_score = None
            try:
                fundamentals = get_company_fundamentals(r.ticker)
                quality_score = fundamentals.get('quality_score')
            except Exception:
                # Se falhar ao buscar, continua sem o score
                pass
            
            # Aplicar filtros de quality_score
            if quality_gt is not None and (quality_score is None or quality_score <= quality_gt):
                continue
            if quality_lt is not None and (quality_score is None or quality_score >= quality_lt):
                continue
            
            formatted_results.append({
                "ticker": r.ticker,
                "last_price": float(r.last_price) if r.last_price is not None else None,
                "rsi_14": float(r.rsi_14) if r.rsi_14 is not None else None,
                "macd_h": float(r.macd_h) if r.macd_h is not None else None,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "mm_9_cruza_mm_21": scanner_data.mm_9_cruza_mm_21 if scanner_data else None,
                "quality_score": quality_score,
            })
        
        # Ordenar por quality_score se solicitado
        if sort_by_quality:
            formatted_results.sort(
                key=lambda x: (x['quality_score'] is not None, x['quality_score'] or 0),
                reverse=True
            )
            # Aplicar limite após ordenação
            formatted_results = formatted_results[:limit]
        
        return formatted_results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no servidor ao consultar scanner: {e}"
        )

