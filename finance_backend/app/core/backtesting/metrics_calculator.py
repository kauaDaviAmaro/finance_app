"""
Cálculo de métricas de performance para backtesting.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any


class MetricsCalculator:
    """Calcula métricas de performance de backtests."""
    
    def __init__(self, initial_capital: float, trades: List[Dict[str, Any]], 
                 positions: List[Dict[str, Any]], data: pd.DataFrame):
        self.initial_capital = initial_capital
        self.trades = trades
        self.positions = positions
        self.data = data
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calcula métricas de performance do backtest."""
        if not self.trades:
            return self._get_empty_metrics()
        
        # Calcular retorno total
        final_capital = self._calculate_final_capital()
        total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100
        
        # Calcular retorno anualizado
        annualized_return = self._calculate_annualized_return(final_capital, total_return)
        
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
        
        # Calcular métricas de trades
        trade_metrics = self._calculate_trade_metrics(closed_trades_pnl)
        
        # Sharpe ratio
        sharpe_ratio = self._calculate_sharpe_ratio(closed_trades_pnl)
        
        # Maximum drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        return {
            'total_return': round(total_return, 4),
            'annualized_return': round(annualized_return, 4),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'max_drawdown': round(max_drawdown, 4),
            'win_rate': round(trade_metrics['win_rate'], 2),
            'profit_factor': round(trade_metrics['profit_factor'], 4),
            'total_trades': trade_metrics['total_trades'],
            'winning_trades': trade_metrics['winning_trades'],
            'losing_trades': trade_metrics['losing_trades'],
            'avg_win': round(trade_metrics['avg_win'], 2),
            'avg_loss': round(trade_metrics['avg_loss'], 2),
            'final_capital': round(final_capital, 2)
        }
    
    def _get_empty_metrics(self) -> Dict[str, Any]:
        """Retorna métricas vazias quando não há trades."""
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
    
    def _calculate_final_capital(self) -> float:
        """Calcula o capital final incluindo posições abertas."""
        final_capital = sum(
            t['capital_after'] for t in self.trades 
            if t['capital_after'] is not None
        )
        
        if not final_capital:
            final_capital = self.initial_capital
        
        # Adicionar valor das posições abertas
        if self.positions and self.data is not None and len(self.data) > 0:
            last_price = float(self.data.iloc[-1]['close'])
            for pos in self.positions:
                final_capital += pos['quantity'] * last_price
        
        return final_capital
    
    def _calculate_annualized_return(self, final_capital: float, total_return: float) -> float:
        """Calcula o retorno anualizado."""
        if self.data is None or len(self.data) == 0:
            return total_return
        
        start_date = self.data.iloc[0]['date']
        end_date = self.data.iloc[-1]['date']
        days = (end_date - start_date).days
        years = days / 365.25
        
        if years > 0:
            annualized_return = ((final_capital / self.initial_capital) ** (1 / years) - 1) * 100
        else:
            annualized_return = total_return
        
        return annualized_return
    
    def _calculate_trade_metrics(self, closed_trades_pnl: List[float]) -> Dict[str, Any]:
        """Calcula métricas relacionadas aos trades."""
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
        
        return {
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'avg_win': avg_win,
            'avg_loss': avg_loss
        }
    
    def _calculate_sharpe_ratio(self, closed_trades_pnl: List[float]) -> float:
        """Calcula o Sharpe ratio (simplificado)."""
        if len(closed_trades_pnl) > 1:
            returns = np.array(closed_trades_pnl) / self.initial_capital
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        return sharpe_ratio
    
    def _calculate_max_drawdown(self) -> float:
        """Calcula o maximum drawdown."""
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
        
        return max_drawdown

