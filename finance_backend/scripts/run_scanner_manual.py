"""
Script para executar manualmente o scan completo do mercado.
Útil para popular os dados inicialmente ou testar a funcionalidade.

Uso:
    python finance_backend/scripts/run_scanner_manual.py
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.celery_worker import _run_full_market_scan_logic
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Executando scan completo do mercado manualmente...")
    logger.info("=" * 60)
    
    try:
        result = _run_full_market_scan_logic()
        logger.info("=" * 60)
        logger.info("✓ Scan completo executado com sucesso!")
        logger.info(f"Resultado: {result}")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ Erro ao executar scan: {e}")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

