# 🛡️ UrbanShield

> **AI-Powered Urban Infrastructure Risk Management & Resource Optimization Platform**  
> *Team Crusaders — Phoenix Hacks* | **Track:** Sustainable Cities & Infrastructure

---

## 📌 Problem Statement

Rapid urbanization and climate volatility have made municipal flood response increasingly high-stakes. Municipal emergency managers face severe operational hurdles:
- **Data Fragmentation:** Raw precipitation, drainage telemetry, and soil sensors exist in silos without predictive intelligence.
- **Cognitive Overload:** Commanders must triage dozens of vulnerable zones simultaneously during cloudbursts and tidal surges.
- **Sub-Optimal Resource Deployment:** Heavy pumps and response crews are often deployed reactively rather than positioned where consequence-of-failure is highest.

---

## 💡 Solution: UrbanShield

**UrbanShield** bridges sensor telemetry and operational dispatch by converting raw environmental data into prioritized, explainable, and resource-optimized decisions. In sub-second response times, the platform:
1. Senses real-time environmental stress across 6 city zones.
2. Predicts localized flood probabilities using Machine Learning.
3. Prioritizes vulnerable sectors by consequence-weighting critical assets (hospitals, substations, ports).
4. Optimizes heavy equipment and crew placement using linear mathematical solvers.
5. Recommends plain-language, explainable action briefs with multi-dimensional rationale.
6. Simulates complex "what-if" extreme weather scenarios to stress-test municipal capacity.

---

## ⚡ Multi-Layer Pipeline Architecture

```text
                URBANSHIELD
                     │
                     ▼
            Infrastructure Data
                     │
                     ▼
                  SENSE
            (6 Sensor Feeds)
                     │
                     ▼
                 PREDICT
         (Random Forest ML Model)
                     │
                     ▼
               PRIORITIZE
      (Consequence & Population)
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
        (What-If Stress Recalc)
                     │
                     ▼
            Municipal Decision
                Dashboard
```

---

## 🛠️ Technology Stack

| Layer | Technologies Implemented |
|---|---|
| **Frontend & Visualization** | Streamlit (Python), Plotly (Interactive Charts), Folium / Leaflet (Geospatial Mapping) |
| **Backend & Integration** | Python REST API, Uvicorn / Starlette / HTTP Server, SQLite (Embedded Database) |
| **AI / Machine Learning** | Random Forest Classifier, Scikit-Learn / Pickle Artifacts |
| **Operations Research** | Google OR-Tools (Linear Mixed-Integer Programming Solver) |
| **Data Processing** | Pandas, NumPy, JSON Schema Normalizers |

---

## 🌟 Key Features

- **Geospatial Risk Mapping:** Interactive Folium map colored by risk severity with click-to-select zone markers.
- **Ranked Priority Matrix:** Prioritized triage table combining ML risk scores, population consequence weighting, and equipment allocation.
- **Explainable Action Briefs:** 3-dimensional rationale covering Environmental Drivers, Protected Infrastructure, and OR-Tools optimization logic.
- **What-If Simulation Sandbox:** 1-click stress-testing presets (Coastal Typhoon, Flash Cloudburst, Siltation Crisis, Nominal Baseline) with live equipment deficit calculations.
- **3-Tier Fallback Architecture:** Seamless failover chain (🟢 Live REST API ➔ 🟡 SQLite / Local Model ➔ 🟠 Calibrated Mock Fallback) ensuring zero UI freeze.
- **Bidirectional Synchronization:** Instant map ↔ table ↔ action brief state synchronicity across all interactions.

---

## 🏗️ System Data Flow

```text
Backend REST API (FastAPI / HTTP Server)
    │
    ▼
services/api_client.py (Schema Normalization & Fast-Fail Health Caching)
    │
    ▼
services/data_service.py + services/agent_service.py (Seams & Fallbacks)
    │
    ▼
Streamlit Session State (`selected_zone_id`)
    │
    ▼
Presentation Components (Header, KPI Cards, Map, Table, Brief, Charts, Simulation)
```

---

## 🚀 Running Locally

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.10 – 3.14)
- `pip` package manager

### 2. Clone & Install Dependencies
```bash
# Navigate to the repository
cd URBAN

# (Optional) Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
# Start Streamlit dashboard
streamlit run app.py
```
The dashboard will open in your browser at `http://localhost:8501`.

### 4. (Optional) Run the Live REST API Backend
```bash
# Start backend server on port 8000
python services/backend_server.py 8000
```

---

## 🔌 API & Environment Configuration

UrbanShield detects backend connectivity automatically via environment variables or the sidebar UI:

| Variable | Default | Purpose |
|---|---|---|
| `URBANSHIELD_API_URL` | `http://localhost:8000` | Target URL for live REST backend services |
| `BACKEND_API_URL` | `http://localhost:8000` | Fallback environment variable for API URL |
| `URBANSHIELD_API_TIMEOUT` | `0.4` seconds | Fast-fail timeout threshold to prevent UI latency |

### Fallback Tiers:
- 🟢 **Live REST API (`#10B981`):** Active HTTP connection to backend.
- 🟡 **SQLite DB / Local Model (`#3B82F6`):** Running on local `urbanshield.db` or `model.pkl`.
- 🟠 **Calibrated Mock Fallback (`#EA580C`):** Calibrated baseline telemetry active when offline.

---

## ⏱️ 2-Minute Hackathon Demo Flow

1. **City Risk Overview:** Review the 4 top KPI metrics and the **🚨 MOST URGENT PROBLEM** callout.
2. **Zone Drill-Down:** Click **Zone Z-01 (South Lowland Basin)** on the map or dropdown.
3. **Inspect 88% Critical Risk:** View the 6-stage pipeline trace from 68.5 mm/hr rain to #1 priority rank.
4. **Inspect Resource Allocation:** Observe OR-Tools assigning 4 heavy pumps and 2 crews to protect Metro General Hospital.
5. **Review Action Brief:** Read the 3-dimensional explainable rationale.
6. **Open What-If Simulation:** Switch to Tab 2 and select **🌊 Coastal Typhoon & Surge**.
7. **Observe Stress Recalculation:** Watch city risk jump to 92%, pump demand rise to 23 units, and an equipment deficit of **🚨 9 Pumps** trigger mutual aid protocols.
8. **Restore Baseline:** Click **☀️ Nominal Baseline** to confirm zero deficit.

---

## 👥 Team Crusaders

| Member | Track Responsibility |
|---|---|
| **Vandhana.M** | Team Lead, Pitch & Narrative Strategy |
| **Varsha.K** | AI/ML (Random Forest) & OR-Tools Optimization |
| **Varshini.S** | Frontend Architecture, UI Components & GIS Visualization |
| **Varssini.A** | Data Engineering, SQLite Schemas & QA Validation |
