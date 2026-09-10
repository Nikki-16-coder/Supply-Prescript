import pulp


def optimize_shipment(
    budget,
    max_delivery_days,
    required_quantity,
    supplier_capacity,
    predicted_delay_days
):

    options = {
        "Air Freight": {
            "cost": 15000,
            "delivery_days": 2
        },
        "Secondary Supplier": {
            "cost": 18000,
            "delivery_days": 4
        },
        "Accept Delay": {
            "cost": 0,
            "delivery_days": predicted_delay_days
        }
    }
    if required_quantity > supplier_capacity:
      return {
        "recommended_action": None,
        "status": "Infeasible",
        "message": "Required quantity exceeds supplier capacity.",
        "options": options
    }
    problem = pulp.LpProblem(
        "Shipment_Optimization",
        pulp.LpMinimize
    )

    decisions = {
        name: pulp.LpVariable(name, cat="Binary")
        for name in options
    }

    # Select exactly one option
    problem += pulp.lpSum(decisions.values()) == 1

    # Budget constraint
    problem += pulp.lpSum(
        decisions[name] * options[name]["cost"]
        for name in options
    ) <= budget

    # Delivery time constraint
    problem += pulp.lpSum(
        decisions[name] * options[name]["delivery_days"]
        for name in options
    ) <= max_delivery_days

    # Supplier capacity constraint
    problem += required_quantity <= supplier_capacity

    # Minimize cost
    problem += pulp.lpSum(
        decisions[name] * options[name]["cost"]
        for name in options
    )

    problem.solve(pulp.PULP_CBC_CMD(msg=False))

    status = pulp.LpStatus[problem.status]

    if status != "Optimal":
        return {
            "recommended_action": None,
            "status": status,
            "message": "No feasible shipment option satisfies the given constraints.",
            "options": options
        }

    selected_option = None

    for name, variable in decisions.items():
        if variable.value() == 1:
            selected_option = name

    return {
        "recommended_action": selected_option,
        "status": status,
        "options": options
    }