"""
UrbanShield Mock Engine
Provides deterministic, domain-realistic calculations for risk assessments,
priority rankings, actionable recommendations, and what-if simulation cascades.
Used in MOCK_MODE or as automatic fallback when Member 3's AI Agent is unreachable.
"""

import uuid
import datetime

HAZARD_MAP = {
    "bridge": "Structural Fatigue & Heavy Load Shear",
    "road": "Subgrade Settlement & Asphalt Deformation",
    "drainage": "Flash Flood Inundation & Culvert Silt Blockage",
    "water": "Hydrodynamic Surge & Mainline Corrosion Fracture",
    "power": "Transformer Thermal Overload & Grid Surge",
    "public_building": "Foundation Subsidence & Seismic Lateral Drift"
}

ACTION_TEMPLATES = {
    "bridge": [
        ("structural_retrofit", "Emergency Pier Post-Tensioning & Deck Jacketing", "Apply high-tensile carbon-fiber wrap and external post-tensioning tendons to vulnerable support bents.", 750000.0, 62.0),
        ("emergency_closure", "Partial Heavy Vehicle Lane Closure", "Restrict freight over 15 tons to outer diversion routes to preserve structural stability during peak weather.", 45000.0, 38.0)
    ],
    "road": [
        ("pavement_reconstruction", "Deep Soil Injection & Geogrid Overlay", "Inject polyurethane resin beneath subgrade to arrest void propagation and lay reinforced geogrid.", 320000.0, 54.0),
        ("traffic_diversion", "Automated Smart Lane Rerouting", "Deploy dynamic LED lane signals to distribute vehicular axle stress away from degraded segments.", 80000.0, 31.0)
    ],
    "drainage": [
        ("activate_auxiliary_floodgates", "Auxiliary Spillway & Automated Sluice Deployment", "Actuate motorized floodgates to divert stormwater surge into retention reservoirs.", 280000.0, 71.0),
        ("culvert_dredging", "Rapid High-Volume Silt Desilting", "Deploy hydro-vac excavators to clear 85% sediment blockage across choke points.", 120000.0, 48.0)
    ],
    "water": [
        ("pressure_relief", "Pressure Reducing Valve Calibration & Bypass", "Install automated PRVs to dampen hydraulic water hammer pressure spikes.", 190000.0, 66.0),
        ("pipe_relining", "CIPP (Cured-In-Place Pipe) Structural Relining", "Trenchless epoxy liner installation to seal micro-fissures without street excavation.", 450000.0, 78.0)
    ],
    "power": [
        ("power_rerouting", "SCADA Automated Feeder Balancing & Bus Tie", "Shift 40MW load across auxiliary 115kV transmission lines to isolate hot transformer banks.", 150000.0, 69.0),
        ("substation_hardening", "Mobile Substation Bypass & Flood Barrier Deployment", "Erect rapid-deploy modular flood walls and pre-stage mobile transformer units.", 580000.0, 81.0)
    ],
    "public_building": [
        ("seismic_retrofitting", "Base Isolator Damping & Shear Wall Bracing", "Install elastomeric base isolators and cross-braced steel damper frames.", 920000.0, 74.0),
        ("sensor_audit", "Continuous Dynamic Interferometric Radar Monitoring", "Mount millimeter-wave displacement sensors on structural pillars for real-time deflection telemetry.", 85000.0, 35.0)
    ]
}


