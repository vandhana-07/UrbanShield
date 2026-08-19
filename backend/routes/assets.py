import uuid
from flask import Blueprint, request
from database import db
from models import Asset, RiskAssessment, PriorityRanking, Recommendation
from services.agent_client import agent_client
from routes import make_response, make_error

assets_bp = Blueprint("assets", __name__)

ALLOWED_CATEGORIES = {"bridge", "road", "drainage", "water", "power", "public_building"}
ALLOWED_STATUSES = {"healthy", "degraded", "critical"}

@assets_bp.route("/assets", methods=["GET"])
def get_assets():
    """
    List all infrastructure assets with optional filtering by category, status, and zone.
    """
    try:
        query = Asset.query
        
        category = request.args.get("category")
        if category:
            query = query.filter(Asset.category == category.strip().lower())
            
        status = request.args.get("status")
        if status:
            query = query.filter(Asset.status == status.strip().lower())
            
        zone = request.args.get("zone")
        if zone:
            query = query.filter(Asset.zone.ilike(f"%{zone.strip()}%"))

        assets = query.all()
        return make_response([a.to_dict() for a in assets], source="mock")
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to retrieve assets", details=[str(exc)], status_code=500)


@assets_bp.route("/assets/<asset_id>", methods=["GET"])
def get_asset_by_id(asset_id):
    """
    Retrieve single asset details including sensor telemetry, latest risk score, and recommendations.
    """
    try:
        asset = Asset.query.get(asset_id)
        if not asset:
            return make_error("NOT_FOUND", f"Asset with ID '{asset_id}' not found", status_code=404)
        
        return make_response(asset.to_dict(include_relations=True), source="mock")
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to retrieve asset details", details=[str(exc)], status_code=500)


@assets_bp.route("/assets", methods=["POST"])
def create_asset():
    """
    Register a new infrastructure asset and generate its initial risk assessment.
    """
    try:
        payload = request.get_json(silent=True)
        if not payload:
            return make_error("INVALID_JSON", "Request body must be a valid JSON object", status_code=400)

        # Validation
        required = ["name", "category", "latitude", "longitude", "zone", "year_built"]
        missing = [f for f in required if f not in payload]
        if missing:
            return make_error("VALIDATION_ERROR", f"Missing required fields: {', '.join(missing)}", status_code=400)

        category = str(payload["category"]).strip().lower()
        if category not in ALLOWED_CATEGORIES:
            return make_error(
                "VALIDATION_ERROR",
                f"Invalid category '{category}'. Allowed categories: {', '.join(sorted(ALLOWED_CATEGORIES))}",
                status_code=400
            )

        try:
            lat = float(payload["latitude"])
            lng = float(payload["longitude"])
            year_built = int(payload["year_built"])
            health_index = float(payload.get("health_index", 85.0))
            criticality = float(payload.get("criticality_score", 5.0))
        except (ValueError, TypeError) as exc:
            return make_error("VALIDATION_ERROR", "Invalid data type for numeric field", details=[str(exc)], status_code=400)

        # Range checks
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
            return make_error("VALIDATION_ERROR", "Latitude must be [-90, 90] and Longitude [-180, 180]", status_code=400)
        if not (0.0 <= health_index <= 100.0):
            return make_error("VALIDATION_ERROR", "health_index must be between 0.0 and 100.0", status_code=400)
        if not (1.0 <= criticality <= 10.0):
            return make_error("VALIDATION_ERROR", "criticality_score must be between 1.0 and 10.0", status_code=400)

        # Generate asset ID if not provided
        prefix_map = {"bridge": "BRG", "road": "RD", "drainage": "DRN", "water": "WTR", "power": "PWR", "public_building": "BLD"}
        prefix = prefix_map.get(category, "AST")
        asset_id = payload.get("id") or f"AST-{prefix}-{uuid.uuid4().hex[:4].upper()}"

        # Determine initial status
        status = payload.get("status", "healthy").strip().lower()
        if status not in ALLOWED_STATUSES:
            if health_index < 45.0:
                status = "critical"
            elif health_index < 70.0:
                status = "degraded"
            else:
                status = "healthy"

        asset = Asset(
            id=asset_id,
            name=payload["name"].strip(),
            category=category,
            latitude=lat,
            longitude=lng,
            zone=payload["zone"].strip(),
            year_built=year_built,
            health_index=health_index,
            criticality_score=criticality,
            status=status,
            sensor_data=payload.get("sensor_data", {})
        )

        db.session.add(asset)
        db.session.flush()

        # Compute initial risk & priority via agent_client
        analysis = agent_client.analyze_assets([asset])
        assessments = analysis.get("assessments", [])
        source = analysis.get("source", "mock")

        if assessments:
            first = assessments[0]
            risk_data = first.get("risk", {})
            priority_data = first.get("priority", {})
            recs_data = first.get("recommendations", [])

            risk_obj = RiskAssessment(
                asset_id=asset.id,
                risk_score=risk_data.get("risk_score", 0.5),
                failure_probability=risk_data.get("failure_probability", 0.4),
                consequence_level=risk_data.get("consequence_level", "medium"),
                primary_hazard=risk_data.get("primary_hazard", "Environmental Stress"),
                predicted_days_to_failure=risk_data.get("predicted_days_to_failure", 180),
                confidence_score=risk_data.get("confidence_score", 0.85),
                source=source
            )
            db.session.add(risk_obj)

            priority_obj = PriorityRanking(
                asset_id=asset.id,
                rank=Asset.query.count(),
                priority_tier=priority_data.get("priority_tier", "P3_MEDIUM"),
                composite_urgency_score=priority_data.get("composite_urgency_score", 50.0),
                estimated_population_impact=priority_data.get("estimated_population_impact", 10000),
                estimated_economic_exposure=priority_data.get("estimated_economic_exposure", 500000.0),
                source=source
            )
            db.session.add(priority_obj)

            for r in recs_data:
                rec_obj = Recommendation(
                    asset_id=asset.id,
                    action_type=r.get("action_type", "sensor_audit"),
                    title=r.get("title", "Standard Inspection"),
                    description=r.get("description", "Perform baseline sensor inspection."),
                    estimated_cost=r.get("estimated_cost", 50000.0),
                    expected_risk_reduction_pct=r.get("expected_risk_reduction_pct", 30.0),
                    status="pending",
                    tradeoff_analysis=r.get("tradeoff_analysis", {}),
                    source=source
                )
                db.session.add(rec_obj)

        db.session.commit()
        return make_response(asset.to_dict(include_relations=True), source=source, status_code=201)
    except Exception as exc:
        db.session.rollback()
        return make_error("INTERNAL_ERROR", "Failed to create asset", details=[str(exc)], status_code=500)
