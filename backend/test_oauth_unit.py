"""
SupplyPrescript - Google OAuth Helper Functions Unit Tests
Tests:
1. Environment variable retrieval and defaults
2. Configuration detection (is_google_oauth_configured)
3. CSRF state generation entropy
4. Authorization URL building with standard scopes
5. Token exchange with httpx mock
6. User profile fetching and email_verified validation
"""

import os
import sys
import unittest
from unittest.mock import patch, AsyncMock, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.oauth import (
    get_google_client_id,
    get_google_client_secret,
    get_google_redirect_uri,
    is_google_oauth_configured,
    generate_oauth_state,
    build_google_authorization_url,
    exchange_google_code_for_token,
    fetch_google_user_profile,
    get_facebook_client_id,
    get_facebook_client_secret,
    get_facebook_redirect_uri,
    is_facebook_oauth_configured,
    build_facebook_authorization_url,
    exchange_facebook_code_for_token,
    fetch_facebook_user_profile,
)


class TestGoogleOAuthHelpers(unittest.IsolatedAsyncioTestCase):

    def test_environment_variable_helpers(self):
        with patch.dict(os.environ, {
            "GOOGLE_CLIENT_ID": "mock-client-id-123",
            "GOOGLE_CLIENT_SECRET": "mock-secret-456",
            "GOOGLE_REDIRECT_URI": "http://127.0.0.1:8000/auth/google/callback",
        }):
            self.assertEqual(get_google_client_id(), "mock-client-id-123")
            self.assertEqual(get_google_client_secret(), "mock-secret-456")
            self.assertEqual(get_google_redirect_uri(), "http://127.0.0.1:8000/auth/google/callback")
            self.assertTrue(is_google_oauth_configured())

    def test_unconfigured_when_missing_credentials(self):
        with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "", "GOOGLE_CLIENT_SECRET": ""}):
            self.assertFalse(is_google_oauth_configured())

        with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "id-only", "GOOGLE_CLIENT_SECRET": ""}):
            self.assertFalse(is_google_oauth_configured())

    def test_generate_oauth_state(self):
        state1 = generate_oauth_state()
        state2 = generate_oauth_state()
        self.assertNotEqual(state1, state2)
        self.assertTrue(len(state1) >= 32)

    def test_build_google_authorization_url(self):
        with patch.dict(os.environ, {
            "GOOGLE_CLIENT_ID": "my-client.apps.googleusercontent.com",
            "GOOGLE_CLIENT_SECRET": "my-sec",
        }):
            url = build_google_authorization_url(state="mock_state_xyz", redirect_uri="http://localhost:8000/auth/google/callback")
            self.assertTrue(url.startswith("https://accounts.google.com/o/oauth2/v2/auth?"))
            self.assertIn("client_id=my-client.apps.googleusercontent.com", url)
            self.assertIn("state=mock_state_xyz", url)
            self.assertIn("response_type=code", url)
            self.assertIn("scope=openid+email+profile", url)
            self.assertIn("access_type=online", url)
            self.assertIn("prompt=select_account", url)

    async def test_fetch_google_user_profile_unverified_email_raises(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "email": "unverified@example.com",
            "email_verified": False,
            "name": "Unverified User",
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with self.assertRaises(ValueError) as ctx:
            await fetch_google_user_profile("mock-token", client=mock_client)
        self.assertIn("not verified", str(ctx.exception))

    async def test_fetch_google_user_profile_verified_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "email": "verified@example.com",
            "email_verified": True,
            "name": "Verified User",
            "sub": "1234567890",
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        profile = await fetch_google_user_profile("mock-token", client=mock_client)
        self.assertEqual(profile["email"], "verified@example.com")
        self.assertTrue(profile["email_verified"])

    async def test_exchange_google_code_for_token_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "mock-token-abc",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch.dict(os.environ, {
            "GOOGLE_CLIENT_ID": "client-id",
            "GOOGLE_CLIENT_SECRET": "client-secret",
        }):
            token_data = await exchange_google_code_for_token("auth-code", "http://localhost:8000/auth/google/callback", client=mock_client)
            self.assertEqual(token_data["access_token"], "mock-token-abc")


class TestFacebookOAuthHelpers(unittest.IsolatedAsyncioTestCase):

    def test_facebook_environment_variable_helpers(self):
        with patch.dict(os.environ, {
            "FACEBOOK_CLIENT_ID": "fb-client-123",
            "FACEBOOK_CLIENT_SECRET": "fb-secret-456",
            "FACEBOOK_REDIRECT_URI": "http://127.0.0.1:8000/auth/facebook/callback",
        }):
            self.assertEqual(get_facebook_client_id(), "fb-client-123")
            self.assertEqual(get_facebook_client_secret(), "fb-secret-456")
            self.assertEqual(get_facebook_redirect_uri(), "http://127.0.0.1:8000/auth/facebook/callback")
            self.assertTrue(is_facebook_oauth_configured())

    def test_facebook_app_id_fallback(self):
        with patch.dict(os.environ, {
            "FACEBOOK_CLIENT_ID": "",
            "FACEBOOK_CLIENT_SECRET": "",
            "FACEBOOK_APP_ID": "app-id-789",
            "FACEBOOK_APP_SECRET": "app-secret-012",
        }):
            self.assertEqual(get_facebook_client_id(), "app-id-789")
            self.assertEqual(get_facebook_client_secret(), "app-secret-012")
            self.assertTrue(is_facebook_oauth_configured())

    def test_facebook_unconfigured_when_missing(self):
        with patch.dict(os.environ, {
            "FACEBOOK_CLIENT_ID": "",
            "FACEBOOK_CLIENT_SECRET": "",
            "FACEBOOK_APP_ID": "",
            "FACEBOOK_APP_SECRET": "",
        }):
            self.assertFalse(is_facebook_oauth_configured())

    def test_facebook_unconfigured_when_placeholder(self):
        with patch.dict(os.environ, {
            "FACEBOOK_CLIENT_ID": "your-facebook-app-id",
            "FACEBOOK_CLIENT_SECRET": "your-facebook-app-secret",
        }):
            self.assertFalse(is_facebook_oauth_configured())

    def test_build_facebook_authorization_url(self):
        with patch.dict(os.environ, {
            "FACEBOOK_CLIENT_ID": "9876543210",
            "FACEBOOK_CLIENT_SECRET": "secret_abc",
        }):
            url = build_facebook_authorization_url(state="fb_state_123", redirect_uri="http://localhost:8000/auth/facebook/callback")
            self.assertTrue(url.startswith("https://www.facebook.com/v19.0/dialog/oauth?"))
            self.assertIn("client_id=9876543210", url)
            self.assertIn("state=fb_state_123", url)
            self.assertIn("response_type=code", url)
            self.assertIn("scope=email%2Cpublic_profile", url)

    async def test_exchange_facebook_code_for_token_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "fb-access-token-xyz",
            "token_type": "bearer",
            "expires_in": 5184000,
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch.dict(os.environ, {
            "FACEBOOK_CLIENT_ID": "fb-id",
            "FACEBOOK_CLIENT_SECRET": "fb-secret",
        }):
            token_data = await exchange_facebook_code_for_token("auth-code-123", "http://localhost:8000/auth/facebook/callback", client=mock_client)
            self.assertEqual(token_data["access_token"], "fb-access-token-xyz")

    async def test_exchange_facebook_code_for_token_error_raises(self):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid verification code format",
                "type": "OAuthException",
                "code": 100,
            }
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch.dict(os.environ, {
            "FACEBOOK_CLIENT_ID": "fb-id",
            "FACEBOOK_CLIENT_SECRET": "fb-secret",
        }):
            with self.assertRaises(ValueError) as ctx:
                await exchange_facebook_code_for_token("bad-code", client=mock_client)
            self.assertIn("Invalid verification code", str(ctx.exception))

    async def test_fetch_facebook_user_profile_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "10001234567890",
            "name": "Jane Logistics Analyst",
            "email": "jane.analyst@example.com",
            "first_name": "Jane",
            "last_name": "Analyst",
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        profile = await fetch_facebook_user_profile("fb-token-123", client=mock_client)
        self.assertEqual(profile["id"], "10001234567890")
        self.assertEqual(profile["email"], "jane.analyst@example.com")
        self.assertEqual(profile["name"], "Jane Logistics Analyst")

    async def test_fetch_facebook_user_profile_missing_id_raises(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Invalid token"}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with self.assertRaises(ValueError) as ctx:
            await fetch_facebook_user_profile("invalid-token", client=mock_client)
        self.assertIn("valid user ID", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
