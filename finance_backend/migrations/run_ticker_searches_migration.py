"""
Script para executar a migração do banco de dados.
Adiciona tabela ticker_searches para rastrear pesquisas de tickers.
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, create_engine
from app.core.config import settings
from app.db.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Executa a migração do banco de dados."""
    try:
        # Obter URL do banco
        db_url = settings.get_database_url()
        logger.info(f"Conectando ao banco de dados: {db_url.split('@')[1] if '@' in db_url else '***'}")
        
        # Ler arquivo SQL
        migration_file = os.path.join(os.path.dirname(__file__), "add_ticker_searches.sql")
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Executar migração
        with engine.connect() as conn:
            logger.info("Criando tabela ticker_searches...")
            try:
                conn.execute(text(migration_sql))
                conn.commit()
                logger.info("✓ Tabela ticker_searches criada com sucesso")
            except Exception as e:
                logger.error(f"Erro ao criar tabela ticker_searches: {e}")
                conn.rollback()
                raise
        
        logger.info("=" * 50)
        logger.info("✓ Migração concluída com sucesso!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Erro ao executar migração: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    run_migration()

