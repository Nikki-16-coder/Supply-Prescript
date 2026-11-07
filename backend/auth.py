"""
SupplyPrescript - Authentication & Role-Based Access Control (RBAC)
Handles session verification, token extraction (Bearer & Cookie), and role enforcement.
"""

import os
from typing import Dict, Any, List, Optional
from fastapi import Request, HTTPException, Depends
from database.db import get_session_user, revoke_session

# Authentication enforcement flag:
# When true, all protected endpoints strictly require valid active sessions.
ENFORCE_AUTH = os.environ.get("SUPPLYPRESCRIPT_ENFORCE_AUTH", "true").lower() in ("1", "true", "yes")


def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Extracts session token from:
    1. Authorization header ('Bearer <token>')
    2. Cookie ('session_token=<token>')
    3. Query parameter ('token=<token>')
    """
    # 1. Authorization Bearer header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.strip():
        parts = auth_header.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1].strip()
        elif len(parts) == 1:
            return parts[0].strip()

    # 2. HTTP-only session cookie
    cookie_token = request.cookies.get("session_token")
    if cookie_token and cookie_token.strip():
        return cookie_token.strip()

    # 3. Query parameter fallback
    query_token = request.query_params.get("token")
    if query_token and query_token.strip():
        return query_token.strip()

    return None


def get_current_user(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency that resolves and validates the authenticated user.
    Raises HTTP 401 if missing, expired, or deactivated.
    """
    token = extract_token_from_request(request)

    if not token:
        if ENFORCE_AUTH:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please log in.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Fallback for unauthenticated legacy tests when ENFORCE_AUTH=false
        return {
            "id": 1,
            "username": "admin",
            "email": "admin@supplyprescript.corp",
            "role": "admin",
            "full_name": "Executive Administrator",
            "is_active": 1,
        }

    user = get_session_user(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid session token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", 1):
        raise HTTPException(
            status_code=403,
            detail="User account is deactivated. Contact system administrator.",
        )

    return user


def get_optional_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Returns the authenticated user if session is valid, or None if unauthenticated."""
    token = extract_token_from_request(request)
    if not token:
        return None
    return get_session_user(token)


def require_role(allowed_roles: List[str]):
    """
    Role verification dependency factory.
    Enforces that current user belongs to one of allowed_roles.
    Returns HTTP 403 Forbidden if user lacks necessary permission.
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = (current_user.get("role") or "analyst").lower()
        normalized_allowed = [r.lower() for r in allowed_roles]

        if user_role not in normalized_allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: Insufficient privileges. Required role: {', '.join(allowed_roles)}. Your role: '{user_role}'.",
            )
        return current_user

    return role_checker


def get_role_redirect_url(role: str) -> str:
    """Returns the default destination URL based on user role."""
    clean_role = (role or "analyst").lower()
    if clean_role in ("admin", "manager"):
        return "/dashboard?tab=console"
    return "/dashboard?tab=home"
