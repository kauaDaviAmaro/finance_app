"""
Script para executar a migração do banco de dados.
Adiciona campos Stripe e atualiza o enum UserRole.
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
        
        # Executar migração
        with engine.connect() as conn:
            # 1. Adicionar PRO ao enum (se ainda não existir)
            logger.info("Adicionando 'PRO' ao enum user_role...")
            try:
                conn.execute(text("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_enum 
                            WHERE enumlabel = 'PRO' 
                            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'user_role')
                        ) THEN
                            ALTER TYPE user_role ADD VALUE 'PRO';
                        END IF;
                    END $$;
                """))
                conn.commit()
                logger.info("✓ Enum 'PRO' adicionado com sucesso")
            except Exception as e:
                logger.warning(f"Enum 'PRO' pode já existir: {e}")
                conn.rollback()
            
            # 2. Adicionar coluna stripe_customer_id
            logger.info("Adicionando coluna stripe_customer_id...")
            try:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
                """))
                conn.commit()
                logger.info("✓ Coluna stripe_customer_id adicionada")
            except Exception as e:
                logger.error(f"Erro ao adicionar stripe_customer_id: {e}")
                conn.rollback()
                raise
            
            # 3. Adicionar coluna subscription_status
            logger.info("Adicionando coluna subscription_status...")
            try:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'inactive';
                """))
                conn.commit()
                logger.info("✓ Coluna subscription_status adicionada")
            except Exception as e:
                logger.error(f"Erro ao adicionar subscription_status: {e}")
                conn.rollback()
                raise
            
            # 4. Criar índice único para stripe_customer_id
            logger.info("Criando índice para stripe_customer_id...")
            try:
                conn.execute(text("""
                    CREATE UNIQUE INDEX IF NOT EXISTS ix_users_stripe_customer_id 
                    ON users(stripe_customer_id) 
                    WHERE stripe_customer_id IS NOT NULL;
                """))
                conn.commit()
                logger.info("✓ Índice criado")
            except Exception as e:
                logger.warning(f"Índice pode já existir: {e}")
                conn.rollback()
            
            # 5. Atualizar valores padrão
            logger.info("Atualizando valores padrão...")
            try:
                conn.execute(text("""
                    UPDATE users 
                    SET subscription_status = 'inactive' 
                    WHERE subscription_status IS NULL;
                """))
                conn.commit()
                logger.info("✓ Valores padrão atualizados")
            except Exception as e:
                logger.warning(f"Erro ao atualizar valores padrão: {e}")
                conn.rollback()

            # 6. Criar tabela daily_scan_results (snapshot do scanner)
            logger.info("Garantindo tabela daily_scan_results...")
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS daily_scan_results (
                        ticker VARCHAR(20) PRIMARY KEY,
                        last_price NUMERIC(18,6) NOT NULL,
                        rsi_14 NUMERIC(9,4),
                        macd_h NUMERIC(9,4),
                        bb_upper NUMERIC(18,6),
                        bb_lower NUMERIC(18,6),
                        timestamp TIMESTAMPTZ DEFAULT NOW()
                    );
                """))
                conn.commit()
                logger.info("✓ Tabela daily_scan_results pronta")
            except Exception as e:
                logger.error(f"Erro ao criar tabela daily_scan_results: {e}")
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

