"""
SupplyPrescript - Machine Learning Inference Module
Loads trained XGBoost model and preprocessor to predict:
1. Delay probability (Late_delivery_risk)
2. Predicted delay days

Adheres strictly to the contract:
{
  "shipment_id": "SHP001",
  "delay_probability": 0.87,
  "predicted_delay_days": 14
}
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Union

from ml.preprocess import (
    APPROVED_NUMERICAL_FEATURES,
    APPROVED_CATEGORICAL_FEATURES,
    APPROVED_FEATURES,
    MODELS_DIR,
    PREPROCESSOR_PATH,
)

CLASSIFIER_PATH = os.path.join(MODELS_DIR, "xgb_classifier.joblib")
REGRESSOR_PATH = os.path.join(MODELS_DIR, "xgb_regressor.joblib")

# Sensible default values for supply chain microchip shipment features
DEFAULT_FEATURE_VALUES: Dict[str, Any] = {
    "Days for shipment (scheduled)": 4,
    "Shipping Mode": "Standard Class",
    "Order Item Quantity": 100,
    "Order Item Product Price": 50.0,
    "Order Item Discount": 0.0,
    "Order Item Discount Rate": 0.0,
    "Customer Segment": "Corporate",
    "Market": "Pacific Asia",
    "Order Region": "Southeast Asia",
    "Order Country": "Taiwan",
    "Category Name": "Electronics",
    "Department Name": "Technology",
    "Product Price": 50.0,
}


class DelayPredictor:
    """Predictor class for SupplyPrescript delay risk inference."""

    def __init__(self, models_dir: str = MODELS_DIR):
        self.preprocessor_path = os.path.join(models_dir, "preprocessor.joblib")
        self.classifier_path = os.path.join(models_dir, "xgb_classifier.joblib")
        self.regressor_path = os.path.join(models_dir, "xgb_regressor.joblib")

        self.preprocessor = None
        self.classifier = None
        self.regressor = None
        self._load_artifacts()

    def _load_artifacts(self):
        if not os.path.exists(self.preprocessor_path):
            raise FileNotFoundError(
                f"Preprocessor artifact not found at {self.preprocessor_path}. Please run ml/train.py first."
            )
        if not os.path.exists(self.classifier_path):
            raise FileNotFoundError(
                f"Classifier artifact not found at {self.classifier_path}. Please run ml/train.py first."
            )

        self.preprocessor = joblib.load(self.preprocessor_path)
        self.classifier = joblib.load(self.classifier_path)

        if os.path.exists(self.regressor_path):
            self.regressor = joblib.load(self.regressor_path)
        else:
            self.regressor = None

    def _prepare_input_df(self, shipment_data: Dict[str, Any]) -> pd.DataFrame:
        """Constructs a single-row DataFrame with all 13 approved features."""
        row_dict = {}
        for feature in APPROVED_FEATURES:
            # Check direct match or case-insensitive/underscore match
            val = shipment_data.get(feature)
            if val is None:
                # Try underscore version (e.g. shipping_mode -> Shipping Mode)
                key_alt = feature.lower().replace(" ", "_").replace("(", "").replace(")", "")
                val = shipment_data.get(key_alt)

            if val is None:
                val = DEFAULT_FEATURE_VALUES.get(feature)

            row_dict[feature] = [val]

        df = pd.DataFrame(row_dict)

        # Ensure correct dtypes
        for col in APPROVED_NUMERICAL_FEATURES:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        for col in APPROVED_CATEGORICAL_FEATURES:
            df[col] = df[col].astype(str)

        return df

    def predict(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs ML delay prediction for a shipment record.

        Expected Output Contract:
        {
          "shipment_id": "SHP001",
          "delay_probability": 0.87,
          "predicted_delay_days": 14
        }
        """
        shipment_id = str(shipment_data.get("shipment_id", "SHP001"))

        df_input = self._prepare_input_df(shipment_data)
        X_trans = self.preprocessor.transform(df_input)

        # 1. Delay Probability from Classifier
        probabilities = self.classifier.predict_proba(X_trans)[0]
        delay_prob = round(float(probabilities[1]), 2)

        # 2. Predicted Delay Days
        # If user explicitly supplied a simulated disruption duration, honor it
        explicit_delay = shipment_data.get("simulated_delay_days") or shipment_data.get("disruption_days")
        if explicit_delay is not None:
            predicted_delay_days = int(explicit_delay) if delay_prob >= 0.5 else 0
        elif delay_prob >= 0.5:
            if self.regressor is not None:
                reg_pred = float(self.regressor.predict(X_trans)[0])
                predicted_delay_days = max(1, int(round(reg_pred)))
            else:
                # Fallback to standard logistics delay duration estimate
                scheduled = float(df_input["Days for shipment (scheduled)"].iloc[0])
                predicted_delay_days = max(1, int(round(scheduled * 0.5)))
        else:
            predicted_delay_days = 0

        return {
            "shipment_id": shipment_id,
            "delay_probability": delay_prob,
            "predicted_delay_days": predicted_delay_days,
        }


# Singleton predictor instance for efficient in-memory re-use
_predictor_instance = None


def get_predictor() -> DelayPredictor:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = DelayPredictor()
    return _predictor_instance


def predict_shipment(shipment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Top-level convenience function matching the output contract."""
    predictor = get_predictor()
    return predictor.predict(shipment_data)


if __name__ == "__main__":
    # Test Case 1: High-risk scenario (Second Class / tight scheduled lead time) with simulated disruption
    sample_high_risk = {
        "shipment_id": "SHP001",
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

    # Test Case 2: Standard historical prediction using model regressor
    sample_standard = {
        "shipment_id": "SHP002",
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

    print("\n--- TEST CASE 1 (Microchip Shipment Disruption Scenario) ---")
    out1 = predict_shipment(sample_high_risk)
    print(out1)

    print("\n--- TEST CASE 2 (Standard First Class Shipment) ---")
    out2 = predict_shipment(sample_standard)
    print(out2)
