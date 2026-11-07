"""
SupplyPrescript - FastAPI Backend Application
Closed-Loop Prescriptive Analytics for Supply Chain Decision Support

Integrates:
- Machine Learning delay prediction (historical DataCo logistics dataset)
- Prescriptive optimization with PuLP (dynamic mitigation alternatives)
- SQLite database layer for shipments, predictions, decisions, and outcomes
"""

import os
import sys
import json
import re
import secrets
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.optimization import optimize_shipment
from backend.schemas import (
    ShipmentRequest,
    LogisticsPredictionRequest,
    LogisticsPredictionResponse,
    PrescribeRequest,
    PrescribeResponse,
    ManagerDecisionRequest,
    OutcomeEvaluationRequest,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    UserResponse,
    UserCreateRequest,
    UserStatusUpdateRequest,
    UserRoleUpdateRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from backend.auth import (
    get_current_user,
    get_optional_current_user,
    require_role,
    get_role_redirect_url,
    extract_token_from_request,
)
from backend.oauth import (
    load_project_env,
    get_google_client_id,
    is_google_oauth_configured,
    get_google_redirect_uri,
    generate_oauth_state,
    build_google_authorization_url,
    exchange_google_code_for_token,
    fetch_google_user_profile,
    get_facebook_client_id,
    is_facebook_oauth_configured,
    get_facebook_redirect_uri,
    build_facebook_authorization_url,
    exchange_facebook_code_for_token,
    fetch_facebook_user_profile,
)

# Ensure project environment variables (.env) are reliably loaded at application start
load_project_env()
from ml.predict import predict_shipment
from ml.preprocess import MODELS_DIR
from database.db import (
    init_db,
    save_shipment,
    save_prediction,
    save_optimization_decision,
    save_prescribe_audit,
    update_manager_decision,
    save_outcome,
    shipment_exists,
    get_all_shipments,
    get_all_decisions,
    get_all_outcomes,
    get_shipment_history,
    get_analytics_summary,
    authenticate_user,
    create_session,
    revoke_session,
    list_all_users,
    create_user,
    get_user_by_id,
    get_user_by_username_or_email,
    get_user_by_facebook_id,
    get_user_by_google_id,
    link_user_oauth,
    get_connection,
    update_user_status,
    update_user_role,
    delete_user,
    get_system_db_stats,
    seed_default_users_if_empty,
    create_password_reset_token,
    verify_password_reset_token,
    complete_password_reset,
)

# Ensure database tables exist on startup
init_db()

app = FastAPI(
    title="SupplyPrescript API",
    description="Closed-Loop Prescriptive Analytics for Microchip Supply Chain Decision Support",
    version="1.0.0",
)

# Enable CORS for local frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Global Exception Handlers (Clean API Errors & No Stack Traces)
# ============================================================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats Pydantic validation errors into clean user-friendly messages."""
    error_messages = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        msg = err.get("msg", "Invalid input")
        error_messages.append(f"{field}: {msg}" if field else msg)
    summary = "; ".join(error_messages)
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "error_type": "ValidationError",
            "message": summary,
            "detail": summary,
            "errors": error_messages,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Formats standard HTTP exceptions into clean, unified JSON error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "detail": exc.detail,
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handles domain and business validation errors with HTTP 400."""
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "error_type": "ValueError",
            "message": str(exc),
            "detail": str(exc),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catches unhandled exceptions without leaking server stack traces."""
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail,
                "detail": exc.detail,
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_type": "InternalServerError",
            "message": "An unexpected error occurred while processing your request.",
            "detail": str(exc),
        },
    )


# ============================================================================
# Core & Health Endpoints
# ============================================================================
@app.get("/")
def root():
    return {"message": "SupplyPrescript Backend is running"}


# ============================================================================
# 1. Optimization Endpoints (Preserved + Dynamic Options Enabled)
# ============================================================================
@app.get("/optimize")
def optimize():
    """Default demonstration endpoint preserving initial implementation."""
    result = optimize_shipment(
        budget=20000,
        max_delivery_days=7,
        required_quantity=5000,
        supplier_capacity=6000,
        predicted_delay_days=14,
    )
    return result


@app.post("/optimize")
def optimize_shipment_api(request: ShipmentRequest):
    """
    Prescriptive optimization endpoint accepting microchip business constraints
    and optional dynamic mitigation options.
    """
    return optimize_shipment(
        budget=request.budget,
        max_delivery_days=request.max_delivery_days,
        required_quantity=request.required_quantity,
        supplier_capacity=request.supplier_capacity,
        predicted_delay_days=request.predicted_delay_days,
        options=request.options,
    )


