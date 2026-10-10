# SupplyPrescript

## Closed-Loop Prescriptive Analytics for Microchip Supply Chain Decision Support

SupplyPrescript is an enterprise-grade decision-support system designed to bridge the operational gap between disruption risk prediction and actionable prescriptive mitigation in mission-critical semiconductor supply chains. The platform couples pre-transit **XGBoost** machine learning models with **PuLP Mixed-Integer Linear Programming (MILP)** optimization, governed by a persistent **SQLite** audit trail and a Swiss-minimalist executive decision cockpit.

---

## 1. Project Development & Academic Authorship

**SupplyPrescript was independently designed, developed, implemented, and validated by Nikhil B. Rao.**

The project was executed as an individual development effort encompassing all engineering and research disciplines:

- **Full-Stack Architecture & Frontend**: Designed and built the executive Swiss-minimalist dashboard (`frontend/index.html`, `frontend/style.css`, `frontend/app.js`) utilizing responsive layouts, clear visual hierarchy, multi-scenario simulation controls, dynamic KPI panels, and audit log exploration.
- **FastAPI REST Backend**: Architected asynchronous endpoints, Pydantic v2 validation models, error handling middleware, and CORS configuration in `backend/main.py` and `backend/schemas.py`.
- **Machine Learning Subsystem**: Implemented pre-transit delay classification and duration regression pipelines (`ml/preprocess.py`, `ml/predict.py`, `ml/train.py`), enforced data leakage prevention, calibrated classification probabilities, and verified model artifacts.
- **Prescriptive Optimization Engine**: Formulated and implemented the Mixed-Integer Linear Programming (MILP) model using PuLP (`backend/optimization.py`), incorporating budget, assembly SLA, supplier capacity, and dynamic mitigation trade-offs with explicit infeasibility handling.
- **Relational Persistence & Audit Trail**: Designed relational database schema (`database/db.py`) with foreign key constraints, atomic multi-table write-backs (`save_prescribe_audit`), and query aggregations powering closed-loop outcome evaluation.
- **Quality Assurance & Verification**: Authored 93 automated tests across 4 comprehensive test suites (`backend/test_integration.py`, `backend/test_validation.py`, `ml/test_ml_pipeline.py`, `database/test_db.py`), establishing 100% test pass rate across all system tiers.

---

## 2. Problem Statement & Objectives

### The Semiconductor Supply Chain Dilemma
Advanced semiconductor manufacturing features extreme capital intensity and rigid operational constraints:
- **Extended Fabrication Cycles**: Front-end wafer fabrication spans 20 to 50 weeks across hundreds of nanometer-scale photolithography steps.
- **Catastrophic Downtime Costs**: Cleanroom assembly plant interruptions and automotive or server assembly line halts incur downtime costs exceeding $1,000,000 per shift.
- **The Operational Chasm**: Conventional supply chain software provides descriptive dashboards or isolated predictive delay alerts. When an alert arrives, operations managers are left without quantified, constraint-respecting guidance on whether to expedite via air freight, activate secondary suppliers, or absorb delays.

### Core Objectives
1. **Accurate Risk Detection**: Predict freight delay risk and expected slippage days prior to transit departure.
2. **Mathematically Guaranteed Mitigation**: Formulate and solve a MILP optimization problem in under 50 milliseconds to prescribe the lowest-cost recovery action satisfying production SLA deadlines, supplier allocations, and budgets.
3. **Closed-Loop Auditability**: Enforce human-in-the-loop managerial authorization and log all recommendations, manager choices, and post-delivery real-world outcomes into an immutable audit trail.
4. **Effectiveness Feedback**: Continuously evaluate decision effectiveness using empirical post-delivery tracking to refine supply chain resilience.

---

## 3. System Architecture & Closed-Loop Workflow

