"""
Engine de backtesting para executar estratégias sobre dados históricos.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime, date

from app.core.market.data_fetcher import get_historical_data
from app.core.market.technical_analysis import (
    get_technical_analysis,
    calculate_moving_averages,
    detect_moving_average_cross
)
from app.db.models import Strategy, StrategyCondition, ConditionType, ConditionLogic


class BacktestEngine:
    """Engine para executar backtests de estratégias."""
    
    def __init__(self, strategy: Strategy, ticker: str, period: str = "1y"):
        self.strategy = strategy
        self.ticker = ticker
        self.period = period
        self.data: Optional[pd.DataFrame] = None
        self.trades: List[Dict[str, Any]] = []
        self.positions: List[Dict[str, Any]] = []
        self.capital = float(strategy.initial_capital)
        self.initial_capital = float(strategy.initial_capital)
        self.equity_curve: List[Dict[str, Any]] = []
        
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
            # Para cruzamento, precisamos comparar com a linha anterior
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
            # Cruzamento acima de outro indicador (ex: MM9 cruza acima de MM21)
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
        
        # Ordenar por ordem
        conditions = sorted(conditions, key=lambda x: x.order)
        
        # Avaliar primeira condição
        result = self._evaluate_condition(row, conditions[0])
        
        # Avaliar condições restantes com lógica
        for i in range(1, len(conditions)):
            condition = conditions[i]
            condition_result = self._evaluate_condition(row, condition)
            
            if condition.logic == ConditionLogic.AND:
                result = result and condition_result
            else:  # OR
                result = result or condition_result
        
        return result
    
    def _calculate_position_size(self, price: float) -> int:
        """Calcula o tamanho da posição baseado no capital e position_size."""
        position_percent = float(self.strategy.position_size) / 100.0
        capital_to_use = self.capital * position_percent
        quantity = int(capital_to_use / price)
        return max(1, quantity)  # Mínimo 1 ação
    
    def _execute_buy(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """Executa uma ordem de compra."""
        price = float(row['close'])
        quantity = self._calculate_position_size(price)
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
    
    def _execute_sell(self, row: pd.Series, position: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calcula métricas de performance do backtest."""
        if not self.trades:
            return {
                'total_return': 0.0,
                'annualized_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'final_capital': self.initial_capital
            }
        
        # Calcular retorno total
        final_capital = self.capital
        # Adicionar valor das posições abertas
        for pos in self.positions:
            if self.data is not None and len(self.data) > 0:
                last_price = float(self.data.iloc[-1]['close'])
                final_capital += pos['quantity'] * last_price
        
        total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100
        
        # Calcular retorno anualizado
        if self.data is not None and len(self.data) > 0:
            start_date = self.data.iloc[0]['date']
            end_date = self.data.iloc[-1]['date']
            days = (end_date - start_date).days
            years = days / 365.25
            if years > 0:
                annualized_return = ((final_capital / self.initial_capital) ** (1 / years) - 1) * 100
            else:
                annualized_return = total_return
        else:
            annualized_return = total_return
        
        # Calcular P&L dos trades fechados
        closed_trades_pnl = [t['pnl'] for t in self.trades if t['type'] == 'SELL' and t['pnl'] is not None]
        
        if not closed_trades_pnl:
            return {
                'total_return': total_return,
                'annualized_return': annualized_return,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'final_capital': final_capital
            }
        
        # Win rate
        winning_trades = [pnl for pnl in closed_trades_pnl if pnl > 0]
        losing_trades = [pnl for pnl in closed_trades_pnl if pnl < 0]
        total_trades = len(closed_trades_pnl)
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0.0
        
        # Profit factor
        total_wins = sum(winning_trades) if winning_trades else 0
        total_losses = abs(sum(losing_trades)) if losing_trades else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else (total_wins if total_wins > 0 else 0)
        
        # Médias
        avg_win = np.mean(winning_trades) if winning_trades else 0.0
        avg_loss = np.mean(losing_trades) if losing_trades else 0.0
        
        # Sharpe ratio (simplificado)
        if len(closed_trades_pnl) > 1:
            returns = np.array(closed_trades_pnl) / self.initial_capital
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        # Maximum drawdown
        equity_values = [self.initial_capital]
        for trade in self.trades:
            if trade['capital_after'] is not None:
                equity_values.append(trade['capital_after'])
        
        if len(equity_values) > 1:
            equity_series = pd.Series(equity_values)
            running_max = equity_series.expanding().max()
            drawdown = (equity_series - running_max) / running_max * 100
            max_drawdown = abs(drawdown.min()) if not drawdown.empty else 0.0
        else:
            max_drawdown = 0.0
        
        return {
            'total_return': round(total_return, 4),
            'annualized_return': round(annualized_return, 4),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'max_drawdown': round(max_drawdown, 4),
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 4),
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'final_capital': round(final_capital, 2)
        }
    
    def run(self) -> Dict[str, Any]:
        """Executa o backtest completo."""
        # Carregar dados
        self.data = self._load_data()
        
        if self.data is None or self.data.empty:
            raise ValueError("Dados históricos vazios")
        
        # Resetar estado
        self.trades = []
        self.positions = []
        self.capital = self.initial_capital
        self.equity_curve = []
        
        # Iterar sobre cada linha de dados
        for idx, row in self.data.iterrows():
            # Verificar condições de saída primeiro (para fechar posições abertas)
            if self.positions:
                exit_signal = self._evaluate_conditions(row, ConditionType.EXIT)
                if exit_signal:
                    # Fechar todas as posições abertas
                    for position in self.positions[:]:
                        self._execute_sell(row, position)
                        self.positions.remove(position)
            
            # Verificar condições de entrada
            if not self.positions:  # Só entra se não tiver posição aberta
                entry_signal = self._evaluate_conditions(row, ConditionType.ENTRY)
                if entry_signal:
                    self._execute_buy(row)
            
            # Registrar equity curve
            current_equity = self.capital
            for pos in self.positions:
                current_equity += pos['quantity'] * float(row['close'])
            
            self.equity_curve.append({
                'date': row['date'],
                'equity': current_equity
            })
        
        # Fechar posições abertas no final
        if self.positions and self.data is not None and len(self.data) > 0:
            last_row = self.data.iloc[-1]
            for position in self.positions[:]:
                self._execute_sell(last_row, position)
                self.positions.remove(position)
        
        # Calcular métricas
        metrics = self._calculate_metrics()
        
        # Preparar resultado
        result = {
            'metrics': metrics,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'start_date': self.data.iloc[0]['date'].date() if self.data is not None and len(self.data) > 0 else None,
            'end_date': self.data.iloc[-1]['date'].date() if self.data is not None and len(self.data) > 0 else None
        }
        
        return result

