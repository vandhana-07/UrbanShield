# UrbanShield Real Data Architecture & Explainability Documentation

This document details the real-world Chennai dataset integration, evidence-based risk estimation methodology, optimization formulation, and limitations for UrbanShield.

---

## 1. System Philosophy & Evidence-Based Estimation (PREDICT Layer)

Urban flood risk estimation during disaster response requires **transparent, defensible, and audit-ready metrics grounded in real-world evidence**. 

Rather than relying on ungrounded synthetic data or circular target labels, UrbanShield utilizes **real historical and surveyed Chennai flood observations** across three primary data streams:
1. **Ground-Surveyed Inundation Depth**: Physical flood water level (inches) measured by municipal field teams.
2. **Official Municipal Hazard Classification**: Long-term vulnerability zoning designated by CMDA and the Greater Chennai Corporation (GCC).
3. **Meteorological Rainfall Evidence**: Real weather station observations from the India Meteorological Department (IMD).

---

## 2. Real Chennai Data Specifications & Sources

UrbanShield integrates four authentic, publicly available Chennai municipal datasets:

* **OpenCity / Greater Chennai Corporation Inundation Points** (`data/opencity_inundation_points.kml`): 192 surveyed ground-truth flood inundation points with measured water depths and field inspection remarks.
* **GCC Municipal Flood Hotspots** (`data/opencity_gcc_flood_hotspots_2020.kml`): 53 vulnerable municipal zones identified during extreme monsoon events.
* **IMD Chennai Weather Station Network** (`data/chennai_rainfall_stations.csv`): 119 station records capturing precipitation across metropolitan Chennai.
* **CMDA / GCC Flood Hazard Zone Mapping** (`data/opencity_flood_hazard_zones.kml`): 7,453 geospatial flood hazard polygons categorizing susceptibility into *Very High, High, Moderate, Low, Very Low*.

*(See [`docs/data_sources.md`](./data_sources.md) for full citations, URLs, and access metadata).*

---

## 3. Evidence-Based Flood Risk Formulation (PREDICT Layer)

Urban flood risk probability (`risk_score`) is calculated directly from observed empirical evidence:

$$\text{norm\_depth} = \min\left(1.0, \frac{\text{inundation\_depth\_inches}}{24.0}\right)$$

$$\text{hazard\_factor} \in \{1.00 \text{ (VERY\_HIGH)}, 0.75 \text{ (HIGH)}, 0.50 \text{ (MODERATE)}, 0.25 \text{ (LOW)}\}$$

$$\text{proximity\_weight} = \max\left(0.30, 1.0 - \frac{\text{dist\_km}}{20.0}\right)$$

$$\text{norm\_rainfall} = \min\left(1.0, \frac{\text{rainfall\_mm}}{60.0}\right) \cdot \text{proximity\_weight}$$

$$\text{risk\_score} = 0.45 \cdot \text{norm\_depth} + 0.35 \cdot \text{hazard\_factor} + 0.20 \cdot \text{norm\_rainfall}$$

### Factor Rationale:
* **Inundation Depth ($45\%$)**: Direct physical observation of standing flood water. Inundation exceeding 12–18 inches severely disrupts traffic, overwhelms stormwater drains, and damages structures.
* **Official Hazard Category ($35\%$)**: Reflects long-term topography, soil permeability, and municipal drainage capacity established by CMDA/GCC.
* **IMD Rainfall Evidence ($20\%$)**: Proximate rainfall telemetry weighted by distance confidence from the reporting weather station.

---

## 4. Observational Confidence

Prediction uncertainty is modeled through an **observational confidence score** (`risk_confidence` $\in [0.70, 0.99]$):

$$\text{risk\_confidence} = 0.85 + 0.15 \cdot \text{proximity\_weight}$$

Zones located directly adjacent to verified IMD weather stations and with direct ground inundation surveys receive up to $99\%$ confidence, while distant stations receive smooth dampening without suppressing high-risk alerts below an $85\%$ floor.

---

## 5. Limitations & Disclosure

> [!IMPORTANT]
> **DATA & METHODOLOGY DISCLOSURE**
> **UrbanShield uses publicly available historical Chennai rainfall, inundation and flood-hazard observations. The current prototype performs evidence-based risk estimation rather than claiming a fully trained real-world predictive ML model. Future versions will integrate larger time-aligned historical datasets for supervised prediction.**

