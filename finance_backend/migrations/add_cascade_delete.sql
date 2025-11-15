-- Migration: Add CASCADE DELETE to foreign keys
-- This ensures that when a user is deleted, all related records are also deleted

-- Drop existing foreign key constraints
ALTER TABLE alerts DROP CONSTRAINT IF EXISTS alerts_user_id_fkey;
ALTER TABLE watchlist_items DROP CONSTRAINT IF EXISTS watchlist_items_user_id_fkey;
ALTER TABLE portfolio_items DROP CONSTRAINT IF EXISTS portfolio_items_user_id_fkey;

-- Recreate foreign key constraints with CASCADE DELETE
ALTER TABLE alerts 
    ADD CONSTRAINT alerts_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE watchlist_items 
    ADD CONSTRAINT watchlist_items_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE portfolio_items 
    ADD CONSTRAINT portfolio_items_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

