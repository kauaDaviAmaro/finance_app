-- Migration: Adicionar campos Stripe e atualizar enum UserRole
-- Execute este script no banco de dados PostgreSQL

-- 1. Adicionar valor PRO ao enum user_role (se ainda não existir)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'PRO' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'user_role')) THEN
        ALTER TYPE user_role ADD VALUE 'PRO';
    END IF;
END $$;

-- 2. Adicionar coluna stripe_customer_id
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);

-- 3. Adicionar coluna subscription_status
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'inactive';

-- 4. Criar índice único para stripe_customer_id
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_stripe_customer_id ON users(stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;

-- 5. Atualizar valores padrão para usuários existentes
UPDATE users 
SET subscription_status = 'inactive' 
WHERE subscription_status IS NULL;











