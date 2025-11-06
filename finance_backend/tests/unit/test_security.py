"""
Unit tests for security functions.
"""
import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)
from app.core.config import settings
from app.db.models import User, UserRole


class TestPasswordHashing:
    """Tests for password hashing functions."""
    
    def test_hash_password(self):
        """Test that password is hashed correctly."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        hashed = hash_password(password)
        wrong_password = "wrongpassword"
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_hash_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "testpassword123"
        hashed1 = hash_password(password)
        hashed2 = hash_password(password)
        
        # Hashes should be different due to salt
        assert hashed1 != hashed2
        # But both should verify correctly
        assert verify_password(password, hashed1) is True
        assert verify_password(password, hashed2) is True


class TestTokenCreation:
    """Tests for JWT token creation."""
    
    def test_create_access_token(self):
        """Test that access token is created correctly."""
        user_id = "123"
        token = create_access_token(subject=user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_expiration(self):
        """Test token creation with custom expiration."""
        user_id = "123"
        expires_minutes = 60
        token = create_access_token(subject=user_id, expires_minutes=expires_minutes)
        
        # Decode token to verify expiration
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == user_id
        assert "exp" in payload
    
    def test_create_access_token_default_expiration(self):
        """Test token creation with default expiration."""
        user_id = "123"
        token = create_access_token(subject=user_id)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Should expire in approximately 30 minutes (default)
        expected_exp = now + timedelta(minutes=settings.access_token_expire_minutes)
        assert abs((exp - expected_exp).total_seconds()) < 60  # Allow 1 minute tolerance


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""
    
    def test_get_current_user_valid_token(self, db: Session, test_user: User):
        """Test get_current_user with valid token."""
        token = create_access_token(subject=str(test_user.id))
        
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # get_current_user is a dependency, so we call it directly for unit testing
        user = get_current_user(credentials=credentials, db=db)
        
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert user.username == test_user.username
    
    def test_get_current_user_invalid_token(self, db: Session):
        """Test get_current_user with invalid token."""
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials, db=db)
        
        assert exc_info.value.status_code == 401
    
    def test_get_current_user_nonexistent_user(self, db: Session):
        """Test get_current_user with token for non-existent user."""
        # Create token for user that doesn't exist
        token = create_access_token(subject="99999")
        
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials, db=db)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)
    
    def test_get_current_user_expired_token(self, db: Session, test_user: User):
        """Test get_current_user with expired token."""
        # Create token with negative expiration (already expired)
        # Note: This test may not work as expected because JWT validation happens before user lookup
        # The token will fail to decode, so we'll get a JWT error
        from datetime import timedelta
        from jose import jwt
        from app.core.config import settings
        
        # Create manually expired token
        from datetime import datetime, timezone
        expire = datetime.now(timezone.utc) - timedelta(minutes=1)
        to_encode = {"sub": str(test_user.id), "exp": expire}
        token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials, db=db)
        
        assert exc_info.value.status_code == 401

