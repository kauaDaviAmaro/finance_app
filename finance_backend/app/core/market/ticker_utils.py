"""
Utilitários para formatação e validação de tickers.
"""
import re
import json
from pathlib import Path
from typing import List


def format_ticker(ticker: str) -> str:
    """
    Ajusta o ticker. Se for um ticker da B3 (ex: 4 letras + número),
    adiciona o '.SA' para o yfinance.
    """
    ticker_upper = ticker.upper().strip()
    
    if ticker_upper.endswith(".SA"):
        return ticker_upper
    
    b3_pattern = re.compile(r"^[A-Z]{4}\d+$")
    
    if b3_pattern.match(ticker_upper):
        return f"{ticker_upper}.SA"
        
    return ticker_upper


def get_all_b3_tickers() -> List[str]:
    """
    Lê a lista completa de tickers B3 do arquivo JSON estático local.
    Retorna uma lista de strings com os tickers (ex: ['PETR4', 'VALE3', ...]).
    Sem dependência externa - arquivo estático versionado.
    """
    # Caminho relativo ao arquivo atual
    current_dir = Path(__file__).parent
    json_path = current_dir / "static" / "b3_stocks_tickers.json"
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Extrair apenas os tickers da lista de dicionários
            tickers = [item['ticker'] for item in data if 'ticker' in item]
            return tickers
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Arquivo de tickers B3 não encontrado em {json_path}. "
            "Certifique-se de que o arquivo b3_stocks_tickers.json está em app/core/market/static/"
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Erro ao decodificar JSON de tickers B3: {e}")
    except Exception as e:
        raise RuntimeError(f"Erro ao ler arquivo de tickers B3: {e}")


def remove_tickers_from_json(tickers_to_remove: List[str]) -> int:
    """
    Remove tickers do arquivo JSON estático.
    
    Args:
        tickers_to_remove: Lista de tickers a serem removidos (ex: ['TICKER1', 'TICKER2'])
    
    Returns:
        Número de tickers removidos
    """
    if not tickers_to_remove:
        return 0
    
    current_dir = Path(__file__).parent
    json_path = current_dir / "static" / "b3_stocks_tickers.json"
    
    try:
        # Ler arquivo atual
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Converter para set para busca mais rápida
        tickers_to_remove_set = {ticker.upper() for ticker in tickers_to_remove}
        
        # Filtrar tickers a serem removidos
        original_count = len(data)
        data = [item for item in data if item.get('ticker', '').upper() not in tickers_to_remove_set]
        removed_count = original_count - len(data)
        
        # Salvar arquivo atualizado
        if removed_count > 0:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        
        return removed_count
        
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Arquivo de tickers B3 não encontrado em {json_path}. "
            "Certifique-se de que o arquivo b3_stocks_tickers.json está em app/core/market/static/"
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Erro ao decodificar JSON de tickers B3: {e}")
    except Exception as e:
        raise RuntimeError(f"Erro ao atualizar arquivo de tickers B3: {e}")
