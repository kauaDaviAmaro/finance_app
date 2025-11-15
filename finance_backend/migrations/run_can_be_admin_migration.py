"""
Script para executar a migração do campo can_be_admin.
Adiciona o campo can_be_admin na tabela users.
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
    """Executa a migração do campo can_be_admin."""
    try:
        logger.info("Iniciando migração: adicionar campo can_be_admin...")
        
        with engine.connect() as conn:
            # Adicionar coluna can_be_admin
            logger.info("Adicionando coluna can_be_admin...")
            try:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS can_be_admin BOOLEAN DEFAULT TRUE NOT NULL;
                """))
                conn.commit()
                logger.info("✓ Coluna can_be_admin adicionada")
            except Exception as e:
                logger.error(f"Erro ao adicionar can_be_admin: {e}")
                conn.rollback()
                raise
            
            # Atualizar valores padrão para usuários existentes
            logger.info("Atualizando valores padrão...")
            try:
                conn.execute(text("""
                    UPDATE users 
                    SET can_be_admin = TRUE 
                    WHERE can_be_admin IS NULL;
                """))
                conn.commit()
                logger.info("✓ Valores padrão atualizados")
            except Exception as e:
                logger.warning(f"Erro ao atualizar valores padrão: {e}")
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

