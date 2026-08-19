from flask import Blueprint, request
from database import db
from models import Asset, Simulation
from services.agent_client import agent_client
from routes import make_response, make_error

simulations_bp = Blueprint("simulations", __name__)

ALLOWED_HAZARDS = {"flood", "earthquake", "power_outage", "extreme_heat"}

@simulations_bp.route("/simulations/run", methods=["POST"])
def run_simulation():
    """
    Synchronously executes a what-if infrastructure stress-test simulation.
    Returns baseline vs. simulated metrics, damage prevented, ROI, and cascade analysis.
    """
    try:
        payload = request.get_json(silent=True)
        if not payload:
            return make_error("INVALID_JSON", "Request body must be a valid JSON object", status_code=400)

        # Validation
        if "hazard_type" not in payload:
            return make_error("VALIDATION_ERROR", "Missing required field: 'hazard_type'", status_code=400)

        hazard_type = str(payload["hazard_type"]).strip().lower()
        if hazard_type not in ALLOWED_HAZARDS:
            return make_error(
                "VALIDATION_ERROR",
                f"Invalid hazard_type '{hazard_type}'. Allowed: {', '.join(sorted(ALLOWED_HAZARDS))}",
                status_code=400
            )

        try:
            intensity = float(payload.get("intensity", 0.75))
            budget_limit = float(payload.get("budget_limit", 1000000.0))
        except (ValueError, TypeError) as exc:
            return make_error("VALIDATION_ERROR", "Invalid numeric value for intensity or budget_limit", details=[str(exc)], status_code=400)

        if not (0.0 <= intensity <= 1.0):
            return make_error("VALIDATION_ERROR", "Intensity must be a float between 0.0 and 1.0", status_code=400)
        if budget_limit < 0:
            return make_error("VALIDATION_ERROR", "budget_limit must be a non-negative number", status_code=400)

        name = str(payload.get("name") or f"{hazard_type.capitalize()} Impact Scenario").strip()
        selected_interventions = payload.get("selected_interventions", [])
        if not isinstance(selected_interventions, list):
            return make_error("VALIDATION_ERROR", "'selected_interventions' must be a list of intervention objects", status_code=400)

        # Retrieve assets for simulation
        assets = Asset.query.all()
        if not assets:
            return make_error("PRECONDITION_FAILED", "No assets found in database to simulate against. Please seed the database first.", status_code=400)

        # Execute simulation synchronously via agent_client (or mock fallback)
        sim_result = agent_client.run_simulation(
            name=name,
            hazard_type=hazard_type,
            intensity=intensity,
            selected_interventions=selected_interventions,
            budget_limit=budget_limit,
            assets=assets
        )

        sim_id = sim_result.get("simulation_id")
        source = sim_result.get("source", "mock")

        # Save simulation result to DB
        sim_record = Simulation(
            id=sim_id,
            name=name,
            hazard_type=hazard_type,
            input_parameters={
                "intensity": intensity,
                "hazard_type": hazard_type,
                "interventions_count": len(selected_interventions)
            },
            selected_interventions=selected_interventions,
            budget_limit=budget_limit,
            baseline_metrics=sim_result.get("baseline_metrics", {}),
            simulated_metrics=sim_result.get("simulated_metrics", {}),
            net_benefit=sim_result.get("net_benefit", {}),
            cascade_analysis=sim_result.get("cascade_analysis", []),
            status="completed",
            source=source
        )

        db.session.add(sim_record)
        db.session.commit()

        return make_response(sim_result, source=source, status_code=201)
    except Exception as exc:
        db.session.rollback()
        return make_error("INTERNAL_ERROR", "Simulation execution failed", details=[str(exc)], status_code=500)


@simulations_bp.route("/simulations", methods=["GET"])
def get_simulations():
    """
    List historical simulation runs ordered by execution timestamp.
    """
    try:
        sims = Simulation.query.order_by(Simulation.executed_at.desc()).all()
        source = sims[0].source if sims else "mock"
        return make_response([s.to_dict() for s in sims], source=source)
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to retrieve simulation history", details=[str(exc)], status_code=500)


@simulations_bp.route("/simulations/<simulation_id>", methods=["GET"])
def get_simulation_by_id(simulation_id):
    """
    Retrieve full scenario metrics, baseline vs. simulated charts, and cascade graph data.
    """
    try:
        sim = Simulation.query.get(simulation_id)
        if not sim:
            return make_error("NOT_FOUND", f"Simulation scenario '{simulation_id}' not found", status_code=404)
        return make_response(sim.to_dict(), source=sim.source)
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to retrieve simulation result", details=[str(exc)], status_code=500)
