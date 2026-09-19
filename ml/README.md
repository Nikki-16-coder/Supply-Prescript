# SupplyPrescript — Machine Learning Pipeline & Reliability Architecture

## 1. Architectural Distinction & Data Lineage

It is critical to clearly distinguish between the historical training dataset and the application scenario:

| Dimension | DataCo Supply Chain Dataset | SupplyPrescript Application Layer |
| :--- | :--- | :--- |
| **Domain** | Historical Global Logistics & Retail Freight | Specialized Semiconductor & Microchip Supply Chain |
| **Data Scope** | 180,000+ generalized commercial shipments across multiple shipping modes and global markets | High-value microchip wafer fab consignments (e.g., TSMC Fab 18, 4nm AI accelerators) |
| **Role in Pipeline** | Provides the empirical baseline for training generalized transit delay patterns | Ingests delay risk probabilities and solves multi-objective prescriptive mitigation decisions |
| **Data Authenticity** | Open-source empirical logistics dataset (Kaggle DataCo) | Realistic industrial scenario modeled for mission-critical cleanroom assembly deadlines |

> [!NOTE]
> **Data Lineage Note**: The DataCo dataset is **not** an authentic microchip-specific dataset. It is a historical general logistics dataset used to train robust delay classification and duration estimation models. SupplyPrescript maps these logistics signals into a semiconductor decision-support application layer.

---

## 2. ML Component Roles & Artifacts

The machine learning subsystem in `ml/` comprises four specialized components:

### A. Preprocessor (`ml/models/preprocessor.joblib`)
- **Type**: scikit-learn `ColumnTransformer`
- **Transformation Pipeline**:
  - **Categorical Features (7)**: `OneHotEncoder(handle_unknown="ignore", sparse_output=True)` applied to `Shipping Mode`, `Customer Segment`, `Market`, `Order Region`, `Order Country`, `Category Name`, and `Department Name`.
  - **Numerical Features (6)**: Passthrough transformer applied to `Days for shipment (scheduled)`, `Order Item Quantity`, `Order Item Product Price`, `Order Item Discount`, `Order Item Discount Rate`, and `Product Price`.
- **Strict Data Leakage Prevention**:
  Excludes post-transit outcome fields (`Days for shipping (real)`, `Delivery Status`, `shipping date (DateOrders)`). Prohibits leakage columns at inference.

### B. Primary Model: Delay Risk Classifier (`ml/models/xgb_classifier.joblib`)
- **Algorithm**: `XGBClassifier(n_estimators=150, max_depth=6, learning_rate=0.08, eval_metric="logloss")`
- **Objective**: Predict binary `Late_delivery_risk` (0 = On-time / Early, 1 = Late delivery).
- **Output**: Calibrated probability `delay_probability` in the range `[0.0, 1.0]`.
- **Performance**: Evaluated on 20% stratified holdout test set (`metrics.json`):
  - Accuracy: **69.80%**
  - Precision: **84.31%**
  - ROC-AUC: **0.7370**

### C. Secondary Model: Delay Duration Regressor (`ml/models/xgb_regressor.joblib`)
- **Algorithm**: `XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.08)`
- **Objective**: Conditioned on `Late_delivery_risk == 1`, predicts the expected delay duration in days (`predicted_delay_days`).
- **Performance**: MAE of **0.48 days**, RMSE of **0.66 days** on delayed test samples.

### D. Inference Engine (`ml/predict.py`)
- Encapsulates `DelayPredictor` singleton with lazy caching.
- Handles feature ordering, snake_case alias translation, missing value imputation, and input boundary validation.
- Supports scenario disruption overrides (`simulated_delay_days`) when evaluating high-risk fab disruption cases.

---

## 3. Prediction Output Contract

All ML inference calls adhere strictly to the JSON contract:

```json
{
  "shipment_id": "SHP001",
  "delay_probability": 0.76,
  "predicted_delay_days": 14
}
```

- `shipment_id` (`str`): Unique consignment identifier.
- `delay_probability` (`float`): Clamped probability between `0.0` and `1.0` (rounded to 2 decimal places).
- `predicted_delay_days` (`int`): Non-negative integer representing projected delivery slippage.

---

## 4. Closed-Loop Prescriptive Handoff

The ML pipeline strictly serves as an informational risk sensor for the prescriptive analytics layer:
1. **Prediction Handoff**: `ml/predict.py` produces `predicted_delay_days`.
2. **Prescriptive Optimization**: The predicted delay is fed directly into `backend/optimization.py` alongside microchip business constraints (`budget`, `max_delivery_days`, `required_quantity`, `supplier_capacity`).
3. **Constraint Integrity**: ML predictions **never** bypass or weaken PuLP MILP constraints. If a disruption exceeds SLA and budget limits, the PuLP solver truthfully reports `Infeasible`.
4. **Audit Trail**: Predictions and prescriptive decisions are logged to the SQLite database (`predictions` and `optimization_decisions` tables) for downstream auditability and post-delivery outcome tracking.