```
                                SUPPLYPRESCRIPT CLOSED-LOOP ARCHITECTURE

  [ Shipment Profile & Business Constraints ]
                      │
                      ▼
   ┌─────────────────────────────────────┐
   │ 1. XGBoost Delay Risk Classifier    │ ───► Delay Probability [0.0, 1.0]
   │    & Delay Duration Regressor       │ ───► Predicted Slippage Duration (Days)
   └─────────────────────────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────┐
   │ 2. PuLP Prescriptive MILP Engine    │ ◄─── Constraints: Budget, SLA, Capacity
   │    (Min Cost s.t. Budget, SLA, Cap) │ ───► Optimal Action (Air Freight / Sec Supplier / Accept Delay)
   └─────────────────────────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────┐
   │ 3. Manager Authorization Interface  │ ───► Human-in-the-Loop Sign-off & Notes
   └─────────────────────────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────┐
   │ 4. SQLite Atomic Database Ledger    │ ───► Linked: Shipments ↔ Predictions ↔ Decisions
   └─────────────────────────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────┐
   │ 5. Post-Delivery Outcome Evaluation │ ───► Actual Transit Days, Real Cost, Effectiveness KPI
   └─────────────────────────────────────┘
```

The workflow operates across five synchronized stages:
1. **Shipment Configuration**: The user configures consignment parameters (fab source, component type, order quantity, scheduled transit days, shipping mode, destination) and business constraints (budget ceiling, assembly SLA deadline, supplier capacity).
2. **ML Risk Prediction**: Pre-transit features are encoded and evaluated by the XGBoost pipeline to produce a calibrated delay risk probability and projected delay duration.
3. **Prescriptive Optimization**: The predicted delay is injected into the PuLP solver alongside candidate mitigation alternatives. The solver returns the mathematically optimal decision or flags infeasibility.
4. **Manager Authorization**: Operations leadership reviews solver recommendations, authorizes the optimal choice or records a justified override, and commits the decision.
5. **Outcome Evaluation & Audit**: Post-delivery actuals (real lead time, realized cost, effectiveness) are recorded in SQLite to power closed-loop KPI analytics.

---

## 4. Technology Stack

| Layer | Technologies | Role & Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, Vanilla CSS3, JavaScript (ES6+) | Swiss-minimalist executive cockpit, dynamic scenario presets, real-time KPI visualization, zero framework lock-in. |
| **Backend API** | FastAPI, Uvicorn, Starlette | Asynchronous REST service, OpenAPI/Swagger self-documentation, Pydantic v2 request validation, unified JSON error contracts. |
| **Machine Learning** | Scikit-learn, XGBoost, Joblib | Pre-transit delay classification (`XGBClassifier`), duration regression (`XGBRegressor`), `ColumnTransformer` feature pipeline. |
| **Optimization** | PuLP (MILP), CBC Solver | Mixed-Integer Linear Programming formulation, constraint satisfaction, cost minimization under SLA and capacity boundaries. |
| **Persistence** | SQLite 3 (`sqlite3`) | Relational audit ledger, foreign key referential integrity (`PRAGMA foreign_keys = ON`), atomic transaction logging. |
| **Testing** | Python `unittest`, `fastapi.testclient` (`httpx`) | 93 automated tests across integration, business validation, ML reliability, and database audit tiers. |

---

## 5. Machine Learning Pipeline & Data Lineage

### Data Lineage & Architectural Distinction
It is critical to maintain a clear distinction between the historical training dataset and the operational microchip scenario:

- **Historical Training Dataset (DataCo Logistics)**: The machine learning models were trained on 180,000+ generalized commercial logistics records from the open-source DataCo Global Supply Chain dataset. This empirical dataset captures transit modes, geographic corridors, scheduled lead times, and historical freight delays.
- **Application Context (Semiconductor Cleanroom Logistics)**: The DataCo dataset does **not** contain proprietary microchip records. Instead, it serves as the foundational empirical sensor for freight transit disruption patterns. SupplyPrescript maps these transit delay signals into high-value semiconductor manufacturing scenarios (e.g., TSMC Fab 18, 4nm AI accelerators, automotive MCUs) via the business constraint and prescriptive optimization layer.

