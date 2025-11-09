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
import time
import logging

from app.core.market.ticker_utils import format_ticker

logger = logging.getLogger(__name__)


def get_current_price(ticker: str, db: Session = None, cache_threshold_seconds: int = 900) -> Optional[float]:
    """
    Busca o preço atual de um ticker.
    Primeiro consulta o cache do banco de dados (TickerPrice).
    Se não encontrar ou o cache estiver desatualizado (idade > cache_threshold_seconds), busca na yfinance.
    Retorna None se não conseguir buscar.
    
    Args:
        ticker: Símbolo do ticker
        db: Sessão do banco de dados (opcional)
        cache_threshold_seconds: Idade máxima do cache em segundos (padrão: 900 = 15 minutos)
                                Use 0 para forçar busca direta, ignorando cache
    """
    from app.db.models import TickerPrice
    
    formatted_ticker = format_ticker(ticker)
    
    # Se temos acesso ao DB, consultar o cache primeiro (a menos que threshold seja 0)
    if db and cache_threshold_seconds > 0:
        try:
            cached_price = db.query(TickerPrice).filter(
                TickerPrice.ticker == formatted_ticker
            ).first()
            
            if cached_price:
                # Verificar se o cache está recente (menos que cache_threshold_seconds)
                now = datetime.now(cached_price.timestamp.tzinfo) if cached_price.timestamp.tzinfo else datetime.now()
                cache_age = now - cached_price.timestamp
                if cache_age.total_seconds() < cache_threshold_seconds:
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


def _fetch_ticker_price_with_backoff(ticker: str, max_retries: int = 3, initial_delay: float = 1.0) -> Optional[float]:
    """
    Busca o preço de um ticker com retry e backoff exponencial.
    
    Args:
        ticker: Símbolo do ticker
        max_retries: Número máximo de tentativas
        initial_delay: Delay inicial em segundos (será multiplicado exponencialmente)
    
    Returns:
        Preço do ticker ou None se falhar após todas as tentativas
    """
    formatted_ticker = format_ticker(ticker)
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(formatted_ticker)
            data = stock.history(period="1d")
            
            if data.empty:
                logger.warning(f"Dados vazios para {formatted_ticker} (tentativa {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2  # Backoff exponencial
                    continue
                return None
            
            current_price = float(data['Close'].iloc[-1])
            return current_price
            
        except Exception as e:
            logger.warning(f"Erro ao buscar preço para {formatted_ticker} (tentativa {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                # Backoff exponencial: espera delay antes de tentar novamente
                logger.info(f"Aguardando {delay:.2f}s antes de tentar novamente...")
                time.sleep(delay)
                delay *= 2  # Aumenta o delay exponencialmente
            else:
                logger.error(f"Falha ao buscar preço para {formatted_ticker} após {max_retries} tentativas")
                return None
    
    return None


def update_ticker_prices(tickers: List[str], db: Session, delay_between_requests: float = 0.5) -> Dict[str, Optional[float]]:
    """
    Atualiza os preços de múltiplos tickers no cache.
    Esta função será chamada pelo worker assíncrono (Cron/Celery) a cada 5-15 minutos.
    
    Implementa:
    - Delay entre requisições para evitar rate limiting
    - Backoff exponencial em caso de falhas
    - Retry automático para requisições falhadas
    
    Args:
        tickers: Lista de tickers para atualizar
        db: Sessão do banco de dados
        delay_between_requests: Delay em segundos entre cada requisição (padrão: 0.5s)
    
    Returns:
        Dicionário com ticker -> preço atualizado
    """
    from app.db.models import TickerPrice
    
    results = {}
    total_tickers = len(tickers)
    
    logger.info(f"Iniciando atualização de preços para {total_tickers} tickers (delay entre requisições: {delay_between_requests}s)")
    
    for index, ticker in enumerate(tickers, 1):
        formatted_ticker = format_ticker(ticker)
        
        # Delay entre requisições para evitar rate limiting (exceto no primeiro ticker)
        if index > 1:
            time.sleep(delay_between_requests)
        
        # Buscar preço com backoff exponencial
        current_price = _fetch_ticker_price_with_backoff(ticker)
        results[ticker] = current_price
        
        if current_price is None:
            logger.warning(f"Não foi possível obter preço para {ticker}")
            continue
        
        try:
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
            
            logger.debug(f"Preço atualizado para {ticker}: {current_price} ({index}/{total_tickers})")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar cache de preço para {ticker}: {e}")
            db.rollback()
    
    # Commit todas as atualizações de uma vez
    try:
        db.commit()
        logger.info(f"Atualização concluída: {len([r for r in results.values() if r is not None])}/{total_tickers} tickers atualizados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao commitar atualizações de preços: {e}")
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