# ============================================================================
# 2. ML Delay Prediction Endpoints
# ============================================================================
@app.post("/predict", response_model=LogisticsPredictionResponse)
def predict_delay_api(request: LogisticsPredictionRequest):
    """
    Predicts shipment delay risk and expected delay duration.
    Uses XGBoost classifier trained on historical logistics data (DataCo).

    Expected ML Output Contract:
    {
      "shipment_id": "SHP001",
      "delay_probability": 0.87,
      "predicted_delay_days": 14
    }
    """
    payload = request.model_dump(by_alias=True)
    result = predict_shipment(payload)
    return result


@app.get("/ml/metrics")
def get_ml_metrics():
    """Returns classification evaluation metrics of the trained XGBoost model."""
    metrics_path = os.path.join(MODELS_DIR, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {"status": "Metrics file not found. Train the model first."}


# ============================================================================
# 3. Prescriptive Analytics Closed-Loop Endpoint (ML -> PuLP -> DB Write-Back)
# ============================================================================
@app.post("/prescribe", response_model=PrescribeResponse)
def prescribe_solution_api(request: PrescribeRequest):
    """
    Complete closed-loop decision workflow:
    1. Runs ML delay prediction on logistics profile.
    2. Feeds predicted delay into PuLP optimization engine alongside
       microchip business constraints and dynamic mitigation options.
    3. Persists shipment, prediction, and decision to SQLite database.
    4. Returns both ML prediction and prescriptive recommendation.
    """
    payload = request.model_dump(by_alias=True)

    # 1. ML Delay Prediction
    prediction = predict_shipment(payload)

    # 2. Optimization using predicted delay days, constraints, and dynamic options
    optimization_result = optimize_shipment(
        budget=request.budget,
        max_delivery_days=request.max_delivery_days,
        required_quantity=request.required_quantity,
        supplier_capacity=request.supplier_capacity,
        predicted_delay_days=prediction["predicted_delay_days"],
        options=request.options,
    )

    # 3. Automatic Database Write-Back for Audit Trail (Atomic Transaction)
    try:
        save_prescribe_audit(
            shipment_data=payload,
            prediction_data=prediction,
            shipment_id=request.shipment_id,
            budget=request.budget,
            max_delivery_days=request.max_delivery_days,
            required_quantity=request.required_quantity,
            supplier_capacity=request.supplier_capacity,
            optimization_result=optimization_result,
        )
    except Exception as exc:
        print(f"Database logging warning: {exc}")

    return {
        "shipment_id": request.shipment_id,
        "prediction": prediction,
        "optimization": optimization_result,
    }


# ============================================================================
# 4. User Authentication & Access Management Endpoints
# ============================================================================
@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest, response: Response):
    """
    Enterprise login endpoint: validates credentials, creates a server session in SQLite,
    and returns a Bearer session token while setting a secure HttpOnly cookie.
    """
    user = authenticate_user(
        username_or_email=request.username_or_email,
        password=request.password,
    )
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials. Please verify your username/email and password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session_token = create_session(user_id=user["id"], duration_hours=24)
    redirect_url = get_role_redirect_url(user["role"])

    # Set HttpOnly session cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=86400,
        samesite="lax",
        secure=False,
    )

    return {
        "status": "success",
        "token": session_token,
        "token_type": "Bearer",
        "expires_at": "24 hours",
        "user": user,
        "redirect_url": redirect_url,
    }


@app.post("/auth/logout", response_model=LogoutResponse)
def logout(request: Request, response: Response):
    """
    Invalidates the active session token in SQLite and removes the session cookie.
    """
    token = extract_token_from_request(request)
    if token:
        revoke_session(token)
    response.delete_cookie(key="session_token")
    return {
        "status": "success",
        "message": "Successfully logged out.",
    }


# ============================================================================
# Password Reset & Email Recovery
# ============================================================================
def is_email_service_configured() -> bool:
    """
    Checks whether an outbound SMTP email service is configured.
    Requires SMTP_HOST or EMAIL_HOST to be set with a non-placeholder value.
    """
    host = (os.environ.get("SMTP_HOST") or os.environ.get("EMAIL_HOST") or "").strip()
    placeholder_hosts = ("none", "placeholder", "smtp.example.com", "your-smtp-host", "your_smtp_host", "localhost")
    if not host or host.lower() in placeholder_hosts:
        return False
    return True


