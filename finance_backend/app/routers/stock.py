from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.schemas.stock import (
    TickerRequest, TickerHistoricalDataOut, TechnicalAnalysisOut, FundamentalsOut
)
from app.core.market_service import (
    get_historical_data, get_technical_analysis, get_company_fundamentals
)
from app.core.security import get_current_user, get_pro_user
from app.db.models import User, DailyScanResult
from app.db.database import get_db
from sqlalchemy.orm import Session
from typing import Optional, Literal, List

router = APIRouter(prefix="/stocks", tags=["Stocks Analysis"])


@router.post("/historical-data", response_model=TickerHistoricalDataOut)
def fetch_historical_data(
    payload: TickerRequest,
    current_user: User = Depends(get_current_user) 
):
    """
    Busca dados históricos de um ativo na bolsa.
    """
    try:
        historical_data = get_historical_data(payload.ticker, payload.period)
        
        if not historical_data:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum dado encontrado para o ticker: {payload.ticker}"
            )

        return TickerHistoricalDataOut(
            ticker=payload.ticker,
            period=payload.period,
            data=historical_data
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no servidor ao buscar dados: {e}"
        )


@router.post("/analysis", response_model=TechnicalAnalysisOut)
def fetch_technical_analysis(
    payload: TickerRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Busca dados históricos de um ativo com indicadores técnicos calculados:
    MACD, Stochastic, ATR, Bollinger Bands, OBV, RSI.
    """
    try:
        technical_data = get_technical_analysis(payload.ticker, payload.period)
        
        if not technical_data:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum dado encontrado para o ticker: {payload.ticker}"
            )
        
        # Mapear colunas do pandas-ta para o schema
        formatted_data = []
        for row in technical_data:
            formatted_row = {
                'date': row['date'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'],
                'macd': row.get('MACD_12_26_9'),
                'macd_signal': row.get('MACDs_12_26_9'),
                'macd_histogram': row.get('MACDh_12_26_9'),
                'stochastic_k': row.get('STOCHk_14_3_3'),
                'stochastic_d': row.get('STOCHd_14_3_3'),
                'atr': row.get('ATRr_14'),
                'bb_lower': row.get('BBL_20_2.0'),
                'bb_middle': row.get('BBM_20_2.0'),
                'bb_upper': row.get('BBU_20_2.0'),
                'obv': row.get('OBV'),
                'rsi': row.get('RSI_14')
            }
            formatted_data.append(formatted_row)

        return TechnicalAnalysisOut(
            ticker=payload.ticker,
            period=payload.period,
            data=formatted_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no servidor ao buscar análise técnica: {e}"
        )


@router.get("/fundamentals/{ticker}", response_model=FundamentalsOut)
def fetch_fundamentals(
    ticker: str,
    current_user: User = Depends(get_current_user)
):
    """
    Busca dados fundamentalistas de uma empresa:
    P/E, P/VP, Dividend Yield, Beta, Setor, Indústria, Market Cap.
    """
    try:
        fundamentals = get_company_fundamentals(ticker)
        
        return FundamentalsOut(
            ticker=ticker,
            **fundamentals
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no servidor ao buscar fundamentos: {e}"
        )


@router.get("/scanner")
def get_scanner_results(
    rsi_lt: Optional[float] = Query(default=None),
    rsi_gt: Optional[float] = Query(default=None),
    macd_gt: Optional[float] = Query(default=None),
    macd_lt: Optional[float] = Query(default=None),
    bb_touch: Optional[Literal['upper', 'lower', 'any']] = Query(default=None),
    sort: Optional[Literal['rsi_asc', 'rsi_desc', 'macd_desc']] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_pro_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint PRO: retorna snapshot filtrado do scanner diário.
    Não faz chamadas externas; apenas SELECT em daily_scan_results.
    """
    try:
        query = db.query(DailyScanResult)

        if rsi_lt is not None:
            query = query.filter(DailyScanResult.rsi_14 != None, DailyScanResult.rsi_14 < rsi_lt)  # noqa: E711
        if rsi_gt is not None:
            query = query.filter(DailyScanResult.rsi_14 != None, DailyScanResult.rsi_14 > rsi_gt)  # noqa: E711
        if macd_gt is not None:
            query = query.filter(DailyScanResult.macd_h != None, DailyScanResult.macd_h > macd_gt)  # noqa: E711
        if macd_lt is not None:
            query = query.filter(DailyScanResult.macd_h != None, DailyScanResult.macd_h < macd_lt)  # noqa: E711

        if bb_touch is not None:
            if bb_touch == 'upper':
                query = query.filter(
                    DailyScanResult.bb_upper != None,  # noqa: E711
                    DailyScanResult.last_price >= DailyScanResult.bb_upper
                )
            elif bb_touch == 'lower':
                query = query.filter(
                    DailyScanResult.bb_lower != None,  # noqa: E711
                    DailyScanResult.last_price <= DailyScanResult.bb_lower
                )
            elif bb_touch == 'any':
                query = query.filter(
                    (
                        (DailyScanResult.bb_upper != None) & (DailyScanResult.last_price >= DailyScanResult.bb_upper)
                    ) | (
                        (DailyScanResult.bb_lower != None) & (DailyScanResult.last_price <= DailyScanResult.bb_lower)
                    )
                )

        if sort == 'rsi_asc':
            query = query.order_by(DailyScanResult.rsi_14.asc().nulls_last())
        elif sort == 'rsi_desc':
            query = query.order_by(DailyScanResult.rsi_14.desc().nulls_last())
        elif sort == 'macd_desc':
            query = query.order_by(DailyScanResult.macd_h.desc().nulls_last())

        results: List[DailyScanResult] = query.limit(limit).all()

        return [
            {
                "ticker": r.ticker,
                "last_price": float(r.last_price) if r.last_price is not None else None,
                "rsi_14": float(r.rsi_14) if r.rsi_14 is not None else None,
                "macd_h": float(r.macd_h) if r.macd_h is not None else None,
                "bb_upper": float(r.bb_upper) if r.bb_upper is not None else None,
                "bb_lower": float(r.bb_lower) if r.bb_lower is not None else None,
                "timestamp": r.timestamp,
            }
            for r in results
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no servidor ao consultar scanner: {e}"
        )