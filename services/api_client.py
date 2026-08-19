"""
UrbanShield - Backend API Client & Service Integration Layer
Handles REST API communication with the backend (Member 2 & Member 3 endpoints),
supports environment variable configuration (URBANSHIELD_API_URL / BACKEND_API_URL),
normalizes disparate backend schemas, and enforces short timeouts with graceful fallbacks.
"""

import os
import requests
from typing import List, Dict, Any, Optional

# Default API URL from environment variable or local dev default
DEFAULT_API_URL = os.environ.get(
    "URBANSHIELD_API_URL",
    os.environ.get("BACKEND_API_URL", "http://localhost:8000")
).rstrip("/")

REQUEST_TIMEOUT_SECONDS = float(os.environ.get("URBANSHIELD_API_TIMEOUT", "0.4"))

def get_configured_api_url() -> str:
    """Returns the currently active backend API URL."""
    return os.environ.get(
        "URBANSHIELD_API_URL",
        os.environ.get("BACKEND_API_URL", "http://localhost:8000")
    ).rstrip("/")

try:
    import streamlit as st
    _cache_decorator = st.cache_data(ttl=3, show_spinner=False)
except Exception:
    def _cache_decorator(func):
        return func

@_cache_decorator
def check_backend_health() -> Dict[str, Any]:
    """
    Pings backend health or root endpoint to determine connectivity.
    Cached for 3 seconds to avoid redundant round-trips across UI components.
    Returns status dict with connectivity info and latency.
    """
    api_url = get_configured_api_url()
    try:
        # Check standard health endpoints
        for endpoint in ["/api/health", "/health", "/api/status", "/"]:
            url = f"{api_url}{endpoint}"
            try:
                resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
                if resp.status_code in [200, 201, 204]:
                    return {
                        "is_live": True,
                        "url": api_url,
                        "endpoint": endpoint,
                        "status_code": resp.status_code,
                        "message": f"Connected to {api_url}"
                    }
            except (requests.ConnectionError, requests.Timeout):
                # Server host is completely unreachable; do not waste time retrying further endpoints on dead port
                break
            except requests.RequestException:
                continue
        return {
            "is_live": False,
            "url": api_url,
            "message": f"No response from {api_url} (offline/unreachable)"
        }
    except Exception as e:
        return {
            "is_live": False,
            "url": api_url,
            "message": f"Connection error: {str(e)}"
        }

