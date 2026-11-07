import os

def add_chapter_9(doc, h):
    h['add_chapter_cover']("9. APPENDIX")
    h['add_chapter_title']("9. APPENDIX")
    
    # 9.1 Coding
    h['add_heading_14']("9.1 CODING")
    h['add_body'](
        "This section presents authentic source code listings from the core operational modules of the SupplyPrescript platform. "
        "The listings demonstrate the mathematical Mixed-Integer Linear Programming implementation, asynchronous FastAPI endpoint routing, "
        "machine learning feature safety pipelines, relational database persistence, and enterprise multi-provider OAuth 2.0 authentication."
    )
    
    # Listing 9.1: Prescriptive Optimization Engine
    h['add_heading_12']("Listing 9.1: Prescriptive Optimization Engine Formulation (backend/optimization.py)")
    code_opt = """\"\"\"
SupplyPrescript - Prescriptive Optimization Engine
MILP Solver using PuLP for Microchip Supply Chain Mitigation Actions.
\"\"\"

from typing import Dict, Any, Optional, Union
import pulp

DEFAULT_MITIGATION_OPTIONS = {
    "Air Freight": {"cost": 15000, "delivery_days": 2},
    "Secondary Supplier": {"cost": 18000, "delivery_days": 4},
    "Accept Delay": {"cost": 0, "delivery_days": None},
}

def build_options_dict(predicted_delay_days: int, custom_options: Optional[Dict] = None):
    if custom_options:
        options = {}
        for name, details in custom_options.items():
            cost = float(details.get("cost", 0))
            delivery_days = details.get("delivery_days")
            if delivery_days is None:
                delivery_days = int(predicted_delay_days)
            options[name] = {"cost": cost, "delivery_days": int(delivery_days)}
        return options
    return {
        "Air Freight": {"cost": 15000, "delivery_days": 2},
        "Secondary Supplier": {"cost": 18000, "delivery_days": 4},
        "Accept Delay": {"cost": 0, "delivery_days": int(predicted_delay_days)},
    }

def optimize_shipment(budget: float, max_delivery_days: int, required_quantity: int,
                      supplier_capacity: int, predicted_delay_days: int,
                      options: Optional[Dict] = None) -> Dict[str, Any]:
    if required_quantity <= 0 or supplier_capacity <= 0 or budget < 0 or max_delivery_days <= 0:
        raise ValueError("Invalid optimization constraints.")

    resolved_options = build_options_dict(predicted_delay_days, options)

    # 1. Supplier Capacity Feasibility Check
    if required_quantity > supplier_capacity:
        return {
            "recommended_action": None,
            "status": "Infeasible",
            "message": "Required quantity exceeds supplier capacity.",
            "options": resolved_options,
        }

    # 2. PuLP Optimization Formulation (Minimize Mitigation Cost)
    problem = pulp.LpProblem("Shipment_Optimization", pulp.LpMinimize)

    # Binary decision variables for each mitigation alternative
    decisions = {name: pulp.LpVariable(f"option_{i}", cat="Binary")
                 for i, name in enumerate(resolved_options)}

    # Constraint 1: Exclusivity - Select exactly one alternative
    problem += pulp.lpSum(decisions.values()) == 1

    # Constraint 2: Budget Constraint
    problem += pulp.lpSum(decisions[name] * resolved_options[name]["cost"]
                          for name in resolved_options) <= budget

    # Constraint 3: SLA Maximum Delivery Days Constraint
    problem += pulp.lpSum(decisions[name] * resolved_options[name]["delivery_days"]
                          for name in resolved_options) <= max_delivery_days

    # Objective: Minimize Total Cost
    problem += pulp.lpSum(decisions[name] * resolved_options[name]["cost"]
                          for name in resolved_options)

    # Solve using COIN-OR CBC Solver silently
    problem.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[problem.status]

    if status != "Optimal":
        return {
            "recommended_action": None,
            "status": status,
            "message": "No feasible shipment option satisfies the given constraints.",
            "options": resolved_options,
        }

    selected_option = next((name for name, var in decisions.items() if var.value() == 1), None)
    return {
        "recommended_action": selected_option,
        "status": status,
        "chosen_option": resolved_options.get(selected_option),
        "options": resolved_options,
    }
"""
    h['add_code_block'](code_opt)
    
    # Listing 9.2: Machine Learning Preprocessing & Feature Leakage Safety
    h['add_heading_12']("Listing 9.2: ML Preprocessing & Feature Leakage Prevention (ml/preprocess.py)")
    code_prep = """\"\"\"
SupplyPrescript - Machine Learning Preprocessing Module
Dataset: DataCo Supply Chain Dataset (Historical Logistics)
Strictly enforces feature safety and prevents data leakage.
\"\"\"

import os, joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

APPROVED_NUMERICAL_FEATURES = [
    "Days for shipment (scheduled)", "Order Item Quantity",
    "Order Item Product Price", "Order Item Discount",
    "Order Item Discount Rate", "Product Price",
]

APPROVED_CATEGORICAL_FEATURES = [
    "Shipping Mode", "Customer Segment", "Market",
    "Order Region", "Order Country", "Category Name", "Department Name",
]

APPROVED_FEATURES = APPROVED_NUMERICAL_FEATURES + APPROVED_CATEGORICAL_FEATURES
TARGET_CLASSIFICATION = "Late_delivery_risk"

# Strictly prohibited leakage columns (post-transit outcome fields)
FORBIDDEN_LEAKAGE_COLUMNS = [
    "Days for shipping (real)", "Delivery Status", "shipping date (DateOrders)"
]

def validate_feature_safety(columns: list) -> None:
    for col in FORBIDDEN_LEAKAGE_COLUMNS:
        if col in columns:
            raise ValueError(f"DATA LEAKAGE ERROR: Prohibited column '{col}' detected!")

def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", "passthrough", APPROVED_NUMERICAL_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=True),
             APPROVED_CATEGORICAL_FEATURES),
        ]
    )
"""
    h['add_code_block'](code_prep)
    
    # Listing 9.3: Machine Learning Inference Engine
    h['add_heading_12']("Listing 9.3: Machine Learning Inference Engine (ml/predict.py)")
    code_pred = """\"\"\"
SupplyPrescript - Delay Prediction Inference Engine
Encapsulates DelayPredictor singleton with cached model loading.
\"\"\"

import os, joblib, numpy as np, pandas as pd
from ml.preprocess import APPROVED_FEATURES, validate_feature_safety, MODELS_DIR

class DelayPredictor:
    def __init__(self, models_dir: str = MODELS_DIR):
        self.preprocessor_path = os.path.join(models_dir, "preprocessor.joblib")
        self.classifier_path = os.path.join(models_dir, "xgb_classifier.joblib")
        self.regressor_path = os.path.join(models_dir, "xgb_regressor.joblib")
        self._preprocessor = None
        self._classifier = None
        self._regressor = None

    def _ensure_loaded(self):
        if self._classifier is None:
            self._preprocessor = joblib.load(self.preprocessor_path)
            self._classifier = joblib.load(self.classifier_path)
            self._regressor = joblib.load(self.regressor_path)

    def predict(self, raw_input: dict) -> dict:
        self._ensure_loaded()
        df = pd.DataFrame([raw_input])
        validate_feature_safety(list(df.columns))

        # Align features with training contract
        for feat in APPROVED_FEATURES:
            if feat not in df.columns:
                df[feat] = 0

        X = self._preprocessor.transform(df[APPROVED_FEATURES])
        proba = float(self._classifier.predict_proba(X)[0][1])
        delay_days = 0

        if proba >= 0.50:
            pred_reg = float(self._regressor.predict(X)[0])
            delay_days = max(1, int(round(pred_reg)))

        return {
            "shipment_id": str(raw_input.get("shipment_id", "UNKNOWN")),
            "delay_probability": round(proba, 2),
            "predicted_delay_days": delay_days
        }

_predictor_instance = None
def predict_shipment(input_data: dict) -> dict:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = DelayPredictor()
    return _predictor_instance.predict(input_data)
"""
    h['add_code_block'](code_pred)
    
    # Listing 9.4: Database Schema Layer
    h['add_heading_12']("Listing 9.4: Relational Persistence Layer (database/db.py)")
    code_db = """\"\"\"
SupplyPrescript - SQLite Database Layer
Handles persistent storage for shipments, predictions, decisions, outcomes, users.
\"\"\"

import os, sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "supplyprescript.db")

def get_connection(db_path=None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db(db_path=None):
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS shipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shipment_id TEXT UNIQUE NOT NULL,
                supplier_name TEXT DEFAULT 'Primary Microchip Fab',
                component TEXT DEFAULT 'Microchips',
                quantity INTEGER DEFAULT 5000,
                scheduled_days INTEGER DEFAULT 4,
                shipping_mode TEXT DEFAULT 'Standard Class',
                customer_segment TEXT DEFAULT 'Corporate',
                market TEXT DEFAULT 'Pacific Asia',
                order_region TEXT DEFAULT 'Southeast Asia',
                order_country TEXT DEFAULT 'Taiwan',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        \"\"\")
        cur.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shipment_id TEXT NOT NULL,
                delay_probability REAL NOT NULL,
                predicted_delay_days INTEGER NOT NULL,
                model_name TEXT DEFAULT 'XGBoost Delay Classifier',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
            );
        \"\"\")
        cur.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS optimization_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shipment_id TEXT NOT NULL,
                budget REAL NOT NULL,
                max_delivery_days INTEGER NOT NULL,
                required_quantity INTEGER NOT NULL,
                supplier_capacity INTEGER NOT NULL,
                recommended_action TEXT,
                optimization_status TEXT NOT NULL,
                options_evaluated TEXT,
                manager_decision TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
            );
        \"\"\")
        cur.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shipment_id TEXT NOT NULL,
                actual_delivery_days INTEGER,
                actual_cost REAL,
                delay_occurred INTEGER DEFAULT 0,
                decision_effective INTEGER DEFAULT 1,
                feedback_notes TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
            );
        \"\"\")
        cur.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'analyst',
                full_name TEXT,
                is_active INTEGER DEFAULT 1,
                auth_provider TEXT DEFAULT 'local',
                facebook_id TEXT,
                google_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
        \"\"\")
        conn.commit()
    finally:
        conn.close()
"""
    h['add_code_block'](code_db)
    
    # Listing 9.5: Multi-Provider OAuth 2.0 Integration
    h['add_heading_12']("Listing 9.5: Multi-Provider OAuth 2.0 Handler (backend/oauth.py)")
    code_oauth = """\"\"\"
SupplyPrescript - Multi-Provider OAuth 2.0 Authentication Engine
Implements authorization URL generation, state validation, and token exchanges
for Google Identity Services and Facebook Graph API v19.0.
\"\"\"

import os, json, secrets, urllib.parse, urllib.request

def generate_oauth_state() -> str:
    return secrets.token_urlsafe(32)

def build_google_authorization_url(state: str) -> str:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

def build_facebook_authorization_url(state: str) -> str:
    client_id = os.getenv("FACEBOOK_CLIENT_ID")
    redirect_uri = os.getenv("FACEBOOK_REDIRECT_URI", "http://localhost:8000/auth/facebook/callback")
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": "email,public_profile",
        "response_type": "code"
    }
    return f"https://www.facebook.com/v19.0/dialog/oauth?{urllib.parse.urlencode(params)}"
"""
    h['add_code_block'](code_oauth)
    
    # Listing 9.6: RBAC & Authentication Guard
    h['add_heading_12']("Listing 9.6: Role-Based Access Control Guards & Password Security (backend/auth.py)")
    code_auth_guard = """\"\"\"
SupplyPrescript - Enterprise RBAC & Password Hashing Module
Implements PBKDF2-HMAC-SHA256 password hashing and role enforcement decorators.
\"\"\"

import hashlib, secrets
from fastapi import HTTPException, status, Depends

def hash_password(password: str, salt: str = None) -> tuple:
    if not salt:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return dk.hex(), salt

def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    hashed, _ = hash_password(password, salt)
    return secrets.compare_digest(hashed, expected_hash)

def require_role(required_role: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "analyst")
        role_hierarchy = {"analyst": 1, "manager": 2, "admin": 3}
        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: '{required_role}' privilege required."
            )
        return current_user
    return role_checker
"""
    h['add_code_block'](code_auth_guard)
    
    # SCREENSHOTS SECTION
    h['add_heading_14']("SCREENSHOTS")
    h['add_body'](
        "This section presents actual high-resolution screenshots captured directly from the live, operational SupplyPrescript "
        "application running in the enterprise production environment. The screenshots document the primary user interfaces corresponding "
        "to operational monitoring, enterprise authentication, and administrative governance."
    )
    
    # Screenshot 1: Home Page
    h['add_heading_12']("Home Page")
    h['add_body'](
        "Figure 9.1 displays the SupplyPrescript Operations Command Center (Home Page). The dashboard provides logistics analysts and supply chain "
        "managers with end-to-end visibility across incoming semiconductor consignments. Visible components include: (1) the shipment manifest "
        "ingestion form with fields for Tracking ID, Semiconductor Component, Quantity, Scheduled Days, and Freight Velocity; (2) the pre-transit "
        "predictive risk output panel displaying calibrated delay probability (P(Delay)) and projected delay slippage; (3) the interactive "
        "prescriptive optimization configuration sliders allowing real-time adjustment of budget cost ceilings and SLA deadlines; (4) the "
        "prescriptive decision cards detailing evaluated alternatives (Air Freight, Secondary Supplier, Accept Delay) with highlighted optimal "
        "recommendation; and (5) the live shipment history table with post-delivery outcome feedback controls."
    )
    
    home_page_img = os.path.join(r"C:\Academic Project\Supply-Prescript", "Home Page.png")
    h['add_image_figure'](home_page_img, "Figure 9.1: SupplyPrescript Operations Command Center & Prescription Interface (Home Page)", width_inches=6.2)
    
    # Screenshot 2: Login page
    h['add_heading_12']("Login page")
    h['add_body'](
        "Figure 9.2 presents the redesigned SupplyPrescript Enterprise User Login interface. The view features a balanced two-column layout conforming "
        "to modern enterprise design aesthetics: (1) the left hero panel establishes corporate branding with the headline 'Predict Disruption. Prescribe "
        "Recovery.' and introductory platform documentation; and (2) the right authentication card incorporates prominent, styled single sign-on buttons "
        "for Google and Facebook OAuth 2.0 alongside local credential sign-in fields. Unnecessary technical statistics and distracting badges have been "
        "eliminated, ensuring a distraction-free, professional enterprise login experience."
    )
    
    login_page_img = os.path.join(r"C:\Academic Project\Supply-Prescript", "Login Page.png")
    h['add_image_figure'](login_page_img, "Figure 9.2: SupplyPrescript Enterprise User Login with Google & Facebook SSO (Login page)", width_inches=6.2)
    
    # Screenshot 3: Admin Home Page
    h['add_heading_12']("Admin Home Page")
    h['add_body'](
        "Figure 9.3 illustrates the SupplyPrescript Admin Governance Portal (Admin Home Page). Accessible exclusively to authorized users with the 'admin' "
        "role, this interface provides complete governance oversight: (1) user account provisioning and profile editing; (2) Role-Based Access Control "
        "(RBAC) assignment dropdowns allowing instant modification of user roles between 'admin', 'manager', and 'analyst'; (3) account status toggle "
        "controls (Active / Disabled); (4) OAuth identity provider linkage indicators (showing Google ID and Facebook ID status); and (5) immutable "
        "system audit logs tracking user activity timestamps and security events."
    )
    
    admin_page_img = os.path.join(r"C:\Academic Project\Supply-Prescript", "Admin page.png")
    h['add_image_figure'](admin_page_img, "Figure 9.3: SupplyPrescript Admin Governance & User Management Portal (Admin Home Page)", width_inches=6.2)
    
    doc.add_page_break()
