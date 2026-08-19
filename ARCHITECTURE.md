# 🏛️ UrbanShield — System Architecture

This document describes the end-to-end technical architecture of **UrbanShield**, explaining how data flows from environmental sensor feeds through Machine Learning, Mixed-Integer Optimization, and Explainable Action generation to the Streamlit commander interface.

---

## 1. System Overview & Multi-Layer Pipeline

UrbanShield is designed as an autonomous multi-layer decision pipeline:

```text
                URBANSHIELD
                     │
                     ▼
            Infrastructure Data
                     │
                     ▼
                  SENSE
       (Rainfall, Drainage, Soil)
                     │
                     ▼
                 PREDICT
        (Random Forest Classifier)
                     │
                     ▼
               PRIORITIZE
      (Consequence & Vulnerability)
                     │
                     ▼
                OPTIMIZE
        (OR-Tools Linear Solver)
                     │
                     ▼
               RECOMMEND
        (Explainable Action Brief)
                     │
                     ▼
                SIMULATE
         (What-If Recalculation)
                     │
                     ▼
            Municipal Decision
                Dashboard
```

---

## 2. Layer-by-Layer Breakdown

### A. Frontend Presentation Layer (`app.py`, `components/`)
Built with **Streamlit** for real-time reactivity without JavaScript bloat:
- **`app.py`:** Main application shell orchestrating layout, system health badges, tab navigation, and reactive state routing.
- **`components/header.py`:** Municipal branding bar and 6-stage pipeline progress stepper with real-time status pill indicators.
- **`components/kpi_cards.py`:** 4 high-level city operational counters with an automatic **🚨 MOST URGENT PROBLEM** callout banner.
- **`components/map_view.py`:** Interactive Folium geospatial map rendering circle markers sized and colored by risk severity with click-to-focus event extraction.
- **`components/priority_table.py`:** Ranked urgency dataframe and embedded 6-stage decision trace expander with pre-synchronized selectbox state.
- **`components/recommendation_view.py`:** Plain-language explainable decision brief detailing Environmental Drivers, Asset Protection Rationale, and OR-Tools optimization logic.
- **`components/charts.py`:** Plotly horizontal bar charts for Risk Distribution and OR-Tools asset deployments.
- **`components/simulation_panel.py`:** Scenario stress-testing sandbox with 1-click presets, manual sliders, Plotly before-vs-after risk delta charts, and equipment deficit indicators.

---

### B. API Integration & Normalization Layer (`services/api_client.py`)
Provides seamless REST communication between the frontend and backend services:
- **Fast-Fail Health Probing:** Probes `/api/health`, `/health`, or `/api/status` with a 0.4s timeout threshold.
- **Health Caching:** Uses `@st.cache_data(ttl=3)` to eliminate redundant network round-trips across UI components.
- **Connection Error Short-Circuiting:** Instantly breaks on dead host errors to guarantee sub-millisecond offline performance.
- **Schema Normalization:** Translates varied backend field aliases (`latitude`/`lat`, `pop`/`population`, `score`/`risk_score`) into strict frontend schemas.

---

### C. Data Ingestion & Storage Layer (`services/data_service.py`)
Manages city zone attributes, infrastructure metadata, and municipal resource pools:
- **Dynamic Data Sourcing:** Attempts Live REST API ➔ SQLite (`urbanshield.db`) ➔ Calibrated Mock Fallback.
- **Resource Pool Management:** Tracks total heavy pumps (14), rapid response crews (10), and emergency budget ($300k).

---

### D. AI/ML Prediction & Optimization Layer (`services/agent_service.py`)
Connects the analytical intelligence core:
- **PREDICT:** Evaluates 4 core features (`rainfall_mm_per_hr`, `drainage_capacity_pct`, `soil_saturation_pct`, `elevation_m`) through Random Forest classifiers to predict flood probabilities.
- **PRIORITIZE:** Ranks sectors by combining ML risk probability with population density and critical infrastructure consequence weighting.
- **OPTIMIZE:** Executes OR-Tools linear mixed-integer programming (MIP) to optimally assign pumps and crews under strict supply constraints.
- **SIMULATE:** Dynamically recalculates risk shifts, re-ranks priorities, and computes equipment deficits under altered rainfall and storm surge parameters.

---

## 3. Fallback & Fault-Tolerance Architecture

To guarantee 100% demo reliability under unpredictable hackathon presentation environments, UrbanShield implements a strict 3-tier fallback architecture:

```text
       ┌─────────────────────────────────────────┐
       │         Tier 1: Live REST API           │
       │    (FastAPI / Flask on port 8000)       │
       │           Badge: 🟢 Live REST           │
       └────────────────────┬────────────────────┘
                            │ (If offline / timeout)
                            ▼
       ┌─────────────────────────────────────────┐
       │     Tier 2: Embedded SQLite / Model     │
       │     (urbanshield.db / model.pkl)        │
       │          Badge: 🟡 SQLite/Model         │
       └────────────────────┬────────────────────┘
                            │ (If DB/model absent)
                            ▼
       ┌─────────────────────────────────────────┐
       │   Tier 3: Calibrated Fallback Mock      │
       │       (services/mock_data.py)           │
       │          Badge: 🟠 Mock Stubs           │
       └─────────────────────────────────────────┘
```

### Why This Matters for Hackathon Judging:
1. **Zero UI Freeze:** If the backend crashes or network Wi-Fi drops, the frontend transitions to mock stubs in **2.1ms** without throwing Python exceptions or freezing the page.
2. **Transparent Status:** The system status badge in the header explicitly communicates whether live or fallback data is being displayed.
3. **Instant Recovery:** Reconnecting the live API automatically restores live REST mode on the next interaction.

---

## 4. State Synchronization Matrix

```text
Folium Map Click (Marker Z-01)
       │
       ├──────────────────────────────────────────┐
       ▼                                          ▼
st.session_state["selected_zone_id"]    st.session_state["priority_zone_selector"]
       │                                          │
       ├──────────────────────────────────────────┘
       ▼
Action Brief (Z-01)  +  Decision Trace (Z-01)  +  Table Selection (Z-01)
```
- **Bidirectional Consistency:** Updating the dropdown immediately focuses the map; clicking a map marker immediately updates the dropdown and Action Brief.
