from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from pydantic import BaseModel
from app.db.models import User
from app.core.security import get_admin_user
from app.celery_worker import celery_app, _run_full_market_scan_logic

router = APIRouter()


class ScanStartResponse(BaseModel):
    message: str
    task_id: Optional[str] = None
    status: str


@router.post("/scanner/start", response_model=ScanStartResponse)
def start_scanner_scan(
    async_mode: bool = Query(default=True, description="Executar de forma assíncrona via Celery"),
    current_user: User = Depends(get_admin_user)
):
    """
    Iniciar scan completo do mercado B3 manualmente (apenas admin).
    
    O scan processa todos os tickers B3 e calcula indicadores técnicos (RSI, MACD, MM).
    Pode levar 10-30 minutos para completar.
    
    Parâmetros:
    - async_mode: Se True, executa via Celery de forma assíncrona (recomendado).
                 Se False, executa diretamente (bloqueia a requisição até completar).
    """
    try:
        if async_mode:
            # Disparar task Celery de forma assíncrona
            task = celery_app.send_task(
                'app.celery_worker.run_full_market_scan',
                queue='periodic_tasks'
            )
            return ScanStartResponse(
                message="Scan iniciado de forma assíncrona. O processamento pode levar 10-30 minutos.",
                task_id=task.id,
                status="started"
            )
        else:
            # Executar diretamente (bloqueia até completar)
            result = _run_full_market_scan_logic()
            return ScanStartResponse(
                message=result or "Scan concluído com sucesso.",
                status="completed"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar scan: {str(e)}"
        )

