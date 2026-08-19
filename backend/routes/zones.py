from flask import Blueprint, request
from models import Asset, RiskAssessment, PriorityRanking, Recommendation
from routes import make_response, make_error

zones_bp = Blueprint("zones", __name__)

PRIORITY_WEIGHT = {
    "P1_URGENT": 4,
    "P2_HIGH": 3,
    "P3_MEDIUM": 2,
    "P4_LOW": 1
}


def compute_zones_summary_data():
    """
    Helper function that computes aggregated metrics for all municipal zones.
    """
    assets = Asset.query.all()
    if not assets:
        return []

    zones_data = {}
    for asset in assets:
        zone_name = asset.zone or "Unassigned Zone"
        if zone_name not in zones_data:
            zones_data[zone_name] = {
                "zone": zone_name,
                "asset_count": 0,
                "critical_asset_count": 0,
                "risk_scores": [],
                "total_population_impact": 0,
                "total_economic_exposure": 0.0,
                "highest_priority_tier": "P4_LOW",
                "highest_priority_weight": 0
            }

        z = zones_data[zone_name]
        z["asset_count"] += 1
        if asset.status == "critical":
            z["critical_asset_count"] += 1

        # Latest Risk Assessment
        latest_risk = RiskAssessment.query.filter_by(asset_id=asset.id).order_by(RiskAssessment.assessed_at.desc()).first()
        if latest_risk:
            z["risk_scores"].append(latest_risk.risk_score)

        # Priority Ranking
        priority = PriorityRanking.query.filter_by(asset_id=asset.id).first()
        if priority:
            z["total_population_impact"] += priority.estimated_population_impact
            z["total_economic_exposure"] += priority.estimated_economic_exposure
            
            tier = priority.priority_tier
            weight = PRIORITY_WEIGHT.get(tier, 0)
            if weight > z["highest_priority_weight"]:
                z["highest_priority_weight"] = weight
                z["highest_priority_tier"] = tier

    zones_list = []
    for zone_name, z in zones_data.items():
        avg_risk = sum(z["risk_scores"]) / len(z["risk_scores"]) if z["risk_scores"] else 0.0
        zones_list.append({
            "zone": z["zone"],
            "asset_count": z["asset_count"],
            "critical_asset_count": z["critical_asset_count"],
            "avg_risk_score": round(avg_risk, 3),
            "total_population_impact": z["total_population_impact"],
            "total_economic_exposure": round(z["total_economic_exposure"], 2),
            "highest_priority_tier": z["highest_priority_tier"],
            "priority_weight": z["highest_priority_weight"]
        })

    # Sort zones by critical count descending, then avg risk score descending
    zones_list.sort(key=lambda x: (x["priority_weight"], x["critical_asset_count"], x["avg_risk_score"]), reverse=True)
    return zones_list


@zones_bp.route("/zones/summary", methods=["GET"])
def get_zones_summary():
    """
    Aggregates infrastructure asset, risk, and priority metrics by municipal zone.
    """
    try:
        zones_list = compute_zones_summary_data()
        # Clean internal priority_weight before returning
        clean_zones = [
            {k: v for k, v in z.items() if k != "priority_weight"}
            for z in zones_list
        ]
        return make_response({"zones": clean_zones}, source="mock")
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to compile zone summaries", details=[str(exc)], status_code=500)


