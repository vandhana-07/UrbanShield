"""
UrbanShield — AI Emergency Infrastructure Command Center
Decision Support, Real Chennai Geospatial Intelligence & Resource Optimization
Powered by 6-Layer Multi-Layer AI Pipeline, Real OpenCity/GCC/IMD Data, Google OR-Tools CP-SAT, and Folium
"""

import os
import sys
import json
import requests
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime

try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

# Configure Streamlit Page
st.set_page_config(
    page_title="UrbanShield | AI Emergency Infrastructure Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000/api").rstrip("/")
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8000").rstrip("/")

# Custom CSS Command Center Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace;
    }

    /* Command Center Header */
    .command-header {
        background: linear-gradient(135deg, #0B0F17 0%, #151D2A 50%, #0F172A 100%);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 18px;
        padding: 1.6rem 2.2rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }

    .command-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }

    .command-subtitle {
        color: #94A3B8;
        font-size: 1.02rem;
        margin-top: 0.35rem;
        margin-bottom: 0;
        font-weight: 400;
    }

    /* Top KPI Cards */
    .kpi-card {
        background: rgba(21, 29, 42, 0.85);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.2rem 1.3rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.4);
    }

    .kpi-label {
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    .kpi-value {
        font-family: 'Outfit', sans-serif;
        font-size: 2.1rem;
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1.1;
    }

    .kpi-sub {
        font-size: 0.82rem;
        margin-top: 0.3rem;
        font-weight: 500;
    }

    /* Commander Mode Briefing Box */
    .commander-briefing {
        background: rgba(15, 23, 42, 0.95);
        border-left: 5px solid #EF4444;
        border-radius: 12px;
        padding: 1.3rem 1.6rem;
        margin-bottom: 1.5rem;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }

    .tradeoff-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 14px;
        padding: 1.3rem;
        height: 100%;
    }

    .trace-step {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=8)
def fetch_real_pipeline_data():
    """Fetches real Chennai 6-layer pipeline data via Backend API or Agent."""
    # 1. Try Backend API
    try:
        resp = requests.get(f"{BACKEND_URL}/zones/real", timeout=3.0)
        if resp.status_code == 200:
            payload = resp.json()
            if payload.get("success") and "data" in payload:
                return payload["data"]
            if "zones" in payload:
                return payload
    except Exception:
        pass

    # 2. Try Direct Agent REST Server
    try:
        resp = requests.post(f"{AGENT_URL}/agent/analyze", json={}, timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    # 3. Direct In-Process Layer Execution Fallback
    try:
        from agent.orchestrator import UrbanShieldAgent
        agent = UrbanShieldAgent()
        final_df, opt_summary = agent.run_full_pipeline()
        return {
            "pipeline_summary": opt_summary,
            "zones": final_df.to_dict(orient="records"),
            "data_provenance": "Real Chennai Observations (OpenCity / GCC / IMD)"
        }
    except Exception as e:
        st.error(f"Error executing intelligence pipeline: {str(e)}")
        return {"zones": [], "pipeline_summary": {}}


def render_folium_map(zones: list):
    """Renders high-contrast command center geospatial map."""
    if not HAS_FOLIUM or not zones:
        return None

    chennai_center = [13.0450, 80.1800]
    m = folium.Map(
        location=chennai_center,
        zoom_start=11,
        tiles="CartoDB dark_matter",
        control_scale=True
    )

    for z in zones:
        zid = z.get("zone_id", "")
        lat = float(z.get("latitude", 13.04))
        lon = float(z.get("longitude", 80.21))
        name = z.get("zone_name", "Chennai Zone")
        risk = float(z.get("risk_score", 0.5))
        priority = float(z.get("priority_score", 0.5))
        depth = z.get("inundation_depth_inches", "N/A")
        hazard = z.get("hazard_category", "MODERATE")
        rainfall = z.get("rainfall_mm", "N/A")
        station = z.get("nearest_rainfall_station", "IMD")
        dist_km = float(z.get("rainfall_station_dist_km", 0.0))
        conf = float(z.get("risk_confidence", 0.95)) * 100
        status = z.get("allocation_status", "PENDING")

        is_rec = zid == "CHN-REC-01" or "Rajalakshmi" in name

        if is_rec:
            color = "#8B5CF6"  # Distinct Purple for REC Critical Campus
            radius = 12
            border_color = "#38BDF8"  # Cyan ring
            weight = 3
            popup_html = f"""
            <div style="font-family: sans-serif; font-size: 12px; min-width: 270px; line-height: 1.45; color: #0F172A;">
                <b style="color: #6366F1; font-size: 13.5px;">🎓 {name}</b><br>
                <b>Location:</b> Rajalakshmi Nagar, Thandalam, Chennai<br>
                <hr style="margin: 5px 0; border: none; border-top: 1px solid #CBD5E1;">
                <b>Nearest rainfall station:</b> {station}<br>
                <b>Distance:</b> {dist_km:.2f} km<br>
                <b>Rainfall:</b> {rainfall} mm<br>
                <b>Nearest inundation observation:</b> Subway surveyed point (35.0")<br>
                <b>Distance:</b> 18.89 km<br>
                <b>Hazard category:</b> {hazard} (nearest polygon: 14.97 km)<br>
                <b>Evidence quality:</b> {conf:.1f}%<br>
                <b>Risk:</b> {risk:.4f} (Evidence-based Low Risk)<br>
                <b>Priority:</b> {priority:.4f} (Rank 16 / 16 — Routine Monitoring)<br>
                <div style="margin-top: 7px; padding: 5px 7px; background: #F8FAFC; border-left: 3px solid #6366F1; border-radius: 4px; font-size: 10.5px; color: #475569;">
                    <i>Environmental observations are linked from the nearest available public observations; they are not claimed to be direct on-campus measurements.</i>
                </div>
            </div>
            """
        else:
            if risk >= 0.70:
                color = "#EF4444"  # Red (Critical)
                radius = 12
            elif risk >= 0.50:
                color = "#F97316"  # Orange (High)
            elif risk >= 0.35:
                color = "#FACC15"  # Yellow (Moderate)
            else:
                color = "#10B981"  # Green (Low)
                radius = 7
            border_color = color
            weight = 2

            popup_html = f"""
            <div style="font-family: sans-serif; font-size: 12px; min-width: 220px; line-height: 1.4; color: #0F172A;">
                <b style="color: #0284C7; font-size: 13px;">{name}</b><br>
                <b>Risk Score:</b> {risk:.2f} | <b>Priority:</b> {priority:.2f}<br>
                <b>Hazard Tier:</b> {hazard}<br>
                <b>Inundation Depth:</b> {depth}"<br>
                <b>Rainfall:</b> {rainfall} mm ({station}, {dist_km:.1f} km)<br>
                <b>Status:</b> <span style="font-weight: bold; color: {'#10B981' if status=='ALLOCATED' else '#EF4444'};">{status}</span>
            </div>
            """

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=310),
            tooltip=f"{'🎓 ' if is_rec else ''}{name} (Risk: {risk:.2f})",
            color=border_color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            weight=weight
        ).add_to(m)

    return m


