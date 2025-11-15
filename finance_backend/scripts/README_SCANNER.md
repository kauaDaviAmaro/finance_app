# Como Executar o Scanner Manualmente

Para popular os dados do scanner ou testar a funcionalidade, você pode executar o scan manualmente de duas formas:

## Opção 1: Script Python (Recomendado)

Execute o script diretamente:

```bash
cd finance_backend
python scripts/run_scanner_manual.py
```

Ou a partir da raiz do projeto:

```bash
python finance_backend/scripts/run_scanner_manual.py
```

## Opção 2: Via Celery CLI

Se o Celery estiver rodando, você pode disparar a task manualmente:

```bash
celery -A app.celery_worker call app.celery_worker.run_full_market_scan
```

## Opção 3: Python Interativo

```python
from app.celery_worker import _run_full_market_scan_logic
result = _run_full_market_scan_logic()
print(result)
```

## Nota Importante

⚠️ **O scan processa ~500+ tickers e pode levar vários minutos!**

- Delay de 0.5s entre cada ticker (para evitar rate limiting)
- Progresso é logado a cada 50 tickers
- Commits periódicos para não perder dados em caso de interrupção

## Verificar Resultados

Após executar, você pode verificar os dados no banco:

```sql
SELECT COUNT(*) FROM scanner_data;
SELECT * FROM scanner_data LIMIT 10;
```

Ou via API (requer usuário PRO):

```
GET /scanner/?limit=10
```

