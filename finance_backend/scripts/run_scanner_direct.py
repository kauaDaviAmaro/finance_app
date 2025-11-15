"""
Script para executar manualmente o scan completo do mercado.
Versão que executa a lógica diretamente sem depender do Celery.
"""
import sys
import os

# Adicionar o diretório raiz ao path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Importar diretamente os módulos sem passar pelo __init__.py
import importlib.util

# Adicionar o diretório app ao sys.modules para evitar imports relativos problemáticos
sys.modules['app'] = type(sys)('app')
sys.modules['app.core'] = type(sys)('app.core')
sys.modules['app.core.market'] = type(sys)('app.core.market')

# Carregar ticker_utils diretamente
ticker_utils_path = os.path.join(backend_dir, 'app', 'core', 'market', 'ticker_utils.py')
spec = importlib.util.spec_from_file_location("app.core.market.ticker_utils", ticker_utils_path)
ticker_utils = importlib.util.module_from_spec(spec)
sys.modules['app.core.market.ticker_utils'] = ticker_utils
spec.loader.exec_module(ticker_utils)
get_all_b3_tickers = ticker_utils.get_all_b3_tickers

# Carregar technical_analysis diretamente (agora pode importar ticker_utils sem problemas)
tech_analysis_path = os.path.join(backend_dir, 'app', 'core', 'market', 'technical_analysis.py')
spec = importlib.util.spec_from_file_location("app.core.market.technical_analysis", tech_analysis_path)
technical_analysis = importlib.util.module_from_spec(spec)
sys.modules['app.core.market.technical_analysis'] = technical_analysis
spec.loader.exec_module(technical_analysis)
get_scanner_indicators = technical_analysis.get_scanner_indicators

# Importar database
from app.db.database import SessionLocal, engine
from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import logging
import time

# Definir Base localmente para evitar imports circulares
Base = declarative_base()

# Definir ScannerData localmente
class ScannerData(Base):
    __tablename__ = "scanner_data"
    
    ticker = Column(String(20), primary_key=True, index=True)
    rsi_14 = Column(Numeric(9, 4), nullable=True)
    macd_signal = Column(Numeric(9, 4), nullable=True)
    mm_9_cruza_mm_21 = Column(String(20), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_scanner():
    """Executa o scan completo do mercado B3."""
    logger.info("Iniciando scan completo do mercado B3...")

    db = SessionLocal()
    
    try:
        # Garantir que as tabelas existem
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Tabelas verificadas/criadas")
    except Exception as e:
        logger.error(f"Erro ao garantir a criação das tabelas: {e}")
        db.close()
        return None

    try:
        # Ler lista completa de tickers B3 do arquivo estático
        all_tickers = get_all_b3_tickers()
        logger.info(f"Processando {len(all_tickers)} tickers do mercado B3...")
        
        success_count = 0
        error_count = 0
        delay_between_requests = 0.5  # Delay para evitar rate limiting do yfinance
        
        for idx, ticker in enumerate(all_tickers, 1):
            try:
                # Calcular indicadores técnicos
                indicators = get_scanner_indicators(ticker)
                
                # Fazer UPSERT na tabela scanner_data
                scanner_data = db.query(ScannerData).filter(ScannerData.ticker == ticker).first()
                
                if scanner_data:
                    # UPDATE
                    scanner_data.rsi_14 = indicators['rsi_14']
                    scanner_data.macd_signal = indicators['macd_signal']
                    scanner_data.mm_9_cruza_mm_21 = indicators['mm_9_cruza_mm_21']
                    # last_updated é atualizado automaticamente pelo onupdate
                else:
                    # INSERT
                    scanner_data = ScannerData(
                        ticker=ticker,
                        rsi_14=indicators['rsi_14'],
                        macd_signal=indicators['macd_signal'],
                        mm_9_cruza_mm_21=indicators['mm_9_cruza_mm_21']
                    )
                    db.add(scanner_data)
                
                success_count += 1
                
                # Log de progresso a cada 50 tickers
                if idx % 50 == 0:
                    logger.info(f"Progresso: {idx}/{len(all_tickers)} tickers processados ({success_count} sucesso, {error_count} erros)")
                    db.commit()  # Commit periódico para não perder dados
                
                # Delay entre requisições para evitar rate limiting
                time.sleep(delay_between_requests)
                
            except Exception as e:
                error_count += 1
                logger.warning(f"Erro ao processar ticker {ticker}: {e}")
                # Continuar processamento mesmo se um ticker falhar
                continue
        
        # Commit final
        db.commit()
        
        logger.info(
            f"Scan completo concluído! "
            f"Total: {len(all_tickers)}, Sucesso: {success_count}, Erros: {error_count}"
        )
        
        return f"Scan completo concluído. {success_count}/{len(all_tickers)} tickers processados com sucesso."

    except Exception as e:
        logger.error(f"Erro crítico no scan completo do mercado: {e}", exc_info=True)
        db.rollback()
        raise
        
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Executando scan completo do mercado manualmente...")
    logger.info("=" * 60)
    
    try:
        result = run_scanner()
        logger.info("=" * 60)
        logger.info("✓ Scan completo executado com sucesso!")
        logger.info(f"Resultado: {result}")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ Erro ao executar scan: {e}")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

