from flask import Blueprint
from models import Asset, RiskAssessment, PriorityRanking
from routes import make_response, make_error

zones_bp = Blueprint("zones", __name__)

PRIORITY_WEIGHT = {
    "P1_URGENT": 4,
    "P2_HIGH": 3,
    "P3_MEDIUM": 2,
    "P4_LOW": 1
}

@zones_bp.route("/zones/summary", methods=["GET"])
def get_zones_summary():
    """
    Aggregates infrastructure asset, risk, and priority metrics by municipal zone.
    """
    try:
        assets = Asset.query.all()
        if not assets:
            return make_response({"zones": []}, source="mock")

        # Group assets by zone
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

        # Format output list
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
                "highest_priority_tier": z["highest_priority_tier"]
            })

        # Sort zones by critical count descending, then avg risk score descending
        zones_list.sort(key=lambda x: (x["critical_asset_count"], x["avg_risk_score"]), reverse=True)

        return make_response({"zones": zones_list}, source="mock")
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to compile zone summaries", details=[str(exc)], status_code=500)
