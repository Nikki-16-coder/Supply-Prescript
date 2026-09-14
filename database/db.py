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


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with Row factory enabled for dictionary access."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite database tables if they do not exist."""
    conn = get_connection()
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

    conn.commit()
    conn.close()


# ============================================================================
# CRUD Operations
# ============================================================================

def save_shipment(data: Dict[str, Any]) -> int:
    """Inserts or updates a shipment record."""
    conn = get_connection()
    cursor = conn.cursor()
    shipment_id = str(data.get("shipment_id", "SHP001"))

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
            data.get("supplier_name", "Primary Microchip Fab"),
            data.get("component", "Microchips"),
            int(data.get("quantity", data.get("required_quantity", 5000))),
            int(data.get("scheduled_days", data.get("Days for shipment (scheduled)", 4))),
            str(data.get("shipping_mode", data.get("Shipping Mode", "Standard Class"))),
            str(data.get("customer_segment", data.get("Customer Segment", "Corporate"))),
            str(data.get("market", data.get("Market", "Pacific Asia"))),
            str(data.get("order_region", data.get("Order Region", "Southeast Asia"))),
            str(data.get("order_country", data.get("Order Country", "Taiwan"))),
        ),
    )
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def save_prediction(prediction: Dict[str, Any], model_name: str = "XGBoost Delay Classifier") -> int:
    """Stores ML delay prediction results."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO predictions (
            shipment_id, delay_probability, predicted_delay_days, model_name
        ) VALUES (?, ?, ?, ?)
        """,
        (
            str(prediction.get("shipment_id", "SHP001")),
            float(prediction.get("delay_probability", 0.0)),
            int(prediction.get("predicted_delay_days", 0)),
            model_name,
        ),
    )
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def save_optimization_decision(
    shipment_id: str,
    budget: float,
    max_delivery_days: int,
    required_quantity: int,
    supplier_capacity: int,
    optimization_result: Dict[str, Any],
    manager_decision: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    """Stores prescriptive optimization recommendation and manager decision."""
    conn = get_connection()
    cursor = conn.cursor()

    rec_action = optimization_result.get("recommended_action")
    status = optimization_result.get("status", "Unknown")
    options_json = json.dumps(optimization_result.get("options", {}))
    chosen_decision = manager_decision or rec_action

    cursor.execute(
        """
        INSERT INTO optimization_decisions (
            shipment_id, budget, max_delivery_days, required_quantity,
            supplier_capacity, recommended_action, optimization_status,
            options_evaluated, manager_decision, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(shipment_id),
            float(budget),
            int(max_delivery_days),
            int(required_quantity),
            int(supplier_capacity),
            rec_action,
            status,
            options_json,
            chosen_decision,
            notes,
        ),
    )
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def update_manager_decision(shipment_id: str, manager_decision: str, notes: Optional[str] = None) -> bool:
    """Updates the manager decision for the latest optimization record of a shipment."""
    conn = get_connection()
    cursor = conn.cursor()
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
        (manager_decision, notes, str(shipment_id)),
    )
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def save_outcome(outcome: Dict[str, Any]) -> int:
    """Records the post-shipment real-world outcome and feedback."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO outcomes (
            shipment_id, actual_delivery_days, actual_cost,
            delay_occurred, decision_effective, feedback_notes
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            str(outcome.get("shipment_id")),
            int(outcome.get("actual_delivery_days", 0)),
            float(outcome.get("actual_cost", 0.0)),
            int(outcome.get("delay_occurred", 0)),
            int(outcome.get("decision_effective", 1)),
            outcome.get("feedback_notes"),
        ),
    )
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


# ============================================================================
# Query Operations
# ============================================================================

def get_all_shipments() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shipments ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_all_decisions() -> List[Dict[str, Any]]:
    conn = get_connection()
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
    conn.close()
    return rows


def get_all_outcomes() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM outcomes ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_shipment_history(shipment_id: str) -> Dict[str, Any]:
    """Retrieves full closed-loop audit trail for a shipment."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM shipments WHERE shipment_id = ?", (shipment_id,))
    shipment = cursor.fetchone()

    cursor.execute("SELECT * FROM predictions WHERE shipment_id = ? ORDER BY id DESC", (shipment_id,))
    predictions = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM optimization_decisions WHERE shipment_id = ? ORDER BY id DESC", (shipment_id,))
    decisions = [dict(r) for r in cursor.fetchall()]
    for d in decisions:
        if d.get("options_evaluated"):
            try:
                d["options_evaluated"] = json.loads(d["options_evaluated"])
            except Exception:
                pass

    cursor.execute("SELECT * FROM outcomes WHERE shipment_id = ? ORDER BY id DESC", (shipment_id,))
    outcomes = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "shipment": dict(shipment) if shipment else None,
        "predictions": predictions,
        "decisions": decisions,
        "outcomes": outcomes,
    }


def get_analytics_summary() -> Dict[str, Any]:
    """Computes closed-loop analytics KPIs across all logged records."""
    conn = get_connection()
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

    conn.close()

    return {
        "total_shipments_tracked": total_shipments,
        "total_predictions_made": total_predictions,
        "average_delay_probability": round(avg_delay_prob, 4),
        "optimal_solutions_found": optimal_solutions,
        "action_distribution": action_distribution,
        "total_outcomes_evaluated": total_outcomes,
        "decision_effectiveness_pct": round(effectiveness_rate, 2),
    }


# Automatically initialize schema when module is imported
init_db()
