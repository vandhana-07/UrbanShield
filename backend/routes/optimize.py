from flask import Blueprint, request
from models import Recommendation, Asset
from routes import make_response, make_error
from services.optimizer_service import optimizer_service

optimize_bp = Blueprint("optimize", __name__)

@optimize_bp.route("/optimize/allocate", methods=["POST"])
def optimize_budget_allocation():
    """
    Optimizes intervention recommendation selection under a financial budget constraint
    using Google OR-Tools (Mixed-Integer Linear Programming) with greedy fallback.
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
        
        # Execute OR-Tools optimization
        result = optimizer_service.solve_budget_knapsack(candidate_recs, budget_limit)
        
        source = candidate_recs[0].source if candidate_recs else "mock"
        return make_response(result, source=source)
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to optimize budget allocation", details=[str(exc)], status_code=500)
