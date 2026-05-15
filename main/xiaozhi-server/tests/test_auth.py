"""Tests for core.auth.AuthManager — token generation and verification."""

import time
from unittest.mock import patch
from core.auth import AuthManager, AuthenticationError


class TestAuthManager:
    def setup_method(self):
        self.secret = "test-secret-key-12345"
        self.auth = AuthManager(self.secret, expire_seconds=3600)

    # ------------------------------------------------------------------
    # Token generation
    # ------------------------------------------------------------------

    def test_generate_token_format(self):
        token = self.auth.generate_token("client-1", "device-1")
        parts = token.split(".")
        assert len(parts) == 2, "Token must be <signature>.<timestamp>"
        sig, ts = parts
        assert sig, "Signature part must be non-empty"
        assert ts.isdigit(), "Timestamp part must be numeric"

    # ------------------------------------------------------------------
    # Successful verification
    # ------------------------------------------------------------------

    def test_verify_valid_token(self):
        token = self.auth.generate_token("client-1", "device-1")
        assert self.auth.verify_token(token, "client-1", "device-1") is True

    # ------------------------------------------------------------------
    # Expiration
    # ------------------------------------------------------------------

    def test_verify_expired_token(self):
        auth_short = AuthManager(self.secret, expire_seconds=1)
        token = auth_short.generate_token("c", "d")
        with patch("core.auth.time") as mock_time:
            mock_time.time.return_value = time.time() + 5
            assert auth_short.verify_token(token, "c", "d") is False

    def test_default_expire_on_invalid_value(self):
        auth = AuthManager(self.secret, expire_seconds=-1)
        assert auth.expire_seconds == 60 * 60 * 24 * 30

    # ------------------------------------------------------------------
    # Wrong credentials
    # ------------------------------------------------------------------

    def test_verify_wrong_client_id(self):
        token = self.auth.generate_token("client-1", "device-1")
        assert self.auth.verify_token(token, "WRONG", "device-1") is False

    def test_verify_wrong_username(self):
        token = self.auth.generate_token("client-1", "device-1")
        assert self.auth.verify_token(token, "client-1", "WRONG") is False

    # ------------------------------------------------------------------
    # Tampered / malformed tokens
    # ------------------------------------------------------------------

    def test_verify_tampered_signature(self):
        token = self.auth.generate_token("client-1", "device-1")
        sig, ts = token.split(".")
        tampered = "AAAA" + sig[4:] + "." + ts
        assert self.auth.verify_token(tampered, "client-1", "device-1") is False

    def test_verify_malformed_token_no_dot(self):
        assert self.auth.verify_token("no-dot-here", "a", "b") is False

    def test_verify_malformed_token_empty(self):
        assert self.auth.verify_token("", "a", "b") is False

    def test_verify_malformed_token_non_numeric_ts(self):
        assert self.auth.verify_token("sig.notanumber", "a", "b") is False
