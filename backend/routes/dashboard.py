from flask import Blueprint
from models import Asset, RiskAssessment, PriorityRanking, Recommendation
from routes import make_response, make_error

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard/summary", methods=["GET"])
def get_dashboard_summary():
    """
    Returns aggregated city-wide infrastructure KPIs and top urgent interventions.
    """
    try:
        total_assets = Asset.query.count()
        critical_count = Asset.query.filter(Asset.status == "critical").count()
        degraded_count = Asset.query.filter(Asset.status == "degraded").count()
        healthy_count = Asset.query.filter(Asset.status == "healthy").count()

        # Risk calculations
        risks = RiskAssessment.query.all()
        if risks:
            avg_risk = sum(r.risk_score for r in risks) / len(risks)
            city_risk_score = round(avg_risk * 100.0, 1)
            source = risks[0].source
        else:
            city_risk_score = 0.0
            source = "mock"

        # Recommendations summary
        pending_recs = Recommendation.query.filter(Recommendation.status == "pending").all()
        total_budget = sum(r.estimated_cost for r in pending_recs)

        # Top urgent interventions (top 5 priority rankings)
        top_priorities = PriorityRanking.query.order_by(PriorityRanking.rank.asc()).limit(5).all()
        urgent_list = []
        for p in top_priorities:
            latest_risk = RiskAssessment.query.filter_by(asset_id=p.asset_id).order_by(RiskAssessment.assessed_at.desc()).first()
            top_rec = Recommendation.query.filter_by(asset_id=p.asset_id, status="pending").first()

            urgent_list.append({
                "rank": p.rank,
                "asset_id": p.asset_id,
                "asset_name": p.asset.name if p.asset else p.asset_id,
                "category": p.asset.category if p.asset else "unknown",
                "zone": p.asset.zone if p.asset else "unknown",
                "risk_score": latest_risk.risk_score if latest_risk else 0.0,
                "priority_tier": p.priority_tier,
                "composite_urgency_score": p.composite_urgency_score,
                "primary_hazard": latest_risk.primary_hazard if latest_risk else "Environmental Hazard",
                "top_recommendation": top_rec.title if top_rec else "Maintain standard inspection schedule",
                "estimated_cost": top_rec.estimated_cost if top_rec else 0.0
            })

        summary_data = {
            "summary": {
                "total_assets": total_assets,
                "critical_count": critical_count,
                "degraded_count": degraded_count,
                "healthy_count": healthy_count,
                "city_wide_risk_score": city_risk_score,
                "total_budget_required_usd": round(total_budget, 2),
                "pending_recommendations_count": len(pending_recs)
            },
            "urgent_interventions": urgent_list
        }
        return make_response(summary_data, source=source)
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to compile dashboard summary", details=[str(exc)], status_code=500)
