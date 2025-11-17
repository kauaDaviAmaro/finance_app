"""
Engine de backtesting para executar estratégias sobre dados históricos.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import date

from app.core.market.technical_analysis import (
    get_technical_analysis,
    calculate_moving_averages
)
from app.db.models import Strategy, ConditionType
from app.core.backtesting.condition_evaluator import ConditionEvaluator
from app.core.backtesting.trade_executor import TradeExecutor
from app.core.backtesting.metrics_calculator import MetricsCalculator


class BacktestEngine:
    """Engine para executar backtests de estratégias."""
    
    def __init__(self, strategy: Strategy, ticker: str, period: str = "1y"):
        self.strategy = strategy
        self.ticker = ticker
        self.period = period
        self.data: Optional[pd.DataFrame] = None
        self.initial_capital = float(strategy.initial_capital)
        self.equity_curve: List[Dict[str, Any]] = []
        
        # Componentes separados
        self.trade_executor: Optional[TradeExecutor] = None
        self.condition_evaluator: Optional[ConditionEvaluator] = None
        
    def _load_data(self) -> pd.DataFrame:
        """Carrega dados históricos e calcula indicadores técnicos."""
        # Buscar dados técnicos que já incluem indicadores
        technical_data = get_technical_analysis(self.ticker, self.period)
        
        if not technical_data:
            raise ValueError(f"Nenhum dado encontrado para o ticker {self.ticker}")
        
        # Converter para DataFrame
        df = pd.DataFrame(technical_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # Calcular médias móveis
        df = calculate_moving_averages(df)
        
        # Converter valores None para NaN
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].replace('None', np.nan)
        
        return df
    
    
    def run(self) -> Dict[str, Any]:
        """Executa o backtest completo."""
        # Carregar dados
        self.data = self._load_data()
        
        if self.data is None or self.data.empty:
            raise ValueError("Dados históricos vazios")
        
        # Resetar estado
        self.equity_curve = []
        
        # Inicializar componentes
        self.trade_executor = TradeExecutor(self.strategy, self.initial_capital)
        self.condition_evaluator = ConditionEvaluator(self.strategy, self.data)
        
        # Iterar sobre cada linha de dados
        for idx, row in self.data.iterrows():
            # Verificar condições de saída primeiro (para fechar posições abertas)
            if self.trade_executor.positions:
                exit_signal = self.condition_evaluator.evaluate_conditions(row, ConditionType.EXIT)
                if exit_signal:
                    self.trade_executor.close_all_positions(row)
            
            # Verificar condições de entrada
            if not self.trade_executor.positions:  # Só entra se não tiver posição aberta
                entry_signal = self.condition_evaluator.evaluate_conditions(row, ConditionType.ENTRY)
                if entry_signal:
                    self.trade_executor.execute_buy(row)
            
            # Registrar equity curve
            current_equity = self.trade_executor.capital
            for pos in self.trade_executor.positions:
                current_equity += pos['quantity'] * float(row['close'])
            
            self.equity_curve.append({
                'date': row['date'],
                'equity': current_equity
            })
        
        # Fechar posições abertas no final
        if self.trade_executor.positions and self.data is not None and len(self.data) > 0:
            last_row = self.data.iloc[-1]
            self.trade_executor.close_all_positions(last_row)
        
        # Calcular métricas
        metrics_calculator = MetricsCalculator(
            self.initial_capital,
            self.trade_executor.trades,
            self.trade_executor.positions,
            self.data
        )
        metrics = metrics_calculator.calculate_metrics()
        
        # Preparar resultado
        result = {
            'metrics': metrics,
            'trades': self.trade_executor.trades,
            'equity_curve': self.equity_curve,
            'start_date': self.data.iloc[0]['date'].date() if self.data is not None and len(self.data) > 0 else None,
            'end_date': self.data.iloc[-1]['date'].date() if self.data is not None and len(self.data) > 0 else None
        }
        
        return result

