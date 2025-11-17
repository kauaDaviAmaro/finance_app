from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.schemas.stock import (
    TickerRequest, TickerHistoricalDataOut, TechnicalAnalysisOut, FundamentalsOut,
    TickerComparisonRequest, TickerComparisonOut,
    FinancialStatementsOut, IncomeStatementOut, BalanceSheetOut, CashFlowOut,
    FinancialStatementRow, AdvancedAnalysisOut, ElliottAnnotationIn, ElliottAnnotationOut,
    SupportResistanceLevel, ChartPattern, CandlestickPattern, ElliottWaves, ElliottWavePoint
)
from app.core.market_service import (
    get_historical_data, get_technical_analysis, get_company_fundamentals,
    get_income_statement, get_balance_sheet, get_cashflow
)
from app.core.market.pattern_analysis import get_advanced_analysis
from app.core.security import get_current_user, get_pro_user
from app.db.models import User, DailyScanResult, TickerSearch, ElliottAnnotation
from app.db.database import get_db
from app.core.market.ticker_utils import format_ticker
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, Literal, List
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/stocks", tags=["Stocks Analysis"])


def log_ticker_search(ticker: str, user_id: Optional[int], db: Session):
    """Registra uma pesquisa de ticker no banco de dados."""
    try:
        formatted_ticker = format_ticker(ticker)
        search = TickerSearch(
            ticker=formatted_ticker,
            user_id=user_id
        )
        db.add(search)
        db.commit()
    except Exception:
        # Não queremos que erros no log quebrem a requisição
        db.rollback()
        pass


