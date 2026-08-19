"""
UrbanShield - Main Application Entrypoint
Team Crusaders — Phoenix Hacks (Sustainable Cities & Infrastructure)
Member 1: UI / Frontend

This application connects the 6-stage UrbanShield pipeline:
SENSE -> PREDICT -> PRIORITIZE -> OPTIMIZE -> RECOMMEND -> SIMULATE
"""

import os
import streamlit as st

# Set Streamlit Page Configuration (Must be first Streamlit call)
st.set_page_config(
    page_title="UrbanShield | Municipal Flood & Infrastructure Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from services.data_service import get_zones_summary, get_data_source_status
from services.agent_service import get_pipeline_predictions, get_model_source_status
from services.api_client import get_configured_api_url, check_backend_health

# Defensive Session State Initialization
zones_list = get_zones_summary() or []
valid_ids = [z["zone_id"] for z in zones_list] if zones_list else ["Z-01"]

if "selected_zone_id" not in st.session_state or st.session_state["selected_zone_id"] not in valid_ids:
    try:
        preds = get_pipeline_predictions()
        if preds:
            top_zone = sorted(preds, key=lambda x: x.get("priority_rank", 99))[0]["zone_id"]
            st.session_state["selected_zone_id"] = top_zone if top_zone in valid_ids else valid_ids[0]
        else:
            st.session_state["selected_zone_id"] = valid_ids[0]
    except Exception:
        st.session_state["selected_zone_id"] = valid_ids[0]

# Import Presentation Components
from components.header import render_header
from components.kpi_cards import render_kpi_metrics
from components.map_view import render_city_map
from components.priority_table import render_priority_table
from components.charts import render_operational_charts
from components.recommendation_view import render_recommendations_view
from components.simulation_panel import render_simulation_panel

def main():
    # -------------------------------------------------------------------------
    # SIDEBAR: Context, System Health & Integration Status
    # -------------------------------------------------------------------------
    data_status = get_data_source_status()
    model_status = get_model_source_status()

    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
        st.markdown("### **UrbanShield OS**")
        st.caption("AI-Powered Municipal Resilience & Resource Optimization")
        
        st.markdown("---")
        st.markdown("#### 📡 System Status")
        st.success("🟢 Autonomous Agent Online")
        st.markdown(
            f"""
            <div style="background-color: #1E293B; border-radius: 6px; padding: 8px 10px; font-size: 0.8rem; margin-top: 4px;">
                <div style="margin-bottom: 4px;"><b>Data Layer:</b> <span style="color: {data_status['badge_color']}; font-weight: bold;">{data_status['mode']}</span></div>
                <div><b>AI/ML Engine:</b> <span style="color: {model_status['badge_color']}; font-weight: bold;">{model_status['mode']}</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # API Connection Configuration Expander (For Live Judge Demo)
        with st.expander("🔌 Backend API Connection", expanded=False):
            current_api_url = get_configured_api_url()
            new_api_url = st.text_input("Backend REST URL:", value=current_api_url, key="sidebar_api_url_input")
            if new_api_url != current_api_url:
                os.environ["URBANSHIELD_API_URL"] = new_api_url
                st.cache_data.clear()
                st.toast(f"API Target updated: {new_api_url}")
            
            if st.button("⚡ Test API Ping", use_container_width=True):
                st.cache_data.clear()
                health = check_backend_health()
                if health.get("is_live"):
                    st.success(f"✅ {health['message']} (HTTP {health.get('status_code', 200)})")
                else:
                    st.warning(f"⚠️ {health.get('message', 'Offline')} (Serving calibrated fallback data)")

        st.markdown("---")
        st.markdown("#### 🌧️ Weather Advisory")
        st.warning("⚠️ Monsoon Level 3: 68.5 mm/hr active precipitation in South Basin.")

        st.markdown("---")
        st.markdown("#### 👥 Team Crusaders Roster")
        st.markdown(
            """
            - **Vandhana.M:** Team Lead & Pitch
            - **Varsha.K:** AI/ML (RF + OR-Tools)
            - **Varshini.S:** Frontend / UI
            - **Varssini.A:** Data & QA (SQLite)
            """
        )
        st.caption("Track: Sustainable Cities & Infrastructure")

        st.markdown("---")
        if st.button("🔄 Refresh Telemetry Feeds", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # -------------------------------------------------------------------------
    # MAIN STAGE: Header & Navigation
    # -------------------------------------------------------------------------
    render_header()

    # Primary View Navigation Tabs
    tab_overview, tab_simulation = st.tabs([
        "🏙️ City Overview & Live Operations (MVP)",
        "🔄 What-If Simulation Sandbox (MVP)"
    ])

    # -------------------------------------------------------------------------
    # VIEW 1: City Overview & Live Operations
    # -------------------------------------------------------------------------
    with tab_overview:
        # 1. Top KPI Summary Metrics
        render_kpi_metrics()
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

        # 2. Main Grid: Map & Recommendations (Left) + Priority Table (Right)
        col_left, col_right = st.columns([1.1, 1.1], gap="medium")

        with col_left:
            st.markdown("##### 🗺️ City Flood Risk & Infrastructure Map")
            st.caption("Click any circle marker to focus decision recommendations and zone telemetry.")
            # Interactive Map View (Updates st.session_state.selected_zone_id on marker click)
            render_city_map(st.session_state["selected_zone_id"])
            
            st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
            # Explainable Recommendation Box for selected zone
            render_recommendations_view(st.session_state["selected_zone_id"])

        with col_right:
            # Ranked Urgency Table with Embedded Zone Deep-Dive Expander
            render_priority_table()

        st.markdown("---")

        # 3. Bottom Row: Focused Operational Plotly Charts
        st.markdown("##### 📈 Operational Telemetry & Resource Distribution")
        render_operational_charts()

    # -------------------------------------------------------------------------
    # VIEW 2: What-If Simulation Sandbox
    # -------------------------------------------------------------------------
    with tab_simulation:
        render_simulation_panel()

if __name__ == "__main__":
    main()
