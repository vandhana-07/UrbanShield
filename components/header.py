"""
UrbanShield - Header & Pipeline Stepper Component
Renders the municipal title and the 6-stage Multi-Layer Agent pipeline banner.
"""

import streamlit as st
from services.data_service import get_data_source_status
from services.agent_service import get_model_source_status

def render_header(active_stage: str = "LIVE"):
    """
    Renders the municipal header and 6-stage pipeline progress indicator with live telemetry badges.
    """
    data_status = get_data_source_status()
    model_status = get_model_source_status()

    def _badge_style(status_dict):
        tier = status_dict.get("tier", "mock")
        if tier == "live":
            return "background-color: #064E3B; color: #6EE7B7; border: 1px solid #059669;"
        elif tier in ["sqlite", "model"]:
            return "background-color: #1E3A8A; color: #93C5FD; border: 1px solid #3B82F6;"
        else:
            return "background-color: #78350F; color: #FDE68A; border: 1px solid #D97706;"

    # Title & Branding Bar
    col1, col2 = st.columns([2.5, 1.5])
    with col1:
        st.markdown("## 🛡️ **UrbanShield** | Municipal Infrastructure & Flood Response Engine")
        st.caption("📍 **Simulated Metro District** • Team Crusaders (Phoenix Hacks — Sustainable Cities & Infrastructure)")
    with col2:
        st.markdown(
            f"""
            <div style="text-align: right; padding-top: 5px; display: flex; gap: 8px; justify-content: flex-end; flex-wrap: wrap;">
                <span title="{data_status['details']}" style="{_badge_style(data_status)} padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.78rem;">
                    {data_status.get('icon', '●')} Data: {data_status['mode']}
                </span>
                <span title="{model_status['details']}" style="{_badge_style(model_status)} padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.78rem;">
                    {model_status.get('icon', '●')} Model: {model_status['mode']}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # 6-Stage Multi-Layer Agent Pipeline Stepper
    st.markdown("##### ⚡ Multi-Layer Agent Pipeline Architecture")
    
    stages = [
        ("1. SENSE", "6 Sensor Feeds", "📡", "#3B82F6"),
        ("2. PREDICT", "Random Forest ML", "🤖", "#8B5CF6"),
        ("3. PRIORITIZE", "Impact Weighting", "⚖️", "#EC4899"),
        ("4. OPTIMIZE", "OR-Tools Solver", "🧩", "#F59E0B"),
        ("5. RECOMMEND", "Explainable Action", "📋", "#10B981"),
        ("6. SIMULATE", "What-If Recalc", "🔄", "#06B6D4")
    ]
    
    cols = st.columns(len(stages))
    for idx, (name, subtitle, icon, accent_color) in enumerate(stages):
        with cols[idx]:
            st.markdown(
                f"""
                <div style="background-color: #1E293B; border-top: 3px solid {accent_color}; border-radius: 6px; padding: 10px 6px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    <div style="font-size: 1.2rem; margin-bottom: 2px;">{icon}</div>
                    <div style="font-weight: 700; font-size: 0.82rem; color: #F8FAFC;">{name}</div>
                    <div style="font-size: 0.70rem; color: #94A3B8; margin-top: 2px;">{subtitle}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