def calculate_risk_assessment(asset, source="mock"):
    """
    Computes deterministic risk assessment metrics from asset parameters.
    """
    current_year = 2026
    age = max(1, current_year - asset.year_built)
    age_factor = min(1.0, age / 75.0)
    health_factor = (100.0 - asset.health_index) / 100.0
    criticality_factor = asset.criticality_score / 10.0

    # Sensor telemetry adjustment
    sensor_boost = 0.0
    if isinstance(asset.sensor_data, dict):
        if asset.sensor_data.get("vibration_hz", 0) > 10.0:
            sensor_boost += 0.08
        if asset.sensor_data.get("load_pct", 0) > 85.0:
            sensor_boost += 0.06
        if asset.sensor_data.get("pressure_psi", 0) > 130.0:
            sensor_boost += 0.07

    # Weighted risk score
    raw_risk = (health_factor * 0.45) + (age_factor * 0.25) + (criticality_factor * 0.25) + sensor_boost
    risk_score = round(min(0.98, max(0.06, raw_risk)), 3)
    failure_prob = round(min(0.95, max(0.03, risk_score * 0.94)), 3)

    if risk_score >= 0.82 or (criticality_factor >= 0.9 and risk_score >= 0.65):
        consequence_level = "catastrophic"
    elif risk_score >= 0.60:
        consequence_level = "high"
    elif risk_score >= 0.35:
        consequence_level = "medium"
    else:
        consequence_level = "low"

    primary_hazard = HAZARD_MAP.get(asset.category, "Environmental Degradation & Material Fatigue")
    predicted_days = int(max(7, (1.0 - risk_score) * 365))
    confidence_score = round(0.85 + (criticality_factor * 0.08), 2)

    return {
        "asset_id": asset.id,
        "risk_score": risk_score,
        "failure_probability": failure_prob,
        "consequence_level": consequence_level,
        "primary_hazard": primary_hazard,
        "predicted_days_to_failure": predicted_days,
        "confidence_score": confidence_score,
        "source": source,
    }


def calculate_priority_ranking(asset, risk_assessment, source="mock"):
    """
    Computes priority ranking and urgency metrics.
    """
    risk_score = risk_assessment["risk_score"]
    health_index = asset.health_index
    crit_score = asset.criticality_score

    composite_score = (risk_score * 52.0) + (crit_score * 3.8) + ((100.0 - health_index) * 0.10)
    composite_urgency = round(min(99.5, max(12.0, composite_score)), 1)

    if composite_urgency >= 80.0:
        priority_tier = "P1_URGENT"
    elif composite_urgency >= 62.0:
        priority_tier = "P2_HIGH"
    elif composite_urgency >= 42.0:
        priority_tier = "P3_MEDIUM"
    else:
        priority_tier = "P4_LOW"

    pop_multipliers = {
        "bridge": 11000,
        "water": 14500,
        "power": 18000,
        "drainage": 8500,
        "road": 9500,
        "public_building": 6000
    }
    multiplier = pop_multipliers.get(asset.category, 8000)
    pop_impact = int(crit_score * multiplier * (0.6 + risk_score * 0.5))
    economic_exposure = round(crit_score * risk_score * 1750000.0, 2)

    return {
        "asset_id": asset.id,
        "priority_tier": priority_tier,
        "composite_urgency_score": composite_urgency,
        "estimated_population_impact": pop_impact,
        "estimated_economic_exposure": economic_exposure,
        "source": source,
    }


def generate_recommendations_for_asset(asset, risk_assessment, source="mock"):
    """
    Generates realistic actionable recommendations for an asset.
    """
    templates = ACTION_TEMPLATES.get(asset.category, ACTION_TEMPLATES["bridge"])
    recs = []

    # Pick template based on severity
    if risk_assessment["risk_score"] >= 0.55:
        action_type, title, desc, base_cost, base_reduction = templates[0]
    else:
        action_type, title, desc, base_cost, base_reduction = templates[1]

    # Adjust cost slightly by criticality
    cost = round(base_cost * (0.85 + (asset.criticality_score / 20.0)), 2)
    risk_reduct = round(min(92.0, base_reduction * (0.9 + (risk_assessment["risk_score"] * 0.2))), 1)

    tradeoff = {
        "estimated_downtime_hours": 12 if "closure" in action_type else 36,
        "cost_benefit_ratio": round((risk_assessment["risk_score"] * 1000000.0) / max(1.0, cost), 2),
        "safety_margin_improvement_pct": round(risk_reduct * 1.15, 1)
    }

    recs.append({
        "asset_id": asset.id,
        "action_type": action_type,
        "title": title,
        "description": desc,
        "estimated_cost": cost,
        "expected_risk_reduction_pct": risk_reduct,
        "status": "pending",
        "tradeoff_analysis": tradeoff,
        "source": source
    })
    return recs


