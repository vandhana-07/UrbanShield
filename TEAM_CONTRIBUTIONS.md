# 👥 UrbanShield — Team Crusaders Contributions

**Track:** Sustainable Cities & Infrastructure | **Hackathon:** Phoenix Hacks

---

## Team Roster & Individual Contributions

### 1. Vandhana.M — Team Lead, Pitch & Narrative Strategy
- **Responsibilities:**
  - Problem framing, municipal user persona definition, and pitch narrative.
  - Value proposition alignment with UN Sustainable Development Goal 11 (Sustainable Cities and Communities).
  - 2-minute judge pitch delivery and Q&A coordination.
  - Overall presentation timing and deck design.

---

### 2. Varsha.K — AI/ML & Optimization Engineering
- **Responsibilities:**
  - Designed the **PREDICT** layer using Random Forest machine learning for flood vulnerability scoring.
  - Formulated the **OPTIMIZE** layer using Google OR-Tools Mixed-Integer Programming (MIP) to solve resource-constrained equipment allocation.
  - Implemented risk probability calculations and driver extraction.
  - Provided REST endpoint schemas for ML predictions and OR-Tools recommendations.

---

### 3. Varshini.S — Frontend Architecture, UI & GIS Visualization (This Repository)
- **Responsibilities:**
  - Architected the Streamlit municipal command dashboard (`app.py`, `components/`).
  - Implemented interactive Folium geospatial mapping with risk-colored CircleMarkers and click-to-focus event extraction.
  - Developed the **What-If Simulation Sandbox** with 1-click presets and before-vs-after Plotly risk delta charts.
  - Built the decoupled REST API client (`services/api_client.py`) with schema normalization, fast-fail health probing, and 3-tier fallback architecture.
  - Guaranteed bidirectional state synchronization between map clicks, priority table selections, and Action Briefs.

---

### 4. Varssini.A — Data Engineering, Database Schemas & QA Validation
- **Responsibilities:**
  - Designed SQLite database schemas (`urbanshield.db`) for city zone definitions, sensor telemetry, and resource pools.
  - Authored automated integration test suites (`test_pipeline.py`, `test_live_backend_integration.py`).
  - Executed fault-tolerance, network latency, and offline fallback stress testing.
  - Validated data contracts, schema alias handling, and edge case resilience.
