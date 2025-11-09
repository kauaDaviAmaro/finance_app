# Migrations

Este diretório contém scripts de migração do banco de dados.

## Migração: Adicionar campos Stripe

Esta migração adiciona os campos necessários para o sistema de assinaturas:

- Adiciona `PRO` ao enum `user_role`
- Adiciona coluna `stripe_customer_id` (VARCHAR(255), nullable, unique)
- Adiciona coluna `subscription_status` (VARCHAR(50), default='inactive')
- Cria índice único para `stripe_customer_id`

### Como executar:

#### Opção 1: Usando o script Python (Recomendado)

```bash
# No container do backend
docker-compose -f docker-compose.dev.yml exec api python migrations/run_migration.py

# Ou localmente
cd finance_backend
python migrations/run_migration.py
```

#### Opção 2: Executando SQL diretamente

```bash
# No container do banco de dados
docker-compose -f docker-compose.dev.yml exec db psql -U postgres -d finances_db -f /path/to/add_stripe_fields.sql

# Ou copiando o arquivo e executando
docker-compose -f docker-compose.dev.yml exec -T db psql -U postgres -d finances_db < migrations/add_stripe_fields.sql
```

#### Opção 3: Manualmente via psql

```bash
# Conectar ao banco
docker-compose -f docker-compose.dev.yml exec db psql -U postgres -d finances_db

# Executar os comandos do arquivo add_stripe_fields.sql
```

### Verificar se a migração foi aplicada:

```sql
-- Verificar colunas
\d users

-- Verificar enum
SELECT enum_range(NULL::user_role);

-- Verificar índices
SELECT indexname FROM pg_indexes WHERE tablename = 'users';
```



