"""
SupplyPrescript - Database & Audit Trail Unit Test Suite
Milestone Day 5: Database CRUD, Referential Integrity, Audit Trail,
Atomic Closed-Loop Persistence, Transaction Rollback, and KPI Calculations.
"""

import os
import shutil
import tempfile
import unittest
import sqlite3

from database.db import (
    init_db,
    get_connection,
    shipment_exists,
    get_shipment,
    save_shipment,
    save_prediction,
    save_optimization_decision,
    update_manager_decision,
    save_outcome,
    save_prescribe_audit,
    get_all_shipments,
    get_all_decisions,
    get_all_outcomes,
    get_shipment_history,
    get_analytics_summary,
)


class TestDatabaseAuditTrail(unittest.TestCase):

    def setUp(self):
        """Create an isolated temporary SQLite database for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_supplyprescript.db")
        init_db(self.db_path)

    def tearDown(self):
        """Clean up the temporary directory and database file."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # ========================================================================
    # 1. Schema & Table Initialization
    # ========================================================================
    def test_schema_initialization_and_indices(self):
        """Verify that all tables and audit indices are properly created."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row["name"] for row in cursor.fetchall()}
            expected_tables = {"shipments", "predictions", "optimization_decisions", "outcomes"}
            self.assertTrue(expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}")

            # Verify indices
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indices = {row["name"] for row in cursor.fetchall()}
            expected_indices = {
                "idx_predictions_shipment_id",
                "idx_decisions_shipment_id",
                "idx_outcomes_shipment_id",
            }
            self.assertTrue(expected_indices.issubset(indices), f"Missing indices: {expected_indices - indices}")
        finally:
            conn.close()

    # ========================================================================
    # 2. Shipment CRUD & UPSERT Handling
    # ========================================================================
    def test_shipment_insert_and_retrieval(self):
        """Verify inserting a new shipment and retrieving it."""
        data = {
            "shipment_id": "CHIP-TEST-001",
            "supplier_name": "TSMC Fab 18",
            "component": "3nm AI Accelerators",
            "quantity": 5000,
            "scheduled_days": 4,
            "shipping_mode": "Second Class",
            "customer_segment": "Corporate",
            "market": "Pacific Asia",
            "order_region": "Southeast Asia",
            "order_country": "Taiwan",
        }
        shipment_id_num = save_shipment(data, db_path=self.db_path)
        self.assertIsInstance(shipment_id_num, int)
        self.assertTrue(shipment_id_num > 0)

        self.assertTrue(shipment_exists("CHIP-TEST-001", db_path=self.db_path))
        self.assertFalse(shipment_exists("CHIP-NON-EXISTENT", db_path=self.db_path))

        record = get_shipment("CHIP-TEST-001", db_path=self.db_path)
        self.assertIsNotNone(record)
        self.assertEqual(record["shipment_id"], "CHIP-TEST-001")
        self.assertEqual(record["supplier_name"], "TSMC Fab 18")
        self.assertEqual(record["quantity"], 5000)

        all_shipments = get_all_shipments(db_path=self.db_path)
        self.assertEqual(len(all_shipments), 1)
        self.assertEqual(all_shipments[0]["shipment_id"], "CHIP-TEST-001")

    def test_shipment_upsert_on_duplicate_key(self):
        """Verify that inserting duplicate shipment_id updates existing row without duplicate keys."""
        initial = {
            "shipment_id": "CHIP-UPSERT-01",
            "supplier_name": "Fab Alpha",
            "quantity": 3000,
            "scheduled_days": 3,
        }
        save_shipment(initial, db_path=self.db_path)

        updated = {
            "shipment_id": "CHIP-UPSERT-01",
            "supplier_name": "Fab Beta Updated",
            "quantity": 6000,
            "scheduled_days": 5,
        }
        save_shipment(updated, db_path=self.db_path)

        all_shipments = get_all_shipments(db_path=self.db_path)
        self.assertEqual(len(all_shipments), 1)
        record = get_shipment("CHIP-UPSERT-01", db_path=self.db_path)
        self.assertEqual(record["supplier_name"], "Fab Beta Updated")
        self.assertEqual(record["quantity"], 6000)
        self.assertEqual(record["scheduled_days"], 5)

    # ========================================================================
    # 3. Prediction CRUD & Range Validation
    # ========================================================================
    def test_prediction_crud_and_bounds(self):
        """Verify inserting prediction for an existing shipment and retrieving it."""
        save_shipment({"shipment_id": "CHIP-PRED-01", "quantity": 2000}, db_path=self.db_path)

        pred_data = {
            "shipment_id": "CHIP-PRED-01",
            "delay_probability": 0.85,
            "predicted_delay_days": 12,
        }
        pred_id = save_prediction(pred_data, model_name="XGBoost Classifier v1", db_path=self.db_path)
        self.assertIsInstance(pred_id, int)
        self.assertTrue(pred_id > 0)

        history = get_shipment_history("CHIP-PRED-01", db_path=self.db_path)
        self.assertEqual(len(history["predictions"]), 1)
        pred = history["predictions"][0]
        self.assertEqual(pred["shipment_id"], "CHIP-PRED-01")
        self.assertAlmostEqual(pred["delay_probability"], 0.85)
        self.assertEqual(pred["predicted_delay_days"], 12)
        self.assertEqual(pred["model_name"], "XGBoost Classifier v1")

    # ========================================================================
    # 4. Optimization Decision & Options JSON Deserialization
    # ========================================================================
    def test_optimization_decision_crud(self):
        """Verify saving optimization decision, options JSON storage, and retrieval."""
        save_shipment({"shipment_id": "CHIP-OPT-01", "quantity": 4000}, db_path=self.db_path)

        opt_result = {
            "status": "Optimal",
            "recommended_action": "Air Freight",
            "chosen_option": {"cost": 15000.0, "lead_time_days": 2, "capacity": 5000},
            "options": {
                "Air Freight": {"cost": 15000.0, "lead_time_days": 2, "capacity": 5000},
                "Expedited Sea": {"cost": 6000.0, "lead_time_days": 8, "capacity": 6000},
            },
        }

        dec_id = save_optimization_decision(
            shipment_id="CHIP-OPT-01",
            budget=20000.0,
            max_delivery_days=7,
            required_quantity=4000,
            supplier_capacity=6000,
            optimization_result=opt_result,
            db_path=self.db_path,
        )
        self.assertIsInstance(dec_id, int)

        decisions = get_all_decisions(db_path=self.db_path)
        self.assertEqual(len(decisions), 1)
        dec = decisions[0]
        self.assertEqual(dec["shipment_id"], "CHIP-OPT-01")
        self.assertEqual(dec["recommended_action"], "Air Freight")
        self.assertEqual(dec["manager_decision"], "Air Freight")
        self.assertEqual(dec["optimization_status"], "Optimal")
        self.assertIsInstance(dec["options_evaluated"], dict)
        self.assertIn("Air Freight", dec["options_evaluated"])

    # ========================================================================
    # 5. Manager Decision Update & Solver Recommendation Preservation
    # ========================================================================
    def test_manager_decision_update_preserves_solver_recommendation(self):
        """Verify that updating manager decision does not overwrite recommended_action."""
        save_shipment({"shipment_id": "CHIP-MGR-01"}, db_path=self.db_path)

        opt_result = {
            "status": "Optimal",
            "recommended_action": "Air Freight",
            "options": {"Air Freight": {"cost": 15000, "lead_time_days": 2}},
        }
        save_optimization_decision(
            shipment_id="CHIP-MGR-01",
            budget=20000.0,
            max_delivery_days=7,
            required_quantity=5000,
            supplier_capacity=6000,
            optimization_result=opt_result,
            db_path=self.db_path,
        )

        # Manager overrides to Production Buffer Overtime
        updated = update_manager_decision(
            shipment_id="CHIP-MGR-01",
            manager_decision="Production Buffer Overtime",
            notes="Overridden: Fab schedule allows minor buffer window.",
            db_path=self.db_path,
        )
        self.assertTrue(updated)

        # Verify audit trail: recommended_action must remain Air Freight!
        history = get_shipment_history("CHIP-MGR-01", db_path=self.db_path)
        self.assertEqual(len(history["decisions"]), 1)
        dec = history["decisions"][0]
        self.assertEqual(dec["recommended_action"], "Air Freight", "Solver recommendation was lost!")
        self.assertEqual(dec["manager_decision"], "Production Buffer Overtime")
        self.assertEqual(dec["notes"], "Overridden: Fab schedule allows minor buffer window.")

    def test_manager_decision_update_non_existent_shipment(self):
        """Updating manager decision for untracked shipment must return False."""
        updated = update_manager_decision(
            shipment_id="CHIP-DOES-NOT-EXIST",
            manager_decision="Air Freight",
            db_path=self.db_path,
        )
        self.assertFalse(updated)

    # ========================================================================
    # 6. Post-Delivery Outcome CRUD
    # ========================================================================
    def test_outcome_crud(self):
        """Verify recording post-delivery outcome and retrieving history."""
        save_shipment({"shipment_id": "CHIP-OUT-01"}, db_path=self.db_path)

        outcome_data = {
            "shipment_id": "CHIP-OUT-01",
            "actual_delivery_days": 2,
            "actual_cost": 15000.0,
            "delay_occurred": 0,
            "decision_effective": 1,
            "feedback_notes": "Delivered on schedule with no production downtime.",
        }
        outcome_id = save_outcome(outcome_data, db_path=self.db_path)
        self.assertIsInstance(outcome_id, int)
        self.assertTrue(outcome_id > 0)

        outcomes = get_all_outcomes(db_path=self.db_path)
        self.assertEqual(len(outcomes), 1)
        out = outcomes[0]
        self.assertEqual(out["shipment_id"], "CHIP-OUT-01")
        self.assertEqual(out["actual_delivery_days"], 2)
        self.assertAlmostEqual(out["actual_cost"], 15000.0)
        self.assertEqual(out["delay_occurred"], 0)
        self.assertEqual(out["decision_effective"], 1)

    # ========================================================================
    # 7. Complete Closed-Loop Audit Trail Correlation
    # ========================================================================
    def test_complete_closed_loop_lifecycle(self):
        """
        Verify full lifecycle:
        Shipment -> ML Prediction -> PuLP Recommendation -> Manager Decision -> Post-Delivery Outcome
        All entities must correctly associate with the single shipment.
        """
        shipment_id = "CHIP-FULL-LOOP-01"

        # 1. Shipment
        save_shipment(
            {"shipment_id": shipment_id, "supplier_name": "TSMC Fab 18", "quantity": 5000},
            db_path=self.db_path,
        )

        # 2. Prediction
        save_prediction(
            {"shipment_id": shipment_id, "delay_probability": 0.88, "predicted_delay_days": 14},
            db_path=self.db_path,
        )

        # 3. PuLP Decision
        save_optimization_decision(
            shipment_id=shipment_id,
            budget=25000.0,
            max_delivery_days=7,
            required_quantity=5000,
            supplier_capacity=6000,
            optimization_result={"status": "Optimal", "recommended_action": "Air Freight"},
            db_path=self.db_path,
        )

        # 4. Manager Approval
        update_manager_decision(
            shipment_id=shipment_id,
            manager_decision="Air Freight",
            notes="Approved by Operations Lead",
            db_path=self.db_path,
        )

        # 5. Realized Outcome
        save_outcome(
            {
                "shipment_id": shipment_id,
                "actual_delivery_days": 2,
                "actual_cost": 15000.0,
                "delay_occurred": 0,
                "decision_effective": 1,
                "feedback_notes": "Zero line downtime.",
            },
            db_path=self.db_path,
        )

        # Retrieve audit trail
        history = get_shipment_history(shipment_id, db_path=self.db_path)
        self.assertIsNotNone(history["shipment"])
        self.assertEqual(history["shipment"]["shipment_id"], shipment_id)
        self.assertEqual(len(history["predictions"]), 1)
        self.assertEqual(len(history["decisions"]), 1)
        self.assertEqual(len(history["outcomes"]), 1)

        self.assertEqual(history["decisions"][0]["manager_decision"], "Air Freight")
        self.assertEqual(history["outcomes"][0]["decision_effective"], 1)

    # ========================================================================
    # 8. Atomic Prescribe Audit & Transaction Rollback
    # ========================================================================
    def test_save_prescribe_audit_atomic_success(self):
        """Verify save_prescribe_audit commits shipment, prediction, and decision together."""
        res = save_prescribe_audit(
            shipment_data={"shipment_id": "CHIP-ATOMIC-01", "quantity": 4500},
            prediction_data={"shipment_id": "CHIP-ATOMIC-01", "delay_probability": 0.75, "predicted_delay_days": 10},
            shipment_id="CHIP-ATOMIC-01",
            budget=18000.0,
            max_delivery_days=7,
            required_quantity=4500,
            supplier_capacity=5000,
            optimization_result={"status": "Optimal", "recommended_action": "Air Freight"},
            db_path=self.db_path,
        )
        self.assertIn("shipment_id", res)
        self.assertIn("prediction_id", res)
        self.assertIn("decision_id", res)

        history = get_shipment_history("CHIP-ATOMIC-01", db_path=self.db_path)
        self.assertIsNotNone(history["shipment"])
        self.assertEqual(len(history["predictions"]), 1)
        self.assertEqual(len(history["decisions"]), 1)

    def test_save_prescribe_audit_rollback_on_failure(self):
        """
        Verify that if decision parameters are invalid (e.g. negative budget),
        the entire transaction rolls back, leaving no partial shipment or prediction records.
        """
        with self.assertRaises(ValueError):
            save_prescribe_audit(
                shipment_data={"shipment_id": "CHIP-ROLLBACK-01", "quantity": 3000},
                prediction_data={"shipment_id": "CHIP-ROLLBACK-01", "delay_probability": 0.8, "predicted_delay_days": 5},
                shipment_id="CHIP-ROLLBACK-01",
                budget=-5000.0,  # Invalid: negative budget!
                max_delivery_days=7,
                required_quantity=3000,
                supplier_capacity=5000,
                optimization_result={"status": "Optimal"},
                db_path=self.db_path,
            )

        # Neither shipment nor prediction should exist
        self.assertFalse(shipment_exists("CHIP-ROLLBACK-01", db_path=self.db_path))
        history = get_shipment_history("CHIP-ROLLBACK-01", db_path=self.db_path)
        self.assertIsNone(history["shipment"])
        self.assertEqual(len(history["predictions"]), 0)
        self.assertEqual(len(history["decisions"]), 0)

    # ========================================================================
    # 9. Referential Integrity (Foreign Key Enforcement)
    # ========================================================================
    def test_foreign_key_enforcement_for_predictions(self):
        """Saving a prediction for a non-existent shipment must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            save_prediction(
                {"shipment_id": "UNTRACKED-001", "delay_probability": 0.5, "predicted_delay_days": 3},
                db_path=self.db_path,
            )
        self.assertIn("does not exist", str(ctx.exception).lower())

    def test_foreign_key_enforcement_for_decisions(self):
        """Saving an optimization decision for a non-existent shipment must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            save_optimization_decision(
                shipment_id="UNTRACKED-002",
                budget=10000.0,
                max_delivery_days=7,
                required_quantity=1000,
                supplier_capacity=2000,
                optimization_result={"status": "Optimal"},
                db_path=self.db_path,
            )
        self.assertIn("does not exist", str(ctx.exception).lower())

    def test_foreign_key_enforcement_for_outcomes(self):
        """Saving an outcome for a non-existent shipment must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            save_outcome(
                {"shipment_id": "UNTRACKED-003", "actual_delivery_days": 2, "actual_cost": 5000.0},
                db_path=self.db_path,
            )
        self.assertIn("does not exist", str(ctx.exception).lower())

    # ========================================================================
    # 10. Analytics & KPI Calculations
    # ========================================================================
    def test_analytics_empty_database(self):
        """Analytics summary on empty database must return zeroed metrics without crashing."""
        summary = get_analytics_summary(db_path=self.db_path)
        self.assertEqual(summary["total_shipments_tracked"], 0)
        self.assertEqual(summary["total_predictions_made"], 0)
        self.assertEqual(summary["average_delay_probability"], 0.0)
        self.assertEqual(summary["optimal_solutions_found"], 0)
        self.assertEqual(summary["action_distribution"], {})
        self.assertEqual(summary["total_outcomes_evaluated"], 0)
        self.assertEqual(summary["decision_effectiveness_pct"], 0.0)

    def test_analytics_populated_database(self):
        """Analytics summary must accurately aggregate metrics across shipments, decisions, and outcomes."""
        # Shipment 1: Optimal Air Freight, Effective outcome
        save_shipment({"shipment_id": "KPI-01"}, db_path=self.db_path)
        save_prediction({"shipment_id": "KPI-01", "delay_probability": 0.8, "predicted_delay_days": 10}, db_path=self.db_path)
        save_optimization_decision(
            shipment_id="KPI-01", budget=20000, max_delivery_days=7, required_quantity=5000, supplier_capacity=6000,
            optimization_result={"status": "Optimal", "recommended_action": "Air Freight"},
            db_path=self.db_path,
        )
        save_outcome({"shipment_id": "KPI-01", "actual_delivery_days": 2, "actual_cost": 15000, "decision_effective": 1}, db_path=self.db_path)

        # Shipment 2: Optimal Expedited Sea, Ineffective outcome
        save_shipment({"shipment_id": "KPI-02"}, db_path=self.db_path)
        save_prediction({"shipment_id": "KPI-02", "delay_probability": 0.6, "predicted_delay_days": 6}, db_path=self.db_path)
        save_optimization_decision(
            shipment_id="KPI-02", budget=10000, max_delivery_days=10, required_quantity=3000, supplier_capacity=4000,
            optimization_result={"status": "Optimal", "recommended_action": "Expedited Sea"},
            db_path=self.db_path,
        )
        save_outcome({"shipment_id": "KPI-02", "actual_delivery_days": 9, "actual_cost": 7000, "decision_effective": 0}, db_path=self.db_path)

        # Shipment 3: Infeasible
        save_shipment({"shipment_id": "KPI-03"}, db_path=self.db_path)
        save_prediction({"shipment_id": "KPI-03", "delay_probability": 0.9, "predicted_delay_days": 14}, db_path=self.db_path)
        save_optimization_decision(
            shipment_id="KPI-03", budget=5000, max_delivery_days=3, required_quantity=8000, supplier_capacity=5000,
            optimization_result={"status": "Infeasible", "recommended_action": None},
            db_path=self.db_path,
        )

        summary = get_analytics_summary(db_path=self.db_path)
        self.assertEqual(summary["total_shipments_tracked"], 3)
        self.assertEqual(summary["total_predictions_made"], 3)
        # Average delay prob: (0.8 + 0.6 + 0.9) / 3 = 0.7667
        self.assertAlmostEqual(summary["average_delay_probability"], 0.7667, places=3)
        self.assertEqual(summary["optimal_solutions_found"], 2)
        self.assertEqual(summary["action_distribution"], {"Air Freight": 1, "Expedited Sea": 1})
        self.assertEqual(summary["total_outcomes_evaluated"], 2)
        # 1 effective out of 2 = 50.0%
        self.assertEqual(summary["decision_effectiveness_pct"], 50.0)

    # ========================================================================
    # 11. Repeated Records Handling
    # ========================================================================
    def test_repeated_predictions_and_outcomes_handled(self):
        """Verify that repeated predictions or multiple outcomes for the same shipment are tracked."""
        save_shipment({"shipment_id": "CHIP-REPEAT-01"}, db_path=self.db_path)

        # Log 2 predictions at different times
        save_prediction({"shipment_id": "CHIP-REPEAT-01", "delay_probability": 0.4, "predicted_delay_days": 3}, db_path=self.db_path)
        save_prediction({"shipment_id": "CHIP-REPEAT-01", "delay_probability": 0.85, "predicted_delay_days": 14}, db_path=self.db_path)

        # Log 2 outcome audits
        save_outcome({"shipment_id": "CHIP-REPEAT-01", "actual_delivery_days": 3, "actual_cost": 8000.0, "decision_effective": 1}, db_path=self.db_path)
        save_outcome({"shipment_id": "CHIP-REPEAT-01", "actual_delivery_days": 4, "actual_cost": 8500.0, "decision_effective": 1}, db_path=self.db_path)

        history = get_shipment_history("CHIP-REPEAT-01", db_path=self.db_path)
        self.assertEqual(len(history["predictions"]), 2)
        self.assertEqual(len(history["outcomes"]), 2)
        # Latest should appear first due to ORDER BY id DESC
        self.assertAlmostEqual(history["predictions"][0]["delay_probability"], 0.85)

    # ========================================================================
    # 12. Invalid Input & Error Handling (Safety)
    # ========================================================================
    def test_invalid_shipment_id_rejected(self):
        """Empty or whitespace-only shipment_id must be rejected in all operations."""
        with self.assertRaises(ValueError):
            save_shipment({"shipment_id": ""}, db_path=self.db_path)
        with self.assertRaises(ValueError):
            save_shipment({"shipment_id": "   "}, db_path=self.db_path)
        with self.assertRaises(ValueError):
            save_prediction({"shipment_id": ""}, db_path=self.db_path)
        with self.assertRaises(ValueError):
            save_optimization_decision(
                shipment_id="  ", budget=1000, max_delivery_days=7, required_quantity=100, supplier_capacity=200,
                optimization_result={}, db_path=self.db_path,
            )
        with self.assertRaises(ValueError):
            update_manager_decision(shipment_id="  ", manager_decision="Air Freight", db_path=self.db_path)
        with self.assertRaises(ValueError):
            save_outcome({"shipment_id": ""}, db_path=self.db_path)

    def test_invalid_numeric_values_rejected(self):
        """Out-of-range probabilities, negative costs, or non-positive quantities must raise ValueError."""
        save_shipment({"shipment_id": "CHIP-VALID-01"}, db_path=self.db_path)

        # Invalid delay probability (> 1.0 or < 0.0)
        with self.assertRaises(ValueError):
            save_prediction({"shipment_id": "CHIP-VALID-01", "delay_probability": 1.5}, db_path=self.db_path)
        with self.assertRaises(ValueError):
            save_prediction({"shipment_id": "CHIP-VALID-01", "delay_probability": -0.1}, db_path=self.db_path)

        # Negative delay days
        with self.assertRaises(ValueError):
            save_prediction({"shipment_id": "CHIP-VALID-01", "predicted_delay_days": -5}, db_path=self.db_path)

        # Negative actual cost
        with self.assertRaises(ValueError):
            save_outcome({"shipment_id": "CHIP-VALID-01", "actual_cost": -100.0}, db_path=self.db_path)

        # Negative actual delivery days
        with self.assertRaises(ValueError):
            save_outcome({"shipment_id": "CHIP-VALID-01", "actual_delivery_days": -1}, db_path=self.db_path)

        # Invalid flags
        with self.assertRaises(ValueError):
            save_outcome({"shipment_id": "CHIP-VALID-01", "delay_occurred": 5}, db_path=self.db_path)
        with self.assertRaises(ValueError):
            save_outcome({"shipment_id": "CHIP-VALID-01", "decision_effective": -1}, db_path=self.db_path)

    # ========================================================================
    # 13. Resource Cleanup & Absence of Leaked Handles
    # ========================================================================
    def test_resource_cleanup_allows_temp_deletion(self):
        """Verify that all connections are strictly closed, allowing SQLite file removal."""
        save_shipment({"shipment_id": "CHIP-CLEAN-01"}, db_path=self.db_path)
        get_all_shipments(db_path=self.db_path)
        get_analytics_summary(db_path=self.db_path)
        # Attempt to remove the SQLite database file directly
        # On Windows, open handles raise PermissionError: [WinError 32]
        try:
            os.remove(self.db_path)
            file_deleted = True
        except PermissionError:
            file_deleted = False
        self.assertTrue(file_deleted, "Database file remained locked! Connection was not closed.")


if __name__ == "__main__":
    unittest.main()
