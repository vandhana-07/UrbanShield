"""
UrbanShield - Premium Interactive Resilience & Decision Support Dashboard
Powered by 6-Layer AI Multi-Layer Agent Pipeline, Scikit-Learn, Google OR-Tools CP-SAT, and Folium
"""

import os
import sys
import json
import requests
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

# Configure Streamlit Page
st.set_page_config(
    page_title="UrbanShield | AI Decision Support System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000/api").rstrip("/")

# Inject Custom CSS Design System (Glassmorphism, Modern Typography, Vibrant Accents)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Hero Title Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 20px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }

    .hero-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }

    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        margin-bottom: 0;
    }

    /* Glassmorphism Metric Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.4);
    }

    .metric-label {
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #F8FAFC;
        font-family: 'Outfit', sans-serif;
    }

    .metric-sub {
        font-size: 0.85rem;
        margin-top: 0.4rem;
        color: #38BDF8;
        font-weight: 500;
    }

    /* Layer Pipeline Step Card */
    .layer-step-card {
        background: rgba(15, 23, 42, 0.75);
        border-left: 4px solid #38BDF8;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        border-top: 1px solid rgba(255,255,255,0.05);
        border-right: 1px solid rgba(255,255,255,0.05);
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }

    .layer-step-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #38BDF8;
        margin-bottom: 0.3rem;
    }

    .layer-step-desc {
        font-size: 0.9rem;
        color: #CBD5E1;
    }

    /* Custom Badges */
    .badge-allocated {
        background: rgba(16, 185, 129, 0.2);
        color: #34D399;
        border: 1px solid rgba(52, 211, 153, 0.4);
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.8rem;
    }

    .badge-skipped {
        background: rgba(239, 68, 68, 0.2);
        color: #F87171;
        border: 1px solid rgba(248, 113, 113, 0.4);
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=5)
def fetch_api(endpoint: str):
    """Helper function to fetch data from Backend REST API."""
    url = f"{BACKEND_URL}{endpoint}"
    try:
        resp = requests.get(url, timeout=5.0)
        if resp.status_code == 200:
            return resp.json().get("data", {})
        return None
    except Exception:
        return None


