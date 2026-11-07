"""
SupplyPrescript - SQLite Database Layer
Handles persistent storage for:
1. shipments
2. predictions
3. optimization_decisions
4. outcomes

No external APIs, cloud services, or paid dependencies required.
Uses Python built-in sqlite3.
"""

import os
import json
import sqlite3
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "supplyprescript.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns a SQLite connection with Row factory and Foreign Keys enabled."""
    target_path = db_path or os.environ.get("SUPPLYPRESCRIPT_DB_PATH") or DB_PATH
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None):
    """Initializes SQLite database tables and indices if they do not exist."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()

        # 1. shipments table
        cursor.execute(
            """
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
            )
            """
        )

        # 2. predictions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shipment_id TEXT NOT NULL,
                delay_probability REAL NOT NULL,
                predicted_delay_days INTEGER NOT NULL,
                model_name TEXT DEFAULT 'XGBoost Delay Classifier',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
            )
            """
        )

        # 3. optimization_decisions table
        cursor.execute(
            """
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
            )
            """
        )

        # 4. outcomes table
        cursor.execute(
            """
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
            )
            """
        )

        # 5. users table (Enterprise Role-Based Access Control)
        cursor.execute(
            """
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
            )
            """
        )

        # Ensure schema migrations for existing databases
        cursor.execute("PRAGMA table_info(users)")
        existing_user_cols = {row[1] for row in cursor.fetchall()}
        if "auth_provider" not in existing_user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN auth_provider TEXT DEFAULT 'local'")
        if "facebook_id" not in existing_user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN facebook_id TEXT")
        if "google_id" not in existing_user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN google_id TEXT")

        # 6. sessions table (Server-Side Session Store with Instant Revocation)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        # 7. password_resets table (Cryptographically Hashed Single-Use Reset Tokens)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        # Indices for audit trail lookup performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_shipment_id ON predictions(shipment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_shipment_id ON optimization_decisions(shipment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_shipment_id ON outcomes(shipment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_facebook_id ON users(facebook_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_auth_provider ON users(auth_provider)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_resets_token_hash ON password_resets(token_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_resets_user_id ON password_resets(user_id)")

        conn.commit()
    finally:
        conn.close()


# ============================================================================
# Utilities & Existence Checks
# ============================================================================

