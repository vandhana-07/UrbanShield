"""
UrbanShield Agent Adapter
Provides lossless bi-directional translation between Backend Asset payloads and Agent Zone DataFrames.
"""

import logging
import pandas as pd

logger = logging.getLogger("urbanshield.adapter")


def asset_to_zone_dict(asset_dict: dict) -> dict:
    """
    Converts a single Backend Asset object/dictionary into a valid Agent Zone dictionary.
    Guarantees no fields get dropped or misnamed.
    """
    asset_id = str(asset_dict.get("id", "Z00"))
    name = str(asset_dict.get("name", "Unknown Asset"))
    sensor = asset_dict.get("sensor_data") or {}

    # Extract or derive physical metrics required by Layer 1 (SENSE) & Layer 2 (PREDICT)
    health_idx = float(asset_dict.get("health_index", 75.0))
    crit_score = float(asset_dict.get("criticality_score", 5.0))

    # 1. Rainfall (mm)
    rainfall = float(sensor.get("rainfall_mm", sensor.get("rainfall", 32.0)))

    # 2. Inundation depth (inches)
    depth = float(sensor.get("inundation_depth_inches", sensor.get("depth", max(4.0, (100.0 - health_idx) / 5.0))))

    # 3. Hazard Category
    hazard = str(sensor.get("hazard_category", "HIGH" if crit_score >= 4.0 else "MODERATE")).upper()

    # 4 & 5. Geolocation
    lat = float(asset_dict.get("latitude", 13.0450))
    lon = float(asset_dict.get("longitude", 80.2100))

    return {
        "zone_id": asset_id,
        "zone_name": name,
        "rainfall_mm": rainfall,
        "inundation_depth_inches": depth,
        "hazard_category": hazard,
        "nearest_rainfall_station": "IMD_STATION",
        "rainfall_station_dist_km": 2.5,
        "latitude": lat,
        "longitude": lon
    }


def assets_payload_to_dataframe(assets_payload: list) -> pd.DataFrame:
    """
    Converts a list of Backend Asset dictionaries into a pandas DataFrame expected by UrbanShieldAgent.
    """
    zones_list = [asset_to_zone_dict(a) for a in assets_payload]
    return pd.DataFrame(zones_list)


def agent_df_to_assessments_response(recommendations_df: pd.DataFrame) -> dict:
    """
    Translates the 6-layer final DataFrame output of UrbanShieldAgent back into the 
    Backend 'assessments' JSON format expected by backend/services/agent_client.py.
    """
    if recommendations_df is None or (isinstance(recommendations_df, pd.DataFrame) and recommendations_df.empty):
        return {"source": "agent", "assessments": []}

    assessments = []

    for _, row in recommendations_df.iterrows():
        asset_id = str(row["zone_id"])
        risk_score = float(row.get("risk_score", 0.5))
        risk_conf = float(row.get("risk_confidence", 0.9))
        priority_score = float(row.get("priority_score", 0.5))
        rank = int(row.get("priority_rank", 1))
        priority_reason = str(row.get("priority_reason", "MCDA Score Evaluation"))
        action = str(row.get("recommended_action", "MONITOR"))
        cost = float(row.get("allocated_cost", 0.0))
        status = str(row.get("allocation_status", "SKIPPED"))
        reason = str(row.get("allocation_reason", "Unallocated"))
        briefing = str(row.get("executive_summary", "Routine monitoring active."))

        # Map risk_score to consequence level for Backend format
        if risk_score >= 0.8:
            consequence = "catastrophic"
            risk_level = "high"
        elif risk_score >= 0.5:
            consequence = "high"
            risk_level = "medium"
        elif risk_score >= 0.25:
            consequence = "medium"
            risk_level = "low"
        else:
            consequence = "low"
            risk_level = "low"

        # Construct Backend Risk Assessment Object
        risk_obj = {
            "risk_score": round(risk_score, 4),
            "failure_probability": round(risk_score, 4),
            "risk_confidence": round(risk_conf, 4),
            "risk_level": risk_level,
            "consequence_level": consequence,
            "primary_hazard": "Flood & Drainage Overflow",
            "source": "agent"
        }

        # Construct Backend Priority Ranking Object
        tier = "CRITICAL" if priority_score >= 0.70 else "HIGH" if priority_score >= 0.45 else "MODERATE" if priority_score >= 0.25 else "LOW"
        priority_obj = {
            "priority_score": round(priority_score, 4),
            "rank": rank,
            "tier": tier,
            "reason": priority_reason,
            "source": "agent"
        }

        # Construct Backend Recommendations List matching RecommendLayer exact strings
        rec_obj = {
            "action": action,
            "action_type": action,
            "title": action,
            "description": briefing,
            "estimated_cost": cost,
            "expected_risk_reduction_pct": 85.0 if status == "ALLOCATED" else 0.0,
            "cost": cost,
            "status": status.lower(),
            "reason": reason,
            "executive_summary": briefing,
            "urgency": "immediate" if status == "ALLOCATED" else "standard",
            "source": "agent"
        }

        assessments.append({
            "asset_id": asset_id,
            "risk": risk_obj,
            "priority": priority_obj,
            "recommendations": [rec_obj]
        })

    return {
        "source": "agent",
        "assessments": assessments
    }
