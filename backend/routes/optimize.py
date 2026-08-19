from flask import Blueprint, request
from models import Recommendation, Asset
from routes import make_response, make_error

optimize_bp = Blueprint("optimize", __name__)

@optimize_bp.route("/optimize/allocate", methods=["POST"])
def optimize_budget_allocation():
    """
    Optimizes intervention recommendation selection under a financial budget constraint
    using a greedy cost-efficiency knapsack algorithm.
    """
    try:
        payload = request.get_json(silent=True)
        if not payload:
            return make_error("INVALID_JSON", "Request body must be a valid JSON object", status_code=400)

        if "budget_limit" not in payload:
            return make_error("VALIDATION_ERROR", "Missing required field: 'budget_limit'", status_code=400)

        try:
            budget_limit = float(payload["budget_limit"])
        except (ValueError, TypeError) as exc:
            return make_error("VALIDATION_ERROR", "Invalid numeric value for 'budget_limit'", details=[str(exc)], status_code=400)

        if budget_limit < 0:
            return make_error("VALIDATION_ERROR", "'budget_limit' must be greater than or equal to 0", status_code=400)

        zone_filter = payload.get("zone_filter")

        # Query pending recommendations
        query = Recommendation.query.filter(Recommendation.status == "pending")
        if zone_filter:
            query = query.join(Asset).filter(Asset.zone.ilike(f"%{str(zone_filter).strip()}%"))

        candidate_recs = query.all()
        if not candidate_recs:
            return make_response({
                "budget_limit": round(budget_limit, 2),
                "total_cost": 0.0,
                "remaining_budget": round(budget_limit, 2),
                "total_risk_reduction_achieved_pct": 0.0,
                "recommendations_considered": 0,
                "recommendations_selected": 0,
                "selected_recommendations": []
            }, source="mock")

        # Calculate efficiency value ratio: risk_reduction_pct / cost
        scored_candidates = []
        for rec in candidate_recs:
            cost = max(1.0, rec.estimated_cost)
            reduction = rec.expected_risk_reduction_pct
            ratio = reduction / cost
            scored_candidates.append({
                "rec": rec,
                "cost": rec.estimated_cost,
                "risk_reduction": reduction,
                "value_ratio": ratio
            })

        # Sort by value ratio descending (Greedy Knapsack)
        scored_candidates.sort(key=lambda x: x["value_ratio"], reverse=True)

        selected = []
        remaining_budget = budget_limit
        total_cost = 0.0
        total_risk_reduction = 0.0

        for item in scored_candidates:
            if item["cost"] <= remaining_budget:
                selected.append(item["rec"].to_dict())
                remaining_budget -= item["cost"]
                total_cost += item["cost"]
                total_risk_reduction += item["risk_reduction"]

        result = {
            "budget_limit": round(budget_limit, 2),
            "total_cost": round(total_cost, 2),
            "remaining_budget": round(remaining_budget, 2),
            "total_risk_reduction_achieved_pct": round(total_risk_reduction, 1),
            "recommendations_considered": len(candidate_recs),
            "recommendations_selected": len(selected),
            "selected_recommendations": selected
        }

        source = candidate_recs[0].source if candidate_recs else "mock"
        return make_response(result, source=source)
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to optimize budget allocation", details=[str(exc)], status_code=500)
