"""
SupplyPrescript - Google and Facebook OAuth 2.0 Integration Module
Handles:
1. OAuth authorization URL generation with CSRF state protection
2. Token exchange with Google and Facebook OAuth 2.0 endpoints (httpx)
3. User profile verification from Google OpenID and Facebook Graph API
4. SQLite user lookup, safe auto-provisioning, account linking, and session creation
"""

import os
import json
import secrets
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import httpx
from dotenv import load_dotenv

# Determine project root directory regardless of current working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROOT_ENV_PATH = PROJECT_ROOT / ".env"


def load_project_env(force_reload: bool = False) -> None:
    """
    Reliably loads environment variables from the project root .env file,
    regardless of the terminal's current working directory.
    Checks project root first, then current working directory, then backend folder.
    """
    candidate_paths = [
        ROOT_ENV_PATH,
        Path.cwd() / ".env",
        Path(__file__).resolve().parent / ".env",
    ]
    for p in candidate_paths:
        if p.is_file():
            load_dotenv(dotenv_path=p, override=force_reload)
            # If credentials are not yet present in os.environ, force override
            if (not os.environ.get("GOOGLE_CLIENT_ID") or not os.environ.get("GOOGLE_CLIENT_SECRET")
                or not os.environ.get("FACEBOOK_CLIENT_ID")):
                load_dotenv(dotenv_path=p, override=True)
            return
    # Fallback to default search
    load_dotenv(override=force_reload)


# Load .env file automatically upon module import
load_project_env()

# Google OAuth Endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def get_google_client_id() -> Optional[str]:
    """Retrieves Google Client ID from environment variables."""
    if "GOOGLE_CLIENT_ID" not in os.environ:
        load_project_env()
    val = os.environ.get("GOOGLE_CLIENT_ID")
    if not val:
        return None
    val = val.strip().strip("'\"")
    return val if val else None


def get_google_client_secret() -> Optional[str]:
    """Retrieves Google Client Secret from environment variables."""
    if "GOOGLE_CLIENT_SECRET" not in os.environ:
        load_project_env()
    val = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not val:
        return None
    val = val.strip().strip("'\"")
    return val if val else None


def get_google_redirect_uri(request_host: Optional[str] = None) -> str:
    """
    Returns the exact Google OAuth callback URL.
    Prefers explicit GOOGLE_REDIRECT_URI environment variable,
    falling back to standard local callback URL.
    """
    if "GOOGLE_REDIRECT_URI" not in os.environ:
        load_project_env()
    configured = os.environ.get("GOOGLE_REDIRECT_URI")
    if configured and configured.strip():
        return configured.strip().strip("'\"")
    
    if request_host:
        proto = "https" if "https" in request_host else "http"
        return f"{proto}://{request_host}/auth/google/callback"

    return "http://127.0.0.1:8000/auth/google/callback"


def is_google_oauth_configured() -> bool:
    """Checks whether both Client ID and Client Secret are configured and non-placeholder."""
    cid = get_google_client_id()
    secret = get_google_client_secret()
    if not cid or not secret:
        return False
    cid_lower = cid.lower()
    secret_lower = secret.lower()
    for ph in ["your-google-client-id", "your-google-client-secret", "placeholder"]:
        if ph in cid_lower or ph in secret_lower:
            return False
    return True


def generate_oauth_state() -> str:
    """Generates a cryptographically secure random state parameter for CSRF mitigation."""
    return secrets.token_urlsafe(32)