@router.post("/historical-data", response_model=TickerHistoricalDataOut)
def fetch_historical_data(
    payload: TickerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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

        # Registrar pesquisa
        log_ticker_search(payload.ticker, current_user.id, db)

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
        
        # Registrar pesquisa
        log_ticker_search(payload.ticker, current_user.id, db)
        
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Busca dados fundamentalistas de uma empresa:
    P/E, P/VP, Dividend Yield, Beta, Setor, Indústria, Market Cap.
    """
    try:
        fundamentals = get_company_fundamentals(ticker)
        
        # Registrar pesquisa
        log_ticker_search(ticker, current_user.id, db)
        
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


@router.get("/financial-statements/{ticker}", response_model=FinancialStatementsOut)
def fetch_financial_statements(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Busca as demonstrações financeiras de uma empresa:
    DRE (Income Statement), Balanço Patrimonial (Balance Sheet) e Fluxo de Caixa (Cash Flow).
    """
    try:
        # Buscar as três demonstrações
        income_statement_data = get_income_statement(ticker)
        balance_sheet_data = get_balance_sheet(ticker)
        cashflow_data = get_cashflow(ticker)
        
        # Registrar pesquisa
        log_ticker_search(ticker, current_user.id, db)
        
        # Construir objetos de resposta
        income_statement = IncomeStatementOut(
            ticker=ticker,
            periods=income_statement_data.get('periods', []),
            data=[FinancialStatementRow(**row) for row in income_statement_data.get('data', [])]
        )
        
        balance_sheet = BalanceSheetOut(
            ticker=ticker,
            periods=balance_sheet_data.get('periods', []),
            data=[FinancialStatementRow(**row) for row in balance_sheet_data.get('data', [])]
        )
        
        cash_flow = CashFlowOut(
            ticker=ticker,
            periods=cashflow_data.get('periods', []),
            data=[FinancialStatementRow(**row) for row in cashflow_data.get('data', [])]
        )
        
        return FinancialStatementsOut(
            ticker=ticker,
            income_statement=income_statement,
            balance_sheet=balance_sheet,
            cash_flow=cash_flow
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no servidor ao buscar demonstrações financeiras: {e}"
        )


@router.get("/most-searched")
def get_most_searched_tickers(
    limit: int = Query(default=10, ge=1, le=50),
    days: int = Query(default=7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna os tickers mais pesquisados nos últimos N dias.
    """
    try:
        # Calcular data de corte
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Buscar tickers mais pesquisados
        results = db.query(
            TickerSearch.ticker,
            func.count(TickerSearch.id).label('search_count')
        ).filter(
            TickerSearch.created_at >= cutoff_date
        ).group_by(
            TickerSearch.ticker
        ).order_by(
            desc(func.count(TickerSearch.id))
        ).limit(limit).all()
        
        return [
            {
                "ticker": ticker,
                "search_count": count
            }
            for ticker, count in results
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no servidor ao buscar tickers mais pesquisados: {e}"
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
        else:
            # Ordenação padrão: por ticker
            query = query.order_by(DailyScanResult.ticker.asc())

        results: List[DailyScanResult] = query.limit(limit).all()

        return [
            {
                "ticker": r.ticker,
                "last_price": float(r.last_price) if r.last_price is not None else None,
                "rsi_14": float(r.rsi_14) if r.rsi_14 is not None else None,
                "macd_h": float(r.macd_h) if r.macd_h is not None else None,
                "bb_upper": float(r.bb_upper) if r.bb_upper is not None else None,
                "bb_lower": float(r.bb_lower) if r.bb_lower is not None else None,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
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


@router.post("/compare", response_model=TickerComparisonOut)
def compare_tickers(
    payload: TickerComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compara dois tickers retornando análise técnica e fundamentos de ambos.
    """
    try:
        # Buscar análise técnica para ambos os tickers
        ticker1_technical = get_technical_analysis(payload.ticker1, payload.period)
        ticker2_technical = get_technical_analysis(payload.ticker2, payload.period)
        
        if not ticker1_technical:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum dado encontrado para o ticker: {payload.ticker1}"
            )
        
        if not ticker2_technical:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum dado encontrado para o ticker: {payload.ticker2}"
            )
        
        # Buscar fundamentos para ambos os tickers
        ticker1_fundamentals = get_company_fundamentals(payload.ticker1)
        ticker2_fundamentals = get_company_fundamentals(payload.ticker2)
        
        # Registrar pesquisas
        log_ticker_search(payload.ticker1, current_user.id, db)
        log_ticker_search(payload.ticker2, current_user.id, db)
        
        # Formatar dados técnicos do ticker1
        ticker1_formatted_data = []
        for row in ticker1_technical:
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
            ticker1_formatted_data.append(formatted_row)
        
        # Formatar dados técnicos do ticker2
        ticker2_formatted_data = []
        for row in ticker2_technical:
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
            ticker2_formatted_data.append(formatted_row)
        
        return TickerComparisonOut(
            ticker1=payload.ticker1,
            ticker2=payload.ticker2,
            period=payload.period,
            ticker1_data=TechnicalAnalysisOut(
                ticker=payload.ticker1,
                period=payload.period,
                data=ticker1_formatted_data
            ),
            ticker2_data=TechnicalAnalysisOut(
                ticker=payload.ticker2,
                period=payload.period,
                data=ticker2_formatted_data
            ),
            ticker1_fundamentals=FundamentalsOut(
                ticker=payload.ticker1,
                **ticker1_fundamentals
            ),
            ticker2_fundamentals=FundamentalsOut(
                ticker=payload.ticker2,
                **ticker2_fundamentals
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no servidor ao comparar tickers: {e}"
        )


@router.post("/advanced-analysis", response_model=AdvancedAnalysisOut)
def fetch_advanced_analysis(
    payload: TickerRequest,
    current_user: User = Depends(get_pro_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint PRO: Busca análise técnica avançada incluindo padrões gráficos,
    suporte/resistência, padrões de candlestick, retrações de Fibonacci e ondas de Elliott.
    """
    try:
        analysis = get_advanced_analysis(payload.ticker, payload.period)
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum dado encontrado para o ticker: {payload.ticker}"
            )
        
        # Registrar pesquisa
        log_ticker_search(payload.ticker, current_user.id, db)
        
        # Converter para schemas Pydantic
        support_levels = [
            SupportResistanceLevel(**level) for level in analysis['support_levels']
        ]
        resistance_levels = [
            SupportResistanceLevel(**level) for level in analysis['resistance_levels']
        ]
        patterns = [
            ChartPattern(**pattern) for pattern in analysis['patterns']
        ]
        candlestick_patterns = [
            CandlestickPattern(**pattern) for pattern in analysis['candlestick_patterns']
        ]
        
        # Converter ondas de Elliott
        elliott_waves_data = analysis['elliott_waves']
        elliott_waves = ElliottWaves(
            pattern_type=elliott_waves_data.get('pattern_type'),
            waves=[
                ElliottWavePoint(**wave) for wave in elliott_waves_data.get('waves', [])
            ],
            confidence=elliott_waves_data.get('confidence', 0.0),
            wave_labels=elliott_waves_data.get('wave_labels')
        )
        
        return AdvancedAnalysisOut(
            ticker=analysis['ticker'],
            period=analysis['period'],
            patterns=patterns,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            candlestick_patterns=candlestick_patterns,
            fibonacci_levels=analysis['fibonacci_levels'],
            elliott_waves=elliott_waves
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no servidor ao buscar análise avançada: {e}"
        )


@router.post("/elliott-annotations", response_model=ElliottAnnotationOut)
def save_elliott_annotations(
    payload: ElliottAnnotationIn,
    current_user: User = Depends(get_pro_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint PRO: Salva anotações manuais de ondas de Elliott.
    """
    try:
        formatted_ticker = format_ticker(payload.ticker)
        
        # Verificar se já existe anotação para este ticker/periodo
        existing = db.query(ElliottAnnotation).filter(
            ElliottAnnotation.user_id == current_user.id,
            ElliottAnnotation.ticker == formatted_ticker,
            ElliottAnnotation.period == payload.period
        ).first()
        
        annotations_data = [ann.dict() for ann in payload.annotations]
        
        if existing:
            # Atualizar existente
            existing.annotations = annotations_data
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
        else:
            # Criar novo
            annotation = ElliottAnnotation(
                user_id=current_user.id,
                ticker=formatted_ticker,
                period=payload.period,
                annotations=annotations_data
            )
            db.add(annotation)
            db.commit()
            db.refresh(annotation)
            existing = annotation
        
        return ElliottAnnotationOut(
            id=existing.id,
            ticker=existing.ticker,
            period=existing.period,
            annotations=payload.annotations,
            created_at=existing.created_at.isoformat() if existing.created_at else None,
            updated_at=existing.updated_at.isoformat() if existing.updated_at else None
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao salvar anotações: {e}"
        )


@router.get("/elliott-annotations/{ticker}", response_model=Optional[ElliottAnnotationOut])
def get_elliott_annotations(
    ticker: str,
    period: str = Query(default="1y", description="Período dos dados"),
    current_user: User = Depends(get_pro_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint PRO: Busca anotações manuais de ondas de Elliott salvas.
    """
    try:
        formatted_ticker = format_ticker(ticker)
        
        annotation = db.query(ElliottAnnotation).filter(
            ElliottAnnotation.user_id == current_user.id,
            ElliottAnnotation.ticker == formatted_ticker,
            ElliottAnnotation.period == period
        ).first()
        
        if not annotation:
            return None
        
        # Converter annotations de dict para WavePoint
        from app.schemas.stock import WavePoint
        wave_points = [WavePoint(**ann) for ann in annotation.annotations]
        
        return ElliottAnnotationOut(
            id=annotation.id,
            ticker=annotation.ticker,
            period=annotation.period,
            annotations=wave_points,
            created_at=annotation.created_at.isoformat() if annotation.created_at else None,
            updated_at=annotation.updated_at.isoformat() if annotation.updated_at else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar anotações: {e}"
        )


@router.delete("/elliott-annotations/{ticker}")
def delete_elliott_annotations(
    ticker: str,
    period: str = Query(default="1y", description="Período dos dados"),
    current_user: User = Depends(get_pro_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint PRO: Deleta anotações manuais de ondas de Elliott.
    """
    try:
        formatted_ticker = format_ticker(ticker)
        
        annotation = db.query(ElliottAnnotation).filter(
            ElliottAnnotation.user_id == current_user.id,
            ElliottAnnotation.ticker == formatted_ticker,
            ElliottAnnotation.period == period
        ).first()
        
        if not annotation:
            raise HTTPException(
                status_code=404,
                detail="Anotações não encontradas"
            )
        
        db.delete(annotation)
        db.commit()
        
        return {"message": "Anotações deletadas com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao deletar anotações: {e}"
        )