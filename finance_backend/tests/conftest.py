"""
Shared test fixtures and configuration.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch
from typing import Generator

from app.main import app
from app.db.database import Base, get_db
from app.db.models import User, UserRole
from app.core.security import hash_password, create_access_token
from app.core.config import settings

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database for each test.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database override.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """
    Create a test user.
    """
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("testpassword"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
        role=UserRole.USER
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user_admin(db: Session) -> User:
    """
    Create a test admin user.
    """
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=hash_password("adminpassword"),
        full_name="Admin User",
        is_active=True,
        is_verified=True,
        role=UserRole.ADMIN
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """
    Generate an access token for the test user.
    """
    return create_access_token(subject=str(test_user.id))


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """
    Return authorization headers for authenticated requests.
    """
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def mock_yfinance_ticker():
    """
    Mock yfinance.Ticker object with sample data.
    """
    def _create_mock_ticker(history_data=None, info_data=None):
        mock_ticker = Mock()
        
        # Mock history method
        if history_data is not None:
            import pandas as pd
            if isinstance(history_data, list):
                df = pd.DataFrame(history_data)
            else:
                df = history_data
            mock_ticker.history.return_value = df
        else:
            # Default mock history data
            import pandas as pd
            from datetime import datetime, timedelta
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            default_data = pd.DataFrame({
                'Open': [100.0] * 30,
                'High': [105.0] * 30,
                'Low': [95.0] * 30,
                'Close': [102.0] * 30,
                'Volume': [1000000] * 30,
                'Dividends': [0.0] * 30,
                'Stock Splits': [0.0] * 30
            }, index=dates)
            mock_ticker.history.return_value = default_data
        
        # Mock info property
        if info_data is not None:
            mock_ticker.info = info_data
        else:
            mock_ticker.info = {
                'trailingPE': 15.5,
                'forwardPE': 16.0,
                'priceToBook': 2.5,
                'dividendYield': 0.03,
                'beta': 1.2,
                'sector': 'Technology',
                'industry': 'Software',
                'marketCap': 1000000000
            }
        
        return mock_ticker
    
    return _create_mock_ticker


@pytest.fixture
def mock_yfinance():
    """
    Mock the yfinance module.
    """
    with patch('yfinance.Ticker') as mock_ticker_class:
        yield mock_ticker_class


@pytest.fixture
def mock_email_service():
    """
    Mock the email service.
    """
    with patch('app.core.email_service.send_email') as mock_send:
        mock_send.return_value = True
        yield mock_send

