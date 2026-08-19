# 🌐 UrbanShield Data Provenance & Real Data Sources

This document details the publicly available, real-world Chennai datasets integrated into UrbanShield.

> [!IMPORTANT]
> **Data & Methodology Disclosure**
> **UrbanShield uses publicly available historical Chennai rainfall, inundation and flood-hazard observations. The current prototype performs evidence-based risk estimation rather than claiming a fully trained real-world predictive ML model. Future versions will integrate larger time-aligned historical datasets for supervised prediction.**

---

### 1. Chennai Inundation Survey Points
* **Dataset Name**: `chennai_flood_inundation_inches` (`data/opencity_inundation_points.kml`)
* **Source Organization**: OpenCity.in / Greater Chennai Corporation (GCC)
* **Original URL**: [https://data.opencity.in/dataset/chennai-flooding-data](https://data.opencity.in/dataset/chennai-flooding-data)
* **Date Accessed**: August 2026
* **File Format**: KML (ExtendedData XML Schema)
* **Record Count**: 192 surveyed inundation points
* **Relevant Fields**:
  * `F_LATITUDE`, `F_LONGITUDE`: Exact surveyed GPS coordinates across Chennai.
  * `DEPTH`: Measured street flood water depth in inches (ranging from 5.0 to 60.0 inches).
  * `F_REMARKS`: Field inspection reports (*e.g., "completely inundated with flood water", "water stagnant on main road", "railway station covered by flood upto 1 feet"*).
* **How UrbanShield Uses It**: Provides ground-truth physical flood waterlogging evidence in Layer 1 (SENSE) and Layer 2 (PREDICT).
* **Limitations**: Observational survey snapshot; does not contain continuous time-series telemetry.

---

### 2. Chennai Municipal Flood Hotspots (Cyclone Nivar / Monsoon Logs)
* **Dataset Name**: `chennai-gcc-flood-hotspots-2020` (`data/opencity_gcc_flood_hotspots_2020.kml`)
* **Source Organization**: Greater Chennai Corporation (GCC) Disaster Management Cell / OpenCity.in
* **Original URL**: [https://data.opencity.in/dataset/3aef2eef-a97e-4fac-a4a9-aaa42a91fbfa](https://data.opencity.in/dataset/3aef2eef-a97e-4fac-a4a9-aaa42a91fbfa)
* **Date Accessed**: August 2026
* **File Format**: KML
* **Record Count**: 53 designated municipal flood zones
* **Relevant Fields**:
  * `name`: Official Chennai locality / ward name (*e.g., Jothi Nagar, Rajaji Nagar, Thirumalai Nagar, Parimalam Nagar, Balaji Nagar, Villivakkam*).
  * `latitude`, `longitude`: GPS centroids of vulnerable municipal zones.
* **How UrbanShield Uses It**: Defines active municipal zone boundaries and vulnerability targets for emergency dispatch optimization.
* **Limitations**: Zone locations represent vulnerability clusters rather than full polygon boundaries.

---

### 3. Chennai Meteorological Weather Station Network
* **Dataset Name**: `chennai_rainfall_stations.csv`
* **Source Organization**: India Meteorological Department (IMD) / GCC Regional Meteorological Centre (RMC) Chennai
* **Original URL**: [https://github.com/Esri/arcgis-python-api](https://github.com/Esri/arcgis-python-api) / [https://mausam.imd.gov.in/chennai/](https://mausam.imd.gov.in/chennai/)
* **Date Accessed**: August 2026
* **File Format**: CSV
* **Record Count**: 119 station/district records (20 core metropolitan Chennai weather stations)
* **Relevant Fields**:
  * `WEATHER STATION`: Official station name (*e.g., Tambaram, Chembarambakkam, Chennai AP [Meenambakkam], Taramani ARG, Anna University ARG, Red Hills, Poonamallee, DGP Office*).
  * `LOCATION`: Chennai district locality.
  * `RAINFALL`: Real observed rainfall in mm (*e.g., 49mm, 47mm, 35mm, 32mm, 27mm*).
* **How UrbanShield Uses It**: Spatial proximity matching using the Haversine formula assigns the nearest IMD station rainfall and station distance (km) to each zone.
* **Limitations**: Stations report cumulative 24h precipitation; micro-burst variances between stations are smoothed via distance-weighted confidence bounds.

---

### 4. Chennai Master Plan Flood Hazard Zones
* **Dataset Name**: `chennai_flood_hazard_zones` (`data/opencity_flood_hazard_zones.kml`)
* **Source Organization**: Chennai Metropolitan Development Authority (CMDA) & GCC
* **Original URL**: [https://data.opencity.in/dataset/022dd080-e927-40d7-897d-adf3ee98ad69](https://data.opencity.in/dataset/022dd080-e927-40d7-897d-adf3ee98ad69)
* **Date Accessed**: August 2026
* **File Format**: KML
* **Record Count**: 7,453 geospatial polygons
* **Relevant Fields**:
  * `CATEGORY`: Official flood hazard level (`Very High`, `High`, `Moderate`, `Low`, `Very Low`).
  * `SHAPE.AREA`, `SHAPE.LEN`: Spatial footprint.
* **How UrbanShield Uses It**: Supplies official municipal hazard susceptibility ratings in Layer 2 (PREDICT) and Layer 3 (PRIORITIZE).

---

---

### 5. Critical Infrastructure Location: Rajalakshmi Engineering College (REC)
* **Location Name**: Rajalakshmi Engineering College (REC)
* **Address**: Rajalakshmi Nagar, Thandalam, Chennai – 602105
* **Official Institutional Source**: [https://www.rajalakshmi.org/](https://www.rajalakshmi.org/)
* **Official Coordinates**: `13.009644, 80.004336`
* **Infrastructure Type**: Critical Higher-Education & Research Campus
* **Environmental Data Linking & Proximity Provenance**:
  * **Nearest IMD Rainfall Station**: `CHEMBARABAKKAM` (Observed Rainfall: `47.0 mm`, Haversine Distance: `5.76 km`)
  * **Nearest Surveyed Inundation Point**: OpenCity Subway waterlogging survey point (Surveyed Depth: `35.0 inches`, Haversine Distance: `18.89 km`)
  * **Nearest CMDA Flood Hazard Polygon**: `LOW` / `VERY_LOW` (Centroid Distance: `14.97 km`)
  * **Data Integrity Notice**: REC is integrated as a critical infrastructure monitoring asset. Environmental observations are linked from nearest available public telemetry and spatial surveys; they are not presented as direct on-campus telemetry measurements.

---

### 6. Summary of Integration & Spatial Coupling

```
┌──────────────────────────────────────────────────────────┐
│                   REAL DATA SOURCES                      │
├──────────────────────────┬───────────────────────────────┤
│ OpenCity / GCC           │ 192 Inundation Survey Points  │
│ GCC Disaster Cell        │ 53 Municipal Flood Hotspots   │
│ IMD Chennai Network      │ 119 Weather Station Records   │
│ CMDA / GCC Master Plan   │ 7,453 Flood Hazard Polygons   │
│ REC Official Coordinates │ Rajalakshmi Nagar, Thandalam  │
└──────────────────────────┴───────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│              LAYER 1: SENSE INGESTION                    │
│ • Haversine distance spatial matching                    │
│ • Observational validation & provenance tracking         │
│ • SQLite persistence (data/urbanshield.db - 16 locations)│
└──────────────────────────┴───────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│              LAYER 2: PREDICT ESTIMATION                 │
│ • Inundation depth weight (45%)                          │
│ • Official hazard tier weight (35%)                      │
│ • Distance-weighted rainfall evidence (20%)              │
│ • Zero synthetic formulas / Zero circular labels         │
└──────────────────────────┴───────────────────────────────┘
```
