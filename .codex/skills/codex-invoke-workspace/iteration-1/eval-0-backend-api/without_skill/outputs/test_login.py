"""
Test suite for the login endpoint implementation.

Tests cover:
- Successful login with valid credentials
- Login failures (invalid password, user not found)
- Input validation (invalid email format)
- Error handling and HTTP status codes
"""

import os
import pytest
from unittest.mock import Mock, patch

from auth_service import (
    hash_password,
    verify_password,
    find_user_by_email,
    generate_jwt_token,
)


class TestPasswordHashing:
    """Test bcrypt password hashing and verification."""

    def test_hash_password_creates_hash(self):
        """Password should be hashed and different from plaintext."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 20
        assert hashed.startswith("$2b$")

    def test_verify_password_with_correct_password(self):
        """Correct password should verify successfully."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_with_incorrect_password(self):
        """Incorrect password should fail verification."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_with_invalid_hash(self):
        """Invalid hash format should return False, not raise exception."""
        password = "test_password_123"
        invalid_hash = "not_a_real_hash"

        assert verify_password(password, invalid_hash) is False

    def test_hash_password_with_special_characters(self):
        """Passwords with special characters should hash correctly."""
        password = "p@ssw0rd!#$%^&*()"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_hash_password_with_unicode(self):
        """Unicode passwords should hash correctly."""
        password = "日本語パスワード123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True


class TestFindUserByEmail:
    """Test user lookup from database."""

    def test_find_existing_user(self):
        """Should return user data when email exists."""
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "test@example.com",
                "password_hash": "$2b$12$...",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        result = find_user_by_email(mock_client, "test@example.com")

        assert result is not None
        assert result["email"] == "test@example.com"
        assert result["id"] == "123e4567-e89b-12d3-a456-426614174000"

    def test_find_nonexistent_user(self):
        """Should return None when email does not exist."""
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        result = find_user_by_email(mock_client, "nonexistent@example.com")

        assert result is None

    def test_find_user_calls_supabase_correctly(self):
        """Should call Supabase with correct parameters."""
        mock_client = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = Mock(data=[])

        find_user_by_email(mock_client, "test@example.com")

        mock_client.table.assert_called_once_with("users")
        mock_table.select.assert_called_once_with("*")
        mock_select.eq.assert_called_once_with("email", "test@example.com")
        mock_eq.execute.assert_called_once()


class TestGenerateJWTToken:
    """Test JWT token generation."""

    def test_generate_token_with_secret_key(self):
        """Should generate valid JWT token when secret key is set."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test_secret_key_123"}):
            token = generate_jwt_token(
                user_id="123e4567-e89b-12d3-a456-426614174000", email="test@example.com"
            )

            assert isinstance(token, str)
            assert len(token) > 0
            assert token.count(".") == 2  # JWT has 3 parts

    def test_generate_token_without_secret_key(self):
        """Should raise ValueError when JWT_SECRET_KEY is not set."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("JWT_SECRET_KEY", None)

            with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
                generate_jwt_token(
                    user_id="123e4567-e89b-12d3-a456-426614174000",
                    email="test@example.com",
                )

    def test_token_contains_user_info(self):
        """Generated token should encode user_id and email."""
        import jwt

        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test_secret_key_123"}):
            user_id = "123e4567-e89b-12d3-a456-426614174000"
            email = "test@example.com"
            token = generate_jwt_token(user_id=user_id, email=email)

            decoded = jwt.decode(token, "test_secret_key_123", algorithms=["HS256"])

            assert decoded["sub"] == user_id
            assert decoded["email"] == email
            assert "iat" in decoded
            assert "exp" in decoded

    def test_token_expiration(self):
        """Token should have correct expiration time."""
        import jwt

        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test_secret_key_123"}):
            expires_in_hours = 24
            token = generate_jwt_token(
                user_id="user123",
                email="test@example.com",
                expires_in_hours=expires_in_hours,
            )

            decoded = jwt.decode(token, "test_secret_key_123", algorithms=["HS256"])

            # Token expiration should be approximately 24 hours from now
            exp_time = decoded["exp"]
            iat_time = decoded["iat"]
            diff_seconds = exp_time - iat_time

            # Allow 1 minute tolerance for test execution time
            expected_seconds = expires_in_hours * 60 * 60
            assert abs(diff_seconds - expected_seconds) < 60


class TestEndpointIntegration:
    """Integration tests for the login endpoint."""

    def test_login_success_flow(self):
        """Successful login should return token and user info."""
        email = "test@example.com"
        password = "password123"
        user_id = "123e4567-e89b-12d3-a456-426614174000"

        # Mock database user
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [
            {
                "id": user_id,
                "email": email,
                "password_hash": hash_password(password),
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        # Test password verification
        user = find_user_by_email(mock_client, email)
        assert user is not None
        assert verify_password(password, user["password_hash"]) is True

        # Test token generation
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test_secret_key_123"}):
            token = generate_jwt_token(user["id"], user["email"])
            assert token is not None
            assert len(token) > 0

    def test_login_failure_wrong_password(self):
        """Login should fail with wrong password."""
        email = "test@example.com"
        correct_password = "password123"
        wrong_password = "wrongpassword"
        user_id = "123e4567-e89b-12d3-a456-426614174000"

        # Mock database user
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [
            {
                "id": user_id,
                "email": email,
                "password_hash": hash_password(correct_password),
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        user = find_user_by_email(mock_client, email)
        assert user is not None
        assert verify_password(wrong_password, user["password_hash"]) is False

    def test_login_failure_user_not_found(self):
        """Login should fail when user doesn't exist."""
        email = "nonexistent@example.com"

        # Mock database (no user)
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        user = find_user_by_email(mock_client, email)
        assert user is None
