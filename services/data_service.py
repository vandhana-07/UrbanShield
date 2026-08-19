"""
UrbanShield - Data Service (Member 2 Seam)
Provides zone summaries, environmental sensor telemetry, and municipal resource pools.
Supports live REST API connection (via services.api_client), live SQLite DB connection,
and automatic fallback to mock_data.py with visible UI telemetry badges.
"""

import os
from typing import List, Dict, Any
from services.mock_data import MOCK_ZONES_SUMMARY, MOCK_RESOURCES
from services.api_client import (
    get_configured_api_url,
    check_backend_health,
    fetch_api_zones,
    fetch_api_resources
)

def get_data_source_status() -> Dict[str, Any]:
    """
    Returns explicit status of the data layer for header and sidebar badges.
    Follows Step 7 Fallback Architecture:
    🟢 Live REST API -> 🟡 SQLite DB -> 🟠 Mock Fallback
    """
    # 1. Check REST API
    api_health = check_backend_health()
    if api_health.get("is_live"):
        return {
            "mode": f"Live REST API ({api_health['url']})",
            "is_live": True,
            "badge_color": "#10B981",
            "tier": "live",
            "icon": "🟢",
            "details": f"Connected to {api_health['url']}{api_health.get('endpoint', '')}"
        }

    # 2. Check SQLite DB
    for db_name in ["urbanshield.db", "data.db", "infrastructure.db"]:
        db_file = os.path.join(os.getcwd(), db_name)
        if os.path.exists(db_file):
            return {
                "mode": f"SQLite DB ({db_name})",
                "is_live": True,
                "badge_color": "#3B82F6",
                "tier": "sqlite",
                "icon": "🟡",
                "details": f"Connected to local SQLite database: {db_name}"
            }

    # 3. Fallback Mock Data
    return {
        "mode": "Calibrated Mock Fallback",
        "is_live": False,
        "badge_color": "#EA580C",
        "tier": "mock",
        "icon": "🟠",
        "details": "REST API / SQLite offline; serving calibrated municipal baseline telemetry"
    }

def get_zones_summary() -> List[Dict[str, Any]]:
    """
    Returns city zones with base attributes, infrastructure status, and live sensor readings.
    Attempts REST API first, then SQLite, then fallback mock data.
    """
    try:
        # Try REST API
        api_zones = fetch_api_zones()
        if api_zones is not None and len(api_zones) > 0:
            return api_zones

        # Try SQLite DB if present
        for db_name in ["urbanshield.db", "data.db", "infrastructure.db"]:
            db_file = os.path.join(os.getcwd(), db_name)
            if os.path.exists(db_file):
                import sqlite3
                try:
                    conn = sqlite3.connect(db_file)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    # Inspect tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    target_table = next((t for t in ["zones", "infrastructure", "city_zones", "assets"] if t in tables), None)
                    if target_table:
                        cursor.execute(f"SELECT * FROM {target_table}")
                        rows = cursor.fetchall()
                        if rows:
                            from services.api_client import normalize_zone_record
                            zones = [normalize_zone_record(dict(r)) for r in rows]
                            conn.close()
                            return zones
                    conn.close()
                except Exception as dbe:
                    print(f"[WARN] SQLite query failed on {db_name}: {dbe}. Falling back.")

        return MOCK_ZONES_SUMMARY
    except Exception as e:
        print(f"[ERROR] data_service.get_zones_summary failed: {e}. Falling back to mock data.")
        return MOCK_ZONES_SUMMARY

def get_available_resources() -> Dict[str, Any]:
    """
    Returns municipal resource pools (heavy pumps, response crews, budget).
    Attempts REST API first, then SQLite, then fallback mock data.
    """
    try:
        api_res = fetch_api_resources()
        if api_res is not None:
            return api_res

        # Try SQLite DB resources table
        for db_name in ["urbanshield.db", "data.db", "infrastructure.db"]:
            db_file = os.path.join(os.getcwd(), db_name)
            if os.path.exists(db_file):
                import sqlite3
                try:
                    conn = sqlite3.connect(db_file)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    if "resources" in tables:
                        cursor.execute("SELECT * FROM resources LIMIT 1")
                        row = cursor.fetchone()
                        if row:
                            r_dict = dict(row)
                            conn.close()
                            return {
                                "total_heavy_pumps": int(r_dict.get("total_heavy_pumps", 14)),
                                "deployed_heavy_pumps": int(r_dict.get("deployed_heavy_pumps", 9)),
                                "available_heavy_pumps": int(r_dict.get("available_heavy_pumps", 5)),
                                "total_rapid_crews": int(r_dict.get("total_rapid_crews", 10)),
                                "deployed_rapid_crews": int(r_dict.get("deployed_rapid_crews", 6)),
                                "available_rapid_crews": int(r_dict.get("available_rapid_crews", 4)),
                                "allocated_budget_usd": int(r_dict.get("allocated_budget_usd", 185000)),
                                "total_emergency_budget_usd": int(r_dict.get("total_emergency_budget_usd", 300000))
                            }
                    conn.close()
                except Exception as dbe:
                    print(f"[WARN] SQLite resource query failed: {dbe}")

        return MOCK_RESOURCES
    except Exception as e:
        print(f"[ERROR] data_service.get_available_resources failed: {e}. Falling back to mock resources.")
        return MOCK_RESOURCES

def get_zone_telemetry(zone_id: str) -> Dict[str, Any]:
    """
    Returns detailed sensor history & telemetry for a single zone.
    """
    try:
        zones = get_zones_summary()
        for z in zones:
            if z.get("zone_id") == zone_id:
                return z
        return zones[0] if zones else MOCK_ZONES_SUMMARY[0]
    except Exception as e:
        print(f"[ERROR] data_service.get_zone_telemetry failed: {e}")
        return MOCK_ZONES_SUMMARY[0]
