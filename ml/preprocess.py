"""
SupplyPrescript - Machine Learning Preprocessing Module
Dataset: DataCo Supply Chain Dataset (Historical Logistics)
Scenario: Supplier -> Microchips -> Manufacturer (Delay Risk Prediction)

Strictly enforces feature selection and prevents data leakage.
"""

import os
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

# Approved ML Features (13 features)
APPROVED_NUMERICAL_FEATURES = [
    "Days for shipment (scheduled)",
    "Order Item Quantity",
    "Order Item Product Price",
    "Order Item Discount",
    "Order Item Discount Rate",
    "Product Price",
]

APPROVED_CATEGORICAL_FEATURES = [
    "Shipping Mode",
    "Customer Segment",
    "Market",
    "Order Region",
    "Order Country",
    "Category Name",
    "Department Name",
]

APPROVED_FEATURES = APPROVED_NUMERICAL_FEATURES + APPROVED_CATEGORICAL_FEATURES

# Target column
TARGET_CLASSIFICATION = "Late_delivery_risk"

# Forbidden leakage columns (MUST NOT be used as input features)
FORBIDDEN_LEAKAGE_COLUMNS = [
    "Days for shipping (real)",
    "Delivery Status",
    "shipping date (DateOrders)",
]

DATASET_PATH = os.path.join(os.path.dirname(__file__), "data", "DataCoSupplyChainDataset.csv")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
PREPROCESSOR_PATH = os.path.join(MODELS_DIR, "preprocessor.joblib")


def validate_feature_safety(columns: list[str]) -> None:
    """Ensure no data leakage columns are included in feature lists."""
    for col in FORBIDDEN_LEAKAGE_COLUMNS:
        if col in columns:
            raise ValueError(f"DATA LEAKAGE ERROR: Prohibited column '{col}' found in feature list!")


def load_and_clean_data(dataset_path: str = DATASET_PATH) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Loads DataCo dataset with latin1 encoding, isolates approved features,
    and extracts classification and regression targets without leakage.
    
    Returns:
        X (pd.DataFrame): Approved features only.
        y_class (pd.Series): Late_delivery_risk (0 or 1).
        y_delay_days (pd.Series): Historical delay days (max(0, real - scheduled)).
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at: {dataset_path}")

    print(f"Loading dataset from: {dataset_path} ...")
    df = pd.read_csv(dataset_path, encoding="latin1")
    print(f"Loaded {len(df):,} records with {len(df.columns)} raw columns.")

    # Target calculation for regression (only used as a training label, never an input feature)
    actual_shipping = df["Days for shipping (real)"]
    scheduled_shipping = df["Days for shipment (scheduled)"]
    y_delay_days = (actual_shipping - scheduled_shipping).clip(lower=0)

    # Classification target
    y_class = df[TARGET_CLASSIFICATION].astype(int)

    # Validate that features contain NO leakage
    validate_feature_safety(APPROVED_FEATURES)

    # Extract approved features
    X = df[APPROVED_FEATURES].copy()

    # Fill numerical NaNs with median and categorical with 'Unknown' if any exist
    for col in APPROVED_NUMERICAL_FEATURES:
        X[col] = X[col].fillna(X[col].median())

    for col in APPROVED_CATEGORICAL_FEATURES:
        X[col] = X[col].fillna("Unknown").astype(str)

    print(f"Preprocessing completed. Features shape: {X.shape}")
    print(f"Target distribution (Late_delivery_risk):\n{y_class.value_counts(normalize=True).to_dict()}")

    return X, y_class, y_delay_days


def build_preprocessor() -> ColumnTransformer:
    """
    Constructs a ColumnTransformer that passes numerical features through
    and applies OneHotEncoder with handle_unknown='ignore' to categorical features.
    """
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", APPROVED_NUMERICAL_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=True),
                APPROVED_CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )
    return preprocessor


def save_preprocessor(preprocessor: ColumnTransformer, output_path: str = PREPROCESSOR_PATH) -> None:
    """Saves fitted preprocessor to disk."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(preprocessor, output_path)
    print(f"Saved preprocessor to: {output_path}")


def load_preprocessor(preprocessor_path: str = PREPROCESSOR_PATH) -> ColumnTransformer:
    """Loads preprocessor artifact from disk."""
    if not os.path.exists(preprocessor_path):
        raise FileNotFoundError(f"Preprocessor artifact not found at: {preprocessor_path}")
    return joblib.load(preprocessor_path)