@zones_bp.route("/zones/allocate-resources", methods=["POST"])
def allocate_resources_to_zones():
    """
    Statelessly allocates limited countable resources (pumps, crews, budget)
    across municipal zones ordered by urgency and critical asset density.
    """
    try:
        payload = request.get_json(silent=True)
        if not payload:
            return make_error("INVALID_JSON", "Request body must be a valid JSON object", status_code=400)

        try:
            pumps_avail = float(payload.get("pumps_available", 0.0))
            crews_avail = float(payload.get("crews_available", 0.0))
            budget_avail = float(payload.get("budget_available", 0.0))
        except (ValueError, TypeError) as exc:
            return make_error("VALIDATION_ERROR", "Resource quantities must be numeric values", details=[str(exc)], status_code=400)

        if pumps_avail < 0 or crews_avail < 0 or budget_avail < 0:
            return make_error("VALIDATION_ERROR", "Resource quantities must be non-negative", status_code=400)

        zones_list = compute_zones_summary_data()
        if not zones_list:
            return make_response({
                "allocations": [],
                "total_pumps_allocated": 0,
                "total_crews_allocated": 0,
                "total_budget_allocated": 0.0,
                "unallocated_pumps": pumps_avail,
                "unallocated_crews": crews_avail,
                "unallocated_budget": budget_avail
            }, source="mock")

        remaining_pumps = pumps_avail
        remaining_crews = crews_avail
        remaining_budget = budget_avail

        total_critical = sum(z["critical_asset_count"] for z in zones_list) or 1

        allocations = []
        for z in zones_list:
            # Proportional pump and crew allocation based on critical asset concentration and risk
            zone_crit = z["critical_asset_count"]
            zone_risk = z["avg_risk_score"]

            if zone_crit > 0 or zone_risk >= 0.5:
                # Proportional share
                pumps_share = int(round((zone_crit / total_critical) * pumps_avail)) if total_critical > 0 else 1
                crews_share = int(round((zone_crit / total_critical) * crews_avail)) if total_critical > 0 else 1

                pumps_to_assign = min(remaining_pumps, max(1, pumps_share)) if remaining_pumps > 0 else 0
                crews_to_assign = min(remaining_crews, max(1, crews_share)) if remaining_crews > 0 else 0
            else:
                pumps_to_assign = 0
                crews_to_assign = 0

            remaining_pumps -= pumps_to_assign
            remaining_crews -= crews_to_assign

            # Budget allocation to pending recommendations in this zone
            zone_recs = Recommendation.query.filter(
                Recommendation.status == "pending"
            ).join(Asset).filter(Asset.zone == z["zone"]).all()

            # Value-ratio knapsack for zone recommendations
            scored_recs = []
            for r in zone_recs:
                cost = max(1.0, r.estimated_cost)
                ratio = r.expected_risk_reduction_pct / cost
                scored_recs.append((r, ratio))
            scored_recs.sort(key=lambda x: x[1], reverse=True)

            zone_budget_spent = 0.0
            funded_recs = []
            for rec, _ in scored_recs:
                if rec.estimated_cost <= remaining_budget:
                    funded_recs.append(rec.to_dict())
                    remaining_budget -= rec.estimated_cost
                    zone_budget_spent += rec.estimated_cost

            allocations.append({
                "zone": z["zone"],
                "priority_tier": z["highest_priority_tier"],
                "critical_asset_count": z["critical_asset_count"],
                "avg_risk_score": z["avg_risk_score"],
                "pumps_allocated": int(pumps_to_assign),
                "crews_allocated": int(crews_to_assign),
                "budget_allocated": round(zone_budget_spent, 2),
                "recommendations_funded": funded_recs
            })

        total_pumps_alloc = int(pumps_avail - remaining_pumps)
        total_crews_alloc = int(crews_avail - remaining_crews)
        total_budget_alloc = round(budget_avail - remaining_budget, 2)

        data = {
            "allocations": allocations,
            "total_pumps_allocated": total_pumps_alloc,
            "total_crews_allocated": total_crews_alloc,
            "total_budget_allocated": total_budget_alloc,
            "unallocated_pumps": int(remaining_pumps),
            "unallocated_crews": int(remaining_crews),
            "unallocated_budget": round(remaining_budget, 2)
        }
        return make_response(data, source="mock")
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to allocate resources to zones", details=[str(exc)], status_code=500)


@zones_bp.route("/zones/predict-flood-risk", methods=["POST"])
def predict_zone_flood_risk():
    """
    SENSE Stage: Computes a deterministic flood risk score and contributing factors for a zone.
    """
    try:
        payload = request.get_json(silent=True)
        if not payload:
            return make_error("INVALID_JSON", "Request body must be a valid JSON object", status_code=400)

        zone = str(payload.get("zone", "Unspecified Zone")).strip()
        
        try:
            rainfall_mm = float(payload.get("rainfall_mm", 50.0))
            drainage_cap = float(payload.get("drainage_capacity_pct", 50.0))
            population = float(payload.get("population", 50000))
            traffic_index = float(payload.get("traffic_index", 0.5))
        except (ValueError, TypeError) as exc:
            return make_error("VALIDATION_ERROR", "Numeric values required for rainfall, drainage, population, and traffic", details=[str(exc)], status_code=400)

        if rainfall_mm < 0 or population < 0 or traffic_index < 0:
            return make_error("VALIDATION_ERROR", "Rainfall, population, and traffic index must be non-negative", status_code=400)

        if not (0.0 <= drainage_cap <= 100.0):
            return make_error("VALIDATION_ERROR", "drainage_capacity_pct must be between 0.0 and 100.0", status_code=400)

        # Factor calculations
        rainfall_factor = round(min(1.0, max(0.0, rainfall_mm / 120.0)), 2)
        drainage_deficit_factor = round(min(1.0, max(0.0, (100.0 - drainage_cap) / 100.0)), 2)
        population_factor = round(min(1.0, max(0.0, population / 200000.0)), 2)
        traffic_factor = round(min(1.0, max(0.0, traffic_index)), 2)

        raw_score = (rainfall_factor * 0.45) + (drainage_deficit_factor * 0.30) + (population_factor * 0.15) + (traffic_factor * 0.10)
        flood_risk_score = round(min(0.98, max(0.05, raw_score)), 2)

        if flood_risk_score >= 0.82:
            risk_level = "catastrophic"
        elif flood_risk_score >= 0.62:
            risk_level = "high"
        elif flood_risk_score >= 0.38:
            risk_level = "medium"
        else:
            risk_level = "low"

        result = {
            "zone": zone,
            "flood_risk_score": flood_risk_score,
            "risk_level": risk_level,
            "contributing_factors": {
                "rainfall_factor": rainfall_factor,
                "drainage_deficit_factor": drainage_deficit_factor,
                "population_exposure_factor": population_factor,
                "traffic_factor": traffic_factor
            },
            "source": "mock"
        }
        return make_response(result, source="mock")
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to predict flood risk", details=[str(exc)], status_code=500)