### Strict Data Leakage Prevention
To guarantee real-world inference validity, the training and inference pipelines strictly prohibit post-transit leakage fields:
- **Excluded Features**: `Days for shipping (real)`, `Delivery Status`, `shipping date (DateOrders)`, and customer IDs.
- **Approved Feature Set (13 Features)**:
  - *Categorical (7)*: `Shipping Mode`, `Customer Segment`, `Market`, `Order Region`, `Order Country`, `Category Name`, `Department Name` (encoded with `OneHotEncoder(handle_unknown='ignore')`).
  - *Numerical (6)*: `Days for shipment (scheduled)`, `Order Item Quantity`, `Order Item Product Price`, `Order Item Discount`, `Order Item Discount Rate`, `Product Price`.
- **Runtime Leakage Guard**: The `predict_shipment()` function actively scans input payloads and raises explicit `ValueError: DATA LEAKAGE ERROR` if any forbidden post-transit field is submitted.

### Model Architecture & Empirical Performance Metrics
Evaluated on a 20% stratified holdout test set (stored in `ml/models/metrics.json`):

| Model Component | Algorithm & Hyperparameters | Evaluation Metric | Result |
| :--- | :--- | :--- | :--- |
| **Delay Classifier** | `XGBClassifier(n_estimators=150, max_depth=6, lr=0.08)` | **Accuracy** | **69.80%** |
| | | **Precision** | **84.31%** |
| | | **Recall** | **55.18%** |
| | | **F1-Score** | **0.6670** |
| | | **ROC-AUC** | **0.7370** |
| **Delay Duration Regressor** | `XGBRegressor(n_estimators=100, max_depth=5, lr=0.08)` | **Mean Absolute Error (MAE)** | **0.4772 days** |
| | | **Root Mean Squared Error (RMSE)** | **0.6632 days** |

---

## 6. Prescriptive Optimization Engine (PuLP MILP)

The prescriptive analytics layer in `backend/optimization.py` formulates disruption mitigation as a binary Mixed-Integer Linear Program.

### Mathematical Formulation

Let $I$ be the set of mitigation alternatives:
$$I = \{\text{Air Freight}, \text{Secondary Supplier}, \text{Accept Delay}\}$$

For each option $i \in I$, let:
- $c_i$: Direct mitigation cost in USD ($c_{\text{Air}} = \$15,000$, $c_{\text{Sec}} = \$18,000$, $c_{\text{Delay}} = \$0$)
- $d_i$: Realized delivery time in days ($d_{\text{Air}} = 2$, $d_{\text{Sec}} = 4$, $d_{\text{Delay}} = \text{predicted\_delay\_days}$)
- $x_i \in \{0, 1\}$: Binary decision variable indicating selection of alternative $i$

**Objective Function**:
$$\min_{x} \sum_{i \in I} c_i x_i$$

**Subject to Constraints**:
1. **Exclusive Selection**: Exactly one alternative must be executed:
   $$\sum_{i \in I} x_i = 1$$
2. **Mitigation Budget Constraint**: Total cost cannot exceed authorized budget $B$:
   $$\sum_{i \in I} c_i x_i \le B$$
3. **Assembly SLA Delivery Constraint**: Delivery lead time cannot breach the manufacturing deadline $\text{SLA}$:
   $$\sum_{i \in I} d_i x_i \le \text{SLA}$$
4. **Supplier Capacity Boundary**: Production requirement $Q$ cannot exceed allocated fab capacity $C$:
   $$Q \le C$$

### Infeasibility Handling
If required quantity exceeds supplier capacity ($Q > C$) or if no mitigation alternative simultaneously satisfies both budget and delivery SLA deadlines, the solver truthfully returns `status: "Infeasible"` with a clear explanatory diagnostic message. It never produces an invalid or unexecutable plan.

---

## 7. SQLite Relational Schema & Audit Ledger

Persistence is implemented using Python's native `sqlite3` with foreign key enforcement enabled (`PRAGMA foreign_keys = ON;`).

