"""
Módulo para gerenciamento de cache de preços de tickers.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import Optional, Dict, List
from decimal import Decimal

from app.core.market.ticker_utils import format_ticker


def get_current_price(ticker: str, db: Session = None) -> Optional[float]:
    """
    Busca o preço atual de um ticker.
    Primeiro consulta o cache do banco de dados (TickerPrice).
    Se não encontrar ou o cache estiver desatualizado (>15 min), busca na yfinance.
    Retorna None se não conseguir buscar.
    """
    from app.db.models import TickerPrice
    
    formatted_ticker = format_ticker(ticker)
    
    # Se temos acesso ao DB, consultar o cache primeiro
    if db:
        try:
            cached_price = db.query(TickerPrice).filter(
                TickerPrice.ticker == formatted_ticker
            ).first()
            
            if cached_price:
                # Verificar se o cache está recente (menos de 15 minutos)
                now = datetime.now(cached_price.timestamp.tzinfo) if cached_price.timestamp.tzinfo else datetime.now()
                cache_age = now - cached_price.timestamp
                if cache_age.total_seconds() < 900:  # 15 minutos
                    return float(cached_price.last_price)
        except Exception as e:
            print(f"Erro ao consultar cache de preço para {formatted_ticker}: {e}")
    
    # Cache não encontrado ou desatualizado - buscar na yfinance
    try:
        stock = yf.Ticker(formatted_ticker)
        data = stock.history(period="1d")
        
        if data.empty:
            return None
        
        current_price = float(data['Close'].iloc[-1])
        
        # Se temos DB, atualizar o cache
        if db and current_price:
            try:
                ticker_price = db.query(TickerPrice).filter(
                    TickerPrice.ticker == formatted_ticker
                ).first()
                
                if ticker_price:
                    # Atualizar preço existente
                    ticker_price.last_price = Decimal(str(current_price))
                    ticker_price.timestamp = func.now()
                else:
                    # Criar novo registro
                    ticker_price = TickerPrice(
                        ticker=formatted_ticker,
                        last_price=Decimal(str(current_price))
                    )
                    db.add(ticker_price)
                
                db.commit()
            except Exception as e:
                print(f"Erro ao atualizar cache de preço para {formatted_ticker}: {e}")
                db.rollback()
        
        return current_price
        
    except Exception as e:
        print(f"Erro ao buscar preço atual do ticker {formatted_ticker}: {e}")
        return None


def update_ticker_prices(tickers: List[str], db: Session) -> Dict[str, Optional[float]]:
    """
    Atualiza os preços de múltiplos tickers no cache.
    Esta função será chamada pelo worker assíncrono (Cron/Celery) a cada 5-15 minutos.
    Retorna um dicionário com ticker -> preço atualizado.
    """
    from app.db.models import TickerPrice
    
    results = {}
    
    for ticker in tickers:
        formatted_ticker = format_ticker(ticker)
        
        try:
            stock = yf.Ticker(formatted_ticker)
            data = stock.history(period="1d")
            
            if data.empty:
                results[ticker] = None
                continue
            
            current_price = float(data['Close'].iloc[-1])
            results[ticker] = current_price
            
            # Atualizar ou criar no cache
            ticker_price = db.query(TickerPrice).filter(
                TickerPrice.ticker == formatted_ticker
            ).first()
            
            if ticker_price:
                ticker_price.last_price = Decimal(str(current_price))
                ticker_price.timestamp = func.now()
            else:
                ticker_price = TickerPrice(
                    ticker=formatted_ticker,
                    last_price=Decimal(str(current_price))
                )
                db.add(ticker_price)
            
        except Exception as e:
            print(f"Erro ao atualizar preço para {ticker}: {e}")
            results[ticker] = None
    
    try:
        db.commit()
    except Exception as e:
        print(f"Erro ao commitar atualizações de preços: {e}")
        db.rollback()
    
    return results


def get_all_tracked_tickers(db: Session) -> List[str]:
    """
    Retorna lista de todos os tickers únicos que estão sendo rastreados
    (presentes em WatchlistItem ou PortfolioItem).
    Será usado pelo worker para saber quais tickers atualizar.
    """
    from app.db.models import WatchlistItem, PortfolioItem
    
    watchlist_tickers = db.query(WatchlistItem.ticker).distinct().all()
    portfolio_tickers = db.query(PortfolioItem.ticker).distinct().all()
    
    # Combinar e remover duplicatas
    all_tickers = set()
    for (ticker,) in watchlist_tickers:
        all_tickers.add(ticker)
    for (ticker,) in portfolio_tickers:
        all_tickers.add(ticker)
    
    return list(all_tickers)

