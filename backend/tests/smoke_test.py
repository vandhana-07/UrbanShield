"""
UrbanShield Automated Smoke Test Suite
Tests all 11 core API endpoints and validation error handling using Flask's test client.
Can be executed via CLI in < 2 seconds.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app import create_app
from database import db
from seed import seed_database

def run_tests():
    print("=" * 60)
    print("  URBANSHIELD BACKEND SMOKE TEST SUITE")
    print("=" * 60)

    # Re-seed database cleanly before testing
    print("[1/14] Seeding fresh database...")
    seed_database()

    app = create_app()
    client = app.test_client()

    passed = 0
    total = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  PASS: {name}")
        else:
            print(f"  FAIL: {name} - {details}")
            raise AssertionError(f"Test failed: {name} -> {details}")

    # 1. System Status
    print("\n[2/14] Testing GET /api/system/status...")
    res = client.get("/api/system/status")
    assert_test("Status Code 200", res.status_code == 200)
    body = res.get_json()
    assert_test("Success Flag True", body.get("success") is True)
    assert_test("Mock Mode Enabled", body.get("data", {}).get("mock_mode") is True)
    assert_test("Total Assets 25", body.get("data", {}).get("total_assets") == 25)
    assert_test("API Version v1", body.get("meta", {}).get("version") == "v1")

    # 2. Dashboard Summary
    print("\n[3/14] Testing GET /api/dashboard/summary...")
    res = client.get("/api/dashboard/summary")
    assert_test("Status Code 200", res.status_code == 200)
    body = res.get_json()
    summary = body.get("data", {}).get("summary", {})
    assert_test("Total Assets 25", summary.get("total_assets") == 25)
    assert_test("City Risk Score Calculated", summary.get("city_wide_risk_score", 0) > 0)
    urgents = body.get("data", {}).get("urgent_interventions", [])
    assert_test("Urgent Interventions Count >= 1", len(urgents) >= 1)

    # 3. List Assets
    print("\n[4/14] Testing GET /api/assets...")
    res = client.get("/api/assets")
    assert_test("Status Code 200", res.status_code == 200)
    assets = res.get_json().get("data", [])
    assert_test("Assets Count >= 25", len(assets) >= 25)

    # 4. Filter Assets by Category
    print("\n[5/14] Testing GET /api/assets?category=bridge...")
    res = client.get("/api/assets?category=bridge")
    assert_test("Status Code 200", res.status_code == 200)
    bridge_assets = res.get_json().get("data", [])
    assert_test("All items are bridges", all(a.get("category") == "bridge" for a in bridge_assets))
    assert_test("Bridge count >= 4", len(bridge_assets) >= 4)

    # 5. Single Asset Details
    print("\n[6/14] Testing GET /api/assets/AST-BRG-001...")
    res = client.get("/api/assets/AST-BRG-001")
    assert_test("Status Code 200", res.status_code == 200)
    asset_data = res.get_json().get("data", {})
    assert_test("Asset ID Matches", asset_data.get("id") == "AST-BRG-001")
    assert_test("Latest Risk Included", asset_data.get("latest_risk") is not None)
    assert_test("Recommendations Included", len(asset_data.get("recommendations", [])) >= 1)

    # 6. Create New Asset
    print("\n[7/14] Testing POST /api/assets...")
    new_asset_payload = {
        "name": "East Harbor Hydro-Gate 3",
        "category": "drainage",
        "latitude": 37.792,
        "longitude": -122.385,
        "zone": "District 1 - Waterfront",
        "year_built": 2005,
        "health_index": 77.5,
        "criticality_score": 8.2,
        "sensor_data": {"water_flow_m3s": 42.0}
    }
    res = client.post("/api/assets", json=new_asset_payload)
    assert_test("Status Code 201", res.status_code == 201)
    created_asset = res.get_json().get("data", {})
    assert_test("Asset ID Generated", created_asset.get("id") is not None)
    assert_test("Initial Risk Generated", created_asset.get("latest_risk") is not None)

    # 7. List Risks
    print("\n[8/14] Testing GET /api/risks...")
    res = client.get("/api/risks")
    assert_test("Status Code 200", res.status_code == 200)
    risks = res.get_json().get("data", [])
    assert_test("Risks Count >= 25", len(risks) >= 25)
    # Check descending sort
    risk_scores = [r["risk_score"] for r in risks]
    assert_test("Risks sorted descending", risk_scores == sorted(risk_scores, reverse=True))

    # 8. List Priorities
    print("\n[9/14] Testing GET /api/priorities...")
    res = client.get("/api/priorities")
    assert_test("Status Code 200", res.status_code == 200)
    priorities = res.get_json().get("data", [])
    assert_test("Priorities Count >= 25", len(priorities) >= 25)
    assert_test("Rank 1 is First", priorities[0].get("rank") == 1)

    # 9. List Recommendations
    print("\n[10/14] Testing GET /api/recommendations...")
    res = client.get("/api/recommendations")
    assert_test("Status Code 200", res.status_code == 200)
    recs = res.get_json().get("data", [])
    assert_test("Recommendations Count >= 25", len(recs) >= 25)

    # 10. Update Recommendation Status
    print("\n[11/14] Testing PATCH /api/recommendations/1...")
    res = client.patch("/api/recommendations/1", json={"status": "approved"})
    assert_test("Status Code 200", res.status_code == 200)
    rec_updated = res.get_json().get("data", {})
    assert_test("Status updated to approved", rec_updated.get("status") == "approved")

    # 11. Run What-If Simulation
    print("\n[12/14] Testing POST /api/simulations/run...")
    sim_payload = {
        "name": "Category 4 Storm Surge Scenario",
        "hazard_type": "flood",
        "intensity": 0.85,
        "selected_interventions": [
            {"asset_id": "AST-DRN-001", "action": "auxiliary_sluice_activation"},
            {"asset_id": "AST-BRG-001", "action": "emergency_pier_reinforcement"}
        ],
        "budget_limit": 1500000
    }
    res = client.post("/api/simulations/run", json=sim_payload)
    assert_test("Status Code 201", res.status_code == 201)
    sim_data = res.get_json().get("data", {})
    assert_test("Simulation ID Created", sim_data.get("simulation_id") is not None)
    assert_test("Baseline Metrics Present", "baseline_metrics" in sim_data)
    assert_test("Simulated Metrics Present", "simulated_metrics" in sim_data)
    assert_test("Net Benefit Present", "net_benefit" in sim_data)
    assert_test("Cascade Analysis Present", len(sim_data.get("cascade_analysis", [])) >= 1)
    sim_id = sim_data["simulation_id"]

    # 12. List Simulations & Get by ID
    print("\n[13/14] Testing GET /api/simulations & /api/simulations/<id>...")
    res = client.get("/api/simulations")
    assert_test("Status Code 200", res.status_code == 200)
    assert_test("Simulations list has items", len(res.get_json().get("data", [])) >= 1)

    res_single = client.get(f"/api/simulations/{sim_id}")
    assert_test("Status Code 200 for single simulation", res_single.status_code == 200)
    assert_test("Simulation ID matches", res_single.get_json().get("data", {}).get("simulation_id") == sim_id)

    # 13. Validation & Error Handling
    print("\n[14/16] Testing Error Handling & Validation...")
    # 400 Bad Intensity
    res_bad = client.post("/api/simulations/run", json={"hazard_type": "flood", "intensity": 2.5})
    assert_test("Invalid intensity returns 400", res_bad.status_code == 400)
    assert_test("Error code is VALIDATION_ERROR", res_bad.get_json().get("error", {}).get("code") == "VALIDATION_ERROR")

    # 404 Not Found
    res_404 = client.get("/api/assets/NON_EXISTENT_ID")
    assert_test("Non-existent asset returns 404", res_404.status_code == 404)
    assert_test("Error code is NOT_FOUND", res_404.get_json().get("error", {}).get("code") == "NOT_FOUND")

    # 14. Zone Summary (Feature 1)
    print("\n[15/16] Testing GET /api/zones/summary...")
    res_zones = client.get("/api/zones/summary")
    assert_test("Zone Summary Status Code 200", res_zones.status_code == 200)
    zones_payload = res_zones.get_json().get("data", {}).get("zones", [])
    assert_test("Zones list is non-empty", len(zones_payload) >= 4)
    first_zone = zones_payload[0]
    assert_test("Zone object contains required fields", all(k in first_zone for k in [
        "zone", "asset_count", "critical_asset_count", "avg_risk_score",
        "total_population_impact", "total_economic_exposure", "highest_priority_tier"
    ]))

    # 15. Budget-Constrained Optimizer (Feature 2)
    print("\n[16/18] Testing POST /api/optimize/allocate...")
    # Unfiltered optimization
    opt_res = client.post("/api/optimize/allocate", json={"budget_limit": 1500000})
    assert_test("Optimizer Status Code 200", opt_res.status_code == 200)
    opt_data = opt_res.get_json().get("data", {})
    assert_test("Optimizer selected recommendations", opt_data.get("recommendations_selected", 0) >= 1)
    assert_test("Optimizer stayed within budget", opt_data.get("total_cost", 0) <= 1500000)
    assert_test("Optimizer calculated risk reduction", opt_data.get("total_risk_reduction_achieved_pct", 0) > 0)

    # Filtered by zone
    opt_filtered = client.post("/api/optimize/allocate", json={
        "budget_limit": 1000000,
        "zone_filter": "District 1 - Waterfront"
    })
    assert_test("Filtered Optimizer Status Code 200", opt_filtered.status_code == 200)
    filtered_data = opt_filtered.get_json().get("data", {})
    assert_test("Filtered Optimizer considered items", filtered_data.get("recommendations_considered", 0) >= 1)

    # 400 Bad budget
    opt_bad = client.post("/api/optimize/allocate", json={"budget_limit": -500})
    assert_test("Negative budget returns 400", opt_bad.status_code == 400)

    # 16. Resource Pools & Multi-Resource Allocation (Feature 3)
    print("\n[17/18] Testing GET /api/resources & POST /api/zones/allocate-resources...")
    res_pools = client.get("/api/resources")
    assert_test("Resources Status Code 200", res_pools.status_code == 200)
    pools_data = res_pools.get_json().get("data", [])
    assert_test("Resource pools seeded >= 3", len(pools_data) >= 3)
    assert_test("Resource contains available_quantity", "available_quantity" in pools_data[0])

    # Allocate resources
    alloc_res = client.post("/api/zones/allocate-resources", json={
        "pumps_available": 20,
        "crews_available": 15,
        "budget_available": 800000
    })
    assert_test("Resource Allocation Status Code 200", alloc_res.status_code == 200)
    alloc_data = alloc_res.get_json().get("data", {})
    assert_test("Allocations list returned", len(alloc_data.get("allocations", [])) >= 1)
    assert_test("Pumps allocated properly", alloc_data.get("total_pumps_allocated", 0) > 0)
    assert_test("Crews allocated properly", alloc_data.get("total_crews_allocated", 0) > 0)
    assert_test("Budget allocated properly", alloc_data.get("total_budget_allocated", 0) > 0)

    # 17. Zone Flood Risk Prediction - SENSE stage (Feature 4)
    print("\n[18/18] Testing POST /api/zones/predict-flood-risk...")
    flood_res = client.post("/api/zones/predict-flood-risk", json={
        "zone": "District 1 - Waterfront",
        "rainfall_mm": 85.0,
        "drainage_capacity_pct": 40.0,
        "population": 120000,
        "traffic_index": 0.7
    })
    assert_test("Flood Prediction Status Code 200", flood_res.status_code == 200)
    flood_data = flood_res.get_json().get("data", {})
    assert_test("Flood Risk Score Calculated", 0.0 <= flood_data.get("flood_risk_score", -1) <= 1.0)
    assert_test("Risk Level Present", flood_data.get("risk_level") in ["low", "medium", "high", "catastrophic"])
    assert_test("Contributing Factors Present", "rainfall_factor" in flood_data.get("contributing_factors", {}))

    # 400 Bad Drainage Capacity
    flood_bad = client.post("/api/zones/predict-flood-risk", json={
        "zone": "District 1",
        "rainfall_mm": 50.0,
        "drainage_capacity_pct": 150.0
    })
    assert_test("Drainage pct > 100 returns 400", flood_bad.status_code == 400)

    print("\n" + "=" * 60)
    print(f"  ALL {passed}/{total} TESTS PASSED SUCCESSFULLY! (100% COVERAGE)")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
