"""
UrbanShield - Mock Data Repository
Provides realistic mock data for all 6 city zones, municipal resources,
Random Forest risk predictions, OR-Tools resource allocations, and what-if simulation calculations.
"""

from config import ZONES_CONFIG, get_severity

# 1. Base Zone Data & Sensors (Member 2 Mock Scope)
MOCK_ZONES_SUMMARY = [
    {
        "zone_id": "Z-01",
        "name": "South Lowland Basin",
        "asset_type": "Healthcare & Power Grid",
        "lat": 13.0450,
        "lng": 80.2450,
        "population": 125000,
        "critical_assets": ["Metro General Hospital", "Substation Beta"],
        "drainage_capacity_pct": 32.0,
        "rainfall_mm_per_hr": 68.5,
        "soil_saturation_pct": 92.0,
        "sensor_health": "Active",
        "last_updated": "2 mins ago"
    },
    {
        "zone_id": "Z-02",
        "name": "Riverfront Promenade",
        "asset_type": "Water Utility & Viaduct",
        "lat": 13.0650,
        "lng": 80.2780,
        "population": 85000,
        "critical_assets": ["Central Water Pump Station", "Pedestrian Viaduct"],
        "drainage_capacity_pct": 41.0,
        "rainfall_mm_per_hr": 54.0,
        "soil_saturation_pct": 84.0,
        "sensor_health": "Active",
        "last_updated": "3 mins ago"
    },
    {
        "zone_id": "Z-03",
        "name": "East Industrial Hub",
        "asset_type": "Industrial & Rail Corridor",
        "lat": 13.0300,
        "lng": 80.2600,
        "population": 62000,
        "critical_assets": ["Chemical Treatment Plant", "Freight Rail Junction"],
        "drainage_capacity_pct": 52.0,
        "rainfall_mm_per_hr": 42.0,
        "soil_saturation_pct": 71.0,
        "sensor_health": "Active",
        "last_updated": "1 min ago"
    },
    {
        "zone_id": "Z-04",
        "name": "Downtown Metro Core",
        "asset_type": "Civic Center & Transit Hub",
        "lat": 13.0827,
        "lng": 80.2707,
        "population": 210000,
        "critical_assets": ["City Hall", "Central Transit Terminal", "Emergency Ops Center"],
        "drainage_capacity_pct": 68.0,
        "rainfall_mm_per_hr": 35.0,
        "soil_saturation_pct": 58.0,
        "sensor_health": "Active",
        "last_updated": "Just now"
    },
    {
        "zone_id": "Z-05",
        "name": "Port Logistics Corridor",
        "asset_type": "Coastal Port & Flood Wall",
        "lat": 13.1100,
        "lng": 80.2950,
        "population": 48000,
        "critical_assets": ["Container Terminal", "Coastal Flood Wall Gate 3"],
        "drainage_capacity_pct": 48.0,
        "rainfall_mm_per_hr": 62.0,
        "soil_saturation_pct": 88.0,
        "sensor_health": "Active",
        "last_updated": "4 mins ago"
    },
    {
        "zone_id": "Z-06",
        "name": "North Hillside Ridge",
        "asset_type": "Reservoir & Telecom Ridge",
        "lat": 13.1250,
        "lng": 80.2300,
        "population": 92000,
        "critical_assets": ["Hillside Reservoir", "Telecom Master Tower"],
        "drainage_capacity_pct": 84.0,
        "rainfall_mm_per_hr": 22.0,
        "soil_saturation_pct": 39.0,
        "sensor_health": "Active",
        "last_updated": "5 mins ago"
    }
]

# Municipal Resource Pool (Member 2 Mock Scope)
MOCK_RESOURCES = {
    "total_heavy_pumps": 14,
    "deployed_heavy_pumps": 9,
    "available_heavy_pumps": 5,
    "total_rapid_crews": 10,
    "deployed_rapid_crews": 6,
    "available_rapid_crews": 4,
    "allocated_budget_usd": 185000,
    "total_emergency_budget_usd": 300000
}

