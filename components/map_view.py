"""
UrbanShield - Interactive Folium Map Component
Renders lightweight CircleMarkers colored by risk severity with direct zone_id payload click-to-select sync.
"""

import re
import streamlit as st
import folium
from streamlit_folium import st_folium
from config import CITY_CENTER_LAT, CITY_CENTER_LNG, DEFAULT_MAP_ZOOM, SEVERITY_CONFIG
from services.data_service import get_zones_summary
from services.agent_service import get_pipeline_predictions

def extract_zone_id_from_payload(map_data: dict, valid_zones: list) -> str:
    """
    Extracts exact zone_id directly from the click tooltip or popup payload.
    Falls back to nearest coordinate proximity matching if payload string is absent.
    """
    if not map_data:
        return None

    valid_zone_ids = {z["zone_id"] for z in valid_zones}

    # 1. Check tooltip payload
    tooltip_str = map_data.get("last_object_clicked_tooltip")
    if tooltip_str:
        match = re.search(r"(Z-\d+)", str(tooltip_str))
        if match and match.group(1) in valid_zone_ids:
            return match.group(1)

    # 2. Check popup payload
    popup_str = map_data.get("last_object_clicked_popup")
    if popup_str:
        match = re.search(r"(Z-\d+)", str(popup_str))
        if match and match.group(1) in valid_zone_ids:
            return match.group(1)

    # 3. Coordinate Proximity Fallback
    clicked_obj = map_data.get("last_object_clicked")
    if isinstance(clicked_obj, dict) and "lat" in clicked_obj and "lng" in clicked_obj:
        c_lat, c_lng = float(clicked_obj["lat"]), float(clicked_obj["lng"])
        best_zone = None
        min_dist = float("inf")
        for z in valid_zones:
            dist = (float(z.get("lat", 0)) - c_lat) ** 2 + (float(z.get("lng", 0)) - c_lng) ** 2
            if dist < min_dist:
                min_dist = dist
                best_zone = z.get("zone_id")
        if min_dist < 0.005:  # within close radius of marker
            return best_zone

    return None

def render_city_map(selected_zone_id: str = None) -> str:
    """
    Renders an interactive Folium map with zone CircleMarkers.
    Extracts zone_id directly from the click payload and synchronizes st.session_state.
    Handles empty zone feeds gracefully.
    """
    if not selected_zone_id:
        selected_zone_id = st.session_state.get("selected_zone_id", "Z-01")

    try:
        zones = get_zones_summary() or []
        predictions = {p["zone_id"]: p for p in (get_pipeline_predictions() or [])}

        # Create base Folium Map centered on simulated city
        m = folium.Map(
            location=[CITY_CENTER_LAT, CITY_CENTER_LNG],
            zoom_start=DEFAULT_MAP_ZOOM,
            tiles="CartoDB dark_matter",
            control_scale=True
        )

        if not zones:
            st.info("ℹ️ No geospatial zone coordinates loaded. Displaying baseline city sector map.")
            st_folium(m, width="100%", height=300)
            return selected_zone_id

        # Add CircleMarker per zone
        for zone in zones:
            z_id = zone.get("zone_id", "Z-XX")
            pred = predictions.get(z_id, {"risk_score": 0.0, "severity": "Low"})
            severity = pred.get("severity", "Low")
            risk_score = pred.get("risk_score", 0.0)
            
            hex_color = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["Low"])["color"]
            is_selected = (z_id == selected_zone_id)

            # HTML formatted popup tooltip
            popup_html = f"""
            <div style="font-family: sans-serif; min-width: 190px; color: #0F172A;">
                <div style="font-weight: bold; font-size: 14px; border-bottom: 2px solid {hex_color}; padding-bottom: 3px; margin-bottom: 6px;">
                    [{z_id}] {zone.get('name', z_id)}
                </div>
                <div><b>Risk Score:</b> <span style="color:{hex_color}; font-weight:bold;">{risk_score:.2f} ({severity})</span></div>
                <div><b>Rainfall:</b> {zone.get('rainfall_mm_per_hr', 0)} mm/hr</div>
                <div><b>Drainage:</b> {zone.get('drainage_capacity_pct', 0)}% Cap</div>
                <div><b>Population:</b> {zone.get('population', 0):,}</div>
                <div style="margin-top: 4px; font-size: 11px; color: #475569;">
                    <b>Key Asset:</b> {zone.get('critical_assets', ['N/A'])[0]}
                </div>
            </div>
            """

            radius = 24 if is_selected else 16

            folium.CircleMarker(
                location=[zone.get("lat", CITY_CENTER_LAT), zone.get("lng", CITY_CENTER_LNG)],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=f"[{z_id}] {zone.get('name', z_id)} — Risk: {risk_score:.2f} ({severity})",
                color="#FFFFFF" if is_selected else hex_color,
                weight=4 if is_selected else 2,
                fill=True,
                fill_color=hex_color,
                fill_opacity=0.85 if is_selected else 0.65
            ).add_to(m)

        # Display map in Streamlit container with tooltip & popup return tracking
        map_data = st_folium(
            m,
            width="100%",
            height=400,
            returned_objects=["last_object_clicked", "last_object_clicked_tooltip", "last_object_clicked_popup"]
        )

        # Extract zone_id directly from the click payload
        clicked_zone_id = extract_zone_id_from_payload(map_data, zones)
        if clicked_zone_id and clicked_zone_id != st.session_state.get("selected_zone_id"):
            st.session_state["selected_zone_id"] = clicked_zone_id
            st.rerun()

        return st.session_state.get("selected_zone_id", selected_zone_id)

    except Exception as e:
        st.error(f"⚠️ Error rendering live map: {e}")
        return selected_zone_id