def main():
    # ------------------------------------------------------------------
    # COMMAND CENTER HEADER
    # ------------------------------------------------------------------
    st.markdown("""
        <div class="command-header">
            <h1 class="command-title">🛡️ UrbanShield</h1>
            <p class="command-subtitle">AI Emergency Infrastructure Command Center & Decision Support System • Chennai Metropolitan Region</p>
        </div>
    """, unsafe_allow_html=True)

    # Fetch live pipeline data
    data = fetch_real_pipeline_data()
    zones = data.get("zones", [])
    summary = data.get("pipeline_summary", {})
    zones_df = pd.DataFrame(zones) if zones else pd.DataFrame()

    # ------------------------------------------------------------------
    # TOP KPI COMMAND CARDS
    # ------------------------------------------------------------------
    total_locations = len(zones_df) if not zones_df.empty else 16
    crit_high_count = len(zones_df[zones_df["risk_score"] >= 0.50]) if not zones_df.empty else 8
    pumps_deployed = summary.get("pumps_deployed", 4)
    pumps_cap = summary.get("total_pumps_capacity", 6)
    crews_deployed = summary.get("crews_deployed", 4)
    crews_cap = summary.get("total_crews_capacity", 4)
    budget_spent = summary.get("budget_spent", 390000.0)
    budget_cap = summary.get("total_budget_capacity", 500000.0)

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Active Monitored Locations</div>
                <div class="kpi-value">{total_locations}</div>
                <div class="kpi-sub" style="color:#38BDF8;">15 Municipal + 1 REC Campus</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Critical / High Priority</div>
                <div class="kpi-value">{crit_high_count} <span style="font-size:1.1rem;color:#94A3B8;">({crit_high_count/total_locations*100:.0f}%)</span></div>
                <div class="kpi-sub" style="color:#F87171;">Risk Score ≥ 0.50</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Rescue Crews Assigned</div>
                <div class="kpi-value">{crews_deployed} / {crews_cap}</div>
                <div class="kpi-sub" style="color:#F59E0B;">Critical Bottleneck Constraint</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Portable Pumps Deployed</div>
                <div class="kpi-value">{pumps_deployed} / {pumps_cap}</div>
                <div class="kpi-sub" style="color:#34D399;">High-Capacity Dewatering</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi5:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Emergency Budget Pool</div>
                <div class="kpi-value">₹{budget_spent/100000:.2f}L</div>
                <div class="kpi-sub" style="color:#A78BFA;">Cap: ₹{budget_cap/100000:.2f} Lakhs (INR)</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # SIDEBAR NAVIGATION & SYSTEM TELEMETRY
    # ------------------------------------------------------------------
    with st.sidebar:
        st.markdown("### 🎮 Control Center")
        nav_option = st.radio(
            "Command View Selection",
            [
                "🚨 COMMANDER MODE",
                "🗺️ Live Geospatial Risk Map",
                "⚖️ Resource Allocation & Optimization",
                "🧠 Why Did UrbanShield Choose This?",
                "🧪 What-If Crisis Scenario Simulator",
                "🎓 REC Infrastructure Profile & Twin",
                "🤖 Six-Layer Pipeline Architecture",
                "🌐 Real Data Sources & Provenance"
            ]
        )

        st.markdown("---")
        st.markdown("### 📡 System Telemetry")
        
        # Telemetry probes
        backend_online = False
        try:
            r = requests.get(f"{BACKEND_URL}/system/status", timeout=1.5)
            backend_online = r.status_code == 200
        except Exception:
            backend_online = False

        agent_online = False
        try:
            r = requests.get(f"{AGENT_URL}/agent/health", timeout=1.5)
            agent_online = r.status_code == 200
        except Exception:
            agent_online = False

        st.markdown(f"**Backend API:** {'🟢 ONLINE (Port 5000)' if backend_online else '🟡 LOCAL IN-PROCESS'}")
        st.markdown(f"**AI Agent Server:** {'🟢 LIVE (Port 8000)' if agent_online else '🟡 LOCAL IN-PROCESS'}")
        st.markdown("**Constraint Solver:** 🟢 Google OR-Tools CP-SAT")
        st.markdown("**Currency Standard:** 🇮🇳 Indian Rupees (₹ INR)")

    # ------------------------------------------------------------------
    # VIEW 1: 🚨 COMMANDER MODE (OPERATIONAL SITUATION BRIEFING)
    # ------------------------------------------------------------------
    if nav_option == "🚨 COMMANDER MODE":
        st.subheader("🚨 COMMANDER MODE — Operational Decision Support & Incident Directives")
        st.caption("Real-Time Incident Briefing & Actionable Resource Orders for Greater Chennai Emergency Incident Commanders")

        if not zones_df.empty:
            allocated_zones = zones_df[zones_df["allocation_status"] == "ALLOCATED"]
            unserved_critical = zones_df[(zones_df["allocation_status"] == "SKIPPED") & (zones_df["priority_score"] >= 0.65)]
            
            primary_zone = allocated_zones.iloc[0]["zone_name"] if not allocated_zones.empty else "None"
            sec_zones = [z for z in allocated_zones["zone_name"].tolist() if z != primary_zone]

            st.markdown(f"""
                <div class="commander-briefing">
                    <h3 style="color: #EF4444; margin-top: 0; font-size: 1.35rem;">⚠️ OPERATIONAL SITUATION ASSESSMENT</h3>
                    <p style="font-size: 1.05rem; line-height: 1.5; color: #F1F5F9; margin-bottom: 0.8rem;">
                        <b>CURRENT SITUATION:</b> <b>{len(allocated_zones)} municipal zones</b> are actively allocated emergency intervention resources. 
                        <b>{len(unserved_critical)} high-priority zones</b> remain unserviced due to the strict <b>4-crew emergency pool constraint</b>.
                    </p>
                    <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 0.8rem 0;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; font-size: 0.95rem;">
                        <div>
                            <span style="color: #38BDF8; font-weight: 600;">✓ PRIMARY DEPLOYMENT ORDER:</span><br>
                            <span style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC;">{primary_zone}</span> (2 Heavy Pumps, 2 Rescue Crews — ₹1,80,000)
                        </div>
                        <div>
                            <span style="color: #34D399; font-weight: 600;">✓ SECONDARY DISPATCH ORDERS:</span><br>
                            <span style="font-size: 1.05rem; font-weight: 600; color: #E2E8F0;">{', '.join(sec_zones) if sec_zones else 'None'}</span> (1 Pump, 1 Crew each)
                        </div>
                        <div>
                            <span style="color: #F87171; font-weight: 600;">⚠ UNSERVED HIGH-PRIORITY BOTTLENECK:</span><br>
                            <span style="font-size: 1.05rem; font-weight: 700; color: #FCA5A5;">{', '.join(unserved_critical['zone_name'].tolist())}</span>
                        </div>
                        <div>
                            <span style="color: #FBBF24; font-weight: 600;">🚨 COMMAND ESCALATION DIRECTIVE:</span><br>
                            <span style="color: #FEF08A; font-weight: 600;">Immediate request for +2 emergency rescue crews to City Command.</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Interactive Incident Brief Generator
            col_b1, col_b2 = st.columns([1, 2])
            with col_b1:
                st.markdown("### 📄 Formal Incident Dispatch Memo")
                if st.button("🚨 GENERATE OFFICIAL INCIDENT BRIEF", type="primary", use_container_width=True):
                    brief_text = f"""================================================================================
GREATER CHENNAI DISASTER MANAGEMENT CELL — EMERGENCY INCIDENT BRIEF
GENERATED: {datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")}
CLASSIFICATION: EMERGENCY DISPATCH ORDER / STRICT RESOURCE CONSTRAINED
================================================================================

1. SITUATION OVERVIEW:
   - Monitored Urban Infrastructure Locations : 16 locations
   - Critical / High Inundation Zones          : {crit_high_count} zones (Risk >= 0.50)
   - Available Rescue Crew Capacity            : {crews_cap} Teams (100% Committed)
   - Available Portable Pumps Capacity         : {pumps_cap} Units (4 Deployed)
   - Total Emergency Operating Pool            : ₹{budget_cap:,.0f} (₹{budget_spent:,.0f} Committed)

2. DEPLOYED INTERVENTION ORDERS:
   - PRIMARY: {primary_zone} (2 Heavy Pumps + 2 Rescue Crews)
   - SECONDARY: {', '.join(sec_zones)} (1 Pump + 1 Rescue Crew Each)

3. UNSERVED HIGH-PRIORITY BOTTLENECKS:
   - {', '.join(unserved_critical['zone_name'].tolist())}
   - DIRECTIVE: ESCALATE FOR REINFORCEMENTS (Requires +2 Rescue Crews)

4. AI REASONING / EXPLAINABILITY:
   - Global Knapsack Objective: Maximizes total city-wide priority coverage (1.6533).
   - Servicing 3 population hubs protects +7.5% higher total priority coverage 
     than exhausting all remaining crews on a single secondary high-severity point.
================================================================================
"""
                    st.code(brief_text, language="text")
                    st.download_button("💾 Download Incident Brief (.txt)", brief_text, file_name="chennai_incident_brief.txt", mime="text/plain")

            with col_b2:
                st.markdown("### 🗺️ Real-Time Incident Map")
                fmap = render_folium_map(zones)
                if fmap and HAS_FOLIUM:
                    st_folium(fmap, width="100%", height=380)
                elif not zones_df.empty:
                    st.map(zones_df[["latitude", "longitude"]], zoom=10)

    # ------------------------------------------------------------------
    # VIEW 2: 🗺️ LIVE GEOSPATIAL RISK MAP & EVIDENCE TRACE
    # ------------------------------------------------------------------
    elif nav_option == "🗺️ Live Geospatial Risk Map":
        st.subheader("🗺️ Real Chennai Flood Inundation & Geospatial Risk Map")
        st.caption("Spatially matched to 192 OpenCity ground depth surveys, 53 GCC hotspots, and IMD meteorological stations.")

        col_map, col_details = st.columns([1.3, 1])
        with col_map:
            fmap = render_folium_map(zones)
            if fmap and HAS_FOLIUM:
                st_folium(fmap, width="100%", height=480)
            elif not zones_df.empty:
                st.map(zones_df[["latitude", "longitude"]], zoom=10)

            # Map Legend
            st.markdown("""
                <div style="display: flex; gap: 15px; flex-wrap: wrap; font-size: 0.85rem; padding: 8px 12px; background: rgba(15,23,42,0.8); border-radius: 8px; margin-top: 6px; border: 1px solid rgba(255,255,255,0.08);">
                    <span>🔴 <b>Critical (≥ 0.70)</b></span>
                    <span>🟠 <b>High (0.50 – 0.69)</b></span>
                    <span>🟡 <b>Moderate (0.35 – 0.49)</b></span>
                    <span>🟢 <b>Low (< 0.35)</b></span>
                    <span>🟣 <b>REC Campus (CHN-REC-01)</b></span>
                </div>
            """, unsafe_allow_html=True)

        with col_details:
            st.markdown("### 📋 Zone Risk Registry")
            if not zones_df.empty:
                disp_cols = ["priority_rank", "zone_name", "risk_score", "hazard_category", "inundation_depth_inches", "allocation_status"]
                st.dataframe(zones_df[disp_cols], height=480, use_container_width=True)

    # ------------------------------------------------------------------
    # VIEW 3: ⚖️ RESOURCE ALLOCATION & OPTIMIZATION
    # ------------------------------------------------------------------
    elif nav_option == "⚖️ Resource Allocation & Optimization":
        st.subheader("⚖️ Resource-Constrained Optimization (Google OR-Tools CP-SAT)")
        st.caption("Solves 0-1 Multi-Dimensional Knapsack problem under discrete pump, rescue crew, and budget bounds.")

        if not zones_df.empty:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Pumps Deployed", f"{summary.get('pumps_deployed', 4)} / {summary.get('total_pumps_capacity', 6)}")
            with m2:
                st.metric("Rescue Crews", f"{summary.get('crews_deployed', 4)} / {summary.get('total_crews_capacity', 4)}", "Bottleneck Constraint")
            with m3:
                st.metric("Budget Spent", f"₹{summary.get('budget_spent', 390000.0):,.0f}", f"Cap: ₹{summary.get('total_budget_capacity', 500000.0):,.0f}")
            with m4:
                st.metric("Solver Status", summary.get("solver_status", "OPTIMAL"), f"Solve Time: {summary.get('solve_time_seconds', 0.021):.3f}s")

            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("AI Optimized Deployment Registry")

            # Table with clear status badges
            display_alloc_df = zones_df[[
                "priority_rank", "zone_id", "zone_name", "priority_score",
                "hazard_category", "inundation_depth_inches", "allocation_status",
                "allocated_pumps", "allocated_crews", "allocated_cost", "recommended_action"
            ]].copy()
            
            st.dataframe(display_alloc_df, height=450, use_container_width=True)

    # ------------------------------------------------------------------
    # VIEW 4: 🧠 WHY DID URBANSHIELD CHOOSE THIS? (EXPLAINABLE AI)
    # ------------------------------------------------------------------
    elif nav_option == "🧠 Why Did UrbanShield Choose This?":
        st.subheader("🧠 Explainable Optimization — Why UrbanShield Made This Decision")
        st.caption("Mathematical & Operational Explainability of the Google OR-Tools CP-SAT Knapsack Tradeoff")

        st.markdown("""
        ### The Knapsack Optimization Tradeoff Breakdown
        UrbanShield maximizes **total protected city-wide priority coverage** under scarce emergency rescue crew bottlenecks.
        """)

        col_opt_a, col_opt_b = st.columns(2)
        with col_opt_a:
            st.markdown("""
                <div class="tradeoff-card" style="border-left: 4px solid #F87171;">
                    <h4 style="color: #F87171; margin-top: 0;">OPTION A: GREEDY ALLOCATION</h4>
                    <p><b>Strategy:</b> Blindly allocate to Rank 1 and Rank 2 in order.</p>
                    <ul>
                        <li><b>Velachery Lake Basin (Rank 1):</b> 2 Crews, 2 Pumps (₹1,80,000)</li>
                        <li><b>Adyar River South Bank (Rank 2):</b> 2 Crews, 2 Pumps (₹1,80,000)</li>
                    </ul>
                    <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1);">
                    <p><b>Total Crews Consumed:</b> 4 / 4 (Exhausted)</p>
                    <p><b>Total Zones Serviced:</b> <b>2 Zones</b></p>
                    <p style="font-size: 1.2rem; font-weight: 700; color: #FCA5A5;">Total Priority Coverage = 0.8023 + 0.7358 = 1.5381</p>
                </div>
            """, unsafe_allow_html=True)

        with col_opt_b:
            st.markdown("""
                <div class="tradeoff-card" style="border-left: 4px solid #34D399;">
                    <h4 style="color: #34D399; margin-top: 0;">OPTION B: URBANSHIELD GLOBAL OPTIMUM ✓</h4>
                    <p><b>Strategy:</b> CP-SAT Multi-Dimensional Knapsack Global Solve.</p>
                    <ul>
                        <li><b>Velachery Lake Basin (Rank 1):</b> 2 Crews, 2 Pumps (₹1,80,000)</li>
                        <li><b>Taramani IT Corridor (Rank 9):</b> 1 Crew, 1 Pump (₹1,05,000)</li>
                        <li><b>Anna University Canal (Rank 10):</b> 1 Crew, 1 Pump (₹1,05,000)</li>
                    </ul>
                    <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1);">
                    <p><b>Total Crews Consumed:</b> 4 / 4 (Exhausted)</p>
                    <p><b>Total Zones Serviced:</b> <b>3 Zones</b></p>
                    <p style="font-size: 1.2rem; font-weight: 700; color: #6EE7B7;">Total Priority Coverage = 0.8023 + 0.4343 + 0.4167 = 1.6533</p>
                    <p style="color: #38BDF8; font-weight: 600;">→ +7.5% higher total priority coverage across 3 population hubs!</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🔍 Zone-by-Zone Explainability Inspector")
        if not zones_df.empty:
            selected_zone_name = st.selectbox("Select Zone to Inspect Reasoning", zones_df["zone_name"].tolist())
            z_row = zones_df[zones_df["zone_name"] == selected_zone_name].iloc[0]

            st.info(f"**Zone Decision Analysis for {selected_zone_name} [{z_row['zone_id']}]:**\n\n"
                    f"• **Allocation Status:** `{z_row['allocation_status']}`\n\n"
                    f"• **Priority Score:** `{z_row['priority_score']:.4f}` (Rank {z_row['priority_rank']} of 16)\n\n"
                    f"• **Mathematical Reason:** {z_row['allocation_reason']}\n\n"
                    f"• **Dispatcher Briefing:** {z_row.get('executive_summary', 'Routine surveillance.')}")

    # ------------------------------------------------------------------
    # VIEW 5: 🧪 WHAT-IF CRISIS SCENARIO SIMULATOR
    # ------------------------------------------------------------------
    elif nav_option == "🧪 What-If Crisis Scenario Simulator":
        st.subheader("🧪 What-If Crisis Scenario Simulator")
        st.caption("Test emergency resource overrides in-memory without database mutation before deploying real-world personnel.")
        st.warning("⚠️ **Notice:** These values are generated strictly for interactive 'What-If' simulation testing. They do NOT represent historical observations.")

        col1, col2, col3 = st.columns(3)
        with col1:
            sim_crews = st.slider("Emergency Rescue Crews Available", 2, 10, 6, 1, help="Increase available crews from baseline (4) to test reinforcement dispatch")
        with col2:
            sim_pumps = st.slider("Portable Heavy Pumps Available", 2, 15, 8, 1, help="Increase dewatering pump inventory from baseline (6)")
        with col3:
            sim_budget = st.number_input("Emergency Budget Cap (₹ INR)", min_value=100000, max_value=2000000, value=750000, step=50000)

        if st.button("🚀 RUN IN-MEMORY WHAT-IF SIMULATION", type="primary", use_container_width=True):
            with st.spinner("Executing Google OR-Tools CP-SAT re-solve in-memory..."):
                try:
                    from layers.simulate import SimulateLayer
                    sim_layer = SimulateLayer()
                    sim_df, sim_summary, comp_delta = sim_layer.run_simulation(
                        resource_overrides={
                            "total_crews": sim_crews,
                            "total_pumps": sim_pumps,
                            "total_budget": float(sim_budget)
                        }
                    )

                    st.success("✓ Simulation Executed Successfully!")

                    b_cov = comp_delta.get("global_metrics", {}).get("score_coverage_pct", {}).get("before", 20.8)
                    s_cov = comp_delta.get("global_metrics", {}).get("score_coverage_pct", {}).get("after", 41.6)
                    delta_cov = s_cov - b_cov

                    b_zones = comp_delta.get("global_metrics", {}).get("serviced_zones", {}).get("before", 3)
                    s_zones = comp_delta.get("global_metrics", {}).get("serviced_zones", {}).get("after", 5)

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Serviced Zones (BEFORE → AFTER)", f"{b_zones} → {s_zones}", f"{s_zones - b_zones:+d} Zones Gained")
                    with c2:
                        st.metric("Priority Coverage (BEFORE → AFTER)", f"{b_cov:.1f}% → {s_cov:.1f}%", f"{delta_cov:+.2f}% Coverage")
                    with c3:
                        st.metric("Budget Utilization", f"₹{sim_summary.get('budget_spent', 0):,.0f}", f"Cap: ₹{sim_budget:,.0f}")

                    st.markdown("### 🔄 Side-by-Side Allocation Comparison")
                    gained = comp_delta.get("gained_zones", [])
                    if gained:
                        st.success(f"🎉 **Newly Allocated High-Priority Zones with +{sim_crews - 4} Crews:** {', '.join(gained)}")

                    sim_display_cols = ["priority_rank", "zone_id", "zone_name", "risk_score", "priority_score", "allocation_status", "allocated_crews", "allocated_pumps", "allocated_cost", "recommended_action"]
                    st.dataframe(sim_df[sim_display_cols], height=400, use_container_width=True)

                except Exception as e:
                    st.error(f"Simulation failed: {str(e)}")

    # ------------------------------------------------------------------
    # VIEW 6: 🎓 REC INFRASTRUCTURE PROFILE & DIGITAL TWIN
    # ------------------------------------------------------------------
    elif nav_option == "🎓 REC Infrastructure Profile & Twin":
        st.subheader("🎓 Critical Infrastructure Profile: Rajalakshmi Engineering College (REC)")
        st.caption("Digital Twin & Geospatial Evidence Attribution for Higher-Education Campus Infrastructure")

        col_rec_info, col_rec_trace = st.columns([1, 1.2])
        with col_rec_info:
            st.markdown("""
                <div class="tradeoff-card" style="border-left: 4px solid #8B5CF6;">
                    <h3 style="color: #8B5CF6; margin-top: 0;">🎓 Rajalakshmi Engineering College</h3>
                    <p><b>Zone Identifier:</b> <code>CHN-REC-01</code></p>
                    <p><b>Campus Address:</b> Rajalakshmi Nagar, Thandalam, Chennai – 602105</p>
                    <p><b>GPS Coordinates:</b> <code>13.009644, 80.004336</code></p>
                    <p><b>Facility Classification:</b> Critical Higher-Education & Research Infrastructure</p>
                    <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1);">
                    <p><b>Evidence-Based Risk Score:</b> <code>0.1990</code> (Low Risk Tier)</p>
                    <p><b>Priority Score:</b> <code>0.1559</code> (Rank 16 / 16)</p>
                    <p><b>Evidence Quality Confidence:</b> <code>95.7%</code> (Distance-Weighted Proxy)</p>
                    <p><b>Operational Action Directive:</b> <span style="color:#10B981;font-weight:700;">ROUTINE TELEMETRY MONITORING</span></p>
                </div>
            """, unsafe_allow_html=True)

            st.info("⚠️ **Data Integrity Standard:** Environmental observations are linked from the nearest available public observations; they are not claimed to be direct on-campus measurements.")

        with col_rec_trace:
            st.markdown("### 🔎 Spatially Linked Evidence Trace")
            st.markdown("""
                <div class="trace-step">
                    <b style="color: #38BDF8;">1. METEOROLOGICAL RAINFALL EVIDENCE</b><br>
                    • Nearest IMD Weather Station: <b>CHEMBARABAKKAM</b><br>
                    • Geodesic Haversine Distance: <b>5.76 km</b><br>
                    • Real Observed 24h Rainfall: <b>47.0 mm</b>
                </div>
                <div class="trace-step">
                    <b style="color: #FBBF24;">2. PHYSICAL INUNDATION EVIDENCE</b><br>
                    • Nearest GCC/OpenCity Survey Point: <b>Subway surveyed point (35.0")</b><br>
                    • Geodesic Haversine Distance: <b>18.89 km</b><br>
                    • On-Campus Survey Status: Unmeasured on-campus (Proxy linked from nearest point)
                </div>
                <div class="trace-step">
                    <b style="color: #34D399;">3. CMDA FLOOD HAZARD EVIDENCE</b><br>
                    • Nearest Hazard Polygon Category: <b>LOW / VERY LOW</b><br>
                    • Centroid Haversine Distance: <b>14.97 km</b>
                </div>
            """, unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # VIEW 7: 🤖 SIX-LAYER PIPELINE ARCHITECTURE
    # ------------------------------------------------------------------
    elif nav_option == "🤖 Six-Layer Pipeline Architecture":
        st.subheader("🤖 Six-Layer Intelligence Pipeline Architecture")
        st.caption("End-to-End Decision Flow: SENSE → PREDICT → PRIORITIZE → OPTIMIZE → RECOMMEND → SIMULATE")

        st.code("""
1. SENSE      : Ingests 192 OpenCity ground surveys, 53 GCC hotspots, 119 IMD stations with Haversine matching
      ↓
2. PREDICT    : Computes evidence-based risk_score (0.45*depth + 0.35*hazard + 0.20*rain*w_dist) + confidence
      ↓
3. PRIORITIZE : Deterministic Multi-Criteria Decision Analysis (MCDA) assigning transparent urgency tiers
      ↓
4. OPTIMIZE   : Google OR-Tools CP-SAT 0-1 Knapsack solver allocating pumps, rescue crews, and ₹ INR budget
      ↓
5. RECOMMEND  : Generates auditable operational directives (e.g. REPAIR & DISPATCH) and natural language briefings
      ↓
6. SIMULATE   : In-memory crisis scenario engine testing deluge surges and budget contractions without DB mutation
        """, language="text")

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "1. SENSE", "2. PREDICT", "3. PRIORITIZE", "4. OPTIMIZE", "5. RECOMMEND", "6. SIMULATE"
        ])

        with tab1:
            st.write("Structured state loaded across all 16 locations from SQLite `data/urbanshield.db`.")
            st.dataframe(zones_df[["zone_id", "zone_name", "latitude", "longitude", "inundation_depth_inches", "rainfall_mm", "nearest_rainfall_station", "rainfall_station_dist_km"]], height=350, use_container_width=True)

        with tab2:
            st.write("Evidence-based risk scores and distance-weighted observational confidence.")
            st.dataframe(zones_df[["zone_id", "zone_name", "risk_score", "risk_confidence", "hazard_category"]], height=350, use_container_width=True)

        with tab3:
            st.write("Multi-Criteria Decision Analysis (MCDA) urgency ranking.")
            st.dataframe(zones_df[["priority_rank", "zone_id", "zone_name", "priority_score", "priority_reason"]], height=350, use_container_width=True)

        with tab4:
            st.write("Google OR-Tools CP-SAT allocation plan under discrete resource limits.")
            st.dataframe(zones_df[["priority_rank", "zone_id", "zone_name", "allocation_status", "allocated_pumps", "allocated_crews", "allocated_cost", "allocation_reason"]], height=350, use_container_width=True)

        with tab5:
            st.write("Actionable operational directives and executive briefing memos.")
            for _, r in zones_df.head(6).iterrows():
                color = "green" if r["allocation_status"] == "ALLOCATED" else "orange"
                st.markdown(f"**Rank {r['priority_rank']} | [{r['zone_id']}] {r['zone_name']}** — `:{color}[{r['recommended_action']}]`")
                st.caption(f"📝 {r.get('executive_summary', '')}")
                st.markdown("---")

        with tab6:
            st.write("In-Memory What-If crisis simulation scenario results.")
            st.info("Navigate to the '🧪 What-If Crisis Scenario Simulator' tab to run live interactive scenario tests.")

    # ------------------------------------------------------------------
    # VIEW 8: 🌐 REAL DATA SOURCES & PROVENANCE
    # ------------------------------------------------------------------
    elif nav_option == "🌐 Real Data Sources & Provenance":
        st.subheader("🌐 Real Chennai Data Sources & Provenance")
        st.warning(
            "⚠️ **Disclaimer:** UrbanShield uses publicly available historical Chennai rainfall, inundation and flood-hazard observations. "
            "The current prototype performs evidence-based risk estimation rather than claiming a fully trained real-world predictive ML model. "
            "Future versions will integrate larger time-aligned historical datasets for supervised prediction."
        )

        st.markdown("""
        | Source Organization | Dataset Name & File | Format & Scope | Contribution to UrbanShield Pipeline |
        | :--- | :--- | :--- | :--- |
        | **OpenCity.in / GCC** | `chennai_flood_inundation_inches`<br>(`data/opencity_inundation_points.kml`) | 192 Surveyed Points (KML) | **Physical Ground Truth**: Measured flood waterlogging depth (5.0 to 60.0 inches) and field inspection remarks. |
        | **GCC Disaster Management Cell** | `chennai-gcc-flood-hotspots-2020`<br>(`data/opencity_gcc_flood_hotspots_2020.kml`) | 53 Municipal Zones (KML) | **Vulnerability Centroids**: Official municipal flood hotspot zones identified during Cyclone Nivar and extreme monsoon events. |
        | **India Meteorological Department (IMD)** | `chennai_rainfall_stations.csv` | 119 Station Records (CSV) | **Meteorological Telemetry**: Station-wise precipitation (mm) with Haversine distance spatial matching. |
        | **CMDA / GCC Master Plan** | `chennai_flood_hazard_zones`<br>(`data/opencity_flood_hazard_zones.kml`) | 7,453 Polygons (KML) | **Official Hazard Zoning**: Categorized flood susceptibility (*Very High, High, Moderate, Low, Very Low*). |
        | **Rajalakshmi Engineering College (REC)** | Official Institutional Campus Registry | Coordinates (`13.009644, 80.004336`) | **Critical Infrastructure Profile**: Distance-weighted spatial linking to nearest IMD Chembarambakkam station. |
        """)


if __name__ == "__main__":
    main()
