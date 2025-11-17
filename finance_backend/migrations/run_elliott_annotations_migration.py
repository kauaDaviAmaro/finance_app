"""
Script para executar a migração do banco de dados.
Adiciona tabela elliott_annotations para armazenar anotações manuais de ondas de Elliott.
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Executa a migração do banco de dados."""
    try:
        logger.info("Iniciando migração para tabela elliott_annotations...")
        
        # Executar migração
        with engine.connect() as conn:
            # Criar tabela elliott_annotations
            logger.info("Criando tabela elliott_annotations...")
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS elliott_annotations (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        ticker VARCHAR(20) NOT NULL,
                        period VARCHAR(20) NOT NULL,
                        annotations JSONB NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ,
                        CONSTRAINT fk_elliott_annotations_user 
                            FOREIGN KEY (user_id) 
                            REFERENCES users(id) 
                            ON DELETE CASCADE
                    );
                """))
                conn.commit()
                logger.info("✓ Tabela elliott_annotations criada")
            except Exception as e:
                logger.error(f"Erro ao criar tabela: {e}")
                conn.rollback()
                raise
            
            # Criar índices
            logger.info("Criando índices...")
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_elliott_annotations_user_id 
                    ON elliott_annotations(user_id);
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_elliott_annotations_ticker 
                    ON elliott_annotations(ticker);
                """))
                conn.commit()
                logger.info("✓ Índices criados")
            except Exception as e:
                logger.warning(f"Erro ao criar índices (podem já existir): {e}")
                conn.rollback()
            
            # Criar constraint único
            logger.info("Criando constraint único...")
            try:
                conn.execute(text("""
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_user_ticker_period 
                    ON elliott_annotations(user_id, ticker, period);
                """))
                conn.commit()
                logger.info("✓ Constraint único criado")
            except Exception as e:
                logger.warning(f"Constraint único pode já existir: {e}")
                conn.rollback()
        
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