```sql
-- 1. Shipments Table
CREATE TABLE shipments (
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
);

-- 2. ML Delay Predictions Table
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id TEXT NOT NULL,
    delay_probability REAL NOT NULL,
    predicted_delay_days INTEGER NOT NULL,
    model_name TEXT DEFAULT 'XGBoost Delay Classifier',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
);

-- 3. PuLP Prescriptive Decisions Table
CREATE TABLE optimization_decisions (
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
);

-- 4. Post-Delivery Outcomes Table
CREATE TABLE outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id TEXT NOT NULL,
    actual_delivery_days INTEGER,
    actual_cost REAL,
    delay_occurred INTEGER DEFAULT 0,
    decision_effective INTEGER DEFAULT 1,
    feedback_notes TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
);
```

- **Atomic Transactions**: `save_prescribe_audit()` commits the shipment, ML prediction, and prescriptive decision in a single atomic database transaction. If any write fails, the entire transaction rolls back.
- **Relational Integrity**: Indexed lookups on `shipment_id` enable complete, sub-millisecond retrieval of end-to-end consignment histories.

---

## 8. API Specification

| Method | Endpoint | Description | Request Payload / Params | Response Summary |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Health check endpoint | None | `{"message": "SupplyPrescript Backend is running"}` |
| `GET` | `/docs` | OpenAPI / Swagger interactive documentation | None | Swagger UI interface |
| `GET` | `/dashboard/` | Executive Swiss-minimalist web application | None | Static HTML, CSS, JS dashboard |
| `POST` | `/predict` | Pre-transit delay risk prediction | `LogisticsPredictionRequest` | `{"shipment_id", "delay_probability", "predicted_delay_days"}` |
| `POST` | `/optimize` | Prescriptive PuLP optimization solver | `ShipmentRequest` | `{"status", "recommended_action", "chosen_option", "options"}` |
| `POST` | `/prescribe` | Complete closed-loop execution (ML → PuLP → DB) | `PrescribeRequest` | Unified prediction, optimization, and SQLite write-back |
| `POST` | `/decision` | Manager authorization / override record | `ManagerDecisionRequest` | `{"status": "success", "message": "..."}` |
| `POST` | `/outcome` | Post-delivery realization & effectiveness log | `OutcomeEvaluationRequest` | `{"status": "success", "outcome_id": int}` |
| `GET` | `/history/shipments` | List all tracked shipment records | None | Array of shipment records |
| `GET` | `/history/decisions` | List all prescriptive decisions | None | Array of decision records |
| `GET` | `/history/outcomes` | List all post-delivery outcomes | None | Array of outcome evaluations |
| `GET` | `/history/{id}` | Full audit trail for a specific consignment | `shipment_id` path param | Linked shipment, predictions, decisions, and outcomes |
| `GET` | `/analytics` | Aggregated closed-loop KPIs | None | Tracked counts, avg risk, optimal count, effectiveness % |
| `GET` | `/ml/metrics` | Holdout evaluation metrics of XGBoost models | None | Classification accuracy, precision, F1, ROC-AUC, regression MAE |

---

## 9. Installation & Execution Guide

### Prerequisites
- Python 3.10 or higher
- PowerShell, Bash, or Command Prompt
- Modern web browser (Chrome, Edge, Firefox, Safari)

### Step 1: Clone or Navigate to the Repository
```powershell
cd "C:\Academic Project\Supply-prescript"
```

