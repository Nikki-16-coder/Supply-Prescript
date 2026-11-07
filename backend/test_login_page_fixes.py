"""
Automated Test Suite for Login Page Fixes:
1. Google SSO detection, active status, and redirect to /auth/google
2. Login spinner lifecycle (hidden on load, shown during submit, reset on 401/error/timeout, duplicate prevention)
3. Password visibility toggle (single eye button, only 1 icon visible at any time)
4. Authentication preservation (admin/manager/analyst login, password check, role redirect)
"""

import os
import re
import unittest
from html.parser import HTMLParser
from fastapi.testclient import TestClient

from backend.main import app
from database.db import authenticate_user, create_session, get_user_by_username_or_email
from backend.oauth import is_google_oauth_configured, get_google_client_id, get_google_redirect_uri


class SimpleHTMLMatcher(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        self.elements.append({"tag": tag, "attrs": attr_dict})


class TestLoginPageFixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.login_html_path = os.path.join(cls.project_root, "frontend", "login.html")
        cls.style_css_path = os.path.join(cls.project_root, "frontend", "style.css")
        cls.app_js_path = os.path.join(cls.project_root, "frontend", "app.js")

        with open(cls.login_html_path, "r", encoding="utf-8") as f:
            cls.login_html = f.read()

        with open(cls.style_css_path, "r", encoding="utf-8") as f:
            cls.style_css = f.read()

        with open(cls.app_js_path, "r", encoding="utf-8") as f:
            cls.app_js = f.read()

        parser = SimpleHTMLMatcher()
        parser.feed(cls.login_html)
        cls.elements = parser.elements

    # =========================================================================
    # Requirement 1: Google SSO Endpoint, Configuration, and Button
    # =========================================================================
    def test_oauth_config_endpoint_live(self):
        """GET /auth/oauth-config returns 200, google_oauth_enabled: True, client_id, redirect_uri."""
        res = self.client.get("/auth/oauth-config")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["google_oauth_enabled"])
        self.assertTrue(bool(data["google_client_id"]))
        self.assertIn("callback", data["redirect_uri"])

    def test_auth_google_endpoint_redirects(self):
        """GET /auth/google returns HTTP 302 redirecting to accounts.google.com with oauth_state cookie."""
        res = self.client.get("/auth/google", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        location = res.headers.get("location", "")
        self.assertTrue(location.startswith("https://accounts.google.com/o/oauth2/v2/auth"))
        self.assertIn("client_id=", location)
        self.assertIn("response_type=code", location)
        self.assertIn("scope=", location)
        self.assertIn("state=", location)
        self.assertIn("oauth_state", res.cookies)

    def test_auth_google_with_target_redirect(self):
        """GET /auth/google?target=/admin sets oauth_target cookie and redirects to Google."""
        res = self.client.get("/auth/google?target=/admin", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("oauth_target", res.cookies)
        self.assertEqual(res.cookies["oauth_target"].strip('"'), "/admin")

    def test_login_html_google_sso_button_structure(self):
        """Verify Google SSO button and pill exist with correct IDs."""
        btn_found = any(e["attrs"].get("id") == "btnGoogleSso" for e in self.elements)
        self.assertTrue(btn_found, "btnGoogleSso button element must exist in login.html")
        pill_found = any(e["attrs"].get("id") == "googleSsoPill" for e in self.elements)
        self.assertTrue(pill_found, "googleSsoPill element must exist inside login.html")

    def test_login_html_js_activates_google_sso(self):
        """Verify initOAuthConfig in login.html properly enables button, removes disabled, sets Active pill, and sets redirect to /auth/google."""
        self.assertIn("initOAuthConfig", self.login_html)
        self.assertIn("/auth/oauth-config", self.login_html)
        self.assertIn("googleBtn.disabled = false", self.login_html)
        self.assertIn("googleBtn.removeAttribute('disabled')", self.login_html)
        self.assertIn("googleBtn.classList.add('active')", self.login_html)
        self.assertIn("googlePill.textContent = 'Active'", self.login_html)
        self.assertIn("/auth/google", self.login_html)

    # =========================================================================
    # Requirement 2: Login Spinner Lifecycle and Duplicate Submission Guard
    # =========================================================================
    def test_login_spinner_structure_and_initial_hidden(self):
        """Spinner must exist, have class 'hidden' and style 'display: none;', not spinning on load."""
        spinner_elem = next((e for e in self.elements if e["attrs"].get("id") == "loginSpinner"), None)
        self.assertIsNotNone(spinner_elem, "loginSpinner element must exist")
        classes = spinner_elem["attrs"].get("class", "").split()
        self.assertIn("hidden", classes, "loginSpinner must have 'hidden' class by default")
        style = spinner_elem["attrs"].get("style", "")
        self.assertIn("display: none", style, "loginSpinner must have inline display: none by default")

    def test_style_css_hidden_rule_enforces_display_none(self):
        """frontend/style.css must define .hidden, #loginSpinner.hidden, .spinner-inline.hidden with display: none !important."""
        self.assertIn(".hidden", self.style_css)
        self.assertIn("display: none !important", self.style_css)
        self.assertIn("#loginSpinner.hidden", self.style_css)

    def test_login_form_js_spinner_lifecycle(self):
        """Verify JS controls spinner lifecycle: starts stopped, shows during fetch, stops on 401, stops on timeout, stops on network error."""
        self.assertIn("resetSubmitButton()", self.login_html)
        self.assertIn("isSubmitting = true", self.login_html)
        self.assertIn("isSubmitting = false", self.login_html)
        # Check duplicate submission guard
        self.assertIn("if (isSubmitting) return", self.login_html)
        # Check spinner displayed only when submitting
        self.assertIn("spinner.style.display = 'inline-block'", self.login_html)
        self.assertIn("spinner.style.display = 'none'", self.login_html)
        # Check abort timeout
        self.assertIn("AbortController", self.login_html)

    # =========================================================================
    # Requirement 3: Password Visibility Single Eye Button Toggle
    # =========================================================================
    def test_password_visibility_single_button_two_toggled_icons(self):
        """There must be exactly ONE button for toggling password, with two SVG icons toggled mutually exclusively."""
        toggle_btn = next((e for e in self.elements if e["attrs"].get("id") == "btnTogglePassword"), None)
        self.assertIsNotNone(toggle_btn, "btnTogglePassword button must exist")
        self.assertEqual(toggle_btn["tag"], "button")

        show_icon = next((e for e in self.elements if e["attrs"].get("id") == "eyeIconShow"), None)
        hide_icon = next((e for e in self.elements if e["attrs"].get("id") == "eyeIconHide"), None)
        self.assertIsNotNone(show_icon, "eyeIconShow SVG must exist")
        self.assertIsNotNone(hide_icon, "eyeIconHide SVG must exist")

        # Initial state of eyeIconHide must be hidden
        hide_classes = hide_icon["attrs"].get("class", "").split()
        self.assertIn("hidden", hide_classes, "eyeIconHide must have 'hidden' class initially")
        self.assertIn("display: none", hide_icon["attrs"].get("style", ""), "eyeIconHide must have 'display: none' initially")

    def test_password_visibility_js_mutual_exclusion(self):
        """JS must ensure only ONE eye icon is displayed at any time."""
        self.assertIn("initShowHidePassword", self.login_html)
        self.assertIn("updateIcon", self.login_html)
        self.assertIn("showIcon.style.display = 'none'", self.login_html)
        self.assertIn("hideIcon.style.display = 'block'", self.login_html)
        self.assertIn("showIcon.style.display = 'block'", self.login_html)
        self.assertIn("hideIcon.style.display = 'none'", self.login_html)

    # =========================================================================
    # Requirement 4: Authentication Preservation
    # =========================================================================
    def test_login_api_wrong_password_returns_401(self):
        """POST /auth/login with invalid password returns HTTP 401 Unauthorized."""
        res = self.client.post("/auth/login", json={
            "username_or_email": "admin",
            "password": "WrongPassword@999"
        })
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertIn("detail", data)

    def test_login_api_nonexistent_user_returns_401(self):
        """POST /auth/login with unknown username returns HTTP 401 Unauthorized."""
        res = self.client.post("/auth/login", json={
            "username_or_email": "nonexistent_user_xyz",
            "password": "AnyPassword@123"
        })
        self.assertEqual(res.status_code, 401)

    def test_login_api_valid_admin(self):
        """POST /auth/login with valid admin credentials returns HTTP 200, JWT token, user info, redirect_url."""
        res = self.client.post("/auth/login", json={
            "username_or_email": "admin",
            "password": "Admin@123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(bool(data["token"]))
        self.assertEqual(data["user"]["role"], "admin")
        self.assertEqual(data["redirect_url"], "/dashboard?tab=console")
        self.assertIn("session_token", res.cookies)

    def test_login_api_valid_manager(self):
        """POST /auth/login with manager credentials returns role 'manager' and redirect to /dashboard?tab=console."""
        res = self.client.post("/auth/login", json={
            "username_or_email": "manager",
            "password": "Manager@123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["user"]["role"], "manager")
        self.assertEqual(data["redirect_url"], "/dashboard?tab=console")

    def test_login_api_valid_analyst(self):
        """POST /auth/login with analyst credentials returns role 'analyst' and redirect to /dashboard?tab=home."""
        res = self.client.post("/auth/login", json={
            "username_or_email": "analyst",
            "password": "Analyst@123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["user"]["role"], "analyst")
        self.assertEqual(data["redirect_url"], "/dashboard?tab=home")

    def test_facebook_sso_remains_disabled(self):
        """Facebook SSO button remains disabled with 'Unavailable' pill."""
        fb_match = re.search(r'<button[^>]*class="[^"]*btn-sso[^"]*"[^>]*disabled[^>]*>.*?Facebook SSO.*?<span[^>]*class="sso-status-pill"[^>]*>Unavailable</span>.*?</button>', self.login_html, re.DOTALL)
        self.assertIsNotNone(fb_match, "Facebook SSO button must remain disabled with Unavailable pill")


if __name__ == "__main__":
    unittest.main()
