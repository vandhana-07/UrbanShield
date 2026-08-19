from flask import Blueprint
from models import RiskAssessment, PriorityRanking
from routes import make_response, make_error

risks_bp = Blueprint("risks", __name__)

@risks_bp.route("/risks", methods=["GET"])
def get_risks():
    """
    List all active infrastructure risk assessments sorted by risk severity.
    """
    try:
        risks = RiskAssessment.query.order_by(RiskAssessment.risk_score.desc()).all()
        source = risks[0].source if risks else "mock"
        return make_response([r.to_dict() for r in risks], source=source)
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to retrieve risk assessments", details=[str(exc)], status_code=500)


@risks_bp.route("/priorities", methods=["GET"])
def get_priorities():
    """
    List infrastructure assets prioritized by composite urgency rank.
    """
    try:
        priorities = PriorityRanking.query.order_by(PriorityRanking.rank.asc()).all()
        source = priorities[0].source if priorities else "mock"
        return make_response([p.to_dict() for p in priorities], source=source)
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to retrieve priority rankings", details=[str(exc)], status_code=500)