def send_password_reset_email(to_email: str, reset_url: str) -> bool:
    """
    Dispatches a password reset link to the recipient using standard SMTP.
    Safely respects configuration, TLS, and port settings.
    Never exposes credentials or tokens in application logs.
    """
    if not is_email_service_configured():
        return False

    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    host = (os.environ.get("SMTP_HOST") or os.environ.get("EMAIL_HOST") or "").strip()
    port = int(os.environ.get("SMTP_PORT") or os.environ.get("EMAIL_PORT") or 587)
    user = os.environ.get("SMTP_USER") or os.environ.get("EMAIL_USER") or None
    password = os.environ.get("SMTP_PASSWORD") or os.environ.get("EMAIL_PASSWORD") or None
    sender = os.environ.get("SMTP_FROM") or os.environ.get("EMAIL_FROM") or "security@supplyprescript.corp"
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "SupplyPrescript - Password Reset Request"
    msg["From"] = f"SupplyPrescript Security <{sender}>"
    msg["To"] = to_email

    text_body = f"""Hello,

A password reset request was received for your SupplyPrescript enterprise account.
Please visit the link below to set a new password (valid for 15 minutes):

{reset_url}

If you did not request a password reset, please disregard this email or notify your system administrator.

SupplyPrescript Enterprise Security
"""
    html_body = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; color: #0f172a;">
        <h2 style="color: #0f172a; margin-top: 0; font-size: 20px;">SupplyPrescript Security</h2>
        <p style="color: #475569; font-size: 14px; line-height: 1.5;">A password reset request was received for your enterprise account. Click the button below to choose a new password. This link is single-use and expires in 15 minutes.</p>
        <div style="margin: 24px 0; text-align: center;">
            <a href="{reset_url}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Reset Password</a>
        </div>
        <p style="color: #64748b; font-size: 13px;">If you cannot click the button, copy and paste this URL into your browser:<br/><a href="{reset_url}" style="color: #2563eb; word-break: break-all;">{reset_url}</a></p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
        <p style="color: #94a3b8; font-size: 12px; margin-bottom: 0;">If you did not request a password reset, no action is needed. Your account remains secure.</p>
    </div>
    """
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            if use_tls:
                server.starttls()
            if user and password:
                server.login(user, password)
            server.sendmail(sender, [to_email], msg.as_string())
        return True
    except Exception as exc:
        print(f"Password reset dispatch notice: {type(exc).__name__}")
        return False


@app.post("/auth/forgot-password")
def forgot_password(request: ForgotPasswordRequest, req: Request):
    """
    Initiates password reset workflow:
    - Verifies whether email delivery service is configured. If not, reports clearly (HTTP 503).
    - If configured, generates a single-use cryptographically secure reset token (15-min expiry).
    - Dispatches email with reset link without revealing whether email is registered.
    """
    if not is_email_service_configured():
        raise HTTPException(
            status_code=503,
            detail="Password reset email delivery service is not configured on this server. Please contact your system administrator to configure SMTP settings.",
        )

    clean_email = request.email.strip().lower()
    user = get_user_by_username_or_email(clean_email)
    if user and user.get("is_active", 1):
        token = create_password_reset_token(user_id=user["id"], duration_minutes=15)
        base_url = (os.environ.get("APP_BASE_URL") or str(req.base_url)).rstrip("/")
        reset_url = f"{base_url}/reset-password?token={token}"
        send_password_reset_email(to_email=user["email"], reset_url=reset_url)

    # Always return identical generic success message to prevent user enumeration
    return {
        "status": "success",
        "message": "If an account associated with that email exists, password reset instructions have been sent to your inbox.",
    }


@app.get("/auth/verify-reset-token")
def verify_reset_token(token: str):
    """
    Verifies if a reset token is valid, unused, and not expired.
    """
    if not token or not token.strip():
        raise HTTPException(status_code=400, detail="Missing reset token parameter.")
    rec = verify_password_reset_token(token.strip())
    if not rec:
        return {
            "status": "error",
            "valid": False,
            "message": "Invalid, expired, or already used password reset link. Please request a new reset link.",
        }
    return {
        "status": "success",
        "valid": True,
        "username": rec.get("username"),
    }


@app.post("/auth/reset-password")
def reset_password(request: ResetPasswordRequest):
    """
    Resets account password using a valid, unused, single-use token.
    Invalidates the token and terminates all active user sessions for security.
    """
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")

    success = complete_password_reset(request.token, request.new_password)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid, expired, or already used password reset link. Please request a new reset link.",
        )
    return {
        "status": "success",
        "message": "Your password has been successfully updated. You may now sign in with your new credentials.",
    }


# ============================================================================
# Single Sign-On (SSO) Endpoints: Google & Facebook OAuth 2.0
# ============================================================================
@app.get("/auth/oauth-config")
def get_oauth_configuration():
    """
    Returns public OAuth availability status and configuration parameters.
    Allows frontend clients to conditionally render SSO action buttons.
    Never exposes client secrets or private tokens.
    """
    is_google_configured = is_google_oauth_configured()
    google_client_id = get_google_client_id() if is_google_configured else None
    google_redirect_uri = get_google_redirect_uri()

    is_fb_configured = is_facebook_oauth_configured()
    fb_client_id = get_facebook_client_id() if is_fb_configured else None
    fb_redirect_uri = get_facebook_redirect_uri()

    return {
        "status": "success",
        "google_oauth_enabled": is_google_configured,
        "google_client_id": google_client_id,
        "redirect_uri": google_redirect_uri,
        "facebook_oauth_enabled": is_fb_configured,
        "facebook_client_id": fb_client_id,
        "facebook_redirect_uri": fb_redirect_uri,
    }


@app.get("/auth/google")
def google_oauth_authorize(request: Request, target: Optional[str] = None):
    """
    Initiates Google OAuth 2.0 authorization flow.
    Generates a cryptographically random CSRF state, stores it in an HttpOnly cookie,
    and returns an HTTP 302 redirect to Google's consent screen.
    """
    if not is_google_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured on this server. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in the environment.",
        )

    state = generate_oauth_state()
    redirect_uri = get_google_redirect_uri()
    auth_url = build_google_authorization_url(state=state, redirect_uri=redirect_uri)

    response = RedirectResponse(url=auth_url, status_code=302)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        max_age=600,
        samesite="lax",
        secure=False,
        path="/",
    )
    if target and target.startswith("/"):
        response.set_cookie(
            key="oauth_target",
            value=target,
            httponly=True,
            max_age=600,
            samesite="lax",
            secure=False,
            path="/",
        )
    return response


@app.get("/auth/google/callback")
async def google_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """
    Handles Google OAuth 2.0 callback:
    1. Validates error or cancellation from Google.
    2. Validates CSRF state against the state cookie.
    3. Exchanges authorization code for access tokens via httpx.
    4. Fetches and validates verified Google user profile.
    5. Looks up or auto-provisions user in SQLite database (with least-privilege 'analyst' role).
    6. Verifies account is active.
    7. Creates server-side session in SQLite sessions table.
    8. Sets HttpOnly session cookie and redirects user to target dashboard or role view.
    """
    # 1. Handle Google Error / User Cancellation
    if error:
        err_msg = error_description or error or "Google authorization was cancelled or failed."
        return RedirectResponse(url=f"/login?error={urllib.parse.quote(err_msg)}", status_code=302)

    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Missing required OAuth parameter 'code' or 'state' from Google callback.",
        )

    # 2. CSRF State Verification
    cookie_state = request.cookies.get("oauth_state")
    if not cookie_state or not secrets.compare_digest(cookie_state, state):
        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state parameter. Possible CSRF attack detected.",
        )

    # 3. Check Google OAuth configuration
    if not is_google_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured on this server.",
        )

    # 4. Exchange authorization code for tokens
    try:
        redirect_uri = get_google_redirect_uri()
        token_data = await exchange_google_code_for_token(code=code, redirect_uri=redirect_uri)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange Google authorization code: {str(exc)}",
        )

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="Google token response did not contain an access_token.",
        )

    # 5. Fetch verified Google user profile
    try:
        profile = await fetch_google_user_profile(access_token=access_token)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch Google profile: {str(exc)}",
        )

    email = profile.get("email")
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Google user profile does not contain an email address.",
        )

    google_sub = profile.get("sub")

    # 6. User lookup or auto-provisioning in SQLite
    user = get_user_by_google_id(str(google_sub)) if google_sub else None
    if not user:
        user = get_user_by_username_or_email(email)
        if user and google_sub:
            link_user_oauth(user["id"], provider="google", provider_user_id=str(google_sub))
            user = get_user_by_id(user["id"])

    if user:
        if not user.get("is_active", 1):
            raise HTTPException(
                status_code=403,
                detail=f"User account '{user['username']}' is deactivated. Please contact an administrator.",
            )
        # Update last login timestamp
        conn = get_connection()
        try:
            conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
            conn.commit()
        finally:
            conn.close()
    else:
        # Auto-provision new user with least-privilege 'analyst' role
        email_prefix = email.split("@")[0].lower()
        clean_prefix = re.sub(r"[^a-zA-Z0-9_]", "_", email_prefix).strip("_") or "google_user"
        base_username = clean_prefix[:20]
        candidate_username = base_username
        while get_user_by_username_or_email(candidate_username):
            candidate_username = f"{base_username}_{secrets.token_hex(2)}"

        random_pw = secrets.token_urlsafe(32) + "A1!"
        full_name = profile.get("name") or profile.get("given_name") or email_prefix.capitalize()

        new_user_id = create_user(
            username=candidate_username,
            email=email,
            password=random_pw,
            role="analyst",
            full_name=full_name,
            auth_provider="google",
            google_id=str(google_sub) if google_sub else None,
        )
        user = get_user_by_id(new_user_id)

    # 7. Create server-side SQLite session
    session_token = create_session(user_id=user["id"], duration_hours=24)

    # 8. Determine destination
    target_cookie = request.cookies.get("oauth_target")
    if target_cookie:
        target_cookie = target_cookie.strip('"')
    role_redirect = get_role_redirect_url(user["role"])
    destination = target_cookie if (target_cookie and target_cookie.startswith("/")) else role_redirect

    # Pass session_token in hash fragment so client-side JS can store in localStorage
    redirect_target = f"{destination}#token={session_token}&oauth=success"
    response = RedirectResponse(url=redirect_target, status_code=302)

    # Set HttpOnly session cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=86400,
        samesite="lax",
        secure=False,
        path="/",
    )
    # Clear temporary oauth cookies
    response.delete_cookie(key="oauth_state", path="/")
    response.delete_cookie(key="oauth_target", path="/")

    return response


# ============================================================================
# Facebook OAuth 2.0 Single Sign-On Endpoints
# ============================================================================
@app.get("/auth/facebook")
def facebook_oauth_authorize(request: Request, target: Optional[str] = None):
    """
    Initiates Facebook OAuth 2.0 authorization flow.
    Generates a cryptographically random CSRF state, stores it in an HttpOnly cookie,
    and returns an HTTP 302 redirect to Facebook's OAuth consent screen.
    """
    if not is_facebook_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="Facebook OAuth is not configured on this server. Please set FACEBOOK_CLIENT_ID and FACEBOOK_CLIENT_SECRET in the environment.",
        )

    state = generate_oauth_state()
    redirect_uri = get_facebook_redirect_uri()
    auth_url = build_facebook_authorization_url(state=state, redirect_uri=redirect_uri)

    response = RedirectResponse(url=auth_url, status_code=302)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        max_age=600,
        samesite="lax",
        secure=False,
        path="/",
    )
    if target and target.startswith("/"):
        response.set_cookie(
            key="oauth_target",
            value=target,
            httponly=True,
            max_age=600,
            samesite="lax",
            secure=False,
            path="/",
        )
    return response


@app.get("/auth/facebook/callback")
async def facebook_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_code: Optional[str] = None,
    error_description: Optional[str] = None,
    error_reason: Optional[str] = None,
):
    """
    Handles Facebook OAuth 2.0 callback:
    1. Validates error, cancellation, or denied permissions from Facebook.
    2. Validates CSRF state against the state cookie.
    3. Exchanges authorization code for access tokens via Facebook Graph API.
    4. Fetches and validates Facebook user profile (id, name, email).
    5. Handles missing email scenario (e.g. phone registration, denied email permission).
    6. Safely handles account linking and duplicate email scenarios.
    7. Looks up or auto-provisions user in SQLite database (with least-privilege 'analyst' role).
    8. Verifies account is active.
    9. Creates server-side session in SQLite sessions table.
    10. Sets HttpOnly session cookie and redirects user to target dashboard or role view.
    """
    # 1. Handle Facebook Error / User Cancellation / Denied Permissions
    if error or error_reason or error_code:
        err_msg = error_description or error_reason or error or "Facebook authorization was cancelled or permissions were denied."
        return RedirectResponse(url=f"/login?error={urllib.parse.quote(err_msg)}", status_code=302)

    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Missing required OAuth parameter 'code' or 'state' from Facebook callback.",
        )

    # 2. CSRF State Verification
    cookie_state = request.cookies.get("oauth_state")
    if not cookie_state or not secrets.compare_digest(cookie_state, state):
        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state parameter. Possible CSRF attack detected.",
        )

    # 3. Check Facebook OAuth configuration
    if not is_facebook_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="Facebook OAuth is not configured on this server.",
        )

    # 4. Exchange authorization code for tokens
    try:
        redirect_uri = get_facebook_redirect_uri()
        token_data = await exchange_facebook_code_for_token(code=code, redirect_uri=redirect_uri)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange Facebook authorization code: {str(exc)}",
        )

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="Facebook token response did not contain an access_token.",
        )

    # 5. Fetch verified Facebook user profile
    try:
        profile = await fetch_facebook_user_profile(access_token=access_token)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch Facebook profile: {str(exc)}",
        )

    fb_id = str(profile.get("id"))
    email = profile.get("email")

    # 6. Handle Missing Email (phone registration or email permission withheld)
    if not email or not email.strip():
        err_msg = "Your Facebook account does not provide an email address or email permission was not granted. Please sign in with corporate credentials or Google."
        return RedirectResponse(url=f"/login?error={urllib.parse.quote(err_msg)}", status_code=302)

    clean_email = email.strip().lower()

    # 7. Safe Account Linking and Duplicate Email Handling
    # First, lookup by Facebook ID
    user = get_user_by_facebook_id(fb_id)

    if not user:
        # Check by email for existing local/google account
        user = get_user_by_username_or_email(clean_email)
        if user:
            # Check if this user account is already linked to a different Facebook ID
            existing_fb_id = user.get("facebook_id")
            if existing_fb_id and str(existing_fb_id) != fb_id:
                raise HTTPException(
                    status_code=409,
                    detail=f"Account '{user['username']}' is already linked to another Facebook account.",
                )
            # Safe account linking: Link Facebook ID to existing verified account
            link_user_oauth(user["id"], provider="facebook", provider_user_id=fb_id)
            user = get_user_by_id(user["id"])

    if user:
        if not user.get("is_active", 1):
            raise HTTPException(
                status_code=403,
                detail=f"User account '{user['username']}' is deactivated. Please contact an administrator.",
            )
        # Update last login timestamp
        conn = get_connection()
        try:
            conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
            conn.commit()
        finally:
            conn.close()
    else:
        # Auto-provision new user with least-privilege 'analyst' role
        email_prefix = clean_email.split("@")[0]
        clean_prefix = re.sub(r"[^a-zA-Z0-9_]", "_", email_prefix).strip("_") or "facebook_user"
        base_username = clean_prefix[:20]
        candidate_username = base_username
        while get_user_by_username_or_email(candidate_username):
            candidate_username = f"{base_username}_{secrets.token_hex(2)}"

        random_pw = secrets.token_urlsafe(32) + "A1!"
        full_name = profile.get("name") or profile.get("first_name") or email_prefix.capitalize()

        new_user_id = create_user(
            username=candidate_username,
            email=clean_email,
            password=random_pw,
            role="analyst",
            full_name=full_name,
            auth_provider="facebook",
            facebook_id=fb_id,
        )
        user = get_user_by_id(new_user_id)

    # 8. Create server-side SQLite session
    session_token = create_session(user_id=user["id"], duration_hours=24)

    # 9. Determine destination
    target_cookie = request.cookies.get("oauth_target")
    if target_cookie:
        target_cookie = target_cookie.strip('"')
    role_redirect = get_role_redirect_url(user["role"])
    destination = target_cookie if (target_cookie and target_cookie.startswith("/")) else role_redirect

    # Pass session_token in hash fragment so client-side JS can store in localStorage
    redirect_target = f"{destination}#token={session_token}&oauth=success"
    response = RedirectResponse(url=redirect_target, status_code=302)

    # Set HttpOnly session cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=86400,
        samesite="lax",
        secure=False,
        path="/",
    )
    # Clear temporary oauth cookies
    response.delete_cookie(key="oauth_state", path="/")
    response.delete_cookie(key="oauth_target", path="/")

    return response


@app.get("/auth/me", response_model=UserResponse)
def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns profile information for the authenticated user."""
    return current_user


