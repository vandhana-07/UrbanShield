from flask import Blueprint
from models import Resource
from routes import make_response, make_error

resources_bp = Blueprint("resources", __name__)

@resources_bp.route("/resources", methods=["GET"])
def get_resources():
    """
    Lists all available municipal emergency resource pools and remaining capacities.
    """
    try:
        resources = Resource.query.all()
        return make_response([r.to_dict() for r in resources], source="mock")
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to retrieve resource pools", details=[str(exc)], status_code=500)
