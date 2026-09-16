"""
SupplyPrescript - Prescriptive Optimization Engine
MILP Solver using PuLP for Microchip Supply Chain Mitigation Actions.

Supports:
- Dynamic and configurable mitigation options (costs and lead times)
- Default fallback options (Air Freight, Secondary Supplier, Accept Delay)
- Supplier capacity check
- Budget and SLA maximum delivery days constraints
"""

from typing import Dict, Any, Optional, Union
import pulp

DEFAULT_MITIGATION_OPTIONS = {
    "Air Freight": {
        "cost": 15000,
        "delivery_days": 2,
    },
    "Secondary Supplier": {
        "cost": 18000,
        "delivery_days": 4,
    },
    "Accept Delay": {
        "cost": 0,
        "delivery_days": None,  # Populated dynamically with predicted_delay_days
    },
}


def build_options_dict(
    predicted_delay_days: int,
    custom_options: Optional[Dict[str, Dict[str, Union[float, int]]]] = None,
) -> Dict[str, Dict[str, Union[float, int]]]:
    """
    Builds the options dictionary, using custom options if provided,
    or falling back to standard mitigation alternatives.
    """
    if custom_options:
        options = {}
        for name, details in custom_options.items():
            cost = float(details.get("cost", 0))
            if cost < 0:
                raise ValueError(f"Option '{name}' cost cannot be negative.")
            delivery_days = details.get("delivery_days")
            if delivery_days is None:
                delivery_days = int(predicted_delay_days)
            else:
                delivery_days = int(delivery_days)
            if delivery_days < 0:
                raise ValueError(f"Option '{name}' delivery days cannot be negative.")
            options[name] = {"cost": cost, "delivery_days": delivery_days}
        return options

    # Fallback default options
    return {
        "Air Freight": {
            "cost": 15000,
            "delivery_days": 2,
        },
        "Secondary Supplier": {
            "cost": 18000,
            "delivery_days": 4,
        },
        "Accept Delay": {
            "cost": 0,
            "delivery_days": int(predicted_delay_days),
        },
    }


def optimize_shipment(
    budget: float,
    max_delivery_days: int,
    required_quantity: int,
    supplier_capacity: int,
    predicted_delay_days: int,
    options: Optional[Dict[str, Dict[str, Union[float, int]]]] = None,
) -> Dict[str, Any]:
    """
    Solves binary integer linear programming problem to select the optimal
    supply chain disruption mitigation alternative.
    """
    # 0. Practical Input Validation
    if required_quantity <= 0:
        raise ValueError("Required quantity must be positive (> 0).")
    if supplier_capacity <= 0:
        raise ValueError("Supplier capacity must be positive (> 0).")
    if budget < 0:
        raise ValueError("Mitigation budget cannot be negative (>= 0).")
    if max_delivery_days <= 0:
        raise ValueError("Maximum delivery days (SLA) must be positive (> 0).")
    if predicted_delay_days < 0:
        raise ValueError("Predicted delay days cannot be negative (>= 0).")

    resolved_options = build_options_dict(predicted_delay_days, options)

    # 1. Supplier Capacity Infeasibility Check
    if required_quantity > supplier_capacity:
        return {
            "recommended_action": None,
            "status": "Infeasible",
            "message": "Required quantity exceeds supplier capacity.",
            "options": resolved_options,
        }

    # 2. PuLP Optimization Formulation
    problem = pulp.LpProblem("Shipment_Optimization", pulp.LpMinimize)

    # Binary decision variables for each alternative
    decisions = {
        name: pulp.LpVariable(f"option_{i}", cat="Binary")
        for i, name in enumerate(resolved_options)
    }

    # Constraint 1: Select exactly one alternative
    problem += pulp.lpSum(decisions.values()) == 1

    # Constraint 2: Budget constraint
    problem += (
        pulp.lpSum(decisions[name] * resolved_options[name]["cost"] for name in resolved_options)
        <= budget
    )

    # Constraint 3: Delivery time constraint
    problem += (
        pulp.lpSum(decisions[name] * resolved_options[name]["delivery_days"] for name in resolved_options)
        <= max_delivery_days
    )

    # Constraint 4: Supplier capacity feasibility condition
    problem += required_quantity <= supplier_capacity

    # Objective Function: Minimize Total Mitigation Cost
    problem += pulp.lpSum(
        decisions[name] * resolved_options[name]["cost"] for name in resolved_options
    )

    # Solve MILP using default CBC solver silently
    problem.solve(pulp.PULP_CBC_CMD(msg=False))

    status = pulp.LpStatus[problem.status]

    if status != "Optimal":
        return {
            "recommended_action": None,
            "status": status,
            "message": "No feasible shipment option satisfies the given constraints.",
            "options": resolved_options,
        }

    selected_option = None
    for name, variable in decisions.items():
        if variable.value() == 1:
            selected_option = name
            break

    chosen_details = resolved_options.get(selected_option)

    return {
        "recommended_action": selected_option,
        "status": status,
        "chosen_option": chosen_details,
        "options": resolved_options,
    }