def build_google_authorization_url(state: str, redirect_uri: Optional[str] = None) -> str:
    """
    Builds the Google OAuth 2.0 authorization consent URL.
    Scopes requested: openid email profile
    """
    client_id = get_google_client_id()
    if not client_id:
        raise ValueError("Google Client ID is not configured.")

    r_uri = redirect_uri or get_google_redirect_uri()

    params = {
        "client_id": client_id,
        "redirect_uri": r_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


async def exchange_google_code_for_token(
    code: str,
    redirect_uri: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """
    Exchanges an authorization code for Google access and ID tokens.
    """
    client_id = get_google_client_id()
    client_secret = get_google_client_secret()
    if not client_id or not client_secret:
        raise ValueError("Google OAuth credentials are not configured.")

    r_uri = redirect_uri or get_google_redirect_uri()

    payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": r_uri,
        "grant_type": "authorization_code",
    }

    headers = {"Accept": "application/json"}

    if client:
        res = await client.post(GOOGLE_TOKEN_URL, data=payload, headers=headers)
    else:
        async with httpx.AsyncClient(timeout=10.0) as async_client:
            res = await async_client.post(GOOGLE_TOKEN_URL, data=payload, headers=headers)

    if res.status_code != 200:
        err_detail = "Token exchange failed."
        try:
            err_data = res.json()
            err_detail = err_data.get("error_description") or err_data.get("error") or err_detail
        except Exception:
            err_detail = res.text or err_detail
        raise ValueError(f"Google Token Exchange Error ({res.status_code}): {err_detail}")

    return res.json()


async def fetch_google_user_profile(
    access_token: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """
    Fetches verified user identity from Google OpenID userinfo endpoint.
    Returns dictionary containing email, email_verified, name, sub, picture.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    if client:
        res = await client.get(GOOGLE_USERINFO_URL, headers=headers)
    else:
        async with httpx.AsyncClient(timeout=10.0) as async_client:
            res = await async_client.get(GOOGLE_USERINFO_URL, headers=headers)

    if res.status_code != 200:
        raise ValueError(f"Failed to fetch Google user profile ({res.status_code}): {res.text}")

    user_info = res.json()

    if not user_info.get("email"):
        raise ValueError("Google user profile does not contain an email address.")

    if not user_info.get("email_verified", False):
        raise ValueError("Google account email is not verified by Google.")

    return user_info


# ============================================================================
# Facebook OAuth 2.0 Integration
# ============================================================================

# Facebook OAuth & Graph API Endpoints
FACEBOOK_AUTH_URL = "https://www.facebook.com/v19.0/dialog/oauth"
FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"
FACEBOOK_USERINFO_URL = "https://graph.facebook.com/v19.0/me"


def get_facebook_client_id() -> Optional[str]:
    """
    Retrieves Facebook App / Client ID from environment variables.
    Checks FACEBOOK_CLIENT_ID first, then FACEBOOK_APP_ID.
    """
    if "FACEBOOK_CLIENT_ID" not in os.environ and "FACEBOOK_APP_ID" not in os.environ:
        load_project_env()
    val = os.environ.get("FACEBOOK_CLIENT_ID") or os.environ.get("FACEBOOK_APP_ID")
    if not val:
        return None
    val = val.strip().strip("'\"")
    return val if val else None


def get_facebook_client_secret() -> Optional[str]:
    """
    Retrieves Facebook App / Client Secret from environment variables.
    Checks FACEBOOK_CLIENT_SECRET first, then FACEBOOK_APP_SECRET.
    """
    if "FACEBOOK_CLIENT_SECRET" not in os.environ and "FACEBOOK_APP_SECRET" not in os.environ:
        load_project_env()
    val = os.environ.get("FACEBOOK_CLIENT_SECRET") or os.environ.get("FACEBOOK_APP_SECRET")
    if not val:
        return None
    val = val.strip().strip("'\"")
    return val if val else None


def get_facebook_redirect_uri(request_host: Optional[str] = None) -> str:
    """
    Returns the exact Facebook OAuth callback URL.
    Prefers explicit FACEBOOK_REDIRECT_URI environment variable,
    falling back to standard local callback URL.
    """
    if "FACEBOOK_REDIRECT_URI" not in os.environ:
        load_project_env()
    configured = os.environ.get("FACEBOOK_REDIRECT_URI")
    if configured and configured.strip():
        return configured.strip().strip("'\"")

    if request_host:
        proto = "https" if "https" in request_host else "http"
        return f"{proto}://{request_host}/auth/facebook/callback"

    return "http://127.0.0.1:8000/auth/facebook/callback"


def is_facebook_oauth_configured() -> bool:
    """Checks whether both Facebook App ID and App Secret are configured and non-placeholder."""
    cid = get_facebook_client_id()
    secret = get_facebook_client_secret()
    if not cid or not secret:
        return False
    cid_lower = cid.lower()
    secret_lower = secret.lower()
    for ph in [
        "your-facebook-app-id",
        "your-facebook-app-secret",
        "your-facebook-client-id",
        "your-facebook-client-secret",
        "placeholder",
    ]:
        if ph in cid_lower or ph in secret_lower:
            return False
    return True


def build_facebook_authorization_url(state: str, redirect_uri: Optional[str] = None) -> str:
    """
    Builds the Facebook OAuth 2.0 authorization consent URL.
    Scopes requested: email, public_profile
    """
    client_id = get_facebook_client_id()
    if not client_id:
        raise ValueError("Facebook Client ID is not configured.")

    r_uri = redirect_uri or get_facebook_redirect_uri()

    params = {
        "client_id": client_id,
        "redirect_uri": r_uri,
        "state": state,
        "response_type": "code",
        "scope": "email,public_profile",
    }
    return f"{FACEBOOK_AUTH_URL}?{urllib.parse.urlencode(params)}"


async def exchange_facebook_code_for_token(
    code: str,
    redirect_uri: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """
    Exchanges an authorization code for Facebook access tokens via Graph API.
    """
    client_id = get_facebook_client_id()
    client_secret = get_facebook_client_secret()
    if not client_id or not client_secret:
        raise ValueError("Facebook OAuth credentials are not configured.")

    r_uri = redirect_uri or get_facebook_redirect_uri()

    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": r_uri,
        "code": code,
    }
    headers = {"Accept": "application/json"}

    if client:
        res = await client.get(FACEBOOK_TOKEN_URL, params=params, headers=headers)
    else:
        async with httpx.AsyncClient(timeout=10.0) as async_client:
            res = await async_client.get(FACEBOOK_TOKEN_URL, params=params, headers=headers)

    if res.status_code != 200:
        err_detail = "Facebook token exchange failed."
        try:
            err_data = res.json()
            if "error" in err_data and isinstance(err_data["error"], dict):
                err_detail = err_data["error"].get("message") or err_detail
            elif "error_description" in err_data:
                err_detail = err_data["error_description"]
        except Exception:
            err_detail = res.text or err_detail
        raise ValueError(f"Facebook Token Exchange Error ({res.status_code}): {err_detail}")

    token_data = res.json()
    if not token_data.get("access_token"):
        raise ValueError("Facebook token response did not contain an access_token.")

    return token_data


async def fetch_facebook_user_profile(
    access_token: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """
    Fetches verified user identity from Facebook Graph API (/me endpoint).
    Requests fields: id, name, email, first_name, last_name.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    params = {
        "fields": "id,name,email,first_name,last_name",
    }

    if client:
        res = await client.get(FACEBOOK_USERINFO_URL, params=params, headers=headers)
    else:
        async with httpx.AsyncClient(timeout=10.0) as async_client:
            res = await async_client.get(FACEBOOK_USERINFO_URL, params=params, headers=headers)

    if res.status_code != 200:
        err_detail = res.text
        try:
            err_data = res.json()
            if "error" in err_data and isinstance(err_data["error"], dict):
                err_detail = err_data["error"].get("message") or err_detail
        except Exception:
            pass
        raise ValueError(f"Failed to fetch Facebook user profile ({res.status_code}): {err_detail}")

    user_info = res.json()
    if not user_info.get("id"):
        raise ValueError("Facebook user profile did not return a valid user ID.")

    return user_info

