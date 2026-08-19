# 🏙️ UrbanShield — AI-Powered Urban Infrastructure Risk Management & Decision Support

> **UrbanShield** is an end-to-end intelligent resilience platform that predicts structural failures, prioritizes municipal interventions, and simulates disaster scenarios across critical metropolitan infrastructure assets.

[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen.svg)]()
[![Backend](https://img.shields.io/badge/Backend-Flask%20%7C%20SQLite%20%7C%20REST-blue.svg)](./backend/README.md)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%7C%20Vite%20%7C%20Tailwind-purple.svg)]()
[![AI Engine](https://img.shields.io/badge/AI%20Agent-Multi--Layer%20Intelligence-orange.svg)]()

---

## 🏛️ System Architecture & Team Allocation

UrbanShield is designed around a modular 3-tier architecture with clean separation of concerns:

```mermaid
graph LR
    subgraph Member1 ["Frontend (Member 1)"]
        UI[Interactive Geospatial Dashboard & Scenario Visualizer]
    end

    subgraph Member2 ["Backend & DB (Member 2)"]
        API[Flask REST API Engine\n+ Deterministic Mock System\n+ SQLite DB]
    end

    subgraph Member3 ["AI / Multi-Layer Agent (Member 3)"]
        AI[Sense → Predict → Prioritize → Optimize → Recommend → Simulate]
    end

    UI <===>|HTTP REST /api| API
    API <===>|HTTP REST /agent (Fallback-Protected)| AI
```

---

## 📊 Dataset & Machine Learning Calibration

UrbanShield trains its predictive models on a **calibrated synthetic dataset** (`data/indian_flood_dataset.csv`) whose parameter distributions are anchored to documented Indian monsoon events and municipal statistics across major metropolitan flood zones (e.g., Mumbai Mithi River, Chennai Velachery, Bengaluru Silk Board, Kolkata MG Road, Delhi Yamuna Floodplain, Hyderabad Musi River, and Kochi). 

*All parameter anchors and citations are documented in [`data/SOURCES.md`](./data/SOURCES.md).*  
*Note: The training dataset is synthetically generated and calibrated against published figures; it is not raw governmental sensor telemetry.*

---

## 📂 Repository Organization

```
UrbanShield/
├── backend/                     # 🛡️ Backend API, SQLite Database, Mock Engine, & Tests (Member 2)
│   ├── app.py                   # Flask Application Factory & Blueprints
│   ├── config.py                # Typed Environment Config Loader
│   ├── database.py              # SQLAlchemy DB Instance
│   ├── models.py                # Asset, RiskAssessment, PriorityRanking, Recommendation, Simulation
│   ├── seed.py                  # CLI Seeder for 25 Urban Infrastructure Assets
│   ├── routes/                  # REST Endpoints (/api/system, /api/dashboard, /api/assets, /api/simulations)
│   ├── services/                # Mock Engine & Resilient Agent Client with Fallback
│   ├── tests/                   # 45-Point Automated Smoke Test Suite
│   └── README.md                # 📖 Complete Backend Documentation & API Reference
│
├── frontend/                    # 🎨 Interactive Geospatial Dashboard (Member 1)
├── layers/                      # 🤖 Multi-Layer AI Intelligence (Sense, Predict, Prioritize, Optimize, Recommend, Simulate)
├── data/                        # 📈 Calibrated Datasets (indian_flood_dataset.csv, SOURCES.md)
└── docs/                        # 📖 AI/ML Architecture & Explainability Documentation
```

---

## 🚀 Quickstart Guide

### 1. Run the Backend API (Port 5000)
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python seed.py
python app.py
```
*Backend runs at `http://localhost:5000/api`.*  
*For comprehensive backend API documentation, see [backend/README.md](./backend/README.md).*

---

## 👥 Team Members & Roles

- **Member 1 (Frontend Lead):** User Interface, Geospatial Maps, Simulation Graphs & Dashboard Experience.
- **Member 2 (Backend & Database Lead):** REST APIs, SQLite Schema, Deterministic Mock System & Agent Bridge.
- **Member 3 (AI / Intelligence Lead):** Multi-Layer Agent Intelligence, Sensor Telemetry Analysis & Optimization.

---
*Built during the 24-Hour Urban Resilience Hackathon.*