def normalize_zone_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes variable backend field naming into frontend schema:
    - zone_id / id / zone -> zone_id
    - name / zone_name / asset_name -> name
    - lat / latitude -> lat
    - lng / lon / longitude -> lng
    - population / pop -> population
    - critical_assets / assets / protected_assets -> critical_assets
    - drainage_capacity_pct / drainage / capacity -> drainage_capacity_pct
    - rainfall_mm_per_hr / rainfall / precipitation -> rainfall_mm_per_hr
    - soil_saturation_pct / saturation / soil_moisture -> soil_saturation_pct
    - sensor_health / status -> sensor_health
    - last_updated / updated_at / timestamp -> last_updated
    """
    if not isinstance(raw, dict):
        return {}

    zone_id = str(raw.get("zone_id") or raw.get("id") or raw.get("zone") or "Z-XX")
    name = str(raw.get("name") or raw.get("zone_name") or raw.get("asset_name") or f"Zone {zone_id}")
    lat = float(raw.get("lat") or raw.get("latitude") or 13.0827)
    lng = float(raw.get("lng") or raw.get("lon") or raw.get("longitude") or 80.2707)
    pop = int(raw.get("population") or raw.get("pop") or 50000)
    
    raw_assets = raw.get("critical_assets") or raw.get("assets") or raw.get("protected_assets")
    if isinstance(raw_assets, str) and raw_assets.strip():
        assets = [a.strip() for a in raw_assets.split(",") if a.strip()]
    elif isinstance(raw_assets, list) and len(raw_assets) > 0:
        assets = [str(a) for a in raw_assets]
    else:
        assets = ["Municipal Infrastructure"]

    # Asset Type / Category
    asset_type_defaults = {
        "Z-01": "Healthcare & Power Grid",
        "Z-02": "Water Utility & Viaduct",
        "Z-03": "Industrial & Rail Corridor",
        "Z-04": "Civic Center & Transit Hub",
        "Z-05": "Coastal Port & Flood Wall",
        "Z-06": "Reservoir & Telecom Ridge"
    }
    asset_type = str(
        raw.get("asset_type") or raw.get("type") or raw.get("category") or
        asset_type_defaults.get(zone_id, "Urban Infrastructure")
    )

    drainage = float(raw.get("drainage_capacity_pct") or raw.get("drainage") or raw.get("capacity") or 50.0)
    rainfall = float(raw.get("rainfall_mm_per_hr") or raw.get("rainfall") or raw.get("precipitation") or 0.0)
    saturation = float(raw.get("soil_saturation_pct") or raw.get("saturation") or raw.get("soil_moisture") or 50.0)
    sensor_health = str(raw.get("sensor_health") or raw.get("status") or "Active")
    last_updated = str(raw.get("last_updated") or raw.get("updated_at") or "Live")

    return {
        "zone_id": zone_id,
        "name": name,
        "asset_type": asset_type,
        "lat": lat,
        "lng": lng,
        "population": pop,
        "critical_assets": assets,
        "drainage_capacity_pct": drainage,
        "rainfall_mm_per_hr": rainfall,
        "soil_saturation_pct": saturation,
        "sensor_health": sensor_health,
        "last_updated": last_updated
    }

def normalize_prediction_record(raw: Dict[str, Any], default_rank: int = 1) -> Dict[str, Any]:
    """
    Normalizes variable ML backend prediction formats.
    """
    if not isinstance(raw, dict):
        return {}

    zone_id = str(raw.get("zone_id") or raw.get("id") or raw.get("zone") or "Z-XX")
    risk = float(raw.get("risk_score") or raw.get("risk") or raw.get("score") or raw.get("probability") or 0.0)
    # Clamp risk between 0.0 and 1.0
    risk = max(0.0, min(1.0, risk))
    
    # Severity classification
    from config import get_severity
    severity = raw.get("severity") or get_severity(risk)
    rank = int(raw.get("priority_rank") or raw.get("rank") or raw.get("priority") or default_rank)
    
    raw_drivers = raw.get("key_drivers") or raw.get("drivers") or raw.get("reasons")
    if isinstance(raw_drivers, str) and raw_drivers.strip():
        drivers = [d.strip() for d in raw_drivers.split(",") if d.strip()]
    elif isinstance(raw_drivers, list) and len(raw_drivers) > 0:
        drivers = [str(d) for d in raw_drivers]
    else:
        drivers = [f"Automated risk classification score: {risk:.2f}"]

    return {
        "zone_id": zone_id,
        "risk_score": round(risk, 2),
        "priority_rank": rank,
        "severity": severity,
        "key_drivers": drivers
    }

def fetch_api_zones() -> Optional[List[Dict[str, Any]]]:
    """
    Queries backend REST endpoint for infrastructure zone data.
    Tries endpoints: /api/infrastructure, /api/zones, /zones
    """
    if not check_backend_health().get("is_live"):
        return None

    api_url = get_configured_api_url()
    for endpoint in ["/api/infrastructure", "/api/zones", "/zones"]:
        url = f"{api_url}{endpoint}"
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and "zones" in data:
                    items = data["zones"]
                elif isinstance(data, dict) and "data" in data:
                    items = data["data"]
                elif isinstance(data, list):
                    items = data
                else:
                    continue
                return [normalize_zone_record(z) for z in items if isinstance(z, dict)]
        except requests.RequestException:
            continue
    return None

def fetch_api_resources() -> Optional[Dict[str, Any]]:
    """
    Queries backend REST endpoint for municipal resource pools.
    Tries endpoints: /api/resources, /resources
    """
    if not check_backend_health().get("is_live"):
        return None

    api_url = get_configured_api_url()
    for endpoint in ["/api/resources", "/resources"]:
        url = f"{api_url}{endpoint}"
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                res_dict = data.get("resources", data) if isinstance(data, dict) else {}
                if res_dict:
                    return {
                        "total_heavy_pumps": int(res_dict.get("total_heavy_pumps", 14)),
                        "deployed_heavy_pumps": int(res_dict.get("deployed_heavy_pumps", 9)),
                        "available_heavy_pumps": int(res_dict.get("available_heavy_pumps", 5)),
                        "total_rapid_crews": int(res_dict.get("total_rapid_crews", 10)),
                        "deployed_rapid_crews": int(res_dict.get("deployed_rapid_crews", 6)),
                        "available_rapid_crews": int(res_dict.get("available_rapid_crews", 4)),
                        "allocated_budget_usd": int(res_dict.get("allocated_budget_usd", 185000)),
                        "total_emergency_budget_usd": int(res_dict.get("total_emergency_budget_usd", 300000))
                    }
        except requests.RequestException:
            continue
    return None

def fetch_api_predictions() -> Optional[List[Dict[str, Any]]]:
    """
    Queries backend AI/ML REST endpoint for flood predictions.
    Tries endpoints: /api/predictions, /api/predict, /predictions
    """
    if not check_backend_health().get("is_live"):
        return None

    api_url = get_configured_api_url()
    for endpoint in ["/api/predictions", "/api/predict", "/predictions"]:
        url = f"{api_url}{endpoint}"
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("predictions", data) if isinstance(data, dict) else data
                if isinstance(items, list):
                    return [normalize_prediction_record(p, idx + 1) for idx, p in enumerate(items)]
        except requests.RequestException:
            continue
    return None

def fetch_api_recommendations() -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Queries backend OR-Tools optimization endpoint for allocations & actions.
    Tries endpoints: /api/recommendations, /api/allocations, /recommendations
    """
    if not check_backend_health().get("is_live"):
        return None

    api_url = get_configured_api_url()
    for endpoint in ["/api/recommendations", "/api/allocations", "/recommendations"]:
        url = f"{api_url}{endpoint}"
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("recommendations", data) if isinstance(data, dict) else data
                if isinstance(items, dict):
                    return items
                elif isinstance(items, list):
                    recs_by_id = {}
                    for rec in items:
                        if isinstance(rec, dict) and "zone_id" in rec:
                            recs_by_id[rec["zone_id"]] = rec
                    return recs_by_id
        except requests.RequestException:
            continue
    return None

def fetch_api_simulation(rainfall_multiplier: float, drainage_capacity_pct: float, storm_surge: bool) -> Optional[Dict[str, Any]]:
    """
    Queries backend simulation endpoint with scenario parameters.
    """
    if not check_backend_health().get("is_live"):
        return None

    api_url = get_configured_api_url()
    payload = {
        "rainfall_multiplier": rainfall_multiplier,
        "drainage_capacity_pct": drainage_capacity_pct,
        "storm_surge": storm_surge
    }
    for endpoint in ["/api/simulate", "/simulate"]:
        url = f"{api_url}{endpoint}"
        try:
            resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and "zones" in data:
                    return data
        except requests.RequestException:
            continue
    return None
