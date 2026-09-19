"""
SupplyPrescript - Machine Learning Pipeline Reliability Test Suite
Milestone Day 4: ML Reliability, Loading, Preprocessing Consistency,
Leakage Prevention, and Contract Verification.
"""

import os
import shutil
import tempfile
import unittest
import numpy as np

from ml.preprocess import (
    APPROVED_NUMERICAL_FEATURES,
    APPROVED_CATEGORICAL_FEATURES,
    APPROVED_FEATURES,
    FORBIDDEN_LEAKAGE_COLUMNS,
    MODELS_DIR,
)
from ml.predict import (
    DelayPredictor,
    get_predictor,
    reset_predictor,
    predict_shipment,
)


class TestMLPipelineReliability(unittest.TestCase):

    def setUp(self):
        # Ensure a clean singleton instance for each test
        reset_predictor()

    def tearDown(self):
        reset_predictor()

    # ========================================================================
    # 1. Model Artifact Loading Tests
    # ========================================================================
    def test_artifact_loading_success(self):
        """Verify that preprocessor, classifier, and regressor artifacts load correctly."""
        predictor = DelayPredictor(models_dir=MODELS_DIR)
        self.assertIsNotNone(predictor.preprocessor, "Preprocessor should not be None")
        self.assertIsNotNone(predictor.classifier, "Classifier should not be None")
        self.assertIsNotNone(predictor.regressor, "Regressor should not be None")

    def test_missing_artifact_raises_file_not_found(self):
        """Verify that pointing to a non-existent directory raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as empty_dir:
            with self.assertRaises(FileNotFoundError) as ctx:
                DelayPredictor(models_dir=empty_dir)
            self.assertIn("not found", str(ctx.exception).lower())

    def test_corrupted_artifact_raises_runtime_error(self):
        """Verify that corrupted or invalid artifact files raise a clear RuntimeError."""
        with tempfile.TemporaryDirectory() as corrupt_dir:
            # Create a 0-byte corrupt preprocessor file
            preprocessor_path = os.path.join(corrupt_dir, "preprocessor.joblib")
            with open(preprocessor_path, "wb") as f:
                f.write(b"CORRUPTED_BINARY_DATA_NOT_A_VALID_JOBLIB")

            classifier_path = os.path.join(corrupt_dir, "xgb_classifier.joblib")
            with open(classifier_path, "wb") as f:
                f.write(b"CORRUPTED_CLASSIFIER")

            with self.assertRaises(RuntimeError) as ctx:
                DelayPredictor(models_dir=corrupt_dir)
            self.assertIn("failed to load", str(ctx.exception).lower())

    def test_singleton_reset(self):
        """Verify reset_predictor() properly clears singleton cache."""
        p1 = get_predictor()
        self.assertIsNotNone(p1)
        reset_predictor()
        p2 = get_predictor()
        self.assertIsNotNone(p2)
        self.assertIsNot(p1, p2)

    # ========================================================================
    # 2. Valid Prediction & Contract Tests
    # ========================================================================
    def test_high_risk_disruption_prediction(self):
        """Verify prediction for high-risk microchip shipment with simulated disruption."""
        sample_high_risk = {
            "shipment_id": "CHIP-TEST-HIGH-01",
            "Days for shipment (scheduled)": 2,
            "Shipping Mode": "Second Class",
            "Order Item Quantity": 5000,
            "Order Item Product Price": 45.0,
            "Order Item Discount": 5.0,
            "Order Item Discount Rate": 0.1,
            "Customer Segment": "Corporate",
            "Market": "Pacific Asia",
            "Order Region": "Southeast Asia",
            "Order Country": "Taiwan",
            "Category Name": "Technology",
            "Department Name": "Technology",
            "Product Price": 45.0,
            "simulated_delay_days": 14,
        }
        res = predict_shipment(sample_high_risk)
        self.assertEqual(res["shipment_id"], "CHIP-TEST-HIGH-01")
        self.assertIsInstance(res["delay_probability"], float)
        self.assertTrue(0.0 <= res["delay_probability"] <= 1.0)
        self.assertIsInstance(res["predicted_delay_days"], int)
        self.assertTrue(res["predicted_delay_days"] >= 0)
        # In a high-risk disruption scenario (prob >= 0.5), simulated days must be honored
        if res["delay_probability"] >= 0.5:
            self.assertEqual(res["predicted_delay_days"], 14)

    def test_standard_shipment_prediction(self):
        """Verify prediction for standard First Class shipment without explicit disruption."""
        sample_standard = {
            "shipment_id": "CHIP-TEST-STD-02",
            "Days for shipment (scheduled)": 1,
            "Shipping Mode": "First Class",
            "Order Item Quantity": 2500,
            "Order Item Product Price": 50.0,
            "Order Item Discount": 0.0,
            "Order Item Discount Rate": 0.0,
            "Customer Segment": "Consumer",
            "Market": "USCA",
            "Order Region": "US",
            "Order Country": "United States",
            "Category Name": "Electronics",
            "Department Name": "Technology",
            "Product Price": 50.0,
        }
        res = predict_shipment(sample_standard)
        self.assertEqual(res["shipment_id"], "CHIP-TEST-STD-02")
        self.assertIsInstance(res["delay_probability"], float)
        self.assertTrue(0.0 <= res["delay_probability"] <= 1.0)
        self.assertIsInstance(res["predicted_delay_days"], int)
        self.assertTrue(res["predicted_delay_days"] >= 0)

    def test_default_feature_imputation(self):
        """Verify that missing optional features are imputed using sensible defaults."""
        minimal_input = {
            "shipment_id": "CHIP-MINIMAL-01",
            "Shipping Mode": "Standard Class",
        }
        res = predict_shipment(minimal_input)
        self.assertEqual(res["shipment_id"], "CHIP-MINIMAL-01")
        self.assertIsInstance(res["delay_probability"], float)
        self.assertIsInstance(res["predicted_delay_days"], int)

    # ========================================================================
    # 3. Preprocessing Consistency & Normalization Tests
    # ========================================================================
    def test_underscore_alias_mapping(self):
        """Verify that snake_case aliases are properly mapped to model feature names."""
        snake_case_input = {
            "shipment_id": "CHIP-ALIAS-01",
            "shipping_mode": "Standard Class",
            "customer_segment": "Corporate",
            "order_item_quantity": 3000,
            "order_item_product_price": 60.0,
        }
        res = predict_shipment(snake_case_input)
        self.assertEqual(res["shipment_id"], "CHIP-ALIAS-01")
        self.assertTrue(0.0 <= res["delay_probability"] <= 1.0)

    def test_unseen_categorical_levels_handled_gracefully(self):
        """Verify that unseen categorical levels do not cause crashes (handle_unknown='ignore')."""
        novel_input = {
            "shipment_id": "CHIP-NOVEL-01",
            "Shipping Mode": "Hypersonic Drone Shuttle",
            "Market": "Interplanetary Mars Hub",
            "Order Country": "Moon Colony Alpha",
            "Category Name": "Quantum Cryocoolers",
        }
        res = predict_shipment(novel_input)
        self.assertEqual(res["shipment_id"], "CHIP-NOVEL-01")
        self.assertIsInstance(res["delay_probability"], float)
        self.assertIsInstance(res["predicted_delay_days"], int)

    def test_approved_feature_ordering(self):
        """Confirm approved features list contains 13 unique non-leaking features."""
        self.assertEqual(len(APPROVED_FEATURES), 13)
        self.assertEqual(len(APPROVED_NUMERICAL_FEATURES), 6)
        self.assertEqual(len(APPROVED_CATEGORICAL_FEATURES), 7)
        for forbidden in FORBIDDEN_LEAKAGE_COLUMNS:
            self.assertNotIn(forbidden, APPROVED_FEATURES)

    # ========================================================================
    # 4. Data Leakage Prevention & Error Handling Tests
    # ========================================================================
    def test_reject_non_dict_input(self):
        """Verify that passing non-dict input raises TypeError."""
        with self.assertRaises(TypeError):
            predict_shipment(None)
        with self.assertRaises(TypeError):
            predict_shipment("invalid_string_input")
        with self.assertRaises(TypeError):
            predict_shipment([1, 2, 3])

    def test_reject_data_leakage_columns(self):
        """Verify that attempting to supply post-transit outcome columns raises ValueError."""
        # Exact column name
        with self.assertRaises(ValueError) as ctx:
            predict_shipment({
                "shipment_id": "LEAK-01",
                "Days for shipping (real)": 5,
            })
        self.assertIn("DATA LEAKAGE ERROR", str(ctx.exception))

        # Another forbidden column
        with self.assertRaises(ValueError) as ctx:
            predict_shipment({
                "shipment_id": "LEAK-02",
                "Delivery Status": "Late delivery",
            })
        self.assertIn("DATA LEAKAGE ERROR", str(ctx.exception))

        # Normalized snake_case forbidden column
        with self.assertRaises(ValueError) as ctx:
            predict_shipment({
                "shipment_id": "LEAK-03",
                "delivery_status": "Advance shipping",
            })
        self.assertIn("DATA LEAKAGE ERROR", str(ctx.exception))

    def test_reject_negative_scheduled_days(self):
        """Verify that negative scheduled days is rejected."""
        with self.assertRaises(ValueError) as ctx:
            predict_shipment({
                "shipment_id": "ERR-01",
                "Days for shipment (scheduled)": -3,
            })
        self.assertIn("non-negative", str(ctx.exception).lower())

    def test_reject_non_positive_quantity(self):
        """Verify that zero or negative order quantity is rejected."""
        with self.assertRaises(ValueError) as ctx:
            predict_shipment({
                "shipment_id": "ERR-02",
                "Order Item Quantity": 0,
            })
        self.assertIn("positive", str(ctx.exception).lower())

        with self.assertRaises(ValueError) as ctx:
            predict_shipment({
                "shipment_id": "ERR-02b",
                "Order Item Quantity": -100,
            })
        self.assertIn("positive", str(ctx.exception).lower())

    def test_reject_negative_prices_and_discounts(self):
        """Verify that negative prices or discounts are rejected."""
        with self.assertRaises(ValueError) as ctx:
            predict_shipment({
                "shipment_id": "ERR-03",
                "Product Price": -10.0,
            })
        self.assertIn("non-negative", str(ctx.exception).lower())

        with self.assertRaises(ValueError) as ctx:
            predict_shipment({
                "shipment_id": "ERR-04",
                "Order Item Discount": -5.0,
            })
        self.assertIn("non-negative", str(ctx.exception).lower())

    def test_reject_invalid_discount_rate(self):
        """Verify that discount rate outside [0.0, 1.0] is rejected."""
        with self.assertRaises(ValueError) as ctx:
            predict_shipment({
                "shipment_id": "ERR-05",
                "Order Item Discount Rate": 1.5,
            })
        self.assertIn("between 0.0 and 1.0", str(ctx.exception).lower())

        with self.assertRaises(ValueError) as ctx:
            predict_shipment({
                "shipment_id": "ERR-06",
                "Order Item Discount Rate": -0.1,
            })
        self.assertIn("between 0.0 and 1.0", str(ctx.exception).lower())

    def test_reject_negative_simulated_delay_days(self):
        """Verify that negative simulated delay days is rejected."""
        with self.assertRaises(ValueError) as ctx:
            predict_shipment({
                "shipment_id": "ERR-07",
                "simulated_delay_days": -5,
            })
        self.assertIn("non-negative", str(ctx.exception).lower())

    def test_reject_unparseable_numerical_strings(self):
        """Verify that invalid strings for numerical features raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            predict_shipment({
                "shipment_id": "ERR-08",
                "Order Item Quantity": "not_a_valid_number",
            })
        self.assertIn("invalid numeric value", str(ctx.exception).lower())

    # ========================================================================
    # 5. Output Contract Schema Verification
    # ========================================================================
    def test_prediction_output_contract(self):
        """Verify that the prediction output matches exact keys and strict types."""
        sample = {
            "shipment_id": "CONTRACT-TEST-01",
            "Days for shipment (scheduled)": 3,
            "Shipping Mode": "Second Class",
        }
        res = predict_shipment(sample)
        # Exact expected keys
        self.assertEqual(set(res.keys()), {"shipment_id", "delay_probability", "predicted_delay_days"})
        # Exact expected types
        self.assertIsInstance(res["shipment_id"], str)
        self.assertIsInstance(res["delay_probability"], float)
        self.assertIsInstance(res["predicted_delay_days"], int)
        # Expected ranges
        self.assertTrue(0.0 <= res["delay_probability"] <= 1.0)
        self.assertTrue(res["predicted_delay_days"] >= 0)


if __name__ == "__main__":
    unittest.main()
