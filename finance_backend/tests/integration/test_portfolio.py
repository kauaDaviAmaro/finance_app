"""
Integration tests for portfolio endpoints.
"""
import pytest
from unittest.mock import patch
from datetime import date
from decimal import Decimal
from fastapi import status


class TestAddPortfolioItem:
    """Tests for POST /portfolio endpoint."""
    
    @patch('app.routers.portfolio.get_current_price')
    def test_add_portfolio_item_success(self, mock_get_price, client, auth_headers, test_user, db):
        """Test successfully adding a portfolio item."""
        mock_get_price.return_value = 25.50
        
        payload = {
            "ticker": "PETR4",
            "quantity": 100,
            "purchase_price": "20.00",
            "purchase_date": "2023-01-01"
        }
        
        response = client.post("/portfolio", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["ticker"] == "PETR4"
        assert data["quantity"] == 100
        assert data["purchase_price"] == "20.00"
        # user_id não está no schema de resposta (PortfolioItemOut)
        # Verificar que o preço atual foi retornado (pode ter pequenas diferenças de precisão)
        assert data["current_price"] is not None
        assert abs(float(data["current_price"]) - 25.50) < 0.1  # Tolerância para diferenças de precisão
        assert data["unrealized_pnl"] is not None
    
    @patch('app.routers.portfolio.get_current_price')
    def test_add_portfolio_item_case_insensitive(self, mock_get_price, client, auth_headers, test_user, db):
        """Test that ticker is converted to uppercase."""
        mock_get_price.return_value = 25.50
        
        payload = {
            "ticker": "petr4",
            "quantity": 100,
            "purchase_price": "20.00",
            "purchase_date": "2023-01-01"
        }
        
        response = client.post("/portfolio", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["ticker"] == "PETR4"
    
    def test_add_portfolio_item_unauthorized(self, client):
        """Test adding portfolio item without authentication."""
        payload = {
            "ticker": "PETR4",
            "quantity": 100,
            "purchase_price": "20.00",
            "purchase_date": "2023-01-01"
        }
        
        response = client.post("/portfolio", json=payload)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetPortfolio:
    """Tests for GET /portfolio endpoint."""
    
    @patch('app.routers.portfolio.get_current_price')
    def test_get_portfolio_success(self, mock_get_price, client, auth_headers, test_user, db):
        """Test getting user's portfolio."""
        from app.db.models import PortfolioItem
        
        mock_get_price.return_value = 25.50
        
        # Add portfolio items
        item1 = PortfolioItem(
            user_id=test_user.id,
            ticker="PETR4",
            quantity=100,
            purchase_price=Decimal("20.00"),
            purchase_date=date(2023, 1, 1)
        )
        item2 = PortfolioItem(
            user_id=test_user.id,
            ticker="VALE3",
            quantity=50,
            purchase_price=Decimal("30.00"),
            purchase_date=date(2023, 2, 1)
        )
        db.add(item1)
        db.add(item2)
        db.commit()
        
        response = client.get("/portfolio", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["positions"]) == 2
        assert data["total_invested"] is not None
        assert data["total_unrealized_pnl"] is not None
    
    def test_get_portfolio_empty(self, client, auth_headers, test_user):
        """Test getting empty portfolio."""
        response = client.get("/portfolio", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["positions"]) == 0
        assert data["total_invested"] == "0"
        assert data["total_realized_pnl"] == "0"
        assert data["total_unrealized_pnl"] == "0"
    
    def test_get_portfolio_unauthorized(self, client):
        """Test getting portfolio without authentication."""
        response = client.get("/portfolio")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @patch('app.core.market_service.get_current_price')
    def test_get_portfolio_with_realized_pnl(self, mock_get_price, client, auth_headers, test_user, db):
        """Test portfolio with sold positions (realized P&L)."""
        from app.db.models import PortfolioItem
        
        # Add sold position
        item = PortfolioItem(
            user_id=test_user.id,
            ticker="PETR4",
            quantity=100,
            purchase_price=Decimal("20.00"),
            purchase_date=date(2023, 1, 1),
            sold_price=Decimal("25.00"),
            sold_date=date(2023, 6, 1)
        )
        db.add(item)
        db.commit()
        
        response = client.get("/portfolio", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["positions"]) == 1
        assert data["total_realized_pnl"] == "500.00"  # (25-20) * 100


class TestGetPortfolioItem:
    """Tests for GET /portfolio/{item_id} endpoint."""
    
    @patch('app.routers.portfolio.get_current_price')
    def test_get_portfolio_item_success(self, mock_get_price, client, auth_headers, test_user, db):
        """Test getting a specific portfolio item."""
        from app.db.models import PortfolioItem
        
        mock_get_price.return_value = 25.50
        
        item = PortfolioItem(
            user_id=test_user.id,
            ticker="PETR4",
            quantity=100,
            purchase_price=Decimal("20.00"),
            purchase_date=date(2023, 1, 1)
        )
        db.add(item)
        db.commit()
        
        response = client.get(f"/portfolio/{item.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == item.id
        assert data["ticker"] == "PETR4"
        assert data["quantity"] == 100
    
    def test_get_portfolio_item_not_found(self, client, auth_headers, test_user):
        """Test getting non-existent portfolio item."""
        response = client.get("/portfolio/99999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "não encontrada" in response.json()["detail"]
    
    def test_get_portfolio_item_unauthorized(self, client):
        """Test getting portfolio item without authentication."""
        response = client.get("/portfolio/1")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_portfolio_item_user_isolation(self, client, auth_headers, test_user, db):
        """Test that users can only see their own items."""
        from app.db.models import User, PortfolioItem
        from app.core.security import hash_password
        
        # Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=hash_password("password123")
        )
        db.add(other_user)
        db.commit()
        
        # Add item for other user
        item = PortfolioItem(
            user_id=other_user.id,
            ticker="VALE3",
            quantity=50,
            purchase_price=Decimal("30.00"),
            purchase_date=date(2023, 1, 1)
        )
        db.add(item)
        db.commit()
        
        # Current user tries to access other user's item
        response = client.get(f"/portfolio/{item.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSellPortfolioItem:
    """Tests for PATCH /portfolio/{item_id}/sell endpoint."""
    
    def test_sell_portfolio_item_success(self, client, auth_headers, test_user, db):
        """Test successfully marking a position as sold."""
        from app.db.models import PortfolioItem
        
        item = PortfolioItem(
            user_id=test_user.id,
            ticker="PETR4",
            quantity=100,
            purchase_price=Decimal("20.00"),
            purchase_date=date(2023, 1, 1)
        )
        db.add(item)
        db.commit()
        
        payload = {
            "sold_price": "25.00",
            "sold_date": "2023-06-01"
        }
        
        response = client.patch(f"/portfolio/{item.id}/sell", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sold_price"] == "25.00"
        assert data["sold_date"] == "2023-06-01"
        assert data["realized_pnl"] == "500.00"  # (25-20) * 100
        assert data["unrealized_pnl"] is None
    
    def test_sell_portfolio_item_already_sold(self, client, auth_headers, test_user, db):
        """Test selling an already sold position."""
        from app.db.models import PortfolioItem
        
        item = PortfolioItem(
            user_id=test_user.id,
            ticker="PETR4",
            quantity=100,
            purchase_price=Decimal("20.00"),
            purchase_date=date(2023, 1, 1),
            sold_price=Decimal("25.00"),
            sold_date=date(2023, 6, 1)
        )
        db.add(item)
        db.commit()
        
        payload = {
            "sold_price": "30.00",
            "sold_date": "2023-07-01"
        }
        
        response = client.patch(f"/portfolio/{item.id}/sell", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "já foi marcada como vendida" in response.json()["detail"]
    
    def test_sell_portfolio_item_not_found(self, client, auth_headers, test_user):
        """Test selling non-existent portfolio item."""
        payload = {
            "sold_price": "25.00",
            "sold_date": "2023-06-01"
        }
        
        response = client.patch("/portfolio/99999/sell", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_sell_portfolio_item_unauthorized(self, client):
        """Test selling portfolio item without authentication."""
        payload = {
            "sold_price": "25.00",
            "sold_date": "2023-06-01"
        }
        
        response = client.patch("/portfolio/1/sell", json=payload)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeletePortfolioItem:
    """Tests for DELETE /portfolio/{item_id} endpoint."""
    
    def test_delete_portfolio_item_success(self, client, auth_headers, test_user, db):
        """Test successfully deleting a portfolio item."""
        from app.db.models import PortfolioItem
        
        item = PortfolioItem(
            user_id=test_user.id,
            ticker="PETR4",
            quantity=100,
            purchase_price=Decimal("20.00"),
            purchase_date=date(2023, 1, 1)
        )
        db.add(item)
        db.commit()
        item_id = item.id
        
        response = client.delete(f"/portfolio/{item_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify item was deleted
        deleted = db.query(PortfolioItem).filter(PortfolioItem.id == item_id).first()
        assert deleted is None
    
    def test_delete_portfolio_item_not_found(self, client, auth_headers, test_user):
        """Test deleting non-existent portfolio item."""
        response = client.delete("/portfolio/99999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_portfolio_item_unauthorized(self, client):
        """Test deleting portfolio item without authentication."""
        response = client.delete("/portfolio/1")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

