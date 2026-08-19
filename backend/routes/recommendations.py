from flask import Blueprint, request
from database import db
from models import Recommendation
from routes import make_response, make_error

recommendations_bp = Blueprint("recommendations", __name__)

ALLOWED_REC_STATUSES = {"pending", "approved", "rejected", "in_progress"}

@recommendations_bp.route("/recommendations", methods=["GET"])
def get_recommendations():
    """
    List AI-driven intervention recommendations with optional filtering by status and asset_id.
    """
    try:
        query = Recommendation.query
        
        status = request.args.get("status")
        if status:
            query = query.filter(Recommendation.status == status.strip().lower())
            
        asset_id = request.args.get("asset_id")
        if asset_id:
            query = query.filter(Recommendation.asset_id == asset_id.strip())

        recs = query.order_by(Recommendation.expected_risk_reduction_pct.desc()).all()
        source = recs[0].source if recs else "mock"
        return make_response([r.to_dict() for r in recs], source=source)
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to retrieve recommendations", details=[str(exc)], status_code=500)


@recommendations_bp.route("/recommendations/<int:rec_id>", methods=["PATCH"])
def update_recommendation_status(rec_id):
    """
    Update the decision status of an intervention recommendation (e.g. approve or reject).
    """
    try:
        payload = request.get_json(silent=True)
        if not payload:
            return make_error("INVALID_JSON", "Request body must be a valid JSON object", status_code=400)

        if "status" not in payload:
            return make_error("VALIDATION_ERROR", "Missing required field: 'status'", status_code=400)

        new_status = str(payload["status"]).strip().lower()
        if new_status not in ALLOWED_REC_STATUSES:
            return make_error(
                "VALIDATION_ERROR",
                f"Invalid status '{new_status}'. Allowed statuses: {', '.join(sorted(ALLOWED_REC_STATUSES))}",
                status_code=400
            )

        rec = Recommendation.query.get(rec_id)
        if not rec:
            return make_error("NOT_FOUND", f"Recommendation with ID {rec_id} not found", status_code=404)

        rec.status = new_status
        db.session.commit()

        return make_response(rec.to_dict(), source=rec.source)
    except Exception as exc:
        db.session.rollback()
        return make_error("INTERNAL_ERROR", "Failed to update recommendation", details=[str(exc)], status_code=500)
