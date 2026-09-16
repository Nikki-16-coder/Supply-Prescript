"""
SupplyPrescript - FastAPI Backend Application
Closed-Loop Prescriptive Analytics for Supply Chain Decision Support

Integrates:
- Machine Learning delay prediction (historical DataCo logistics dataset)
- Prescriptive optimization with PuLP (dynamic mitigation alternatives)
- SQLite database layer for shipments, predictions, decisions, and outcomes
"""

import os
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.optimization import optimize_shipment
from backend.schemas import (
    ShipmentRequest,
    LogisticsPredictionRequest,
    LogisticsPredictionResponse,
    PrescribeRequest,
    PrescribeResponse,
    ManagerDecisionRequest,
    OutcomeEvaluationRequest,
)
from ml.predict import predict_shipment
from ml.preprocess import MODELS_DIR
from database.db import (
    init_db,
    save_shipment,
    save_prediction,
    save_optimization_decision,
    update_manager_decision,
    save_outcome,
    get_all_shipments,
    get_all_decisions,
    get_all_outcomes,
    get_shipment_history,
    get_analytics_summary,
)

# Ensure database tables exist on startup
init_db()

app = FastAPI(
    title="SupplyPrescript API",
    description="Closed-Loop Prescriptive Analytics for Microchip Supply Chain Decision Support",
    version="1.0.0",
)

# Enable CORS for local frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Global Exception Handlers (Clean API Errors & No Stack Traces)
# ============================================================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats Pydantic validation errors into clean user-friendly messages."""
    error_messages = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        msg = err.get("msg", "Invalid input")
        error_messages.append(f"{field}: {msg}" if field else msg)
    summary = "; ".join(error_messages)
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "error_type": "ValidationError",
            "message": summary,
            "detail": summary,
            "errors": error_messages,
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handles domain and business validation errors with HTTP 400."""
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "error_type": "ValueError",
            "message": str(exc),
            "detail": str(exc),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catches unhandled exceptions without leaking server stack traces."""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail,
                "detail": exc.detail,
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_type": "InternalServerError",
            "message": "An unexpected error occurred while processing your request.",
            "detail": str(exc),
        },
    )


# ============================================================================
# Core & Health Endpoints
# ============================================================================
@app.get("/")
def root():
    return {"message": "SupplyPrescript Backend is running"}


# ============================================================================
# 1. Optimization Endpoints (Preserved + Dynamic Options Enabled)
# ============================================================================
@app.get("/optimize")
def optimize():
    """Default demonstration endpoint preserving initial implementation."""
    result = optimize_shipment(
        budget=20000,
        max_delivery_days=7,
        required_quantity=5000,
        supplier_capacity=6000,
        predicted_delay_days=14,
    )
    return result


@app.post("/optimize")
def optimize_shipment_api(request: ShipmentRequest):
    """
    Prescriptive optimization endpoint accepting microchip business constraints
    and optional dynamic mitigation options.
    """
    return optimize_shipment(
        budget=request.budget,
        max_delivery_days=request.max_delivery_days,
        required_quantity=request.required_quantity,
        supplier_capacity=request.supplier_capacity,
        predicted_delay_days=request.predicted_delay_days,
        options=request.options,
    )


# ============================================================================
# 2. ML Delay Prediction Endpoints
# ============================================================================
@app.post("/predict", response_model=LogisticsPredictionResponse)
def predict_delay_api(request: LogisticsPredictionRequest):
    """
    Predicts shipment delay risk and expected delay duration.
    Uses XGBoost classifier trained on historical logistics data (DataCo).

    Expected ML Output Contract:
    {
      "shipment_id": "SHP001",
      "delay_probability": 0.87,
      "predicted_delay_days": 14
    }
    """
    payload = request.model_dump(by_alias=True)
    result = predict_shipment(payload)
    return result