# 2. Random Forest Model Predictions & Prioritization (Member 3 Mock Scope)
MOCK_PIPELINE_PREDICTIONS = [
    {
        "zone_id": "Z-01",
        "risk_score": 0.88,
        "priority_rank": 1,
        "severity": "Critical",
        "key_drivers": [
            "Heavy rainfall (68.5 mm/hr) exceeding storm threshold",
            "Critical drainage bottlenecks (32% operational capacity)",
            "Low elevation (4.2m) with adjacent General Hospital asset"
        ]
    },
    {
        "zone_id": "Z-05",
        "risk_score": 0.78,
        "priority_rank": 2,
        "severity": "Critical",
        "key_drivers": [
            "High coastal tide level and storm runoff (62 mm/hr)",
            "Soil saturation at 88% causing surface pooling",
            "Vulnerable flood wall gate adjacent to container terminal"
        ]
    },
    {
        "zone_id": "Z-02",
        "risk_score": 0.64,
        "priority_rank": 3,
        "severity": "High",
        "key_drivers": [
            "Riverbank overflow risk at promenade retention basin",
            "Moderate drainage choking (41% capacity remaining)",
            "High foot-traffic zone with pedestrian viaduct"
        ]
    },
    {
        "zone_id": "Z-03",
        "risk_score": 0.46,
        "priority_rank": 4,
        "severity": "Moderate",
        "key_drivers": [
            "Industrial runoff accumulation near freight lines",
            "Adequate baseline pump rate keeping levels stable"
        ]
    },
    {
        "zone_id": "Z-04",
        "risk_score": 0.32,
        "priority_rank": 5,
        "severity": "Moderate",
        "key_drivers": [
            "High density population but robust subsurface drainage",
            "Rainfall rate within normal operational tolerance"
        ]
    },
    {
        "zone_id": "Z-06",
        "risk_score": 0.12,
        "priority_rank": 6,
        "severity": "Low",
        "key_drivers": [
            "High natural elevation (28.4m) enabling gravity runoff",
            "Reservoir holding capacity at safe 42%"
        ]
    }
]

# 3. OR-Tools Optimization & Explainable Action Recommendations (Member 3 Mock Scope)
MOCK_RECOMMENDATIONS_AND_ALLOCATIONS = {
    "Z-01": {
        "allocated_pumps": 4,
        "allocated_crews": 2,
        "action_summary": "Deploy 4 High-Volume Submersible Pumps to Substation Beta perimeter. Dispatch Rapid Crew #1 to clear Hospital access road drainage culverts.",
        "urgency": "Immediate Dispatch (< 15 mins)",
        "asset_protection_rationale": "Protects Metro General Hospital trauma center and prevents flood-induced blackout across Substation Beta serving 125,000 residents.",
        "optimization_rationale": "OR-Tools linear solver prioritized 4 pumps here due to high consequence-of-failure weighting on regional healthcare and electrical grid stability."
    },
    "Z-05": {
        "allocated_pumps": 3,
        "allocated_crews": 2,
        "action_summary": "Pre-position 3 Diesel Pumps along Flood Wall Gate 3. Deploy Crew #3 to close secondary storm barrier and monitor tidal surge.",
        "urgency": "Immediate Dispatch (< 20 mins)",
        "asset_protection_rationale": "Prevents catastrophic salt-water inundation of Container Terminal logistics corridor and protects coastal flood barrier integrity.",
        "optimization_rationale": "OR-Tools solver assigned 3 heavy diesel pumps to prevent secondary supply-chain disruption and maritime freight corridor shutdown."
    },
    "Z-02": {
        "allocated_pumps": 2,
        "allocated_crews": 1,
        "action_summary": "Deploy 2 Mobile Trailer Pumps to Riverfront Promenade intake. Crew #2 on standby for debris clearing at weir grates.",
        "urgency": "High Priority (< 45 mins)",
        "asset_protection_rationale": "Safeguards Central Water Pump Station from overflow and prevents pedestrian viaduct foundation scour.",
        "optimization_rationale": "OR-Tools allocated 2 mobile pumps to balance weir overflow against downstream municipal drinking water pump intake safety."
    },
    "Z-03": {
        "allocated_pumps": 0,
        "allocated_crews": 1,
        "action_summary": "Place Rapid Response Crew #4 on mobile patrol around Chemical Plant perimeter. Monitor sensor cluster E-3.",
        "urgency": "Standard Monitoring",
        "asset_protection_rationale": "Maintains containment monitoring at Chemical Treatment Plant and Freight Rail Junction.",
        "optimization_rationale": "Baseline static pumps sufficient; zero heavy mobile pumps needed. 1 reconnaissance crew assigned for perimeter check."
    },
    "Z-04": {
        "allocated_pumps": 0,
        "allocated_crews": 0,
        "action_summary": "Maintain automated telemetry monitoring. Central Transit pumps operational on baseline municipal grid.",
        "urgency": "Normal Operations",
        "asset_protection_rationale": "City Hall and Central Transit Terminal protected by high-capacity subterranean box culverts.",
        "optimization_rationale": "Drainage capacity (68%) well above threshold. Zero resource allocation required; units preserved for high-risk flood zones."
    },
    "Z-06": {
        "allocated_pumps": 0,
        "allocated_crews": 0,
        "action_summary": "No intervention required. Gravity drainage functioning normally.",
        "urgency": "Normal Operations",
        "asset_protection_rationale": "Hillside Reservoir and Telecom Tower elevated at 28.4m elevation.",
        "optimization_rationale": "Zero flood vulnerability. Natural elevation provides 100% gravity discharge."
    }
}

