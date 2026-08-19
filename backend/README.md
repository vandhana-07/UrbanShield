# UrbanShield — Backend API & Database

AI-powered urban infrastructure risk management and decision-support backend for UrbanShield.

---

## Quickstart (Local Development)

### 1. Create and Activate Virtual Environment
```bash
# From the backend directory
cd UrbanShield-Team/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (cmd):
.\venv\Scripts\activate.bat
# macOS / Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
```bash
python seed.py
```
*Seeds SQLite (`urbanshield.db`) with 25 realistic, interconnected infrastructure assets (bridges, power grid, water lines, drainage, roads, public facilities) across a metropolitan coordinate cluster with risk scores, priority rankings, and recommendations.*

### 4. Run Smoke Tests
```bash
python tests/smoke_test.py
```

### 5. Start Backend Server
```bash
python app.py
```
*Server starts at `http://localhost:5000` with CORS enabled for all frontend dev ports.*

---

## Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `FLASK_ENV` | `development` | Environment mode |
| `PORT` | `5000` | Local port |
| `MOCK_MODE` | `true` | `true` uses built-in mock engine. Set to `false` when Member 3's AI Agent is running on port 8000. |
| `AGENT_URL` | `http://localhost:8000` | Member 3 AI Agent URL |
| `AGENT_TIMEOUT_SECONDS` | `6.0` | HTTP timeout before falling back to mock engine |
| `DATABASE_URL` | `sqlite:///urbanshield.db` | SQLite database URI |

---

## API Summary (Base URL: `http://localhost:5000/api`)

- **System:** `GET /api/system/status`
- **Dashboard:** `GET /api/dashboard/summary`
- **Assets:** `GET /api/assets`, `GET /api/assets/<id>`, `POST /api/assets`
- **Risks:** `GET /api/risks`
- **Priorities:** `GET /api/priorities`
- **Recommendations:** `GET /api/recommendations`, `PATCH /api/recommendations/<id>`
- **Simulations:** `POST /api/simulations/run`, `GET /api/simulations`, `GET /api/simulations/<id>`
