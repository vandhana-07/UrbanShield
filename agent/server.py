"""
UrbanShield Agent HTTP REST Server
Exposes the 6-Layer Multi-Layer AI Agent on localhost:8000 for Flask Backend and Streamlit Frontend communication.
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
    """Health check probe used by backend agent_client and frontend."""
    return jsonify({
        "status": "online",
        "agent": "UrbanShieldAgent",
        "layers_count": 6,
        "layers": ["SENSE", "PREDICT", "PRIORITIZE", "OPTIMIZE", "RECOMMEND", "SIMULATE"],
        "data_provenance": "Real Chennai Observations (OpenCity / GCC / IMD)"
    }), 200


@app.route("/agent/analyze", methods=["POST"])
def analyze_assets():
    """
    Executes the 5-layer pipeline (SENSE -> PREDICT -> PRIORITIZE -> OPTIMIZE -> RECOMMEND)
    on real Chennai municipal zone state.
    """
    try:
        data = request.get_json(silent=True) or {}
        assets_payload = data.get("assets", [])

        # If empty payload or standard call, run the full real Chennai pipeline
        if not assets_payload:
            logger.info("Executing 6-layer pipeline on real Chennai municipal zones...")
            final_df, opt_summary = agent.run_full_pipeline()
            resp = agent_df_to_assessments_response(final_df)
            resp["pipeline_summary"] = opt_summary
            resp["zones"] = final_df.to_dict(orient="records")
            return jsonify(resp), 200

        # If incoming Asset payload from backend, adapt and run pipeline
        zone_df = assets_payload_to_dataframe(assets_payload)
        logger.info(f"Received {len(zone_df)} custom assets. Running 5-layer pipeline...")

        # 1. PREDICT
        pred_df = agent.predict_layer.get_predictions(zone_df)
        # 2. PRIORITIZE
        ranked_df = agent.prioritize_layer.prioritize_zones(pred_df)
        # 3. OPTIMIZE
        alloc_df, opt_summary = agent.optimize_layer.optimize_allocation(ranked_df)
        # 4. RECOMMEND
        final_df = agent.recommend_layer.generate_recommendations(alloc_df)

        resp = agent_df_to_assessments_response(final_df)
        resp["pipeline_summary"] = opt_summary
        resp["zones"] = final_df.to_dict(orient="records")
        logger.info(f"Successfully processed {len(final_df)} assets through all layers.")
        return jsonify(resp), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error in /agent/analyze: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/agent/simulate", methods=["POST"])
def run_simulation():
    """
    Executes Layer 6 (SIMULATE) for what-if scenario testing.
    """
    try:
        data = request.get_json(silent=True) or {}
        intensity = float(data.get("intensity", 0.5))
        budget_limit = float(data.get("budget_limit", 500000.0))
        zone_overrides = data.get("zone_overrides") or {}
        resource_overrides = data.get("resource_overrides") or {}

        # If intensity passed without explicit zone_overrides, scale real Chennai deluge
        if not zone_overrides and intensity > 0:
            # Scale top vulnerable Chennai zones with storm deluge
            zone_overrides = {
                "CHN-Z01": {"rainfall_mm": round(35.0 * (1.0 + intensity), 1), "inundation_depth_inches": round(18.0 * (1.0 + 0.5 * intensity), 1)},
                "CHN-Z03": {"rainfall_mm": round(32.0 * (1.0 + 1.5 * intensity), 1), "inundation_depth_inches": round(12.0 * (1.0 + 0.8 * intensity), 1)},
                "CHN-Z04": {"rainfall_mm": round(49.0 * (1.0 + intensity), 1), "inundation_depth_inches": round(14.0 * (1.0 + 0.5 * intensity), 1)},
            }

        if not resource_overrides:
            resource_overrides = {"total_budget": budget_limit}
        elif "total_budget" not in resource_overrides:
            resource_overrides["total_budget"] = budget_limit

        sim_df, sim_summary, comparison_delta = agent.run_simulation(
            zone_overrides=zone_overrides,
            resource_overrides=resource_overrides
        )

        resp = {
            "source": "agent",
            "simulation_id": f"SIM-CHENNAI-{int(intensity*100)}",
            "status": "completed",
            "baseline_metrics": comparison_delta.get("global_metrics", {}).get("score_coverage_pct", {}),
            "simulated_metrics": sim_summary,
            "comparison_delta": {
                "gained_zones": comparison_delta.get("gained_zones", []),
                "lost_zones": comparison_delta.get("lost_zones", []),
                "global_metrics": comparison_delta.get("global_metrics", {})
            },
            "simulated_zones": sim_df.to_dict(orient="records"),
            "zone_delta": comparison_delta.get("zone_delta_df", sim_df).to_dict(orient="records") if hasattr(comparison_delta.get("zone_delta_df"), "to_dict") else []
        }
        return jsonify(resp), 200

    except Exception as e:
        logger.error(f"Error in /agent/simulate: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting UrbanShield Agent HTTP Server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
