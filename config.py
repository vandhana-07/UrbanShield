"""
UrbanShield - Configuration & City Definitions
Central definitions for city zones, map coordinates, risk thresholds, and visual badges.
"""

# City Center Reference Coordinates (Simulated Metro City)
CITY_CENTER_LAT = 13.0827
CITY_CENTER_LNG = 80.2707
DEFAULT_MAP_ZOOM = 12

# 6 Core City Zones with Baseline Metadata
ZONES_CONFIG = {
    "Z-01": {
        "zone_id": "Z-01",
        "name": "South Lowland Basin",
        "lat": 13.0450,
        "lng": 80.2450,
        "population": 125000,
        "critical_assets": ["Metro General Hospital", "Substation Beta"],
        "base_drainage_capacity_pct": 35.0,  # Highly vulnerable
        "elevation_m": 4.2
    },
    "Z-02": {
        "zone_id": "Z-02",
        "name": "Riverfront Promenade",
        "lat": 13.0650,
        "lng": 80.2780,
        "population": 85000,
        "critical_assets": ["Central Water Pump Station", "Pedestrian Viaduct"],
        "base_drainage_capacity_pct": 45.0,
        "elevation_m": 6.8
    },
    "Z-03": {
        "zone_id": "Z-03",
        "name": "East Industrial Hub",
        "lat": 13.0300,
        "lng": 80.2600,
        "population": 62000,
        "critical_assets": ["Chemical Treatment Plant", "Freight Rail Junction"],
        "base_drainage_capacity_pct": 55.0,
        "elevation_m": 8.5
    },
    "Z-04": {
        "zone_id": "Z-04",
        "name": "Downtown Metro Core",
        "lat": 13.0827,
        "lng": 80.2707,
        "population": 210000,
        "critical_assets": ["City Hall", "Central Transit Terminal", "Emergency Ops Center"],
        "base_drainage_capacity_pct": 70.0,
        "elevation_m": 12.1
    },
    "Z-05": {
        "zone_id": "Z-05",
        "name": "Port Logistics Corridor",
        "lat": 13.1100,
        "lng": 80.2950,
        "population": 48000,
        "critical_assets": ["Container Terminal", "Coastal Flood Wall Gate 3"],
        "base_drainage_capacity_pct": 50.0,
        "elevation_m": 3.5
    },
    "Z-06": {
        "zone_id": "Z-06",
        "name": "North Hillside Ridge",
        "lat": 13.1250,
        "lng": 80.2300,
        "population": 92000,
        "critical_assets": ["Hillside Reservoir", "Telecom Master Tower"],
        "base_drainage_capacity_pct": 85.0,
        "elevation_m": 28.4
    }
}

# Risk Thresholds and Urgency Colors
SEVERITY_CONFIG = {
    "Critical": {
        "min_score": 0.75,
        "color": "#EF4444",
        "badge": "🚨 CRITICAL",
        "map_color": "red"
    },
    "High": {
        "min_score": 0.50,
        "color": "#F97316",
        "badge": "⚠️ HIGH",
        "map_color": "orange"
    },
    "Moderate": {
        "min_score": 0.25,
        "color": "#F59E0B",
        "badge": "⚡ MODERATE",
        "map_color": "beige"
    },
    "Low": {
        "min_score": 0.00,
        "color": "#10B981",
        "badge": "✅ LOW",
        "map_color": "green"
    }
}

def get_severity(risk_score: float) -> str:
    """Helper to classify risk score into severity level."""
    if risk_score >= 0.75:
        return "Critical"
    elif risk_score >= 0.50:
        return "High"
    elif risk_score >= 0.25:
        return "Moderate"
    return "Low"

def get_severity_color(severity: str) -> str:
    """Helper to retrieve hex color for severity level."""
    return SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["Low"])["color"]
