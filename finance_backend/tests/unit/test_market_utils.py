"""
Unit tests for market utilities.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.market.ticker_utils import format_ticker
from app.core.market.price_cache import (
    get_current_price,
    update_ticker_prices,
    get_all_tracked_tickers
)
from app.db.models import TickerPrice, WatchlistItem, PortfolioItem


class TestFormatTicker:
    """Tests for ticker formatting."""
    
    def test_format_ticker_b3_stock(self):
        """Test formatting B3 stock ticker."""
        assert format_ticker("PETR4") == "PETR4.SA"
        assert format_ticker("VALE3") == "VALE3.SA"
        assert format_ticker("ITUB4") == "ITUB4.SA"
    
    def test_format_ticker_already_formatted(self):
        """Test ticker that already has .SA suffix."""
        assert format_ticker("PETR4.SA") == "PETR4.SA"
        assert format_ticker("VALE3.SA") == "VALE3.SA"
    
    def test_format_ticker_us_stock(self):
        """Test formatting US stock ticker (no change)."""
        assert format_ticker("AAPL") == "AAPL"
        assert format_ticker("MSFT") == "MSFT"
        assert format_ticker("GOOGL") == "GOOGL"
    
    def test_format_ticker_case_insensitive(self):
        """Test that formatting is case insensitive."""
        assert format_ticker("petr4") == "PETR4.SA"
        assert format_ticker("Petr4") == "PETR4.SA"
        assert format_ticker("PETR4") == "PETR4.SA"
    
    def test_format_ticker_with_spaces(self):
        """Test formatting ticker with spaces."""
        assert format_ticker(" PETR4 ") == "PETR4.SA"
        assert format_ticker("  AAPL  ") == "AAPL"


class TestGetCurrentPrice:
    """Tests for get_current_price function."""
    
    @patch('app.core.market.price_cache.yf.Ticker')
    def test_get_current_price_from_cache(self, mock_ticker_class, db):
        """Test getting price from cache."""
        # Create cached price in database
        cached_price = TickerPrice(
            ticker="PETR4.SA",
            last_price=Decimal("25.50"),
            timestamp=datetime.now()
        )
        db.add(cached_price)
        db.commit()
        
        price = get_current_price("PETR4", db)
        
        assert price == 25.50
        # Should not call yfinance
        mock_ticker_class.assert_not_called()
    
    @patch('app.core.market.price_cache.yf.Ticker')
    def test_get_current_price_from_yfinance(self, mock_ticker_class, db):
        """Test getting price from yfinance when cache is empty."""
        import pandas as pd
        
        # Mock yfinance response
        mock_ticker = Mock()
        mock_data = pd.DataFrame({
            'Close': [25.50]
        })
        mock_ticker.history.return_value = mock_data
        mock_ticker_class.return_value = mock_ticker
        
        price = get_current_price("PETR4", db)
        
        assert price == 25.50
        mock_ticker_class.assert_called_once_with("PETR4.SA")
        
        # Verify cache was updated
        cached = db.query(TickerPrice).filter(TickerPrice.ticker == "PETR4.SA").first()
        assert cached is not None
        assert float(cached.last_price) == 25.50
    
    @patch('app.core.market.price_cache.yf.Ticker')
    def test_get_current_price_stale_cache(self, mock_ticker_class, db):
        """Test getting price when cache is stale (>15 minutes)."""
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Create stale cache (20 minutes ago)
        stale_time = datetime.now() - timedelta(minutes=20)
        cached_price = TickerPrice(
            ticker="PETR4.SA",
            last_price=Decimal("20.00"),
            timestamp=stale_time
        )
        db.add(cached_price)
        db.commit()
        
        # Mock yfinance response with new price
        mock_ticker = Mock()
        mock_data = pd.DataFrame({
            'Close': [25.50]
        })
        mock_ticker.history.return_value = mock_data
        mock_ticker_class.return_value = mock_ticker
        
        price = get_current_price("PETR4", db)
        
        # Should get new price from yfinance, not from cache
        assert price == 25.50
        mock_ticker_class.assert_called_once()
    
    @patch('app.core.market.price_cache.yf.Ticker')
    def test_get_current_price_no_db(self, mock_ticker_class):
        """Test getting price without database."""
        import pandas as pd
        
        mock_ticker = Mock()
        mock_data = pd.DataFrame({
            'Close': [25.50]
        })
        mock_ticker.history.return_value = mock_data
        mock_ticker_class.return_value = mock_ticker
        
        price = get_current_price("PETR4", db=None)
        
        assert price == 25.50
        mock_ticker_class.assert_called_once_with("PETR4.SA")
    
    @patch('app.core.market.price_cache.yf.Ticker')
    def test_get_current_price_invalid_ticker(self, mock_ticker_class, db):
        """Test getting price for invalid ticker."""
        import pandas as pd
        
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()  # Empty dataframe
        mock_ticker_class.return_value = mock_ticker
        
        price = get_current_price("INVALID", db)
        
        assert price is None


class TestGetAllTrackedTickers:
    """Tests for get_all_tracked_tickers function."""
    
    def test_get_all_tracked_tickers_from_watchlist(self, db, test_user):
        """Test getting tickers from watchlist."""
        # Add watchlist items
        db.add(WatchlistItem(user_id=test_user.id, ticker="PETR4"))
        db.add(WatchlistItem(user_id=test_user.id, ticker="VALE3"))
        db.commit()
        
        tickers = get_all_tracked_tickers(db)
        
        assert "PETR4" in tickers
        assert "VALE3" in tickers
        assert len(tickers) == 2
    
    def test_get_all_tracked_tickers_from_portfolio(self, db, test_user):
        """Test getting tickers from portfolio."""
        from datetime import date
        
        # Add portfolio items
        db.add(PortfolioItem(
            user_id=test_user.id,
            ticker="ITUB4",
            quantity=10,
            purchase_price=Decimal("20.00"),
            purchase_date=date.today()
        ))
        db.commit()
        
        tickers = get_all_tracked_tickers(db)
        
        assert "ITUB4" in tickers
        assert len(tickers) == 1
    
    def test_get_all_tracked_tickers_combined(self, db, test_user):
        """Test getting tickers from both watchlist and portfolio."""
        from datetime import date
        
        # Add watchlist items
        db.add(WatchlistItem(user_id=test_user.id, ticker="PETR4"))
        
        # Add portfolio items
        db.add(PortfolioItem(
            user_id=test_user.id,
            ticker="VALE3",
            quantity=10,
            purchase_price=Decimal("20.00"),
            purchase_date=date.today()
        ))
        db.commit()
        
        tickers = get_all_tracked_tickers(db)
        
        assert "PETR4" in tickers
        assert "VALE3" in tickers
        assert len(tickers) == 2
    
    def test_get_all_tracked_tickers_no_duplicates(self, db, test_user):
        """Test that duplicates are removed."""
        from datetime import date
        
        # Add same ticker to both watchlist and portfolio
        db.add(WatchlistItem(user_id=test_user.id, ticker="PETR4"))
        db.add(PortfolioItem(
            user_id=test_user.id,
            ticker="PETR4",
            quantity=10,
            purchase_price=Decimal("20.00"),
            purchase_date=date.today()
        ))
        db.commit()
        
        tickers = get_all_tracked_tickers(db)
        
        assert tickers.count("PETR4") == 1
        assert len(tickers) == 1
    
    def test_get_all_tracked_tickers_empty(self, db):
        """Test getting tickers when none exist."""
        tickers = get_all_tracked_tickers(db)
        
        assert tickers == []


class TestUpdateTickerPrices:
    """Tests for update_ticker_prices function."""
    
    @patch('app.core.market.price_cache._fetch_ticker_price_with_backoff')
    def test_update_ticker_prices_success(self, mock_fetch, db):
        """Test updating prices for multiple tickers."""
        mock_fetch.side_effect = [25.50, 30.00, 15.75]
        
        tickers = ["PETR4", "VALE3", "ITUB4"]
        results = update_ticker_prices(tickers, db, delay_between_requests=0.1)
        
        assert results["PETR4"] == 25.50
        assert results["VALE3"] == 30.00
        assert results["ITUB4"] == 15.75
        
        # Verify prices were cached
        for ticker in tickers:
            formatted = format_ticker(ticker)
            cached = db.query(TickerPrice).filter(TickerPrice.ticker == formatted).first()
            assert cached is not None
    
    @patch('app.core.market.price_cache._fetch_ticker_price_with_backoff')
    def test_update_ticker_prices_partial_failure(self, mock_fetch, db):
        """Test updating prices when some fail."""
        mock_fetch.side_effect = [25.50, None, 15.75]
        
        tickers = ["PETR4", "VALE3", "ITUB4"]
        results = update_ticker_prices(tickers, db, delay_between_requests=0.1)
        
        assert results["PETR4"] == 25.50
        assert results["VALE3"] is None
        assert results["ITUB4"] == 15.75
    
    @patch('app.core.market.price_cache._fetch_ticker_price_with_backoff')
    def test_update_ticker_prices_updates_existing(self, mock_fetch, db):
        """Test updating existing cached prices."""
        # Create existing cache entry
        existing = TickerPrice(
            ticker="PETR4.SA",
            last_price=Decimal("20.00"),
            timestamp=datetime.now()
        )
        db.add(existing)
        db.commit()
        
        mock_fetch.return_value = 25.50
        
        tickers = ["PETR4"]
        update_ticker_prices(tickers, db, delay_between_requests=0.1)
        
        # Verify price was updated
        db.refresh(existing)
        assert float(existing.last_price) == 25.50