### Technical Limitations:
1. **Temporal Coupling**: Rainfall observations and inundation survey snapshots are linked through spatial proximity rather than microsecond-synchronized IoT telemetry.
2. **Spatial Correlation**: Zones are currently treated as discrete administrative units; future iterations will incorporate watershed hydraulic routing between neighboring basins.

---

## 6. Multi-Criteria Decision Analysis (PRIORITIZE Layer)

Layer 3 (**PRIORITIZE**) uses a **deterministic Multi-Criteria Decision Analysis (MCDA)** approach:

$$\text{raw\_priority} = 0.60 \cdot \text{risk\_score} + 0.25 \cdot \text{norm\_depth} + 0.15 \cdot \text{hazard\_factor}$$

$$\text{confidence\_factor} = 0.85 + 0.15 \cdot \text{risk\_confidence}$$

$$\text{priority\_score} = \text{raw\_priority} \cdot \text{confidence\_factor}$$

### Named Tier Thresholds:

| Named Tier Constant | Score Threshold | Justification & Policy Action |
| :--- | :--- | :--- |
| `TIER_CRITICAL_THRESHOLD` | `priority_score >= 0.65` | **CRITICAL PRIORITY**: Immediate emergency resource dispatch (pumps & heavy rescue crews). |
| `TIER_HIGH_THRESHOLD` | `priority_score >= 0.45` | **HIGH PRIORITY**: Heightened alert; pre-positioning support crews & mobile pumps. |
| `TIER_MODERATE_THRESHOLD` | `priority_score >= 0.30` | **MODERATE PRIORITY**: Standard monitoring and drain inspection. |
| *Below 0.30* | `priority_score < 0.30` | **LOW PRIORITY**: Routine operations; automated sensor telemetry monitoring. |

---

## 7. Constraint Optimization (OPTIMIZE Layer)

Layer 4 (**OPTIMIZE**) solves a **0-1 Multi-Dimensional Knapsack Problem** using the **Google OR-Tools CP-SAT Solver**:

* **Decision Variables**: $x_z \in \{0, 1\}$ for each zone $z$.
* **Objective Function**:
  $$\max \sum_{z=1}^Z \left(\lfloor\text{priority\_score}_z \cdot 10000\rfloor\right) \cdot x_z$$
* **Hard Constraints**:
  1. $\sum \text{req\_pumps}_z \cdot x_z \le \text{TOTAL\_PUMPS}$ (default 6 units)
  2. $\sum \text{req\_crews}_z \cdot x_z \le \text{TOTAL\_CREWS}$ (default 4 teams)
  3. $\sum \text{req\_cost}_z \cdot x_z \le \text{TOTAL\_BUDGET}$ (default $500,000)

---

## 8. Action Directives & Executive Briefings (RECOMMEND Layer)

Layer 5 (**RECOMMEND**) maps optimization outcomes to deterministic action directives:

| Allocation Status | Priority / Risk Score Criteria | Action Directive (`recommended_action`) | Rationale |
| :--- | :--- | :--- | :--- |
| **`ALLOCATED`** | `risk_score >= 0.80` OR `priority_score >= 0.70` | `"REPAIR & DISPATCH IMMEDIATELY"` | Severe inundation; immediate deployment of heavy pumps & crews. |
| **`ALLOCATED`** | `risk_score < 0.80` AND `priority_score < 0.70` | `"ACTIVE RESPONSE DISPATCHED"` | Active mitigation deployed to prevent flood escalation. |
| **`SKIPPED`** | `priority_score >= 0.65` | `"ESCALATE FOR REINFORCEMENTS"` | **High-priority unserved zone**; immediate escalation to city command. |
| **`SKIPPED`** | $0.45 \le \text{priority\_score} < 0.65$ | `"INSPECT & MONITOR HIGH RISK"` | Substantial risk unserviced; mobile inspection dispatched. |
| **`SKIPPED`** | $\text{priority\_score} < 0.45$ | `"ROUTINE MONITORING"` | Low flood impact; retain on telemetry monitoring. |

---

## 9. Scenario Simulation (SIMULATE Layer)

Layer 6 (**SIMULATE**) provides interactive **What-If Scenario Simulation** (e.g. +50% deluge storm surge or -40% municipal budget cut). Overrides are applied strictly in-memory (`zone_state.copy()`) without mutating the underlying database, generating clean BEFORE vs. AFTER delta comparisons.