def simulate_scenario(name, hazard_type, intensity, selected_interventions, budget_limit, assets, source="mock"):
    """
    Synchronously executes a what-if scenario against current infrastructure assets.
    Computes baseline vs. mitigated metrics, damage reduction, and cascade prevention.
    """
    sim_id = f"SIM-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    intensity = float(intensity)
    budget_limit = float(budget_limit) if budget_limit else 0.0

    # Build intervention map
    intervened_ids = set()
    for item in selected_interventions:
        if isinstance(item, dict) and "asset_id" in item:
            intervened_ids.add(item["asset_id"])

    # Baseline Calculations
    baseline_risks = []
    baseline_losses = 0.0
    critical_failing = 0
    pop_disrupted = 0

    simulated_risks = []
    simulated_losses = 0.0
    sim_critical_failing = 0
    sim_pop_disrupted = 0

    cascade_events = []

    for asset in assets:
        # Base vulnerability
        vuln = (100.0 - asset.health_index) / 100.0
        crit = asset.criticality_score

        # Hazard vulnerability alignment
        hazard_weight = 1.2 if (
            (hazard_type == "flood" and asset.category in ("drainage", "water", "bridge")) or
            (hazard_type == "earthquake" and asset.category in ("bridge", "public_building", "road")) or
            (hazard_type == "power_outage" and asset.category in ("power", "water")) or
            (hazard_type == "extreme_heat" and asset.category in ("power", "road"))
        ) else 0.85

        # Baseline risk under shock
        base_asset_risk = min(1.0, (vuln * 0.5 + intensity * 0.45) * hazard_weight)
        base_loss = base_asset_risk * crit * 320000.0 * (1.0 + intensity)
        baseline_risks.append(base_asset_risk)
        baseline_losses += base_loss

        if base_asset_risk >= 0.72:
            critical_failing += 1
            pop_disrupted += int(crit * 11500 * intensity)

        # Simulated state with interventions
        if asset.id in intervened_ids:
            # Intervention mitigates 65% - 85% of incremental risk
            mitigation_pct = 0.75
            sim_asset_risk = max(0.08, base_asset_risk * (1.0 - mitigation_pct))
            sim_loss = sim_asset_risk * crit * 320000.0 * (1.0 + intensity)
            
            cascade_events.append({
                "asset_id": asset.id,
                "asset_name": asset.name,
                "action_taken": "Intervention Applied",
                "impact": f"Stabilized {asset.name}; prevented cascading overload into neighboring grid nodes."
            })
        else:
            sim_asset_risk = base_asset_risk
            sim_loss = base_loss

        simulated_risks.append(sim_asset_risk)
        simulated_losses += sim_loss

        if sim_asset_risk >= 0.72:
            sim_critical_failing += 1
            sim_pop_disrupted += int(crit * 11500 * intensity)

    total_assets = max(1, len(assets))
    avg_base_risk = round((sum(baseline_risks) / total_assets) * 100.0, 1)
    avg_sim_risk = round((sum(simulated_risks) / total_assets) * 100.0, 1)

    damage_prevented = round(max(0.0, baseline_losses - simulated_losses), 2)
    risk_reduction_pct = round(max(0.0, ((avg_base_risk - avg_sim_risk) / max(0.1, avg_base_risk)) * 100.0), 1)
    roi = round(damage_prevented / max(1.0, budget_limit if budget_limit > 0 else 500000.0), 2)

    baseline_metrics = {
        "total_risk_score": avg_base_risk,
        "expected_direct_damage_usd": round(baseline_losses, 2),
        "critical_assets_failing": critical_failing,
        "population_disrupted": pop_disrupted
    }

    simulated_metrics = {
        "total_risk_score": avg_sim_risk,
        "expected_direct_damage_usd": round(simulated_losses, 2),
        "critical_assets_failing": sim_critical_failing,
        "population_disrupted": sim_pop_disrupted
    }

    net_benefit = {
        "risk_reduction_pct": risk_reduction_pct,
        "damage_prevented_usd": damage_prevented,
        "roi_ratio": roi
    }

    if not cascade_events:
        cascade_events.append({
            "asset_id": "SYSTEM",
            "asset_name": "Grid Overall",
            "action_taken": "No Interventions Selected",
            "impact": "Unmitigated hazard propagation across all vulnerable infrastructure nodes."
        })

    return {
        "simulation_id": sim_id,
        "name": name,
        "hazard_type": hazard_type,
        "intensity": intensity,
        "selected_interventions": selected_interventions,
        "budget_limit": budget_limit,
        "status": "completed",
        "baseline_metrics": baseline_metrics,
        "simulated_metrics": simulated_metrics,
        "net_benefit": net_benefit,
        "cascade_analysis": cascade_events,
        "source": source,
        "executed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
