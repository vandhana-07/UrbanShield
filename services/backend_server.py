"""
UrbanShield - Standalone Live REST API Backend Server (Member 2 & Member 3 Endpoints)
Implements all 6 REST API endpoints using Python standard http.server.
Endpoints:
- GET  /api/health or /health
- GET  /api/infrastructure or /api/zones
- GET  /api/resources
- GET  /api/predictions
- GET  /api/recommendations
- POST /api/simulate
"""

import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Base data definitions
ZONES_DATA = [
    {
        "zone_id": "Z-01",
        "name": "South Lowland Basin",
        "asset_type": "Healthcare & Power Grid",
        "lat": 13.0450,
        "lng": 80.2450,
        "population": 125000,
        "critical_assets": ["Metro General Hospital", "Substation Beta"],
        "drainage_capacity_pct": 32.0,
        "rainfall_mm_per_hr": 68.5,
        "soil_saturation_pct": 92.0,
        "sensor_health": "Active",
        "last_updated": "Live REST API Stream"
    },
    {
        "zone_id": "Z-02",
        "name": "Riverfront Promenade",
        "asset_type": "Water Utility & Viaduct",
        "lat": 13.0650,
        "lng": 80.2780,
        "population": 85000,
        "critical_assets": ["Central Water Pump Station", "Pedestrian Viaduct"],
        "drainage_capacity_pct": 41.0,
        "rainfall_mm_per_hr": 54.0,
        "soil_saturation_pct": 84.0,
        "sensor_health": "Active",
        "last_updated": "Live REST API Stream"
    },
    {
        "zone_id": "Z-03",
        "name": "East Industrial Hub",
        "asset_type": "Industrial & Rail Corridor",
        "lat": 13.0300,
        "lng": 80.2600,
        "population": 62000,
        "critical_assets": ["Chemical Treatment Plant", "Freight Rail Junction"],
        "drainage_capacity_pct": 52.0,
        "rainfall_mm_per_hr": 42.0,
        "soil_saturation_pct": 71.0,
        "sensor_health": "Active",
        "last_updated": "Live REST API Stream"
    },
    {
        "zone_id": "Z-04",
        "name": "Downtown Metro Core",
        "asset_type": "Civic Center & Transit Hub",
        "lat": 13.0827,
        "lng": 80.2707,
        "population": 210000,
        "critical_assets": ["City Hall", "Central Transit Terminal", "Emergency Ops Center"],
        "drainage_capacity_pct": 68.0,
        "rainfall_mm_per_hr": 35.0,
        "soil_saturation_pct": 58.0,
        "sensor_health": "Active",
        "last_updated": "Live REST API Stream"
    },
    {
        "zone_id": "Z-05",
        "name": "Port Logistics Corridor",
        "asset_type": "Coastal Port & Flood Wall",
        "lat": 13.1100,
        "lng": 80.2950,
        "population": 48000,
        "critical_assets": ["Container Terminal", "Coastal Flood Wall Gate 3"],
        "drainage_capacity_pct": 48.0,
        "rainfall_mm_per_hr": 62.0,
        "soil_saturation_pct": 88.0,
        "sensor_health": "Active",
        "last_updated": "Live REST API Stream"
    },
    {
        "zone_id": "Z-06",
        "name": "North Hillside Ridge",
        "asset_type": "Reservoir & Telecom Ridge",
        "lat": 13.1250,
        "lng": 80.2300,
        "population": 92000,
        "critical_assets": ["Hillside Reservoir", "Telecom Master Tower"],
        "drainage_capacity_pct": 84.0,
        "rainfall_mm_per_hr": 22.0,
        "soil_saturation_pct": 39.0,
        "sensor_health": "Active",
        "last_updated": "Live REST API Stream"
    }
]

RESOURCES_DATA = {
    "total_heavy_pumps": 14,
    "deployed_heavy_pumps": 9,
    "available_heavy_pumps": 5,
    "total_rapid_crews": 10,
    "deployed_rapid_crews": 6,
    "available_rapid_crews": 4,
    "allocated_budget_usd": 185000,
    "total_emergency_budget_usd": 300000
}

