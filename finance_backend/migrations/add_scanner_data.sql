-- Migration: Criar tabela scanner_data para armazenar dados pré-calculados do scanner
-- Execute este script no banco de dados PostgreSQL

-- 1. Criar tabela scanner_data
CREATE TABLE IF NOT EXISTS scanner_data (
    ticker VARCHAR(20) PRIMARY KEY,
    rsi_14 NUMERIC(9, 4),
    macd_signal NUMERIC(9, 4),
    mm_9_cruza_mm_21 VARCHAR(20),  -- 'BULLISH', 'BEARISH', 'NEUTRAL'
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Criar índice para last_updated (para queries de ordenação)
CREATE INDEX IF NOT EXISTS ix_scanner_data_last_updated ON scanner_data(last_updated);

-- 3. Criar índice para mm_9_cruza_mm_21 (para filtros)
CREATE INDEX IF NOT EXISTS ix_scanner_data_mm_cross ON scanner_data(mm_9_cruza_mm_21);

