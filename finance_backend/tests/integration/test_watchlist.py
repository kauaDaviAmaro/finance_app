"""
Integration tests for watchlist endpoints.
"""
import pytest
from fastapi import status


class TestAddToWatchlist:
    """Tests for POST /watchlist endpoint."""
    
    def test_add_to_watchlist_success(self, client, auth_headers, test_user, db):
        """Test successfully adding a ticker to watchlist."""
        payload = {
            "ticker": "PETR4"
        }
        
        response = client.post("/watchlist", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["ticker"] == "PETR4"
        # user_id não está no schema de resposta (WatchlistItemOut)
    
    def test_add_to_watchlist_duplicate(self, client, auth_headers, test_user, db):
        """Test adding duplicate ticker to watchlist."""
        from app.db.models import WatchlistItem
        
        # Add existing watchlist item
        item = WatchlistItem(user_id=test_user.id, ticker="PETR4")
        db.add(item)
        db.commit()
        
        payload = {
            "ticker": "PETR4"
        }
        
        response = client.post("/watchlist", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "já está na sua watchlist" in response.json()["detail"]
    
    def test_add_to_watchlist_case_insensitive(self, client, auth_headers, test_user, db):
        """Test that ticker is converted to uppercase."""
        payload = {
            "ticker": "petr4"
        }
        
        response = client.post("/watchlist", json=payload, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["ticker"] == "PETR4"
    
    def test_add_to_watchlist_unauthorized(self, client):
        """Test adding to watchlist without authentication."""
        payload = {
            "ticker": "PETR4"
        }
        
        response = client.post("/watchlist", json=payload)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetWatchlist:
    """Tests for GET /watchlist endpoint."""
    
    def test_get_watchlist_success(self, client, auth_headers, test_user, db):
        """Test getting user's watchlist."""
        from app.db.models import WatchlistItem
        
        # Add watchlist items
        item1 = WatchlistItem(user_id=test_user.id, ticker="PETR4")
        item2 = WatchlistItem(user_id=test_user.id, ticker="VALE3")
        db.add(item1)
        db.add(item2)
        db.commit()
        
        response = client.get("/watchlist", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2
        tickers = [item["ticker"] for item in data["items"]]
        assert "PETR4" in tickers
        assert "VALE3" in tickers
    
    def test_get_watchlist_empty(self, client, auth_headers, test_user):
        """Test getting empty watchlist."""
        response = client.get("/watchlist", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 0
    
    def test_get_watchlist_unauthorized(self, client):
        """Test getting watchlist without authentication."""
        response = client.get("/watchlist")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_watchlist_user_isolation(self, client, auth_headers, test_user, db):
        """Test that users only see their own watchlist."""
        from app.db.models import User, WatchlistItem
        from app.core.security import hash_password
        
        # Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=hash_password("password123")
        )
        db.add(other_user)
        db.commit()
        
        # Add items for both users
        item1 = WatchlistItem(user_id=test_user.id, ticker="PETR4")
        item2 = WatchlistItem(user_id=other_user.id, ticker="VALE3")
        db.add(item1)
        db.add(item2)
        db.commit()
        
        # Current user should only see their items
        response = client.get("/watchlist", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["ticker"] == "PETR4"


class TestRemoveFromWatchlist:
    """Tests for DELETE /watchlist/{ticker} endpoint."""
    
    def test_remove_from_watchlist_success(self, client, auth_headers, test_user, db):
        """Test successfully removing a ticker from watchlist."""
        from app.db.models import WatchlistItem
        
        # Add watchlist item
        item = WatchlistItem(user_id=test_user.id, ticker="PETR4")
        db.add(item)
        db.commit()
        
        response = client.delete("/watchlist/PETR4", headers=auth_headers)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify item was removed
        remaining = db.query(WatchlistItem).filter(
            WatchlistItem.user_id == test_user.id,
            WatchlistItem.ticker == "PETR4"
        ).first()
        assert remaining is None
    
    def test_remove_from_watchlist_not_found(self, client, auth_headers, test_user):
        """Test removing non-existent ticker from watchlist."""
        response = client.delete("/watchlist/NONEXISTENT", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "não encontrado" in response.json()["detail"]
    
    def test_remove_from_watchlist_case_insensitive(self, client, auth_headers, test_user, db):
        """Test that ticker removal is case insensitive."""
        from app.db.models import WatchlistItem
        
        # Add with uppercase
        item = WatchlistItem(user_id=test_user.id, ticker="PETR4")
        db.add(item)
        db.commit()
        
        # Remove with lowercase
        response = client.delete("/watchlist/petr4", headers=auth_headers)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_remove_from_watchlist_unauthorized(self, client):
        """Test removing from watchlist without authentication."""
        response = client.delete("/watchlist/PETR4")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_remove_from_watchlist_user_isolation(self, client, auth_headers, test_user, db):
        """Test that users can only remove their own items."""
        from app.db.models import User, WatchlistItem
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
        item = WatchlistItem(user_id=other_user.id, ticker="VALE3")
        db.add(item)
        db.commit()
        
        # Current user tries to remove other user's item
        response = client.delete("/watchlist/VALE3", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

