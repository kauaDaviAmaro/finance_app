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
from app.db.models import Strategy, StrategyCondition, ConditionType, ConditionLogic, PaperTradeStatus
from app.db.database import get_db
from app.core.backtesting.engine import BacktestEngine


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
    
    def _get_indicator_value(self, row: pd.Series, indicator: str) -> Optional[float]:
        """Obtém o valor de um indicador para uma linha específica."""
        indicator_map = {
            'RSI': 'RSI_14',
            'MACD': 'MACD_12_26_9',
            'MACD_SIGNAL': 'MACDs_12_26_9',
            'MACD_HISTOGRAM': 'MACDh_12_26_9',
            'STOCHASTIC_K': 'STOCHk_14_3_3',
            'STOCHASTIC_D': 'STOCHd_14_3_3',
            'ATR': 'ATRr_14',
            'BB_UPPER': 'BBU_20_2.0',
            'BB_MIDDLE': 'BBM_20_2.0',
            'BB_LOWER': 'BBL_20_2.0',
            'OBV': 'OBV',
            'CLOSE': 'close',
            'OPEN': 'open',
            'HIGH': 'high',
            'LOW': 'low',
            'VOLUME': 'volume',
            'MM9': 'MM9',
            'MM21': 'MM21',
        }
        
        col_name = indicator_map.get(indicator.upper())
        if not col_name or col_name not in row.index:
            return None
        
        value = row[col_name]
        if pd.isna(value):
            return None
        
        return float(value)
    
    def _evaluate_condition(self, row: pd.Series, condition: StrategyCondition) -> bool:
        """Avalia uma condição individual."""
        indicator_value = self._get_indicator_value(row, condition.indicator)
        
        if indicator_value is None:
            return False
        
        value = float(condition.value) if condition.value else None
        
        operator = condition.operator.upper()
        
        if operator == 'GREATER_THAN':
            return indicator_value > value if value is not None else False
        elif operator == 'LESS_THAN':
            return indicator_value < value if value is not None else False
        elif operator == 'GREATER_EQUAL':
            return indicator_value >= value if value is not None else False
        elif operator == 'LESS_EQUAL':
            return indicator_value <= value if value is not None else False
        elif operator == 'EQUAL':
            return abs(indicator_value - value) < 0.0001 if value is not None else False
        elif operator == 'CROSS_ABOVE':
            idx = row.name
            if idx == 0:
                return False
            prev_value = self._get_indicator_value(self.data.iloc[idx - 1], condition.indicator)
            if prev_value is None or indicator_value is None:
                return False
            return prev_value <= value and indicator_value > value if value is not None else False
        elif operator == 'CROSS_BELOW':
            idx = row.name
            if idx == 0:
                return False
            prev_value = self._get_indicator_value(self.data.iloc[idx - 1], condition.indicator)
            if prev_value is None or indicator_value is None:
                return False
            return prev_value >= value and indicator_value < value if value is not None else False
        elif operator == 'CROSS_ABOVE_INDICATOR':
            if condition.indicator == 'MM9' and 'MM21' in row.index:
                idx = row.name
                if idx == 0:
                    return False
                prev_row = self.data.iloc[idx - 1]
                prev_mm9 = prev_row.get('MM9')
                prev_mm21 = prev_row.get('MM21')
                curr_mm9 = row.get('MM9')
                curr_mm21 = row.get('MM21')
                if pd.isna(prev_mm9) or pd.isna(prev_mm21) or pd.isna(curr_mm9) or pd.isna(curr_mm21):
                    return False
                return prev_mm9 <= prev_mm21 and curr_mm9 > curr_mm21
        elif operator == 'CROSS_BELOW_INDICATOR':
            if condition.indicator == 'MM9' and 'MM21' in row.index:
                idx = row.name
                if idx == 0:
                    return False
                prev_row = self.data.iloc[idx - 1]
                prev_mm9 = prev_row.get('MM9')
                prev_mm21 = prev_row.get('MM21')
                curr_mm9 = row.get('MM9')
                curr_mm21 = row.get('MM21')
                if pd.isna(prev_mm9) or pd.isna(prev_mm21) or pd.isna(curr_mm9) or pd.isna(curr_mm21):
                    return False
                return prev_mm9 >= prev_mm21 and curr_mm9 < curr_mm21
        
        return False
    
    def _evaluate_conditions(self, row: pd.Series, condition_type: ConditionType) -> bool:
        """Avalia todas as condições de um tipo (ENTRY ou EXIT) com lógica AND/OR."""
        conditions = [c for c in self.strategy.conditions if c.condition_type == condition_type]
        
        if not conditions:
            return False
        
        conditions = sorted(conditions, key=lambda x: x.order)
        
        result = self._evaluate_condition(row, conditions[0])
        
        for i in range(1, len(conditions)):
            condition = conditions[i]
            condition_result = self._evaluate_condition(row, condition)
            
            if condition.logic == ConditionLogic.AND:
                result = result and condition_result
            else:
                result = result or condition_result
        
        return result
    
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
        entry_signal = False
        exit_signal = False
        
        if not self.positions:
            entry_signal = self._evaluate_conditions(last_row, ConditionType.ENTRY)
        else:
            exit_signal = self._evaluate_conditions(last_row, ConditionType.EXIT)
        
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

