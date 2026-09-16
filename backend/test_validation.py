"""
Unit Tests for SupplyPrescript Day 2 Validation & Robustness
Validates:
1. Pydantic Schemas (valid inputs, zero/negative quantities, negative budgets, invalid SLA, negative disruption, empty shipment ID)
2. Business constraint validation (quantity > capacity infeasibility in PuLP layer)
3. PuLP Optimization parameter validation
"""

import unittest
from pydantic import ValidationError

from backend.schemas import (
    ShipmentRequest,
    LogisticsPredictionRequest,
    PrescribeRequest,
    ManagerDecisionRequest,
    OutcomeEvaluationRequest,
)
from backend.optimization import optimize_shipment


class TestDay2Validation(unittest.TestCase):

    # ========================================================================
    # 1. Pydantic Schema Validation Tests
    # ========================================================================
    def test_valid_prescribe_request(self):
        """Valid shipment and business inputs must pass schema validation."""
        req = PrescribeRequest(
            shipment_id="CHIP-TEST-001",
            required_quantity=5000,
            supplier_capacity=6000,
            budget=20000.0,
            max_delivery_days=7,
            scheduled_days=2,
            simulated_delay_days=14,
        )
        self.assertEqual(req.shipment_id, "CHIP-TEST-001")
        self.assertEqual(req.required_quantity, 5000)
        self.assertEqual(req.supplier_capacity, 6000)
        self.assertEqual(req.budget, 20000.0)
        self.assertEqual(req.max_delivery_days, 7)
        self.assertEqual(req.scheduled_days, 2)
        self.assertEqual(req.simulated_delay_days, 14)

    def test_zero_or_negative_quantity(self):
        """Zero or negative required quantity must be rejected."""
        with self.assertRaises(ValidationError):
            PrescribeRequest(shipment_id="CHIP-01", required_quantity=0)
        with self.assertRaises(ValidationError):
            PrescribeRequest(shipment_id="CHIP-01", required_quantity=-500)
        with self.assertRaises(ValidationError):
            ShipmentRequest(
                budget=20000, max_delivery_days=7, required_quantity=0,
                supplier_capacity=5000, predicted_delay_days=5
            )

    def test_invalid_supplier_capacity(self):
        """Zero or negative supplier capacity must be rejected."""
        with self.assertRaises(ValidationError):
            PrescribeRequest(shipment_id="CHIP-01", supplier_capacity=0)
        with self.assertRaises(ValidationError):
            PrescribeRequest(shipment_id="CHIP-01", supplier_capacity=-100)
        with self.assertRaises(ValidationError):
            ShipmentRequest(
                budget=20000, max_delivery_days=7, required_quantity=1000,
                supplier_capacity=0, predicted_delay_days=5
            )

    def test_invalid_budget(self):
        """Negative mitigation budget must be rejected."""
        with self.assertRaises(ValidationError):
            PrescribeRequest(shipment_id="CHIP-01", budget=-500.0)
        with self.assertRaises(ValidationError):
            ShipmentRequest(
                budget=-1.0, max_delivery_days=7, required_quantity=1000,
                supplier_capacity=2000, predicted_delay_days=5
            )

    def test_invalid_sla(self):
        """Zero or negative max delivery days (SLA) must be rejected."""
        with self.assertRaises(ValidationError):
            PrescribeRequest(shipment_id="CHIP-01", max_delivery_days=0)
        with self.assertRaises(ValidationError):
            PrescribeRequest(shipment_id="CHIP-01", max_delivery_days=-3)
        with self.assertRaises(ValidationError):
            ShipmentRequest(
                budget=10000, max_delivery_days=0, required_quantity=1000,
                supplier_capacity=2000, predicted_delay_days=5
            )

    def test_invalid_disruption_duration(self):
        """Negative simulated disruption duration must be rejected."""
        with self.assertRaises(ValidationError):
            PrescribeRequest(shipment_id="CHIP-01", simulated_delay_days=-1)
        with self.assertRaises(ValidationError):
            LogisticsPredictionRequest(shipment_id="CHIP-01", simulated_delay_days=-5)

    def test_empty_or_whitespace_shipment_id(self):
        """Empty or whitespace-only shipment IDs must be rejected."""
        with self.assertRaises(ValidationError):
            PrescribeRequest(shipment_id="")
        with self.assertRaises(ValidationError):
            PrescribeRequest(shipment_id="   ")
        with self.assertRaises(ValidationError):
            LogisticsPredictionRequest(shipment_id="")
        with self.assertRaises(ValidationError):
            ManagerDecisionRequest(shipment_id="  ", manager_decision="Air Freight")

    def test_invalid_scheduled_days(self):
        """Negative scheduled transit days must be rejected."""
        with self.assertRaises(ValidationError):
            PrescribeRequest(shipment_id="CHIP-01", scheduled_days=-2)

    # ========================================================================
    # 2. Business Constraint Validation (PuLP Optimization Layer)
    # ========================================================================
    def test_required_quantity_exceeding_supplier_capacity(self):
        """
        Business constraint: required quantity > supplier capacity
        Must return Infeasible status without raising unhandled exceptions.
        """
        result = optimize_shipment(
            budget=30000.0,
            max_delivery_days=7,
            required_quantity=7500,
            supplier_capacity=5000,
            predicted_delay_days=14,
        )
        self.assertEqual(result["status"], "Infeasible")
        self.assertIsNone(result["recommended_action"])
        self.assertIn("exceeds supplier capacity", result["message"].lower())

    def test_optimization_direct_parameter_validation(self):
        """optimize_shipment must raise ValueError on invalid numeric inputs."""
        with self.assertRaises(ValueError):
            optimize_shipment(budget=-100, max_delivery_days=7, required_quantity=1000, supplier_capacity=2000, predicted_delay_days=5)
        with self.assertRaises(ValueError):
            optimize_shipment(budget=1000, max_delivery_days=0, required_quantity=1000, supplier_capacity=2000, predicted_delay_days=5)
        with self.assertRaises(ValueError):
            optimize_shipment(budget=1000, max_delivery_days=7, required_quantity=0, supplier_capacity=2000, predicted_delay_days=5)
        with self.assertRaises(ValueError):
            optimize_shipment(budget=1000, max_delivery_days=7, required_quantity=1000, supplier_capacity=0, predicted_delay_days=5)
        with self.assertRaises(ValueError):
            optimize_shipment(budget=1000, max_delivery_days=7, required_quantity=1000, supplier_capacity=2000, predicted_delay_days=-1)

    def test_valid_optimization_workflow(self):
        """Existing valid optimization problem must find Optimal solution."""
        result = optimize_shipment(
            budget=20000.0,
            max_delivery_days=7,
            required_quantity=5000,
            supplier_capacity=6000,
            predicted_delay_days=14,
        )
        self.assertEqual(result["status"], "Optimal")
        self.assertEqual(result["recommended_action"], "Air Freight")
        self.assertIsNotNone(result.get("chosen_option"))


if __name__ == "__main__":
    unittest.main()