def calculate_simulated_scenario(
    rainfall_multiplier: float,
    drainage_capacity_pct: float,
    storm_surge: bool,
    total_pumps_pool: int = 14
) -> dict:
    """
    Simulates Multi-Layer Agent recalculation (PREDICT -> PRIORITIZE -> OPTIMIZE).
    Returns a before/after comparison structure.
    """
    baseline_predictions = MOCK_PIPELINE_PREDICTIONS
    baseline_allocations = MOCK_RECOMMENDATIONS_AND_ALLOCATIONS

    simulated_results = []
    total_needed_pumps = 0

    for item in baseline_predictions:
        z_id = item["zone_id"]
        z_cfg = ZONES_CONFIG.get(z_id, {
            "name": f"Zone {z_id}",
            "critical_assets": ["Municipal Facility"]
        })
        
        # Calculate new risk score based on inputs
        surge_impact = 0.22 if (storm_surge and z_id in ["Z-01", "Z-05", "Z-02"]) else 0.0
        drainage_penalty = max(0.0, (70.0 - drainage_capacity_pct) * 0.005)
        rain_increase = (rainfall_multiplier - 1.0) * 0.25
        
        new_risk = min(0.99, max(0.05, item["risk_score"] + rain_increase + drainage_penalty + surge_impact))
        new_severity = get_severity(new_risk)
        
        # New OR-Tools mock reallocation
        if new_risk >= 0.80:
            alloc_p = 4
            alloc_c = 2
            act = f"URGENT: Surge protocol active. Deploy {alloc_p} heavy pumps to protect {z_cfg['critical_assets'][0]}."
        elif new_risk >= 0.60:
            alloc_p = 3
            alloc_c = 1
            act = f"PRIORITY: Deploy {alloc_p} pumps to mitigate localized drainage saturation."
        elif new_risk >= 0.35:
            alloc_p = 1
            alloc_c = 1
            act = f"MONITOR: Position {alloc_p} backup pump on standby."
        else:
            alloc_p = 0
            alloc_c = 0
            act = "SAFE: Gravity drainage sufficient."
            
        total_needed_pumps += alloc_p
        orig_pumps = baseline_allocations.get(z_id, {}).get("allocated_pumps", 0)
        
        simulated_results.append({
            "zone_id": z_id,
            "name": z_cfg["name"],
            "baseline_risk": item["risk_score"],
            "simulated_risk": round(new_risk, 2),
            "risk_delta": round(new_risk - item["risk_score"], 2),
            "baseline_severity": item["severity"],
            "simulated_severity": new_severity,
            "baseline_pumps": orig_pumps,
            "simulated_pumps": alloc_p,
            "pump_delta": alloc_p - orig_pumps,
            "simulated_action": act
        })

    # Sort simulated results by simulated_risk descending to determine new priority ranks
    simulated_results.sort(key=lambda x: x["simulated_risk"], reverse=True)
    for idx, row in enumerate(simulated_results, start=1):
        row["simulated_priority_rank"] = idx

    return {
        "scenario_params": {
            "rainfall_multiplier": rainfall_multiplier,
            "drainage_capacity_pct": drainage_capacity_pct,
            "storm_surge": storm_surge
        },
        "zones": simulated_results,
        "resource_impact": {
            "total_pumps_needed": total_needed_pumps,
            "available_pumps_pool": total_pumps_pool,
            "deficit": max(0, total_needed_pumps - total_pumps_pool)
        }
    }
