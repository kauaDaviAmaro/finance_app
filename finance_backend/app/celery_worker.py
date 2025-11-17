from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from app.db.database import SessionLocal, engine
from app.core.market_service import get_all_tracked_tickers, update_ticker_prices, check_and_trigger_alerts
from app.core.market.ticker_utils import get_all_b3_tickers, remove_tickers_from_json
from app.core.market.technical_analysis import get_all_scanner_indicators
from app.db.models import Base, ScannerData, DailyScanResult
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

celery_app = Celery(
    "finance_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.celery_worker']
)

# Configurações de concorrência para limitar requisições externas
celery_app.conf.update(
    # Limitar concorrência de tarefas que fazem requisições externas
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Processa uma tarefa por vez por worker
    # Limitar taxa de execução de tarefas
    task_default_rate_limit='10/m',  # Máximo 10 tarefas por minuto
    # Configurações de pool de workers
    worker_max_tasks_per_child=50,  # Reinicia worker após 50 tarefas para evitar memory leaks
)

celery_app.conf.beat_schedule = {
    # Tarefa de atualização de preços (cada 5 minutos)
    'schedule-price-update': {
        'task': 'app.celery_worker.update_prices_task',
        'schedule': 300.0,  # 5 minutos
        'args': (),
        'options': {'queue': 'periodic_tasks'}
    },
    # NOVA TAREFA: Checagem de Alertas (cada 10 minutos)
    'schedule-alert-checker': {
        'task': 'app.celery_worker.check_alerts_task',
        'schedule': 600.0,  # 10 minutos
        'args': (),
        'options': {'queue': 'periodic_tasks'}
    },
    # Tarefa de scan completo do mercado (toda madrugada às 3:00 AM)
    'schedule-full-market-scan': {
        'task': 'app.celery_worker.run_full_market_scan',
        'schedule': crontab(hour=3, minute=0),  # 3:00 AM
        'args': (),
        'options': {'queue': 'periodic_tasks'}
    },
}

