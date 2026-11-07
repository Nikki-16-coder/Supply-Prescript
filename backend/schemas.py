"""
SupplyPrescript - Backend API Schemas (Pydantic Models)

Separates:
1. Historical logistics delay prediction features (DataCo-trained ML layer)
2. Microchip business & supply chain constraints (PuLP optimization layer)
3. Database write-back schemas for closed-loop decision tracking and outcome evaluation
"""

from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ============================================================================
# 1. Existing Optimization Request (Preserved for backwards compatibility,
#    now optionally accepting dynamic options)
# ============================================================================
class ShipmentRequest(BaseModel):
    budget: float = Field(..., ge=0.0, description="Mitigation budget must be non-negative (>= 0)")
    max_delivery_days: int = Field(..., gt=0, description="Maximum delivery / SLA days must be positive (> 0)")
    required_quantity: int = Field(..., gt=0, description="Required quantity must be positive (> 0)")
    supplier_capacity: int = Field(..., gt=0, description="Supplier capacity must be positive (> 0)")
    predicted_delay_days: int = Field(..., ge=0, description="Predicted delay days must be non-negative (>= 0)")
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

    shipment_id: str = Field(default="SHP001", min_length=1, description="Shipment consignment identifier")
    scheduled_days: int = Field(default=4, ge=0, alias="Days for shipment (scheduled)", description="Scheduled transit days must be non-negative")
    shipping_mode: str = Field(default="Standard Class", alias="Shipping Mode")
    order_item_quantity: int = Field(default=100, gt=0, alias="Order Item Quantity", description="Quantity must be positive (> 0)")
    order_item_product_price: float = Field(default=50.0, ge=0.0, alias="Order Item Product Price", description="Product price must be non-negative")
    order_item_discount: float = Field(default=0.0, ge=0.0, alias="Order Item Discount", description="Discount must be non-negative")
    order_item_discount_rate: float = Field(default=0.0, ge=0.0, le=1.0, alias="Order Item Discount Rate", description="Discount rate must be between 0.0 and 1.0")
    customer_segment: str = Field(default="Corporate", alias="Customer Segment")
    market: str = Field(default="Pacific Asia", alias="Market")
    order_region: str = Field(default="Southeast Asia", alias="Order Region")
    order_country: str = Field(default="Taiwan", alias="Order Country")
    category_name: str = Field(default="Technology", alias="Category Name")
    department_name: str = Field(default="Technology", alias="Department Name")
    product_price: float = Field(default=50.0, ge=0.0, alias="Product Price", description="Unit price must be non-negative")
    simulated_delay_days: Optional[int] = Field(default=None, ge=0, description="Projected disruption duration must be non-negative (>= 0)")

    @field_validator("shipment_id")
    @classmethod
    def validate_shipment_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Shipment ID cannot be empty or whitespace.")
        return v.strip()


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
    shipment_id: str = Field(default="SHP001", min_length=1, description="Shipment consignment identifier")
    supplier_name: Optional[str] = "Primary Microchip Fab"
    component: Optional[str] = "Microchips"

    # Logistics features for ML delay prediction
    scheduled_days: int = Field(default=2, ge=0, alias="Days for shipment (scheduled)", description="Scheduled transit days must be non-negative")
    shipping_mode: str = Field(default="Second Class", alias="Shipping Mode")
    order_item_quantity: int = Field(default=5000, gt=0, alias="Order Item Quantity", description="Order quantity must be positive (> 0)")
    order_item_product_price: float = Field(default=45.0, ge=0.0, alias="Order Item Product Price", description="Product price must be non-negative")
    order_item_discount: float = Field(default=5.0, ge=0.0, alias="Order Item Discount", description="Discount must be non-negative")
    order_item_discount_rate: float = Field(default=0.1, ge=0.0, le=1.0, alias="Order Item Discount Rate", description="Discount rate must be between 0.0 and 1.0")
    customer_segment: str = Field(default="Corporate", alias="Customer Segment")
    market: str = Field(default="Pacific Asia", alias="Market")
    order_region: str = Field(default="Southeast Asia", alias="Order Region")
    order_country: str = Field(default="Taiwan", alias="Order Country")
    category_name: str = Field(default="Technology", alias="Category Name")
    department_name: str = Field(default="Technology", alias="Department Name")
    product_price: float = Field(default=45.0, ge=0.0, alias="Product Price", description="Unit price must be non-negative")
    simulated_delay_days: Optional[int] = Field(default=14, ge=0, description="Projected disruption duration must be non-negative (>= 0)")

    # Microchip Business & Optimization Constraints
    budget: float = Field(default=20000.0, ge=0.0, description="Mitigation budget must be non-negative (>= 0)")
    max_delivery_days: int = Field(default=7, gt=0, description="Assembly SLA delivery deadline must be positive (> 0)")
    required_quantity: int = Field(default=5000, gt=0, description="Required production volume must be positive (> 0)")
    supplier_capacity: int = Field(default=6000, gt=0, description="Supplier allocation capacity must be positive (> 0)")

    # Optional dynamic mitigation options
    options: Optional[Dict[str, Dict[str, Union[float, int]]]] = None

    @field_validator("shipment_id")
    @classmethod
    def validate_shipment_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Shipment ID cannot be empty or whitespace.")
        return v.strip()


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
    shipment_id: str = Field(..., min_length=1, description="Shipment identifier")
    manager_decision: str = Field(..., min_length=1, description="Selected mitigation decision")
    notes: Optional[str] = None

    @field_validator("shipment_id", "manager_decision")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace.")
        return v.strip()


