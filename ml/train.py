"""
SupplyPrescript - Machine Learning Model Training Module
Trains:
1. Primary: XGBoost Classifier for Late_delivery_risk prediction (Delay Probability)
2. Secondary: XGBoost Regressor for delay duration prediction (Conditional Delay Days)

Saves trained artifacts and metrics to ml/models/.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    mean_absolute_error,
    root_mean_squared_error,
)
import xgboost as xgb

from ml.preprocess import (
    load_and_clean_data,
    build_preprocessor,
    save_preprocessor,
    MODELS_DIR,
)

CLASSIFIER_PATH = os.path.join(MODELS_DIR, "xgb_classifier.joblib")
REGRESSOR_PATH = os.path.join(MODELS_DIR, "xgb_regressor.joblib")
METRICS_PATH = os.path.join(MODELS_DIR, "metrics.json")


def train_models():
    print("=" * 60)
    print("SupplyPrescript ML Training Pipeline")
    print("=" * 60)

    # 1. Load data
    X, y_class, y_delay_days = load_and_clean_data()

    # 2. Stratified Train / Test Split (80% Train, 20% Test)
    print("\nSplitting data into 80% Train and 20% Test sets...")
    (
        X_train,
        X_test,
        y_class_train,
        y_class_test,
        y_reg_train,
        y_reg_test,
    ) = train_test_split(
        X,
        y_class,
        y_delay_days,
        test_size=0.20,
        random_state=42,
        stratify=y_class,
    )

    print(f"Train samples: {len(X_train):,}, Test samples: {len(X_test):,}")

    # 3. Fit preprocessor on training data only
    print("\nFitting preprocessing pipeline...")
    preprocessor = build_preprocessor()
    X_train_trans = preprocessor.fit_transform(X_train)
    X_test_trans = preprocessor.transform(X_test)
    save_preprocessor(preprocessor)

    # 4. Train Primary Model: XGBoost Classifier
    print("\nTraining XGBoost Classifier for Late_delivery_risk...")
    xgb_clf = xgb.XGBClassifier(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        eval_metric="logloss",
    )
    xgb_clf.fit(X_train_trans, y_class_train)

    # Evaluate Classifier
    y_pred_class = xgb_clf.predict(X_test_trans)
    y_pred_proba = xgb_clf.predict_proba(X_test_trans)[:, 1]

    acc = float(accuracy_score(y_class_test, y_pred_class))
    prec = float(precision_score(y_class_test, y_pred_class))
    rec = float(recall_score(y_class_test, y_pred_class))
    f1 = float(f1_score(y_class_test, y_pred_class))
    roc_auc = float(roc_auc_score(y_class_test, y_pred_proba))
    cm = confusion_matrix(y_class_test, y_pred_class).tolist()

    print("\n" + "=" * 40)
    print("XGBOOST CLASSIFIER EVALUATION")
    print("=" * 40)
    print(f"Accuracy  : {acc:.4f} ({acc * 100:.2f}%)")
    print(f"Precision : {prec:.4f}")
    print(f"Recall    : {rec:.4f}")
    print(f"F1 Score  : {f1:.4f}")
    print(f"ROC-AUC   : {roc_auc:.4f}")
    print("\nConfusion Matrix:")
    print(f"TN: {cm[0][0]}, FP: {cm[0][1]}")
    print(f"FN: {cm[1][0]}, TP: {cm[1][1]}")
    print("\nDetailed Classification Report:")
    print(classification_report(y_class_test, y_pred_class, digits=4))

    # 5. Train Secondary Model: XGBoost Regressor for Delay Days
    # We train conditionally on delayed shipments to model expected delay duration
    print("\nTraining XGBoost Regressor for delay duration (delayed cases)...")
    delayed_mask_train = y_class_train == 1
    delayed_mask_test = y_class_test == 1

    X_train_delayed = X_train_trans[delayed_mask_train.values]
    y_reg_train_delayed = y_reg_train[delayed_mask_train]

    X_test_delayed = X_test_trans[delayed_mask_test.values]
    y_reg_test_delayed = y_reg_test[delayed_mask_test]

    xgb_reg = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.08,
        random_state=42,
        n_jobs=-1,
    )
    xgb_reg.fit(X_train_delayed, y_reg_train_delayed)

    y_pred_reg = xgb_reg.predict(X_test_delayed)
    mae = float(mean_absolute_error(y_reg_test_delayed, y_pred_reg))
    rmse = float(root_mean_squared_error(y_reg_test_delayed, y_pred_reg))

    print("\n" + "=" * 40)
    print("DELAY DURATION REGRESSOR EVALUATION")
    print("=" * 40)
    print(f"MAE  : {mae:.4f} days")
    print(f"RMSE : {rmse:.4f} days")

    # 6. Save models and metrics
    print("\nSaving model artifacts...")
    joblib.dump(xgb_clf, CLASSIFIER_PATH)
    joblib.dump(xgb_reg, REGRESSOR_PATH)
    print(f"Saved Classifier to: {CLASSIFIER_PATH}")
    print(f"Saved Regressor to: {REGRESSOR_PATH}")

    metrics = {
        "model": "XGBoost Classifier",
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "confusion_matrix": cm,
        "regression_mae": round(mae, 4),
        "regression_rmse": round(rmse, 4),
    }

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved evaluation metrics to: {METRICS_PATH}")

    print("\nModel training pipeline completed successfully!")
    return metrics


if __name__ == "__main__":
    train_models()