@celery_app.task(
    name='app.celery_worker.update_prices_task',
    bind=True,
    # Limitar concorrência desta tarefa específica
    # Apenas 1 instância desta tarefa pode rodar por vez
    rate_limit='1/m',  # Máximo 1 execução por minuto (já é controlada pelo beat schedule)
    max_retries=3,
    default_retry_delay=60
)
def update_prices_task(self):
    """
    Tarefa agendada para buscar e atualizar os preços de todos os tickers monitorados.
    Limita concorrência para evitar sobrecarga de requisições externas.
    """
    logger.info("Iniciando tarefa de atualização de preços...")

    db = SessionLocal()
    
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Erro ao garantir a criação das tabelas no worker: {e}")
        db.close()
        return

    try:
        tickers_to_update = get_all_tracked_tickers(db)

        if not tickers_to_update:
            logger.info("Nenhum ticker para rastrear. Finalizando.")
            return "Nenhum ticker rastreado."

        # Delay entre requisições configurável (0.5s padrão para evitar rate limiting)
        update_ticker_prices(tickers_to_update, db, delay_between_requests=0.5)

        logger.info(f"Preços de {len(tickers_to_update)} tickers atualizados com sucesso no cache.")
        return f"Atualização de preços concluída para {len(tickers_to_update)} tickers."

    except Exception as e:
        logger.error(f"Erro crítico na tarefa de atualização de preços: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60, max_retries=3)
        
    finally:
        db.close()


@celery_app.task(
    name='app.celery_worker.check_alerts_task',
    bind=True,
    # Limitar concorrência desta tarefa também
    rate_limit='1/m',
    max_retries=3,
    default_retry_delay=60
)
def check_alerts_task(self):
    """
    Tarefa agendada para verificar se algum alerta foi disparado.
    Limita concorrência para evitar sobrecarga de requisições externas.
    """
    logger.info("Iniciando tarefa de checagem de alertas...")

    db = SessionLocal()
    
    try:
        # Tenta criar tabelas, se necessário (segurança)
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Erro ao garantir a criação das tabelas no worker: {e}")
        db.close()
        return

    try:
        # Chama a lógica de checagem do market_service
        triggered_count = check_and_trigger_alerts(db)

        if triggered_count > 0:
            logger.warning(f"{triggered_count} alertas disparados!")
        else:
            logger.info("Nenhum alerta disparado nesta rodada.")
            
        return f"Checagem de alertas concluída. {triggered_count} alertas disparados."

    except Exception as e:
        logger.error(f"Erro crítico na tarefa de checagem de alertas: {e}", exc_info=True)
        # Tenta re-executar a tarefa
        raise self.retry(exc=e, countdown=60, max_retries=3)
        
    finally:
        db.close()


def _run_full_market_scan_logic():
    """
    Lógica principal do scan completo do mercado B3.
    Pode ser chamada diretamente ou via task Celery.
    """
    logger.info("Iniciando scan completo do mercado B3...")

    db = SessionLocal()
    
    try:
        # Garantir que as tabelas existem
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Erro ao garantir a criação das tabelas no worker: {e}")
        db.close()
        return None

    try:
        # Ler lista completa de tickers B3 do arquivo estático
        all_tickers = get_all_b3_tickers()
        logger.info(f"Processando {len(all_tickers)} tickers do mercado B3...")
        
        success_count = 0
        error_count = 0
        invalid_tickers = []  # Lista de tickers que não existem para remover do JSON
        delay_between_requests = 0.5  # Delay para evitar rate limiting do yfinance
        
        for idx, ticker in enumerate(all_tickers, 1):
            try:
                # Calcular TODOS os indicadores em uma única chamada (otimização)
                all_indicators = get_all_scanner_indicators(ticker)
                
                # Verificar se temos dados válidos antes de fazer operações no banco
                has_scanner_data = any([
                    all_indicators.get('rsi_14') is not None,
                    all_indicators.get('macd_signal') is not None,
                    all_indicators.get('mm_9_cruza_mm_21') != 'NEUTRAL'
                ])
                
                has_daily_data = all_indicators.get('last_price') is not None
                
                # Verificar se o ticker é inválido (não existe ou não tem dados)
                # Um ticker é considerado inválido se não tem preço E não tem RSI
                is_invalid = (
                    all_indicators.get('last_price') is None and 
                    all_indicators.get('rsi_14') is None
                )
                
                if is_invalid:
                    invalid_tickers.append(ticker)
                    error_count += 1
                    logger.debug(f"Ticker {ticker}: sem dados disponíveis (ticker inválido/delistado)")
                    # Não atualizar banco para tickers inválidos
                    continue
                
                # Atualizar ScannerData apenas se tivermos dados válidos
                if has_scanner_data:
                    scanner_data = db.query(ScannerData).filter(ScannerData.ticker == ticker).first()
                    
                    if scanner_data:
                        # UPDATE
                        scanner_data.rsi_14 = all_indicators['rsi_14']
                        scanner_data.macd_signal = all_indicators['macd_signal']
                        scanner_data.mm_9_cruza_mm_21 = all_indicators['mm_9_cruza_mm_21']
                        # last_updated é atualizado automaticamente pelo onupdate
                    else:
                        # INSERT
                        scanner_data = ScannerData(
                            ticker=ticker,
                            rsi_14=all_indicators['rsi_14'],
                            macd_signal=all_indicators['macd_signal'],
                            mm_9_cruza_mm_21=all_indicators['mm_9_cruza_mm_21']
                        )
                        db.add(scanner_data)
                
                # Atualizar DailyScanResult apenas se tivermos dados válidos
                if has_daily_data:
                    daily_scan = db.query(DailyScanResult).filter(DailyScanResult.ticker == ticker).first()
                    
                    if daily_scan:
                        # UPDATE
                        daily_scan.last_price = all_indicators['last_price']
                        daily_scan.rsi_14 = all_indicators['rsi_14']
                        daily_scan.macd_h = all_indicators['macd_h']
                        daily_scan.bb_upper = all_indicators['bb_upper']
                        daily_scan.bb_lower = all_indicators['bb_lower']
                        # timestamp é atualizado automaticamente
                    else:
                        # INSERT
                        daily_scan = DailyScanResult(
                            ticker=ticker,
                            last_price=all_indicators['last_price'],
                            rsi_14=all_indicators['rsi_14'],
                            macd_h=all_indicators['macd_h'],
                            bb_upper=all_indicators['bb_upper'],
                            bb_lower=all_indicators['bb_lower']
                        )
                        db.add(daily_scan)
                
                # Contar como sucesso apenas se tivermos pelo menos alguns dados
                if has_scanner_data or has_daily_data:
                    success_count += 1
                
                # Log de progresso a cada 50 tickers
                if idx % 50 == 0:
                    logger.info(f"Progresso: {idx}/{len(all_tickers)} tickers processados ({success_count} sucesso, {error_count} erros, {len(invalid_tickers)} inválidos)")
                    db.commit()  # Commit periódico para não perder dados
                
                # Delay entre requisições para evitar rate limiting
                time.sleep(delay_between_requests)
                
            except Exception as e:
                error_count += 1
                # Adicionar à lista de inválidos se houver erro ao buscar dados
                invalid_tickers.append(ticker)
                logger.warning(f"Erro ao processar ticker {ticker}: {e}")
                # Continuar processamento mesmo se um ticker falhar
                continue
        
        # Commit final
        db.commit()
        
        # Remover tickers inválidos do arquivo JSON
        if invalid_tickers:
            try:
                removed_count = remove_tickers_from_json(invalid_tickers)
                logger.info(f"Removidos {removed_count} tickers inválidos do arquivo JSON: {', '.join(invalid_tickers[:10])}{'...' if len(invalid_tickers) > 10 else ''}")
            except Exception as e:
                logger.error(f"Erro ao remover tickers inválidos do JSON: {e}")
        
        logger.info(
            f"Scan completo concluído! "
            f"Total: {len(all_tickers)}, Sucesso: {success_count}, Erros: {error_count}, "
            f"Tickers inválidos removidos: {len(invalid_tickers)}"
        )
        
        return f"Scan completo concluído. {success_count}/{len(all_tickers)} tickers processados com sucesso. {len(invalid_tickers)} tickers inválidos removidos."

    except Exception as e:
        logger.error(f"Erro crítico no scan completo do mercado: {e}", exc_info=True)
        db.rollback()
        raise
        
    finally:
        db.close()


@celery_app.task(
    name='app.celery_worker.run_full_market_scan',
    bind=True,
    rate_limit='1/h',  # Máximo 1 execução por hora (já é controlada pelo beat schedule)
    max_retries=2,
    default_retry_delay=3600  # 1 hora em caso de retry
)
def run_full_market_scan(self):
    """
    Tarefa agendada para fazer scan completo do mercado B3.
    Calcula indicadores técnicos (RSI, MACD, MM cruzamento) para todos os tickers
    e salva na tabela scanner_data para consulta rápida pela API.
    Roda toda madrugada às 3:00 AM.
    """
    try:
        result = _run_full_market_scan_logic()
        return result
    except Exception as e:
        # Retry apenas em caso de erro crítico (não para erros individuais de tickers)
        raise self.retry(exc=e, countdown=3600, max_retries=2)

