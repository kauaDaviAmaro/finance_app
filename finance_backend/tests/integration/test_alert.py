"""
Integration tests for alert endpoints.
"""
import pytest
from decimal import Decimal
from fastapi import status


class TestCreateAlert:
    """Tests for POST /alerts endpoint."""
    
    def test_create_alert_success(self, client, auth_headers, test_user, db):
        """Test successfully creating an alert."""
        payload = {
            "ticker": "PETR4",
            "indicator_type": "RSI",
            "condition": "GREATER_THAN",
            "threshold_value": "70.0"
        }
        
        response = client.post("/alerts", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["ticker"] == "PETR4"
        assert data["indicator_type"] == "RSI"
        assert data["condition"] == "GREATER_THAN"
        # Decimal pode ser serializado como '70.0' ou '70.0000', então comparamos como float
        assert abs(float(data["threshold_value"]) - 70.0) < 0.001
        assert data["is_active"] is True
        # user_id não está no schema de resposta
    
    def test_create_alert_cross_above(self, client, auth_headers, test_user, db):
        """Test creating alert with CROSS_ABOVE condition (no threshold)."""
        payload = {
            "ticker": "PETR4",
            "indicator_type": "MACD",
            "condition": "CROSS_ABOVE",
            "threshold_value": None
        }
        
        response = client.post("/alerts", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["condition"] == "CROSS_ABOVE"
        assert data["threshold_value"] is None
    
    def test_create_alert_case_insensitive(self, client, auth_headers, test_user, db):
        """Test that ticker, indicator, and condition are converted to uppercase."""
        payload = {
            "ticker": "petr4",
            "indicator_type": "rsi",
            "condition": "greater_than",
            "threshold_value": "70.0"
        }
        
        response = client.post("/alerts", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["ticker"] == "PETR4"
        assert data["indicator_type"] == "RSI"
        assert data["condition"] == "GREATER_THAN"
    
    def test_create_alert_invalid_indicator(self, client, auth_headers, test_user):
        """Test creating alert with invalid indicator type."""
        payload = {
            "ticker": "PETR4",
            "indicator_type": "INVALID",
            "condition": "GREATER_THAN",
            "threshold_value": "70.0"
        }
        
        response = client.post("/alerts", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Tipo de indicador inválido" in response.json()["detail"]
    
    def test_create_alert_invalid_condition(self, client, auth_headers, test_user):
        """Test creating alert with invalid condition."""
        payload = {
            "ticker": "PETR4",
            "indicator_type": "RSI",
            "condition": "INVALID",
            "threshold_value": "70.0"
        }
        
        response = client.post("/alerts", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Condição inválida" in response.json()["detail"]
    
    def test_create_alert_missing_threshold(self, client, auth_headers, test_user):
        """Test creating alert without threshold for GREATER_THAN."""
        payload = {
            "ticker": "PETR4",
            "indicator_type": "RSI",
            "condition": "GREATER_THAN",
            "threshold_value": None
        }
        
        response = client.post("/alerts", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "threshold_value é obrigatório" in response.json()["detail"]
    
    def test_create_alert_unauthorized(self, client):
        """Test creating alert without authentication."""
        payload = {
            "ticker": "PETR4",
            "indicator_type": "RSI",
            "condition": "GREATER_THAN",
            "threshold_value": "70.0"
        }
        
        response = client.post("/alerts", json=payload)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetAlerts:
    """Tests for GET /alerts endpoint."""
    
    def test_get_alerts_success(self, client, auth_headers, test_user, db):
        """Test getting user's alerts."""
        from app.db.models import Alert
        
        # Add alerts
        alert1 = Alert(
            user_id=test_user.id,
            ticker="PETR4",
            indicator_type="RSI",
            condition="GREATER_THAN",
            threshold_value=Decimal("70.0")
        )
        alert2 = Alert(
            user_id=test_user.id,
            ticker="VALE3",
            indicator_type="MACD",
            condition="CROSS_ABOVE"
        )
        db.add(alert1)
        db.add(alert2)
        db.commit()
        
        response = client.get("/alerts", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["alerts"]) == 2
    
    def test_get_alerts_empty(self, client, auth_headers, test_user):
        """Test getting empty alerts list."""
        response = client.get("/alerts", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["alerts"]) == 0
    
    def test_get_alerts_unauthorized(self, client):
        """Test getting alerts without authentication."""
        response = client.get("/alerts")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_alerts_user_isolation(self, client, auth_headers, test_user, db):
        """Test that users only see their own alerts."""
        from app.db.models import User, Alert
        from app.core.security import hash_password
        
        # Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=hash_password("password123")
        )
        db.add(other_user)
        db.commit()
        
        # Add alerts for both users
        alert1 = Alert(
            user_id=test_user.id,
            ticker="PETR4",
            indicator_type="RSI",
            condition="GREATER_THAN",
            threshold_value=Decimal("70.0")
        )
        alert2 = Alert(
            user_id=other_user.id,
            ticker="VALE3",
            indicator_type="MACD",
            condition="CROSS_ABOVE"
        )
        db.add(alert1)
        db.add(alert2)
        db.commit()
        
        # Current user should only see their alerts
        response = client.get("/alerts", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["alerts"]) == 1
        assert data["alerts"][0]["ticker"] == "PETR4"


class TestGetAlert:
    """Tests for GET /alerts/{alert_id} endpoint."""
    
    def test_get_alert_success(self, client, auth_headers, test_user, db):
        """Test getting a specific alert."""
        from app.db.models import Alert
        
        alert = Alert(
            user_id=test_user.id,
            ticker="PETR4",
            indicator_type="RSI",
            condition="GREATER_THAN",
            threshold_value=Decimal("70.0")
        )
        db.add(alert)
        db.commit()
        
        response = client.get(f"/alerts/{alert.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == alert.id
        assert data["ticker"] == "PETR4"
    
    def test_get_alert_not_found(self, client, auth_headers, test_user):
        """Test getting non-existent alert."""
        response = client.get("/alerts/99999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Alerta não encontrado" in response.json()["detail"]
    
    def test_get_alert_unauthorized(self, client):
        """Test getting alert without authentication."""
        response = client.get("/alerts/1")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_alert_user_isolation(self, client, auth_headers, test_user, db):
        """Test that users can only see their own alerts."""
        from app.db.models import User, Alert
        from app.core.security import hash_password
        
        # Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=hash_password("password123")
        )
        db.add(other_user)
        db.commit()
        
        # Add alert for other user
        alert = Alert(
            user_id=other_user.id,
            ticker="VALE3",
            indicator_type="MACD",
            condition="CROSS_ABOVE"
        )
        db.add(alert)
        db.commit()
        
        # Current user tries to access other user's alert
        response = client.get(f"/alerts/{alert.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestToggleAlert:
    """Tests for PATCH /alerts/{alert_id}/toggle endpoint."""
    
    def test_toggle_alert_success(self, client, auth_headers, test_user, db):
        """Test successfully toggling alert active status."""
        from app.db.models import Alert
        
        alert = Alert(
            user_id=test_user.id,
            ticker="PETR4",
            indicator_type="RSI",
            condition="GREATER_THAN",
            threshold_value=Decimal("70.0"),
            is_active=True
        )
        db.add(alert)
        db.commit()
        original_active = alert.is_active
        
        response = client.patch(f"/alerts/{alert.id}/toggle", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] != original_active
        
        # Toggle again
        response = client.patch(f"/alerts/{alert.id}/toggle", headers=auth_headers)
        data = response.json()
        assert data["is_active"] == original_active
    
    def test_toggle_alert_not_found(self, client, auth_headers, test_user):
        """Test toggling non-existent alert."""
        response = client.patch("/alerts/99999/toggle", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_toggle_alert_unauthorized(self, client):
        """Test toggling alert without authentication."""
        response = client.patch("/alerts/1/toggle")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteAlert:
    """Tests for DELETE /alerts/{alert_id} endpoint."""
    
    def test_delete_alert_success(self, client, auth_headers, test_user, db):
        """Test successfully deleting an alert."""
        from app.db.models import Alert
        
        alert = Alert(
            user_id=test_user.id,
            ticker="PETR4",
            indicator_type="RSI",
            condition="GREATER_THAN",
            threshold_value=Decimal("70.0")
        )
        db.add(alert)
        db.commit()
        alert_id = alert.id
        
        response = client.delete(f"/alerts/{alert_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify alert was deleted
        deleted = db.query(Alert).filter(Alert.id == alert_id).first()
        assert deleted is None
    
    def test_delete_alert_not_found(self, client, auth_headers, test_user):
        """Test deleting non-existent alert."""
        response = client.delete("/alerts/99999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_alert_unauthorized(self, client):
        """Test deleting alert without authentication."""
        response = client.delete("/alerts/1")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

