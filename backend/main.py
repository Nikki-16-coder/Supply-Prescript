from pydantic import BaseModel
from fastapi import FastAPI
from backend.optimization import optimize_shipment

app = FastAPI(title="SupplyPrescript API")

class ShipmentRequest(BaseModel):
    budget: float
    max_delivery_days: int
    required_quantity: int
    supplier_capacity: int
    predicted_delay_days: int


@app.get("/")
def root():
    return {"message": "SupplyPrescript Backend is running"}


@app.get("/optimize")
def optimize():
    result = optimize_shipment(
        budget=20000,
        max_delivery_days=7,
        required_quantity=5000,
        supplier_capacity=6000,
        predicted_delay_days=14
    )

    return result

@app.post("/optimize")
def optimize_shipment_api(request: ShipmentRequest):
    return optimize_shipment(
        budget=request.budget,
        max_delivery_days=request.max_delivery_days,
        required_quantity=request.required_quantity,
        supplier_capacity=request.supplier_capacity,
        predicted_delay_days=request.predicted_delay_days
    )