### Step 2: Create and Activate Virtual Environment
```powershell
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

*Installed core packages*: `fastapi`, `uvicorn`, `pandas`, `scikit-learn`, `xgboost`, `pulp`, `httpx`.

### Step 4: Launch the Application Backend
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 5: Access the Web Dashboard and API Docs
- **Executive Decision Cockpit**: [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Root Health Check**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 10. Automated Test Suites & Verified Results

The repository includes 4 automated test suites covering every layer of the architecture.

### Execution Commands & Verified Results

| Test Suite | Command | Scope & Coverage | Verified Result |
| :--- | :--- | :--- | :--- |
| **Integration Suite** | `.\.venv\Scripts\python.exe backend\test_integration.py` | Full closed-loop journey, live FastAPI endpoints, PuLP solver, DB write-back, 404/422 validation, ML-to-optimization handoff regression | **42/42 PASSED** |
| **Validation Suite** | `.\.venv\Scripts\python.exe -m unittest backend.test_validation` | Pydantic schema validation, zero/negative inputs, capacity violation boundaries, FastAPI endpoint constraints | **12/12 PASSED** |
| **ML Pipeline Suite** | `.\.venv\Scripts\python.exe -m unittest ml.test_ml_pipeline` | Artifact loading, preprocessor consistency, strict data leakage rejection, contract typing, missing value imputation | **19/19 PASSED** |
| **Database Audit Suite** | `.\.venv\Scripts\python.exe -m unittest database.test_db` | SQLite initialization, foreign key referential integrity, atomic transactions, rollbacks, KPI aggregations | **20/20 PASSED** |
| **Overall Total** | — | **End-to-End System Reliability** | **93/93 PASSED (100%)** |

---

## 11. Known Limitations & Future Enhancements

1. **Static Pre-Training Baseline**: The XGBoost models are trained on offline historical DataCo freight data. Future production iterations could implement an online continuous learning pipeline with Apache Kafka and feature store integration to stream real-time maritime AIS transponder and air traffic data.
2. **Single-Echelon Optimization**: The current PuLP MILP formulation models single-echelon expedited transport and secondary sourcing trade-offs. Future extensions could expand to multi-echelon supply network flows with inventory buffering across tier-2 wafer fabs and OSAT packaging facilities.
3. **Deterministic Cost Inputs**: Mitigation options currently operate on deterministic cost and lead time parameters. Future versions could incorporate stochastic programming or robust optimization to model uncertain fuel surcharges and flight availability fluctuations.
4. **Database Architecture**: SQLite provides lightweight zero-configuration ACID persistence suitable for embedded decision cockpits. For multi-tenant global enterprise deployments, migrating to PostgreSQL with row-level security and Snowflake data warehousing is recommended.

---

## 12. Project Structure

```
Supply-prescript/
├── .gitignore                      # Git ignore configuration
├── requirements.txt                # Root Python package dependencies
├── README.md                       # Comprehensive project documentation
├── backend/
│   ├── __init__.py
│   ├── main.py                     # FastAPI REST application & routing
│   ├── optimization.py             # PuLP MILP prescriptive optimization engine
│   ├── requirements.txt            # Backend Python dependencies
│   ├── schemas.py                  # Pydantic v2 validation models & schemas
│   ├── test_integration.py        # 42-test end-to-end integration suite
│   └── test_validation.py         # 12-test schema & constraint validation suite
├── database/
│   ├── __init__.py
│   ├── db.py                       # SQLite persistence layer, CRUD, and audit queries
│   ├── supplyprescript.db          # SQLite operational database file
│   └── test_db.py                  # 20-test database & audit trail unit tests
├── frontend/
│   ├── app.js                      # Controller, API client, tab routing, DOM binding
│   ├── index.html                  # Swiss-minimalist executive cockpit interface
│   ├── logo.png                    # SupplyPrescript enterprise brand logo
│   └── style.css                   # Custom typography, responsive design system
└── ml/
    ├── __init__.py
    ├── README.md                   # Machine learning data lineage & architecture doc
    ├── predict.py                  # DelayPredictor inference engine & contract validator
    ├── preprocess.py               # Feature pipeline, column mapping & leakage guards
    ├── test_ml_pipeline.py         # 19-test ML pipeline reliability suite
    ├── train.py                    # Model training script for classifier & regressor
    └── models/
        ├── metrics.json            # Stratified holdout evaluation metrics
        ├── preprocessor.joblib     # Serialized scikit-learn ColumnTransformer
        ├── xgb_classifier.joblib   # Trained XGBoost binary delay classifier
        └── xgb_regressor.joblib    # Trained XGBoost delay duration regressor
```

---

## 13. License & Academic Integrity

This project was developed for academic submission and operational evaluation. All algorithms, formulations, test suites, and source code are authored by Nikhil B. Rao.