def shipment_exists(
    shipment_id: str,
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """Checks whether a shipment_id exists in the shipments table."""
    if not shipment_id or not str(shipment_id).strip():
        return False
    clean_id = str(shipment_id).strip()
    own_conn = conn is None
    active_conn = conn or get_connection(db_path)
    try:
        cursor = active_conn.cursor()
        cursor.execute("SELECT 1 FROM shipments WHERE shipment_id = ? LIMIT 1", (clean_id,))
        return cursor.fetchone() is not None
    finally:
        if own_conn:
            active_conn.close()


def get_shipment(
    shipment_id: str,
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieves a single shipment record as a dictionary, or None if not found."""
    if not shipment_id or not str(shipment_id).strip():
        return None
    clean_id = str(shipment_id).strip()
    own_conn = conn is None
    active_conn = conn or get_connection(db_path)
    try:
        cursor = active_conn.cursor()
        cursor.execute("SELECT * FROM shipments WHERE shipment_id = ? LIMIT 1", (clean_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if own_conn:
            active_conn.close()


# ============================================================================
# CRUD Operations
# ============================================================================

def save_shipment(
    data: Dict[str, Any],
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """
    Inserts or updates a shipment record with input validation and UPSERT conflict handling.
    Returns the database primary key ID of the shipment record.
    """
    if not isinstance(data, dict):
        raise ValueError("Shipment data must be a dictionary.")

    raw_id = data.get("shipment_id")
    if not raw_id or not str(raw_id).strip():
        raise ValueError("shipment_id is required and cannot be empty or whitespace.")
    shipment_id = str(raw_id).strip()

    raw_quantity = data.get("quantity", data.get("required_quantity", data.get("Order Item Quantity", 5000)))
    try:
        quantity = int(raw_quantity)
        if quantity <= 0:
            raise ValueError("Shipment quantity must be positive (> 0).")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid quantity '{raw_quantity}': must be a positive integer.") from exc

    raw_scheduled = data.get("scheduled_days", data.get("Days for shipment (scheduled)", 4))
    try:
        scheduled_days = int(raw_scheduled)
        if scheduled_days < 0:
            raise ValueError("scheduled_days must be non-negative (>= 0).")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid scheduled_days '{raw_scheduled}': must be a non-negative integer.") from exc

    supplier_name = str(data.get("supplier_name") or "Primary Microchip Fab")
    component = str(data.get("component") or "Microchips")
    shipping_mode = str(data.get("shipping_mode", data.get("Shipping Mode", "Standard Class")))
    customer_segment = str(data.get("customer_segment", data.get("Customer Segment", "Corporate")))
    market = str(data.get("market", data.get("Market", "Pacific Asia")))
    order_region = str(data.get("order_region", data.get("Order Region", "Southeast Asia")))
    order_country = str(data.get("order_country", data.get("Order Country", "Taiwan")))

    own_conn = conn is None
    active_conn = conn or get_connection(db_path)
    try:
        cursor = active_conn.cursor()
        cursor.execute(
            """
            INSERT INTO shipments (
                shipment_id, supplier_name, component, quantity,
                scheduled_days, shipping_mode, customer_segment,
                market, order_region, order_country
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(shipment_id) DO UPDATE SET
                supplier_name = excluded.supplier_name,
                component = excluded.component,
                quantity = excluded.quantity,
                scheduled_days = excluded.scheduled_days,
                shipping_mode = excluded.shipping_mode,
                customer_segment = excluded.customer_segment,
                market = excluded.market,
                order_region = excluded.order_region,
                order_country = excluded.order_country
            """,
            (
                shipment_id,
                supplier_name,
                component,
                quantity,
                scheduled_days,
                shipping_mode,
                customer_segment,
                market,
                order_region,
                order_country,
            ),
        )
        if own_conn:
            active_conn.commit()

        # Retrieve the deterministic record ID for the shipment_id
        cursor.execute("SELECT id FROM shipments WHERE shipment_id = ?", (shipment_id,))
        row = cursor.fetchone()
        return row["id"] if row else cursor.lastrowid
    finally:
        if own_conn:
            active_conn.close()


def save_prediction(
    prediction: Dict[str, Any],
    model_name: str = "XGBoost Delay Classifier",
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """
    Stores ML delay prediction results with validation and referential integrity check.
    Returns the database primary key ID of the inserted prediction record.
    """
    if not isinstance(prediction, dict):
        raise ValueError("Prediction data must be a dictionary.")

    raw_id = prediction.get("shipment_id")
    if not raw_id or not str(raw_id).strip():
        raise ValueError("shipment_id is required and cannot be empty or whitespace.")
    shipment_id = str(raw_id).strip()

    raw_prob = prediction.get("delay_probability", 0.0)
    try:
        delay_prob = float(raw_prob)
        if not (0.0 <= delay_prob <= 1.0):
            raise ValueError("delay_probability must be between 0.0 and 1.0.")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid delay_probability '{raw_prob}': must be between 0.0 and 1.0.") from exc

    raw_days = prediction.get("predicted_delay_days", 0)
    try:
        predicted_delay_days = int(raw_days)
        if predicted_delay_days < 0:
            raise ValueError("predicted_delay_days must be non-negative (>= 0).")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid predicted_delay_days '{raw_days}': must be a non-negative integer.") from exc

    own_conn = conn is None
    active_conn = conn or get_connection(db_path)
    try:
        cursor = active_conn.cursor()
        cursor.execute(
            """
            INSERT INTO predictions (
                shipment_id, delay_probability, predicted_delay_days, model_name
            ) VALUES (?, ?, ?, ?)
            """,
            (
                shipment_id,
                delay_prob,
                predicted_delay_days,
                model_name,
            ),
        )
        if own_conn:
            active_conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"Cannot save prediction: shipment '{shipment_id}' does not exist.") from exc
    finally:
        if own_conn:
            active_conn.close()


def save_optimization_decision(
    shipment_id: str,
    budget: float,
    max_delivery_days: int,
    required_quantity: int,
    supplier_capacity: int,
    optimization_result: Dict[str, Any],
    manager_decision: Optional[str] = None,
    notes: Optional[str] = None,
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """
    Stores prescriptive optimization recommendation and manager decision with parameter validation.
    Returns the database primary key ID of the inserted decision record.
    """
    if not shipment_id or not str(shipment_id).strip():
        raise ValueError("shipment_id is required and cannot be empty or whitespace.")
    clean_id = str(shipment_id).strip()

    if not isinstance(optimization_result, dict):
        raise ValueError("optimization_result must be a dictionary.")

    try:
        budget_val = float(budget)
        if budget_val < 0.0:
            raise ValueError("budget must be non-negative (>= 0).")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid budget '{budget}': must be non-negative.") from exc

    try:
        sla_val = int(max_delivery_days)
        if sla_val <= 0:
            raise ValueError("max_delivery_days must be positive (> 0).")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid max_delivery_days '{max_delivery_days}': must be positive.") from exc

    try:
        qty_val = int(required_quantity)
        if qty_val <= 0:
            raise ValueError("required_quantity must be positive (> 0).")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid required_quantity '{required_quantity}': must be positive.") from exc

    try:
        cap_val = int(supplier_capacity)
        if cap_val <= 0:
            raise ValueError("supplier_capacity must be positive (> 0).")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid supplier_capacity '{supplier_capacity}': must be positive.") from exc

    rec_action = optimization_result.get("recommended_action")
    status = optimization_result.get("status", "Unknown")
    options_json = json.dumps(optimization_result.get("options", {}))
    chosen_decision = manager_decision or rec_action

    own_conn = conn is None
    active_conn = conn or get_connection(db_path)
    try:
        cursor = active_conn.cursor()
        cursor.execute(
            """
            INSERT INTO optimization_decisions (
                shipment_id, budget, max_delivery_days, required_quantity,
                supplier_capacity, recommended_action, optimization_status,
                options_evaluated, manager_decision, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clean_id,
                budget_val,
                sla_val,
                qty_val,
                cap_val,
                rec_action,
                status,
                options_json,
                chosen_decision,
                notes,
            ),
        )
        if own_conn:
            active_conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"Cannot save optimization decision: shipment '{clean_id}' does not exist.") from exc
    finally:
        if own_conn:
            active_conn.close()


def update_manager_decision(
    shipment_id: str,
    manager_decision: str,
    notes: Optional[str] = None,
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """
    Updates the manager decision for the latest optimization record of a shipment.
    Preserves original solver recommendation while logging manager choice and rationale.
    Returns True if an existing decision record was updated, False otherwise.
    """
    if not shipment_id or not str(shipment_id).strip():
        raise ValueError("shipment_id is required and cannot be empty or whitespace.")
    clean_id = str(shipment_id).strip()

    if not manager_decision or not str(manager_decision).strip():
        raise ValueError("manager_decision is required and cannot be empty or whitespace.")
    clean_decision = str(manager_decision).strip()

    own_conn = conn is None
    active_conn = conn or get_connection(db_path)
    try:
        cursor = active_conn.cursor()
        cursor.execute(
            """
            UPDATE optimization_decisions
            SET manager_decision = ?, notes = coalesce(?, notes)
            WHERE id = (
                SELECT id FROM optimization_decisions
                WHERE shipment_id = ?
                ORDER BY id DESC LIMIT 1
            )
            """,
            (clean_decision, notes, clean_id),
        )
        rows_affected = cursor.rowcount
        if own_conn:
            active_conn.commit()
        return rows_affected > 0
    finally:
        if own_conn:
            active_conn.close()


def save_outcome(
    outcome: Dict[str, Any],
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """
    Records the post-shipment real-world outcome and feedback with validation.
    Returns the database primary key ID of the inserted outcome record.
    """
    if not isinstance(outcome, dict):
        raise ValueError("Outcome data must be a dictionary.")

    raw_id = outcome.get("shipment_id")
    if not raw_id or not str(raw_id).strip():
        raise ValueError("shipment_id is required and cannot be empty or whitespace.")
    shipment_id = str(raw_id).strip()

    raw_days = outcome.get("actual_delivery_days", 0)
    try:
        actual_delivery_days = int(raw_days)
        if actual_delivery_days < 0:
            raise ValueError("actual_delivery_days must be non-negative (>= 0).")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid actual_delivery_days '{raw_days}': must be a non-negative integer.") from exc

    raw_cost = outcome.get("actual_cost", 0.0)
    try:
        actual_cost = float(raw_cost)
        if actual_cost < 0.0:
            raise ValueError("actual_cost must be non-negative (>= 0.0).")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid actual_cost '{raw_cost}': must be non-negative.") from exc

    delay_occurred = int(outcome.get("delay_occurred", 0))
    if delay_occurred not in (0, 1):
        raise ValueError("delay_occurred must be 0 or 1.")

    decision_effective = int(outcome.get("decision_effective", 1))
    if decision_effective not in (0, 1):
        raise ValueError("decision_effective must be 0 or 1.")

    feedback_notes = outcome.get("feedback_notes")

    own_conn = conn is None
    active_conn = conn or get_connection(db_path)
    try:
        cursor = active_conn.cursor()
        cursor.execute(
            """
            INSERT INTO outcomes (
                shipment_id, actual_delivery_days, actual_cost,
                delay_occurred, decision_effective, feedback_notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                shipment_id,
                actual_delivery_days,
                actual_cost,
                delay_occurred,
                decision_effective,
                feedback_notes,
            ),
        )
        if own_conn:
            active_conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"Cannot save outcome: shipment '{shipment_id}' does not exist.") from exc
    finally:
        if own_conn:
            active_conn.close()


def save_prescribe_audit(
    shipment_data: Dict[str, Any],
    prediction_data: Dict[str, Any],
    shipment_id: str,
    budget: float,
    max_delivery_days: int,
    required_quantity: int,
    supplier_capacity: int,
    optimization_result: Dict[str, Any],
    manager_decision: Optional[str] = None,
    notes: Optional[str] = None,
    model_name: str = "XGBoost Delay Classifier",
    db_path: Optional[str] = None,
) -> Dict[str, int]:
    """
    Atomically persists shipment, prediction, and optimization decision
    in a single SQLite transaction.
    If any operation fails, the entire transaction is rolled back, preventing partial records.
    """
    conn = get_connection(db_path)
    try:
        with conn:
            shipment_row_id = save_shipment(shipment_data, conn=conn)
            pred_row_id = save_prediction(prediction_data, model_name=model_name, conn=conn)
            opt_row_id = save_optimization_decision(
                shipment_id=shipment_id,
                budget=budget,
                max_delivery_days=max_delivery_days,
                required_quantity=required_quantity,
                supplier_capacity=supplier_capacity,
                optimization_result=optimization_result,
                manager_decision=manager_decision,
                notes=notes,
                conn=conn,
            )
        return {
            "shipment_id": shipment_row_id,
            "prediction_id": pred_row_id,
            "decision_id": opt_row_id,
        }
    finally:
        conn.close()


# ============================================================================
# Query Operations
# ============================================================================

def get_all_shipments(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shipments ORDER BY id DESC")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_all_decisions(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM optimization_decisions ORDER BY id DESC")
        rows = []
        for r in cursor.fetchall():
            d = dict(r)
            if d.get("options_evaluated"):
                try:
                    d["options_evaluated"] = json.loads(d["options_evaluated"])
                except Exception:
                    pass
            rows.append(d)
        return rows
    finally:
        conn.close()


def get_all_outcomes(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM outcomes ORDER BY id DESC")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_shipment_history(shipment_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves full closed-loop audit trail for a shipment."""
    clean_id = str(shipment_id).strip() if shipment_id else ""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM shipments WHERE shipment_id = ?", (clean_id,))
        shipment = cursor.fetchone()

        cursor.execute("SELECT * FROM predictions WHERE shipment_id = ? ORDER BY id DESC", (clean_id,))
        predictions = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM optimization_decisions WHERE shipment_id = ? ORDER BY id DESC", (clean_id,))
        decisions = [dict(r) for r in cursor.fetchall()]
        for d in decisions:
            if d.get("options_evaluated"):
                try:
                    d["options_evaluated"] = json.loads(d["options_evaluated"])
                except Exception:
                    pass

        cursor.execute("SELECT * FROM outcomes WHERE shipment_id = ? ORDER BY id DESC", (clean_id,))
        outcomes = [dict(r) for r in cursor.fetchall()]

        return {
            "shipment": dict(shipment) if shipment else None,
            "predictions": predictions,
            "decisions": decisions,
            "outcomes": outcomes,
        }
    finally:
        conn.close()


def get_analytics_summary(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Computes closed-loop analytics KPIs across all logged records."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM shipments")
        total_shipments = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(delay_probability) FROM predictions")
        avg_delay_prob = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT COUNT(*) FROM optimization_decisions WHERE optimization_status = 'Optimal'")
        optimal_solutions = cursor.fetchone()[0]

        cursor.execute("SELECT recommended_action, COUNT(*) as count FROM optimization_decisions GROUP BY recommended_action")
        action_distribution = {r["recommended_action"]: r["count"] for r in cursor.fetchall() if r["recommended_action"]}

        cursor.execute("SELECT COUNT(*), AVG(decision_effective) FROM outcomes")
        outcomes_row = cursor.fetchone()
        total_outcomes = outcomes_row[0]
        effectiveness_rate = (outcomes_row[1] or 0.0) * 100

        return {
            "total_shipments_tracked": total_shipments,
            "total_predictions_made": total_predictions,
            "average_delay_probability": round(avg_delay_prob, 4),
            "optimal_solutions_found": optimal_solutions,
            "action_distribution": action_distribution,
            "total_outcomes_evaluated": total_outcomes,
            "decision_effectiveness_pct": round(effectiveness_rate, 2),
        }
    finally:
        conn.close()


# ============================================================================
# User Authentication & Session Management (PBKDF2 & SQLite Session Store)
# ============================================================================
PBKDF2_ITERATIONS = 200_000


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Computes cryptographic PBKDF2-HMAC-SHA256 password hash using a secure random salt.
    Returns (hex_hash, hex_salt).
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=PBKDF2_ITERATIONS,
    )
    return key.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    Constant-time comparison of candidate password against stored PBKDF2 hash.
    Mitigates timing attacks using secrets.compare_digest.
    """
    if not password or not password_hash or not salt:
        return False
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=PBKDF2_ITERATIONS,
    )
    return secrets.compare_digest(key.hex(), password_hash)


def create_user(
    username: str,
    email: str,
    password: str,
    role: str = "analyst",
    full_name: Optional[str] = None,
    auth_provider: str = "local",
    facebook_id: Optional[str] = None,
    google_id: Optional[str] = None,
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """
    Creates a new user with secure password hash and assigned enterprise role.
    Allowed roles: 'admin', 'manager', 'analyst'.
    """
    if not username or not username.strip():
        raise ValueError("Username cannot be empty or whitespace.")
    clean_username = username.strip().lower()

    if not email or "@" not in email or not email.strip():
        raise ValueError("Valid email address is required.")
    clean_email = email.strip().lower()

    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")

    valid_roles = ("admin", "manager", "analyst")
    clean_role = role.strip().lower() if role else "analyst"
    if clean_role not in valid_roles:
        raise ValueError(f"Invalid role '{role}'. Allowed roles: {', '.join(valid_roles)}")

    pwd_hash, salt = hash_password(password)
    clean_provider = (auth_provider or "local").strip().lower()

    own_conn = conn is None
    active_conn = conn or get_connection(db_path)
    try:
        cursor = active_conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, salt, role, full_name, is_active, auth_provider, facebook_id, google_id)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (
                clean_username,
                clean_email,
                pwd_hash,
                salt,
                clean_role,
                full_name or clean_username.title(),
                clean_provider,
                str(facebook_id).strip() if facebook_id else None,
                str(google_id).strip() if google_id else None,
            ),
        )
        if own_conn:
            active_conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"User with username '{clean_username}' or email '{clean_email}' already exists.") from exc
    finally:
        if own_conn:
            active_conn.close()


def get_user_by_username_or_email(
    identifier: str,
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieves user record by username or email (case-insensitive)."""
    if not identifier or not identifier.strip():
        return None
    clean_id = identifier.strip().lower()

    own_conn = conn is None
    active_conn = conn or get_connection(db_path)
    try:
        cursor = active_conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, password_hash, salt, role, full_name, is_active,
                   auth_provider, facebook_id, google_id, created_at, last_login
            FROM users
            WHERE lower(username) = ? OR lower(email) = ?
            LIMIT 1
            """,
            (clean_id, clean_id),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if own_conn:
            active_conn.close()


def get_user_by_id(
    user_id: int,
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieves sanitized user profile by primary key ID."""
    own_conn = conn is None
    active_conn = conn or get_connection(db_path)
    try:
        cursor = active_conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, role, full_name, is_active,
                   auth_provider, facebook_id, google_id, created_at, last_login
            FROM users
            WHERE id = ? LIMIT 1
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if own_conn:
            active_conn.close()


def get_user_by_facebook_id(
    facebook_id: str,
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieves user record by unique Facebook ID."""
    if not facebook_id or not str(facebook_id).strip():
        return None
    clean_fb_id = str(facebook_id).strip()

    own_conn = conn is None
    active_conn = conn or get_connection(db_path)
    try:
        cursor = active_conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, password_hash, salt, role, full_name, is_active,
                   auth_provider, facebook_id, google_id, created_at, last_login
            FROM users
            WHERE facebook_id = ?
            LIMIT 1
            """,
            (clean_fb_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if own_conn:
            active_conn.close()


def get_user_by_google_id(
    google_id: str,
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieves user record by unique Google ID / Subject."""
    if not google_id or not str(google_id).strip():
        return None
    clean_g_id = str(google_id).strip()

    own_conn = conn is None
    active_conn = conn or get_connection(db_path)
    try:
        cursor = active_conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, password_hash, salt, role, full_name, is_active,
                   auth_provider, facebook_id, google_id, created_at, last_login
            FROM users
            WHERE google_id = ?
            LIMIT 1
            """,
            (clean_g_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if own_conn:
            active_conn.close()


def link_user_oauth(
    user_id: int,
    provider: str,
    provider_user_id: str,
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """
    Safely links an OAuth provider ID (facebook_id or google_id) to an existing user.
    Also ensures the auth_provider column reflects the linked status.
    """
    if not user_id or not provider or not provider_user_id:
        return False

    clean_provider = provider.strip().lower()
    clean_pid = str(provider_user_id).strip()

    own_conn = conn is None
    active_conn = conn or get_connection(db_path)
    try:
        cursor = active_conn.cursor()
        if clean_provider == "facebook":
            cursor.execute(
                """
                UPDATE users
                SET facebook_id = ?,
                    auth_provider = CASE WHEN auth_provider IS NULL OR auth_provider = 'local' THEN 'facebook' ELSE auth_provider END,
                    last_login = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (clean_pid, user_id),
            )
        elif clean_provider == "google":
            cursor.execute(
                """
                UPDATE users
                SET google_id = ?,
                    auth_provider = CASE WHEN auth_provider IS NULL OR auth_provider = 'local' THEN 'google' ELSE auth_provider END,
                    last_login = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (clean_pid, user_id),
            )
        else:
            return False

        if own_conn:
            active_conn.commit()
        return cursor.rowcount > 0
    finally:
        if own_conn:
            active_conn.close()
        if own_conn:
            active_conn.close()


def authenticate_user(
    username_or_email: str,
    password: str,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Authenticates candidate credentials against database.
    Returns sanitized user profile dict if valid, or None if authentication fails.
    """
    user = get_user_by_username_or_email(username_or_email, db_path=db_path)
    if not user:
        return None
    if not user.get("is_active", 1):
        return None

    # Cryptographic verification: candidate password against stored PBKDF2 hash
    if not verify_password(password, user["password_hash"], user["salt"]):
        return None

    # Update last login timestamp
    conn = get_connection(db_path)
    try:
        conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
        conn.commit()
    finally:
        conn.close()

    # Return sanitized user record (exclude password_hash and salt)
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "full_name": user["full_name"],
        "is_active": user["is_active"],
    }


def create_session(
    user_id: int,
    duration_hours: int = 24,
    db_path: Optional[str] = None,
) -> str:
    """
    Generates a cryptographically secure random session token and stores it in SQLite.
    Returns the session token string.
    """
    session_token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=duration_hours)).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions (user_id, session_token, expires_at, is_active)
            VALUES (?, ?, ?, 1)
            """,
            (user_id, session_token, expires_at),
        )
        conn.commit()
        return session_token
    finally:
        conn.close()


def get_session_user(
    session_token: str,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Validates a session token against active sessions.
    Returns the user profile if active and unexpired, None otherwise.
    """
    if not session_token or not session_token.strip():
        return None
    clean_token = session_token.strip()

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            SELECT u.id, u.username, u.email, u.role, u.full_name, u.is_active,
                   u.auth_provider, u.facebook_id, u.google_id,
                   s.session_token, s.expires_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = ?
              AND s.is_active = 1
              AND s.expires_at > ?
              AND u.is_active = 1
            LIMIT 1
            """,
            (clean_token, now_str),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def revoke_session(
    session_token: str,
    db_path: Optional[str] = None,
) -> bool:
    """Invalidates an active session token (instant logout)."""
    if not session_token:
        return False
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET is_active = 0 WHERE session_token = ?",
            (session_token.strip(),),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def revoke_all_user_sessions(
    user_id: int,
    db_path: Optional[str] = None,
) -> int:
    """Invalidates all sessions for a specific user ID."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET is_active = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def create_password_reset_token(
    user_id: int,
    duration_minutes: int = 15,
    db_path: Optional[str] = None,
) -> str:
    """
    Generates a cryptographically secure, single-use password reset token.
    Stores the SHA-256 hash of the token with a 15-minute expiration timestamp.
    Invalidates any previous unused tokens for the specified user.
    Returns the unhashed raw token string for dispatch (never persisted in plain text).
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        # Invalidate existing unused tokens for this user
        cursor.execute(
            "UPDATE password_resets SET used = 1 WHERE user_id = ? AND used = 0",
            (user_id,),
        )
        cursor.execute(
            """
            INSERT INTO password_resets (user_id, token_hash, expires_at, used)
            VALUES (?, ?, ?, 0)
            """,
            (user_id, token_hash, expires_at),
        )
        conn.commit()
        return raw_token
    finally:
        conn.close()


def verify_password_reset_token(
    raw_token: str,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Verifies that a password reset token exists, is unused, is unexpired, and belongs to an active user.
    Returns the reset record with user metadata if valid, or None.
    """
    if not raw_token or not raw_token.strip():
        return None
    token_hash = hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pr.id, pr.user_id, pr.expires_at, pr.used,
                   u.username, u.email, u.role, u.is_active
            FROM password_resets pr
            JOIN users u ON pr.user_id = u.id
            WHERE pr.token_hash = ?
              AND pr.used = 0
              AND pr.expires_at > ?
              AND u.is_active = 1
            LIMIT 1
            """,
            (token_hash, now_str),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def complete_password_reset(
    raw_token: str,
    new_password: str,
    db_path: Optional[str] = None,
) -> bool:
    """
    Applies the new password for a valid reset token.
    Invalidates the reset token (marks used = 1) and revokes all active sessions for that user.
    Returns True if the reset was successful, False otherwise.
    """
    if not new_password or len(new_password) < 6:
        return False
    record = verify_password_reset_token(raw_token, db_path=db_path)
    if not record:
        return False

    user_id = record["user_id"]
    token_hash = hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()
    pwd_hash, salt = hash_password(new_password)

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
            (pwd_hash, salt, user_id),
        )
        cursor.execute(
            "UPDATE password_resets SET used = 1 WHERE token_hash = ?",
            (token_hash,),
        )
        conn.commit()
    finally:
        conn.close()

    # Revoke all active sessions for security so user logs in cleanly with new credentials
    revoke_all_user_sessions(user_id, db_path=db_path)
    return True


def list_all_users(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns list of all users with sensitive hash/salt redacted."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, role, full_name, is_active,
                   auth_provider, facebook_id, google_id, created_at, last_login
            FROM users
            ORDER BY id ASC
            """
        )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def count_users(db_path: Optional[str] = None) -> int:
    """Returns the total number of registered users."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def update_user_status(user_id: int, is_active: int, db_path: Optional[str] = None) -> bool:
    """Updates user active status. Revokes active sessions if deactivated."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id))
        conn.commit()
        updated = cursor.rowcount > 0
        if updated and not is_active:
            revoke_all_user_sessions(user_id, db_path=db_path)
        return updated
    finally:
        conn.close()


def update_user_role(user_id: int, role: str, db_path: Optional[str] = None) -> bool:
    """Updates assigned role for a user. Valid roles: admin, manager, analyst."""
    valid_roles = ("admin", "manager", "analyst")
    clean_role = role.strip().lower() if role else "analyst"
    if clean_role not in valid_roles:
        raise ValueError(f"Invalid role '{role}'. Allowed roles: {', '.join(valid_roles)}")
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (clean_role, user_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_user(user_id: int, db_path: Optional[str] = None) -> bool:
    """Deletes a user record by ID. Deletes associated sessions automatically via cascade."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_system_db_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves operational table counts and storage telemetry for admin diagnostics."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM shipments")
        shipments_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM predictions")
        predictions_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM optimization_decisions")
        decisions_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM outcomes")
        outcomes_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1")
        active_sessions = cursor.fetchone()[0]

        target_path = db_path or os.environ.get("SUPPLYPRESCRIPT_DB_PATH") or DB_PATH
        size_bytes = os.path.getsize(target_path) if os.path.exists(target_path) else 0

        return {
            "database_file": os.path.basename(target_path),
            "database_path": target_path,
            "database_size_bytes": size_bytes,
            "database_size_kb": round(size_bytes / 1024, 2),
            "shipments_count": shipments_count,
            "predictions_count": predictions_count,
            "decisions_count": decisions_count,
            "outcomes_count": outcomes_count,
            "users_count": users_count,
            "active_sessions_count": active_sessions,
        }
    finally:
        conn.close()


def seed_default_users_if_empty(db_path: Optional[str] = None) -> None:
    """
    Seeds and ensures initial enterprise demonstration accounts exist in the SQLite database:
    - admin: Executive Administrator (role: admin, default pwd: Admin@123)
    - manager: Supply Chain Manager (role: manager, default pwd: Manager@123)
    - analyst: Logistics Analyst (role: analyst, default pwd: Analyst@123)
    Password can be overridden via environment variables:
    - SUPPLYPRESCRIPT_ADMIN_PASSWORD / ADMIN_PASSWORD
    - SUPPLYPRESCRIPT_MANAGER_PASSWORD
    - SUPPLYPRESCRIPT_ANALYST_PASSWORD
    """
    admin_pwd = os.environ.get("SUPPLYPRESCRIPT_ADMIN_PASSWORD") or os.environ.get("ADMIN_PASSWORD") or "Admin@123"
    manager_pwd = os.environ.get("SUPPLYPRESCRIPT_MANAGER_PASSWORD") or "Manager@123"
    analyst_pwd = os.environ.get("SUPPLYPRESCRIPT_ANALYST_PASSWORD") or "Analyst@123"

    demo_accounts = [
        ("admin", "admin@supplyprescript.corp", admin_pwd, "admin", "Executive Administrator"),
        ("manager", "manager@supplyprescript.corp", manager_pwd, "manager", "Supply Chain Manager"),
        ("analyst", "analyst@supplyprescript.corp", analyst_pwd, "analyst", "Logistics Analyst"),
    ]

    for uname, email, pwd, role, full_name in demo_accounts:
        user = get_user_by_username_or_email(uname, db_path=db_path)
        if not user:
            try:
                create_user(
                    username=uname,
                    email=email,
                    password=pwd,
                    role=role,
                    full_name=full_name,
                    db_path=db_path,
                )
            except Exception as exc:
                print(f"User seeding notice for {uname}: {exc}")
        else:
            # If demo account exists, ensure it is active and its stored hash verifies against preset
            needs_pwd_sync = not verify_password(pwd, user["password_hash"], user["salt"])
            is_deactivated = not user.get("is_active", 1)
            if needs_pwd_sync or is_deactivated:
                pwd_hash, salt = hash_password(pwd)
                conn = get_connection(db_path)
                try:
                    conn.execute(
                        "UPDATE users SET password_hash = ?, salt = ?, is_active = 1 WHERE id = ?",
                        (pwd_hash, salt, user["id"]),
                    )
                    conn.commit()
                finally:
                    conn.close()


# Automatically initialize schema and seed default users when module is imported
init_db()
seed_default_users_if_empty()