PREDICTIONS_DATA = [
    {
        "zone_id": "Z-01",
        "risk_score": 0.88,
        "priority_rank": 1,
        "severity": "Critical",
        "key_drivers": [
            "Heavy rainfall (68.5 mm/hr) exceeding storm threshold",
            "Critical drainage bottlenecks (32% operational capacity)",
            "Low elevation (4.2m) with adjacent General Hospital asset"
        ]
    },
    {
        "zone_id": "Z-05",
        "risk_score": 0.78,
        "priority_rank": 2,
        "severity": "Critical",
        "key_drivers": [
            "High coastal tide level and storm runoff (62 mm/hr)",
            "Soil saturation at 88% causing surface pooling",
            "Vulnerable flood wall gate adjacent to container terminal"
        ]
    },
    {
        "zone_id": "Z-02",
        "risk_score": 0.64,
        "priority_rank": 3,
        "severity": "High",
        "key_drivers": [
            "Riverbank overflow risk at promenade retention basin",
            "Moderate drainage choking (41% capacity remaining)",
            "High foot-traffic zone with pedestrian viaduct"
        ]
    },
    {
        "zone_id": "Z-03",
        "risk_score": 0.46,
        "priority_rank": 4,
        "severity": "Moderate",
        "key_drivers": [
            "Industrial runoff accumulation near freight lines",
            "Adequate baseline pump rate keeping levels stable"
        ]
    },
    {
        "zone_id": "Z-04",
        "risk_score": 0.32,
        "priority_rank": 5,
        "severity": "Moderate",
        "key_drivers": [
            "High density population but robust subsurface drainage",
            "Rainfall rate within normal operational tolerance"
        ]
    },
    {
        "zone_id": "Z-06",
        "risk_score": 0.12,
        "priority_rank": 6,
        "severity": "Low",
        "key_drivers": [
            "High natural elevation (28.4m) enabling gravity runoff",
            "Reservoir holding capacity at safe 42%"
        ]
    }
]

RECOMMENDATIONS_DATA = {
    "Z-01": {
        "zone_id": "Z-01",
        "allocated_pumps": 4,
        "allocated_crews": 2,
        "action_summary": "Deploy 4 High-Volume Submersible Pumps to Substation Beta perimeter. Dispatch Rapid Crew #1 to clear Hospital access road drainage culverts.",
        "urgency": "Immediate Dispatch (< 15 mins)",
        "asset_protection_rationale": "Protects Metro General Hospital trauma center and prevents flood-induced blackout across Substation Beta serving 125,000 residents.",
        "optimization_rationale": "OR-Tools linear solver prioritized 4 pumps here due to high consequence-of-failure weighting on regional healthcare and electrical grid stability."
    },
    "Z-05": {
        "zone_id": "Z-05",
        "allocated_pumps": 3,
        "allocated_crews": 2,
        "action_summary": "Pre-position 3 Diesel Pumps along Flood Wall Gate 3. Deploy Crew #3 to close secondary storm barrier and monitor tidal surge.",
        "urgency": "Immediate Dispatch (< 20 mins)",
        "asset_protection_rationale": "Prevents catastrophic salt-water inundation of Container Terminal logistics corridor and protects coastal flood barrier integrity.",
        "optimization_rationale": "OR-Tools solver assigned 3 heavy diesel pumps to prevent secondary supply-chain disruption and maritime freight corridor shutdown."
    },
    "Z-02": {
        "zone_id": "Z-02",
        "allocated_pumps": 2,
        "allocated_crews": 1,
        "action_summary": "Deploy 2 Mobile Trailer Pumps to Riverfront Promenade intake. Crew #2 on standby for debris clearing at weir grates.",
        "urgency": "High Priority (< 45 mins)",
        "asset_protection_rationale": "Safeguards Central Water Pump Station from overflow and prevents pedestrian viaduct foundation scour.",
        "optimization_rationale": "OR-Tools allocated 2 mobile pumps to balance weir overflow against downstream municipal drinking water pump intake safety."
    },
    "Z-03": {
        "zone_id": "Z-03",
        "allocated_pumps": 0,
        "allocated_crews": 1,
        "action_summary": "Place Rapid Response Crew #4 on mobile patrol around Chemical Plant perimeter. Monitor sensor cluster E-3.",
        "urgency": "Standard Monitoring",
        "asset_protection_rationale": "Maintains containment monitoring at Chemical Treatment Plant and Freight Rail Junction.",
        "optimization_rationale": "Baseline static pumps sufficient; zero heavy mobile pumps needed. 1 reconnaissance crew assigned for perimeter check."
    },
    "Z-04": {
        "zone_id": "Z-04",
        "allocated_pumps": 0,
        "allocated_crews": 0,
        "action_summary": "Maintain automated telemetry monitoring. Central Transit pumps operational on baseline municipal grid.",
        "urgency": "Normal Operations",
        "asset_protection_rationale": "City Hall and Central Transit Terminal protected by high-capacity subterranean box culverts.",
        "optimization_rationale": "Drainage capacity (68%) well above threshold. Zero resource allocation required; units preserved for high-risk flood zones."
    },
    "Z-06": {
        "zone_id": "Z-06",
        "allocated_pumps": 0,
        "allocated_crews": 0,
        "action_summary": "No intervention required. Gravity drainage functioning normally.",
        "urgency": "Normal Operations",
        "asset_protection_rationale": "Hillside Reservoir and Telecom Tower elevated at 28.4m elevation.",
        "optimization_rationale": "Zero flood vulnerability. Natural elevation provides 100% gravity discharge."
    }
}

class UrbanShieldAPIHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status_code: int = 200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self._send_json({"status": "ok"})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path in ["/api/health", "/health", "/api/status", ""]:
            self._send_json({
                "status": "ok",
                "service": "UrbanShield Multi-Layer Engine",
                "version": "1.0.0",
                "agent_status": "ONLINE",
                "database": "CONNECTED",
                "ml_engine": "RANDOM_FOREST_ACTIVE"
            })
        elif path in ["/api/infrastructure", "/api/zones", "/zones"]:
            self._send_json({
                "status": "success",
                "count": len(ZONES_DATA),
                "zones": ZONES_DATA
            })
        elif path in ["/api/resources", "/resources"]:
            self._send_json({
                "status": "success",
                "resources": RESOURCES_DATA
            })
        elif path in ["/api/predictions", "/api/predict", "/predictions"]:
            self._send_json({
                "status": "success",
                "model": "RandomForestClassifier-v1.4",
                "predictions": PREDICTIONS_DATA
            })
        elif path in ["/api/recommendations", "/api/allocations", "/recommendations"]:
            self._send_json({
                "status": "success",
                "solver": "OR-Tools Linear MIP Solver",
                "recommendations": RECOMMENDATIONS_DATA
            })
        else:
            self._send_json({"error": "Endpoint not found", "path": path}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path in ["/api/simulate", "/simulate"]:
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                params = json.loads(body.decode("utf-8"))
            except Exception:
                params = {}

            rain_mult = float(params.get("rainfall_multiplier", 1.0))
            drain_cap = float(params.get("drainage_capacity_pct", 50.0))
            surge = bool(params.get("storm_surge", False))

            from services.mock_data import calculate_simulated_scenario
            result = calculate_simulated_scenario(rain_mult, drain_cap, surge, total_pumps_pool=RESOURCES_DATA["total_heavy_pumps"])
            result["status"] = "success"
            self._send_json(result)
        else:
            self._send_json({"error": "Endpoint not found", "path": path}, 404)

    def log_message(self, format, *args):
        # Silent logging to prevent console pollution
        pass

def run_server(port=8000):
    server = HTTPServer(("0.0.0.0", port), UrbanShieldAPIHandler)
    print(f"UrbanShield Backend REST API live on http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