class OutcomeEvaluationRequest(BaseModel):
    shipment_id: str = Field(..., min_length=1, description="Shipment identifier")
    actual_delivery_days: int = Field(..., ge=0, description="Actual realized delivery lead time must be non-negative")
    actual_cost: float = Field(..., ge=0.0, description="Actual incurred cost must be non-negative")
    delay_occurred: int = Field(default=0, ge=0, le=1, description="Delay occurred indicator (0 or 1)")
    decision_effective: int = Field(default=1, ge=0, le=1, description="Decision effective indicator (0 or 1)")
    feedback_notes: Optional[str] = None

    @field_validator("shipment_id")
    @classmethod
    def validate_shipment_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Shipment ID cannot be empty or whitespace.")
        return v.strip()


# ============================================================================
# 5. User Authentication & Authorization Schemas
# ============================================================================
class LoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=1, description="Username or corporate email address")
    password: str = Field(..., min_length=1, description="Account password")

    @field_validator("username_or_email", "password")
    @classmethod
    def validate_credentials(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace.")
        return v.strip()


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    full_name: Optional[str] = None
    is_active: int = 1
    auth_provider: Optional[str] = "local"


class LoginResponse(BaseModel):
    status: str = "success"
    token: str
    token_type: str = "Bearer"
    expires_at: str
    user: UserResponse
    redirect_url: str


class LogoutResponse(BaseModel):
    status: str = "success"
    message: str = "Successfully logged out."


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., min_length=5, max_length=100, description="Corporate email address")
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)")
    role: str = Field(default="analyst", description="Role: admin, manager, or analyst")
    full_name: Optional[str] = Field(default=None, description="Full display name")

    @field_validator("username", "email")
    @classmethod
    def validate_user_fields(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace.")
        return v.strip().lower()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("admin", "manager", "analyst"):
            raise ValueError("Role must be one of: admin, manager, analyst")
        return clean


class UserStatusUpdateRequest(BaseModel):
    is_active: bool = Field(..., description="Active flag for account")


class UserRoleUpdateRequest(BaseModel):
    role: str = Field(..., description="Role: admin, manager, or analyst")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("admin", "manager", "analyst"):
            raise ValueError("Role must be one of: admin, manager, analyst")
        return clean


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=100, description="Account registered email address")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Email cannot be empty or whitespace.")
        return v.strip().lower()


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10, description="Password reset token")
    new_password: str = Field(..., min_length=6, description="New password (minimum 6 characters)")

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Reset token cannot be empty.")
        return v.strip()




