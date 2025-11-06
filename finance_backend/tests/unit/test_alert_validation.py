"""
Unit tests for alert validation logic.
"""
import pytest
from fastapi import HTTPException

from app.routers.alert import validate_alert_data, VALID_INDICATORS, VALID_CONDITIONS


class TestAlertValidation:
    """Tests for alert validation functions."""
    
    def test_validate_alert_data_valid_macd_cross_above(self):
        """Test validation with valid MACD CROSS_ABOVE."""
        # Should not raise exception
        validate_alert_data("MACD", "CROSS_ABOVE", None)
    
    def test_validate_alert_data_valid_rsi_greater_than(self):
        """Test validation with valid RSI GREATER_THAN."""
        # Should not raise exception
        validate_alert_data("RSI", "GREATER_THAN", 70.0)
    
    def test_validate_alert_data_valid_stochastic_cross_below(self):
        """Test validation with valid STOCHASTIC CROSS_BELOW."""
        # Should not raise exception
        validate_alert_data("STOCHASTIC", "CROSS_BELOW", None)
    
    def test_validate_alert_data_valid_bbands_cross_above(self):
        """Test validation with valid BBANDS CROSS_ABOVE."""
        # Should not raise exception
        validate_alert_data("BBANDS", "CROSS_ABOVE", None)
    
    def test_validate_alert_data_case_insensitive_indicator(self):
        """Test that indicator validation is case insensitive."""
        # Should not raise exception
        validate_alert_data("macd", "CROSS_ABOVE", None)
        validate_alert_data("Rsi", "GREATER_THAN", 70.0)
        validate_alert_data("stochastic", "CROSS_BELOW", None)
        validate_alert_data("bbands", "CROSS_ABOVE", None)
    
    def test_validate_alert_data_case_insensitive_condition(self):
        """Test that condition validation is case insensitive."""
        # Should not raise exception
        validate_alert_data("MACD", "cross_above", None)
        validate_alert_data("RSI", "greater_than", 70.0)
        validate_alert_data("RSI", "LESS_THAN", 30.0)
    
    def test_validate_alert_data_invalid_indicator(self):
        """Test validation with invalid indicator type."""
        with pytest.raises(HTTPException) as exc_info:
            validate_alert_data("INVALID", "CROSS_ABOVE", None)
        
        assert exc_info.value.status_code == 400
        assert "Tipo de indicador inválido" in str(exc_info.value.detail)
    
    def test_validate_alert_data_invalid_condition(self):
        """Test validation with invalid condition."""
        with pytest.raises(HTTPException) as exc_info:
            validate_alert_data("MACD", "INVALID", None)
        
        assert exc_info.value.status_code == 400
        assert "Condição inválida" in str(exc_info.value.detail)
    
    def test_validate_alert_data_greater_than_requires_threshold(self):
        """Test that GREATER_THAN requires threshold_value."""
        with pytest.raises(HTTPException) as exc_info:
            validate_alert_data("RSI", "GREATER_THAN", None)
        
        assert exc_info.value.status_code == 400
        assert "threshold_value é obrigatório" in str(exc_info.value.detail)
    
    def test_validate_alert_data_less_than_requires_threshold(self):
        """Test that LESS_THAN requires threshold_value."""
        with pytest.raises(HTTPException) as exc_info:
            validate_alert_data("RSI", "LESS_THAN", None)
        
        assert exc_info.value.status_code == 400
        assert "threshold_value é obrigatório" in str(exc_info.value.detail)
    
    def test_validate_alert_data_cross_above_no_threshold(self):
        """Test that CROSS_ABOVE doesn't require threshold."""
        # Should not raise exception
        validate_alert_data("MACD", "CROSS_ABOVE", None)
        validate_alert_data("MACD", "CROSS_ABOVE", 0)  # Even if provided, should work
    
    def test_validate_alert_data_cross_below_no_threshold(self):
        """Test that CROSS_BELOW doesn't require threshold."""
        # Should not raise exception
        validate_alert_data("MACD", "CROSS_BELOW", None)
    
    def test_validate_alert_data_valid_threshold_values(self):
        """Test validation with various valid threshold values."""
        # Should not raise exception for any numeric value
        validate_alert_data("RSI", "GREATER_THAN", 70.0)
        validate_alert_data("RSI", "GREATER_THAN", 70)
        validate_alert_data("RSI", "LESS_THAN", 30.5)
    
    def test_valid_indicators_list(self):
        """Test that VALID_INDICATORS contains expected values."""
        assert "MACD" in VALID_INDICATORS
        assert "RSI" in VALID_INDICATORS
        assert "STOCHASTIC" in VALID_INDICATORS
        assert "BBANDS" in VALID_INDICATORS
        assert len(VALID_INDICATORS) == 4
    
    def test_valid_conditions_list(self):
        """Test that VALID_CONDITIONS contains expected values."""
        assert "CROSS_ABOVE" in VALID_CONDITIONS
        assert "CROSS_BELOW" in VALID_CONDITIONS
        assert "GREATER_THAN" in VALID_CONDITIONS
        assert "LESS_THAN" in VALID_CONDITIONS
        assert len(VALID_CONDITIONS) == 4
    
    def test_validate_all_indicator_condition_combinations(self):
        """Test all valid combinations of indicators and conditions."""
        valid_combinations = [
            ("MACD", "CROSS_ABOVE", None),
            ("MACD", "CROSS_BELOW", None),
            ("RSI", "GREATER_THAN", 70.0),
            ("RSI", "LESS_THAN", 30.0),
            ("STOCHASTIC", "CROSS_ABOVE", None),
            ("STOCHASTIC", "CROSS_BELOW", None),
            ("BBANDS", "CROSS_ABOVE", None),
            ("BBANDS", "CROSS_BELOW", None),
        ]
        
        for indicator, condition, threshold in valid_combinations:
            # Should not raise exception
            validate_alert_data(indicator, condition, threshold)

