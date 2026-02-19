import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.services.auth import AuthService


class TestAuthService:
    def test_create_access_token(self, mock_db):
        service = AuthService(mock_db)
        user_id = uuid4()
        token = service.create_access_token(user_id)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self, mock_db):
        service = AuthService(mock_db)
        user_id = uuid4()
        token = service.create_access_token(user_id)
        decoded_id = AuthService.decode_token(token)
        assert decoded_id == user_id

    def test_decode_invalid_token(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            AuthService.decode_token("invalid-token")
        assert exc_info.value.status_code == 401

    def test_decode_empty_token(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            AuthService.decode_token("")
