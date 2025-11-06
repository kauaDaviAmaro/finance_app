from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from app.db.database import SessionLocal, engine
from app.core.market_service import get_all_tracked_tickers, update_ticker_prices, check_and_trigger_alerts
from app.db.models import Base
import logging

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

