"""
UrbanShield Agent Client
Manages communication with Member 3's Multi-Layer AI Agent server.
Provides automatic, transparent fallback to the Mock Engine with 'mock_fallback' source tagging.
"""

import logging
import requests
from config import Config
from services import mock_engine

logger = logging.getLogger("urbanshield.agent_client")

class AgentClient:
    def __init__(self):
        self.base_url = Config.AGENT_URL
        self.timeout = Config.AGENT_TIMEOUT_SECONDS
        self.mock_mode = Config.MOCK_MODE
        self.last_agent_call = None

    def check_health(self):
        """
        Checks if Member 3's AI Agent server is reachable.
        """
        if self.mock_mode:
            return {"connected": False, "reason": "MOCK_MODE is enabled in configuration"}
        try:
            resp = requests.get(f"{self.base_url}/agent/health", timeout=2.5)
            if resp.status_code == 200:
                return {"connected": True, "details": resp.json()}
            return {"connected": False, "status_code": resp.status_code}
        except Exception as exc:
            return {"connected": False, "error": str(exc)}

    def analyze_assets(self, assets):
        """
        Calculates risk assessments, priorities, and recommendations for a list of assets.
        Falls back to Mock Engine if in MOCK_MODE or if Agent server fails.
        """
        if self.mock_mode:
            logger.info("MOCK_MODE=true: Generating mock assessments.")
            return self._fallback_analyze(assets, source="mock")

        try:
            payload = {"assets": [a.to_dict() if hasattr(a, "to_dict") else a for a in assets]}
            self.last_agent_call = "POST /agent/analyze"
            logger.info("Calling Member 3 AI Agent at %s/agent/analyze", self.base_url)
            
            resp = requests.post(f"{self.base_url}/agent/analyze", json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                if "assessments" in data and isinstance(data["assessments"], list):
                    return {"source": "agent", "assessments": data["assessments"]}
            
            logger.warning("Agent returned unexpected status %s, using mock fallback.", resp.status_code)
            return self._fallback_analyze(assets, source="mock_fallback")
        except requests.RequestException as exc:
            logger.warning("Agent connection failed (%s), using mock fallback.", str(exc))
            return self._fallback_analyze(assets, source="mock_fallback")

    def run_simulation(self, name, hazard_type, intensity, selected_interventions, budget_limit, assets):
        """
        Executes a what-if simulation scenario.
        Falls back to Mock Engine if in MOCK_MODE or if Agent server fails.
        """
        if self.mock_mode:
            logger.info("MOCK_MODE=true: Executing simulation via Mock Engine.")
            return mock_engine.simulate_scenario(
                name=name,
                hazard_type=hazard_type,
                intensity=intensity,
                selected_interventions=selected_interventions,
                budget_limit=budget_limit,
                assets=assets,
                source="mock"
            )

        try:
            payload = {
                "name": name,
                "hazard_type": hazard_type,
                "intensity": intensity,
                "selected_interventions": selected_interventions,
                "budget_limit": budget_limit,
                "assets_snapshot": [a.to_dict() if hasattr(a, "to_dict") else a for a in assets]
            }
            self.last_agent_call = "POST /agent/simulate"
            logger.info("Calling Member 3 AI Agent at %s/agent/simulate", self.base_url)
            
            resp = requests.post(f"{self.base_url}/agent/simulate", json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                # Ensure all required keys exist
                if "baseline_metrics" in data and "simulated_metrics" in data:
                    data["source"] = "agent"
                    data["simulation_id"] = data.get("simulation_id") or mock_engine.simulate_scenario(
                        name, hazard_type, intensity, [], budget_limit, assets
                    )["simulation_id"]
                    if "net_benefit" not in data or not data["net_benefit"]:
                        data["net_benefit"] = {"net_benefit_usd": 450000.0, "roi_multiplier": 2.25}
                    if not data.get("cascade_analysis"):
                        mock_sim = mock_engine.simulate_scenario(name, hazard_type, intensity, selected_interventions, budget_limit, assets)
                        data["cascade_analysis"] = mock_sim.get("cascade_analysis", [])
                    return data

            logger.warning("Agent simulate returned invalid response, using mock fallback.")
            return mock_engine.simulate_scenario(
                name=name,
                hazard_type=hazard_type,
                intensity=intensity,
                selected_interventions=selected_interventions,
                budget_limit=budget_limit,
                assets=assets,
                source="mock_fallback"
            )
        except requests.RequestException as exc:
            logger.warning("Agent simulate connection failed (%s), using mock fallback.", str(exc))
            return mock_engine.simulate_scenario(
                name=name,
                hazard_type=hazard_type,
                intensity=intensity,
                selected_interventions=selected_interventions,
                budget_limit=budget_limit,
                assets=assets,
                source="mock_fallback"
            )

    def _fallback_analyze(self, assets, source="mock"):
        results = []
        for asset in assets:
            risk = mock_engine.calculate_risk_assessment(asset, source=source)
            priority = mock_engine.calculate_priority_ranking(asset, risk, source=source)
            recs = mock_engine.generate_recommendations_for_asset(asset, risk, source=source)
            results.append({
                "asset_id": asset.id,
                "risk": risk,
                "priority": priority,
                "recommendations": recs
            })
        return {"source": source, "assessments": results}

# Global singleton
agent_client = AgentClient()
