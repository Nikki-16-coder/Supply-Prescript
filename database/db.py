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
from typing import Dict, Any, List, Optional

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

        # Indices for audit trail lookup performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_shipment_id ON predictions(shipment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_shipment_id ON optimization_decisions(shipment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_shipment_id ON outcomes(shipment_id)")

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


# Automatically initialize schema when module is imported
init_db()
