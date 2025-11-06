from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.stock import (
    TickerRequest, TickerHistoricalDataOut, TechnicalAnalysisOut, FundamentalsOut
)
from app.core.market_service import (
    get_historical_data, get_technical_analysis, get_company_fundamentals
)
from app.core.security import get_current_user
from app.db.models import User

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

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no servidor ao buscar fundamentos: {e}"
        )