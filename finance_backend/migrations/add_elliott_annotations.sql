-- Migração para criar tabela elliott_annotations
-- Armazena anotações manuais de ondas de Elliott por usuário/ticker/período

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

-- Criar índices
CREATE INDEX IF NOT EXISTS ix_elliott_annotations_user_id ON elliott_annotations(user_id);
CREATE INDEX IF NOT EXISTS ix_elliott_annotations_ticker ON elliott_annotations(ticker);

-- Criar constraint único para user_id + ticker + period
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_ticker_period 
    ON elliott_annotations(user_id, ticker, period);

