-- Migration: Adicionar suporte a backtesting e simulação de estratégias
-- Execute este script no banco de dados PostgreSQL

-- 1. Criar ENUMs
DO $$ BEGIN
    CREATE TYPE strategy_type AS ENUM ('GRAPHICAL', 'JSON');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE condition_type AS ENUM ('ENTRY', 'EXIT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE condition_logic AS ENUM ('AND', 'OR');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE paper_trade_status AS ENUM ('ACTIVE', 'PAUSED', 'STOPPED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Criar tabela strategies
CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    strategy_type strategy_type NOT NULL DEFAULT 'GRAPHICAL',
    json_config JSONB,
    initial_capital NUMERIC(18, 2) NOT NULL DEFAULT 100000.00,
    position_size NUMERIC(5, 2) NOT NULL DEFAULT 100.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uq_user_strategy_name UNIQUE (user_id, name)
);

-- 3. Criar índices para strategies
CREATE INDEX IF NOT EXISTS ix_strategies_user_id ON strategies(user_id);
CREATE INDEX IF NOT EXISTS ix_strategies_strategy_type ON strategies(strategy_type);

-- 4. Criar tabela strategy_conditions
CREATE TABLE IF NOT EXISTS strategy_conditions (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    condition_type condition_type NOT NULL,
    indicator VARCHAR(50) NOT NULL,
    operator VARCHAR(20) NOT NULL,
    value NUMERIC(18, 6),
    logic condition_logic NOT NULL DEFAULT 'AND',
    "order" INTEGER NOT NULL DEFAULT 0
);

-- 5. Criar índices para strategy_conditions
CREATE INDEX IF NOT EXISTS ix_strategy_conditions_strategy_id ON strategy_conditions(strategy_id);
CREATE INDEX IF NOT EXISTS ix_strategy_conditions_condition_type ON strategy_conditions(condition_type);

-- 6. Criar tabela backtests
CREATE TABLE IF NOT EXISTS backtests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    period VARCHAR(20) NOT NULL,
    start_date DATE,
    end_date DATE,
    total_return NUMERIC(10, 4),
    annualized_return NUMERIC(10, 4),
    sharpe_ratio NUMERIC(10, 4),
    max_drawdown NUMERIC(10, 4),
    win_rate NUMERIC(5, 2),
    profit_factor NUMERIC(10, 4),
    total_trades INTEGER NOT NULL DEFAULT 0,
    winning_trades INTEGER NOT NULL DEFAULT 0,
    losing_trades INTEGER NOT NULL DEFAULT 0,
    avg_win NUMERIC(18, 2),
    avg_loss NUMERIC(18, 2),
    final_capital NUMERIC(18, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Criar índices para backtests
CREATE INDEX IF NOT EXISTS ix_backtests_user_id ON backtests(user_id);
CREATE INDEX IF NOT EXISTS ix_backtests_strategy_id ON backtests(strategy_id);
CREATE INDEX IF NOT EXISTS ix_backtests_ticker ON backtests(ticker);
CREATE INDEX IF NOT EXISTS ix_backtests_created_at ON backtests(created_at);

-- 8. Criar tabela backtest_trades
CREATE TABLE IF NOT EXISTS backtest_trades (
    id SERIAL PRIMARY KEY,
    backtest_id INTEGER NOT NULL REFERENCES backtests(id) ON DELETE CASCADE,
    trade_date DATE NOT NULL,
    trade_type VARCHAR(10) NOT NULL,
    price NUMERIC(18, 6) NOT NULL,
    quantity INTEGER NOT NULL,
    pnl NUMERIC(18, 2),
    capital_after NUMERIC(18, 2)
);

-- 9. Criar índices para backtest_trades
CREATE INDEX IF NOT EXISTS ix_backtest_trades_backtest_id ON backtest_trades(backtest_id);
CREATE INDEX IF NOT EXISTS ix_backtest_trades_trade_date ON backtest_trades(trade_date);

-- 10. Criar tabela paper_trades
CREATE TABLE IF NOT EXISTS paper_trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    initial_capital NUMERIC(18, 2) NOT NULL,
    current_capital NUMERIC(18, 2) NOT NULL,
    status paper_trade_status NOT NULL DEFAULT 'ACTIVE',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    stopped_at TIMESTAMP WITH TIME ZONE,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. Criar índices para paper_trades
CREATE INDEX IF NOT EXISTS ix_paper_trades_user_id ON paper_trades(user_id);
CREATE INDEX IF NOT EXISTS ix_paper_trades_strategy_id ON paper_trades(strategy_id);
CREATE INDEX IF NOT EXISTS ix_paper_trades_status ON paper_trades(status);
CREATE INDEX IF NOT EXISTS ix_paper_trades_ticker ON paper_trades(ticker);

-- 12. Criar tabela paper_trade_positions
CREATE TABLE IF NOT EXISTS paper_trade_positions (
    id SERIAL PRIMARY KEY,
    paper_trade_id INTEGER NOT NULL REFERENCES paper_trades(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    entry_price NUMERIC(18, 6) NOT NULL,
    entry_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    exit_price NUMERIC(18, 6),
    exit_date TIMESTAMP WITH TIME ZONE,
    pnl NUMERIC(18, 2)
);

-- 13. Criar índices para paper_trade_positions
CREATE INDEX IF NOT EXISTS ix_paper_trade_positions_paper_trade_id ON paper_trade_positions(paper_trade_id);
CREATE INDEX IF NOT EXISTS ix_paper_trade_positions_ticker ON paper_trade_positions(ticker);

