from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from app.db.database import SessionLocal, engine
from app.core.market_service import get_all_tracked_tickers, update_ticker_prices
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

celery_app.conf.beat_schedule = {
    'schedule-price-update': {
        'task': 'app.celery_worker.update_prices_task',
        'schedule': 300.0,
        'args': (),
        'options': {'queue': 'periodic_tasks'}
    },
}

@celery_app.task(name='app.celery_worker.update_prices_task', bind=True)
def update_prices_task(self):
    """
    Tarefa agendada para buscar e atualizar os preços de todos os tickers monitorados.
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

        update_ticker_prices(tickers_to_update, db)

        logger.info(f"Preços de {len(tickers_to_update)} tickers atualizados com sucesso no cache.")
        return f"Atualização de preços concluída para {len(tickers_to_update)} tickers."

    except Exception as e:
        logger.error(f"Erro crítico na tarefa de atualização de preços: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60, max_retries=3)
        
    finally:
        db.close()