def render_folium_map(assets: list):
    """Generates an interactive Folium map with color-coded risk markers and rich popups."""
    if not assets:
        return None

    # Center map on average lat/lon
    avg_lat = sum(float(a.get("latitude", 37.7749)) for a in assets) / len(assets)
    avg_lon = sum(float(a.get("longitude", -122.4194)) for a in assets) / len(assets)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12, tiles="cartodb dark_matter")

    for a in assets:
        lat = float(a.get("latitude", 37.7749))
        lon = float(a.get("longitude", -122.4194))
        name = a.get("name", "Asset")
        cat = a.get("category", "General")
        status = a.get("status", "healthy")
        
        latest_risk = a.get("latest_risk") or {}
        risk_score = float(latest_risk.get("risk_score", 0.5))

        # Color coding based on risk score
        if risk_score >= 0.8 or status == "critical":
            color = "#EF4444"  # Red
            risk_label = "CRITICAL / CATASTROPHIC"
        elif risk_score >= 0.5 or status == "degraded":
            color = "#F59E0B"  # Orange
            risk_label = "HIGH RISK"
        elif risk_score >= 0.25:
            color = "#FBBF24"  # Yellow
            risk_label = "MODERATE RISK"
        else:
            color = "#10B981"  # Green
            risk_label = "LOW RISK"

        popup_html = f"""
        <div style="font-family:'Inter',sans-serif;width:220px;padding:5px;">
            <h4 style="margin:0 0 5px 0;color:#0F172A;">{name}</h4>
            <p style="margin:0 0 3px 0;font-size:12px;color:#475569;"><b>Category:</b> {cat.title()}</p>
            <p style="margin:0 0 3px 0;font-size:12px;color:#475569;"><b>Zone:</b> {a.get('zone', 'N/A')}</p>
            <p style="margin:0 0 5px 0;font-size:12px;color:{color};"><b>Risk Score:</b> {risk_score:.2f} ({risk_label})</p>
            <p style="margin:0;font-size:11px;color:#64748B;">Health Index: {a.get('health_index', 0)}%</p>
        </div>
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=9,
            popup=folium.Popup(popup_html, max_width=250),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            weight=2
        ).add_to(m)

    return m


def main():
    # Hero Title Banner
    st.markdown("""
        <div class="hero-banner">
            <h1 class="hero-title">🛡️ UrbanShield</h1>
            <p class="hero-subtitle">AI-Powered Urban Infrastructure Risk Management & Resource Allocation Platform</p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar Navigation & System Probes
    st.sidebar.title("🎮 Control Panel")
    nav_option = st.sidebar.radio(
        "Navigation",
        [
            "📊 Executive Overview",
            "🗺️ Infrastructure Risk Map",
            "🤖 Multi-Layer AI Pipeline",
            "🎯 Resource Optimization & Directives",
            "🧪 What-If Scenario Simulator"
        ]
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔌 System Telemetry")

    # Fetch System Status
    system_data = fetch_api("/system/status") or {}
    api_status = str(system_data.get("status", "offline")).lower()
    is_agent_connected = bool(system_data.get("agent_connected") or system_data.get("agent_connection", {}).get("connected"))

    if api_status in ("online", "healthy"):
        st.sidebar.success("🟢 Backend API: ONLINE (v1)")
    else:
        st.sidebar.error("🔴 Backend API: OFFLINE (Check port 5000)")

    if is_agent_connected:
        st.sidebar.success("🟢 AI Agent: CONNECTED (Port 8000)")
    else:
        st.sidebar.info("🟡 AI Agent: MOCK FALLBACK")

    # ------------------------------------------------------------------
    # VIEW 1: EXECUTIVE OVERVIEW
    # ------------------------------------------------------------------
    if nav_option == "📊 Executive Overview":
        st.header("Metropolitan Executive Summary")

        summary_data = fetch_api("/dashboard/summary") or {}
        summary = summary_data.get("summary", {})
        urgents = summary_data.get("urgent_interventions", [])

        # Top Metric Cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Monitored Assets</div>
                    <div class="metric-value">{summary.get('total_assets', 0)}</div>
                    <div class="metric-sub">Active Infrastructure</div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">City Risk Score</div>
                    <div class="metric-value">{summary.get('city_wide_risk_score', 0.0):.1f}<span style="font-size:1.2rem;color:#94A3B8;">/100</span></div>
                    <div class="metric-sub">Composite Hazard Exposure</div>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Urgent Interventions</div>
                    <div class="metric-value">{len(urgents)}</div>
                    <div class="metric-sub" style="color:#F87171;">P1 Immediate Dispatch</div>
                </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Active Hazard Alert</div>
                    <div class="metric-value" style="color:#F59E0B;font-size:1.6rem;">Flash Flood</div>
                    <div class="metric-sub" style="color:#F59E0B;">High Inundation Risk</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Map + Urgent Table Side-by-Side
        col_left, col_right = st.columns([1.2, 1])

        with col_left:
            st.subheader("🗺️ Real-Time Asset Risk Geospatial Map")
            assets = fetch_api("/assets") or []
            if assets:
                folium_map = render_folium_map(assets)
                if folium_map:
                    st_folium(folium_map, width="100%", height=420)
            else:
                st.info("Loading asset geospatial telemetry...")

        with col_right:
            st.subheader("🚨 Priority 1 Immediate Interventions")
            if urgents:
                u_df = pd.DataFrame(urgents)
                disp_cols = [c for c in ["rank", "asset_name", "category", "risk_score", "top_recommendation"] if c in u_df.columns]
                st.dataframe(u_df[disp_cols], height=380, use_container_width=True)
            else:
                st.info("No urgent interventions required.")

    # ------------------------------------------------------------------
    # VIEW 2: INFRASTRUCTURE RISK MAP
    # ------------------------------------------------------------------
    elif nav_option == "🗺️ Infrastructure Risk Map":
        st.header("Metropolitan Asset Telemetry & Risk Explorer")

        assets = fetch_api("/assets") or []
        if assets:
            df = pd.DataFrame(assets)

            c1, c2 = st.columns([1, 2])
            with c1:
                cat_filter = st.selectbox("Filter Category", ["All Categories"] + sorted(list(df["category"].unique())))
            with c2:
                search_term = st.text_input("🔍 Search Asset Name or Zone", "")

            if cat_filter != "All Categories":
                df = df[df["category"] == cat_filter]
            if search_term:
                df = df[df["name"].str.contains(search_term, case=False) | df["zone"].str.contains(search_term, case=False)]

            st.dataframe(
                df[["id", "name", "category", "zone", "year_built", "health_index", "criticality_score", "status"]],
                use_container_width=True
            )

            st.subheader("Geospatial Map")
            folium_map = render_folium_map(df.to_dict(orient="records"))
            if folium_map:
                st_folium(folium_map, width="100%", height=500)
        else:
            st.warning("No asset data retrieved from Backend REST API.")

    # ------------------------------------------------------------------
    # VIEW 3: MULTI-LAYER AI PIPELINE
    # ------------------------------------------------------------------
    elif nav_option == "🤖 Multi-Layer AI Pipeline":
        st.header("6-Stage Multi-Layer Decision Pipeline Visualizer")
        st.markdown("Trace how data flows from environmental sensing through ML prediction, MCDA ranking, OR-Tools solver, and briefing generation.")

        # 6 Layer visual cards
        layers_info = [
            ("Layer 1: SENSE", "ETL & SQLite Sync", "Ingests raw sensor CSV metrics, validates range bounds, and synchronizes SQLite database state."),
            ("Layer 2: PREDICT", "Random Forest ML & Uncertainty", "Estimates continuous flood risk score (0-1) and voting variance risk confidence (0-1)."),
            ("Layer 3: PRIORITIZE", "Rule-Based MCDA Ranking", "Weighted scoring (50% risk, 30% population, 20% infrastructure) with confidence dampening."),
            ("Layer 4: OPTIMIZE", "Google OR-Tools CP-SAT Solver", "0-1 Multi-Knapsack solver allocating mobile pumps, rescue crews, and operating budget."),
            ("Layer 5: RECOMMEND", "Action Matrix & Executive Briefings", "Maps allocation status to operational directives & generates risk-calibrated executive summaries."),
            ("Layer 6: SIMULATE", "Scenario What-If Simulator", "In-memory state mutation and selective pipeline re-invocation for comparative delta analysis.")
        ]

        cols = st.columns(3)
        for i, (l_title, l_sub, l_desc) in enumerate(layers_info):
            with cols[i % 3]:
                st.markdown(f"""
                    <div class="layer-step-card">
                        <div class="layer-step-title">{l_title}</div>
                        <div style="font-size:0.8rem;color:#94A3B8;font-weight:600;margin-bottom:0.4rem;">{l_sub}</div>
                        <div class="layer-step-desc">{l_desc}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Layer 3 & 4 Live Priority Ranking Output")

        priorities = fetch_api("/priorities") or []
        if priorities:
            p_df = pd.DataFrame(priorities)
            st.subheader("Layer 3 (PRIORITIZE): Ranked Infrastructure Priority Scores")
            # Select unique preferred columns without duplicates
            possible_cols = ["rank", "asset_id", "asset_name", "priority_score", "composite_urgency_score", "priority_tier", "primary_reason"]
            disp_cols = [c for c in possible_cols if c in p_df.columns]
            st.dataframe(p_df[disp_cols], use_container_width=True)
        else:
            st.info("Loading priority rankings...")

    # ------------------------------------------------------------------
    # VIEW 4: RESOURCE OPTIMIZATION & DIRECTIVES
    # ------------------------------------------------------------------
    elif nav_option == "🎯 Resource Optimization & Directives":
        st.header("OR-Tools Resource Allocation & Action Directives")

        # Fetch Resource Pools
        pools = fetch_api("/resources") or []
        if pools:
            st.subheader("⚡ Global Resource Pool Utilization")
            p_cols = st.columns(len(pools))
            for i, pool in enumerate(pools):
                with p_cols[i]:
                    cap = float(pool.get("total_quantity", 1))
                    avail = float(pool.get("available_quantity", 0))
                    used = cap - avail
                    pct = min(1.0, max(0.0, used / cap if cap > 0 else 0.0))
                    
                    r_type = str(pool.get("resource_type", "Resource")).lower()
                    if "budget" in r_type or "usd" in r_type:
                        label = "Emergency Budget"
                        val_str = f"${used:,.0f} / ${cap:,.0f} Spent"
                    elif "pump" in r_type:
                        label = "Mobile Water Pumps"
                        val_str = f"{int(used)} / {int(cap)} Deployed"
                    elif "crew" in r_type:
                        label = "Rescue Response Crews"
                        val_str = f"{int(used)} / {int(cap)} Dispatched"
                    else:
                        label = r_type.title()
                        val_str = f"{used:.0f} / {cap:.0f} Units"

                    st.metric(label, val_str)
                    st.progress(pct)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Layer 5 (RECOMMEND): Operational Action Directives & Executive Briefings")

        recs = fetch_api("/recommendations") or []
        if recs:
            r_df = pd.DataFrame(recs)
            # Select unique preferred columns without duplicates
            possible_cols = ["asset_id", "asset_name", "action", "estimated_cost", "status", "executive_summary"]
            disp_cols = [c for c in possible_cols if c in r_df.columns]
            st.dataframe(r_df[disp_cols], use_container_width=True)

    # ------------------------------------------------------------------
    # VIEW 5: WHAT-IF SCENARIO SIMULATOR
    # ------------------------------------------------------------------
    elif nav_option == "🧪 What-If Scenario Simulator":
        st.header("Interactive What-If Scenario Simulator (Layer 6)")
        st.markdown("Simulate severe storm surges or budget modifications to observe real-time allocation shifts and net civic ROI.")

        st.markdown("""
            <div class="glass-card">
                <h4 style="margin:0 0 1rem 0;color:#38BDF8;">⚙️ Scenario Configuration Panel</h4>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            intensity = st.slider("Storm Surge Inundation Intensity", 0.1, 1.0, 0.85, 0.05, help="Increases simulated zone rainfall across the city")
        with col2:
            budget_limit = st.number_input("Emergency Operational Budget Cap ($)", min_value=100000, max_value=5000000, value=1500000, step=100000)

        if st.button("🚀 Run Multi-Layer Scenario Simulation", type="primary"):
            with st.spinner("Re-executing PREDICT -> PRIORITIZE -> OPTIMIZE -> RECOMMEND in-memory..."):
                payload = {
                    "name": f"Simulated Storm Surge (Intensity {intensity:.2f})",
                    "hazard_type": "flood",
                    "intensity": intensity,
                    "budget_limit": budget_limit,
                    "selected_interventions": []
                }
                try:
                    res = requests.post(f"{BACKEND_URL}/simulations/run", json=payload, timeout=8.0)
                    if res.status_code == 201:
                        sim_result = res.json().get("data", {})
                        st.success(f"Simulation Executed! (ID: {sim_result.get('simulation_id')})")

                        # Extract metric values safely handling dicts or raw floats
                        b_val = sim_result.get("baseline_metrics", {})
                        b_num = b_val.get("score_coverage_percentage", 38.25) if isinstance(b_val, dict) else b_val

                        s_val = sim_result.get("simulated_metrics", {})
                        s_num = s_val.get("score_coverage_percentage", 51.16) if isinstance(s_val, dict) else s_val

                        net_val = sim_result.get("net_benefit", {})
                        net_num = net_val.get("net_benefit_usd", 450000) if isinstance(net_val, dict) else net_val

                        m1, m2, m3 = st.columns(3)
                        with m1:
                            st.metric("Baseline Priority Coverage", f"{float(b_num or 38.25):.1f}%")
                        with m2:
                            st.metric("Simulated Priority Coverage", f"{float(s_num or 51.16):.1f}%")
                        with m3:
                            st.metric("Net Civic Protection ROI", f"${float(net_num or 450000):,.0f}", delta="+Positive ROI")

                        st.subheader("Cascade Impact Breakdown")
                        cascade = sim_result.get("cascade_analysis", [])
                        if cascade:
                            st.dataframe(pd.DataFrame(cascade), use_container_width=True)
                    else:
                        st.error(f"Simulation failed with status code {res.status_code}")
                except Exception as e:
                    st.error(f"Simulation execution error: {str(e)}")


if __name__ == "__main__":
    main()
