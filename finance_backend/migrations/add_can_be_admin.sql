-- Migration: Adicionar campo can_be_admin na tabela users
-- Execute este script no banco de dados PostgreSQL

-- Adicionar coluna can_be_admin
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS can_be_admin BOOLEAN DEFAULT TRUE NOT NULL;

-- Atualizar valores padrão para usuários existentes (todos podem ser admin por padrão)
UPDATE users 
SET can_be_admin = TRUE 
WHERE can_be_admin IS NULL;