@app.get("/ml/metrics")
def get_ml_metrics():
    """Returns classification evaluation metrics of the trained XGBoost model."""
    metrics_path = os.path.join(MODELS_DIR, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {"status": "Metrics file not found. Train the model first."}


# ============================================================================
# 3. Prescriptive Analytics Closed-Loop Endpoint (ML -> PuLP -> DB Write-Back)
# ============================================================================
@app.post("/prescribe", response_model=PrescribeResponse)
def prescribe_solution_api(request: PrescribeRequest):
    """
    Complete closed-loop decision workflow:
    1. Runs ML delay prediction on logistics profile.
    2. Feeds predicted delay into PuLP optimization engine alongside
       microchip business constraints and dynamic mitigation options.
    3. Persists shipment, prediction, and decision to SQLite database.
    4. Returns both ML prediction and prescriptive recommendation.
    """
    payload = request.model_dump(by_alias=True)

    # 1. ML Delay Prediction
    prediction = predict_shipment(payload)

    # 2. Optimization using predicted delay days, constraints, and dynamic options
    optimization_result = optimize_shipment(
        budget=request.budget,
        max_delivery_days=request.max_delivery_days,
        required_quantity=request.required_quantity,
        supplier_capacity=request.supplier_capacity,
        predicted_delay_days=prediction["predicted_delay_days"],
        options=request.options,
    )

    # 3. Automatic Database Write-Back for Audit Trail
    try:
        save_shipment(payload)
        save_prediction(prediction)
        save_optimization_decision(
            shipment_id=request.shipment_id,
            budget=request.budget,
            max_delivery_days=request.max_delivery_days,
            required_quantity=request.required_quantity,
            supplier_capacity=request.supplier_capacity,
            optimization_result=optimization_result,
        )
    except Exception as exc:
        print(f"Database logging warning: {exc}")

    return {
        "shipment_id": request.shipment_id,
        "prediction": prediction,
        "optimization": optimization_result,
    }


# ============================================================================
# 4. Database & Decision Tracking Endpoints
# ============================================================================
@app.post("/decision")
def record_manager_decision(request: ManagerDecisionRequest):
    """Records or overrides manager decision for a shipment."""
    success = update_manager_decision(
        shipment_id=request.shipment_id,
        manager_decision=request.manager_decision,
        notes=request.notes,
    )
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No optimization decision record found for shipment {request.shipment_id}",
        )
    return {
        "status": "success",
        "message": f"Recorded manager decision '{request.manager_decision}' for {request.shipment_id}",
    }


@app.post("/outcome")
def record_shipment_outcome(request: OutcomeEvaluationRequest):
    """Records the real-world post-mitigation outcome and performance evaluation."""
    outcome_id = save_outcome(request.model_dump())
    return {
        "status": "success",
        "outcome_id": outcome_id,
        "message": f"Recorded outcome for {request.shipment_id}",
    }


@app.get("/history/shipments")
def list_shipments():
    """Retrieves all tracked shipments from the database."""
    return get_all_shipments()


@app.get("/history/decisions")
def list_decisions():
    """Retrieves all optimization decisions from the database."""
    return get_all_decisions()


@app.get("/history/outcomes")
def list_outcomes():
    """Retrieves all outcome evaluations from the database."""
    return get_all_outcomes()


@app.get("/history/{shipment_id}")
def get_shipment_audit_trail(shipment_id: str):
    """Retrieves full end-to-end closed-loop audit trail for a shipment."""
    data = get_shipment_history(shipment_id)
    if not data["shipment"] and not data["predictions"] and not data["decisions"]:
        raise HTTPException(status_code=404, detail=f"No records found for shipment {shipment_id}")
    return data


@app.get("/analytics")
def get_analytics():
    """Returns aggregated KPIs across all shipments, decisions, and outcomes."""
    return get_analytics_summary()


# ============================================================================
# Frontend Dashboard Mounting
# ============================================================================
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/dashboard", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")