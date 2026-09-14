"""
SupplyPrescript - Backend API Schemas (Pydantic Models)

Separates:
1. Historical logistics delay prediction features (DataCo-trained ML layer)
2. Microchip business & supply chain constraints (PuLP optimization layer)
3. Database write-back schemas for closed-loop decision tracking and outcome evaluation
"""

from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# 1. Existing Optimization Request (Preserved for backwards compatibility,
#    now optionally accepting dynamic options)
# ============================================================================
class ShipmentRequest(BaseModel):
    budget: float
    max_delivery_days: int
    required_quantity: int
    supplier_capacity: int
    predicted_delay_days: int
    options: Optional[Dict[str, Dict[str, Union[float, int]]]] = None


# ============================================================================
# 2. ML Logistics Delay Prediction Schemas
# ============================================================================
class LogisticsPredictionRequest(BaseModel):
    """
    Input features for historical logistics delay risk prediction.
    Trained on historical logistics data (DataCo dataset).
    """
    model_config = ConfigDict(populate_by_name=True)

    shipment_id: str = "SHP001"
    scheduled_days: int = Field(default=4, alias="Days for shipment (scheduled)")
    shipping_mode: str = Field(default="Standard Class", alias="Shipping Mode")
    order_item_quantity: int = Field(default=100, alias="Order Item Quantity")
    order_item_product_price: float = Field(default=50.0, alias="Order Item Product Price")
    order_item_discount: float = Field(default=0.0, alias="Order Item Discount")
    order_item_discount_rate: float = Field(default=0.0, alias="Order Item Discount Rate")
    customer_segment: str = Field(default="Corporate", alias="Customer Segment")
    market: str = Field(default="Pacific Asia", alias="Market")
    order_region: str = Field(default="Southeast Asia", alias="Order Region")
    order_country: str = Field(default="Taiwan", alias="Order Country")
    category_name: str = Field(default="Technology", alias="Category Name")
    department_name: str = Field(default="Technology", alias="Department Name")
    product_price: float = Field(default=50.0, alias="Product Price")
    simulated_delay_days: Optional[int] = None


class LogisticsPredictionResponse(BaseModel):
    """
    ML Prediction Output Contract:
    {
      "shipment_id": "SHP001",
      "delay_probability": 0.87,
      "predicted_delay_days": 14
    }
    """
    shipment_id: str
    delay_probability: float
    predicted_delay_days: int


# ============================================================================
# 3. Microchip Business Prescriptive Workflow Schemas (Closed-Loop)
# ============================================================================
class PrescribeRequest(BaseModel):
    """
    Closed-loop request combining:
    - Logistics parameters for ML delay prediction
    - Microchip supply chain constraints for PuLP prescriptive optimization
    - Optional dynamic mitigation options
    """
    model_config = ConfigDict(populate_by_name=True)

    # Identification & Business Context
    shipment_id: str = "SHP001"
    supplier_name: Optional[str] = "Primary Microchip Fab"
    component: Optional[str] = "Microchips"

    # Logistics features for ML delay prediction
    scheduled_days: int = Field(default=2, alias="Days for shipment (scheduled)")
    shipping_mode: str = Field(default="Second Class", alias="Shipping Mode")
    order_item_quantity: int = Field(default=5000, alias="Order Item Quantity")
    order_item_product_price: float = Field(default=45.0, alias="Order Item Product Price")
    order_item_discount: float = Field(default=5.0, alias="Order Item Discount")
    order_item_discount_rate: float = Field(default=0.1, alias="Order Item Discount Rate")
    customer_segment: str = Field(default="Corporate", alias="Customer Segment")
    market: str = Field(default="Pacific Asia", alias="Market")
    order_region: str = Field(default="Southeast Asia", alias="Order Region")
    order_country: str = Field(default="Taiwan", alias="Order Country")
    category_name: str = Field(default="Technology", alias="Category Name")
    department_name: str = Field(default="Technology", alias="Department Name")
    product_price: float = Field(default=45.0, alias="Product Price")
    simulated_delay_days: Optional[int] = 14

    # Microchip Business & Optimization Constraints
    budget: float = 20000.0
    max_delivery_days: int = 7
    required_quantity: int = 5000
    supplier_capacity: int = 6000

    # Optional dynamic mitigation options
    options: Optional[Dict[str, Dict[str, Union[float, int]]]] = None


class PrescribeResponse(BaseModel):
    """
    Unified prescriptive analytics response:
    ML Delay Prediction -> Prescriptive PuLP Optimization -> Recommended Action
    """
    shipment_id: str
    prediction: LogisticsPredictionResponse
    optimization: Dict[str, Any]


# ============================================================================
# 4. Database & Decision Tracking Schemas
# ============================================================================
class ManagerDecisionRequest(BaseModel):
    shipment_id: str
    manager_decision: str
    notes: Optional[str] = None


class OutcomeEvaluationRequest(BaseModel):
    shipment_id: str
    actual_delivery_days: int
    actual_cost: float
    delay_occurred: int = 0
    decision_effective: int = 1
    feedback_notes: Optional[str] = None
