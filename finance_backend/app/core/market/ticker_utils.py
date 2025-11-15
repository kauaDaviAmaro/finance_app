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


# Universo de análise: componentes do IBOV (lista editável)
IBOV_TICKERS = [
    # Blue chips
    "PETR4", "PETR3", "VALE3", "ITUB4", "BBDC4", "ABEV3", "BBAS3", "B3SA3",
    "WEGE3", "SUZB3", "GGBR4", "CSNA3", "USIM5", "KLBN11", "ELET3", "ELET6",
    "PRIO3", "RAIZ4", "VIVT3", "TIMS3", "ELET3", "ELET6",
    # Consumo e varejo
    "MGLU3", "VIIA3", "LREN3", "AMER3", "ARZZ3", "ALPA4", "PCAR3", "PETZ3",
    # Siderurgia e papel
    "BRFS3", "EMBR3", "SUZB3", "KLBN11",
    # Energia e saneamento
    "ENBR3", "CMIG4", "CPLE6", "TAEE11", "EQTL3",
    # Construção e imobiliário
    "MRVE3", "CYRE3", "EZTC3",
    # Educação e tecnologia
    "LWSA3", "COGN3", "POSI3",
    # Transporte e turismo
    "AZUL4", "GOLL4", "CVCB3",
    # Locação e serviços
    "RENT3", "LCAM3",
]


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
