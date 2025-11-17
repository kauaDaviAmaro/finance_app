-- Migration: Adicionar funcionalidades de planejamento financeiro
-- Execute este script no banco de dados PostgreSQL

-- 1. Criar enum para status de metas de investimento
DO $$ BEGIN
    CREATE TYPE investment_goal_status AS ENUM ('ACTIVE', 'COMPLETED', 'CANCELLED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Criar tabela investment_goals
CREATE TABLE IF NOT EXISTS investment_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    target_amount NUMERIC(18, 2) NOT NULL,
    current_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    target_date DATE NOT NULL,
    portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE SET NULL,
    status investment_goal_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT chk_target_amount_positive CHECK (target_amount > 0),
    CONSTRAINT chk_current_amount_non_negative CHECK (current_amount >= 0)
);

-- 3. Criar índices para investment_goals
CREATE INDEX IF NOT EXISTS ix_investment_goals_user_id ON investment_goals(user_id);
CREATE INDEX IF NOT EXISTS ix_investment_goals_portfolio_id ON investment_goals(portfolio_id);

-- 4. Criar tabela financial_plans
CREATE TABLE IF NOT EXISTS financial_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    monthly_income NUMERIC(18, 2),
    monthly_expenses NUMERIC(18, 2),
    emergency_fund_target NUMERIC(18, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uq_user_financial_plan_name UNIQUE (user_id, name),
    CONSTRAINT chk_monthly_income_non_negative CHECK (monthly_income IS NULL OR monthly_income >= 0),
    CONSTRAINT chk_monthly_expenses_non_negative CHECK (monthly_expenses IS NULL OR monthly_expenses >= 0),
    CONSTRAINT chk_emergency_fund_non_negative CHECK (emergency_fund_target IS NULL OR emergency_fund_target >= 0)
);

-- 5. Criar índices para financial_plans
CREATE INDEX IF NOT EXISTS ix_financial_plans_user_id ON financial_plans(user_id);

-- 6. Criar tabela retirement_plans
CREATE TABLE IF NOT EXISTS retirement_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_age INTEGER NOT NULL,
    retirement_age INTEGER NOT NULL,
    current_savings NUMERIC(18, 2) NOT NULL DEFAULT 0,
    monthly_contribution NUMERIC(18, 2) NOT NULL DEFAULT 0,
    expected_return_rate NUMERIC(5, 2) NOT NULL DEFAULT 7.0,
    inflation_rate NUMERIC(5, 2) NOT NULL DEFAULT 3.0,
    target_monthly_income NUMERIC(18, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT chk_current_age_valid CHECK (current_age >= 18 AND current_age <= 100),
    CONSTRAINT chk_retirement_age_valid CHECK (retirement_age >= 18 AND retirement_age <= 100),
    CONSTRAINT chk_retirement_age_greater CHECK (retirement_age > current_age),
    CONSTRAINT chk_current_savings_non_negative CHECK (current_savings >= 0),
    CONSTRAINT chk_monthly_contribution_non_negative CHECK (monthly_contribution >= 0),
    CONSTRAINT chk_return_rate_valid CHECK (expected_return_rate >= 0 AND expected_return_rate <= 100),
    CONSTRAINT chk_inflation_rate_valid CHECK (inflation_rate >= 0 AND inflation_rate <= 100),
    CONSTRAINT chk_target_income_positive CHECK (target_monthly_income > 0)
);

-- 7. Criar índices para retirement_plans
CREATE INDEX IF NOT EXISTS ix_retirement_plans_user_id ON retirement_plans(user_id);

-- 8. Criar tabela wealth_history
CREATE TABLE IF NOT EXISTS wealth_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_value NUMERIC(18, 2) NOT NULL,
    portfolio_value NUMERIC(18, 2) NOT NULL DEFAULT 0,
    cash_value NUMERIC(18, 2) NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_wealth_date UNIQUE (user_id, date),
    CONSTRAINT chk_total_value_non_negative CHECK (total_value >= 0),
    CONSTRAINT chk_portfolio_value_non_negative CHECK (portfolio_value >= 0),
    CONSTRAINT chk_cash_value_non_negative CHECK (cash_value >= 0)
);

-- 9. Criar índices para wealth_history
CREATE INDEX IF NOT EXISTS ix_wealth_history_user_id ON wealth_history(user_id);
CREATE INDEX IF NOT EXISTS ix_wealth_history_date ON wealth_history(date);

