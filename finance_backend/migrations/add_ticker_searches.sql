-- Migration: Add ticker_searches table
-- Created: 2024

-- Create ticker_searches table
CREATE TABLE IF NOT EXISTS ticker_searches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    ticker VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_ticker_searches_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for ticker_searches
CREATE INDEX IF NOT EXISTS idx_ticker_searches_user_id ON ticker_searches(user_id);
CREATE INDEX IF NOT EXISTS idx_ticker_searches_ticker ON ticker_searches(ticker);
CREATE INDEX IF NOT EXISTS idx_ticker_searches_created_at ON ticker_searches(created_at);

