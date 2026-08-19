"""
UrbanShield - What-If Simulation Panel Component
Renders interactive scenario presets and sliders (Rainfall, Drainage Blockage, Storm Surge),
triggers the SIMULATE layer, and renders a side-by-side Before/After comparison matrix with Plotly charts.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from services.agent_service import run_simulation
from config import SEVERITY_CONFIG

# -----------------------------------------------------------------------------
# CONSTANTS: 1-Click Stress Test Preset Configurations
# -----------------------------------------------------------------------------
PRESET_SCENARIOS = {
    "typhoon": {
        "label": "🌊 Coastal Typhoon & Surge",
        "rainfall_multiplier": 2.5,
        "drainage_capacity_pct": 35.0,
        "storm_surge": True,
        "help": "Rainfall 2.5x, Drainage 35%, Surge Active (Severe Coastal Threat)"
    },
    "cloudburst": {
        "label": "🌧️ Downtown Flash Cloudburst",
        "rainfall_multiplier": 3.0,
        "drainage_capacity_pct": 65.0,
        "storm_surge": False,
        "help": "Rainfall 3.0x, Drainage 65%, Surge Inactive (Extreme Precipitation)"
    },
    "siltation": {
        "label": "🚰 Culvert Siltation Crisis",
        "rainfall_multiplier": 1.3,
        "drainage_capacity_pct": 20.0,
        "storm_surge": False,
        "help": "Rainfall 1.3x, Drainage 20%, Surge Inactive (Infrastructure Blockage)"
    },
    "nominal": {
        "label": "☀️ Nominal Baseline",
        "rainfall_multiplier": 1.0,
        "drainage_capacity_pct": 85.0,
        "storm_surge": False,
        "help": "Rainfall 1.0x, Drainage 85%, Surge Inactive (Normal Conditions)"
    }
}

def apply_preset(preset_key: str):
    """
    Callback executed BEFORE widget creation to cleanly update slider values in session state.
    """
    cfg = PRESET_SCENARIOS[preset_key]
    st.session_state["sim_rainfall_slider"] = cfg["rainfall_multiplier"]
    st.session_state["sim_drainage_slider"] = cfg["drainage_capacity_pct"]
    st.session_state["sim_surge_checkbox"] = cfg["storm_surge"]

def render_simulation_panel():
    """
    Renders the What-If Sandbox with presets, sliders, delta charts, and Before/After matrix.
    """
    st.markdown("### 🔄 What-If Simulation Sandbox (SIMULATE Layer)")
    st.caption(
        "Stress-test municipal resilience against extreme weather scenarios. "
        "The Multi-Layer Agent dynamically recalculates flood probabilities, re-ranks zone priorities, "
        "and optimizes pump and crew deployment in real time."
    )

    # Pre-initialize session state for slider keys to avoid Streamlit widget mutation errors
    if "sim_rainfall_slider" not in st.session_state:
        st.session_state["sim_rainfall_slider"] = 1.5
    if "sim_drainage_slider" not in st.session_state:
        st.session_state["sim_drainage_slider"] = 50.0
    if "sim_surge_checkbox" not in st.session_state:
        st.session_state["sim_surge_checkbox"] = False

    # -------------------------------------------------------------------------
    # 1. 1-CLICK PITCH SCENARIO PRESETS (Using on_click callbacks)
    # -------------------------------------------------------------------------
    st.markdown("##### ⚡ Quick Scenario Presets (1-Click Judge Demo)")
    pr_cols = st.columns(len(PRESET_SCENARIOS))

    for idx, (key, cfg) in enumerate(PRESET_SCENARIOS.items()):
        with pr_cols[idx]:
            st.button(
                cfg["label"],
                key=f"preset_btn_{key}",
                on_click=apply_preset,
                args=(key,),
                use_container_width=True,
                help=cfg["help"]
            )

    # -------------------------------------------------------------------------
    # 2. SCENARIO CONTROLS (Input Sliders)
    # -------------------------------------------------------------------------
    with st.container():
        st.markdown("##### 🎛️ Manual Scenario Parameters")
        c1, c2, c3 = st.columns([1.5, 1.5, 1])

        with c1:
            rainfall_mult = st.slider(
                "🌧️ Rainfall Multiplier",
                min_value=1.0,
                max_value=3.0,
                step=0.1,
                key="sim_rainfall_slider",
                help="1.0x = Current conditions, 2.0x = Severe storm, 3.0x = Extreme cloudburst emergency"
            )

        with c2:
            drainage_cap = st.slider(
                "🚰 City Drainage Efficiency (%)",
                min_value=10.0,
                max_value=100.0,
                step=5.0,
                key="sim_drainage_slider",
                help="Simulate debris clogging or maintenance deficit across urban culverts"
            )

        with c3:
            st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
            storm_surge = st.checkbox(
                "🌊 Tidal Storm Surge",
                key="sim_surge_checkbox",
                help="Enable coastal surge affecting Lowland Basin & Port"
            )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 3. RUN SIMULATION & RENDER BEFORE / AFTER MATRIX
    # -------------------------------------------------------------------------
    try:
        sim_data = run_simulation(
            rainfall_multiplier=rainfall_mult,
            drainage_capacity_pct=drainage_cap,
            storm_surge=storm_surge
        )

        zones = sim_data["zones"]
        impact = sim_data["resource_impact"]

        # Staleness Guard: Ensure selected_zone_id is still valid
        active_zone_ids = [z["zone_id"] for z in zones]
        if st.session_state.get("selected_zone_id") not in active_zone_ids and active_zone_ids:
            st.session_state["selected_zone_id"] = zones[0]["zone_id"]

        # Resource Pool Deficit / Health Banner
        p1, p2, p3 = st.columns(3)
        with p1:
            st.metric("Total Pumps Needed (Simulated)", f"{impact['total_pumps_needed']} Units", f"Pool: {impact['available_pumps_pool']}")
        with p2:
            deficit = impact["deficit"]
            if deficit > 0:
                st.metric("🚨 Equipment Deficit", f"-{deficit} Pumps Needed", "Over Capacity (Mutual Aid Needed)", delta_color="inverse")
            else:
                st.metric("✅ Equipment Capacity", "Sufficient", "All High-Risk Zones Covered")
        with p3:
            avg_risk_delta = round(sum(z["risk_delta"] for z in zones) / len(zones), 2)
            st.metric("Average City Risk Shift", f"{avg_risk_delta:+.2f}", f"{'+' if avg_risk_delta > 0 else ''}{avg_risk_delta*100:.0f}%")

        # ---------------------------------------------------------------------
        # 4. PLOTLY BEFORE VS AFTER RISK DELTA CHART (Consistently Sorted)
        # ---------------------------------------------------------------------
        st.markdown("##### 📊 Before vs. After Risk Shift by Zone")
        
        # Sort consistently by baseline risk descending so categories do not jump around between runs
        chart_zones = sorted(zones, key=lambda z: z["baseline_risk"], reverse=True)
        zone_labels = [f"[{z['zone_id']}] {z['name']}" for z in chart_zones]
        base_risks = [z["baseline_risk"] for z in chart_zones]
        sim_risks = [z["simulated_risk"] for z in chart_zones]

        fig_sim = go.Figure()
        fig_sim.add_trace(go.Bar(
            x=zone_labels,
            y=base_risks,
            name="Baseline Risk (Normal)",
            marker=dict(color="#64748B")
        ))
        fig_sim.add_trace(go.Bar(
            x=zone_labels,
            y=sim_risks,
            name="Simulated Risk (Stress Scenario)",
            marker=dict(color="#EF4444")
        ))
        fig_sim.update_layout(
            barmode='group',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=20, t=10, b=10),
            height=250,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color='#94A3B8')
            ),
            xaxis=dict(
                tickangle=-15,
                tickfont=dict(color='#F8FAFC', size=11)
            ),
            yaxis=dict(
                title="Flood Probability",
                range=[0, 1.05],
                gridcolor='#334155',
                tickfont=dict(color='#94A3B8')
            )
        )
        st.plotly_chart(fig_sim, use_container_width=True, config={"displayModeBar": False})

        # ---------------------------------------------------------------------
        # 5. BEFORE VS AFTER COMPARISON MATRIX
        # ---------------------------------------------------------------------
        st.markdown("##### 📋 Recalculated Priority & Dynamic Action Plan")
        
        comparison_rows = []
        for z in zones:
            r_delta = z["risk_delta"]
            delta_str = f"+{r_delta:.2f}" if r_delta > 0 else f"{r_delta:.2f}"
            pump_delta = z["pump_delta"]
            p_delta_str = f"+{pump_delta}" if pump_delta > 0 else f"{pump_delta}"

            comparison_rows.append({
                "Sim Rank": f"#{z['simulated_priority_rank']}",
                "Zone": f"[{z['zone_id']}] {z['name']}",
                "Baseline Risk": f"{z['baseline_risk']:.2f} ({z['baseline_severity']})",
                "Simulated Risk": f"{z['simulated_risk']:.2f} ({z['simulated_severity']})",
                "Risk Shift": delta_str,
                "Baseline Pumps": z["baseline_pumps"],
                "Simulated Pumps": z["simulated_pumps"],
                "Pump Reallocation": f"{p_delta_str} Pumps",
                "Dynamic Action Plan": z["simulated_action"]
            })

        df_sim = pd.DataFrame(comparison_rows)
        st.dataframe(
            df_sim,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Sim Rank": st.column_config.TextColumn("New Rank", width="small"),
                "Zone": st.column_config.TextColumn("Zone", width="medium"),
                "Baseline Risk": st.column_config.TextColumn("Baseline Risk", width="small"),
                "Simulated Risk": st.column_config.TextColumn("Simulated Risk", width="small"),
                "Risk Shift": st.column_config.TextColumn("Risk Shift", width="small"),
                "Baseline Pumps": st.column_config.NumberColumn("Orig Pumps", width="small"),
                "Simulated Pumps": st.column_config.NumberColumn("New Pumps", width="small"),
                "Pump Reallocation": st.column_config.TextColumn("Pump Delta", width="small"),
                "Dynamic Action Plan": st.column_config.TextColumn("Recalculated Protocol", width="large")
            }
        )

        st.info("💡 **Judge Note:** Triggering any scenario above recalculates the full PREDICT → PRIORITIZE → OPTIMIZE pipeline live, rebalancing municipal resources in sub-second time without refreshing the page.")

    except Exception as e:
        st.error(f"⚠️ Error running simulation scenario: {e}")


