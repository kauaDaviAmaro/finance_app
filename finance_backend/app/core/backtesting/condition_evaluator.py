"""
Avaliação de condições de estratégias para backtesting.
"""
import pandas as pd
from typing import Optional
from app.db.models import StrategyCondition, ConditionType, ConditionLogic


class ConditionEvaluator:
    """Avalia condições de estratégias sobre dados históricos."""
    
    def __init__(self, strategy, data: pd.DataFrame):
        self.strategy = strategy
        self.data = data
    
    def get_indicator_value(self, row: pd.Series, indicator: str) -> Optional[float]:
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
    
    def evaluate_condition(self, row: pd.Series, condition: StrategyCondition) -> bool:
        """Avalia uma condição individual."""
        indicator_value = self.get_indicator_value(row, condition.indicator)
        
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
            prev_value = self.get_indicator_value(self.data.iloc[idx - 1], condition.indicator)
            if prev_value is None or indicator_value is None:
                return False
            return prev_value <= value and indicator_value > value if value is not None else False
        elif operator == 'CROSS_BELOW':
            idx = row.name
            if idx == 0:
                return False
            prev_value = self.get_indicator_value(self.data.iloc[idx - 1], condition.indicator)
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
    
    def evaluate_conditions(self, row: pd.Series, condition_type: ConditionType) -> bool:
        """Avalia todas as condições de um tipo (ENTRY ou EXIT) com lógica AND/OR."""
        conditions = [c for c in self.strategy.conditions if c.condition_type == condition_type]
        
        if not conditions:
            return False
        
        # Ordenar por ordem
        conditions = sorted(conditions, key=lambda x: x.order)
        
        # Avaliar primeira condição
        result = self.evaluate_condition(row, conditions[0])
        
        # Avaliar condições restantes com lógica
        for i in range(1, len(conditions)):
            condition = conditions[i]
            condition_result = self.evaluate_condition(row, condition)
            
            if condition.logic == ConditionLogic.AND:
                result = result and condition_result
            else:  # OR
                result = result or condition_result
        
        return result

