"""
UrbanShield - Operations Charts Component
Renders exactly 2 focused Plotly charts:
1. Risk Distribution by City Zone (Color-coded severity bars)
2. Resource Allocation vs Baseline Need (Pumps allocated per zone)
"""

import streamlit as st
import plotly.graph_objects as go
from config import SEVERITY_CONFIG, get_severity_color
from services.agent_service import get_pipeline_predictions, get_recommendations_and_allocations
from services.data_service import get_zones_summary

def render_operational_charts():
    """
    Renders 2 focused Plotly charts in side-by-side columns.
    Handles empty data and exceptions gracefully.
    """
    try:
        with st.spinner("Generating operational risk & allocation charts..."):
            predictions = get_pipeline_predictions() or []
            recommendations = get_recommendations_and_allocations() or {}
            zones_list = get_zones_summary() or []
            zones = {z["zone_id"]: z["name"] for z in zones_list}

            # Empty state check
            if not predictions:
                st.info("ℹ️ No active telemetry available to render operational charts.")
                return

            # Prepare Data for Chart 1: Risk Distribution
            zone_names = [f"[{p['zone_id']}] {zones.get(p['zone_id'], p['zone_id'])}" for p in predictions]
            risk_scores = [p.get("risk_score", 0.0) for p in predictions]
            severities = [p.get("severity", "Low") for p in predictions]
            colors = [get_severity_color(s) for s in severities]

            # Prepare Data for Chart 2: Resource Allocation
            pumps_allocated = [recommendations.get(p["zone_id"], {}).get("allocated_pumps", 0) for p in predictions]
            crews_allocated = [recommendations.get(p["zone_id"], {}).get("allocated_crews", 0) for p in predictions]

        col1, col2 = st.columns(2)

        # ---------------------------------------------------------------------
        # CHART 1: Risk Score Distribution
        # ---------------------------------------------------------------------
        with col1:
            st.markdown("###### 📊 Risk Probability by Zone (Random Forest)")
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=risk_scores,
                y=zone_names,
                orientation='h',
                marker=dict(color=colors, line=dict(color='#334155', width=1)),
                text=[f"{s:.2f}" for s in risk_scores],
                textposition='auto',
                hoverinfo='text',
                hovertext=[f"{z}: {s:.2f} ({sev})" for z, s, sev in zip(zone_names, risk_scores, severities)]
            ))
            fig1.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=20, t=10, b=10),
                height=260,
                xaxis=dict(
                    title="Flood Probability (0.0 - 1.0)",
                    range=[0, 1.05],
                    gridcolor='#334155',
                    tickfont=dict(color='#94A3B8')
                ),
                yaxis=dict(
                    autorange="reversed",
                    tickfont=dict(color='#F8FAFC', size=11)
                )
            )
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

        # ---------------------------------------------------------------------
        # CHART 2: Resource Allocation vs Demand
        # ---------------------------------------------------------------------
        with col2:
            st.markdown("###### 🚜 OR-Tools Asset Deployment (Pumps & Crews)")
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=zone_names,
                y=pumps_allocated,
                name="Heavy Pumps (🚜)",
                marker=dict(color="#3B82F6")
            ))
            fig2.add_trace(go.Bar(
                x=zone_names,
                y=crews_allocated,
                name="Response Crews (👷)",
                marker=dict(color="#10B981")
            ))
            fig2.update_layout(
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=20, t=10, b=10),
                height=260,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color='#94A3B8')
                ),
                xaxis=dict(
                    tickangle=-25,
                    tickfont=dict(color='#F8FAFC', size=10)
                ),
                yaxis=dict(
                    title="Units Deployed",
                    gridcolor='#334155',
                    tickfont=dict(color='#94A3B8')
                )
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    except Exception as e:
        st.error(f"⚠️ Error rendering operational charts: {e}")
