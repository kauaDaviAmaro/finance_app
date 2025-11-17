"""
Análise de risco de posições individuais.
"""
import numpy as np
from typing import Dict, List, Any
from decimal import Decimal

from .var_calculator import calculate_var
from .beta_calculator import calculate_portfolio_beta
from .volatility_calculator import calculate_volatility
from .utils import get_historical_returns_df
from app.core.market.technical_analysis import get_technical_analysis


def suggest_stop_loss_take_profit(
    ticker: str,
    current_price: float,
    method: str = "atr"
) -> Dict[str, Any]:
    """
    Sugere níveis de stop loss e take profit.
    
    Args:
        ticker: Ticker do ativo
        current_price: Preço atual
        method: Método ('atr', 'percentage', ou 'both')
    
    Returns:
        Dict com 'stop_loss', 'take_profit', 'stop_loss_percentage', 'take_profit_percentage', 'method'
    """
    suggestions = {
        'stop_loss': None,
        'take_profit': None,
        'stop_loss_percentage': None,
        'take_profit_percentage': None,
        'method': method
    }
    
    try:
        # Buscar análise técnica para obter ATR
        technical_data = get_technical_analysis(ticker, period="3mo")
        
        if technical_data and len(technical_data) > 0:
            # Pegar último ATR
            last_data = technical_data[-1]
            atr = last_data.get('ATRr_14')
            
            if atr and method in ['atr', 'both']:
                # Stop Loss: preço atual - (2 × ATR)
                # Take Profit: preço atual + (3 × ATR)
                stop_loss = current_price - (2 * atr)
                take_profit = current_price + (3 * atr)
                
                suggestions['stop_loss'] = round(max(0, stop_loss), 2)
                suggestions['take_profit'] = round(take_profit, 2)
                suggestions['stop_loss_percentage'] = round(((stop_loss - current_price) / current_price) * 100, 2)
                suggestions['take_profit_percentage'] = round(((take_profit - current_price) / current_price) * 100, 2)
        
        # Método baseado em percentual
        if method in ['percentage', 'both']:
            # Valores padrão: -5% stop loss, +10% take profit
            stop_loss_pct = -5.0
            take_profit_pct = 10.0
            
            # Ajustar baseado em volatilidade se disponível
            returns_df = get_historical_returns_df(ticker, period="3mo")
            if returns_df is not None and len(returns_df) >= 30:
                volatility = np.std(returns_df['returns'].values) * np.sqrt(252) * 100  # Volatilidade anualizada em %
                
                # Ajustar stop loss baseado em volatilidade (mais volátil = stop loss maior)
                if volatility > 30:
                    stop_loss_pct = -7.0
                    take_profit_pct = 15.0
                elif volatility > 20:
                    stop_loss_pct = -6.0
                    take_profit_pct = 12.0
            
            if not suggestions['stop_loss'] or method == 'percentage':
                suggestions['stop_loss'] = round(current_price * (1 + stop_loss_pct / 100), 2)
                suggestions['stop_loss_percentage'] = stop_loss_pct
            
            if not suggestions['take_profit'] or method == 'percentage':
                suggestions['take_profit'] = round(current_price * (1 + take_profit_pct / 100), 2)
                suggestions['take_profit_percentage'] = take_profit_pct
    
    except Exception as e:
        print(f"Erro ao calcular stop loss/take profit para {ticker}: {e}")
        # Valores padrão em caso de erro
        if not suggestions['stop_loss']:
            suggestions['stop_loss'] = round(current_price * 0.95, 2)
            suggestions['stop_loss_percentage'] = -5.0
        if not suggestions['take_profit']:
            suggestions['take_profit'] = round(current_price * 1.10, 2)
            suggestions['take_profit_percentage'] = 10.0
    
    return suggestions


def analyze_position_risk(
    position: Dict[str, Any],
    portfolio_positions: List[Dict[str, Any]],
    benchmark: str = "^BVSP"
) -> Dict[str, Any]:
    """
    Analisa risco de uma posição individual.
    
    Args:
        position: Posição individual com 'ticker', 'quantity', 'purchase_price', 'current_price'
        portfolio_positions: Todas as posições do portfólio (para calcular correlação)
        benchmark: Benchmark para cálculo de beta
    
    Returns:
        Dict com análise completa de risco da posição
    """
    ticker = position.get('ticker')
    current_price = position.get('current_price')
    
    if not ticker or not current_price:
        return {
            'ticker': ticker,
            'error': 'Dados da posição incompletos'
        }
    
    # Calcular VaR individual
    var_result = calculate_var([position], confidence_level=0.95, horizon_days=1)
    
    # Calcular beta individual
    beta_result = calculate_portfolio_beta([position], benchmark=benchmark)
    position_beta = beta_result.get('portfolio_beta')
    
    # Calcular volatilidade individual
    volatility_result = calculate_volatility([position])
    position_volatility = volatility_result.get('portfolio_volatility')
    
    # Calcular correlação com outras posições
    correlations = []
    position_returns_df = get_historical_returns_df(ticker)
    
    if position_returns_df is not None:
        position_returns = position_returns_df['returns'].values
        
        for other_pos in portfolio_positions:
            other_ticker = other_pos.get('ticker')
            if other_ticker == ticker:
                continue
            
            other_returns_df = get_historical_returns_df(other_ticker)
            if other_returns_df is not None:
                other_returns = other_returns_df['returns'].values
                
                # Alinhar tamanhos
                min_len = min(len(position_returns), len(other_returns))
                if min_len >= 30:
                    pos_ret_aligned = position_returns[-min_len:]
                    other_ret_aligned = other_returns[-min_len:]
                    
                    correlation = np.corrcoef(pos_ret_aligned, other_ret_aligned)[0][1]
                    if not np.isnan(correlation):
                        correlations.append({
                            'ticker': other_ticker,
                            'correlation': round(correlation, 4)
                        })
    
    # Calcular contribuição ao risco do portfólio
    portfolio_value = sum(
        Decimal(str(p.get('current_price', 0))) * int(p.get('quantity', 0))
        for p in portfolio_positions
    )
    position_value = Decimal(str(current_price)) * int(position.get('quantity', 0))
    portfolio_weight = float(position_value / portfolio_value) if portfolio_value > 0 else 0.0
    
    # Sugestões de stop loss/take profit
    stop_loss_tp = suggest_stop_loss_take_profit(ticker, float(current_price), method='both')
    
    return {
        'ticker': ticker,
        'var': var_result.get('var_value'),
        'var_percentage': var_result.get('var_percentage'),
        'beta': position_beta,
        'volatility': position_volatility,
        'portfolio_weight': round(portfolio_weight * 100, 2),
        'correlations': sorted(correlations, key=lambda x: abs(x['correlation']), reverse=True)[:5],  # Top 5
        'stop_loss': stop_loss_tp.get('stop_loss'),
        'take_profit': stop_loss_tp.get('take_profit'),
        'stop_loss_percentage': stop_loss_tp.get('stop_loss_percentage'),
        'take_profit_percentage': stop_loss_tp.get('take_profit_percentage')
    }

