"""
SupplyPrescript - Authentication & Role-Based Access Control Test Suite
Tests:
1. Valid login with username and email
2. Invalid password rejection (HTTP 401)
3. Unknown user rejection (HTTP 401)
4. Empty and malformed credential rejection (HTTP 422)
5. Session token generation, retrieval, and cookie handling
6. Profile retrieval (/auth/me) with token vs missing token
7. Instant session revocation on logout
8. Role permission enforcement:
   - Manager and Admin authorized for /decision
   - Analyst rejected with HTTP 403 Forbidden for /decision
   - Admin authorized for /auth/users user creation
   - Manager and Analyst rejected with HTTP 403 Forbidden for /auth/users
9. Password security verification (PBKDF2 hash, salt, zero plaintext storage)
"""

import os
import sys
import unittest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment flags
os.environ["SUPPLYPRESCRIPT_ENFORCE_AUTH"] = "true"

from backend.main import app
from database.db import (
    init_db,
    seed_default_users_if_empty,
    get_connection,
    authenticate_user,
)


class TestAuthenticationAndRBAC(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        seed_default_users_if_empty()
        cls.client = TestClient(app)

    # ========================================================================
    # 1. Login Tests
    # ========================================================================
    def test_login_valid_username_admin(self):
        """Admin login with username should succeed, return Bearer token and role redirect."""
        res = self.client.post("/auth/login", json={
            "username_or_email": "admin",
            "password": "Admin@123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(len(data["token"]) > 20)
        self.assertEqual(data["token_type"], "Bearer")
        self.assertEqual(data["user"]["username"], "admin")
        self.assertEqual(data["user"]["role"], "admin")
        self.assertIn("console", data["redirect_url"])
        self.assertNotIn("password_hash", data["user"])
        self.assertNotIn("salt", data["user"])
        # Cookie verification
        self.assertIn("session_token", res.cookies)

    def test_login_valid_email_manager(self):
        """Manager login with email should succeed and return manager role."""
        res = self.client.post("/auth/login", json={
            "username_or_email": "manager@supplyprescript.corp",
            "password": "Manager@123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["user"]["role"], "manager")
        self.assertIn("console", data["redirect_url"])

    def test_login_valid_analyst_redirect(self):
        """Analyst login should redirect to overview dashboard tab."""
        res = self.client.post("/auth/login", json={
            "username_or_email": "analyst",
            "password": "Analyst@123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["user"]["role"], "analyst")
        self.assertIn("home", data["redirect_url"])

    def test_login_invalid_password(self):
        """Invalid password must return HTTP 401 Unauthorized without stack traces."""
        res = self.client.post("/auth/login", json={
            "username_or_email": "admin",
            "password": "WrongPassword999!"
        })
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertIn("Invalid credentials", data.get("detail", ""))

    def test_login_unknown_user(self):
        """Non-existent user must return generic HTTP 401 Unauthorized."""
        res = self.client.post("/auth/login", json={
            "username_or_email": "nonexistent_user",
            "password": "SomePassword123"
        })
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertIn("Invalid credentials", data.get("detail", ""))

    def test_login_empty_credentials(self):
        """Empty username or password must be rejected with HTTP 422."""
        res = self.client.post("/auth/login", json={
            "username_or_email": "",
            "password": "Password123"
        })
        self.assertEqual(res.status_code, 422)

        res2 = self.client.post("/auth/login", json={
            "username_or_email": "admin",
            "password": "   "
        })
        self.assertEqual(res2.status_code, 422)

    # ========================================================================
    # 2. Session Verification & Profile (/auth/me)
    # ========================================================================
    def test_auth_me_with_valid_bearer_token(self):
        """GET /auth/me with Bearer token must return sanitized user profile."""
        login_res = self.client.post("/auth/login", json={
            "username_or_email": "admin",
            "password": "Admin@123"
        })
        token = login_res.json()["token"]

        res = self.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        user = res.json()
        self.assertEqual(user["username"], "admin")
        self.assertEqual(user["role"], "admin")
        self.assertNotIn("password_hash", user)
        self.assertNotIn("salt", user)

    def test_auth_me_with_cookie(self):
        """GET /auth/me with session cookie must return authenticated user profile."""
        # TestClient maintains cookies from previous login request
        client = TestClient(app)
        client.post("/auth/login", json={
            "username_or_email": "manager",
            "password": "Manager@123"
        })
        res = client.get("/auth/me")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["username"], "manager")

    def test_auth_me_unauthenticated(self):
        """GET /auth/me without token must be rejected with HTTP 401."""
        client = TestClient(app)
        res = client.get("/auth/me")
        self.assertEqual(res.status_code, 401)

    # ========================================================================
    # 3. Logout & Session Invalidation
    # ========================================================================
    def test_logout_invalidates_session(self):
        """POST /auth/logout must revoke session in SQLite; subsequent requests return 401."""
        login_res = self.client.post("/auth/login", json={
            "username_or_email": "analyst",
            "password": "Analyst@123"
        })
        token = login_res.json()["token"]

        # Confirm session works
        verify_res = self.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(verify_res.status_code, 200)

        # Logout
        logout_res = self.client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(logout_res.status_code, 200)
        self.assertEqual(logout_res.json()["status"], "success")

        # Confirm revoked token is now rejected
        post_logout_res = self.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(post_logout_res.status_code, 401)

    # ========================================================================
    # 4. Role-Based Access Control (RBAC) on Protected Endpoints
    # ========================================================================
    def test_manager_decision_role_permissions(self):
        """
        /decision requires manager or admin role:
        - Analyst -> 403 Forbidden
        - Manager -> Allowed (past auth layer)
        - Admin -> Allowed (past auth layer)
        """
        # 1. Analyst token
        analyst_login = self.client.post("/auth/login", json={
            "username_or_email": "analyst",
            "password": "Analyst@123"
        })
        analyst_token = analyst_login.json()["token"]

        decision_payload = {
            "shipment_id": "CHIP-TEST-RBAC",
            "manager_decision": "Air Freight",
            "notes": "Testing RBAC permissions"
        }

        # Analyst must receive 403 Forbidden
        res_analyst = self.client.post(
            "/decision",
            json=decision_payload,
            headers={"Authorization": f"Bearer {analyst_token}"}
        )
        self.assertEqual(res_analyst.status_code, 403)
        self.assertIn("Insufficient privileges", res_analyst.json().get("detail", ""))

        # 2. Manager token
        manager_login = self.client.post("/auth/login", json={
            "username_or_email": "manager",
            "password": "Manager@123"
        })
        manager_token = manager_login.json()["token"]

        # Manager should not be blocked with 401 or 403
        res_manager = self.client.post(
            "/decision",
            json=decision_payload,
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        self.assertNotIn(res_manager.status_code, (401, 403))

    def test_admin_user_management_role_permissions(self):
        """
        /auth/users requires admin role:
        - Analyst -> 403 Forbidden
        - Manager -> 403 Forbidden
        - Admin -> 201 Created on POST, 200 OK on GET
        """
        user_payload = {
            "username": f"test_user_{os.urandom(4).hex()}",
            "email": f"user_{os.urandom(4).hex()}@corp.com",
            "password": "Password123!",
            "role": "analyst",
            "full_name": "Test User"
        }

        # Analyst attempting user creation -> 403
        analyst_token = self.client.post("/auth/login", json={"username_or_email": "analyst", "password": "Analyst@123"}).json()["token"]
        res_analyst = self.client.post("/auth/users", json=user_payload, headers={"Authorization": f"Bearer {analyst_token}"})
        self.assertEqual(res_analyst.status_code, 403)

        # Manager attempting user creation -> 403
        manager_token = self.client.post("/auth/login", json={"username_or_email": "manager", "password": "Manager@123"}).json()["token"]
        res_manager = self.client.post("/auth/users", json=user_payload, headers={"Authorization": f"Bearer {manager_token}"})
        self.assertEqual(res_manager.status_code, 403)

        # Admin creating user -> 201 Created
        admin_token = self.client.post("/auth/login", json={"username_or_email": "admin", "password": "Admin@123"}).json()["token"]
        res_admin = self.client.post("/auth/users", json=user_payload, headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res_admin.status_code, 201)
        self.assertEqual(res_admin.json()["username"], user_payload["username"])

        # Admin listing users -> 200 OK
        res_list = self.client.get("/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res_list.status_code, 200)
        usernames = [u["username"] for u in res_list.json()]
        self.assertIn("admin", usernames)
        self.assertIn("manager", usernames)

    def test_admin_page_access_control(self):
        """
        /admin route is strictly backend-protected:
        - Unauthenticated -> 302 redirect to /login?redirect=/admin
        - Analyst -> 403 Forbidden
        - Manager -> 403 Forbidden
        - Admin -> 200 OK (serves admin.html)
        """
        # 1. Unauthenticated client
        unauth_client = TestClient(app)
        res_unauth = unauth_client.get("/admin", follow_redirects=False)
        self.assertEqual(res_unauth.status_code, 302)
        self.assertIn("/login", res_unauth.headers.get("location", ""))

        # 2. Analyst token -> 403 Forbidden
        analyst_login = self.client.post("/auth/login", json={"username_or_email": "analyst", "password": "Analyst@123"}).json()
        res_analyst = self.client.get("/admin", headers={"Authorization": f"Bearer {analyst_login['token']}"})
        self.assertEqual(res_analyst.status_code, 403)
        self.assertIn("Administrator role required", res_analyst.json().get("detail", ""))

        # 3. Manager token -> 403 Forbidden
        manager_login = self.client.post("/auth/login", json={"username_or_email": "manager", "password": "Manager@123"}).json()
        res_manager = self.client.get("/admin", headers={"Authorization": f"Bearer {manager_login['token']}"})
        self.assertEqual(res_manager.status_code, 403)
        self.assertIn("Administrator role required", res_manager.json().get("detail", ""))

        # 4. Admin token -> 200 OK
        admin_login = self.client.post("/auth/login", json={"username_or_email": "admin", "password": "Admin@123"}).json()
        res_admin = self.client.get("/admin", headers={"Authorization": f"Bearer {admin_login['token']}"})
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn("text/html", res_admin.headers.get("content-type", ""))

    def test_admin_system_status_rbac(self):
        """GET /admin/system-status requires admin role and returns real telemetry."""
        admin_token = self.client.post("/auth/login", json={"username_or_email": "admin", "password": "Admin@123"}).json()["token"]
        manager_token = self.client.post("/auth/login", json={"username_or_email": "manager", "password": "Manager@123"}).json()["token"]

        # Manager rejected
        res_mgr = self.client.get("/admin/system-status", headers={"Authorization": f"Bearer {manager_token}"})
        self.assertEqual(res_mgr.status_code, 403)

        # Admin allowed
        res_admin = self.client.get("/admin/system-status", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res_admin.status_code, 200)
        status_data = res_admin.json()
        self.assertEqual(status_data["status"], "operational")
        self.assertIn("database", status_data)
        self.assertIn("ml_engine", status_data)
        self.assertIn("optimization_engine", status_data)

    def test_admin_user_status_toggle_and_deactivation_enforcement(self):
        """Admin can toggle user active status; deactivated user cannot log in."""
        admin_token = self.client.post("/auth/login", json={"username_or_email": "admin", "password": "Admin@123"}).json()["token"]

        # Create temporary user
        uname = f"temp_user_{os.urandom(3).hex()}"
        pwd = "TempUserPassword123!"
        res_create = self.client.post("/auth/users", json={
            "username": uname,
            "email": f"{uname}@corp.com",
            "password": pwd,
            "role": "analyst",
            "full_name": "Temporary Test User"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        user_id = res_create.json()["id"]

        # Confirm user can log in
        login_res1 = self.client.post("/auth/login", json={"username_or_email": uname, "password": pwd})
        self.assertEqual(login_res1.status_code, 200)

        # Deactivate user
        res_deact = self.client.patch(
            f"/auth/users/{user_id}/status",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        self.assertEqual(res_deact.status_code, 200)
        self.assertEqual(res_deact.json()["is_active"], 0)

        # Deactivated user login rejected (HTTP 401)
        login_res2 = self.client.post("/auth/login", json={"username_or_email": uname, "password": pwd})
        self.assertEqual(login_res2.status_code, 401)

        # Reactivate user
        res_react = self.client.patch(
            f"/auth/users/{user_id}/status",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        self.assertEqual(res_react.status_code, 200)

        # User can log in again
        login_res3 = self.client.post("/auth/login", json={"username_or_email": uname, "password": pwd})
        self.assertEqual(login_res3.status_code, 200)

        # Admin cannot deactivate root admin account
        admin_user_id = self.client.post("/auth/login", json={"username_or_email": "admin", "password": "Admin@123"}).json()["user"]["id"]
        res_deact_root = self.client.patch(
            f"/auth/users/{admin_user_id}/status",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        self.assertEqual(res_deact_root.status_code, 400)

        # Delete temporary test user
        res_del = self.client.delete(f"/auth/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res_del.status_code, 200)

    # ========================================================================
    # 5. Security & Password Storage Invariant
    # ========================================================================
    def test_database_password_hashes_are_never_plaintext(self):
        """Verifies directly against SQLite that raw passwords are never stored."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT username, password_hash, salt FROM users")
            rows = cursor.fetchall()
            self.assertTrue(len(rows) >= 3)
            for row in rows:
                pwd_hash = row["password_hash"]
                salt = row["salt"]
                # Must be 64-character hex strings (sha256 key hex)
                self.assertEqual(len(pwd_hash), 64)
                self.assertEqual(len(salt), 32)
                # Raw password substrings must NEVER appear
                self.assertNotIn("Admin@123", pwd_hash)
                self.assertNotIn("Manager@123", pwd_hash)
                self.assertNotIn("Analyst@123", pwd_hash)
        finally:
            conn.close()


class TestGoogleOAuth(unittest.TestCase):
    """
    Test suite for Google OAuth 2.0 authorization, callback, CSRF validation,
    account auto-provisioning, and secure session management.
    """

    @classmethod
    def setUpClass(cls):
        init_db()
        seed_default_users_if_empty()
        cls.client = TestClient(app)

    def test_oauth_config_endpoint_unconfigured(self):
        """When OAuth env vars are unset, endpoint returns google_oauth_enabled=False."""
        with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "", "GOOGLE_CLIENT_SECRET": ""}):
            res = self.client.get("/auth/oauth-config")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "success")
            self.assertFalse(data["google_oauth_enabled"])
            self.assertIsNone(data["google_client_id"])
            self.assertTrue("callback" in data["redirect_uri"])

    def test_oauth_config_endpoint_configured(self):
        """When OAuth credentials are set, endpoint reports enabled and safe client_id."""
        with patch.dict(os.environ, {
            "GOOGLE_CLIENT_ID": "test-mock-client-id.apps.googleusercontent.com",
            "GOOGLE_CLIENT_SECRET": "test-mock-secret",
        }):
            res = self.client.get("/auth/oauth-config")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["google_oauth_enabled"])
            self.assertEqual(data["google_client_id"], "test-mock-client-id.apps.googleusercontent.com")
            # Secret must NEVER be returned in config endpoint
            self.assertNotIn("test-mock-secret", res.text)

    def test_google_authorize_503_when_unconfigured(self):
        """Authorization endpoint returns HTTP 503 if credentials are missing."""
        with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "", "GOOGLE_CLIENT_SECRET": ""}):
            res = self.client.get("/auth/google", follow_redirects=False)
            self.assertEqual(res.status_code, 503)
            self.assertIn("not configured", res.json().get("detail", ""))

    def test_google_authorize_redirect_when_configured(self):
        """Authorization endpoint returns 302 redirect to Google with CSRF state cookie."""
        with patch.dict(os.environ, {
            "GOOGLE_CLIENT_ID": "test-client.apps.googleusercontent.com",
            "GOOGLE_CLIENT_SECRET": "secret-123",
        }):
            res = self.client.get("/auth/google?target=/admin", follow_redirects=False)
            self.assertEqual(res.status_code, 302)
            location = res.headers.get("location", "")
            self.assertTrue(location.startswith("https://accounts.google.com/o/oauth2/v2/auth"))
            self.assertIn("client_id=test-client.apps.googleusercontent.com", location)
            self.assertIn("response_type=code", location)
            self.assertIn("scope=openid+email+profile", location)
            self.assertIn("state=", location)
            # Cookie verification
            self.assertIn("oauth_state", res.cookies)
            self.assertIn("oauth_target", res.cookies)
            self.assertEqual(res.cookies["oauth_target"].strip('"'), "/admin")

    def test_google_callback_user_cancelled(self):
        """If user cancels or Google returns error, redirect to login page with error."""
        res = self.client.get(
            "/auth/google/callback?error=access_denied&error_description=User+denied+access",
            follow_redirects=False,
        )
        self.assertEqual(res.status_code, 302)
        location = res.headers.get("location", "")
        self.assertTrue(location.startswith("/login"))
        self.assertIn("error=", location)

    def test_google_callback_missing_params(self):
        """Missing code or state returns HTTP 400 Bad Request."""
        res = self.client.get("/auth/google/callback")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Missing required OAuth parameter", res.json().get("detail", ""))

    def test_google_callback_csrf_state_mismatch(self):
        """CSRF state mismatch between cookie and query param returns HTTP 400."""
        client = TestClient(app)
        client.cookies.set("oauth_state", "real-legitimate-state")
        res = client.get("/auth/google/callback?code=mock_code&state=attacker_forged_state")
        self.assertEqual(res.status_code, 400)
        self.assertIn("CSRF", res.json().get("detail", ""))

    @patch("backend.main.exchange_google_code_for_token", new_callable=AsyncMock)
    @patch("backend.main.fetch_google_user_profile", new_callable=AsyncMock)
    def test_google_callback_auto_provisions_new_analyst(self, mock_fetch_profile, mock_exchange_code):
        """
        Valid Google callback auto-provisions new user with analyst role,
        creates SQLite session, sets cookie, and redirects with hash token.
        """
        mock_exchange_code.return_value = {"access_token": "mock-access-token-123"}
        mock_fetch_profile.return_value = {
            "email": "auto_new_analyst@example.com",
            "name": "Jane Google Engineer",
            "email_verified": True,
            "sub": "google-sub-998877",
        }

        with patch.dict(os.environ, {
            "GOOGLE_CLIENT_ID": "client-id",
            "GOOGLE_CLIENT_SECRET": "client-secret",
        }):
            client = TestClient(app)
            state = "valid-matching-csrf-state"
            client.cookies.set("oauth_state", state)

            res = client.get(
                f"/auth/google/callback?code=auth_code_xyz&state={state}",
                follow_redirects=False,
            )
            self.assertEqual(res.status_code, 302)
            location = res.headers.get("location", "")
            self.assertIn("/dashboard", location)
            self.assertIn("#token=", location)
            self.assertIn("oauth=success", location)
            self.assertIn("session_token", res.cookies)

            # Verify auto-provisioned user profile in /auth/me
            me_res = client.get("/auth/me")
            self.assertEqual(me_res.status_code, 200)
            me_data = me_res.json()
            self.assertEqual(me_data["email"], "auto_new_analyst@example.com")
            self.assertEqual(me_data["role"], "analyst")
            self.assertEqual(me_data["full_name"], "Jane Google Engineer")

    @patch("backend.main.exchange_google_code_for_token", new_callable=AsyncMock)
    @patch("backend.main.fetch_google_user_profile", new_callable=AsyncMock)
    def test_google_callback_existing_user(self, mock_fetch_profile, mock_exchange_code):
        """Existing user logging in via Google OAuth successfully creates session."""
        mock_exchange_code.return_value = {"access_token": "mock-access-token-456"}
        mock_fetch_profile.return_value = {
            "email": "manager@supplyprescript.corp",
            "name": "Supply Chain Manager",
            "email_verified": True,
        }

        with patch.dict(os.environ, {
            "GOOGLE_CLIENT_ID": "client-id",
            "GOOGLE_CLIENT_SECRET": "client-secret",
        }):
            client = TestClient(app)
            state = "manager-matching-state"
            client.cookies.set("oauth_state", state)

            res = client.get(
                f"/auth/google/callback?code=auth_code_mgr&state={state}",
                follow_redirects=False,
            )
            self.assertEqual(res.status_code, 302)
            location = res.headers.get("location", "")
            self.assertIn("/dashboard?tab=console", location)

            # Check /auth/me
            me_res = client.get("/auth/me")
            self.assertEqual(me_res.status_code, 200)
            self.assertEqual(me_res.json()["role"], "manager")

    @patch("backend.main.exchange_google_code_for_token", new_callable=AsyncMock)
    @patch("backend.main.fetch_google_user_profile", new_callable=AsyncMock)
    def test_google_callback_deactivated_user_rejected(self, mock_fetch_profile, mock_exchange_code):
        """Deactivated user logging in via Google OAuth is rejected with HTTP 403."""
        # Deactivate user temporarily
        admin_client = TestClient(app)
        admin_res = admin_client.post("/auth/login", json={"username_or_email": "admin", "password": "Admin@123"})
        admin_token = admin_res.json()["token"]

        # Create temporary user and deactivate
        new_user_res = admin_client.post(
            "/auth/users",
            json={
                "username": "oauth_deact_user",
                "email": "deactivated_oauth@supplyprescript.corp",
                "password": "TempPassword@123",
                "role": "analyst",
                "full_name": "Deactivated Test User",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        user_id = new_user_res.json()["id"]

        # Deactivate account
        admin_client.patch(
            f"/auth/users/{user_id}/status",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        mock_exchange_code.return_value = {"access_token": "mock-token"}
        mock_fetch_profile.return_value = {
            "email": "deactivated_oauth@supplyprescript.corp",
            "name": "Deactivated Test User",
            "email_verified": True,
        }

        with patch.dict(os.environ, {
            "GOOGLE_CLIENT_ID": "client-id",
            "GOOGLE_CLIENT_SECRET": "client-secret",
        }):
            client = TestClient(app)
            state = "state-deactivated-test"
            client.cookies.set("oauth_state", state)

            res = client.get(f"/auth/google/callback?code=mock_code&state={state}")
            self.assertEqual(res.status_code, 403)
            self.assertIn("deactivated", res.json().get("detail", ""))

        # Clean up
        admin_client.delete(f"/auth/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"})


class TestFacebookOAuth(unittest.TestCase):
    """
    Test suite for Facebook OAuth 2.0 authorization, callback, CSRF validation,
    account linking, auto-provisioning, error/cancellation handling, and session management.
    """

    @classmethod
    def setUpClass(cls):
        init_db()
        seed_default_users_if_empty()
        cls.client = TestClient(app)

    def test_oauth_config_includes_facebook_fields(self):
        """oauth-config endpoint reports facebook configuration without exposing secrets."""
        with patch.dict(os.environ, {
            "FACEBOOK_CLIENT_ID": "mock-fb-app-12345",
            "FACEBOOK_CLIENT_SECRET": "mock-fb-app-secret-67890",
        }):
            res = self.client.get("/auth/oauth-config")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["facebook_oauth_enabled"])
            self.assertEqual(data["facebook_client_id"], "mock-fb-app-12345")
            self.assertIn("callback", data["facebook_redirect_uri"])
            self.assertNotIn("mock-fb-app-secret-67890", res.text)

    def test_facebook_authorize_503_when_unconfigured(self):
        """Authorization endpoint returns HTTP 503 if Facebook credentials are missing."""
        with patch.dict(os.environ, {"FACEBOOK_CLIENT_ID": "", "FACEBOOK_CLIENT_SECRET": "", "FACEBOOK_APP_ID": "", "FACEBOOK_APP_SECRET": ""}):
            res = self.client.get("/auth/facebook", follow_redirects=False)
            self.assertEqual(res.status_code, 503)

    def test_facebook_authorize_redirect_when_configured(self):
        """Authorization endpoint returns 302 redirect to Facebook dialog with CSRF state cookie."""
        with patch.dict(os.environ, {
            "FACEBOOK_CLIENT_ID": "fb-test-client-id",
            "FACEBOOK_CLIENT_SECRET": "fb-test-secret",
        }):
            res = self.client.get("/auth/facebook?target=/dashboard?tab=console", follow_redirects=False)
            self.assertEqual(res.status_code, 302)
            location = res.headers.get("location", "")
            self.assertTrue(location.startswith("https://www.facebook.com/v19.0/dialog/oauth"))
            self.assertIn("client_id=fb-test-client-id", location)
            self.assertIn("scope=email%2Cpublic_profile", location)
            self.assertIn("response_type=code", location)
            # Check cookies
            cookies = res.cookies
            self.assertIn("oauth_state", cookies)
            self.assertIn("oauth_target", cookies)

    def test_facebook_callback_user_cancelled_redirects_to_login(self):
        """If user denies permission or cancels Facebook dialog, redirects to login with error parameter."""
        res = self.client.get(
            "/auth/facebook/callback?error=access_denied&error_code=200&error_reason=user_denied&error_description=Permissions+error",
            follow_redirects=False,
        )
        self.assertEqual(res.status_code, 302)
        location = res.headers.get("location", "")
        self.assertTrue(location.startswith("/login?error="))
        self.assertIn("Permissions", location)

    def test_facebook_callback_missing_params(self):
        """Missing code or state returns HTTP 400 Bad Request."""
        res = self.client.get("/auth/facebook/callback")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Missing required OAuth parameter", res.json()["detail"])

    def test_facebook_callback_csrf_state_mismatch(self):
        """Mismatched CSRF state cookie returns HTTP 400."""
        client = TestClient(app)
        client.cookies.set("oauth_state", "legitimate_state_abc")
        res = client.get("/auth/facebook/callback?code=mock_code&state=forged_state_xyz")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid OAuth state parameter", res.json()["detail"])

    @patch("backend.main.exchange_facebook_code_for_token", new_callable=AsyncMock)
    @patch("backend.main.fetch_facebook_user_profile", new_callable=AsyncMock)
    def test_facebook_callback_missing_email_redirects_to_login(self, mock_fetch_profile, mock_exchange_code):
        """When Facebook account has no email, redirects to login with descriptive error."""
        mock_exchange_code.return_value = {"access_token": "mock-fb-token"}
        mock_fetch_profile.return_value = {
            "id": "123456789",
            "name": "Phone Only User",
            "email": None,
        }

        with patch.dict(os.environ, {
            "FACEBOOK_CLIENT_ID": "fb-id",
            "FACEBOOK_CLIENT_SECRET": "fb-sec",
        }):
            client = TestClient(app)
            state = "fb-state-no-email"
            client.cookies.set("oauth_state", state)

            res = client.get(f"/auth/facebook/callback?code=mock_code&state={state}", follow_redirects=False)
            self.assertEqual(res.status_code, 302)
            location = res.headers.get("location", "")
            self.assertTrue(location.startswith("/login?error="))
            self.assertIn("email", location)

    @patch("backend.main.exchange_facebook_code_for_token", new_callable=AsyncMock)
    @patch("backend.main.fetch_facebook_user_profile", new_callable=AsyncMock)
    def test_facebook_callback_auto_provisions_new_analyst(self, mock_fetch_profile, mock_exchange_code):
        """Auto-provisions new user with analyst role, stores facebook_id, creates session, redirects to dashboard."""
        mock_exchange_code.return_value = {"access_token": "mock-fb-token-111"}
        mock_fetch_profile.return_value = {
            "id": "fb-id-998877",
            "name": "Mark Facebook Engineer",
            "email": "mark.fb.new@supplyprescript.corp",
        }

        with patch.dict(os.environ, {
            "FACEBOOK_CLIENT_ID": "fb-client-id",
            "FACEBOOK_CLIENT_SECRET": "fb-client-secret",
        }):
            client = TestClient(app)
            state = "state-fb-provision-test"
            client.cookies.set("oauth_state", state)

            res = client.get(
                f"/auth/facebook/callback?code=fb_auth_code_xyz&state={state}",
                follow_redirects=False,
            )
            self.assertEqual(res.status_code, 302)
            location = res.headers.get("location", "")
            # Redirects to dashboard with token hash
            self.assertIn("/dashboard", location)
            self.assertIn("#token=", location)
            self.assertIn("oauth=success", location)

            # Check session cookie was set
            self.assertIn("session_token", res.cookies)
            session_token = res.cookies["session_token"]

            # Verify session works with /auth/me
            me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {session_token}"})
            self.assertEqual(me_res.status_code, 200)
            me_data = me_res.json()
            self.assertEqual(me_data["email"], "mark.fb.new@supplyprescript.corp")
            self.assertEqual(me_data["role"], "analyst")
            self.assertEqual(me_data["full_name"], "Mark Facebook Engineer")
            self.assertEqual(me_data.get("auth_provider"), "facebook")

    @patch("backend.main.exchange_facebook_code_for_token", new_callable=AsyncMock)
    @patch("backend.main.fetch_facebook_user_profile", new_callable=AsyncMock)
    def test_facebook_callback_account_linking_existing_user(self, mock_fetch_profile, mock_exchange_code):
        """Existing user logging in via Facebook with matching email is safely linked and authenticated."""
        mock_exchange_code.return_value = {"access_token": "mock-fb-token-222"}
        mock_fetch_profile.return_value = {
            "id": "fb-id-manager-link",
            "name": "Supply Chain Manager",
            "email": "manager@supplyprescript.corp",
        }

        with patch.dict(os.environ, {
            "FACEBOOK_CLIENT_ID": "fb-client-id",
            "FACEBOOK_CLIENT_SECRET": "fb-client-secret",
        }):
            client = TestClient(app)
            state = "state-fb-link-test"
            client.cookies.set("oauth_state", state)

            res = client.get(
                f"/auth/facebook/callback?code=fb_auth_code_link&state={state}",
                follow_redirects=False,
            )
            self.assertEqual(res.status_code, 302)
            location = res.headers.get("location", "")
            self.assertIn("/dashboard?tab=console", location)
            self.assertIn("#token=", location)

            session_token = res.cookies["session_token"]
            me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {session_token}"})
            self.assertEqual(me_res.status_code, 200)
            self.assertEqual(me_res.json()["username"], "manager")

    @patch("backend.main.exchange_facebook_code_for_token", new_callable=AsyncMock)
    @patch("backend.main.fetch_facebook_user_profile", new_callable=AsyncMock)
    def test_facebook_callback_deactivated_user_rejected(self, mock_fetch_profile, mock_exchange_code):
        """Deactivated user attempting Facebook OAuth is rejected with HTTP 403."""
        admin_client = TestClient(app)
        admin_res = admin_client.post("/auth/login", json={"username_or_email": "admin", "password": "Admin@123"})
        admin_token = admin_res.json()["token"]

        new_user_res = admin_client.post(
            "/auth/users",
            json={
                "username": "fb_deact_user",
                "email": "fb_deactivated@supplyprescript.corp",
                "password": "TempPassword@123",
                "role": "analyst",
                "full_name": "Deactivated FB User",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        user_id = new_user_res.json()["id"]

        admin_client.patch(
            f"/auth/users/{user_id}/status",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        mock_exchange_code.return_value = {"access_token": "mock-token"}
        mock_fetch_profile.return_value = {
            "id": "fb-deact-id-123",
            "email": "fb_deactivated@supplyprescript.corp",
            "name": "Deactivated FB User",
        }

        with patch.dict(os.environ, {
            "FACEBOOK_CLIENT_ID": "fb-client-id",
            "FACEBOOK_CLIENT_SECRET": "fb-client-secret",
        }):
            client = TestClient(app)
            state = "state-deactivated-fb-test"
            client.cookies.set("oauth_state", state)

            res = client.get(f"/auth/facebook/callback?code=mock_code&state={state}")
            self.assertEqual(res.status_code, 403)
            self.assertIn("deactivated", res.json().get("detail", ""))

        # Clean up
        admin_client.delete(f"/auth/users/{user_id}", headers={"Authorization": f"Bearer {admin_token}"})


if __name__ == "__main__":
    unittest.main()
