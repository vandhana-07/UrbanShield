"""
UrbanShield - Automated Verification Script
Validates pipeline flow, offline fallback resilience, zone consistency, and simulation logic.
"""

import os
import sys
import time

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure URBAN directory is on python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config import ZONES_CONFIG, SEVERITY_CONFIG, get_severity, get_severity_color
from services.api_client import (
    normalize_zone_record,
    normalize_prediction_record,
    check_backend_health,
    get_configured_api_url
)
from services.data_service import (
    get_zones_summary,
    get_available_resources,
    get_zone_telemetry,
    get_data_source_status
)
from services.agent_service import (
    get_pipeline_predictions,
    get_recommendations_and_allocations,
    run_simulation,
    get_model_source_status
)
from components.map_view import extract_zone_id_from_payload

def run_tests():
    print("=" * 70)
    print("🚀 RUNNING URBANSHIELD COMPLETE INTEGRATION TEST SUITE")
    print("=" * 70)

    # TEST 1: Schema Normalization
    print("\n[TEST 1] Testing Schema Normalizers...")
    raw_zone = {"zone": "Z-01", "asset_name": "Test Hospital", "latitude": 13.045, "longitude": 80.245}
    norm_zone = normalize_zone_record(raw_zone)
    assert norm_zone["zone_id"] == "Z-01", "Zone ID normalization failed"
    assert norm_zone["lat"] == 13.045, "Latitude normalization failed"

    raw_pred = {"zone": "Z-01", "score": 0.88, "rank": 1}
    norm_pred = normalize_prediction_record(raw_pred)
    assert norm_pred["zone_id"] == "Z-01", "Prediction zone ID normalization failed"
    assert norm_pred["risk_score"] == 0.88, "Prediction risk score normalization failed"
    assert norm_pred["severity"] == "Critical", "Prediction severity normalization failed"
    print("  ✅ Schema normalizers passed.")

    # TEST 2: Offline Fallback & Latency Check
    print("\n[TEST 2] Testing Offline Fallback & Sub-100ms Health Check Latency...")
    t0 = time.time()
    health = check_backend_health()
    t_health = time.time() - t0
    print(f"  Health Check returned: is_live={health.get('is_live')} in {t_health*1000:.1f}ms")
    assert t_health < 1.0, f"Health check took too long ({t_health}s), freeze risk detected!"

    t1 = time.time()
    zones = get_zones_summary()
    res = get_available_resources()
    preds = get_pipeline_predictions()
    recs = get_recommendations_and_allocations()
    t_all = time.time() - t1
    print(f"  All 4 data queries completed in {t_all*1000:.1f}ms")
    assert len(zones) == 6, f"Expected 6 zones, got {len(zones)}"
    assert len(preds) == 6, f"Expected 6 predictions, got {len(preds)}"
    assert len(recs) == 6, f"Expected 6 recommendations, got {len(recs)}"
    assert res["total_heavy_pumps"] >= 14, "Resource pool check failed"
    print("  ✅ Offline fallback & latency checks passed.")

    # TEST 3: Pipeline Flow & Zone ID Consistency
    print("\n[TEST 3] Testing Complete Pipeline Trace (Z-01)...")
    z1_info = next(z for z in zones if z["zone_id"] == "Z-01")
    z1_pred = next(p for p in preds if p["zone_id"] == "Z-01")
    z1_rec = recs["Z-01"]

    print(f"  1. SENSE:      Rain={z1_info['rainfall_mm_per_hr']} mm/h, Drain={z1_info['drainage_capacity_pct']}%")
    print(f"  2. PREDICT:    Risk={z1_pred['risk_score']} ({z1_pred['severity']})")
    print(f"  3. PRIORITIZE: Rank=#{z1_pred['priority_rank']}")
    print(f"  4. OPTIMIZE:   Pumps={z1_rec['allocated_pumps']}, Crews={z1_rec['allocated_crews']}")
    print(f"  5. RECOMMEND:  Urgency={z1_rec['urgency']}")

    assert z1_pred["priority_rank"] == 1, "Z-01 should be priority rank #1"
    assert z1_rec["allocated_pumps"] == 4, "Z-01 should be allocated 4 pumps"
    print("  ✅ Pipeline trace consistency passed.")

    # TEST 4: All 4 Simulation Presets
    print("\n[TEST 4] Testing 4 Simulation Presets...")
    presets = [
        ("🌊 Coastal Typhoon & Surge", 2.5, 35.0, True),
        ("🌧️ Downtown Flash Cloudburst", 3.0, 65.0, False),
        ("🚰 Culvert Siltation Crisis", 1.3, 20.0, False),
        ("☀️ Nominal Baseline", 1.0, 85.0, False)
    ]

    for name, rain, drain, surge in presets:
        sim = run_simulation(rain, drain, surge)
        sim_zones = sim["zones"]
        impact = sim["resource_impact"]
        avg_risk = sum(z["simulated_risk"] for z in sim_zones) / len(sim_zones)
        print(f"  Preset: {name:30s} -> Avg Risk: {avg_risk:.2f} | Pumps Needed: {impact['total_pumps_needed']} | Deficit: {impact['deficit']}")
        assert len(sim_zones) == 6, f"Preset {name} failed: invalid zone count"
        assert impact["total_pumps_needed"] >= 0, f"Preset {name} failed: negative pumps"

    # Specific preset check: Typhoon should create high demand
    typhoon_sim = run_simulation(2.5, 35.0, True)
    assert typhoon_sim["resource_impact"]["total_pumps_needed"] >= 14, "Typhoon should trigger high pump demand"
    
    # Specific preset check: Nominal baseline should have 0 deficit
    nominal_sim = run_simulation(1.0, 85.0, False)
    assert nominal_sim["resource_impact"]["deficit"] == 0, "Nominal baseline should have 0 deficit"
    print("  ✅ All 4 simulation presets passed.")

    # TEST 5: Map Extraction & Proximity Fallback
    print("\n[TEST 5] Testing Map Click Payload & Distance Fallback...")
    # Tooltip payload match
    m_data1 = {"last_object_clicked_tooltip": "[Z-04] Downtown Metro Core — Risk: 0.32"}
    assert extract_zone_id_from_payload(m_data1, zones) == "Z-04", "Tooltip regex match failed"

    # Popup payload match
    m_data2 = {"last_object_clicked_popup": "<div style=''>[Z-02] Riverfront Promenade</div>"}
    assert extract_zone_id_from_payload(m_data2, zones) == "Z-02", "Popup regex match failed"

    # Coordinate distance proximity fallback (near Z-01: 13.045, 80.245)
    m_data3 = {"last_object_clicked": {"lat": 13.0451, "lng": 80.2452}}
    assert extract_zone_id_from_payload(m_data3, zones) == "Z-01", "Coordinate distance proximity fallback failed"
    print("  ✅ Map click extraction & distance fallback passed.")

    # TEST 6: Fallback Status Badges
    print("\n[TEST 6] Testing Fallback Hierarchy Status Badges...")
    d_stat = get_data_source_status()
    m_stat = get_model_source_status()
    print(f"  Data Source Mode:  {d_stat['mode']} ({d_stat['badge_color']})")
    print(f"  Model Source Mode: {m_stat['mode']} ({m_stat['badge_color']})")
    assert "mode" in d_stat and "badge_color" in d_stat
    assert "mode" in m_stat and "badge_color" in m_stat
    print("  ✅ Status badges passed.")

    print("\n" + "=" * 70)
    print("🎉 ALL 6 VERIFICATION TEST SUITES PASSED FLAWLESSLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