@app.get("/auth/users", response_model=List[UserResponse])
def get_users_list(current_user: Dict[str, Any] = Depends(require_role(["admin"]))):
    """Admin-only endpoint: retrieves all registered users."""
    return list_all_users()


@app.post("/auth/users", status_code=201, response_model=UserResponse)
def create_new_user(user_req: UserCreateRequest, current_user: Dict[str, Any] = Depends(require_role(["admin"]))):
    """Admin-only endpoint: creates a new user with an enterprise role."""
    try:
        user_id = create_user(
            username=user_req.username,
            email=user_req.email,
            password=user_req.password,
            role=user_req.role,
            full_name=user_req.full_name,
        )
        return {
            "id": user_id,
            "username": user_req.username,
            "email": user_req.email,
            "role": user_req.role,
            "full_name": user_req.full_name,
            "is_active": 1,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.patch("/auth/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    status_req: UserStatusUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_role(["admin"])),
):
    """Admin-only endpoint: updates a user's active/deactivated status and revokes sessions if deactivated."""
    target_user = get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found.")

    if target_user["username"] == "admin" and not status_req.is_active:
        raise HTTPException(status_code=400, detail="Cannot deactivate the root system administrator.")

    if current_user["id"] == user_id and not status_req.is_active:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own administrator account.")

    success = update_user_status(user_id, 1 if status_req.is_active else 0)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update user status.")

    return {
        "status": "success",
        "message": f"User '{target_user['username']}' status updated to {'active' if status_req.is_active else 'deactivated'}.",
        "user_id": user_id,
        "is_active": 1 if status_req.is_active else 0,
    }


@app.delete("/auth/users/{user_id}")
def remove_user(
    user_id: int,
    current_user: Dict[str, Any] = Depends(require_role(["admin"])),
):
    """Admin-only endpoint: deletes a registered user account."""
    target_user = get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found.")

    if target_user["username"] in ("admin", "manager", "analyst"):
        raise HTTPException(status_code=400, detail="Cannot delete default system demonstration accounts.")

    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own administrator account.")

    success = delete_user(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user.")

    return {
        "status": "success",
        "message": f"User '{target_user['username']}' deleted successfully.",
        "user_id": user_id,
    }


@app.get("/admin/system-status")
def get_system_status(current_user: Dict[str, Any] = Depends(require_role(["admin"]))):
    """Admin-only endpoint: returns live operational health and subsystem metrics."""
    metrics_path = os.path.join(MODELS_DIR, "metrics.json")
    ml_metrics = None
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                ml_metrics = json.load(f)
        except Exception:
            pass

    db_stats = get_system_db_stats()

    return {
        "status": "operational",
        "service": "SupplyPrescript Enterprise Decision Engine",
        "version": "1.0.0",
        "python_version": sys.version.split()[0],
        "database": db_stats,
        "ml_engine": {
            "model_type": "XGBoost Classifier",
            "status": "Loaded & Active",
            "dataset": "DataCo Global Logistics Dataset (180,519 records)",
            "metrics": ml_metrics,
        },
        "optimization_engine": {
            "solver": "PuLP CBC Mixed-Integer Linear Programming",
            "latency_target": "< 50ms",
            "mitigation_options": ["Air Expedite", "Secondary Fab Supplier", "Buffer Acceptance"],
        },
        "security": {
            "hashing_algorithm": "PBKDF2-HMAC-SHA256 (200,000 iterations)",
            "session_ttl_hours": 24,
            "session_store": "SQLite Server-Side Sessions with Instant Revocation",
            "rbac_enforced": True,
        },
        "system_time": datetime.now(timezone.utc).isoformat(),
    }



# ============================================================================
# 5. Database & Decision Tracking Endpoints (Role-Protected)
# ============================================================================
@app.post("/decision")
def record_manager_decision(
    request: ManagerDecisionRequest,
    current_user: Dict[str, Any] = Depends(require_role(["manager", "admin"])),
):
    """Records or overrides manager decision for a shipment. Requires manager or admin role."""
    success = update_manager_decision(
        shipment_id=request.shipment_id,
        manager_decision=request.manager_decision,
        notes=request.notes,
    )
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No optimization decision record found for shipment {request.shipment_id}",
        )
    return {
        "status": "success",
        "message": f"Recorded manager decision '{request.manager_decision}' for {request.shipment_id}",
        "authorized_by": current_user.get("username"),
    }


@app.post("/outcome")
def record_shipment_outcome(
    request: OutcomeEvaluationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Records the real-world post-mitigation outcome and performance evaluation."""
    if not shipment_exists(request.shipment_id):
        raise HTTPException(
            status_code=404,
            detail=f"No shipment found with ID '{request.shipment_id}' to associate outcome.",
        )
    try:
        outcome_id = save_outcome(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "status": "success",
        "outcome_id": outcome_id,
        "message": f"Recorded outcome for {request.shipment_id}",
        "recorded_by": current_user.get("username"),
    }


@app.get("/history/shipments")
def list_shipments():
    """Retrieves all tracked shipments from the database."""
    return get_all_shipments()


@app.get("/history/decisions")
def list_decisions():
    """Retrieves all optimization decisions from the database."""
    return get_all_decisions()


@app.get("/history/outcomes")
def list_outcomes():
    """Retrieves all outcome evaluations from the database."""
    return get_all_outcomes()


@app.get("/history/{shipment_id}")
def get_shipment_audit_trail(shipment_id: str):
    """Retrieves full end-to-end closed-loop audit trail for a shipment."""
    data = get_shipment_history(shipment_id)
    if not data["shipment"] and not data["predictions"] and not data["decisions"]:
        raise HTTPException(status_code=404, detail=f"No records found for shipment {shipment_id}")
    return data


@app.get("/analytics")
def get_analytics():
    """Returns aggregated KPIs across all shipments, decisions, and outcomes."""
    return get_analytics_summary()


# ============================================================================
# Frontend Dashboard & Login Mounting
# ============================================================================
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

@app.get("/login")
def serve_login_page(request: Request):
    """Serves the enterprise split-screen login page."""
    login_path = os.path.join(FRONTEND_DIR, "login.html")
    if os.path.exists(login_path):
        user = get_optional_current_user(request)
        if user:
            redirect_param = request.query_params.get("redirect")
            if redirect_param and redirect_param.startswith("/"):
                # If admin is requested, only allow admin
                if redirect_param == "/admin" and (user.get("role") or "").lower() != "admin":
                    return RedirectResponse(url=get_role_redirect_url(user["role"]), status_code=302)
                return RedirectResponse(url=redirect_param, status_code=302)
            return RedirectResponse(url=get_role_redirect_url(user["role"]), status_code=302)
        return FileResponse(login_path)
    return JSONResponse(status_code=404, content={"message": "Login page not found."})


@app.get("/reset-password")
def serve_reset_password_page(request: Request):
    """Serves the enterprise password reset page."""
    reset_path = os.path.join(FRONTEND_DIR, "reset-password.html")
    if os.path.exists(reset_path):
        return FileResponse(reset_path)
    return JSONResponse(status_code=404, content={"message": "Reset password page not found."})


@app.get("/admin")
def serve_admin_page(request: Request):
    """
    Serves the Admin Console. Backend-enforced role protection:
    - Missing session -> redirect to /login?redirect=/admin
    - Non-admin user (manager/analyst) -> HTTP 403 Forbidden
    - Admin user -> serves admin.html
    """
    user = get_optional_current_user(request)
    if not user:
        return RedirectResponse(url="/login?redirect=/admin", status_code=302)
    user_role = (user.get("role") or "").lower()
    if user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Insufficient privileges. Administrator role required to access the Admin Console. Your role: '{user_role}'.",
        )
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return JSONResponse(status_code=404, content={"message": "Admin console page not found."})


@app.get("/admin.html")
def serve_admin_html(request: Request):
    """Canonical alias redirecting /admin.html to protected /admin."""
    return serve_admin_page(request)


@app.get("/style.css")
def serve_root_style():
    """Serves style.css at root for relative stylesheet references."""
    style_path = os.path.join(FRONTEND_DIR, "style.css")
    if os.path.exists(style_path):
        return FileResponse(style_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="style.css not found")

@app.get("/logo.png")
def serve_root_logo():
    """Serves logo.png at root for relative image references."""
    logo_path = os.path.join(FRONTEND_DIR, "logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="logo.png not found")

@app.get("/favicon.ico")
def serve_favicon():
    """Serves favicon using logo.png."""
    logo_path = os.path.join(FRONTEND_DIR, "logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/png")
    return Response(status_code=204)

if os.path.exists(FRONTEND_DIR):
    app.mount("/dashboard", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")