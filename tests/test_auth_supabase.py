"""Tests for Supabase-backed authentication service.

Run with: pytest tests/test_auth_supabase.py -v
"""

import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import MagicMock, patch

from app.services.auth_supabase import (
    AuthService,
    AuthUser,
    UserAlreadyExists,
    InvalidCredentials,
    PasswordPolicyError,
    VerificationError,
    AccountStatus
)


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client for testing."""
    return MagicMock()


@pytest.fixture
def auth_service(mock_supabase):
    """Create auth service with mocked Supabase client."""
    return AuthService(db=mock_supabase)


class TestRegistration:
    """Tests for user registration flow."""
    
    def test_register_creates_account_and_registration(self, auth_service, mock_supabase):
        """Test successful user registration."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{
            'id': 'user-123',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password_hash': 'hashed',
            'status': 'pending_verification',
            'created_at': datetime.now(UTC).isoformat(),
            'updated_at': datetime.now(UTC).isoformat()
        }]
        
        with patch('app.services.auth_supabase.send_verification_email'):
            result = auth_service.register(
                email='test@example.com',
                password='securepass123',
                full_name='Test User'
            )
        
        assert result.email == 'test@example.com'
        assert result.full_name == 'Test User'
    
    def test_register_rejects_duplicate_email(self, auth_service, mock_supabase):
        """Test registration fails for duplicate email."""
        # Mock existing account
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 'existing-user'}
        ]
        
        with pytest.raises(UserAlreadyExists):
            auth_service.register(
                email='existing@example.com',
                password='password123',
                full_name='Test User'
            )
    
    def test_register_validates_password_length(self, auth_service):
        """Test password length validation."""
        with pytest.raises(PasswordPolicyError):
            auth_service.register(
                email='test@example.com',
                password='short',
                full_name='Test User'
            )


class TestLogin:
    """Tests for user login flow."""
    
    def test_login_success(self, auth_service, mock_supabase):
        """Test successful login."""
        # Hash for "password123"
        password_hash = auth_service._hash_password('password123')
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'id': 'user-123',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password_hash': password_hash,
            'status': 'active',
            'created_at': datetime.now(UTC).isoformat(),
            'updated_at': datetime.now(UTC).isoformat(),
            'last_login_at': None
        }]
        
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        
        user = auth_service.login('test@example.com', 'password123')
        
        assert user.email == 'test@example.com'
        assert user.status == AccountStatus.ACTIVE
    
    def test_login_wrong_password(self, auth_service, mock_supabase):
        """Test login fails with wrong password."""
        password_hash = auth_service._hash_password('correctpass')
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'id': 'user-123',
            'email': 'test@example.com',
            'password_hash': password_hash,
            'status': 'active',
            'created_at': datetime.now(UTC).isoformat(),
            'updated_at': datetime.now(UTC).isoformat()
        }]
        
        with pytest.raises(InvalidCredentials):
            auth_service.login('test@example.com', 'wrongpass')
    
    def test_login_nonexistent_user(self, auth_service, mock_supabase):
        """Test login fails for nonexistent user."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        with pytest.raises(InvalidCredentials):
            auth_service.login('nobody@example.com', 'password123')


class TestSessionManagement:
    """Tests for session creation and verification."""
    
    def test_create_session(self, auth_service, mock_supabase):
        """Test session token creation."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        token = auth_service.create_session(
            account_id='user-123',
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0'
        )
        
        assert isinstance(token, str)
        assert len(token) > 20
    
    def test_verify_valid_session(self, auth_service, mock_supabase):
        """Test verification of valid session."""
        future_time = (datetime.now(UTC) + timedelta(days=30)).isoformat()
        
        # Mock session lookup
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'account_id': 'user-123',
            'expires_at': future_time
        }]
        
        # Mock account lookup (second call to table())
        def table_side_effect(name):
            if name == 'auth_accounts':
                mock = MagicMock()
                mock.select.return_value.eq.return_value.execute.return_value.data = [{
                    'id': 'user-123',
                    'email': 'test@example.com',
                    'full_name': 'Test User',
                    'password_hash': 'hash',
                    'status': 'active',
                    'created_at': datetime.now(UTC).isoformat(),
                    'updated_at': datetime.now(UTC).isoformat(),
                    'last_login_at': None
                }]
                return mock
            return MagicMock()
        
        mock_supabase.table.side_effect = table_side_effect
        
        user = auth_service.verify_session('valid-token')
        
        assert user is not None
        assert user.email == 'test@example.com'
    
    def test_verify_expired_session(self, auth_service, mock_supabase):
        """Test verification of expired session."""
        past_time = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'account_id': 'user-123',
            'expires_at': past_time
        }]
        
        user = auth_service.verify_session('expired-token')
        
        assert user is None


class TestPasswordHashing:
    """Tests for password hashing and verification."""
    
    def test_password_hashing_is_consistent(self, auth_service):
        """Test password hash is consistent."""
        password = 'testpass123'
        hash1 = auth_service._hash_password(password)
        
        # Verify works with same password
        assert auth_service._verify_password(password, hash1)
    
    def test_password_hashing_is_unique(self, auth_service):
        """Test each hash is unique (due to random salt)."""
        password = 'testpass123'
        hash1 = auth_service._hash_password(password)
        hash2 = auth_service._hash_password(password)
        
        # Hashes should be different (different salts)
        assert hash1 != hash2
        
        # But both should verify
        assert auth_service._verify_password(password, hash1)
        assert auth_service._verify_password(password, hash2)
    
    def test_password_verification_rejects_wrong_password(self, auth_service):
        """Test wrong password is rejected."""
        hash1 = auth_service._hash_password('correct')
        
        assert not auth_service._verify_password('wrong', hash1)


# Integration test example (requires real Supabase instance)
@pytest.mark.integration
@pytest.mark.skip(reason="Requires Supabase credentials")
def test_full_registration_flow():
    """Integration test for full registration flow.
    
    To run this test:
    1. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars
    2. Run: pytest tests/test_auth_supabase.py -v -m integration
    """
    from app.core.supabase import require_supabase
    
    db = require_supabase()
    auth_service = AuthService(db)
    
    # Register user
    result = auth_service.register(
        email=f'test-{datetime.now().timestamp()}@example.com',
        password='securepass123',
        full_name='Integration Test User'
    )
    
    assert result.id is not None
    assert result.email.endswith('@example.com')
    
    # Cleanup
    db.table('auth_accounts').delete().eq('id', result.id).execute()
    db.table('onboarding_registrations').delete().eq('email', result.email).execute()
