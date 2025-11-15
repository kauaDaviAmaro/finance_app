"""
Script para executar a migração de portfolios.
Cria a tabela portfolios e adiciona a coluna portfolio_id em portfolio_items.
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

def run_portfolio_migration():
    """Executa a migração de portfolios."""
    try:
        db_url = settings.get_database_url()
        logger.info(f"Conectando ao banco de dados: {db_url.split('@')[1] if '@' in db_url else '***'}")
        
        with engine.connect() as conn:
            # 1. Criar tabela portfolios
            logger.info("Criando tabela portfolios...")
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS portfolios (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        name VARCHAR(255) NOT NULL,
                        category VARCHAR(100),
                        description TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE,
                        CONSTRAINT uq_user_portfolio_name UNIQUE (user_id, name)
                    );
                """))
                conn.commit()
                logger.info("✓ Tabela portfolios criada")
            except Exception as e:
                logger.error(f"Erro ao criar tabela portfolios: {e}")
                conn.rollback()
                raise
            
            # 2. Criar índice para user_id
            logger.info("Criando índice para user_id...")
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_portfolios_user_id ON portfolios(user_id);
                """))
                conn.commit()
                logger.info("✓ Índice criado")
            except Exception as e:
                logger.warning(f"Índice pode já existir: {e}")
                conn.rollback()
            
            # 3. Verificar se a coluna portfolio_id já existe
            logger.info("Verificando coluna portfolio_id...")
            try:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='portfolio_items' AND column_name='portfolio_id';
                """))
                column_exists = result.fetchone() is not None
                
                if not column_exists:
                    # 4. Adicionar coluna portfolio_id (temporariamente nullable)
                    logger.info("Adicionando coluna portfolio_id...")
                    conn.execute(text("""
                        ALTER TABLE portfolio_items 
                        ADD COLUMN portfolio_id INTEGER;
                    """))
                    conn.commit()
                    logger.info("✓ Coluna portfolio_id adicionada")
                else:
                    logger.info("✓ Coluna portfolio_id já existe")
            except Exception as e:
                logger.error(f"Erro ao verificar/adicionar coluna portfolio_id: {e}")
                conn.rollback()
                raise
            
            # 5. Deletar todos os portfolio_items existentes (conforme especificado)
            logger.info("Limpando portfolio_items existentes...")
            try:
                conn.execute(text("DELETE FROM portfolio_items;"))
                conn.commit()
                logger.info("✓ Portfolio items limpos")
            except Exception as e:
                logger.warning(f"Erro ao limpar portfolio_items: {e}")
                conn.rollback()
            
            # 6. Adicionar foreign key constraint
            logger.info("Adicionando foreign key constraint...")
            try:
                conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'fk_portfolio_items_portfolio_id'
                        ) THEN
                            ALTER TABLE portfolio_items
                            ADD CONSTRAINT fk_portfolio_items_portfolio_id 
                            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE;
                        END IF;
                    END $$;
                """))
                conn.commit()
                logger.info("✓ Foreign key constraint adicionada")
            except Exception as e:
                logger.warning(f"Constraint pode já existir: {e}")
                conn.rollback()
            
            # 7. Tornar portfolio_id NOT NULL
            logger.info("Tornando portfolio_id NOT NULL...")
            try:
                conn.execute(text("""
                    ALTER TABLE portfolio_items
                    ALTER COLUMN portfolio_id SET NOT NULL;
                """))
                conn.commit()
                logger.info("✓ Coluna portfolio_id agora é NOT NULL")
            except Exception as e:
                logger.warning(f"Erro ao tornar portfolio_id NOT NULL: {e}")
                logger.warning("Isso pode falhar se houver dados existentes. Execute manualmente se necessário.")
                conn.rollback()
            
            # 8. Criar índice para portfolio_id
            logger.info("Criando índice para portfolio_id...")
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_portfolio_items_portfolio_id ON portfolio_items(portfolio_id);
                """))
                conn.commit()
                logger.info("✓ Índice criado")
            except Exception as e:
                logger.warning(f"Índice pode já existir: {e}")
                conn.rollback()
        
        logger.info("=" * 50)
        logger.info("✓ Migração de portfolios concluída com sucesso!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Erro ao executar migração: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    run_portfolio_migration()

