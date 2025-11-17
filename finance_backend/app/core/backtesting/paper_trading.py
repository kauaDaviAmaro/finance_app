"""
Engine de paper trading para simulação de estratégias em tempo real.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

from app.core.market.technical_analysis import (
    get_technical_analysis,
    calculate_moving_averages
)
from app.core.market_service import get_current_price
from app.db.models import Strategy, ConditionType, PaperTradeStatus
from app.db.database import get_db
from app.core.backtesting.condition_evaluator import ConditionEvaluator


class PaperTradingEngine:
    """Engine para executar paper trading em tempo real."""
    
    def __init__(self, strategy: Strategy, ticker: str, db_session):
        self.strategy = strategy
        self.ticker = ticker
        self.db = db_session
        self.data: Optional[pd.DataFrame] = None
        self.positions: List[Dict[str, Any]] = []
        self.capital = float(strategy.initial_capital)
        self.initial_capital = float(strategy.initial_capital)
        
    def _load_latest_data(self, period: str = "3mo") -> pd.DataFrame:
        """Carrega os dados mais recentes para análise."""
        from app.core.market.technical_analysis import get_technical_analysis
        
        technical_data = get_technical_analysis(self.ticker, period)
        
        if not technical_data:
            raise ValueError(f"Nenhum dado encontrado para o ticker {self.ticker}")
        
        df = pd.DataFrame(technical_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        df = calculate_moving_averages(df)
        
        # Converter valores None para NaN
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].replace('None', np.nan)
        
        return df
    
    def _get_condition_evaluator(self) -> ConditionEvaluator:
        """Obtém ou cria o avaliador de condições."""
        if self.data is None:
            self.data = self._load_latest_data()
        return ConditionEvaluator(self.strategy, self.data)
    
    def _calculate_position_size(self, price: float) -> int:
        """Calcula o tamanho da posição baseado no capital e position_size."""
        position_percent = float(self.strategy.position_size) / 100.0
        capital_to_use = self.capital * position_percent
        quantity = int(capital_to_use / price)
        return max(1, quantity)
    
    def check_signals(self) -> Dict[str, Any]:
        """Verifica sinais de entrada/saída com os dados mais recentes."""
        # Carregar dados mais recentes
        self.data = self._load_latest_data()
        
        if self.data is None or self.data.empty:
            return {'entry_signal': False, 'exit_signal': False, 'error': 'No data available'}
        
        # Pegar última linha (dados mais recentes)
        last_row = self.data.iloc[-1]
        
        # Verificar sinais
        evaluator = self._get_condition_evaluator()
        entry_signal = False
        exit_signal = False
        
        if not self.positions:
            entry_signal = evaluator.evaluate_conditions(last_row, ConditionType.ENTRY)
        else:
            exit_signal = evaluator.evaluate_conditions(last_row, ConditionType.EXIT)
        
        return {
            'entry_signal': entry_signal,
            'exit_signal': exit_signal,
            'current_price': float(last_row['close']),
            'timestamp': datetime.now()
        }
    
    def execute_entry(self, price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Executa uma ordem de entrada."""
        if self.positions:
            return None  # Já tem posição aberta
        
        if price is None:
            # Buscar preço atual
            current_price = get_current_price(self.ticker, self.db)
            if current_price is None:
                return None
            price = float(current_price)
        
        quantity = self._calculate_position_size(price)
        cost = price * quantity
        
        if cost > self.capital:
            return None  # Sem capital suficiente
        
        self.capital -= cost
        
        position = {
            'entry_date': datetime.now(),
            'entry_price': price,
            'quantity': quantity,
            'cost': cost
        }
        
        self.positions.append(position)
        
        return {
            'type': 'BUY',
            'price': price,
            'quantity': quantity,
            'cost': cost,
            'capital_after': self.capital,
            'timestamp': datetime.now()
        }
    
    def execute_exit(self, price: Optional[float] = None) -> List[Dict[str, Any]]:
        """Executa ordens de saída para todas as posições abertas."""
        if not self.positions:
            return []
        
        if price is None:
            current_price = get_current_price(self.ticker, self.db)
            if current_price is None:
                return []
            price = float(current_price)
        
        trades = []
        
        for position in self.positions[:]:
            quantity = position['quantity']
            revenue = price * quantity
            cost = position['entry_price'] * quantity
            pnl = revenue - cost
            
            self.capital += revenue
            
            trade = {
                'type': 'SELL',
                'price': price,
                'quantity': quantity,
                'pnl': pnl,
                'capital_after': self.capital,
                'timestamp': datetime.now()
            }
            
            trades.append(trade)
            self.positions.remove(position)
        
        return trades
    
    def get_current_equity(self) -> float:
        """Calcula o equity atual (capital + valor das posições abertas)."""
        equity = self.capital
        
        if self.positions:
            current_price = get_current_price(self.ticker, self.db)
            if current_price:
                for pos in self.positions:
                    equity += pos['quantity'] * float(current_price)
        
        return equity
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calcula métricas de performance atuais."""
        current_equity = self.get_current_equity()
        total_return = ((current_equity - self.initial_capital) / self.initial_capital) * 100
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.capital,
            'current_equity': current_equity,
            'total_return': round(total_return, 4),
            'open_positions': len(self.positions),
            'positions_value': sum(p['quantity'] * get_current_price(self.ticker, self.db) 
                                 for p in self.positions) if self.positions and get_current_price(self.ticker, self.db) else 0
        }

