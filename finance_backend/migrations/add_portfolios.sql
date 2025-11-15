-- Migration: Adicionar suporte a múltiplos portfolios
-- Execute este script no banco de dados PostgreSQL

-- 1. Criar tabela portfolios
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

-- 2. Criar índice para user_id
CREATE INDEX IF NOT EXISTS ix_portfolios_user_id ON portfolios(user_id);

-- 3. Adicionar coluna portfolio_id em portfolio_items
ALTER TABLE portfolio_items 
ADD COLUMN IF NOT EXISTS portfolio_id INTEGER;

-- 4. Como pode apagar dados existentes, vamos deletar todos os portfolio_items existentes
-- e depois tornar a coluna NOT NULL
DELETE FROM portfolio_items;

-- 5. Adicionar foreign key constraint para portfolio_id
ALTER TABLE portfolio_items
ADD CONSTRAINT fk_portfolio_items_portfolio_id 
FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE;

-- 6. Tornar portfolio_id NOT NULL
ALTER TABLE portfolio_items
ALTER COLUMN portfolio_id SET NOT NULL;

-- 7. Criar índice para portfolio_id
CREATE INDEX IF NOT EXISTS ix_portfolio_items_portfolio_id ON portfolio_items(portfolio_id);

