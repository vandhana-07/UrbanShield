from flask import Blueprint, request
from models import Asset, RiskAssessment, PriorityRanking, Recommendation
from routes import make_response, make_error
from services.ml_model import ml_service
from services.optimizer_service import optimizer_service

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

    # Sort zones by priority weight descending, then critical count descending
    zones_list.sort(key=lambda x: (x["priority_weight"], x["critical_asset_count"], x["avg_risk_score"]), reverse=True)
    return zones_list


@zones_bp.route("/zones/summary", methods=["GET"])
def get_zones_summary():
    """
    Aggregates infrastructure asset, risk, and priority metrics by municipal zone.
    """
    try:
        zones_list = compute_zones_summary_data()
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
    across municipal zones using Google OR-Tools integer programming.
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
        data = optimizer_service.solve_multi_resource_allocation(zones_list, pumps_avail, crews_avail, budget_avail)
        
        return make_response(data, source="mock")
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to allocate resources to zones", details=[str(exc)], status_code=500)


@zones_bp.route("/zones/predict-flood-risk", methods=["POST"])
def predict_zone_flood_risk():
    """
    SENSE Stage: Computes a machine-learning-driven flood risk score using Scikit-Learn RandomForest.
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

        # Call Scikit-Learn Random Forest ML Model
        result = ml_service.predict_flood_risk(
            zone_name=zone,
            rainfall_mm=rainfall_mm,
            drainage_capacity_pct=drainage_cap,
            population=population,
            traffic_index=traffic_index
        )
        
        source = result.get("source", "ml_model")
        return make_response(result, source=source)
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to predict flood risk", details=[str(exc)], status_code=500)


@zones_bp.route("/zones/real", methods=["GET"])
@zones_bp.route("/agent/pipeline", methods=["GET"])
def get_real_chennai_pipeline():
    """
    Executes or fetches the live 6-layer UrbanShield pipeline results
    for real Chennai municipal zones (OpenCity/GCC/IMD data).
    """
    try:
        import requests
        from config import Config
        from agent.orchestrator import UrbanShieldAgent

        agent_url = Config.AGENT_URL
        try:
            resp = requests.post(f"{agent_url}/agent/analyze", json={}, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                return make_response(data, source="agent")
        except Exception:
            pass

        # Fallback to direct in-process Agent execution
        agent_instance = UrbanShieldAgent()
        final_df, opt_summary = agent_instance.run_full_pipeline()
        return make_response({
            "pipeline_summary": opt_summary,
            "zones": final_df.to_dict(orient="records"),
            "data_provenance": "Real Chennai Observations (OpenCity / GCC / IMD)"
        }, source="agent_direct")

    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to retrieve real zone pipeline data", details=[str(exc)], status_code=500)
