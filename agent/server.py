"""
UrbanShield Agent HTTP REST Server
Exposes Member 3's Multi-Layer AI Agent on localhost:8000 for Flask Backend communication.
Endpoints:
  - GET  /agent/health
  - POST /agent/analyze
  - POST /agent/simulate
"""

import logging
import sys
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agent.orchestrator import UrbanShieldAgent
from agent.adapter import assets_payload_to_dataframe, agent_df_to_assessments_response

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s in agent_server: %(message)s")
logger = logging.getLogger("UrbanShield.AgentServer")

app = Flask(__name__)
CORS(app)

# Instantiate single agent instance
agent = UrbanShieldAgent()


@app.route("/agent/health", methods=["GET"])
def health_check():
    """Health check probe used by backend agent_client."""
    return jsonify({
        "status": "online",
        "agent": "UrbanShieldAgent",
        "layers_count": 6,
        "layers": ["SENSE", "PREDICT", "PRIORITIZE", "OPTIMIZE", "RECOMMEND", "SIMULATE"]
    }), 200


@app.route("/agent/analyze", methods=["POST"])
def analyze_assets():
    """
    Executes the 5-layer pipeline (SENSE -> PREDICT -> PRIORITIZE -> OPTIMIZE -> RECOMMEND)
    on incoming Asset payloads from Flask backend.
    """
    try:
        data = request.get_json() or {}
        assets_payload = data.get("assets", [])

        if not assets_payload:
            logger.warning("Received empty assets array in /agent/analyze. Running baseline agent pipeline.")
            final_df, opt_summary = agent.run_full_pipeline()
            resp = agent_df_to_assessments_response(final_df)
            return jsonify(resp), 200

        # Convert Assets to DataFrame
        zone_df = assets_payload_to_dataframe(assets_payload)
        logger.info(f"Received {len(zone_df)} assets. Running 5-layer pipeline...")

        # 1. PREDICT
        pred_df = agent.predict_layer.get_predictions(zone_df)
        # 2. PRIORITIZE
        ranked_df = agent.prioritize_layer.prioritize_zones(pred_df)
        # 3. OPTIMIZE
        alloc_df, opt_summary = agent.optimize_layer.optimize_allocation(ranked_df)
        # 4. RECOMMEND
        final_df = agent.recommend_layer.generate_recommendations(alloc_df)

        resp = agent_df_to_assessments_response(final_df)
        logger.info(f"Successfully processed {len(final_df)} assets through all 5 layers.")
        return jsonify(resp), 200

    except Exception as e:
        logger.error(f"Error in /agent/analyze: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/agent/simulate", methods=["POST"])
def run_simulation():
    """
    Executes Layer 6 (SIMULATE) for what-if scenario testing.
    """
    try:
        data = request.get_json() or {}
        intensity = float(data.get("intensity", 0.5))
        budget_limit = float(data.get("budget_limit", 500000.0))
        assets_snapshot = data.get("assets_snapshot", [])

        # Compute zone overrides based on intensity
        zone_overrides = {}
        if assets_snapshot:
            for asset in assets_snapshot:
                aid = str(asset.get("id"))
                zone_overrides[aid] = {"rainfall": min(200.0, 50.0 + intensity * 150.0)}

        resource_overrides = {"total_budget": budget_limit}

        sim_df, sim_summary, comparison_delta = agent.run_simulation(
            zone_overrides=zone_overrides,
            resource_overrides=resource_overrides
        )

        resp = {
            "source": "agent",
            "simulation_id": f"SIM-AGENT-{int(intensity*100)}",
            "status": "completed",
            "baseline_metrics": comparison_delta["global_metrics"]["score_coverage_pct"],
            "simulated_metrics": sim_summary,
            "comparison_delta": {
                "gained_zones": comparison_delta.get("gained_zones", []),
                "lost_zones": comparison_delta.get("lost_zones", [])
            }
        }
        return jsonify(resp), 200

    except Exception as e:
        logger.error(f"Error in /agent/simulate: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = 8000
    logger.info(f"Starting UrbanShield Agent HTTP Server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
