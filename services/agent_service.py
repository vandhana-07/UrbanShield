"""
UrbanShield - Multi-Layer Agent Service (Member 3 Seam)
Provides Random Forest risk scores, ranked priority ordering, OR-Tools resource allocation,
and what-if simulation recalculations.
Supports live REST API connection, local model.pkl inference, performance caching,
and fallback to mock_data.py.
"""

import os
import streamlit as st
from typing import List, Dict, Any
from services.mock_data import (
    MOCK_PIPELINE_PREDICTIONS,
    MOCK_RECOMMENDATIONS_AND_ALLOCATIONS,
    calculate_simulated_scenario
)
from services.api_client import (
    check_backend_health,
    fetch_api_predictions,
    fetch_api_recommendations,
    fetch_api_simulation
)

def get_model_source_status() -> Dict[str, Any]:
    """
    Returns explicit status of the AI/ML Agent layer for header and sidebar badges.
    Follows Step 7 Fallback Architecture:
    🟢 Live ML API -> 🟡 Local Model (RF + OR-Tools) -> 🟠 Mock Fallback
    """
    # 1. Check REST API
    api_health = check_backend_health()
    if api_health.get("is_live"):
        return {
            "mode": f"Live ML API ({api_health['url']})",
            "is_live": True,
            "badge_color": "#10B981",
            "tier": "live",
            "icon": "🟢",
            "details": f"Connected to {api_health['url']}"
        }

    # 2. Check local trained model artifact
    for m_name in ["model.pkl", "rf_model.pkl", "random_forest.pkl", "model.joblib"]:
        model_file = os.path.join(os.getcwd(), m_name)
        if os.path.exists(model_file):
            return {
                "mode": f"Local Model ({m_name})",
                "is_live": True,
                "badge_color": "#3B82F6",
                "tier": "model",
                "icon": "🟡",
                "details": f"Loaded local AI/ML artifact: {m_name}"
            }

    # 3. Fallback Mock predictions
    return {
        "mode": "Calibrated Mock Fallback",
        "is_live": False,
        "badge_color": "#EA580C",
        "tier": "mock",
        "icon": "🟠",
        "details": "model.pkl / ML API not found; serving calibrated multi-layer agent predictions"
    }

@st.cache_data(show_spinner=False, ttl=10)
def get_pipeline_predictions() -> List[Dict[str, Any]]:
    """
    PREDICT + PRIORITIZE Layer Output (Random Forest & Priority Ranking).
    Attempts REST API, then local model.pkl, then fallback mock data.
    """
    try:
        # 1. Try REST API
        api_preds = fetch_api_predictions()
        if api_preds is not None and len(api_preds) > 0:
            return api_preds

        # 2. Try local model.pkl if exists
        for m_name in ["model.pkl", "rf_model.pkl", "random_forest.pkl"]:
            model_file = os.path.join(os.getcwd(), m_name)
            if os.path.exists(model_file):
                import pickle
                try:
                    with open(model_file, "rb") as f:
                        loaded_model = pickle.load(f)
                    from services.data_service import get_zones_summary
                    from config import get_severity
                    zones = get_zones_summary()
                    preds = []
                    for idx, z in enumerate(zones):
                        # Extract standard feature vector
                        feat = [[
                            float(z.get("rainfall_mm_per_hr", 30.0)),
                            float(z.get("soil_saturation_pct", 50.0)),
                            float(z.get("drainage_capacity_pct", 50.0)),
                            float(z.get("elevation_m", 10.0))
                        ]]
                        prob = float(loaded_model.predict_proba(feat)[0][1]) if hasattr(loaded_model, "predict_proba") else float(loaded_model.predict(feat)[0])
                        prob = max(0.0, min(1.0, prob))
                        preds.append({
                            "zone_id": z.get("zone_id", f"Z-0{idx+1}"),
                            "risk_score": round(prob, 2),
                            "severity": get_severity(prob),
                            "key_drivers": [
                                f"Active precipitation: {z.get('rainfall_mm_per_hr', 0)} mm/hr",
                                f"Drainage capacity at {z.get('drainage_capacity_pct', 0)}%"
                            ]
                        })
                    preds.sort(key=lambda x: x["risk_score"], reverse=True)
                    for rank_idx, p in enumerate(preds, 1):
                        p["priority_rank"] = rank_idx
                    return preds
                except Exception as me:
                    print(f"[WARN] Local model inference failed: {me}. Falling back to mock data.")

        return MOCK_PIPELINE_PREDICTIONS
    except Exception as e:
        print(f"[ERROR] agent_service.get_pipeline_predictions failed: {e}. Falling back to mock data.")
        return MOCK_PIPELINE_PREDICTIONS

@st.cache_data(show_spinner=False, ttl=10)
def get_recommendations_and_allocations() -> Dict[str, Dict[str, Any]]:
    """
    OPTIMIZE + RECOMMEND Layer Output (OR-Tools resource allocation & action summaries).
    Attempts REST API first, then fallback mock data.
    """
    try:
        api_recs = fetch_api_recommendations()
        if api_recs is not None and len(api_recs) > 0:
            return api_recs

        return MOCK_RECOMMENDATIONS_AND_ALLOCATIONS
    except Exception as e:
        print(f"[ERROR] agent_service.get_recommendations_and_allocations failed: {e}. Falling back to mock recommendations.")
        return MOCK_RECOMMENDATIONS_AND_ALLOCATIONS

def run_simulation(rainfall_multiplier: float, drainage_capacity_pct: float, storm_surge: bool) -> Dict[str, Any]:
    """
    SIMULATE Layer Output (What-If Sandbox recalculation).
    Attempts backend API simulation endpoint, then falls back to calibrated simulation logic.
    """
    try:
        api_sim = fetch_api_simulation(rainfall_multiplier, drainage_capacity_pct, storm_surge)
        if api_sim is not None:
            return api_sim

        return calculate_simulated_scenario(rainfall_multiplier, drainage_capacity_pct, storm_surge)
    except Exception as e:
        print(f"[ERROR] agent_service.run_simulation failed: {e}")
        return calculate_simulated_scenario(rainfall_multiplier, drainage_capacity_pct, storm_surge)
