from flask import Blueprint
from config import Config
from models import Asset
from services.agent_client import agent_client
from routes import make_response, make_error

system_bp = Blueprint("system", __name__)

@system_bp.route("/system/status", methods=["GET"])
def get_system_status():
    """
    Returns backend operational status, active mode, agent connectivity, and asset counts.
    """
    try:
        total_assets = Asset.query.count()
        agent_health = agent_client.check_health()
        
        active_source = "mock" if Config.MOCK_MODE else ("agent" if agent_health.get("connected") else "mock_fallback")

        data = {
            "status": "healthy",
            "mock_mode": Config.MOCK_MODE,
            "active_source": active_source,
            "agent_endpoint": Config.AGENT_URL,
            "agent_connected": agent_health.get("connected", False),
            "database": "sqlite_connected",
            "total_assets": total_assets,
            "last_agent_call": agent_client.last_agent_call
        }
        return make_response(data, source="system")
    except Exception as exc:
        return make_error("INTERNAL_ERROR", "Failed to retrieve system status", details=[str(exc)], status_code=500)
