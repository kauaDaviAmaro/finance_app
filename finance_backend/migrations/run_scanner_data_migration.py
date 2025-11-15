"""
Script para executar a migração de scanner_data.
Cria a tabela scanner_data para armazenar dados pré-calculados do scanner assíncrono.
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.config import settings
from app.db.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_scanner_data_migration():
    """Executa a migração de scanner_data."""
    try:
        db_url = settings.get_database_url()
        logger.info(f"Conectando ao banco de dados: {db_url.split('@')[1] if '@' in db_url else '***'}")
        
        with engine.connect() as conn:
            # 1. Criar tabela scanner_data
            logger.info("Criando tabela scanner_data...")
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS scanner_data (
                        ticker VARCHAR(20) PRIMARY KEY,
                        rsi_14 NUMERIC(9, 4),
                        macd_signal NUMERIC(9, 4),
                        mm_9_cruza_mm_21 VARCHAR(20),
                        last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                conn.commit()
                logger.info("✓ Tabela scanner_data criada")
            except Exception as e:
                logger.error(f"Erro ao criar tabela scanner_data: {e}")
                conn.rollback()
                raise
            
            # 2. Criar índice para last_updated
            logger.info("Criando índice para last_updated...")
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_scanner_data_last_updated ON scanner_data(last_updated);
                """))
                conn.commit()
                logger.info("✓ Índice ix_scanner_data_last_updated criado")
            except Exception as e:
                logger.warning(f"Índice pode já existir: {e}")
                conn.rollback()
            
            # 3. Criar índice para mm_9_cruza_mm_21
            logger.info("Criando índice para mm_9_cruza_mm_21...")
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_scanner_data_mm_cross ON scanner_data(mm_9_cruza_mm_21);
                """))
                conn.commit()
                logger.info("✓ Índice ix_scanner_data_mm_cross criado")
            except Exception as e:
                logger.warning(f"Índice pode já existir: {e}")
                conn.rollback()
        
        logger.info("=" * 50)
        logger.info("✓ Migração de scanner_data concluída com sucesso!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Erro ao executar migração: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    run_scanner_data_migration()

