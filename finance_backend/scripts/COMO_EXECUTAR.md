# Como Executar o Scanner Manualmente

## Pré-requisitos

1. **Banco de dados PostgreSQL rodando e configurado**
2. **Variáveis de ambiente configuradas** (ou arquivo `.env`)
3. **Dependências instaladas** (pip install -r requirements.txt)

## Passo 1: Executar a Migração

Primeiro, crie a tabela `scanner_data`:

```bash
cd finance_backend
python migrations/run_scanner_data_migration.py
```

## Passo 2: Executar o Scanner

### Opção A: Via Script Python (Recomendado)

```bash
cd finance_backend
python -c "from app.celery_worker import _run_full_market_scan_logic; _run_full_market_scan_logic()"
```

### Opção B: Via Celery CLI (se Celery estiver rodando)

```bash
celery -A app.celery_worker call app.celery_worker.run_full_market_scan
```

### Opção C: Python Interativo

```python
from app.celery_worker import _run_full_market_scan_logic
result = _run_full_market_scan_logic()
print(result)
```

## Notas Importantes

⚠️ **O scan processa ~500+ tickers e pode levar 10-30 minutos!**

- Delay de 0.5s entre cada ticker (para evitar rate limiting do yfinance)
- Progresso é logado a cada 50 tickers
- Commits periódicos para não perder dados em caso de interrupção

## Verificar Resultados

Após executar, você pode verificar os dados:

```sql
SELECT COUNT(*) FROM scanner_data;
SELECT * FROM scanner_data LIMIT 10;
```

Ou via API (requer usuário PRO):

```
GET /scanner/?limit=10
```

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'celery'"
**Solução:** Instale as dependências: `pip install -r requirements.txt`

### Erro: "password authentication failed"
**Solução:** Verifique as credenciais do banco de dados no arquivo `.env`

### Erro: "table scanner_data does not exist"
**Solução:** Execute a migração primeiro (Passo 1)

