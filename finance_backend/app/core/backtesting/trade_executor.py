"""
Execução de trades para backtesting.
"""
from typing import Dict, List, Optional, Any
import pandas as pd


class TradeExecutor:
    """Executa trades de compra e venda durante backtesting."""
    
    def __init__(self, strategy, initial_capital: float):
        self.strategy = strategy
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.positions: List[Dict[str, Any]] = []
        self.trades: List[Dict[str, Any]] = []
    
    def calculate_position_size(self, price: float) -> int:
        """Calcula o tamanho da posição baseado no capital e position_size."""
        position_percent = float(self.strategy.position_size) / 100.0
        capital_to_use = self.capital * position_percent
        quantity = int(capital_to_use / price)
        return max(1, quantity)  # Mínimo 1 ação
    
    def execute_buy(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """Executa uma ordem de compra."""
        price = float(row['close'])
        quantity = self.calculate_position_size(price)
        cost = price * quantity
        
        if cost > self.capital:
            return None  # Sem capital suficiente
        
        self.capital -= cost
        
        position = {
            'entry_date': row['date'],
            'entry_price': price,
            'quantity': quantity,
            'cost': cost
        }
        
        self.positions.append(position)
        
        trade = {
            'date': row['date'],
            'type': 'BUY',
            'price': price,
            'quantity': quantity,
            'pnl': None,
            'capital_after': self.capital
        }
        
        self.trades.append(trade)
        return trade
    
    def execute_sell(self, row: pd.Series, position: Dict[str, Any]) -> Dict[str, Any]:
        """Executa uma ordem de venda."""
        price = float(row['close'])
        quantity = position['quantity']
        revenue = price * quantity
        cost = position['entry_price'] * quantity
        pnl = revenue - cost
        
        self.capital += revenue
        
        trade = {
            'date': row['date'],
            'type': 'SELL',
            'price': price,
            'quantity': quantity,
            'pnl': pnl,
            'capital_after': self.capital
        }
        
        self.trades.append(trade)
        return trade
    
    def close_all_positions(self, row: pd.Series) -> List[Dict[str, Any]]:
        """Fecha todas as posições abertas."""
        trades = []
        for position in self.positions[:]:
            trade = self.execute_sell(row, position)
            trades.append(trade)
            self.positions.remove(position)
        return trades

