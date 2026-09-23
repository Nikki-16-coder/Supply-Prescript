"""
Complete Closed-Loop Integration Test for SupplyPrescript
Simulates full user journey from Frontend Dashboard against live FastAPI & SQLite backend:
1. Static files check
2. Health check
3. ML Delay Risk Prediction
4. Prescriptive Optimization (PuLP)
5. Full Closed-Loop Prescribe (ML -> PuLP -> DB Write-back)
6. Manager Decision Approval
7. Post-Delivery Outcome Evaluation
8. Audit Trail & Analytics KPIs
9. Infeasible / Constraint Boundary Cases
10. ML Metrics Verification
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://127.0.0.1:8000"

def is_server_running(url=BASE_URL):
    try:
        req = urllib.request.Request(f"{url}/", method="GET")
        with urllib.request.urlopen(req, timeout=1) as resp:
            return resp.status == 200
    except Exception:
        return False

def ensure_server_running():
    if is_server_running():
        return None
    import uvicorn
    from backend.main import app

    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    for _ in range(50):
        time.sleep(0.1)
        if is_server_running():
            break
    return server

def request_json(path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"} if data else {}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            try:
                parsed = json.loads(content)
            except Exception:
                parsed = content
            return status, parsed
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        try:
            parsed_err = json.loads(err_content)
        except Exception:
            parsed_err = err_content
        return e.code, parsed_err

def run_tests():
    print("=" * 70)
    print(" SUPPLYPRESCRIPT - END-TO-END INTEGRATION TEST SUITE")
    print("=" * 70)
    
    passes = 0
    total = 0

    def assert_test(name, condition, details=""):
        nonlocal passes, total
        total += 1
        if condition:
            passes += 1
            print(f" [PASS] {name}")
            if details:
                print(f"        -> {details}")
        else:
            print(f" [FAIL] {name}")
            if details:
                print(f"        -> {details}")

    # 1. Static Files Check
    print("\n--- 1. Frontend Static Assets ---")
    status, _ = request_json("/dashboard/index.html")
    assert_test("Dashboard HTML Served", status == 200, f"Status {status}")
    status, _ = request_json("/dashboard/app.js")
    assert_test("Dashboard JS Served", status == 200, f"Status {status}")
    status, _ = request_json("/dashboard/style.css")
    assert_test("Dashboard CSS Served", status == 200, f"Status {status}")

    # 2. Health Check
    print("\n--- 2. Health & API Root ---")
    status, data = request_json("/")
    assert_test("Root API Status", status == 200 and data.get("message") == "SupplyPrescript Backend is running", str(data))

    # 3. Standalone ML Delay Prediction
    print("\n--- 3. ML Delay Risk Prediction (DataCo Trained) ---")
    ml_payload = {
        "shipment_id": "TEST-CHIP-001",
        "Days for shipment (scheduled)": 2,
        "Shipping Mode": "Second Class",
        "Order Item Quantity": 5000,
        "Order Item Product Price": 45.0,
        "Order Item Discount": 5.0,
        "Order Item Discount Rate": 0.1,
        "Customer Segment": "Corporate",
        "Market": "Pacific Asia",
        "Order Region": "Southeast Asia",
        "Order Country": "Taiwan",
        "Category Name": "Technology",
        "Department Name": "Technology",
        "Product Price": 45.0,
        "simulated_delay_days": 14
    }
    status, ml_res = request_json("/predict", method="POST", data=ml_payload)
    assert_test(
        "ML Delay Prediction Output Contract",
        status == 200 and "delay_probability" in ml_res and "predicted_delay_days" in ml_res,
        f"delay_prob={ml_res.get('delay_probability')}, predicted_delay_days={ml_res.get('predicted_delay_days')}"
    )

    # 4. Standalone Optimization
    print("\n--- 4. Prescriptive Optimization (PuLP MILP Solver) ---")
    opt_payload = {
        "budget": 20000.0,
        "max_delivery_days": 7,
        "required_quantity": 5000,
        "supplier_capacity": 6000,
        "predicted_delay_days": ml_res.get("predicted_delay_days", 14)
    }
    status, opt_res = request_json("/optimize", method="POST", data=opt_payload)
    assert_test(
        "PuLP Optimization Solved",
        status == 200 and opt_res.get("status") == "Optimal" and opt_res.get("recommended_action") == "Air Freight",
        f"Status={opt_res.get('status')}, Action={opt_res.get('recommended_action')}, Cost=${opt_res.get('chosen_option', {}).get('cost')}"
    )

    # 5. Full Closed-Loop Workflow: Shipment Entry -> Prescribe
    print("\n--- 5. Full Closed-Loop Decision Workflow: Prescribe ---")
    prescribe_payload = {
        "shipment_id": "CHIP-LIVE-VERIFY-01",
        "supplier_name": "TSMC Wafer Fab 18",
        "component": "4nm AI Accelerators",
        "scheduled_days": 2,
        "shipping_mode": "Second Class",
        "order_item_quantity": 5000,
        "order_item_product_price": 45.0,
        "order_item_discount": 5.0,
        "order_item_discount_rate": 0.1,
        "customer_segment": "Corporate",
        "market": "Pacific Asia",
        "order_region": "Southeast Asia",
        "order_country": "Taiwan",
        "category_name": "Technology",
        "department_name": "Technology",
        "product_price": 45.0,
        "simulated_delay_days": 14,
        "budget": 20000.0,
        "max_delivery_days": 7,
        "required_quantity": 5000,
        "supplier_capacity": 6000
    }
    status, pres_res = request_json("/prescribe", method="POST", data=prescribe_payload)
    assert_test(
        "Unified Prescribe Pipeline (ML + PuLP + DB Write)",
        status == 200 and "prediction" in pres_res and "optimization" in pres_res,
        f"Recommended Action: {pres_res.get('optimization', {}).get('recommended_action')}"
    )

    # 6. Manager Decision Approval Write-Back
    print("\n--- 6. Manager Decision Approval Write-Back ---")
    decision_payload = {
        "shipment_id": "CHIP-LIVE-VERIFY-01",
        "manager_decision": "Air Freight",
        "notes": "Approved expedited air freight to prevent assembly line stoppage."
    }
    status, dec_res = request_json("/decision", method="POST", data=decision_payload)
    assert_test(
        "Manager Decision Recorded to SQLite",
        status == 200 and dec_res.get("status") == "success",
        str(dec_res.get("message"))
    )

    # 7. Post-Delivery Outcome Evaluation
    print("\n--- 7. Post-Delivery Outcome Evaluation ---")
    outcome_payload = {
        "shipment_id": "CHIP-LIVE-VERIFY-01",
        "actual_delivery_days": 2,
        "actual_cost": 15000.0,
        "delay_occurred": 0,
        "decision_effective": 1,
        "feedback_notes": "Fab delivery on schedule. No manufacturing downtime recorded."
    }
    status, out_res = request_json("/outcome", method="POST", data=outcome_payload)
    assert_test(
        "Outcome Recorded & Closed Loop Completed",
        status == 200 and out_res.get("status") == "success",
        f"Outcome ID={out_res.get('outcome_id')}"
    )

    # 8. SQLite Audit Trail & Analytics KPIs
    print("\n--- 8. SQLite Audit Trail & Analytics Verification ---")
    status, history = request_json("/history/CHIP-LIVE-VERIFY-01")
    assert_test(
        "Shipment Audit Trail Retrieved",
        status == 200 and history.get("shipment") is not None and len(history.get("decisions", [])) > 0 and len(history.get("outcomes", [])) > 0,
        f"Decisions: {len(history.get('decisions', []))}, Outcomes: {len(history.get('outcomes', []))}"
    )

    status, analytics = request_json("/analytics")
    assert_test(
        "Aggregated Analytics KPIs Computed",
        status == 200 and analytics.get("total_shipments_tracked", 0) > 0 and "decision_effectiveness_pct" in analytics,
        f"Shipments: {analytics.get('total_shipments_tracked')}, Effectiveness: {analytics.get('decision_effectiveness_pct')}%"
    )

    # 9. Infeasible Capacity Test Case
    print("\n--- 9. Business Constraint Infeasibility Check ---")
    infeasible_payload = {
        "budget": 30000.0,
        "max_delivery_days": 7,
        "required_quantity": 7500,
        "supplier_capacity": 5000,
        "predicted_delay_days": 14
    }
    status, inf_res = request_json("/optimize", method="POST", data=infeasible_payload)
    assert_test(
        "Supplier Capacity Infeasibility Detection",
        status == 200 and inf_res.get("status") == "Infeasible",
        f"Message: {inf_res.get('message')}"
    )

    # 10. ML Metrics Check
    print("\n--- 10. ML Model Metrics Endpoint ---")
    status, metrics = request_json("/ml/metrics")
    assert_test(
        "ML Evaluation Metrics Served",
        status == 200 and "accuracy" in metrics and "roc_auc" in metrics,
        f"Accuracy: {metrics.get('accuracy')}, ROC-AUC: {metrics.get('roc_auc')}"
    )

    # 11. Day 2 Input Validation & Business Constraint Robustness
    print("\n--- 11. Day 2 Input Validation & Business Constraint Robustness ---")

    # 11a. Zero / Negative Quantity
    status, res = request_json("/prescribe", method="POST", data={
        "shipment_id": "CHIP-INV-QTY",
        "required_quantity": 0,
        "supplier_capacity": 5000,
    })
    assert_test(
        "Reject Zero Quantity (HTTP 422)",
        status == 422 and ("greater than 0" in str(res).lower() or "positive" in str(res).lower()),
        f"Status: {status}, Response: {res}"
    )

    status, res = request_json("/prescribe", method="POST", data={
        "shipment_id": "CHIP-INV-QTY",
        "required_quantity": -500,
        "supplier_capacity": 5000,
    })
    assert_test(
        "Reject Negative Quantity (HTTP 422)",
        status == 422 and ("greater than 0" in str(res).lower() or "positive" in str(res).lower()),
        f"Status: {status}, Response: {res}"
    )

    # 11b. Invalid Supplier Capacity
    status, res = request_json("/prescribe", method="POST", data={
        "shipment_id": "CHIP-INV-CAP",
        "required_quantity": 1000,
        "supplier_capacity": 0,
    })
    assert_test(
        "Reject Zero Supplier Capacity (HTTP 422)",
        status == 422 and ("greater than 0" in str(res).lower() or "positive" in str(res).lower()),
        f"Status: {status}, Response: {res}"
    )

    # 11c. Invalid Mitigation Budget
    status, res = request_json("/prescribe", method="POST", data={
        "shipment_id": "CHIP-INV-BUDGET",
        "budget": -1000.0,
    })
    assert_test(
        "Reject Negative Budget (HTTP 422)",
        status == 422 and ("greater than or equal to 0" in str(res).lower() or "non-negative" in str(res).lower()),
        f"Status: {status}, Response: {res}"
    )

    # 11d. Invalid Max Delivery / SLA Days
    status, res = request_json("/prescribe", method="POST", data={
        "shipment_id": "CHIP-INV-SLA",
        "max_delivery_days": 0,
    })
    assert_test(
        "Reject Non-Positive SLA Days (HTTP 422)",
        status == 422 and ("greater than 0" in str(res).lower() or "positive" in str(res).lower()),
        f"Status: {status}, Response: {res}"
    )

    # 11e. Invalid Disruption Duration
    status, res = request_json("/prescribe", method="POST", data={
        "shipment_id": "CHIP-INV-DISRUPT",
        "simulated_delay_days": -10,
    })
    assert_test(
        "Reject Negative Disruption Duration (HTTP 422)",
        status == 422 and ("greater than or equal to 0" in str(res).lower() or "non-negative" in str(res).lower()),
        f"Status: {status}, Response: {res}"
    )

    # 11f. Empty / Blank Shipment ID
    status, res = request_json("/prescribe", method="POST", data={
        "shipment_id": "   ",
    })
    assert_test(
        "Reject Whitespace Shipment ID (HTTP 422)",
        status == 422 and "empty" in str(res).lower(),
        f"Status: {status}, Response: {res}"
    )

    # 11g. Capacity Deficit Preserved as Infeasible (PuLP Business Constraint)
    deficit_payload = {
        "shipment_id": "CHIP-DEFICIT-01",
        "required_quantity": 8000,
        "supplier_capacity": 5000,
        "budget": 25000.0,
        "max_delivery_days": 7,
    }
    status, def_res = request_json("/prescribe", method="POST", data=deficit_payload)
    assert_test(
        "Prescribe Infeasibility Detection on Allocation Deficit",
        status == 200 and def_res.get("optimization", {}).get("status") == "Infeasible",
        f"Status: {def_res.get('optimization', {}).get('status')}, Message: {def_res.get('optimization', {}).get('message')}"
    )

    # 12. History & Listing Endpoints Contract
    print("\n--- 12. History & Listing Endpoints Contract ---")
    status, decisions = request_json("/history/decisions")
    assert_test(
        "History Decisions Listing Endpoint",
        status == 200 and isinstance(decisions, list) and len(decisions) > 0,
        f"Retrieved {len(decisions)} decision records"
    )

    status, outcomes = request_json("/history/outcomes")
    assert_test(
        "History Outcomes Listing Endpoint",
        status == 200 and isinstance(outcomes, list) and len(outcomes) > 0,
        f"Retrieved {len(outcomes)} outcome records"
    )

    status, shipments = request_json("/history/shipments")
    assert_test(
        "History Shipments Listing Endpoint",
        status == 200 and isinstance(shipments, list) and len(shipments) > 0,
        f"Retrieved {len(shipments)} shipment records"
    )

    # 13. Missing-Resource Handling (HTTP 404)
    print("\n--- 13. Missing-Resource Handling (HTTP 404) ---")
    status, res = request_json("/decision", method="POST", data={
        "shipment_id": "CHIP-NONEXISTENT-999",
        "manager_decision": "Air Freight",
    })
    assert_test(
        "Reject Decision for Untracked Shipment (HTTP 404)",
        status == 404 and "no optimization decision" in str(res).lower(),
        f"Status: {status}, Response: {res}"
    )

    status, res = request_json("/outcome", method="POST", data={
        "shipment_id": "CHIP-NONEXISTENT-999",
        "actual_delivery_days": 2,
        "actual_cost": 15000.0,
        "decision_effective": 1,
    })
    assert_test(
        "Reject Outcome for Untracked Shipment (HTTP 404)",
        status == 404 and "no shipment found" in str(res).lower(),
        f"Status: {status}, Response: {res}"
    )

    status, res = request_json("/history/CHIP-NONEXISTENT-999")
    assert_test(
        "Reject Audit Trail for Untracked Shipment (HTTP 404)",
        status == 404 and "no records found" in str(res).lower(),
        f"Status: {status}, Response: {res}"
    )

    # 14. Manager Decision Schema Validation (HTTP 422)
    print("\n--- 14. Manager Decision Schema Validation (HTTP 422) ---")
    status, res = request_json("/decision", method="POST", data={
        "shipment_id": "CHIP-LIVE-VERIFY-01",
        "manager_decision": "   ",
    })
    assert_test(
        "Reject Whitespace Manager Decision (HTTP 422)",
        status == 422 and "empty" in str(res).lower(),
        f"Status: {status}, Response: {res}"
    )

    status, res = request_json("/decision", method="POST", data={
        "shipment_id": "   ",
        "manager_decision": "Air Freight",
    })
    assert_test(
        "Reject Whitespace Shipment ID on Decision (HTTP 422)",
        status == 422 and "empty" in str(res).lower(),
        f"Status: {status}, Response: {res}"
    )

    # 15. Post-Delivery Outcome Schema Validation (HTTP 422)
    print("\n--- 15. Post-Delivery Outcome Schema Validation (HTTP 422) ---")
    status, res = request_json("/outcome", method="POST", data={
        "shipment_id": "CHIP-LIVE-VERIFY-01",
        "actual_delivery_days": -2,
        "actual_cost": 5000.0,
    })
    assert_test(
        "Reject Negative Actual Delivery Days (HTTP 422)",
        status == 422 and ("greater than or equal to 0" in str(res).lower() or "non-negative" in str(res).lower() or "ge" in str(res).lower()),
        f"Status: {status}, Response: {res}"
    )

    status, res = request_json("/outcome", method="POST", data={
        "shipment_id": "CHIP-LIVE-VERIFY-01",
        "actual_delivery_days": 3,
        "actual_cost": -500.0,
    })
    assert_test(
        "Reject Negative Actual Cost (HTTP 422)",
        status == 422 and ("greater than or equal to 0" in str(res).lower() or "non-negative" in str(res).lower() or "ge" in str(res).lower()),
        f"Status: {status}, Response: {res}"
    )

    status, res = request_json("/outcome", method="POST", data={
        "shipment_id": "CHIP-LIVE-VERIFY-01",
        "actual_delivery_days": 3,
        "actual_cost": 5000.0,
        "decision_effective": 2,
    })
    assert_test(
        "Reject Out-of-Range Decision Effective Flag (HTTP 422)",
        status == 422 and ("less than or equal to 1" in str(res).lower() or "le" in str(res).lower()),
        f"Status: {status}, Response: {res}"
    )

    status, res = request_json("/outcome", method="POST", data={
        "shipment_id": "   ",
        "actual_delivery_days": 3,
        "actual_cost": 5000.0,
    })
    assert_test(
        "Reject Whitespace Shipment ID on Outcome (HTTP 422)",
        status == 422 and "empty" in str(res).lower(),
        f"Status: {status}, Response: {res}"
    )

    # 16. Explicit ML -> Prescription Handoff & Closed-Loop Decoupling
    print("\n--- 16. Explicit ML -> Prescription Handoff & Closed-Loop Decoupling ---")
    disrupted_payload = {
        "shipment_id": "CHIP-HANDOFF-DISRUPTED",
        "simulated_delay_days": 14,
        "budget": 20000.0,
        "max_delivery_days": 7,
        "required_quantity": 5000,
        "supplier_capacity": 6000,
    }
    status, d_res = request_json("/prescribe", method="POST", data=disrupted_payload)
    pred_days = d_res.get("prediction", {}).get("predicted_delay_days")
    opt_accept_delay = d_res.get("optimization", {}).get("options", {}).get("Accept Delay", {}).get("delivery_days")
    assert_test(
        "ML Disruption Delay Injected into Optimization Accept Delay Option",
        status == 200 and pred_days == 14 and opt_accept_delay == 14,
        f"Prediction={pred_days}, PuLP Accept Delay={opt_accept_delay}"
    )

    rec_action = d_res.get("optimization", {}).get("recommended_action")
    assert_test(
        "PuLP Excludes Accept Delay When ML Delay Exceeds SLA",
        status == 200 and rec_action == "Air Freight",
        f"Recommended Action: {rec_action} (SLA=7 days, Accept Delay=14 days)"
    )

    normal_payload = {
        "shipment_id": "CHIP-HANDOFF-NORMAL",
        "simulated_delay_days": 0,
        "budget": 20000.0,
        "max_delivery_days": 7,
        "required_quantity": 5000,
        "supplier_capacity": 6000,
    }
    status, n_res = request_json("/prescribe", method="POST", data=normal_payload)
    n_pred_days = n_res.get("prediction", {}).get("predicted_delay_days")
    n_opt_days = n_res.get("optimization", {}).get("options", {}).get("Accept Delay", {}).get("delivery_days")
    n_action = n_res.get("optimization", {}).get("recommended_action")
    assert_test(
        "PuLP Optimal Solver Selects Accept Delay for Zero Predicted Disruption",
        status == 200 and n_pred_days == 0 and n_opt_days == 0 and n_action == "Accept Delay",
        f"Action: {n_action}, Delivery Days: {n_opt_days}, Cost: $0"
    )

    status, hist = request_json("/history/CHIP-HANDOFF-DISRUPTED")
    assert_test(
        "Database Audit Trail Verifies Multi-Entity Closed-Loop Linkage",
        status == 200
        and hist.get("shipment", {}).get("shipment_id") == "CHIP-HANDOFF-DISRUPTED"
        and len(hist.get("predictions", [])) > 0
        and len(hist.get("decisions", [])) > 0
        and hist.get("decisions", [])[0].get("recommended_action") == "Air Freight",
        f"Linked Shipment: {hist.get('shipment', {}).get('shipment_id')}, Predictions: {len(hist.get('predictions', []))}, Decisions: {len(hist.get('decisions', []))}"
    )

    print("\n" + "=" * 70)
    print(f" TEST RESULTS SUMMARY: {passes}/{total} TESTS PASSED")
    print("=" * 70)

    if passes == total:
        print("\nSUCCESS: All endpoints and full closed-loop workflow verified!")
        return 0
    else:
        print(f"\nFAILURE: {total - passes} tests failed.")
        return 1

if __name__ == "__main__":
    server = ensure_server_running()
    try:
        sys.exit(run_tests())
    finally:
        if server:
            server.should_exit = True

